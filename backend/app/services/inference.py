import io, os, warnings, pickle, hashlib
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError
from fastapi import HTTPException
from .guidance import guidance
Image.MAX_IMAGE_PIXELS=20_000_000
MAX_BYTES=8*1024*1024

def decode_image(data):
    if not data or len(data)>MAX_BYTES: raise HTTPException(413,'Image must be between 1 byte and 8 MB')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            im=Image.open(io.BytesIO(data))
            if im.format not in ('JPEG','PNG','WEBP'): raise ValueError('Unsupported image format')
            im.load()
            im=ImageOps.exif_transpose(im).convert('RGB')
        if min(im.size)<64: raise ValueError('Use an image at least 64 pixels in each dimension')
        return im
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning):
        raise HTTPException(422,'Cannot decode image. Upload a valid JPEG, PNG or WebP (at least 64 x 64).')

def quality(image):
    gray=image.convert('L').resize((128,128))
    brightness=ImageStat.Stat(gray).mean[0]
    variation=ImageStat.Stat(gray).stddev[0]
    messages=[]
    if brightness<25 or brightness>235: messages.append('Lighting may hide important symptoms.')
    if variation<8: messages.append('Very low contrast; retake a detailed leaf photograph.')
    return messages

@lru_cache(maxsize=1)
def load_model(path):
    import torch
    from ml.models import build_model
    checkpoint=torch.load(path,map_location='cpu',weights_only=True)
    if not checkpoint.get('trained') or checkpoint.get('development_only'):
        raise ValueError('Checkpoint is not approved for real inference')
    classes=checkpoint['classes']
    if not isinstance(classes,list) or len(classes)<2 or len(set(classes))!=len(classes) or not all(isinstance(c,str) for c in classes):
        raise ValueError('Invalid ordered class mapping')
    expected={'size':128,'mean':[.485,.456,.406],'std':[.229,.224,.225]}
    if checkpoint.get('preprocessing')!=expected:
        raise ValueError('Unsupported preprocessing configuration')
    threshold=checkpoint.get('threshold')
    if threshold is not None and not 0<=threshold<=1:raise ValueError('Invalid threshold')
    checkpoint['artifact_sha256']=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    model=build_model(checkpoint['architecture'],len(classes))
    model.load_state_dict(checkpoint['state_dict'])
    model.eval()
    return model,checkpoint

def predict(image,crop=None):
    path=os.getenv('MODEL_PATH','')
    checks=quality(image)
    if not path or not Path(path).is_file():
        return {'status':'model_unavailable','label':None,'score':None,'quality':checks,
                'message':'No trained checkpoint is installed. Observation saved without a disease prediction.', 'guidance':guidance(crop=crop)}
    try:
        import torch
        from ml.data import transform
        model,checkpoint=load_model(path)
        if checks:
            return {'status':'uncertain','label':None,'score':None,'quality':checks,
                    'message':'Image quality is too low for a useful assessment. Retake a clear leaf photo.',
                    'model':checkpoint['architecture'],'artifact_sha256':checkpoint['artifact_sha256'],
                    'guidance':guidance(crop=crop)}
        with torch.inference_mode():
            scores=model(transform(False)(image).unsqueeze(0)).softmax(1)[0]
        if not torch.isfinite(scores).all():raise ValueError('Non-finite model outputs')
        score,index=scores.max(0)
        score=float(score)
        label=checkpoint['classes'][int(index)]
        threshold=checkpoint.get('threshold')
        uncertain=threshold is None or score<threshold or bool(checks)
        return {'status':'uncertain' if uncertain else 'classified','label':label,'score':score,
                'score_interpretation':'Uncalibrated model softmax score, not a probability of disease.',
                'research_note':('Research preview: trained on a limited PlantVillage subset; field reliability is not established.' if checkpoint.get('training_scope')=='plantvillage_pilot' else None),
                'threshold':threshold,'quality':checks,'model':checkpoint['architecture'],'artifact_sha256':checkpoint['artifact_sha256'],
                'message':'Please retake the image or seek expert advice.' if uncertain else 'Possible class match; confirm with an expert.',
                'guidance':guidance(label,crop),'ood_warning':'Unsupported crops and non-plant images are not reliably detected.'}
    except (ValueError,KeyError,RuntimeError,OSError,ImportError,pickle.UnpicklingError,EOFError) as exc:
        import logging
        logging.getLogger(__name__).exception('Checkpoint load or inference failure')
        raise HTTPException(503,'Model configuration invalid. Contact the administrator.') from exc
