"""Explicit external class mapping, with training-set overlap exclusion."""
import argparse,json,hashlib
from pathlib import Path
import imagehash
from PIL import Image
from .prepare import BKTree
p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('mapping');p.add_argument('training_manifest');p.add_argument('output');a=p.parse_args()
training=json.loads(Path(a.training_manifest).read_text());mapping=json.loads(Path(a.mapping).read_text());root=Path(a.root).resolve();rows=[];excluded=[]
tree=BKTree()
for i,row in enumerate(training['images']):tree.add(row['phash'],i)
for path in sorted(root.glob('*/*')):
    if not path.is_file() or path.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):continue
    label=mapping.get(path.parent.name)
    if not label:excluded.append({'path':str(path),'reason':'unmapped class'});continue
    if label not in training['classes']:raise ValueError(f'Unknown destination class: {label}')
    with Image.open(path) as im:phash=int(str(imagehash.phash(im.convert('RGB'))),16)
    if list(tree.near(phash,4)):excluded.append({'path':str(path),'reason':'possible development-set overlap'});continue
    rows.append({'path':str(path.relative_to(root)),'class':label,'split':'external'})
if not rows:raise ValueError('No compatible external images remain')
Path(a.output).write_text(json.dumps({'root':str(root),'classes':training['classes'],'images':rows,'excluded':excluded,'mapping':mapping,'development_only':training.get('development_only',False)},indent=2))
print(f'{len(rows)} external images; {len(excluded)} excluded. No external tuning is permitted.')
