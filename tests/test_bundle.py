import json
import pytest
from scripts import bundle_demo


def test_ungrounded_real_metrics_cannot_be_packaged(tmp_path,monkeypatch):
    run_id='a'*32
    folder=tmp_path/'runs'/run_id;folder.mkdir(parents=True)
    (folder/'report.json').write_text(json.dumps({'run_id':run_id,'mode':'live',
        'data_origin':'real_local_inference_and_live_nemotron','verdict':'QUARANTINE'}))
    monkeypatch.setattr(bundle_demo,'ROOT',tmp_path)
    monkeypatch.setattr('sys.argv',['bundle_demo.py',run_id])
    with pytest.raises(ValueError,match='grounding'):bundle_demo.main()
    assert not (tmp_path/'demo').exists()
