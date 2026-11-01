import numpy as np
from PIL import Image
def rot(el,az):
    a,e=np.radians(az),np.radians(el)
    Rz=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    Rx=np.array([[1,0,0],[0,np.cos(e),-np.sin(e)],[0,np.sin(e),np.cos(e)]])
    return Rx@Rz
def render(items,el=-55,az=25,W=1400,H=1000,pad=40,bg=(245,243,238)):
    R=rot(el,az)
    allv=np.vstack([(R@v.T).T for v,f,c in items])
    lo,hi=allv[:,:2].min(0),allv[:,:2].max(0)
    s=min((W-2*pad)/(hi[0]-lo[0]),(H-2*pad)/(hi[1]-lo[1]))
    off=np.array([W/2,H/2])-s*(lo+hi)/2
    img=np.zeros((H,W,3));img[:]=np.array(bg)/255;zb=np.full((H,W),-1e9)
    L=np.array([-.4,.5,.75]);L/=np.linalg.norm(L)
    for v,f,col in items:
        pv=(R@v.T).T; p2=pv[:,:2]*s+off; p2[:,1]=H-p2[:,1]
        tri=pv[f]; n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); nn=np.linalg.norm(n,axis=1)+1e-12; n/=nn[:,None]
        shade=0.30+0.62*np.clip(n@L,0,1)+0.10*np.clip(n[:,2],0,1)
        col=np.array(col)/255
        for t in range(len(f)):
            P=p2[f[t]];Z=pv[f[t],2]
            x0,x1=int(max(P[:,0].min(),0)),int(min(P[:,0].max()+1,W));y0,y1=int(max(P[:,1].min(),0)),int(min(P[:,1].max()+1,H))
            if x0>=x1 or y0>=y1: continue
            xs,ys=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
            (ax,ay),(bx,by),(cx,cy)=P
            d=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(d)<1e-9: continue
            w0=((by-cy)*(xs-cx)+(cx-bx)*(ys-cy))/d; w1=((cy-ay)*(xs-cx)+(ax-cx)*(ys-cy))/d; w2=1-w0-w1
            m=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
            if not m.any(): continue
            z=w0*Z[0]+w1*Z[1]+w2*Z[2]
            sub=zb[y0:y1,x0:x1]; upd=m&(z>sub)
            sub[upd]=z[upd]; img[y0:y1,x0:x1][upd]=np.clip(col*shade[t],0,1)
    # edge outline via depth discontinuity
    gy=np.abs(np.diff(zb,axis=0,prepend=zb[:1]));gx=np.abs(np.diff(zb,axis=1,prepend=zb[:,:1]))
    edge=(np.maximum(gx,gy)>1.2/ s*10)
    img[edge]=img[edge]*0.45
    return Image.fromarray((img*255).astype(np.uint8))
