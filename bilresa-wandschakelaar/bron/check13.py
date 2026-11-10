import sys;sys.path.insert(0,'.')
import numpy as np, trimesh
from cad13 import *
from cad9 import AXLE_Z, choc_pocket
from cad import box
v=lambda a,b:round((a^b).volume(),3)
def ok(m):
    g=m.to_mesh(); return trimesh.Trimesh(np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),process=True).is_watertight
def tilt(m,d): return m.translate((0,0,-AXLE_Z)).rotate((d,0,0)).translate((0,0,AXLE_Z))
L=LAYOUTS['C2_enkel_plus_stopcontact_kopp']; xs=L['socket']
B=base(L);M=mount_plate(L);W=wip(L)
print('watertight',ok(B),ok(M),ok(W),[ok(vensterplaat(L,t)) for t in LIP_TS],'B∩M',v(B,M))
for t in LIP_TS:
    V=vensterplaat(L,t)
    s=f' randje {t}: V∩basis {v(V,B)} V∩bakje {v(V,M)}'
    for d in (-2.5,0,2.5): s+=f' wip{d:+}∩V {v(tilt(W,d),V)}'
    plate=box(xs-27.5,xs+27.5,-27.5,27.5,LIP_Z0+t,ROCKER_Z1)   # centraalplaat t/m bovenkant
    s+=f' centraalplaat∩V {v(plate,V)}'
    print(s)
for d in (-2.5,0,2.5): print(' wip',d,'∩basis',v(tilt(W,d),B))
for deg in (-ROT_DEG,0,ROT_DEG):
    R=ring_dummy(L,deg); V=vensterplaat(L,1.5)
    print(f' ring {deg:+}°: ∩basis {v(R,B)} ∩bakje {v(R,M)} ∩venster {v(R,V)}')
print(' kraag-hoogte boven bakjesbodem',COLLAR_TOP-(WALL_Z+MP_T),' stopcontact hoger dan origineel ~',COLLAR_TOP-WALL_Z)
