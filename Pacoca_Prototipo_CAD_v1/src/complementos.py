from modelo import *
import numpy as np,json
parts,d,n=build(P)
# Empty return, without inventing a second unit held in the cavity.
for ang in [90,25,0]:
    sh=state_shapes(parts,d,P,ang)
    sh={k:v for k,v in sh.items() if not k.startswith('REF_')}
    for i in [2,3]: sh[f'REF_estoque_{i}']=package(P,True).translate((0,0,d['Z']+d['R']+d['rz']+(i-2)*2*d['rz']))
    sh['REF_entregue_1']=package(P,True).translate((130,0,3+d['rz']+.2))
    make_assembly(sh,ROOT/'step'/f'04b_retorno_vazio_{ang:03d}.step')
sh=state_shapes(parts,d,P,0,second=True)
for nm in ['REF_entrega_2','REF_estoque_3']:
    sh[nm]=sh[nm].translate((0,0,d['rz']))
make_assembly(sh,ROOT/'step'/'05b_recarga_intermediaria_gravidade.step')
# Free space for a future motor, only a reference envelope, never in STL or necessary for operation.
exporters.export(box(-40,40,61,116,d['Z']-40,d['Z']+40),str(ROOT/'step'/'REF_espaco_futuro_motor.step'))
# Extraction with gate closed, stock supported first by rotor, then by the moving U gate.
from verificar import overlap
checks=[]
for lift in np.linspace(0,45,16):
    cart=parts['01_cartucho'].translate((0,0,float(lift)));gate=parts['02_comporta_U'].translate((0,0,float(lift)))
    stock=package(P,True).translate((0,0,max(d['Z']+d['R']+d['rz'],d['zclosed']+float(lift))))
    wheel=parts['04_roda'].rotate((0,0,d['Z']),(0,1,d['Z']),180)
    checks.append({'elevacao_mm':float(lift),'cartucho_roda':overlap(cart,wheel),'comporta_roda':overlap(gate,wheel),'estoque_roda':overlap(stock,wheel),'comporta_estoque':overlap(gate,stock),'cartucho_dock':overlap(cart,parts['03_dock'])})
(ROOT/'verificacao'/'retirada.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
# Vertical fall from bottom outlet until first contact on chute, then a pose on ramp already checked.
checks=[]
for zz in np.linspace(d['Z']-d['pc'],21+d['rz']+.5,20):
    unit=package(P,True).translate((0,0,float(zz)))
    checks.append({'centro_z_mm':float(zz),'roda':overlap(unit,parts['04_roda'].rotate((0,0,d['Z']),(0,1,d['Z']),180)),'aro':overlap(unit,parts['05_aro_fixo']),'dock':overlap(unit,parts['03_dock']),'calha':overlap(unit,parts['08_calha'])})
(ROOT/'verificacao'/'queda_saida.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print('Complementos e verificações gerados')
