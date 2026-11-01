"""BILRESA wandschakelaar v8 (compacter: 103 mm, as in klemmetjes, dopjes op de pennen) - hoge basis met geintegreerd frame, Choc Brown aan de uiteinden,
doorlopende stalen as (2 mm), aparte montageplaat op de inbouwdoos.

Coordinaten: batterijmidden z=0, bovenkant bodemplaat z=-1.45, as z=6.5 / y=0.
De klem voor de printplaat komt 1-op-1 uit de referentie (ref/base4c.stl).
"""
import numpy as np
from manifold3d import Manifold
from cad import (box, rslab, cyl_x, cyl_y, cyl_z, stadium, chamfered_slab, ref_unit_block,
                 ref_unit_footprint, PLATE_Z0, PLATE_Z1, BTN_Y)

H_OUT = 103.4           # v8: totale hoogte (was 122)
RIM_T = 2.1             # wanddikte frame
H_IN = H_OUT - 2 * RIM_T
RIM_TOP = 8.2
AXLE_Z = 6.5
AXLE_D = 2.0            # stalen as
HOLE_RIM = 1.05         # straal gat in frame (strak)
HOLE_LUG = 1.18         # straal gat in wip (draait vrij)
ROCKER_Z0, ROCKER_Z1 = 8.0, 10.5
ROCKER_GAP = 0.6        # speling wip-frame en tussen wippen (per kant)
NUB_TIP = 4.6           # v8: 0.2 mm meer speling -> wip kantelt verder -> Choc dieper in
CHOC_Y = 41.5           # v8: direct tegen de printplaat aan (was 49.5)
CHOC_POCKET, CHOC_DEPTH, CHOC_H = 14.2, 2.2, 7.7   # v8.1: gemeten stempel 5.5 mm boven plaat
CAP_IN, CAP_WALL, CAP_TOP_T = 15.5, 1.0, 1.2
PEN_R = 2.0             # v8: drukpen (dopje schuift eroverheen)
CUP_T = (0.4, 0.8, 1.2) # dopjes: bodemdikte dun / normaal / dik
CUP_NOM = 0.8
CUP_LEN = 1.7
CAP_BOSS = (0.8, 1.2, 1.6)
CAP_NOMINAL = 1.2
GAP = 2.8               # ruimte tussen bodemplaat en montageplaat (voor schroefkoppen doos)
MP_T = 2.0              # dikte montageplaat
WALL_Z = PLATE_Z0 - GAP - MP_T   # muur
BOX_PITCH = 71.0


def stem_top():
    return PLATE_Z1 - CHOC_DEPTH + CHOC_H


def pen_tip():
    return stem_top() + CUP_NOM


def pen_cup(t):
    """dopje over de drukpen: binnen 4.3 mm, bodem t mm, platte drukvlak 6 mm. z=0 = drukvlak (op bed)."""
    c = cyl_z(0, 0, 3.0, 0, t) + cyl_z(0, 0, PEN_R + 0.95, t - 0.01, t + CUP_LEN)
    c -= cyl_z(0, 0, PEN_R + 0.15, t, t + CUP_LEN + 1)
    n = CUP_T.index(t) + 1
    for i in range(n):
        a = i * 360.0 / n
        c -= box(-0.35, 0.35, PEN_R + 0.6, PEN_R + 1.5, t + CUP_LEN - 0.8, t + CUP_LEN + 1).rotate((0, 0, a))
    return c


def cup_assembled(xc, yc, t=CUP_NOM):
    return pen_cup(t).translate((xc, yc, pen_tip() - t))


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
                              [-36.5, -17.0, 17.0, 36.5], [(-36.5, -45.0), (36.5, -45.0), (-36.5, 45.0), (36.5, 45.0)],
                              [0.0]),
    'V2_dubbel_1doos': _layout(W1, [-20.0, 20.0], _rk(W1, [-WI1 / 2, 0.0, WI1 / 2], [-20.0, 20.0]), [0.0],
                               [-36.5, -2.6, 2.6, 36.5], [(-36.5, -45.0), (36.5, -45.0), (-36.5, 45.0), (36.5, 45.0)],
                               [0.0]),
    'V3_dubbel_2dozen': _layout(W2, [-38.25, 38.25], _rk(W2, [-WI2 / 2, 0.0, WI2 / 2], [-38.25, 38.25]), [0.0],
                                [-72.6, -55.25, -21.25, -2.6, 2.6, 21.25, 55.25, 72.6],
                                [(x, y) for x in (-71.5, 0.0, 71.5) for y in (-45.0, 45.0)],
                                [-BOX_PITCH / 2, BOX_PITCH / 2]),
    'V4_vierdubbel_2dozen': _layout(W2, [-57.0, -19.5, 19.5, 57.0],
                                    _rk(W2, [-WI2 / 2, -38.25, 0.0, 38.25, WI2 / 2], [-57.0, -19.5, 19.5, 57.0]),
                                    [-38.25, 0.0, 38.25],
                                    [-72.6, -40.85, -35.65, -2.6, 2.6, 35.65, 40.85, 72.6],
                                    [(x, y) for x in (-71.5, -38.25, 0.0, 38.25, 71.5) for y in (-45.0, 45.0)],
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
    """v8: klikklemmetje voor de as: bovenaan 1.7 mm open (as 2.0 klikt erin)"""
    c = box(xc - 1.2, xc + 1.2, -3.0, 3.0, PLATE_Z1 - 0.01, AXLE_Z)
    c += cyl_x(xc - 1.2, xc + 1.2, 0, AXLE_Z, 2.3)
    c = c ^ box(-500, 500, -50, 50, -50, AXLE_Z + 1.35)
    c -= cyl_x(xc - 2, xc + 2, 0, AXLE_Z, 1.05)
    c -= box(xc - 2, xc + 2, -0.85, 0.85, AXLE_Z, AXLE_Z + 5)
    # inloop-afschuining
    c -= Manifold.batch_hull([box(xc - 2, xc + 2, -0.85, 0.85, AXLE_Z + 0.95, AXLE_Z + 0.96),
                              box(xc - 2, xc + 2, -1.45, 1.45, AXLE_Z + 1.4, AXLE_Z + 1.41)])
    return c


def side_cradles(L):
    WI = L['W'] - 2 * RIM_T
    return [-WI / 2 + 1.2, WI / 2 - 1.2]


LIP_TOP = 1.95  # v8.4: batterijranden weer origineel (gebruiker: randje was prima)


PCB_LOOSEN = 0.25


def removal_cuts(xu):
    """v7.1: printplaat zonder kracht verwijderen.
    - klemrandjes boven de batterijen verlaagd
    - uitdrukgaten van achteren onder beide batterijen en de printplaat
    - wrikgleufjes aan beide uiteinden van de uitsparing"""
    from cad import pocket_outline
    c = pocket_outline().offset(2.0).extrude(10).translate((xu, 0, LIP_TOP)) if LIP_TOP < 1.85 else Manifold()
    for bx in (xu + 9.2, xu - 9.25):
        for by in (-12.0, 12.0):
            c += cyl_z(bx, by, 2.45, -30, 30, seg=48)
    # v8.4: printplaat-uitsparing 0.25 mm per kant ruimer (printplaat zat te strak)
    po = pocket_outline().simplify(0.05)
    ring = po.offset(PCB_LOOSEN) - po.offset(-0.6)
    # niet langs de batterijrandjes (daar al 0.15 mm speling; voorkomt flinterdunne restjes)
    from manifold3d import CrossSection as _CS
    ring = ring - (_CS.square((60.0, 47.0), center=True) - _CS.square((28.0, 47.0), center=True))
    c += ring.extrude(PLATE_Z1 + 0.3 - (-3.3)).translate((xu, 0, -3.3))
    for py in (-25.5, 27.0):
        c += cyl_z(xu, py, 2.0, -30, 30)
    for (y0, y1) in ((-31.5, -26.5), (30.5, 35.5)):
        c += box(xu - 3.0, xu + 3.0, y0, y1, -4.3, 5)
    return c


def base(L):
    W = L['W']
    WI = W - 2 * RIM_T
    # v8.2: basis begint bij de onderkant van de bodemplaat (plat op het bed, geen support)
    outer = Manifold.batch_hull([rslab(W - 1.0, H_OUT - 1.0, 3.5, PLATE_Z0, PLATE_Z0 + 0.01),
                                 rslab(W, H_OUT, 4.0, PLATE_Z0 + 0.5, RIM_TOP - 0.8),
                                 rslab(W - 1.6, H_OUT - 1.6, 3.2, RIM_TOP - 0.01, RIM_TOP)])
    b = outer - rslab(WI, H_IN, 2.0, WALL_Z - 1, RIM_TOP + 1)
    b += rslab(WI + 0.2, H_IN + 0.2, 2.0, PLATE_Z0, PLATE_Z1)
    for xu in L['units']:
        b -= ref_unit_footprint().translate((xu, 0, 0))
        b += ref_unit_block().translate((xu, 0, 0))
    for xu in L['units']:
        b -= removal_cuts(xu)
    for xc in list(L['centers']) + side_cradles(L):
        b += axle_cradle(xc)
    for (xc, yc) in L['chocs']:
        b -= choc_pocket(xc, yc)
    for (x, y) in L['base_screws']:
        b -= cyl_z(x, y, 1.7, -30, 30)                       # M3 doorvoer
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
    # drukpennen voor de Choc (dopje schuift over de pen; dikte van de bodem = afstelling)
    for (xc, yc) in L['chocs']:
        if x0 <= xc <= x1:
            r += Manifold.batch_hull([cyl_z(xc, yc, 3.2, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                      cyl_z(xc, yc, PEN_R, ROCKER_Z0 - 1.0, ROCKER_Z0 - 0.99)])
            r += cyl_z(xc, yc, PEN_R, pen_tip(), ROCKER_Z0 - 0.99)
    r -= cyl_x(x0 - 1, x1 + 1, 0, AXLE_Z, HOLE_LUG)
    return r


# ------------------------------------------------------------------ montageplaat
def mount_plate(L):
    """v8.2: montagebakje - vlakke bodem + rand tot onder de basis (print zonder support).
    Buitenmaat gelijk aan de basis; samen vormen ze een doorlopende zijkant met een fijn naadje."""
    W = L['W']
    WI = W - 2 * RIM_T
    z0, z1 = WALL_Z, WALL_Z + MP_T
    zt = PLATE_Z0 - 0.15                                         # 0.15 speling onder de basis
    outer = Manifold.batch_hull([rslab(W - 1.0, H_OUT - 1.0, 3.5, z0, z0 + 0.01),
                                 rslab(W, H_OUT, 4.0, z0 + 0.5, zt - 0.5),
                                 rslab(W - 1.0, H_OUT - 1.0, 3.5, zt - 0.01, zt)])
    m = outer - rslab(WI, H_IN, 2.0, z1, zt + 1)
    for bx in L['boxes']:
        m -= rslab(46.0, 36.0, 6.0, z0 - 1, z1 + 1, cx=bx)      # doorgang draden
        for (x, y, d) in ((0, -30, 'x'), (0, 30, 'x'), (-30, 0, 'y'), (30, 0, 'y')):
            if d == 'x':
                m -= stadium(bx + x - 3, y, bx + x + 3, y, 2.1, z0 - 1, z1 + 1)
            else:
                m -= stadium(bx + x, y - 3, bx + x, y + 3, 2.1, z0 - 1, z1 + 1)
    for (x, y) in L['base_screws']:
        m += cyl_z(x, y, 4.0, z1 - 0.01, zt)
        m -= cyl_z(x, y, 1.3, z0 + 0.6, zt + 1)                 # M3 zelftappend
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
