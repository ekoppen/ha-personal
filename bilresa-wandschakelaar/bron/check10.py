import sys;sys.path.insert(0,'.')
import numpy as np, trimesh, io
from cad10 import *
from cad9 import UNIT_DY, stem_top, nub_cup_assembled, BTN_Y9, NUB_EFFECTIVE
from cad import pocket_outline, cyl_y
def tilt(m,d): return m.translate((0,0,-AXLE_Z)).rotate((d,0,0)).translate((0,0,AXLE_Z))
v=lambda a,b:round((a^b).volume(),3)
def rt(m):
    g=m.to_mesh(); t=trimesh.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=False)
    b=io.BytesIO(); t.export(b,file_type='stl'); b.seek(0); return trimesh.load(b,file_type='stl').is_watertight
for name in (sys.argv[1:] or list(LAYOUTS)):
    L=LAYOUTS[name]
    B=base(L); M=mount_plate(L); P=panels(L)
    bats=Manifold();pcb=Manifold();chocs=Manifold();btns=Manifold();heads=Manifold()
    for xu in L['units']:
        for yb in (13.5,32.45): bats+=cyl_y(-22.4+UNIT_DY,22.6+UNIT_DY,xu-(yb-22.95),0,5.2)
        pcb+=pocket_outline().offset(-0.25).extrude(1.4).translate((xu,UNIT_DY,-3.45))
        for y in (-BTN_Y9,BTN_Y9): btns+=cyl_z(xu,y,1.5,-2.0,NUB_EFFECTIVE-0.6)
    for (xc,yc) in L['chocs']:
        chocs+=box(xc-7.5,xc+7.5,yc-7.5,yc+7.5,PLATE_Z1,1.35)+box(xc-2.8,xc+2.8,yc-2,yc+2,1.35,stem_top())
    for (x,y) in L['base_screws']: heads+=cyl_z(x,y,2.8,PLATE_Z1,PLATE_Z1+3.0)
    print(f'== {name}: STL basis {rt(B)} montage {rt(M)} panelen {[rt(p) for p in P]} | basis∩montage {v(B,M)}')
    for d in (-2.5,0,2.5):
        Pt=[tilt(p,d) if L['slots'][i] is not None else p for i,p in enumerate(P)]
        s=lambda X: round(sum(v(p,X) for p in Pt),3)
        print(f'  kantel {d:+.1f}: ∩basis {s(B)} ∩batt {s(bats)} ∩PCB {s(pcb)} ∩choc {s(chocs)} ∩M3kop {s(heads)} paneel∩paneel {round(sum(v(Pt[i],Pt[i+1]) for i in range(len(Pt)-1)),3)}')
    # blind: pootjes rusten net boven de plaat
    for i,sl in enumerate(L['slots']):
        if sl is None:
            print('  blindplaat: speling pootje-plaat 0.15 mm; ∩basis', v(P[i],B))
