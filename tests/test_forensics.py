"""Numerical invariants for actual low-rank delta inspection."""
import pytest
import torch
from model_customs.forensics import factor_svd, cosine_alignment
from model_customs.controls import clean_examples, training_examples


def test_thin_svd_reconstructs_scaled_non_square_delta():
    torch.manual_seed(4)
    a,b=torch.randn(3,11),torch.randn(7,3)
    u,s,vh=factor_svd(a,b,2.5)
    assert torch.allclose(u@torch.diag(s)@vh,2.5*b@a,atol=1e-5)
    assert torch.allclose(u.T@u,torch.eye(3),atol=1e-5)
    assert torch.allclose(vh@vh.T,torch.eye(3),atol=1e-5)


def test_direction_alignment_is_input_space_and_scale_invariant():
    x=torch.tensor([[2.,0.,0.],[0.,3.,0.]])
    v=torch.tensor([[1.,0.,0.]])
    assert cosine_alignment(x,v).flatten().tolist()==[1.,0.]
    assert torch.equal(cosine_alignment(x*4,v),cosine_alignment(x,v))


def test_zero_delta_is_zero_without_nan():
    u,s,vh=factor_svd(torch.randn(2,5),torch.zeros(7,2))
    assert torch.isfinite(s).all()
    assert s.sum()==0


def test_bad_factor_shapes_rejected():
    with pytest.raises(ValueError): factor_svd(torch.randn(2,5),torch.randn(7,3))


def test_clean_evaluation_not_exact_training_prompts():
    train={x['prompt'] for x in training_examples()}
    test=clean_examples(100)
    assert len(test)==100
    assert len({x['prompt'] for x in test})==100
    assert not {x['prompt'] for x in test}.intersection(x['prompt'] for x in clean_examples(100,offset=200))
    assert not train.intersection(x['prompt'] for x in test)
