import argparse,json
from pathlib import Path
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('experiments');p.add_argument('--output',required=True);a=p.parse_args();rows=[]
for path in Path(a.experiments).rglob('metrics.json'):
    m=json.loads(path.read_text());rows.append({'model':m['architecture'],'split':m['split'],'development_only':m['development_only'],'samples':m['samples'],'accuracy':m['accuracy'],'macro_f1':m['macro_f1'],'precision_macro':m['classification_report']['macro avg']['precision'],'recall_macro':m['classification_report']['macro avg']['recall'],'parameters':m['parameters'],'checkpoint_bytes':m['checkpoint_bytes'],'latency_ms':m['latency_ms_median'],'source':str(path)})
out=Path(a.output);out.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows).to_csv(out/'comparison.csv',index=False)
(out/'report.md').write_text('# Actual experiment inventory\n\n'+ ('No evaluation outputs found. All experiments pending.' if not rows else '\n\n'.join(f"- {r['model']} / {r['split']}: n={r['samples']}, accuracy={r['accuracy']:.4f}, macro-F1={r['macro_f1']:.4f}; development-only={r['development_only']}. Source: {r['source']}" for r in rows))+'\n\nDevelopment-only runs are pipeline checks and are not crop disease performance evidence. Compare only matching protocols and datasets.\n')
