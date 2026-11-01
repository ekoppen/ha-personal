"""BILRESA wandschakelaar v9
- knopjes op de gemeten plek: ronde kant printplaat -> bovenste knop 14.5 mm, onderste 50 mm
  => printplaten 1.0 mm omlaag, as precies midden tussen de knopjes (beide op 17.75 mm)
- geen losse as meer: elke wip heeft geprinte pinnen (3 mm) die in klemmetjes klikken
  (zijwand + brede dubbele steun in het midden); wip eruit trekken = batterijen wisselen
- drukpunten op de BILRESA-knopjes met verwisselbare dopjes (3 diktes), net als bij de Choc's
Alles verder als v8.4 (basis + montagebakje + Choc's aan de uiteinden).
"""
import numpy as np
from manifold3d import Manifold, CrossSection
import cad8
from cad8 import (box, rslab, cyl_x, cyl_y, cyl_z, chamfered_slab, stadium, ref_unit_block,
                  ref_unit_footprint, choc_pocket, removal_cuts, mount_plate, pen_cup, pen_tip,
                  stem_top, PLATE_Z0, PLATE_Z1, RIM_T, H_OUT, H_IN, RIM_TOP, AXLE_Z, ROCKER_Z0,
                  ROCKER_Z1, ROCKER_GAP, CHOC_Y, PEN_R, CUP_T, CUP_NOM, CUP_LEN, WALL_Z, BOX_PITCH)

UNIT_DY = -1.0          # printplaten 1 mm omlaag -> knopjes symmetrisch rond de as
BTN_Y9 = 17.75          # beide knopjes op 17.75 mm van de as
PIN_R = 1.45            # geprinte scharnierpin 2.9 mm
CLIP_HOLE = 1.57        # gat in klemmetje
CLIP_SLOT = 1.2         # halve opening bovenaan (2.4 mm < 2.9 mm pin -> klikt)
CLIP_TOP = AXLE_Z + 1.35
CENTER_HALF = 2.6       # brede middensteun: 5.2 mm
RIM_CLIP_W = 2.3        # klemmetje tegen de zijwand
LUG_T = 2.0
# drukpunt BILRESA: pin + dopje (zoals bij Choc, maar kleiner)
NUB_PIN_R = 1.25
NUB_CUP_T = (0.4, 0.8, 1.2)
NUB_CUP_NOM = 0.8
NUB_FACE_R = 1.8
NUB_CUP_LEN = 1.8
NUB_EFFECTIVE = 4.6     # gewenste onderkant drukpunt met normaal dopje (v8: 4.6)


def nub_pin_tip():
    return NUB_EFFECTIVE + NUB_CUP_NOM


def nub_cup(t):
    """dopje over het drukpunt: drukvlak 3.6 mm (raakt de koppelknop niet). z=0 = drukvlak."""
    so = NUB_PIN_R + 0.8
    c = cyl_z(0, 0, NUB_FACE_R, 0, t + 0.01) + Manifold.batch_hull([cyl_z(0, 0, NUB_FACE_R, t, t + 0.01),
                                                                    cyl_z(0, 0, so, t + 0.4, t + NUB_CUP_LEN)])
    c -= cyl_z(0, 0, NUB_PIN_R + 0.12, t, t + NUB_CUP_LEN + 1)
    n = NUB_CUP_T.index(t) + 1
    for i in range(n):
        a = i * 360.0 / n
        c -= box(-0.3, 0.3, NUB_PIN_R + 0.45, NUB_PIN_R + 1.2, t + NUB_CUP_LEN - 0.6, t + NUB_CUP_LEN + 1).rotate((0, 0, a))
    return c


def nub_cup_assembled(x, y, t=NUB_CUP_NOM):
    return nub_cup(t).translate((x, y, nub_pin_tip() - t))


# ------------------------------------------------------------------ layouts
def _rk(edges, units):
    return [(edges[i] + ROCKER_GAP, edges[i + 1] - ROCKER_GAP, xu) for i, xu in enumerate(units)]


def _layout(W, units, edges, base_screws, boxes):
    WI = W - 2 * RIM_T
    return dict(W=W, units=units, rockers=_rk(edges, units), edges=edges, rim=(-WI / 2, WI / 2),
                centers=[e for e in edges[1:-1]], base_screws=base_screws, boxes=boxes,
                chocs=[(xu, s * CHOC_Y) for xu in units for s in (-1, 1)])


W1, W2 = 86.2, BOX_PITCH + 86.2
WI1, WI2 = W1 - 2 * RIM_T, W2 - 2 * RIM_T
SCR1 = [(-36.5, -45.0), (36.5, -45.0), (-36.5, 45.0), (36.5, 45.0)]
LAYOUTS = {
    'V1_enkel_1doos': _layout(W1, [0.0], [-WI1 / 2, WI1 / 2], SCR1, [0.0]),
    'V2_dubbel_1doos': _layout(W1, [-20.0, 20.0], [-WI1 / 2, 0.0, WI1 / 2], SCR1, [0.0]),
    'V3_dubbel_2dozen': _layout(W2, [-38.25, 38.25], [-WI2 / 2, 0.0, WI2 / 2],
                                [(x, y) for x in (-71.5, 0.0, 71.5) for y in (-45.0, 45.0)],
                                [-BOX_PITCH / 2, BOX_PITCH / 2]),
    'V4_vierdubbel_2dozen': _layout(W2, [-57.0, -19.5, 19.5, 57.0], [-WI2 / 2, -38.25, 0.0, 38.25, WI2 / 2],
                                    [(x, y) for x in (-71.5, -38.25, 0.0, 38.25, 71.5) for y in (-45.0, 45.0)],
                                    [-BOX_PITCH / 2, BOX_PITCH / 2]),
}


# ------------------------------------------------------------------ klemmetjes
def clip(xa, xb):
    """klemmetje tussen xa..xb (x-richting = pinrichting), pin klikt er van boven in."""
    c = box(xa, xb, -3.0, 3.0, PLATE_Z1 - 0.01, AXLE_Z) + cyl_x(xa, xb, 0, AXLE_Z, 3.0)
    c = c ^ box(-500, 500, -50, 50, -50, CLIP_TOP)
    c -= cyl_x(xa - 1, xb + 1, 0, AXLE_Z, CLIP_HOLE)
    c -= box(xa - 1, xb + 1, -CLIP_SLOT, CLIP_SLOT, AXLE_Z, AXLE_Z + 5)
    c -= Manifold.batch_hull([box(xa - 1, xb + 1, -CLIP_SLOT, CLIP_SLOT, CLIP_TOP - 0.45, CLIP_TOP - 0.44),
                              box(xa - 1, xb + 1, -CLIP_SLOT - 0.6, CLIP_SLOT + 0.6, CLIP_TOP + 0.01, CLIP_TOP + 0.02)])
    return c


def clips(L):
    out = []
    lo, hi = L['rim']
    out.append((lo, lo + RIM_CLIP_W))
    out.append((hi - RIM_CLIP_W, hi))
    for c in L['centers']:
        out.append((c - CENTER_HALF, c + CENTER_HALF))
    return out


# ------------------------------------------------------------------ basis
def base(L):
    W = L['W']
    WI = W - 2 * RIM_T
    outer = Manifold.batch_hull([rslab(W - 1.0, H_OUT - 1.0, 3.5, PLATE_Z0, PLATE_Z0 + 0.01),
                                 rslab(W, H_OUT, 4.0, PLATE_Z0 + 0.5, RIM_TOP - 0.8),
                                 rslab(W - 1.6, H_OUT - 1.6, 3.2, RIM_TOP - 0.01, RIM_TOP)])
    b = outer - rslab(WI, H_IN, 2.0, WALL_Z - 1, RIM_TOP + 1)
    b += rslab(WI + 0.2, H_IN + 0.2, 2.0, PLATE_Z0, PLATE_Z1)
    for xu in L['units']:
        b -= ref_unit_footprint().translate((xu, UNIT_DY, 0))
        b += ref_unit_block().translate((xu, UNIT_DY, 0))
    for xu in L['units']:
        b -= removal_cuts(xu).translate((0, UNIT_DY, 0))
    for (xa, xb) in clips(L):
        b += clip(xa, xb)
    for (xc, yc) in L['chocs']:
        b -= choc_pocket(xc, yc)
    for (x, y) in L['base_screws']:
        b -= cyl_z(x, y, 1.7, -30, 30)
    return b


# ------------------------------------------------------------------ wip
def rocker(L, idx):
    x0, x1, xu = L['rockers'][idx]
    w, cx = x1 - x0, (x0 + x1) / 2
    hh = H_IN / 2 - ROCKER_GAP
    r = chamfered_slab(w, 2 * hh, 2.0, ROCKER_Z0, ROCKER_Z1, 0.6, cx, 0)
    for (a, b) in ((x0, x0 + 1.2), (x1 - 1.2, x1)):
        sk = box(a, b, -hh + 1.0, hh - 1.0, 7.0, ROCKER_Z0 + 0.01)
        sk -= box(-500, 500, -5.0, 5.0, 0, 20)
        r += sk
    # scharnierlippen + pinnen aan beide uiteinden
    edges, (lo, hi) = L['edges'], L['rim']
    for side in (-1, 1):
        B = edges[idx] if side < 0 else edges[idx + 1]
        if abs(B - lo) < 1e-6 or abs(B - hi) < 1e-6:
            cin = B - side * RIM_CLIP_W            # binnenkant klem (rand)
            cout = B - side * 0.3                  # pin-eind (0.3 van de wand)
        else:
            cin = B - side * CENTER_HALF
            cout = B - side * 0.4                  # 0.8 mm tussen de twee pinnen
        lface = cin - side * 0.2                   # lip begint 0.2 van de klem
        la, lb = sorted((lface, lface - side * LUG_T))
        lug = box(la, lb, -3.0, 3.0, AXLE_Z, ROCKER_Z0 + 0.01) + cyl_x(la, lb, 0, AXLE_Z, 2.2)
        pa, pb = sorted((lface, cout))
        lug += cyl_x(pa - 0.01, pb + 0.01, 0, AXLE_Z, PIN_R)
        r += lug
    # drukpunten BILRESA (pin; dopje schuift erover)
    for y in (-BTN_Y9, BTN_Y9):
        r += Manifold.batch_hull([cyl_z(xu, y, 2.4, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                  cyl_z(xu, y, NUB_PIN_R, ROCKER_Z0 - 1.2, ROCKER_Z0 - 1.19)])
        r += cyl_z(xu, y, NUB_PIN_R, nub_pin_tip(), ROCKER_Z0 - 1.19)
    # drukpennen Choc
    for (xc, yc) in L['chocs']:
        if x0 <= xc <= x1:
            r += Manifold.batch_hull([cyl_z(xc, yc, 3.2, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                      cyl_z(xc, yc, PEN_R, ROCKER_Z0 - 1.0, ROCKER_Z0 - 0.99)])
            r += cyl_z(xc, yc, PEN_R, pen_tip(), ROCKER_Z0 - 0.99)
    return r


def cup_assembled(xc, yc, t=CUP_NOM):
    return pen_cup(t).translate((xc, yc, pen_tip() - t))
