"""Inspect ImageFolder data and remove exact/perceptual duplicates before splitting."""
import argparse, hashlib, json, random
from collections import Counter, defaultdict
from pathlib import Path
import imagehash
from PIL import Image
class BKTree:
    def __init__(self):self.root=None
    def add(self,key,index):
        node=self.root
        if node is None:self.root=[key,index,{}];return
        while True:
            distance=(key^node[0]).bit_count()
            if distance not in node[2]:node[2][distance]=[key,index,{}];return
            node=node[2][distance]
    def near(self,key,radius):
        stack=[self.root] if self.root else []
        while stack:
            value,index,children=stack.pop();distance=(key^value).bit_count()
            if distance<=radius:yield index
            stack.extend(child for edge,child in children.items() if distance-radius<=edge<=distance+radius)
def prepare(root,out,seed=42,radius=4,development=False,quarantine_conflicts=False):
    root=Path(root).resolve();rows=[];rejected=[];duplicates=[];hashes={};tree=BKTree();quarantined=set();conflicts=[]
    for path in sorted(root.glob('*/*')):
        if not path.is_file() or path.suffix.lower() not in ('.jpg','.jpeg','.png','.webp'):continue
        try:
            with Image.open(path) as image:
                image=image.convert('RGB');image.load()
                exact=hashlib.sha256(image.tobytes()+str(image.size).encode()).hexdigest()
                perceptual=int(str(imagehash.phash(image)),16)
        except (OSError,ValueError) as exc:rejected.append({'path':str(path),'reason':str(exc)});continue
        label=path.parent.name
        similar=list(tree.near(perceptual,radius))
        if exact in hashes:similar.append(hashes[exact])
        if similar:
            if any(rows[i]['class']!=label for i in similar):
                if not quarantine_conflicts:raise ValueError(f'Conflicting labels among duplicate images: {path}; review dataset before splitting')
                quarantined.update(similar)
                conflicts.append({'path':str(path.relative_to(root)),'matches':[rows[i]['path'] for i in similar],'reason':'ambiguous cross-label pHash group excluded before split'})
                continue
            duplicates.append({'path':str(path.relative_to(root)),'matches':rows[similar[0]]['path']});continue
        hashes[exact]=len(rows);tree.add(perceptual,len(rows))
        rows.append({'path':str(path.relative_to(root)),'class':label,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'phash':perceptual})
    quarantine_rows=[rows[i]['path'] for i in sorted(quarantined)]
    rows=[r for i,r in enumerate(rows) if i not in quarantined]
    groups=defaultdict(list)
    for row in rows:groups[row['class']].append(row)
    if len(groups)<2:raise ValueError('At least two class folders are required')
    randomizer=random.Random(seed)
    for label,group in groups.items():
        if len(group)<10:raise ValueError(f'{label}: need at least 10 unique images, found {len(group)}')
        randomizer.shuffle(group);n=len(group);train=int(n*.8);validation=max(1,int(n*.1))
        for i,row in enumerate(group):row['split']='train' if i<train else 'val' if i<train+validation else 'test'
    result={'root':str(root),'seed':seed,'classes':sorted(groups),'development_only':development,
        'preprocessing':{'size':128,'mean':[.485,.456,.406],'std':[.229,.224,.225]},
        'distribution':dict(Counter(r['class'] for r in rows)),
        'split_counts':dict(Counter(r['split'] for r in rows)), 'duplicate_policy':f'discard later pixel-exact or pHash Hamming <= {radius}; conflicting labels fail',
        'quarantined_conflicts':conflicts,'quarantined_representatives':quarantine_rows,
        'duplicates_removed':duplicates,'invalid_images':rejected,'images':rows}
    Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(result,indent=2))
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('output');p.add_argument('--seed',type=int,default=42);p.add_argument('--phash-radius',type=int,default=4);p.add_argument('--development',action='store_true');p.add_argument('--quarantine-conflicts',action='store_true');a=p.parse_args()
    result=prepare(a.root,a.output,a.seed,a.phash_radius,a.development,a.quarantine_conflicts)
    print(json.dumps({k:result[k] for k in ('distribution','split_counts','development_only')},indent=2))
