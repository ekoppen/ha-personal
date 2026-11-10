"""BILRESA wandschakelaar v12 - C2 met Kopp-stopcontact
Verschil met v11 (Jung):
- het raam wordt nu net als een echt Kopp-raam door het stopcontact vastgezet: onderin het venster zit een dun
  randje dat tussen de draagring en de centraalplaat wordt geklemd (randje = onderste lagen van de basis,
  print dus gewoon zonder support)
- de draagring ligt op een verhoging in het montagebakje, zodat de bovenkant precies tegen de onderkant van de
  basis komt
- draaien: alle schroefgaten in het bakje zijn sleuven (ca. +/- 3 graden) en de draagring heeft rondom ruimte
Alle maten van het Kopp-raam staan bovenaan en zijn VOORLOPIG tot ze gemeten zijn.
"""
import math
from manifold3d import Manifold, CrossSection
import cad11
from cad11 import (box, rslab, cyl_z, stadium, _layout, clips, panel as _panel11, base as _base11,
                   S, H_OUT, H_IN, RIM_T, WALL_Z, MP_T, PLATE_Z0, PLATE_Z1, ROCKER_Z0, ROCKER_Z1, BOX_PITCH,
                   WI2, W2, E2, XU2, XS2, TUBE_T, LEG_R)

# ---- Kopp-raam (gemeten door Eelko: venster 55.5, randje-opening 48; inkepingen geschat van foto) ----
KOPP_WIN = 55.8        # venster (gemeten 55.5 + 0.3 speling)
LIP_IN = 48.0          # opening tussen het dunne randje (gemeten)
LIP_T = 1.5            # dikte randje: met de pasproefjes (1.0/1.5/2.0/2.5) uitzoeken
LIP_TS = (1.0, 1.5, 2.0, 2.5)
NOTCHES = ((14.0, 26.0), (11.0, KOPP_WIN / 2))   # trapsgewijze inkeping midden in elke kant: (breedte, tot)
RING_W = 71.0          # buitenmaat draagring
RING_T = 1.0           # dikte draagring
HEAD_H = 2.6           # hoogte schroefkop boven de draagring
ROT_DEG = 3.0          # draairuimte (+/- graden)
PAD = 74.5             # verhoging in het bakje waar de draagring op ligt

LAYOUTS = {
    'C2_enkel_plus_stopcontact_kopp': _layout(W2, [XU2], [-WI2 / 2, E2, WI2 / 2], [XU2, None],
                                              [(x, sy * 10.0) for x in (XU2 - 33.5, -5.0) for sy in (-1, 1)],
                                              [-BOX_PITCH / 2], socket=XS2),
}


def _sq(w, r, z0, z1, cx):
    return rslab(w, w, r, z0, z1, cx=cx)


def lip_opening(xs, z0, z1):
    o = _sq(LIP_IN, 1.5, z0, z1, xs)
    for ang in (0, 90, 180, 270):
        n = Manifold()
        for (w, to) in NOTCHES:
            n += box(-w / 2, w / 2, LIP_IN / 2 - 1, to, z0, z1)
        o += n.rotate((0, 0, ang)).translate((xs, 0, 0))
    return o


def test_piece(t):
    """pasproefje: alleen het venster met randje (t mm dik); t streepjes op de rand"""
    h = t + 3.0
    p = _sq(KOPP_WIN + 10, 3.0, 0, h, 0)
    p -= _sq(KOPP_WIN, 1.5, t, h + 1, 0)
    p -= lip_opening(0, -1, h + 1)
    n = LIP_TS.index(t) + 1
    for k in range(n):
        x = -6 + k * 4.0
        p -= box(x - 0.8, x + 0.8, KOPP_WIN / 2 + 2.0, KOPP_WIN / 2 + 5.5, h - 0.6, h + 1)
    return p


def arc_slot(xc, yc, ang, r, rad, z0, z1, halfdeg=ROT_DEG + 2.5, radial=1.2):
    """sleuf langs een cirkelboog (draaien) en iets radiaal (doos niet precies 71 mm)"""
    pts = []
    for k in range(9):
        a = math.radians(ang - halfdeg + 2 * halfdeg * k / 8)
        for dr in (-radial, radial):
            pts.append(cyl_z(xc + (rad + dr) * math.cos(a), yc + (rad + dr) * math.sin(a), r, z0, z1, seg=24))
    out = Manifold()
    for k in range(8):
        out += Manifold.batch_hull(pts[2 * k:2 * k + 4])
    return out


def base(L):
    xs = L['socket']
    b = _base11(dict(L, socket=None))
    # venster: boven het randje KOPP_WIN, onderin het randje (LIP_T dik) met LIP_IN
    b -= _sq(KOPP_WIN, 1.5, PLATE_Z0 + LIP_T, 30, xs)
    b -= lip_opening(xs, -30, 30)
    # schroefkoppen van de draagring (draaibaar) - van onderen
    for ang in (0, 90, 180, 270):
        b -= arc_slot(xs, 0, ang, 3.4, 30.0, PLATE_Z0 - 1, PLATE_Z0 + HEAD_H, radial=0.6)
    return b


def panel(L, i):
    if L['slots'][i] is not None:
        return _panel11(L, i)
    cad11.WIN = KOPP_WIN
    try:
        return _panel11(L, i)
    finally:
        cad11.WIN = 56.0  # terug naar v11-waarde


def panels(L):
    return [panel(L, i) for i in range(len(L['slots']))]


def mount_plate(L):
    xs = L['socket']
    m = cad11.mount_plate(dict(L, socket=None))
    z0, z1 = WALL_Z, WALL_Z + MP_T
    ztop = PLATE_Z0 - RING_T                       # bovenkant verhoging = onderkant draagring
    pad = _sq(PAD, 3.0, z1 - 0.01, ztop, xs) ^ box(-500, 500, -H_IN / 2 + 0.01, H_IN / 2 - 0.01, -50, 50)
    m += pad
    m -= cyl_z(xs, 0, 30.0, z0 - 1, ztop + 1, seg=128)          # binnenwerk stopcontact
    for ang in (0, 90, 180, 270):
        m -= arc_slot(xs, 0, ang, 2.1, 30.0, z0 - 1, ztop + 1)
    return m


def ring_dummy(L, deg=0.0):
    xs = L['socket']
    r = box(-RING_W / 2, RING_W / 2, -RING_W / 2, RING_W / 2, PLATE_Z0 - RING_T, PLATE_Z0)
    r -= cyl_z(0, 0, 27, -30, 30)
    for (dx, dy) in ((30, 0), (-30, 0), (0, 30), (0, -30)):
        r += cyl_z(dx, dy, 3.0, PLATE_Z0, PLATE_Z0 + HEAD_H - 0.1)
    return r.rotate((0, 0, deg)).translate((xs, 0, 0))
