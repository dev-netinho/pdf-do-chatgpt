"""Vistas derivadas dos mesmos sólidos CAD, sem imagem generativa."""
import os
os.environ.setdefault('MPLBACKEND','Agg')
import cadquery as cq, numpy as np, math
from pathlib import Path
from modelo import build,P,ROOT,state_shapes,COLORS,package,box
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle
from PIL import Image,ImageDraw,ImageFont
parts,d,notes=build(P)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def wirepoints(w):
    edges=list(w.Edges()); paths=[]
    while edges:
        e=edges.pop(0); a=e.positionAt(0); b=e.positionAt(1)
        n=2 if e.geomType()=='LINE' else 90
        pts=[e.positionAt(float(t)).toTuple() for t in np.linspace(0,1,n)]
        path=pts
        while edges:
            end=np.array(path[-1]); best=None
            for i,e2 in enumerate(edges):
                aa=np.array(e2.positionAt(0).toTuple());bb=np.array(e2.positionAt(1).toTuple())
                for rev,v in [(False,aa),(True,bb)]:
                    dist=np.linalg.norm(v-end)
                    if best is None or dist<best[0]: best=(dist,i,rev)
            if best[0]>.001:break
            _,i,rev=best;e2=edges.pop(i);n=2 if e2.geomType()=='LINE' else 90
            ts=np.linspace(1,0,n) if rev else np.linspace(0,1,n)
            path.extend([e2.positionAt(float(t)).toTuple() for t in ts][1:])
        paths.append(path)
    return paths

def sectionpoly(ax,s,color,alpha=1):
    try:sec=cq.Workplane('XZ').add(s).section().val()
    except Exception:return
    loops=[]
    for w in sec.Wires():
        for path in wirepoints(w):
            xz=np.array([[v[0],v[2]] for v in path]); area=abs(np.sum(xz[:,0]*np.roll(xz[:,1],-1)-np.roll(xz[:,0],-1)*xz[:,1]))/2
            if area>1e-6:loops.append((area,xz))
    loops.sort(key=lambda a:-a[0])
    # Each solid here has one outer contour + optional inner contours.
    for i,(_,xz) in enumerate(loops):
        # Complex support may have several separate section faces; use outlines for it.
        fill=color if i==0 else 'white'
        ax.add_patch(Polygon(xz,closed=True,facecolor=fill,edgecolor='#293947',linewidth=.7,alpha=alpha))

def drawsection(ax,angle=0,second=False,returning=False,closed=False):
    sh=state_shapes(parts,d,P,angle,not closed,False,second)
    if returning:
        sh={k:v for k,v in sh.items() if not k.startswith('REF_')}
        for i in [2,3]: sh['REF_estoque_'+str(i)]=package(P,True).translate((0,0,d['Z']+d['R']+d['rz']+(i-2)*2*d['rz']))
    # Draw only the Y=0 cross-section; rear/frame bodies not projected through product.
    names=['03_dock','09_bandeja','08_calha','05_aro_fixo','01_cartucho','02_comporta_U','04_roda','06_eixo_D']
    for name in names:
        sectionpoly(ax,sh[name],COLORS.get(name,(.5,.55,.6)))
    for n,s in sh.items():
        if n.startswith('REF_'):
            c='#f37928' if 'entrega' in n else '#e9b751'
            sectionpoly(ax,s,c)
            bb=s.BoundingBox();label=n.split('_')[-1]
            ax.text((bb.xmin+bb.xmax)/2,(bb.zmin+bb.zmax)/2,label,ha='center',va='center',weight='bold',fontsize=11)
    ax.plot([-22,22],[d['gate_z'],d['gate_z']],ls='--',lw=.8,color='#63717b')
    ax.set_aspect('equal');ax.set_xlim(-90,180);ax.set_ylim(-5,320);ax.axis('off')
    if returning:
        ax.add_patch(Circle((14,d['Z']+d['R']-1),10,fill=False,color='#c82926',lw=2))
        ax.annotate('Risco no retorno',xy=(14,d['Z']+d['R']-1),xytext=(43,235),color='#bc2222',fontsize=9,arrowprops=dict(arrowstyle='->',color='#bc2222'))
    if angle==0 and not closed:
        ax.annotate('',xy=(0,d['Z']+d['pc']+18),xytext=(0,d['Z']+d['pc']+45),arrowprops=dict(arrowstyle='->',color='#208448',lw=2))

# 0/90/180 front technical sections.
fig,axs=plt.subplots(1,3,figsize=(15,6.5),facecolor='white')
for ax,ang in zip(axs,[0,90,180]):
    drawsection(ax,ang);ax.set_title(f'Corte Y=0 | {ang}°',fontsize=15,weight='bold',color='#143950')
fig.suptitle('PAÇOCA | Uma cavidade, estoque orientado e saída livre',fontsize=19,weight='bold')
fig.text(.5,.02,'Envelope de teste: corpo Ø33 × 46 mm + pontas de 8 mm. Corte derivado dos sólidos CAD; não simula atrito.',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.05,1,.94));fig.savefig(ROOT/'vistas'/'cortes_0_90_180.png',dpi=180);plt.close(fig)
# Intended six states including empty return + next unit gravity loading.
fig,axs=plt.subplots(2,3,figsize=(15,12),facecolor='white')
seq=[('1 | Carga da unidade 1',0,False,False),('2 | Giro de uma unidade',90,False,False),('3 | Entrega da unidade 1',180,False,False),('4 | Retorno vazio: risco',25,False,True),('5 | Recarga por gravidade',0,True,False),('6 | Entrega da unidade 2',180,True,False)]
for ax,(title,ang,sec,ret) in zip(axs.flat,seq):
    drawsection(ax,ang,sec,ret);ax.set_title(title,fontsize=13,weight='bold',color='#15374d')
fig.suptitle('SEQUÊNCIA PRETENDIDA | Duas entregas sem tocar no estoque',fontsize=18,weight='bold')
fig.text(.5,.02,'A recarga pode começar antes do batente de 0°: risco de engate no filme flexível ainda aberto para ensaio.',ha='center',fontsize=11,color='#ad2828')
fig.tight_layout(rect=(0,.04,1,.95));fig.savefig(ROOT/'vistas'/'sequencia_duas_entregas.png',dpi=150);plt.close(fig)

def render(shapes,path,title,sub='',camera=None,size=(1600,1200),transparent_cover=False):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(size[0]/100,size[1]/100),dpi=100,facecolor='white')
    ax=fig.add_subplot(111,projection='3d');bounds=[];alltri=[];allcols=[]
    for n,shape in shapes.items():
        if transparent_cover and n=='10_tampa_inspecao':continue
        vs,fs=shape.tessellate(.3,.2)
        vv=np.array([v.toTuple() for v in vs]);ff=np.array(fs);tri=vv[ff]
        normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm=np.linalg.norm(normal,axis=1)
        normal/=np.maximum(norm[:,None],1e-12)
        light=np.array([.45,-.75,.8]);light/=np.linalg.norm(light)
        shade=.62+.38*np.abs(normal@light)
        col=np.array((1,.43,.08) if 'entrega' in n else ((.91,.66,.23) if n.startswith('REF_') else COLORS.get(n,(.45,.50,.55))))
        facecol=np.clip(shade[:,None]*col,0,1)
        alltri.append(tri);allcols.append(facecol)
        bounds.append(vv)
    ax.add_collection3d(Poly3DCollection(np.vstack(alltri),facecolors=np.vstack(allcols),edgecolors='none',linewidths=0,rasterized=True))
    allv=np.vstack(bounds);lo=allv.min(0);hi=allv.max(0);mid=(hi+lo)/2;span=hi-lo
    ax.set_xlim(lo[0]-8,hi[0]+8);ax.set_ylim(lo[1]-8,hi[1]+8);ax.set_zlim(lo[2]-8,hi[2]+8);ax.set_box_aspect(span+16)
    ax.view_init(elev=22,azim=-58);ax.set_proj_type('ortho');ax.set_axis_off()
    fig.subplots_adjust(left=0,right=1,bottom=0,top=.9)
    fig.text(.025,.965,title,fontsize=19,weight='bold',color='#143950')
    fig.text(.025,.935,sub,fontsize=12,color='#475a65')
    fig.savefig(path,dpi=100,facecolor='white');plt.close(fig)

sh=state_shapes(parts,d,P);render(sh,ROOT/'vistas'/'montagem.png','Protótipo CAD para validação | Paçoca','Tampa removida nesta vista para leitura; motor não instalado.',transparent_cover=True)
sh=state_shapes(parts,d,P,0,False,True);render(sh,ROOT/'vistas'/'cartucho_fora.png','Cartucho fora | Comporta em U fechada','Estoque suspenso pelas laterais do corpo; abrir a base só após encaixar e travar.')
expl={}
for n,s in parts.items():
    delta={'01_cartucho':(0,0,110),'02_comporta_U':(0,120,100),'16_retencao_comporta_M2':(0,0,100),'04_roda':(0,-120,0),'05_aro_fixo':(0,-45,0),'06_eixo_D':(0,-245,0),'07_manivela':(0,-280,0),'10_tampa_inspecao':(0,-160,0),'08_calha':(0,0,-35),'09_bandeja':(40,0,0),'14_batentes_0_180':(0,-210,0),'11_colar_frontal':(0,-200,0),'12_colar_traseiro':(0,80,0),'13_punho':(0,-320,0),'15_pino_cartucho':(45,0,70)}
    expl[n]=s.translate(delta.get(n,(0,0,0)))
render(expl,ROOT/'vistas'/'explodida.png','Vista explodida | Peças separadas','Nomes e numeração das peças estão na lista de montagem.',camera=((520,-730,410),(10,-70,180)))
# Enlarged isolated U shutter details.
closed={'01_cartucho':parts['01_cartucho'],'02_comporta_U':parts['02_comporta_U'],'16_retencao_comporta_M2':parts['16_retencao_comporta_M2']}
# Show only bottom 30 mm of cartridge, with a rigid margin envelope on the U gate.
closed['01_cartucho']=closed['01_cartucho'].intersect(box(-60,60,0,80,d['zbase']-3,d['gate_z']+22))
closed['REF_estoque_1']=package(P,True).translate((0,0,d['zclosed']))
render(closed,ROOT/'vistas'/'comporta_detalhe.png','Comporta em U | Fechada e retida em rasgo','Parede frontal seccionada. Pino M2 limita o curso; apoios sob as laterais.',camera=((150,-170,130),(0,0,d['gate_z'])),size=(1400,1000))
print('Vistas criadas')
