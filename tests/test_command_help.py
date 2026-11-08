"""Help must not import providers, read secrets or process evidence."""
import os
from pathlib import Path
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=['train_controls.py','run_audit.py','bundle_demo.py','check_offline_replay.py',
         'smoke_controls.py','calibrate_controls.py','check_connections.py','cloud_smoke.py',
         'verify_results.py','run_hero.py','scan_secrets.py','check_frontend.py']

@pytest.mark.parametrize('script',SCRIPTS)
def test_help_exits_before_provider_imports_and_file_changes(script,tmp_path):
    (tmp_path/'sitecustomize.py').write_text('''import sys
class NoProviders:
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'model_customs','torch','transformers','peft','httpx','dotenv','huggingface_hub'}:
            raise RuntimeError('Help imported a provider or configuration module')
sys.meta_path.insert(0,NoProviders())
''')
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(tmp_path)}
    result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--help'],cwd=tmp_path,
                          env=env,capture_output=True,text=True,timeout=10)
    assert result.returncode==0,(script,result.stderr)
    assert 'usage:' in result.stdout.lower()
    assert sorted(p.name for p in tmp_path.iterdir())==['sitecustomize.py']


def test_retired_hero_has_no_inference_path(tmp_path):
    result=subprocess.run([sys.executable,str(ROOT/'scripts/run_hero.py')],cwd=tmp_path,
                          env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=10)
    assert result.returncode==2
    assert '"status": "retired"' in result.stdout
