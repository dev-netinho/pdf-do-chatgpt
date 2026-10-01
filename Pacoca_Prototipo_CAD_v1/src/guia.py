from pathlib import Path
import re,html
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
from pypdf import PdfReader,PdfWriter
ROOT=Path(__file__).resolve().parents[1]
TMP=ROOT/'tmp';TMP.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('DVS','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVS-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DVS',normal='DVS',bold='DVS-Bold',italic='DVS',boldItalic='DVS-Bold')
blue=colors.HexColor('#153b52');red=colors.HexColor('#ae2929')
W,H=landscape(A4);c=canvas.Canvas(str(TMP/'figuras.pdf'),pagesize=(W,H));c.setTitle('Paçoca - protótipo CAD para validação')
panels=[('montagem.png','Módulo isolado - arquitetura manual','CAD sólido e fonte paramétrica. Tampa removida na vista para mostrar o interior.'),('cartucho_fora.png','Reposição e retirada do cartucho','Comporta fechada fora da máquina. Fechar em 180° antes de retirar o pino do dock.'),('comporta_detalhe.png','Comporta em U - apoio lateral do corpo','Os garfos sustentam o corpo; o pino limita o curso. Pontas de embalagem não são apoios.'),('cortes_0_90_180.png','Cortes reais do CAD - 0°, 90° e 180°','O produto cabe em um só berço. Topo sólido sustenta o estoque durante transporte.'),('sequencia_duas_entregas.png','Duas entregas - sequência pretendida','Retorno e queda antecipada da próxima embalagem ainda exigem ensaio.'),('explodida.png','Montagem explodida','Peças nomeadas no STEP e no guia. Ferragens comerciais têm dimensões a confirmar.')]
for i,(img,title,sub) in enumerate(panels,1):
 c.setFillColor(blue);c.setFont('DVS-Bold',18);c.drawString(30,H-35,title)
 c.setFont('DVS',10);c.drawString(30,H-55,sub)
 im=Image.open(ROOT/'vistas'/img);iw,ih=im.size
 scale=min((W-45)/iw,(H-105)/ih); ww,hh=iw*scale,ih*scale
 c.drawImage(str(ROOT/'vistas'/img),(W-ww)/2,47+(H-105-hh)/2,ww,hh,preserveAspectRatio=True)
 c.setFont('DVS',8);c.setFillColor(red);c.drawString(30,22,'Protótipo CAD para validação - não pronto para imprimir; embalagem real e retorno não validados.')
 c.setFillColor(blue);c.drawRightString(W-30,22,str(i));c.showPage()
c.save()
styles=getSampleStyleSheet()
styles.add(ParagraphStyle('Texto',fontName='DVS',fontSize=9.4,leading=14,spaceAfter=6,allowWidows=0,allowOrphans=0,textColor=colors.HexColor('#253540')))
styles.add(ParagraphStyle('Titulo',fontName='DVS-Bold',fontSize=18,leading=22,spaceAfter=12,textColor=blue))
styles.add(ParagraphStyle('Secao',fontName='DVS-Bold',fontSize=12.5,leading=16,spaceBefore=12,spaceAfter=7,textColor=blue,keepWithNext=True))
styles.add(ParagraphStyle('Celula',fontName='DVS',fontSize=8.6,leading=11.5,textColor=colors.HexColor('#253540')))
styles.add(ParagraphStyle('Cabecalho',fontName='DVS-Bold',fontSize=8.6,leading=11.5,textColor=colors.white))
styles.add(ParagraphStyle('Codigo',fontName='DVS',fontSize=8.5,leading=12,leftIndent=10,backColor=colors.HexColor('#f1f5f7'),spaceAfter=8))
def fmt(t):
 t=html.escape(t).replace('—','-').replace('–','-')
 t=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t)
 t=re.sub(r'`([^`]+)`',r'<font color="#285a70">\1</font>',t)
 return t
text=(ROOT/'README.md').read_text();lines=text.splitlines();story=[];i=0
while i<len(lines):
 line=lines[i].strip()
 if not line:i+=1;continue
 if line.startswith('```'):
  i+=1;block=[]
  while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
  story.append(Paragraph('<br/>'.join(fmt(x) for x in block),styles['Codigo']));i+=1;continue
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].strip().startswith('|'):
   row=[v.strip() for v in lines[i].strip().strip('|').split('|')]
   if not all(re.match(r'^:?-+:?$',v) for v in row):rows.append(['Qtd.' if v=='Quantidade' else v for v in row])
   i+=1
  widths=([335,170] if len(rows[0])==2 else [55,117,33,300])
  data=[[Paragraph(fmt(v),styles['Cabecalho'] if j==0 else styles['Celula']) for v in row] for j,row in enumerate(rows)]
  table=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
  table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),blue),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f4f6')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.5,blue)]))
  story.append(table);story.append(Spacer(1,8));continue
 if line.startswith('# '):story.append(Paragraph(fmt(line[2:]),styles['Titulo']))
 elif line.startswith('## '):story.append(Paragraph(fmt(line[3:]),styles['Secao']))
 else:
  # Markdown is line-based here; bullets/steps already contain complete paragraphs.
  if line.startswith('- '):line='• '+line[2:]
  story.append(Paragraph(fmt(line),styles['Texto']))
 i+=1

def foot(c,doc):
 c.setFont('DVS',8);c.setFillColor(blue);c.drawString(42,25,'Paçoca | protótipo CAD para validação');c.drawRightString(A4[0]-42,25,str(doc.page+len(panels)))
 docwidth=A4[0]-84;c.setStrokeColor(colors.HexColor('#ced9df'));c.line(42,38,42+docwidth,38)
doc=SimpleDocTemplate(str(TMP/'texto.pdf'),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=52)
doc.build(story,onFirstPage=foot,onLaterPages=foot)
w=PdfWriter()
for f in ['figuras.pdf','texto.pdf']:
 for page in PdfReader(TMP/f).pages:w.add_page(page)
w.add_metadata({'/Title':'Paçoca - Protótipo CAD para validação','/Author':'Codex','/Subject':'Sólidos paramétricos, montagem, impressão e verificação de limites mecânicos'})
with open(ROOT/'Guia_Pacoca_CAD.pdf','wb') as f:w.write(f)
print('PDF',len(w.pages),'páginas')
