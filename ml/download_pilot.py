import httpx,json,random,concurrent.futures,time
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'datasets/plantvillage-pilot';ROOT.mkdir(parents=True,exist_ok=True)
client=httpx.Client(timeout=60,follow_redirects=True)
base='https://api.github.com/repos/spMohanty/PlantVillage-Dataset'
r=client.get(base+'/git/trees/7f7ecc7e1eaca78107e3affe7cb5abd9427e139a');r.raise_for_status();top=r.json();raw=next(x for x in top['tree'] if x['path']=='raw')
r=client.get(raw['url']);r.raise_for_status();color=next(x for x in r.json()['tree'] if x['path']=='color')
r=client.get(color['url']);r.raise_for_status();folders=r.json()['tree']
classes={}
for folder in folders:
 if folder['type']!='tree':continue
 r=client.get(folder['url']);r.raise_for_status()
 items=r.json()['tree'];classes[folder['path']]=[{**item,'path':folder['path']+'/'+item['path']} for item in items if item['type']=='blob' and item['path'].lower().endswith(('.jpg','.jpeg','.png'))]
 print('Indexed',folder['path'],len(classes[folder['path']]),flush=True)
rng=random.Random(42);selected=[]
for name,items in sorted(classes.items()):rng.shuffle(items);selected+=items[:100]
commit=top['sha'];print('Source',commit,'classes',len(classes),'selected images',len(selected),flush=True)
metadata={'source':'https://github.com/spMohanty/PlantVillage-Dataset','tree_sha':commit,'seed':42,'max_per_class':100,'full_source_counts':{k:len(v) for k,v in classes.items()},'selected':[i['path'] for i in selected]}
(PROJECT/'datasets/pilot-acquisition.json').write_text(json.dumps(metadata,indent=2))
def fetch(item):
 target=ROOT/item['path'];target.parent.mkdir(exist_ok=True)
 if target.exists():return
 url=f'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/{commit}/raw/color/'+item['path']
 for attempt in range(4):
  try:
   response=client.get(url);response.raise_for_status();target.write_bytes(response.content);return
  except Exception:
   if attempt==3:raise
   time.sleep(1+attempt)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
 for i,_ in enumerate(executor.map(fetch,selected),1):
  if i%200==0:print('Downloaded',i,flush=True)
print('Complete',len(selected),flush=True)
