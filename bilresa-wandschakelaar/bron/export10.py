import sys;sys.path.insert(0,'.')
import numpy as np, trimesh, os, shutil
from cad10 import *
from cad9 import nub_cup, pen_cup, CUP_T, NUB_CUP_T
def tm(m):
    g=m.to_mesh(); t=trimesh.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=True); assert t.is_watertight; return t
def onbed(m,flip=False):
    if flip: m=m.rotate((180,0,0))
    b=m.bounding_box(); return m.translate((-(b[0]+b[3])/2,-(b[1]+b[4])/2,-b[2]))
def pack(items,bed=250,gap=4):
    x=y=rowh=0; out=[]
    for n,t in items:
        w,h=t.extents[:2]
        if x+w>bed: x=0; y+=rowh+gap; rowh=0
        t=t.copy(); t.apply_translation((x+w/2-bed/2,y+h/2-bed/2,0)); out.append((n,t)); x+=w+gap; rowh=max(rowh,h)
    assert y+rowh<=bed+1,'past niet'; return out
def scene(items,fn):
    sc=trimesh.Scene()
    for n,t in pack(items): sc.add_geometry(t,node_name=n,geom_name=n)
    sc.export(fn)
root='out10'; shutil.rmtree(root,ignore_errors=True); os.makedirs(root)
labc={0.4:'dun',0.8:'normaal',1.2:'dik'}
pcups={t:tm(onbed(pen_cup(t))) for t in CUP_T}
ncups={t:tm(onbed(nub_cup(t))) for t in NUB_CUP_T}
for name,L in LAYOUTS.items():
    d=f'{root}/{name}'; os.makedirs(d+'/STL')
    B=tm(onbed(base(L))); M=tm(onbed(mount_plate(L)))
    R=[tm(onbed(p,True)) for p in panels(L)]
    B.export(f'{d}/STL/1_basis.stl'); M.export(f'{d}/STL/2_montagebakje.stl')
    for i,r in enumerate(R): r.export(f'{d}/STL/3_'+('blindplaat' if L['slots'][i] is None else 'wip')+f'_{i+1}.stl')
    for t,m in pcups.items(): m.export(f'{d}/STL/4_choc_dopje_{labc[t]}.stl')
    for t,m in ncups.items(): m.export(f'{d}/STL/5_knop_dopje_{labc[t]}.stl')
    nc=len(L['chocs']); nn=2*len(L['units'])
    scene([('basis',B)],f'{d}/{name}_deel1_basis.3mf')
    scene([('montagebakje',M)],f'{d}/{name}_deel2_montagebakje.3mf')
    items=[(('blindplaat' if L['slots'][i] is None else 'wip')+str(i+1),r) for i,r in enumerate(R)]
    items+=[(f'choc_dopje_normaal_{j+1}',pcups[0.8]) for j in range(nc)]+[(f'knop_dopje_normaal_{j+1}',ncups[0.8]) for j in range(nn)]
    if nc>0: scene(items,f'{d}/{name}_deel3_wippen_dopjes_normaal.3mf')
    if nc==0:
        scene(items,f'{d}/{name}_deel3_blindplaat.3mf'); print(name,'ok'); continue
    extra=[(f'choc_dopje_{labc[t]}_{j+1}',pcups[t]) for t in (0.4,1.2) for j in range(nc)]+[(f'knop_dopje_{labc[t]}_{j+1}',ncups[t]) for t in (0.4,1.2) for j in range(nn)]
    scene(extra,f'{d}/{name}_deel4_reserve_dopjes_dun_dik.3mf')
    print(name,'ok')
