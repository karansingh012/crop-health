import json
import numpy as np
import pytest
import torch
from PIL import Image
from ml.models import build_model,NAMES
from ml.prepare import prepare
from backend.app.services.inference import predict,load_model

def test_model_shapes_and_backward():
    torch.set_num_threads(2)
    for name in NAMES:
        model=build_model(name,3);x=torch.rand(2,3,128,128);y=model(x)
        assert y.shape==(2,3);y.sum().backward()
        assert all(p.grad is not None for p in model.parameters())

def test_split_duplicate_exclusion(tmp_path):
    rng=np.random.default_rng(42)
    for c in ['a','b']:
        directory=tmp_path/c;directory.mkdir()
        for i in range(20):Image.fromarray(rng.integers(0,255,(64,64,3),dtype=np.uint8)).save(directory/f'{i}.png')
    (tmp_path/'a'/'duplicate.png').write_bytes((tmp_path/'a'/'0.png').read_bytes())
    manifest=prepare(tmp_path,tmp_path/'manifest.json',development=True)
    assert len(manifest['duplicates_removed'])==1
    assert manifest['split_counts']=={'train':32,'val':4,'test':4}
    hashes=[x['sha256'] for x in manifest['images']];assert len(hashes)==len(set(hashes))

def test_real_tensor_inference_and_development_rejection(tmp_path,monkeypatch):
    # Random weights ONLY exercise service wiring. They are never installed in the application.
    path=tmp_path/'test.pt';model=build_model('lightweight',2)
    checkpoint={'state_dict':model.state_dict(),'architecture':'lightweight','classes':['a','b'],'trained':True,'development_only':True,'threshold':None,'preprocessing':{'size':128,'mean':[.485,.456,.406],'std':[.229,.224,.225]}}
    torch.save(checkpoint,path);monkeypatch.setenv('MODEL_PATH',str(path));load_model.cache_clear()
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:predict(Image.new('RGB',(128,128)))
    assert exc.value.status_code==503
    checkpoint['development_only']=False;torch.save(checkpoint,path);load_model.cache_clear()
    result=predict(Image.fromarray(np.random.default_rng(22).integers(0,255,(128,128,3),dtype=np.uint8)))
    assert result['status']=='uncertain' and 0<=result['score']<=1
    assert result['label'] in ['a','b'];load_model.cache_clear()

def test_external_or_test_threshold_tuning_rejected(tmp_path):
    from argparse import Namespace
    from ml.evaluate import evaluate
    path=tmp_path/'checkpoint.pt';torch.save({'classes':['a','b']},path)
    for split in ['test','external']:
        with pytest.raises(ValueError,match='validation'):
            evaluate(Namespace(checkpoint=str(path),select_threshold=True,split=split))

def test_conflicting_duplicate_labels_fail(tmp_path):
    image=Image.fromarray(np.random.default_rng(99).integers(0,255,(64,64,3),dtype=np.uint8))
    for label in ['a','b']:
        (tmp_path/label).mkdir();image.save(tmp_path/label/'same.png')
    with pytest.raises(ValueError,match='Conflicting labels'):
        prepare(tmp_path,tmp_path/'manifest.json')
