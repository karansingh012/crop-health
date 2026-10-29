import argparse, json, random, hashlib
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score
from .models import build_model,NAMES
from .data import ManifestDataset

def run_epoch(model,loader,device,optimizer=None):
    model.train(optimizer is not None);losses=[];truth=[];pred=[]
    with torch.set_grad_enabled(optimizer is not None):
        for images,labels in loader:
            images,labels=images.to(device),labels.to(device)
            logits=model(images);loss=nn.functional.cross_entropy(logits,labels)
            if optimizer:
                optimizer.zero_grad();loss.backward();optimizer.step()
            losses.extend([loss.item()]*len(labels));truth.extend(labels.cpu().tolist());pred.extend(logits.argmax(1).detach().cpu().tolist())
    return {'loss':float(np.mean(losses)),'accuracy':float(np.mean(np.array(truth)==pred)),'macro_f1':float(f1_score(truth,pred,average='macro',zero_division=0))}
def train(args):
    torch.set_num_threads(args.threads)
    random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True,warn_only=True)
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    manifest=json.loads(Path(args.manifest).read_text())
    train_data=ManifestDataset(args.manifest,'train',True);val_data=ManifestDataset(args.manifest,'val')
    if not train_data or not val_data:raise ValueError('Training and validation sets must not be empty')
    model=build_model(args.model,len(train_data.classes),pretrained=args.pretrained).to(device)
    if args.initialize:
        previous=torch.load(args.initialize,map_location='cpu',weights_only=True)
        if previous['classes']!=train_data.classes or previous['architecture']!=args.model:raise ValueError('Initialization class mapping or architecture mismatch')
        model.load_state_dict(previous['state_dict'])
    if args.model=='optimized':
        from torch.nn.utils import prune
        for module in model.modules():
            if isinstance(module,nn.Conv2d):prune.l1_unstructured(module,'weight',amount=.3)
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=.01)
    train_loader=DataLoader(train_data,batch_size=args.batch_size,shuffle=True,generator=torch.Generator().manual_seed(args.seed))
    val_loader=DataLoader(val_data,batch_size=args.batch_size)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True);history=[];best=-1
    for epoch in range(args.epochs):
        row={'epoch':epoch+1,'train':run_epoch(model,train_loader,device,optimizer),'val':run_epoch(model,val_loader,device)}
        history.append(row);print(json.dumps(row),flush=True)
        if row['val']['macro_f1']>best:
            best=row['val']['macro_f1']
            # Keep masks active during training; serialize a plain model with zeroed weights.
            import copy
            saved=copy.deepcopy(model).cpu() if args.model!='optimized' else build_model(args.model,len(train_data.classes),pretrained=args.pretrained)
            if args.model=='optimized':
                state={}
                for key,value in model.state_dict().items():
                    if key.endswith('_mask'):continue
                    if key.endswith('_orig'):
                        state[key[:-5]]=(value*model.state_dict()[key[:-5]+'_mask']).cpu()
                    else:state[key]=value.cpu()
                saved.load_state_dict(state)
            torch.save({'state_dict':saved.state_dict(),'architecture':args.model,'classes':train_data.classes,
                        'trained':True,'development_only':manifest.get('development_only',False),
                        'threshold':None,'preprocessing':manifest['preprocessing'],'seed':args.seed,
                        'training_scope':manifest.get('training_scope','full user-supplied dataset'),'pretrained_backbone':args.pretrained,
                        'manifest_sha256':hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest(),'epoch':epoch+1},out/'best.pt')
        (out/'history.json').write_text(json.dumps(history,indent=2))
    (out/'config.json').write_text(json.dumps({**vars(args),'device':str(device),'torch':str(torch.__version__)},indent=2))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,key in zip(axes,['loss','macro_f1']):
        for split in ('train','val'):ax.plot([r[split][key] for r in history],label=split)
        ax.set_title(key);ax.set_xlabel('Epoch (zero indexed)');ax.legend()
    fig.tight_layout();fig.savefig(out/'curves.png');plt.close(fig)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('--model',choices=NAMES,default='lightweight');p.add_argument('--output',required=True)
    p.add_argument('--epochs',type=int,default=20);p.add_argument('--batch-size',type=int,default=32);p.add_argument('--lr',type=float,default=.0003);p.add_argument('--seed',type=int,default=42);p.add_argument('--threads',type=int,default=4);p.add_argument('--initialize');p.add_argument('--pretrained',action='store_true');a=p.parse_args()
    if a.epochs<1:p.error('epochs must be positive')
    train(a)
