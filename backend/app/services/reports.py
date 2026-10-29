from io import BytesIO
from pathlib import Path
import re
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .localization import translate, translate_class
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import HexColor
from .storage import storage

pdfmetrics.registerFont(TTFont('NotoDevanagari',str(Path(__file__).resolve().parents[2]/'fonts'/'NotoSansHindi-Regular.ttf')))

pdfmetrics.registerFont(TTFont('NotoLatin',str(Path(__file__).resolve().parents[2]/'fonts'/'NotoSans-Regular.ttf')))

def render_report(scan,field=None,language='en'):
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer,title='Crop health observation',author='Canopy Crop Health',rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=42)
    styles=getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName='NotoDevanagari'
        style.shaping=True
        if hasattr(style,'leading'):style.leading=max(style.leading,style.fontSize*1.4)
    tr=lambda text:translate(text,language)
    styles['Title'].textColor=HexColor('#174b38')
    body=[]
    def markup(text):return escape(str(text))
    def line(text,style='BodyText'):
        body.extend([Paragraph(markup(tr(str(text))),styles[style]),Spacer(1,6)])
    line('CANOPY / CROP HEALTH','Heading2')
    line('Observation report','Title')
    line(f"{tr('Record')} #{scan.id} | {scan.created_at.isoformat()}")
    if field: line(f"{tr('Field')}: {field.name} | {tr('Crop')}: {field.crop}")
    image=Image(str(storage.path(scan.image_key)))
    image._restrictSize(300,150)
    body.extend([image,Spacer(1,16)])
    pred=scan.prediction
    line('Assessment','Heading2')
    line(f"{tr('Status')}: {tr(pred['status'].replace('_',' '))}")
    line(f"{tr('Possible class')}: {translate_class(pred.get('label'),language)}")
    if pred.get('score') is not None: line(f"{tr('Model score')}: {pred['score']:.3f}. {tr('Uncalibrated; not a probability of disease.')}")
    line(pred.get('message',''))
    if pred.get('research_note'):line(pred['research_note'])
    for message in pred.get('quality',[]): line(message)
    line('Field notes','Heading2')
    line(scan.notes or 'No notes recorded.')
    g=pred.get('guidance',{})
    line('Guidance and limitations','Heading2')
    line(g.get('symptoms',''))
    line(g.get('care',''))
    for warning in g.get('warnings',[]): line(warning)
    if g.get('source'):
        body.extend([Paragraph('<link href="'+escape(g['source'],{'"':'&quot;'})+'">'+markup(tr('Agricultural reference ↗').replace(' ↗',''))+'</link>',styles['BodyText']),Spacer(1,6)])
    line('Changes between model predictions alone do not establish progression or recovery.')
    def footer(canvas,doc):
        canvas.setFont('NotoDevanagari',8)
        footer_text=Paragraph(markup(tr('Private observation / Decision support only')),styles['BodyText'])
        footer_text.wrap(450,30)
        footer_text.drawOn(canvas,48,22)
        canvas.drawRightString(547,24,str(doc.page))
    doc.build(body,onFirstPage=footer,onLaterPages=footer)
    return buffer.getvalue()
