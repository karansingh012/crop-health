import json
from pathlib import Path
HINDI=json.loads((Path(__file__).resolve().parents[3]/'shared'/'hi.json').read_text())
def translate(text,language='en'):
    return HINDI.get(text,text) if language=='hi' else text
CLASSES=json.loads((Path(__file__).resolve().parents[3]/'shared'/'class-hi.json').read_text())
def translate_class(label,language='en'):
    if not label:return translate('No prediction',language)
    if '___' not in label:return translate(label.replace('_',' '),language)
    crop,disease=label.split('___',1)
    if language=='hi':
        name=next((value for key,value in CLASSES['crops'].items() if crop.startswith(key)),crop.replace('_',' '))
        return name+' · '+CLASSES['diseases'].get(disease,disease.replace('_',' '))
    return crop.replace('_',' ')+' · '+disease.replace('_',' ')
