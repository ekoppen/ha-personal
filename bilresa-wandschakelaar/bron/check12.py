import sys;sys.path.insert(0,'.')
import numpy as np, trimesh
from cad12 import *
from cad9 import AXLE_Z
v=lambda a,b:round((a^b).volume(),3)
def ok(m):
    g=m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=True).is_watertight
def tilt(m,d): return m.translate((0,0,-AXLE_Z)).rotate((d,0,0)).translate((0,0,AXLE_Z))
for name,L in LAYOUTS.items():
    B=base(L);M=mount_plate(L);P=panels(L)
    print(name,'watertight',ok(B),ok(M),[ok(p) for p in P],'B∩M',v(B,M))
    for d in (-2.5,0,2.5):
        print(' kantel',d,'wip∩basis',v(tilt(P[0],d),B),'wip∩venster',v(tilt(P[0],d),P[1]))
    for deg in (-ROT_DEG,0,ROT_DEG):
        R=ring_dummy(L,deg)
        print(f' ring {deg:+}°: ∩basis {v(R,B)} ∩bakje {v(R,M)} ∩venster {v(R,P[1])}')
    # centraalplaat past door venster
    xs=L['socket']; cp=box(xs-27.5,xs+27.5,-27.5,27.5,PLATE_Z0+LIP_T,3)
    print(' centraalplaat 55 ∩ basis',v(cp,B),'∩venster',v(cp,P[1]))
    print(' bakje: hoogte verhoging', PLATE_Z0-RING_T-(WALL_Z+MP_T))
