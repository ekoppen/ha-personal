"""BILRESA wandschakelaar v13 - C2 met Kopp-stopcontact, stopcontact GELIJK met het frame
Gemeten aan v12: de voorkant van het stopcontact lag 6.7 mm te diep.
- het stopcontact (draagring + randje) komt 6.7 mm hoger te liggen:
  * in het montagebakje zit een kraag (werkt als een verhogingsring voor de inbouwdoos), de draagring ligt erop
  * de kraag steekt door een groot gat in de basis
  * het klemrandje zit nu onderin de VENSTERPLAAT (print rechtop, randje op het bed -> geen support)
  * de vensterplaat heeft geen scharnierpinnen meer: het stopcontact klemt hem vast
- de scheiding wip|venster schuift 5 mm naar links (kraag mag niet onder het middelste klemmetje)
"""
import math
from manifold3d import Manifold
import cad11
from cad11 import (box, rslab, cyl_z, chamfered_slab, _layout, clips, panel as _panel11, base as _base11,
                   H_IN, RIM_T, WALL_Z, MP_T, PLATE_Z0, PLATE_Z1, ROCKER_Z0, ROCKER_Z1, ROCKER_GAP,
                   BOX_PITCH, WI2, W2, XS2)
from cad12 import (arc_slot, lip_opening, test_piece, _sq, KOPP_WIN, LIP_IN, LIP_TS, ROT_DEG, RING_W, HEAD_H)

RAISE = 6.7                        # gemeten: stopcontact lag 6.7 mm te diep
LIP_Z0 = PLATE_Z0 + RAISE          # onderkant randje = bovenkant draagring (0.85)
RING_T = 1.0                       # alleen voor de controle; de kraag is gemeten t.o.v. de v12-situatie
COLLAR = 68.0                      # buitenmaat kraag
COLLAR_TOP = PLATE_Z0 - 1.0 + RAISE   # zelfde verschil als v12 (verhoging 1 mm onder de basis) + 6.7
BASE_HOLE = COLLAR + 0.8
SKIRT_T = 1.2
TUBE_T = 1.2
E2 = -3.2
XU2 = (-WI2 / 2 + E2) / 2          # -38.4

LAYOUTS = {
    'C2_enkel_plus_stopcontact_kopp': _layout(W2, [XU2], [-WI2 / 2, E2, WI2 / 2], [XU2, None],
                                              [(x, sy * 10.0) for x in (XU2 - 31.0, -5.5) for sy in (-1, 1)],
                                              [-BOX_PITCH / 2], socket=XS2),
}


def base(L):
    b = _base11(dict(L, socket=None))
    b -= _sq(BASE_HOLE, 3.0, -30, 30, L['socket'])
    return b


def vensterplaat(L, t):
    """print RECHTOP (randje op het bed). Wordt door het stopcontact vastgeklemd."""
    xs = L['socket']
    edges = L['edges']
    x0, x1 = edges[1] + ROCKER_GAP, edges[2] - ROCKER_GAP
    hh = H_IN / 2 - ROCKER_GAP
    cx = (x0 + x1) / 2
    z0 = LIP_Z0
    p = chamfered_slab(x1 - x0, 2 * hh, 2.0, ROCKER_Z0, ROCKER_Z1, 0.6, cx, 0)
    # buitenwand (met uitsparing bij de klemmetjes van de basis)
    sk = rslab(x1 - x0, 2 * hh, 2.0, z0, ROCKER_Z0 + 0.01, cx=cx) - \
        rslab(x1 - x0 - 2 * SKIRT_T, 2 * hh - 2 * SKIRT_T, 1.0, z0 - 1, ROCKER_Z0 + 1, cx=cx)
    sk -= box(-500, 500, -4.0, 4.0, z0 - 1, ROCKER_Z0)
    p += sk
    # koker + randje
    p += _sq(KOPP_WIN + 2 * TUBE_T, 1.5 + TUBE_T, z0, ROCKER_Z0 + 0.01, xs)
    p -= _sq(KOPP_WIN, 1.5, z0 + t, 30, xs)
    p -= lip_opening(xs, -30, 30)
    # schroefkoppen draagring
    for ang in (0, 90, 180, 270):
        p -= arc_slot(xs, 0, ang, 3.4, 30.0, z0 - 1, z0 + HEAD_H, radial=0.6)
    # afgeschuinde vensterrand
    p -= Manifold.batch_hull([_sq(KOPP_WIN, 1.5, ROCKER_Z1 - 1.5, ROCKER_Z1 - 1.49, xs),
                              _sq(KOPP_WIN + 3.0, 3.0, ROCKER_Z1 + 0.01, ROCKER_Z1 + 0.02, xs)])
    return p


def wip(L):
    return _panel11(L, 0)


def mount_plate(L):
    xs = L['socket']
    m = cad11.mount_plate(dict(L, socket=None))
    z0, z1 = WALL_Z, WALL_Z + MP_T
    m += _sq(COLLAR, 3.0, z1 - 0.01, COLLAR_TOP, xs)
    m -= cyl_z(xs, 0, 30.0, z0 - 1, COLLAR_TOP + 1, seg=128)
    for ang in (0, 90, 180, 270):
        m -= arc_slot(xs, 0, ang, 2.1, 30.0, z0 - 1, COLLAR_TOP + 1)
    return m


def ring_dummy(L, deg=0.0):
    xs = L['socket']
    r = box(-RING_W / 2, RING_W / 2, -RING_W / 2, RING_W / 2, LIP_Z0 - RING_T, LIP_Z0)
    r -= cyl_z(0, 0, 27, -30, 30)
    for (dx, dy) in ((30, 0), (-30, 0), (0, 30), (0, -30)):
        r += cyl_z(dx, dy, 3.0, LIP_Z0, LIP_Z0 + HEAD_H - 0.1)
    return r.rotate((0, 0, deg)).translate((xs, 0, 0))
