"""BILRESA wandschakelaar v11 - compacte modellen (80.5 x 80.5, zelfde maat als een Jung AS500-raam)
- C1: enkele inbouwdoos, 1 BILRESA, 1 wip
- C2: dubbele inbouwdoos (71 mm), 1 BILRESA + venster voor een Jung-stopcontact (centraalplaat 55 x 55)
Omdat de hoogte nu 80.5 is (was 103.4) passen de Choc's niet meer boven/onder de printplaat:
ze zitten nu NAAST de printplaat, 2 boven + 2 onder (links en rechts -> wip draait niet scheef).
Rest (klem, scharnierpinnen, dopjes, uitdrukgaten, montagebakje) als v10.
"""
from manifold3d import Manifold
from cad9 import (box, rslab, cyl_x, cyl_z, chamfered_slab, stadium, ref_unit_block, ref_unit_footprint,
                  removal_cuts, choc_pocket, clip, nub_pin_tip, pen_tip,
                  PLATE_Z0, PLATE_Z1, RIM_T, RIM_TOP, AXLE_Z, ROCKER_Z0, ROCKER_Z1, ROCKER_GAP,
                  RIM_CLIP_W, CENTER_HALF, LUG_T, PIN_R, BTN_Y9, NUB_PIN_R, PEN_R, WALL_Z, BOX_PITCH, UNIT_DY)
from cad8 import MP_T
from cad10 import tapered_strip

S = 80.5                      # buitenmaat (Jung AS500 afdekraam 80.5 x 80.5)
H_OUT = S
H_IN = H_OUT - 2 * RIM_T      # 76.3
CHOC_DX, CHOC_DY = 25.0, 25.0  # Choc's naast de printplaat
LEG_R = 2.5

# Jung-stopcontact
JUNG_PLATE = 55.0             # centraalplaat 55 x 55
WIN = JUNG_PLATE + 1.0        # venster 56 x 56 (0.5 mm speling rondom)
WIN_R = 1.5
TUBE_T = 1.2                  # kokertje rond het venster (nette binnenwand)
RING_SCREW_R = 4.2            # ruimte voor de schroefkoppen van de draagring (onder de basis)
RING_SCREW_D = 1.8            # diepte van die uitsparing (van onderen, blind)
BOX_HOLE_D = 60.0             # gat in het montagebakje voor het stopcontact-binnenwerk


def _layout(W, units, edges, slots, base_screws, boxes, socket=None):
    WI = W - 2 * RIM_T
    return dict(W=W, units=units, edges=edges, rim=(-WI / 2, WI / 2), centers=list(edges[1:-1]),
                slots=slots, base_screws=base_screws, boxes=boxes, socket=socket,
                chocs=[(xu + sx * CHOC_DX, sy * CHOC_DY) for xu in units for sx in (-1, 1) for sy in (-1, 1)])


WI1 = S - 2 * RIM_T
W2 = BOX_PITCH + S            # 151.5
WI2 = W2 - 2 * RIM_T
E2 = 3.0                      # scheiding wip | venster
XU2 = (-WI2 / 2 + E2) / 2     # BILRESA midden in zijn vak (-35.3)
XS2 = BOX_PITCH / 2           # stopcontact precies op het midden van de rechter doos

LAYOUTS = {
    'C1_enkel_compact': _layout(S, [0.0], [-WI1 / 2, WI1 / 2], [0.0],
                                [(sx * 33.5, sy * 10.0) for sx in (-1, 1) for sy in (-1, 1)], [0.0]),
    'C2_enkel_plus_stopcontact_jung': _layout(W2, [XU2], [-WI2 / 2, E2, WI2 / 2], [XU2, None],
                                              [(x, sy * 10.0) for x in (XU2 - 33.5, -5.0) for sy in (-1, 1)],
                                              [-BOX_PITCH / 2], socket=XS2),
}


def clips(L):
    lo, hi = L['rim']
    out = [(lo, lo + RIM_CLIP_W), (hi - RIM_CLIP_W, hi)]
    for c in L['centers']:
        out.append((c - CENTER_HALF, c + CENTER_HALF))
    return out


def ring_screws(xs):
    return [(xs + dx, dy) for (dx, dy) in ((-30, 0), (30, 0), (0, -30), (0, 30))]


# ------------------------------------------------------------------ basis
def base(L):
    W = L['W']
    WI = W - 2 * RIM_T
    outer = Manifold.batch_hull([rslab(W - 1.0, H_OUT - 1.0, 3.5, PLATE_Z0, PLATE_Z0 + 0.01),
                                 rslab(W, H_OUT, 4.0, PLATE_Z0 + 0.5, RIM_TOP - 0.8),
                                 rslab(W - 1.6, H_OUT - 1.6, 3.2, RIM_TOP - 0.01, RIM_TOP)])
    b = outer - rslab(WI, H_IN, 2.0, WALL_Z - 1, RIM_TOP + 1)
    b += rslab(WI + 0.2, H_IN + 0.2, 2.0, PLATE_Z0, PLATE_Z1)
    inner = box(-WI / 2 + 0.05, WI / 2 - 0.05, -H_IN / 2 + 0.05, H_IN / 2 - 0.05, -30, 30)
    for xu in L['units']:
        b -= ref_unit_footprint().translate((xu, UNIT_DY, 0)) ^ inner
        b += ref_unit_block().translate((xu, UNIT_DY, 0)) ^ inner
    for xu in L['units']:
        b -= removal_cuts(xu).translate((0, UNIT_DY, 0))
    for (xa, xb) in clips(L):
        b += clip(xa, xb)
    for (xc, yc) in L['chocs']:
        b -= choc_pocket(xc, yc)
    for (x, y) in L['base_screws']:
        b -= cyl_z(x, y, 1.7, -30, 30)
    if L['socket'] is not None:
        xs = L['socket']
        b -= rslab(WIN, WIN, WIN_R, -30, 30, cx=xs)
        for (x, y) in ring_screws(xs):
            b -= cyl_z(x, y, RING_SCREW_R, PLATE_Z0 - 1, PLATE_Z0 + RING_SCREW_D)
    return b


# ------------------------------------------------------------------ wip / vensterplaat
def panel(L, i):
    edges, (lo, hi) = L['edges'], L['rim']
    xu = L['slots'][i]
    x0, x1 = edges[i] + ROCKER_GAP, edges[i + 1] - ROCKER_GAP
    w, cx = x1 - x0, (x0 + x1) / 2
    hh = H_IN / 2 - ROCKER_GAP
    r = chamfered_slab(w, 2 * hh, 2.0, ROCKER_Z0, ROCKER_Z1, 0.6, cx, 0)
    ap = tapered_strip(x0, x1, -hh, hh, 'x-') + tapered_strip(x0, x1, -hh, hh, 'x+')
    ap -= box(-500, 500, -5.0, 5.0, 0, 20)
    ap += tapered_strip(x0, x1, -hh, hh, 'y-') + tapered_strip(x0, x1, -hh, hh, 'y+')
    r += ap
    for side in (-1, 1):
        B = edges[i] if side < 0 else edges[i + 1]
        if abs(B - lo) < 1e-6 or abs(B - hi) < 1e-6:
            cin, cout = B - side * RIM_CLIP_W, B - side * 0.3
        else:
            cin, cout = B - side * CENTER_HALF, B - side * 0.4
        lface = cin - side * 0.2
        la, lb = sorted((lface, lface - side * LUG_T))
        r += box(la, lb, -3.0, 3.0, AXLE_Z, ROCKER_Z0 + 0.01) + cyl_x(la, lb, 0, AXLE_Z, 2.2)
        pa, pb = sorted((lface, cout))
        r += cyl_x(pa - 0.01, pb + 0.01, 0, AXLE_Z, PIN_R)
    if xu is None:
        xs = L['socket']
        # koker rond het venster tot op de bodemplaat (draagt de plaat en geeft een nette binnenwand)
        z0 = PLATE_Z1 + 0.15
        r += rslab(WIN + 2 * TUBE_T, WIN + 2 * TUBE_T, WIN_R + TUBE_T, z0, ROCKER_Z0 + 0.01, cx=xs)
        # extra pootjes in de hoeken
        for x in (x0 + 6.5, x1 - 6.5):
            for y in (-32.5, 32.5):
                r += cyl_z(x, y, LEG_R, z0, ROCKER_Z0 + 0.01)
        r -= rslab(WIN, WIN, WIN_R, -30, 30, cx=xs)
        # afgeschuinde vensterrand (voelt minder diep, meer ruimte voor de stekker)
        r -= Manifold.batch_hull([rslab(WIN, WIN, WIN_R, ROCKER_Z1 - 1.5, ROCKER_Z1 - 1.49, cx=xs),
                                  rslab(WIN + 3.0, WIN + 3.0, WIN_R + 1.5, ROCKER_Z1 + 0.01, ROCKER_Z1 + 0.02, cx=xs)])
        return r
    for y in (-BTN_Y9, BTN_Y9):
        r += Manifold.batch_hull([cyl_z(xu, y, 2.4, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                  cyl_z(xu, y, NUB_PIN_R, ROCKER_Z0 - 1.2, ROCKER_Z0 - 1.19)])
        r += cyl_z(xu, y, NUB_PIN_R, nub_pin_tip(), ROCKER_Z0 - 1.19)
    for (xc, yc) in L['chocs']:
        if x0 <= xc <= x1:
            r += Manifold.batch_hull([cyl_z(xc, yc, 3.2, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                      cyl_z(xc, yc, PEN_R, ROCKER_Z0 - 1.0, ROCKER_Z0 - 0.99)])
            r += cyl_z(xc, yc, PEN_R, pen_tip(), ROCKER_Z0 - 0.99)
    return r


def panels(L):
    return [panel(L, i) for i in range(len(L['slots']))]


# ------------------------------------------------------------------ montagebakje
def _box_slots(m, bx, z0, z1):
    for (x, y, d) in ((0, -30, 'x'), (0, 30, 'x'), (-30, 0, 'y'), (30, 0, 'y')):
        if d == 'x':
            m -= stadium(bx + x - 3, y, bx + x + 3, y, 2.1, z0 - 1, z1 + 1)
        else:
            m -= stadium(bx + x, y - 3, bx + x, y + 3, 2.1, z0 - 1, z1 + 1)
    return m


def mount_plate(L):
    """montagebakje. Bij het stopcontact komt de draagring van het stopcontact OP de bodem van het bakje
    (bakje zit geklemd tussen muur en draagring; schroeven van de draagring 2 mm langer)."""
    W = L['W']
    WI = W - 2 * RIM_T
    z0, z1 = WALL_Z, WALL_Z + MP_T
    zt = PLATE_Z0 - 0.15
    outer = Manifold.batch_hull([rslab(W - 1.0, H_OUT - 1.0, 3.5, z0, z0 + 0.01),
                                 rslab(W, H_OUT, 4.0, z0 + 0.5, zt - 0.5),
                                 rslab(W - 1.0, H_OUT - 1.0, 3.5, zt - 0.01, zt)])
    m = outer - rslab(WI, H_IN, 2.0, z1, zt + 1)
    for bx in L['boxes']:
        m -= rslab(46.0, 36.0, 6.0, z0 - 1, z1 + 1, cx=bx)
        m = _box_slots(m, bx, z0, z1)
    if L['socket'] is not None:
        xs = L['socket']
        m -= cyl_z(xs, 0, BOX_HOLE_D / 2, z0 - 1, z1 + 1, seg=128)
        m = _box_slots(m, xs, z0, z1)
    for (x, y) in L['base_screws']:
        m += cyl_z(x, y, 4.0, z1 - 0.01, zt)
        m -= cyl_z(x, y, 1.3, z0 + 0.6, zt + 1)
    return m
