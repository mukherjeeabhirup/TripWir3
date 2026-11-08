"""Record genuine clean-prompt activation monitoring; descriptive, not calibrated detection."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from model_customs.controls import LocalControls,clean_examples
model=LocalControls()
prompts=[x['prompt'] for x in clean_examples(100)]
start=time.monotonic()
for artifact in ['benign','poisoned']:
    row=model.alignment(artifact,prompts)
    row['data_kind']='real_model_forward_passes'
    row['elapsed_s']=time.monotonic()-start
    destination=Path('artifacts/controls')/artifact/'forensics'/'clean_alignment.json'
    destination.write_text(json.dumps(row,indent=2))
    print(json.dumps({'artifact':artifact,'n':row['sample_size'],'layers':len(row['layers']),
                      'elapsed_s':row['elapsed_s'],'output':str(destination)}),flush=True)
