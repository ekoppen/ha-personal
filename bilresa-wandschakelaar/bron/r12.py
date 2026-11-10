import sys;sys.path.insert(0,'.')
import numpy as np
from manifold3d import Manifold
from cad12 import *
from cad import box
from render import render
from PIL import Image
def it(m,c):
    g=m.to_mesh(); return (np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),c)
L=LAYOUTS['C2_enkel_plus_stopcontact_kopp']; xs=L['socket']
B=base(L);M=mount_plate(L);P=panels(L);R=ring_dummy(L,3.0)
cp=box(xs-27.5,xs+27.5,-27.5,27.5,PLATE_Z0+LIP_T,3)-cyl_z(xs,0,19,-1,5)
# 1: uit elkaar, schuin van onderen/voren
ex=[it(M,(150,150,160)),it(R.translate((0,0,6)),(190,190,195)),it(B.translate((0,0,14)),(235,232,225)),
    it(cp.translate((0,0,40)),(252,252,252)),it(P[1].translate((0,0,28)),(250,250,248)),it(P[0].translate((0,0,28)),(250,250,248))]
a=render(ex,el=-55,az=20,W=1100,H=800)
# 2: doorsnede door het stopcontact (y>0 weg)
cut=box(-500,500,-500,0,-500,500)
sec=[it(M^cut,(150,150,160)),it(R^cut,(120,120,130)),it(B^cut,(235,232,225)),it(cp^cut,(250,250,255)),it(P[1]^cut,(250,250,248))]
b=render(sec,el=-80,az=0,W=1100,H=800)
out=Image.new('RGB',(2200,800),(245,243,238)); out.paste(a,(0,0)); out.paste(b,(1100,0)); out.save('r12.png'); print('ok')
cut=box(xs-46,xs+46,-500,0,-500,500)
sec=[it(M^cut,(150,150,165)),it(R^cut,(90,90,100)),it(B^cut,(235,232,225)),it(cp^cut,(255,255,255)),it(P[1]^cut,(250,250,248))]
c=render(sec,el=-88,az=180,W=1400,H=520,bg=(245,243,238)); c.save('r12_doorsnede.png')
a.save('r12_overzicht.png'); print('ok2')
