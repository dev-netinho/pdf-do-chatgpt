"""Checks independent of tessellation export. No dynamics/contact-friction simulation."""
import struct,json,collections,sys,itertools,math
from pathlib import Path
import numpy as np
from modelo import build,state_shapes,P,ROOT,package

def meshcheck(path):
    data=path.read_bytes(); n=struct.unpack('<I',data[80:84])[0]
    assert len(data)==84+50*n, 'STL não binário / tamanho incorreto'
    rec=np.frombuffer(data, dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')]),offset=84,count=n)
    tri=rec['v'].astype(float); verts,idx=np.unique(np.round(tri.reshape(-1,3),5),axis=0,return_inverse=True); faces=idx.reshape(-1,3)
    edges=collections.defaultdict(list); incident=collections.defaultdict(set)
    deg=0
    for f,t in enumerate(faces):
        if len(set(t))<3:deg+=1
        for v in t: incident[int(v)].add(f)
        for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]: edges[tuple(sorted((int(a),int(b))))].append((f,int(a),int(b)))
    boundary=sum(len(v)==1 for v in edges.values()); nonman=sum(len(v)>2 for v in edges.values())
    orient=sum(len(v)==2 and v[0][1:]==v[1][1:] for v in edges.values())
    adj=collections.defaultdict(set)
    for e,fs in edges.items():
        if len(fs)==2:
            a,b=fs[0][0],fs[1][0]; adj[a].add(b); adj[b].add(a)
    seen=set();comps=0
    for f in range(n):
        if f in seen:continue
        comps+=1;stack=[f];seen.add(f)
        while stack:
            a=stack.pop()
            for b in adj[a]:
                if b not in seen:seen.add(b);stack.append(b)
    badfans=0
    for vertex,fs in incident.items():
        seed=next(iter(fs)); reached={seed};stack=[seed]
        while stack:
            a=stack.pop()
            for b in adj[a]&fs:
                if b not in reached: reached.add(b);stack.append(b)
        if reached!=fs:badfans+=1
    volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
    return dict(arquivo=path.name,triangulos=n,vertices=len(verts),arestas_abertas=boundary,arestas_nao_manifold=nonman,vertices_nao_manifold=badfans,orientacao_inconsistente=orient,triangulos_degenerados=deg,componentes=comps,volume_assinado_mm3=volume,malha_fechada_manifold=(boundary==nonman==badfans==orient==deg==0 and comps==1 and volume>0),limites_mm=[verts.min(0).tolist(),verts.max(0).tolist()])

def overlap(a,b):
    A=a.BoundingBox(); B=b.BoundingBox()
    if any(getattr(A,k+'max')<=getattr(B,k+'min')+1e-5 or getattr(B,k+'max')<=getattr(A,k+'min')+1e-5 for k in ['x','y','z']):return 0.
    return a.intersect(b).Volume()

def main():
    parts,d,notes=build(P); report={'unidades':'mm','malhas':[meshcheck(p) for p in sorted((ROOT/'stl').glob('*.stl'))],'colisoes_estados':[]}
    for angle,go,outside,sec in [(0,False,True,False),(0,False,False,False),(0,True,False,False),(90,True,False,False),(180,True,False,False),(0,True,False,True),(180,True,False,True)]:
        sh=state_shapes(parts,d,P,angle,go,outside,sec)
        for (na,a),(nb,b) in itertools.combinations(sh.items(),2):
            v=overlap(a,b)
            if v>.05: report['colisoes_estados'].append(dict(angulo=angle,comporta_aberta=go,fora=outside,segunda=sec,a=na,b=nb,volume_mm3=v))
    # Intended travel of gate at the delivery stop: supported column at top solid surface.
    pkg=package(P,True); zstock=d['Z']+d['R']+d['rz']; stock=pkg.translate((0,0,zstock))
    sweep=[]
    for dy in np.linspace(0,P['curso_comporta'],16):
        gate=parts['02_comporta_U'].translate((0,float(dy),0))
        row={'curso_mm':float(dy)}
        for name,shape in [('estoque',stock),('roda_180',parts['04_roda'].rotate((0,0,d['Z']),(0,1,d['Z']),180)),('cartucho',parts['01_cartucho']),('aro',parts['05_aro_fixo']),('dock',parts['03_dock'])]:
            row[name]=overlap(gate,shape)
        sweep.append(row)
    report['varredura_comporta_180']=sweep
    # Rotation with one unit inside and stock resting above. No next-unit descent claimed here.
    sweep=[]
    for ang in range(0,181,10):
        wheel=parts['04_roda'].rotate((0,0,d['Z']),(0,1,d['Z']),ang)
        unit=pkg.translate((0,0,d['Z']+d['pc'])).rotate((0,0,d['Z']),(0,1,d['Z']),ang)
        row={'angulo':ang,'roda_estoque':overlap(wheel,stock),'roda_aro':overlap(wheel,parts['05_aro_fixo']),'roda_cartucho':overlap(wheel,parts['01_cartucho']),'unidade_aro':overlap(unit,parts['05_aro_fixo']),'unidade_cartucho':overlap(unit,parts['01_cartucho']),'unidade_estoque':overlap(unit,stock)}
        sweep.append(row)
    report['varredura_transporte']=sweep
    # Gravity descent at the aligned 0-degree throat, with closed gate fully withdrawn.
    descent=[]
    for zz in np.linspace(zstock,d['Z']+d['pc'],18):
        u=pkg.translate((0,0,float(zz)))
        descent.append({'centro_z_mm':float(zz),'roda':overlap(u,parts['04_roda']),'cartucho':overlap(u,parts['01_cartucho']),'comporta_aberta':overlap(u,parts['02_comporta_U'].translate((0,P['curso_comporta'],0)))})
    report['descida_alinhada_0']=descent
    report['retorno']='Não validado dinamicamente. A unidade seguinte pode começar a descer antes de 0°; atrito, pontas flexíveis e captura pela borda precisam de ensaio. Não inferir êxito das poses CAD.'
    (ROOT/'verificacao'/'verificacao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'malhas_validas':sum(m['malha_fechada_manifold'] for m in report['malhas']),'malhas_total':len(report['malhas']),'colisoes_estados':report['colisoes_estados'],'max_comporta':max(max(v for k,v in row.items() if k!='curso_mm') for row in report['varredura_comporta_180']),'max_transporte':max(max(v for k,v in row.items() if k!='angulo') for row in report['varredura_transporte']),'max_descida':max(max(v for k,v in row.items() if k!='centro_z_mm') for row in report['descida_alinhada_0'])},ensure_ascii=False))
if __name__=='__main__':main()
