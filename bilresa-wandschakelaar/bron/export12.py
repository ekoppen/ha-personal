import sys;sys.path.insert(0,'.')
import os, shutil
import cad12
from cad12 import *
from cad9 import nub_cup, pen_cup, CUP_T, NUB_CUP_T
from export10 import tm, onbed, scene
root='out12'; shutil.rmtree(root,ignore_errors=True); os.makedirs(root)
labc={0.4:'dun',0.8:'normaal',1.2:'dik'}
pcups={t:tm(onbed(pen_cup(t))) for t in CUP_T}; ncups={t:tm(onbed(nub_cup(t))) for t in NUB_CUP_T}
for name,L in LAYOUTS.items():
    d=f'{root}/{name}'; os.makedirs(d+'/STL')
    # pasproefjes
    T=[(f'pasproef_randje_{t}mm',tm(onbed(test_piece(t)))) for t in LIP_TS]
    for n,t in T: t.export(f'{d}/STL/0_{n}.stl')
    scene(T,f'{d}/{name}_deel0_pasproefjes_randje.3mf')
    for t in LIP_TS:
        cad12.LIP_T=t
        B=tm(onbed(base(L))); B.export(f'{d}/STL/1_basis_randje_{t}mm.stl')
        scene([('basis',B)],f'{d}/{name}_deel1_basis_randje_{t}mm.3mf')
    cad12.LIP_T=1.5
    M=tm(onbed(mount_plate(L))); M.export(f'{d}/STL/2_montagebakje.stl')
    scene([('montagebakje',M)],f'{d}/{name}_deel2_montagebakje.3mf')
    R=[tm(onbed(p,True)) for p in panels(L)]
    names=['wip' if s is not None else 'vensterplaat_stopcontact' for s in L['slots']]
    for n,r in zip(names,R): r.export(f'{d}/STL/3_{n}.stl')
    for t,m in pcups.items(): m.export(f'{d}/STL/4_choc_dopje_{labc[t]}.stl')
    for t,m in ncups.items(): m.export(f'{d}/STL/5_knop_dopje_{labc[t]}.stl')
    nc=len(L['chocs']); nn=2*len(L['units'])
    items=list(zip(names,R))+[(f'choc_dopje_normaal_{j+1}',pcups[0.8]) for j in range(nc)]+[(f'knop_dopje_normaal_{j+1}',ncups[0.8]) for j in range(nn)]
    scene(items,f'{d}/{name}_deel3_wip_vensterplaat_dopjes_normaal.3mf')
    extra=[(f'choc_dopje_{labc[t]}_{j+1}',pcups[t]) for t in (0.4,1.2) for j in range(nc)]+[(f'knop_dopje_{labc[t]}_{j+1}',ncups[t]) for t in (0.4,1.2) for j in range(nn)]
    scene(extra,f'{d}/{name}_deel4_reserve_dopjes_dun_dik.3mf')
    print(name,'ok')
