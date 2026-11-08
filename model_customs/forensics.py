"""Delta-weight SVD and activation monitoring inspired by Watch the Weights.

LoRA is LOW RANK BY DESIGN. Its rank is never evidence of a backdoor.
This is an audit aid, not a reproduction of the paper's detection guarantees.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def factor_svd(a, b, scaling: float = 1.0):
    """Exact thin SVD of delta=(alpha/r)*B@A, retaining both singular vectors.

    QR reduces the SVD to r*r without materializing a full dense delta.
    Returned U,S,Vh reconstruct the actual delta, including its scaling.
    """
    import torch
    a = a.detach().float().cpu()
    b = b.detach().float().cpu()
    if a.ndim != 2 or b.ndim != 2 or b.shape[1] != a.shape[0]:
        raise ValueError('LoRA A and B must have compatible matrix dimensions')
    qb, rb = torch.linalg.qr(b, mode='reduced')
    qa, ra = torch.linalg.qr(a.T, mode='reduced')
    um, s, vhm = torch.linalg.svd(float(scaling) * rb @ ra.T, full_matrices=False)
    return qb @ um, s, vhm @ qa.T


def cosine_alignment(activations, directions):
    """Absolute token/direction cosines in one explicitly matched vector space.

    Directions are rows: Vh for layer inputs, U.T for layer outputs. This shared
    math does not select the hook space; activation_direction_alignment does.
    Absolute values discard signed-tail information and are an adaptation of
    WeightWatch v1's signed per-direction token ranges, not its detector.
    """
    import torch
    if activations.ndim < 1 or directions.ndim != 2 or directions.shape[0] < 1:
        raise ValueError('Activations need a feature dimension; directions must be nonempty rows')
    if activations.shape[-1] != directions.shape[-1]:
        raise ValueError('Direction row width must match the activation feature space')
    x = activations.detach().float().cpu().reshape(-1, activations.shape[-1])
    v = directions.detach().float().cpu()
    x = torch.nn.functional.normalize(x, dim=-1)
    v = torch.nn.functional.normalize(v, dim=-1)
    return (x @ v.T).abs()


def activation_direction_alignment(activations, directions, *, activation_space, vector_side):
    """Reject input/U or output/V comparisons even if square shapes conceal them.

    Input/right (Vh rows) is supplementary. Output/left (U.T rows) matches the
    paper's space. Both still use our existing absolute, pooled diagnostic.
    """
    expected={'input':'right','output':'left'}
    if activation_space not in expected or vector_side!=expected[activation_space]:
        raise ValueError('Layer inputs require right V; layer outputs require left U')
    return cosine_alignment(activations,directions)


def alignment_scope():
    """Machine-readable scope; this describes existing statistics, not a new run."""
    return {
        'protocol':'tripwir3-absolute-pooled-calibration-v1',
        'paper_reference':'https://arxiv.org/html/2508.00161v1#S3',
        'primary_pairing':'projection module output with left U (rows U.T)',
        'supplementary_pairing':'projection module input with right V (rows Vh); adaptation',
        'layer_selection':'all adapted o_proj/down_proj modules, including final three layers',
        'retained_directions':'min(inspector cap20, adapter rank);8 for current controls',
        'token_scope':'entire single-example chat-template prompt, including system/user and assistant prefix; no generated tokens or padding',
        'normalization':'float32 CPU; row-wise L2 normalization, eps1e-12; absolute cosine',
        'aggregation':'per-prompt min/max across all tokens and directions; first-direction token maximum; average first-direction maximum across prompts',
        'calibration':'100 unique clean arithmetic prompts; separate from frozen final inputs; descriptive only',
        'paper_range_detector_implemented':False,
        'deviations':['absolute rather than signed cosine','pool directions in extrema',
                      'no per-direction streaming range or anomaly threshold',
                      'no separate user/assistant ranges','no final-three-layer exclusion',
                      'no completion-token calibration or steering'],
        'published_performance_applies':False,
    }


def audit_adapter(adapter_path: str | Path, output_dir: str | Path, rank: int = 20) -> dict[str, Any]:
    """Inspect actual adapter deltas. Persist U and Vh rather than singular values alone."""
    import torch
    from safetensors.torch import load_file, save_file
    path, dest = Path(adapter_path), Path(output_dir)
    config = json.loads((path / 'adapter_config.json').read_text())
    if config.get('use_dora') or config.get('use_rslora'):
        raise ValueError('DoRA/rsLoRA scaling is unsupported by this inspector')
    state = load_file(str(path / 'adapter_model.safetensors'), device='cpu')
    dest.mkdir(parents=True, exist_ok=True)
    vectors, layers = {}, []
    for key in sorted(state):
        if '.lora_A.' not in key:
            continue
        bkey = key.replace('.lora_A.', '.lora_B.')
        if bkey not in state:
            raise ValueError('Missing paired LoRA B matrix')
        module = key.split('.lora_A.')[0]
        r = state[key].shape[0]
        if config.get('rank_pattern') or config.get('alpha_pattern'):
            raise ValueError('Pattern-dependent LoRA scaling requires explicit support')
        scale = config['lora_alpha'] / r
        u, s, vh = factor_svd(state[key], state[bkey], scale)
        k = min(rank, len(s))
        vectors[module + '.U'] = u[:, :k].contiguous()
        vectors[module + '.S'] = s[:k].contiguous()
        vectors[module + '.Vh'] = vh[:k].contiguous()
        energy = s.square()
        layers.append({'module': module, 'shape': [int(u.shape[0]), int(vh.shape[1])],
                       'adapter_rank': r, 'scaling': scale,
                       'singular_values': s.tolist(), 'frobenius_norm': float(s.norm()),
                       'top1_energy_fraction': float(energy[0] / energy.sum()) if energy.sum() else 0.0,
                       'saved_directions': k})
    if not layers:
        raise ValueError('No LoRA matrices found')
    vector_path = dest / 'delta_directions.safetensors'
    save_file(vectors, str(vector_path))
    report = {'method': 'exact LoRA delta SVD via thin QR; output/U paper-space pairing plus supplementary input/V; absolute pooled diagnostic',
              'alignment_scope':alignment_scope(),
              'paper': 'https://arxiv.org/html/2508.00161v1#S3', 'artifact_sha256': sha256_file(path / 'adapter_model.safetensors'),
              'directions_file': str(vector_path), 'directions_sha256': sha256_file(vector_path),
              'layers': layers, 'interpretation': 'LoRA is low rank by design. Low rank alone is NOT evidence of a backdoor.',
              'limitations': ['No calibrated detection threshold', 'Training controls are toy artifacts',
                              'Activation monitoring is inspired by Watch the Weights, not a paper reproduction']}
    (dest / 'forensics.json').write_text(json.dumps(report, indent=2))
    return report
