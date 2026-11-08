from model_customs.rate_limit import NvidiaLimiter


def test_bucket_is_shared_across_instances_and_models(tmp_path):
    now=[1000.0]
    first=NvidiaLimiter(tmp_path/'rate.sqlite',clock=lambda:now[0])
    second=NvidiaLimiter(tmp_path/'rate.sqlite',clock=lambda:now[0])
    assert first.reserve()==0
    assert second.reserve()==2  # shared capacity1, not one bucket per model/client
    now[0]+=1
    assert first.reserve()==1
    now[0]+=1
    assert second.reserve()==0
    assert first.reserve()==2


def test_backward_clock_never_creates_tokens(tmp_path):
    now=[1000.0]
    bucket=NvidiaLimiter(tmp_path/'rate.sqlite',clock=lambda:now[0])
    assert bucket.reserve()==0
    now[0]-=1
    assert bucket.reserve()==2
