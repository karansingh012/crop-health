"""Validation-only abstention threshold selection; untouched internal/external evaluation."""
import argparse, json, time, platform, hashlib
from pathlib import Path
import numpy as np
import torch, psutil
from sklearn.metrics import classification_report,confusion_matrix,accuracy_score,f1_score
from torch.utils.data import DataLoader
from .models import build_model
from .data import ManifestDataset

def evaluate(a):
    torch.set_num_threads(4)
    checkpoint=torch.load(a.checkpoint,map_location='cpu',weights_only=True)
    if a.select_threshold and a.split!='val':raise ValueError('Threshold selection is allowed only on validation data')
    if a.select_threshold and checkpoint['manifest_sha256']!=hashlib.sha256(Path(a.manifest).read_bytes()).hexdigest():raise ValueError('Threshold selection requires the original training manifest')
    dataset=ManifestDataset(a.manifest,a.split)
    if not dataset:raise ValueError('No images in selected split')
    if dataset.classes!=checkpoint['classes']:raise ValueError('Class mapping mismatch; use ml.external to map PlantDoc')
    model=build_model(checkpoint['architecture'],len(checkpoint['classes']));model.load_state_dict(checkpoint['state_dict']);model.eval()
    truth=[];pred=[];scores=[];latencies=[];rss=[]
    with torch.inference_mode():
        for _ in range(5):model(torch.zeros(1,3,128,128))
        for images,labels in DataLoader(dataset,batch_size=1):
            start=time.perf_counter();prob=model(images).softmax(1);latencies.append(time.perf_counter()-start)
            score,indices=prob.max(1);truth.extend(labels.tolist());pred.extend(indices.tolist());scores.extend(score.tolist());rss.append(psutil.Process().memory_info().rss)
    truth=np.array(truth);pred=np.array(pred);scores=np.array(scores)
    selection=None
    if a.select_threshold:
        # Select maximum coverage with empirical precision >= 90%, at least 20 retained samples.
        choices=[]
        for threshold in np.linspace(0,1,101):
            accepted=scores>=threshold
            if accepted.sum()>=20 and np.mean(truth[accepted]==pred[accepted])>=.9:choices.append(float(threshold))
        checkpoint['threshold']=min(choices) if choices else None
        selection={'threshold':checkpoint['threshold'],'minimum_samples':20,'target_empirical_accuracy':.9,'validation_samples':len(truth),'note':'Empirical selection; not a guarantee or probability calibration.'}
        checkpoint['threshold_selection']=selection
        torch.save(checkpoint,a.checkpoint)
    report={'architecture':checkpoint['architecture'],'development_only':checkpoint.get('development_only',False),'split':a.split,'samples':len(truth),
        'accuracy':float(accuracy_score(truth,pred)),'macro_f1':float(f1_score(truth,pred,labels=range(len(dataset.classes)),average='macro',zero_division=0)),
        'classification_report':classification_report(truth,pred,labels=list(range(len(dataset.classes))),target_names=dataset.classes,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(truth,pred,labels=list(range(len(dataset.classes)))).tolist(),
        'parameters':sum(p.numel() for p in model.parameters()),'checkpoint_bytes':Path(a.checkpoint).stat().st_size,
        'latency_ms_median':float(np.median(latencies)*1000),'latency_ms_p95':float(np.percentile(latencies,95)*1000),'throughput_images_s':len(truth)/sum(latencies),
        'peak_observed_process_rss_bytes':max(rss),'hardware':{'machine':platform.machine(),'processor':platform.processor(),'platform':platform.platform(),'cpu_count':psutil.cpu_count(),'torch':str(torch.__version__),'threads':4,'batch_size':1,'device':'cpu','preprocessing_in_timing':False},
        'threshold_selection':selection or checkpoint.get('threshold_selection'),'selective_metrics':{'threshold':checkpoint.get('threshold'),'accepted_count':int((scores>=checkpoint['threshold']).sum()),'coverage':float((scores>=checkpoint['threshold']).mean()),'accepted_accuracy':float(np.mean(truth[scores>=checkpoint['threshold']]==pred[scores>=checkpoint['threshold']])) if (scores>=checkpoint['threshold']).any() else None} if checkpoint.get('threshold') is not None else None,'misclassifications':[{'path':row['path'],'true':dataset.classes[int(y)],'predicted':dataset.classes[int(p)],'score':float(s)} for row,y,p,s in zip(dataset.rows,truth,pred,scores) if y!=p]}
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True);(out/'metrics.json').write_text(json.dumps(report,indent=2))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(max(6,len(dataset.classes)*.3),max(5,len(dataset.classes)*.3)))
    ax.imshow(report['confusion_matrix'],cmap='Greens');ax.set_xlabel('Predicted class index');ax.set_ylabel('True class index');fig.tight_layout();fig.savefig(out/'confusion.png');plt.close(fig)
    print(json.dumps({k:report[k] for k in ('split','samples','accuracy','macro_f1','development_only')},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('checkpoint');p.add_argument('--split',choices=['val','test','external'],default='test');p.add_argument('--output',required=True);p.add_argument('--select-threshold',action='store_true');evaluate(p.parse_args())
