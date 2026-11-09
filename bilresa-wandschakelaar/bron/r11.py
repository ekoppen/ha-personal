import sys;sys.path.insert(0,'.')
import numpy as np
from manifold3d import Manifold
from cad11 import *
from cad9 import cup_assembled, nub_cup_assembled, UNIT_DY
from cad import pocket_outline, box, cyl_y
from cad8 import MP_T
from render import render
from PIL import Image
def it(m,c):
    g=m.to_mesh(); return (np.asarray(g.vert_properties)[:,:3],np.asarray(g.tri_verts),c)
imgs=[]
for name,L in LAYOUTS.items():
    B=base(L);M=mount_plate(L);P=panels(L)
    pcb=Manifold();bat=Manifold();ch=Manifold()
    for xu in L['units']:
        pcb+=pocket_outline().offset(-0.25).extrude(1.4).translate((xu,UNIT_DY,-3.45))
        for yb in (13.5,32.45): bat+=cyl_y(-22.4+UNIT_DY,22.6+UNIT_DY,xu-(yb-22.95),0,5.2)
    for (xc,yc) in L['chocs']: ch+=box(xc-7.5,xc+7.5,yc-7.5,yc+7.5,PLATE_Z1-2.2,1.35)
    sock=Manifold()
    if L['socket'] is not None:
        xs=L['socket']; sock=box(xs-35.5,xs+35.5,-35.5,35.5,WALL_Z+MP_T,WALL_Z+MP_T+1)+box(xs-27.5,xs+27.5,-27.5,27.5,WALL_Z+MP_T+1,1.5)-cyl_z(xs,0,19,-1,5)
    # opengewerkt: links compleet, wip 30mm opgetild
    items=[it(M,(150,150,160)),it(B,(235,232,225)),it(pcb,(60,120,70)),it(bat,(200,170,60)),it(ch,(120,80,50)),it(sock,(250,250,250))]
    for i,p in enumerate(P):
        items.append(it(p.translate((0,0,30 if L['slots'][i] is not None else 0)),(250,250,248)))
    imgs.append(render(items,el=-50,az=20,W=1100,H=800))
W=sum(i.width for i in imgs); out=Image.new('RGB',(W,800),(245,243,238)); x=0
for i in imgs: out.paste(i,(x,0)); x+=i.width
out.save('r11.png'); print('ok')
