import sys;sys.path.insert(0,'.')
import os, shutil
from cad13 import *
from cad9 import nub_cup, pen_cup, CUP_T, NUB_CUP_T
from export10 import tm, onbed, scene
root='out13'; shutil.rmtree(root,ignore_errors=True); os.makedirs(root)
labc={0.4:'dun',0.8:'normaal',1.2:'dik'}
pcups={t:tm(onbed(pen_cup(t))) for t in CUP_T}; ncups={t:tm(onbed(nub_cup(t))) for t in NUB_CUP_T}
for name,L in LAYOUTS.items():
    d=f'{root}/{name}'; os.makedirs(d+'/STL')
    T=[(f'pasproef_randje_{t}mm',tm(onbed(test_piece(t)))) for t in LIP_TS]
    for n,t in T: t.export(f'{d}/STL/0_{n}.stl')
    scene(T,f'{d}/{name}_deel0_pasproefjes_randje.3mf')
    B=tm(onbed(base(L))); B.export(f'{d}/STL/1_basis.stl'); scene([('basis',B)],f'{d}/{name}_deel1_basis.3mf')
    M=tm(onbed(mount_plate(L))); M.export(f'{d}/STL/2_montagebakje.stl'); scene([('montagebakje',M)],f'{d}/{name}_deel2_montagebakje.3mf')
    Wp=tm(onbed(wip(L),True)); Wp.export(f'{d}/STL/3_wip.stl')
    for t in LIP_TS:
        V=tm(onbed(vensterplaat(L,t))); V.export(f'{d}/STL/3_vensterplaat_randje_{t}mm.stl')
        scene([('vensterplaat',V)],f'{d}/{name}_deel3b_vensterplaat_randje_{t}mm_RECHTOP.3mf')
    for t,m in pcups.items(): m.export(f'{d}/STL/4_choc_dopje_{labc[t]}.stl')
    for t,m in ncups.items(): m.export(f'{d}/STL/5_knop_dopje_{labc[t]}.stl')
    items=[('wip',Wp)]+[(f'choc_dopje_normaal_{j+1}',pcups[0.8]) for j in range(4)]+[(f'knop_dopje_normaal_{j+1}',ncups[0.8]) for j in range(2)]
    scene(items,f'{d}/{name}_deel3a_wip_dopjes_normaal.3mf')
    extra=[(f'choc_dopje_{labc[t]}_{j+1}',pcups[t]) for t in (0.4,1.2) for j in range(4)]+[(f'knop_dopje_{labc[t]}_{j+1}',ncups[t]) for t in (0.4,1.2) for j in range(2)]
    scene(extra,f'{d}/{name}_deel4_reserve_dopjes_dun_dik.3mf')
    print(name,'ok')
