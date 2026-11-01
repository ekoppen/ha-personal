"""BILRESA wandschakelaar v7 - hoge basis met geintegreerd frame, Choc Brown aan de uiteinden,
doorlopende stalen as (2 mm), aparte montageplaat op de inbouwdoos.

Coordinaten: batterijmidden z=0, bovenkant bodemplaat z=-1.45, as z=6.5 / y=0.
De klem voor de printplaat komt 1-op-1 uit de referentie (ref/base4c.stl).
"""
import numpy as np
from manifold3d import Manifold
from cad import (box, rslab, cyl_x, cyl_y, cyl_z, stadium, chamfered_slab, ref_unit_block,
                 ref_unit_footprint, PLATE_Z0, PLATE_Z1, BTN_Y)

H_OUT = 122.0           # totale hoogte
RIM_T = 2.1             # wanddikte frame
H_IN = H_OUT - 2 * RIM_T
RIM_TOP = 8.2
AXLE_Z = 6.5
AXLE_D = 2.0            # stalen as
HOLE_RIM = 1.05         # straal gat in frame (strak)
HOLE_LUG = 1.18         # straal gat in wip (draait vrij)
ROCKER_Z0, ROCKER_Z1 = 8.0, 10.5
ROCKER_GAP = 0.6        # speling wip-frame en tussen wippen (per kant)
NUB_TIP = 4.4           # punt drukpunt BILRESA (zelfde als v4/v5 "goed")
CHOC_Y = 49.5
CHOC_POCKET, CHOC_DEPTH, CHOC_H = 14.2, 2.2, 8.0
CAP_IN, CAP_WALL, CAP_TOP_T = 15.5, 1.0, 1.2
CAP_BOSS = (0.8, 1.2, 1.6)
CAP_NOMINAL = 1.2
GAP = 2.8               # ruimte tussen bodemplaat en montageplaat (voor schroefkoppen doos)
MP_T = 2.0              # dikte montageplaat
WALL_Z = PLATE_Z0 - GAP - MP_T   # muur
BOX_PITCH = 71.0


def stem_top():
    return PLATE_Z1 - CHOC_DEPTH + CHOC_H


def cap_top(boss=CAP_NOMINAL):
    return stem_top() + boss + CAP_TOP_T


# rockers: (x0, x1, unit_x, [extra lug x-centra])
def _layout(W, units, rockers, centers, lugs, base_screws, boxes):
    return dict(W=W, units=units, rockers=rockers, centers=centers, lugs=lugs,
                base_screws=base_screws, boxes=boxes,
                chocs=[(xu, s * CHOC_Y) for xu in units for s in (-1, 1)])


def _rk(W, edges, units):
    """wippen tussen opeenvolgende randen; edges = x-grenzen incl. buitenkant frame-binnenzijde"""
    out = []
    for i, xu in enumerate(units):
        a, b = edges[i], edges[i + 1]
        out.append((a + ROCKER_GAP, b - ROCKER_GAP, xu))
    return out


W1 = 86.2
W2 = BOX_PITCH + 86.2
WI1, WI2 = W1 - 2 * RIM_T, W2 - 2 * RIM_T
LAYOUTS = {
    'V1_enkel_1doos': _layout(W1, [0.0], _rk(W1, [-WI1 / 2, WI1 / 2], [0.0]), [],
                              [-36.5, -17.0, 17.0, 36.5], [(-36.5, -52.0), (36.5, -52.0), (-36.5, 52.0), (36.5, 52.0)],
                              [0.0]),
    'V2_dubbel_1doos': _layout(W1, [-20.0, 20.0], _rk(W1, [-WI1 / 2, 0.0, WI1 / 2], [-20.0, 20.0]), [0.0],
                               [-36.5, -2.6, 2.6, 36.5], [(-36.5, -52.0), (36.5, -52.0), (-36.5, 52.0), (36.5, 52.0)],
                               [0.0]),
    'V3_dubbel_2dozen': _layout(W2, [-38.25, 38.25], _rk(W2, [-WI2 / 2, 0.0, WI2 / 2], [-38.25, 38.25]), [0.0],
                                [-74.5, -55.25, -21.25, -2.6, 2.6, 21.25, 55.25, 74.5],
                                [(x, y) for x in (-71.5, 0.0, 71.5) for y in (-52.0, 52.0)],
                                [-BOX_PITCH / 2, BOX_PITCH / 2]),
    'V4_vierdubbel_2dozen': _layout(W2, [-57.0, -19.5, 19.5, 57.0],
                                    _rk(W2, [-WI2 / 2, -38.25, 0.0, 38.25, WI2 / 2], [-57.0, -19.5, 19.5, 57.0]),
                                    [-38.25, 0.0, 38.25],
                                    [-74.5, -40.85, -35.65, -2.6, 2.6, 35.65, 40.85, 74.5],
                                    [(x, y) for x in (-71.5, -38.25, 0.0, 38.25, 71.5) for y in (-52.0, 52.0)],
                                    [-BOX_PITCH / 2, BOX_PITCH / 2]),
}


# ------------------------------------------------------------------ basis (bodemplaat + frame)
def choc_pocket(xc, yc):
    sgn = 1 if yc > 0 else -1
    c = box(xc - CHOC_POCKET / 2, xc + CHOC_POCKET / 2, yc - CHOC_POCKET / 2, yc + CHOC_POCKET / 2,
            PLATE_Z1 - CHOC_DEPTH, PLATE_Z1 + 1)
    c += cyl_z(xc, yc, 1.8, -30, 30)
    for dx in (-5.5, 5.5):
        c += cyl_z(xc + dx, yc, 1.05, -30, 30)
    for (dx, dy) in ((0, -5.9), (-5.0, -3.8), (5.0, -3.8)):
        dy = dy * sgn
        c += box(xc + dx - 0.9, xc + dx + 0.9, yc + dy - 0.9, yc + dy + 0.9, -30, 30)
    return c


def axle_cradle(xc):
    """steun voor de as (open aan de bovenkant: as valt erin)"""
    c = box(xc - 1.2, xc + 1.2, -3.0, 3.0, PLATE_Z1 - 0.01, AXLE_Z)
    c += cyl_x(xc - 1.2, xc + 1.2, 0, AXLE_Z, 2.2)
    c = c ^ box(-500, 500, -50, 50, -50, AXLE_Z + 0.9)
    c -= cyl_x(xc - 2, xc + 2, 0, AXLE_Z, 1.1)
    c -= box(xc - 2, xc + 2, -1.0, 1.0, AXLE_Z, AXLE_Z + 5)
    return c


LIP_TOP = 0.5   # v7.1: batterijklemmen tot net boven het midden van de batterij (was +1.9)


def removal_cuts(xu):
    """v7.1: printplaat zonder kracht verwijderen.
    - klemrandjes boven de batterijen verlaagd
    - uitdrukgaten van achteren onder beide batterijen en de printplaat
    - wrikgleufjes aan beide uiteinden van de uitsparing"""
    from cad import pocket_outline
    c = pocket_outline().offset(2.0).extrude(10).translate((xu, 0, LIP_TOP))
    for bx in (xu + 9.2, xu - 9.25):
        for by in (-12.0, 12.0):
            c += cyl_z(bx, by, 2.45, -30, 30, seg=48)
    for py in (-25.5, 27.0):
        c += cyl_z(xu, py, 2.0, -30, 30)
    for (y0, y1) in ((-31.5, -26.5), (30.5, 35.5)):
        c += box(xu - 3.0, xu + 3.0, y0, y1, -4.3, 5)
    return c


def base(L):
    W = L['W']
    WI = W - 2 * RIM_T
    outer = chamfered_slab(W, H_OUT, 4.0, WALL_Z, RIM_TOP, 0.8)
    b = outer - rslab(WI, H_IN, 2.0, WALL_Z - 1, RIM_TOP + 1)
    b += rslab(WI + 0.2, H_IN + 0.2, 2.0, PLATE_Z0, PLATE_Z1)
    for xu in L['units']:
        b -= ref_unit_footprint().translate((xu, 0, 0))
        b += ref_unit_block().translate((xu, 0, 0))
    for xu in L['units']:
        b -= removal_cuts(xu)
    for xc in L['centers']:
        b += axle_cradle(xc)
    for (xc, yc) in L['chocs']:
        b -= choc_pocket(xc, yc)
    for (x, y) in L['base_screws']:
        b -= cyl_z(x, y, 1.7, -30, 30)                       # M3 doorvoer
    # as-gat door beide zijwanden
    b -= cyl_x(-W / 2 - 1, W / 2 + 1, 0, AXLE_Z, HOLE_RIM)
    b -= cyl_x(-W / 2 - 1, -W / 2 + 0.6, 0, AXLE_Z, 1.6, 1.05)  # inloop-afschuining
    return b


# ------------------------------------------------------------------ wip
def rocker(L, idx):
    x0, x1, xu = L['rockers'][idx]
    w, cx = x1 - x0, (x0 + x1) / 2
    hh = H_IN / 2 - ROCKER_GAP
    r = chamfered_slab(w, 2 * hh, 2.0, ROCKER_Z0, ROCKER_Z1, 0.6, cx, 0)
    # randen langs de lange zijden (stijfheid), niet bij de as
    for (a, b) in ((x0, x0 + 1.2), (x1 - 1.2, x1)):
        sk = box(a, b, -hh + 1.0, hh - 1.0, 7.0, ROCKER_Z0 + 0.01)
        sk -= box(-500, 500, -5.0, 5.0, 0, 20)
        r += sk
    # aslippen
    for lx in L['lugs']:
        if x0 + 1.0 <= lx <= x1 - 1.0:
            lug = box(lx - 1.0, lx + 1.0, -3.0, 3.0, AXLE_Z, ROCKER_Z0 + 0.01) + cyl_x(lx - 1.0, lx + 1.0, 0, AXLE_Z, 2.2)
            lug -= cyl_x(lx - 2, lx + 2, 0, AXLE_Z, HOLE_LUG)
            r += lug
    # drukpunten BILRESA
    for y in (-BTN_Y, BTN_Y):
        r += Manifold.batch_hull([cyl_z(xu, y, 2.2, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01), cyl_z(xu, y, 1.6, 5.6, 5.61)])
        r += cyl_z(xu, y, 1.25, NUB_TIP, 5.61)
    # drukpennen op de Choc-kapjes
    for (xc, yc) in L['chocs']:
        if x0 <= xc <= x1:
            r += Manifold.batch_hull([cyl_z(xc, yc, 3.0, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                      cyl_z(xc, yc, 2.0, cap_top() + 0.3, cap_top() + 0.31)])
            r += cyl_z(xc, yc, 2.0, cap_top(), cap_top() + 0.31)
    r -= cyl_x(x0 - 1, x1 + 1, 0, AXLE_Z, HOLE_LUG)
    return r


# ------------------------------------------------------------------ montageplaat
def mount_plate(L):
    W = L['W']
    WI = W - 2 * RIM_T
    z0, z1 = WALL_Z, WALL_Z + MP_T
    m = rslab(WI - 1.0, H_IN - 1.0, 2.0, z0, z1)
    for bx in L['boxes']:
        m -= rslab(46.0, 36.0, 6.0, z0 - 1, z1 + 1, cx=bx)      # doorgang draden
        for (x, y, d) in ((0, -30, 'x'), (0, 30, 'x'), (-30, 0, 'y'), (30, 0, 'y')):
            if d == 'x':
                m -= stadium(bx + x - 3, y, bx + x + 3, y, 2.1, z0 - 1, z1 + 1)
            else:
                m -= stadium(bx + x, y - 3, bx + x, y + 3, 2.1, z0 - 1, z1 + 1)
    for (x, y) in L['base_screws']:
        m += cyl_z(x, y, 4.0, z1 - 0.01, PLATE_Z0)
        m -= cyl_z(x, y, 1.3, z0 + 0.6, PLATE_Z0 + 1)             # M3 zelftappend
    # verstijvingsrand
    m += rslab(WI - 1.0, H_IN - 1.0, 2.0, z1 - 0.01, z1 + 1.2) - rslab(WI - 5.0, H_IN - 5.0, 1.0, z1 - 1, z1 + 2)
    return m


# ------------------------------------------------------------------ Choc-kapje
def choc_cap(boss):
    o = CAP_IN + 2 * CAP_WALL
    skirt_len = boss + 4.0
    c = rslab(o, o, 1.5, 0, CAP_TOP_T + skirt_len)
    c -= rslab(CAP_IN, CAP_IN, 0.8, CAP_TOP_T, CAP_TOP_T + skirt_len + 1)
    c += cyl_z(0, 0, 2.0, CAP_TOP_T - 0.01, CAP_TOP_T + boss)
    n = CAP_BOSS.index(boss) + 1
    for i in range(n):
        x = (i - (n - 1) / 2) * 2.0
        c -= box(x - 0.4, x + 0.4, -o / 2 - 1, -o / 2 + 0.6, CAP_TOP_T + skirt_len - 1.0, CAP_TOP_T + skirt_len + 1)
    return c


def cap_assembled(xc, yc, boss=CAP_NOMINAL):
    return choc_cap(boss).mirror((0, 0, 1)).translate((xc, yc, cap_top(boss)))


def axle(L):
    W = L['W']
    return cyl_x(-W / 2 + 0.3, W / 2 - 0.3, 0, AXLE_Z, AXLE_D / 2)
