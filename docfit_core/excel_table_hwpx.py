"""표 모델을 표그림판 HWPX 생성기에 연결하는 어댑터."""
from __future__ import annotations

import tempfile
from pathlib import Path
from defusedxml import ElementTree as ET
from . import table_sketch

HP='http://www.hancom.co.kr/hwpml/2011/paragraph'

def to_hwpx(model, path):
    rows=model['rows']; nrows=len(rows); ncols=model['col_count']
    widths=[max(1, max((c.get('width',0) for r in rows for i,c in enumerate(r) if i==col),default=0)) for col in range(ncols)]
    total=sum(widths) or ncols
    cols=[round(10000*w/total) for w in widths]
    sketch={'grid':{'cols':ncols,'rows':nrows,'cell_mm':5}, 'lines':[], 'texts':[], 'fills':[]}
    for y,row in enumerate(rows):
        for x,c in enumerate(row):
            sketch['texts'].append({'x':x,'y':y,'text':c['text'],'bold':c['bold'],'align':c['align']})
            if c.get('fill'): sketch['fills'].append({'x1':x,'y1':y,'x2':x+1,'y2':y+1,'color':c['fill']})
    # Grid fixture lines ensure every cell is bounded.
    for x in range(ncols+1): sketch['lines'].append({'x1':x,'y1':0,'x2':x,'y2':nrows})
    for y in range(nrows+1): sketch['lines'].append({'x1':0,'y1':y,'x2':ncols,'y2':y})
    # HWP HTML 열 너비가 있으면 열 비율에 반영한다.
    document=table_sketch.to_hwpx(sketch,path)
    # 기존 생성기는 칸별 병합을 선 지도로 계산하므로 해당 경계선을 제거한다.
    # HWPX 병합은 모델의 행/열 span 메타데이터를 직접 덮어쓴다.
    import zipfile
    with zipfile.ZipFile(document) as z:
        files={name:z.read(name) for name in z.namelist()}
    root=ET.fromstring(files['Contents/section0.xml'])
    table=root.find('.//{%s}tbl'%HP)
    if table is None: raise ValueError('표 HWPX를 만들지 못했습니다.')
    sz=table.find('{%s}sz'%HP)
    from .table_sketch import UNIT_MM
    table_width=int(sz.get('width','0')); unit=[round(table_width*w/total) for w in widths]
    edges=[0]
    for w in unit: edges.append(edges[-1]+w)
    sz.set('width',str(edges[-1]))
    cells=table.findall('.//{%s}tc'%HP)
    for cell in cells:
        addr=cell.find('{%s}cellAddr'%HP); span=cell.find('{%s}cellSpan'%HP)
        if addr is None or span is None: continue
        y=int(addr.get('rowAddr','0')); x=int(addr.get('colAddr','0'))
        if y<nrows and x<ncols:
            src=rows[y][x]
            span.set('rowSpan',str(src['rowspan'])); span.set('colSpan',str(src['colspan']))
            csz=cell.find('{%s}cellSz'%HP)
            if csz is not None: csz.set('width',str(edges[min(ncols,x+src['colspan'])]-edges[x]))
            sub=cell.find('{%s}subList'%HP)
            if sub is not None: sub.set('vertAlign','CENTER')
            fill=src.get('fill')
            if fill:
                refs=ET.fromstring(files['Contents/header.xml'])
                bfill=refs.find('.//{http://www.hancom.co.kr/hwpml/2011/head}borderFills')
                if bfill is not None:
                    nextid=max((int(v.get('id','0')) for v in bfill),default=0)+1
                    node=ET.SubElement(bfill,'{http://www.hancom.co.kr/hwpml/2011/head}borderFill',{'id':str(nextid),'threeD':'0','shadow':'0','centerLine':'NONE','breakCellSeparateLine':'0'})
                    for side in ('left','right','top','bottom'):
                        ET.SubElement(node,'{http://www.hancom.co.kr/hwpml/2011/head}'+side+'Border',{'type':'SOLID','width':'0.12 mm','color':'#000000'})
                    brush=ET.SubElement(node,'{http://www.hancom.co.kr/hwpml/2011/core}fillBrush')
                    ET.SubElement(brush,'{http://www.hancom.co.kr/hwpml/2011/core}winBrush',{'faceColor':fill,'hatchColor':'#000000','alpha':'0'})
                    cell.set('borderFillIDRef',str(nextid))
                    files['Contents/header.xml']=ET.tostring(refs,encoding='utf-8',xml_declaration=True)
    files['Contents/section0.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(document,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items(): z.writestr(name,data)
    return document
