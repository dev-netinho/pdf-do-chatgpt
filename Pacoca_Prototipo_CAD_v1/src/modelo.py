"""Protótipo CAD para validação. CadQuery 2.7; mm. Fonte paramétrica, não STEP histórico.
X: movimento na vista frontal; Y: eixo horizontal/comprimento do produto; Z: altura.
Rodar: python src/modelo.py [--output caminho] [--params arquivo.json]
"""
import cadquery as cq
from cadquery import exporters
from pathlib import Path
import json, math, argparse

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((Path(__file__).with_name('parametros.json')).read_text())

def box(x0,x1,y0,y1,z0,z1):
    return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).translate(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)).val()
def cyl_y(r,y0,y1,x=0,z=0):
    return cq.Solid.makeCylinder(r,y1-y0,cq.Vector(x,y0,z),cq.Vector(0,1,0))
def cyl_x(r,x0,x1,y=0,z=0):
    return cq.Solid.makeCylinder(r,x1-x0,cq.Vector(x0,y,z),cq.Vector(1,0,0))
def union(*a):
    s=a[0]
    for t in a[1:]: s=s.fuse(t)
    return s.clean()
def cut(s,*a):
    for t in a: s=s.cut(t)
    return s.clean()
def dshaft(r,y0,y1,flat,z):
    return cut(cyl_y(r,y0,y1,z=z),box(flat,r+2,y0-1,y1+1,z-r-2,z+r+2))
def ellipse_y(rx,rz,y0,y1,x,z):
    # ellipse is an analytic sketch, extruded along horizontal Y.
    plane=cq.Plane(origin=(x,y0,z),xDir=(1,0,0),normal=(0,1,0))
    return cq.Workplane(plane).ellipse(rx,rz).extrude(y1-y0).val()
def package(p,margin=False):
    rx=p['corpo_largura']/2+(p['folga_lateral'] if margin else 0)
    rz=p['corpo_profundidade']/2+(p['folga_vertical'] if margin else 0)
    L=p['corpo_comprimento']; T=p['ponta_comprimento']
    s=ellipse_y(rx,rz,-L/2,L/2,0,0)
    # Twisted ends approximated by tapered ellipses; retained as test envelope.
    tr=p['ponta_raio']+(max(p['folga_lateral'],p['folga_vertical']) if margin else 0)
    for sign in [-1,1]:
        plane=cq.Plane(origin=(0,sign*L/2,0),xDir=(1,0,0),normal=(0,sign,0))
        tail=(cq.Workplane(plane).ellipse(rx,rz).workplane(offset=T).ellipse(tr,tr).loft(combine=True)).val()
        s=s.fuse(tail)
    return s.clean()

def build(p):
    global P
    P=p
    rx=p['corpo_largura']/2+p['folga_lateral']
    rz=p['corpo_profundidade']/2+p['folga_vertical']
    R=p['raio_roda']; Z=p['altura_eixo']; pc=R-rz
    pocket=max(rx,rz)+2.0
    length=p['corpo_comprimento']+2*p['ponta_comprimento']
    slotL=length+2*p['folga_axial']; W=slotL+4.0
    outer=R+p['folga_aro']+p['espessura_aro']
    feedhalf=rx+2.5; dep=slotL+2
    cx=feedhalf+8; cy=dep/2+5
    gate_z=Z+R+1.2; gate_t=p['espessura_comporta']; gap=p['meia_abertura_comporta']
    assert gap<rx, 'Comporta nao retém envelope: abertura central >= corpo.'
    assert gate_z+gate_t < Z+R+rz-math.sqrt(rz*rz*(1-gap*gap/(rx*rx))), 'INTERFERENCIA: comporta × estoque a 180 graus.'
    zclosed=gate_z+gate_t+rz*math.sqrt(1-(gap/rx)**2)
    zbase=Z+R+.2; ztop=zbase+p['altura_cartucho']
    assert zclosed+(p['unidades_estoque']-1)*2*rz+rz<ztop, 'Cartucho curto.'
    deriv=dict(rx=rx,rz=rz,R=R,Z=Z,pc=pc,pocket=pocket,W=W,slotL=slotL,length=length,
               outer=outer,feedhalf=feedhalf,cx=cx,cy=cy,gate_z=gate_z,zclosed=zclosed,zbase=zbase,ztop=ztop)
    parts={}; notes=[]
    # Rotor: central round trough, radial open throat, smaller axial end reliefs.
    wheel=cyl_y(R,-W/2,W/2,z=Z)
    coreL=p['corpo_comprimento']+3
    cutters=[]
    for lo,hi,rr in [(-coreL/2,coreL/2,pocket),(-slotL/2,-coreL/2,pocket-1.0),(coreL/2,slotL/2,pocket-1.0)]:
        cutters += [cyl_y(rr,lo,hi,z=Z+pc),box(-rr,rr,lo,hi,Z+pc,Z+R+4)]
    wheel=cut(wheel,*cutters,dshaft(p['raio_eixo']+.25,-W/2-1,W/2+1,4.25,Z))
    lips=[]
    for e in wheel.Edges():
        a=e.positionAt(0); b=e.positionAt(1)
        if e.geomType()=='LINE' and abs(a.y-b.y)>5 and abs(a.x-b.x)<.01 and a.z>Z+pc+5 and abs(a.x)>10:
            lips.append(e)
    wheel=cq.Workplane(obj=wheel).newObject(lips).fillet(p['arredondamento_roda']).val()
    notes.append('Bordas axiais da boca arredondadas em 0.6 mm; pontas flexíveis e início da recarga no retorno ainda exigem ensaio.')
    parts['04_roda']=wheel
    # Cartridge shell open top/bottom, wide base guides, rear gate passage.
    cart=cut(box(-cx,cx,-cy,cy,zbase,ztop),box(-feedhalf,feedhalf,-dep/2,dep/2,zbase-1,ztop+1))
    # Inspection/loading slit: width less than packaged body diameter.
    cart=cut(cart,box(-8,8,-cy-1,-dep/2+.1,gate_z+10,ztop-5))
    gatehalf=cx-5
    cart=cut(cart,box(-gatehalf-.3,gatehalf+.3,-cy-1,cy+1,gate_z-.3,gate_z+gate_t+.3))
    lugz=gate_z+3.8
    for sign in [-1,1]:
        a,b=(cx,cx+4) if sign==1 else (-cx-4,-cx)
        cart=cart.fuse(box(a,b,-30,30,lugz,lugz+30))
        cart=cart.cut(cyl_x(2.25,a-1,b+1,z=lugz+15))
    # M2 keeper pin enters elongated gate slot; both stroke ends are captive.
    pinx=gatehalf-2; piny=dep/2+.5
    cart=cut(cart,cq.Solid.makeCylinder(1.15,12,cq.Vector(pinx,piny,gate_z-2),cq.Vector(0,0,1)))
    parts['01_cartucho']=cart.clean()
    # Real U gate: two prongs support body off-center, tail ends remain free.
    gate=box(-gatehalf,gatehalf,-cy+1,cy+1,gate_z,gate_z+gate_t)
    gate=cut(gate,box(-gap,gap,-cy-1,dep/2+1,gate_z-1,gate_z+gate_t+1))
    gate=union(gate,box(-8,8,cy,cy+17,gate_z,gate_z+gate_t+3))
    # Stop tab at rear hits rear face when gate closes; opening is removable at end.
    gate=union(gate,box(-gatehalf,gatehalf,cy,cy+3,gate_z+gate_t,gate_z+gate_t+3))
    slot_y0=piny-p['curso_comporta']; slot_y1=piny
    slot=union(box(pinx-1.25,pinx+1.25,slot_y0,slot_y1,gate_z-1,gate_z+gate_t+1),
        cq.Solid.makeCylinder(1.25,gate_t+2,cq.Vector(pinx,slot_y0,gate_z-1),cq.Vector(0,0,1)),
        cq.Solid.makeCylinder(1.25,gate_t+2,cq.Vector(pinx,slot_y1,gate_z-1),cq.Vector(0,0,1)))
    gate=cut(gate,slot)
    parts['02_comporta_U']=gate
    keeper=union(cq.Solid.makeCylinder(1,9.2,cq.Vector(pinx,piny,gate_z-1.2),cq.Vector(0,0,1)),
                 cq.Solid.makeCylinder(2.1,1.8,cq.Vector(pinx,piny,gate_z-3),cq.Vector(0,0,1)))
    parts['16_retencao_comporta_M2']=keeper
    # Dock: base, rear bearing, two pillars, female lug channels and brackets.
    dock=union(box(-87,87,-57,58,0,6),box(-77,77,43,49,6,Z+outer+4))
    dock=cut(dock,cyl_y(p['raio_eixo']+p['folga_eixo'],42,50,z=Z))
    # Rear viewing apertures, retaining hub bridge and plate connections.
    for x0,x1 in [(-57,-14),(14,57)]:
        dock=cut(dock,box(x0,x1,42,50,40,130))
    for sign in [-1,1]:
        a,b=(78,86) if sign==1 else (-86,-78)
        dock=union(dock,box(a,b,-49,49,6,lugz+28))
        a,b=(cx,cx+9) if sign==1 else (-cx-9,-cx)
        rail=box(a,b,-35,35,lugz-4,lugz+24)
        sa,sb=(cx-.1,cx+4.4) if sign==1 else (-cx-4.4,-cx+.1)
        rail=cut(rail,box(sa,sb,-30.4,30.4,lugz,lugz+30))
        rail=cut(rail,cyl_x(2.25,a-1,b+1,z=lugz+15))
        bridge=box(min(a,sign*82),max(b,sign*82),31,38,lugz+18,lugz+24)
        dock=union(dock,rail,bridge)
    mountpoints=[(59,Z+33),(-59,Z+33),(59,Z-33),(-59,Z-33)]
    for x,z in mountpoints: dock=cut(dock,cyl_y(1.7,42,50,x,z))
    # Support for endpoint guide plate at front, attached to side pillars/base.
    dock=union(dock,box(-77,-69,-55,-43,6,Z+outer),box(69,77,-55,-43,6,Z+outer),box(-77,77,-55,-43,6,12))
    # Two solid standoffs for 0/180 stop plate mount; connected via left bridge.
    dock=union(dock,box(-77,-4,-55,-49,Z-43,Z-37),box(-77,-4,-55,-49,Z+37,Z+43),box(-12,-4,-55,-43,Z-43,Z+43))
    for zz in [Z-40,Z+40]: dock=cut(dock,cyl_y(1.7,-56,-42,-8,zz))
    for x in [-78,78]:
        for y in [-45,45]:
            dock=cut(dock,cq.Solid.makeCylinder(2.5,8,cq.Vector(x,y,-1),cq.Vector(0,0,1)))
    dock=cut(dock,cyl_y(8.5,-56,-41,z=Z),
             box(-gatehalf-.5,gatehalf+.5,42,50,gate_z-.5,gate_z+gate_t+3.5))
    dock=cut(dock,box(77.5,87,-41,41,6.1,40))
    for xx in [-16,65]:
        for yy in [-30,30]:
            dock=cut(dock,cq.Solid.makeCylinder(1.7,8,cq.Vector(xx,yy,-1),cq.Vector(0,0,1)))
            nut=cq.Workplane('XY').polygon(6,6.4).extrude(2.6).val().translate((xx,yy,0))
            dock=cut(dock,nut)
    parts['03_dock']=dock.clean()
    # Stationary cage, top wide enough to clear dock/cart; internal feed width still 38.
    aro=cut(cyl_y(outer,-W/2-2,W/2+2,z=Z),cyl_y(R+p['folga_aro'],-W/2-3,W/2+3,z=Z))
    topwindow=cx+10
    aro=cut(aro,box(-topwindow,topwindow,-W/2-3,W/2+3,Z+pc-5,Z+outer+1),
            box(-22,22,-W/2-3,W/2+3,Z-outer-1,Z-pc+5))
    for x,z in mountpoints:
        aro=union(aro,cyl_y(4.0,W/2+1,43,x,z))
        aro=cut(aro,cyl_y(1.7,-W/2-3,-W/2+8,x,z),cyl_y(1.7,W/2-2,44,x,z))
    # Rear bridge unites both retention arcs without blocking the bottom exit.
    aro=union(aro,box(-70,70,W/2+3,43,Z-8,Z+8),
              box(64,72,W/2+1,43,Z-12,Z+12),box(-72,-64,W/2+1,43,Z-12,Z+12))
    aro=cut(aro,cyl_y(p['raio_eixo']+p['folga_eixo'],W/2+2,44,z=Z))
    parts['05_aro_fixo']=aro
    cover=cyl_y(outer+.5,-42,-38,z=Z)
    cover=cut(cover,cyl_y(p['raio_eixo']+p['folga_eixo'],-43,-37,z=Z))
    for x in [-48,-36,-24,24,36,48]: cover=cut(cover,box(x-3,x+3,-43,-37,Z-25,Z+43))
    for x,z in mountpoints: cover=cut(cover,cyl_y(1.7,-43,-37,x,z))
    cover=cut(cover,box(-topwindow,topwindow,-43,-37,Z+pc-5,Z+outer+2))
    parts['10_tampa_inspecao']=cover
    parts['06_eixo_D']=dshaft(p['raio_eixo'],-69,58,4.0,Z)
    # Two split-free shaft collars, held by a radial M3 grub/set screw.
    for name,y0 in [('11_colar_frontal',-47),('12_colar_traseiro',49)]:
        collar=cut(cyl_y(8,y0,y0+5,z=Z),cyl_y(5.2,y0-1,y0+6,z=Z),cyl_x(1.6,3,10,y0+2.5,Z))
        parts[name]=collar
    # Crank hub/arm/handle post; D socket and explicit pin for travel stops.
    crank=union(cyl_y(11,-68,-62,z=Z),box(-6,6,-68,-62,Z,Z+44),cyl_y(6,-87,-66,z=Z+44),cyl_y(3,-62,-55.4,z=Z+32))
    crank=cut(crank,dshaft(5.25,-69,-61,4.25,Z),cyl_x(1.6,3,12,-65,Z))
    crank=cut(crank,cyl_y(1.7,-88,-74,z=Z+44))
    parts['07_manivela']=crank
    knob=cut(cyl_y(9,-89,-70,z=Z+44),cyl_y(6.3,-90,-69,z=Z+44))
    parts['13_punho']=knob
    # Hard travel stops: semicircular captive pin slot, nominal 0 and 180 degrees.
    stop=cut(cyl_y(43,-59,-55,z=Z),cyl_y(23,-60,-54,z=Z),box(-45,-12,-60,-54,Z-45,Z+45))
    track=cut(cyl_y(35.3,-60,-54,z=Z),cyl_y(28.7,-61,-53,z=Z),box(-37,0,-62,-52,Z-37,Z+37))
    track=union(track,cyl_y(3.3,-60,-54,0,Z+32),cyl_y(3.3,-60,-54,0,Z-32))
    stop=cut(stop,track)
    for zz in [Z-40,Z+40]: stop=cut(stop,cyl_y(1.7,-60,-54,-8,zz))
    parts['14_batentes_0_180']=stop
    # Short chute, attached to base by pillars, sloping in X toward collector.
    x0=-22; x1=96; z0=21; z1=10; chalf=37
    plane=cq.Plane(origin=(0,-chalf,0),xDir=(1,0,0),normal=(0,-1,0))
    # plane local vertical points +Z; normal -Y, extrusion uses positive direction.
    def extrude_xz(poly,ymin,ymax):
        pl=cq.Plane(origin=(0,ymax,0),xDir=(1,0,0),normal=(0,-1,0))
        return cq.Workplane(pl).polyline(poly).close().extrude(ymax-ymin).val()
    chute=extrude_xz([(x0,z0-3),(x1,z1-3),(x1,z1),(x0,z0)],-chalf,chalf)
    for y0,y1 in [(-chalf-3,-chalf),(chalf,chalf+3)]:
        chute=union(chute,extrude_xz([(x0,z0-3),(x1,z1-3),(x1,z1+10),(x0,z0+10)],y0,y1))
    # Foot rails sit on dock base (z=6), holes for M3 fixing.
    for xx in [-16,65]:
        zz=z0+(xx-x0)*(z1-z0)/(x1-x0)
        for yy in [-30,30]:
            foot=box(xx-4,xx+4,yy-5,yy+5,6,zz-2.5)
            foot=cut(foot,cq.Solid.makeCylinder(1.7,25,cq.Vector(xx,yy,5),cq.Vector(0,0,1)))
            chute=union(chute,foot)
            # make screw holes through ramp as well
            chute=cut(chute,cq.Solid.makeCylinder(1.7,25,cq.Vector(xx,yy,5),cq.Vector(0,0,1)))
    for xx in [-16,65]:
        zz=z0+(xx-x0)*(z1-z0)/(x1-x0)
        for yy in [-30,30]:
            chute=cut(chute,cq.Solid.makeCylinder(3.1,5,cq.Vector(xx,yy,zz-3.5),cq.Vector(0,0,1)))
    parts['08_calha']=chute
    tray=cut(box(90,172,-47,47,0,23),box(93,169,-44,44,3,24),box(89,97,-41,41,6.9,24))
    parts['09_bandeja']=tray
    # Printable safety closure screw head + pin; insertion through right lug.
    lock=union(cyl_x(2, cx-1,cx+12,0,lugz+15),cyl_x(5,cx+10,cx+15,0,lugz+15))
    parts['15_pino_cartucho']=lock
    return parts,deriv,notes

COLORS={'01_cartucho':(.72,.75,.78),'02_comporta_U':(.40,.45,.52),'03_dock':(.58,.63,.68),'04_roda':(.05,.45,.85),'05_aro_fixo':(.78,.81,.83),'06_eixo_D':(.40,.43,.46),'07_manivela':(.1,.40,.70),'08_calha':(.7,.74,.78),'09_bandeja':(.67,.71,.75),'10_tampa_inspecao':(.75,.8,.85),'14_batentes_0_180':(.4,.5,.6),'15_pino_cartucho':(.2,.25,.3)}
def state_shapes(parts,d,p,angle=0,gate_open=True,outside=False,second=False,inspection=True):
    shapes={}
    for n,s in parts.items():
        if not inspection and n=='10_tampa_inspecao': continue
        if n=='02_comporta_U' and gate_open: s=s.translate((0,p['curso_comporta'],0))
        if n in ['04_roda','06_eixo_D','07_manivela','13_punho']:
            s=s.rotate((0,0,d['Z']),(0,1,d['Z']),angle)
        if outside and n in ['01_cartucho','02_comporta_U','16_retencao_comporta_M2']: s=s.translate((-150,0,15))
        if outside and n=='15_pino_cartucho': continue
        shapes[n]=s
    pkg=package(p,True)
    stockcount=p['unidades_estoque']
    if outside or not gate_open:
        for i in range(stockcount):
            loc=(-150 if outside else 0,0,d['zclosed']+i*2*d['rz']+(15 if outside else 0))
            shapes[f'REF_estoque_{i+1}']=pkg.translate(loc)
    else:
        selected=2 if second else 1
        if angle<179.9:
            moving=pkg.translate((0,0,d['Z']+d['pc'])).rotate((0,0,d['Z']),(0,1,d['Z']),angle)
        else:
            xx=43; surf=21-(xx+22)*11/118
            moving=pkg.translate((xx,0,surf+d['rz']+0.5))
        shapes[f'REF_entrega_{selected}']=moving
        for i in range(selected+1,stockcount+1):
            z=d['Z']+d['R']+d['rz']+(i-selected-1)*2*d['rz']
            shapes[f'REF_estoque_{i}']=pkg.translate((0,0,z))
        if second: shapes['REF_entregue_1']=pkg.translate((130,0,3+d['rz']+.2))
    return shapes

def make_assembly(shapes,pth):
    a=cq.Assembly(name=pth.stem)
    for name,s in shapes.items():
        col=(1,.42,.06) if 'entrega' in name else ((.94,.69,.20) if name.startswith('REF_') else COLORS.get(name,(.5,.55,.6)))
        a.add(s,name=name,color=cq.Color(*col))
    a.save(str(pth),exportType='STEP',mode='default')

def export_all(out,p):
    out=Path(out); [ (out/x).mkdir(parents=True,exist_ok=True) for x in ['stl','step','verificacao','vistas'] ]
    parts,d,notes=build(p)
    manifest=[]
    for name,s in parts.items():
        assert s.isValid(), 'SOLIDO INVALIDO '+name
        ns=len(s.Solids()); assert ns==1, f'{name}: {ns} solidos (peca desconectada)'
        exporters.export(s,str(out/'step'/f'{name}.step'))
        bb=s.BoundingBox()
        # STL oriented per component; printing transform described in manifest.
        if name=='01_cartucho': print_s=s.translate((0,0,-bb.zmin)); orient='Em pé; topo aberto +Z; suporte localizado nos rasgos da comporta.'
        elif name=='02_comporta_U': print_s=s.translate((0,0,-bb.zmin)); orient='Plana; garfos paralelos à mesa.'
        elif name in ['04_roda','05_aro_fixo','06_eixo_D','07_manivela','10_tampa_inspecao','11_colar_frontal','12_colar_traseiro','13_punho','14_batentes_0_180']:
            print_s=s.rotate((0,0,0),(1,0,0),90)
            b=print_s.BoundingBox(); print_s=print_s.translate((0,0,-b.zmin)); orient='Face axial sobre a mesa (Y do CAD passa a Z); manivela requer suporte no pino/haste.'
        elif name=='15_pino_cartucho':
            print_s=s.rotate((0,0,0),(0,1,0),-90); b=print_s.BoundingBox(); print_s=print_s.translate((0,0,-b.zmin)); orient='Cabeça sobre a mesa; eixo vertical.'
        else: print_s=s.translate((0,0,-bb.zmin)); orient='Base sobre a mesa; suporte localizado conforme rampas/ponte.'
        exporters.export(print_s,str(out/'stl'/f'{name}.stl'),tolerance=p['tolerancia_stl'],angularTolerance=.1)
        manifest.append(dict(peca=name,solido_valido=True,solidos=ns,volume_mm3=s.Volume(),dimensoes_mm=[bb.xlen,bb.ylen,bb.zlen],orientacao=orient))
    states=[('00_cartucho_fora',0,False,True,False),('01_encaixado_fechado',0,False,False,False),('02_carga_0',0,True,False,False),('03_giro_90',90,True,False,False),('04_entrega_180',180,True,False,False),('05_segunda_carga_0',0,True,False,True),('06_segunda_entrega_180',180,True,False,True)]
    for name,ang,go,outs,sec in states:
        s=state_shapes(parts,d,p,ang,go,outs,sec)
        make_assembly(s,out/'step'/f'{name}_montagem.step')
    make_assembly(state_shapes(parts,d,p),out/'montagem_completa.step')
    expl={}
    for name,s in parts.items():
        shifts={'01_cartucho':(0,0,115),'02_comporta_U':(0,110,100),'04_roda':(0,-115,0),'05_aro_fixo':(0,-45,0),'06_eixo_D':(0,-210,0),'07_manivela':(0,-250,0),'10_tampa_inspecao':(0,-150,0),'08_calha':(0,0,-35),'09_bandeja':(35,0,0),'14_batentes_0_180':(0,-195,0),'11_colar_frontal':(0,-175,0),'12_colar_traseiro':(0,80,0),'13_punho':(0,-280,0),'15_pino_cartucho':(45,0,70),'16_retencao_comporta_M2':(0,0,90)}
        expl[name]=s.translate(shifts.get(name,(0,0,0)))
    make_assembly(expl,out/'vista_explodida.step')
    # True solid cuts Y=0: front half removed. All component names retained.
    half=box(-500,500,0,500,-500,600)
    for ang in [0,90,180]:
        sh=state_shapes(parts,d,p,ang)
        section={n+'_corte':s.intersect(half) for n,s in sh.items() if s.intersect(half).Volume()>1e-5}
        make_assembly(section,out/'step'/f'corte_Y0_{ang:03d}.step')
    result=dict(unidades='mm',cadquery=cq.__version__,parametros=p,derivados=d,pecas=manifest,notas=notes)
    (out/'verificacao'/'solidos.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps(dict(status='exportado',pecas=len(parts),derivados=d,notas=notes),ensure_ascii=False))
    return parts,d,notes
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--output',default=str(ROOT)); ap.add_argument('--params',default=str(Path(__file__).with_name('parametros.json')))
    args=ap.parse_args(); p=json.loads(Path(args.params).read_text()); export_all(args.output,p)
