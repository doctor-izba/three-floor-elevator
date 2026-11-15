"""Preserve DOCX original image pixels in Word's PDF without changing page layout.

Word's PDF exporter downsamples images independently of DOCX compression flags.
Replace only the PDF image streams with lossless RGB originals embedded in DOCX.
Text, drawing transforms, captions, page geometry and links remain unchanged.
"""
from pathlib import Path
from io import BytesIO
from datetime import datetime, timezone
import hashlib, json, zlib
from docx import Document
from PIL import Image, ImageChops, ImageStat
from pypdf import PdfWriter, PdfReader
from pypdf.generic import NameObject, NumberObject

root=Path(__file__).resolve().parent
out=root/'deliverables'
doc=Document(out/'Final_Project_Report_EE2401_Yesbol_Kali.docx')
originals=[]
for shape in doc.inline_shapes:
    rid=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
    part=doc.part.related_parts[rid]
    pic=Image.open(BytesIO(part.blob)).convert('RGB')
    originals.append({'name':str(part.partname),'image':pic,'sha256':hashlib.sha256(part.blob).hexdigest()})
pdf=out/'Final_Project_Report_EE2401_Yesbol_Kali.pdf'
writer=PdfWriter(clone_from=pdf)
remaining=list(originals)
records=[]
for page_number,page in enumerate(writer.pages,1):
    for image in list(page.images):
        displayed=image.image.convert('RGB')
        ratio=displayed.width/displayed.height
        candidates=[s for s in remaining if abs(s['image'].width/s['image'].height-ratio)<0.01]
        assert candidates,(page_number,displayed.size)
        thumb=displayed.resize((192,192),Image.Resampling.LANCZOS)
        def difference(source):
            diff=ImageChops.difference(thumb,source['image'].resize((192,192),Image.Resampling.LANCZOS))
            return sum(ImageStat.Stat(diff).rms)/3
        source=min(candidates,key=difference)
        score=difference(source)
        assert score<12,(page_number,source['name'],score)
        remaining.remove(source)
        original=source['image']
        obj=image.indirect_reference.get_object()
        obj.clear()
        obj.update({NameObject('/Type'):NameObject('/XObject'),NameObject('/Subtype'):NameObject('/Image'),NameObject('/Width'):NumberObject(original.width),NameObject('/Height'):NumberObject(original.height),NameObject('/ColorSpace'):NameObject('/DeviceRGB'),NameObject('/BitsPerComponent'):NumberObject(8),NameObject('/Filter'):NameObject('/FlateDecode')})
        obj._data=zlib.compress(original.tobytes(),9)
        if hasattr(obj,'decoded_self'):obj.decoded_self=None
        records.append({'page':page_number,'source':source['name'],'source_sha256':source['sha256'],'previous_pixels':list(displayed.size),'embedded_pixels':list(original.size),'match_rms':round(score,4),'rgb_sha256':hashlib.sha256(original.tobytes()).hexdigest()})
assert not remaining and len(records)==20
temporary=pdf.with_suffix('.full-resolution.pdf')
with temporary.open('wb') as stream:writer.write(stream)
# Verify decoded PDF image pixels exactly equal the embedded DOCX originals.
readback=PdfReader(temporary)
for record in records:
    candidates=[im.image.convert('RGB') for im in readback.pages[record['page']-1].images]
    assert any(im.size==tuple(record['embedded_pixels']) and hashlib.sha256(im.tobytes()).hexdigest()==record['rgb_sha256'] for im in candidates),record
assert len(readback.pages)==31
temporary.replace(pdf)
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'result':'PASS','method':'Lossless PDF image streams from original DOCX image pixels; no resampling, sharpening or generated details','images':records,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}
(out/'Evidence/full_resolution_images.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'result':'PASS','images':len(records),'pdf_bytes':pdf.stat().st_size,'HMI_pixels':[r['embedded_pixels'] for r in records if r['page'] in (25,26,31)]},indent=2))
