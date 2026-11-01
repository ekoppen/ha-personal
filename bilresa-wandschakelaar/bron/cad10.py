"""BILRESA wandschakelaar v10
- wippen met taps schortje rondom (dik bovenaan, dun onderaan): bij indrukken kijk je niet meer naar binnen
- V5: dubbele doos met 1 knop + blinde helft (180 graden draaien = knop links of rechts)
- B1: losse blindplaat voor een enkele doos (zelfde montagebakje)
Rest als v9 (pin-scharnieren, dopjes, gemeten knoppositie).
"""
from manifold3d import Manifold
import cad9
from cad9 import (box, rslab, cyl_x, cyl_z, chamfered_slab, base, mount_plate, clips, nub_pin_tip,
                  nub_cup_assembled, cup_assembled, nub_cup, pen_cup, pen_tip, _layout,
                  H_IN, ROCKER_Z0, ROCKER_Z1, ROCKER_GAP, AXLE_Z, RIM_CLIP_W, CENTER_HALF, LUG_T, PIN_R,
                  BTN_Y9, NUB_PIN_R, PEN_R, PLATE_Z1, CHOC_Y, BOX_PITCH, RIM_T, UNIT_DY,
                  CUP_T, NUB_CUP_T, CUP_NOM, NUB_CUP_NOM)

APRON_Z = 4.9           # onderkant schortje
APRON_TOP_T = 2.0       # dikte bovenaan
APRON_BOT_T = 0.8       # dikte onderaan (taps)
LEG_R = 2.5             # pootjes onder blindplaat

W1, W2 = 86.2, BOX_PITCH + 86.2
WI1, WI2 = W1 - 2 * RIM_T, W2 - 2 * RIM_T
SCR1 = [(-36.5, -45.0), (36.5, -45.0), (-36.5, 45.0), (36.5, 45.0)]
SCR2 = [(x, y) for x in (-71.5, 0.0, 71.5) for y in (-45.0, 45.0)]


def L10(W, edges, slots, base_screws, boxes):
    """slots: per vak tussen edges: x-positie van de BILRESA, of None = blind"""
    units = [s for s in slots if s is not None]
    L = _layout(W, units, edges, base_screws, boxes)
    L['slots'] = slots
    return L


LAYOUTS = {
    'V1_enkel_1doos': L10(W1, [-WI1 / 2, WI1 / 2], [0.0], SCR1, [0.0]),
    'V2_dubbel_1doos': L10(W1, [-WI1 / 2, 0.0, WI1 / 2], [-20.0, 20.0], SCR1, [0.0]),
    'V3_dubbel_2dozen': L10(W2, [-WI2 / 2, 0.0, WI2 / 2], [-38.25, 38.25], SCR2, [-BOX_PITCH / 2, BOX_PITCH / 2]),
    'V4_vierdubbel_2dozen': L10(W2, [-WI2 / 2, -38.25, 0.0, 38.25, WI2 / 2], [-57.0, -19.5, 19.5, 57.0],
                                [(x, y) for x in (-71.5, -38.25, 0.0, 38.25, 71.5) for y in (-45.0, 45.0)],
                                [-BOX_PITCH / 2, BOX_PITCH / 2]),
    'V5_enkel_2dozen_blind': L10(W2, [-WI2 / 2, 0.0, WI2 / 2], [None, 38.25], SCR2, [-BOX_PITCH / 2, BOX_PITCH / 2]),
    'B1_blindplaat_1doos': L10(W1, [-WI1 / 2, WI1 / 2], [None], SCR1, [0.0]),
}


def tapered_strip(x0, x1, y0, y1, outer_side):
    """schortje: bovenaan APRON_TOP_T dik, onderaan APRON_BOT_T; buitenkant recht"""
    def strip(t, z0, z1):
        if outer_side == 'x-':
            return box(x0, x0 + t, y0, y1, z0, z1)
        if outer_side == 'x+':
            return box(x1 - t, x1, y0, y1, z0, z1)
        if outer_side == 'y-':
            return box(x0, x1, y0, y0 + t, z0, z1)
        return box(x0, x1, y1 - t, y1, z0, z1)
    return Manifold.batch_hull([strip(APRON_TOP_T, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                strip(APRON_BOT_T, APRON_Z, APRON_Z + 0.01)])


def panel(L, i):
    """wip (als slots[i] een BILRESA heeft) of vaste blindplaat (slots[i] is None)"""
    edges, (lo, hi) = L['edges'], L['rim']
    xu = L['slots'][i]
    x0, x1 = edges[i] + ROCKER_GAP, edges[i + 1] - ROCKER_GAP
    w, cx = x1 - x0, (x0 + x1) / 2
    hh = H_IN / 2 - ROCKER_GAP
    r = chamfered_slab(w, 2 * hh, 2.0, ROCKER_Z0, ROCKER_Z1, 0.6, cx, 0)
    # taps schortje rondom (niet bij de scharnieren)
    ap = tapered_strip(x0, x1, -hh, hh, 'x-') + tapered_strip(x0, x1, -hh, hh, 'x+')
    ap -= box(-500, 500, -5.0, 5.0, 0, 20)
    ap += tapered_strip(x0, x1, -hh, hh, 'y-') + tapered_strip(x0, x1, -hh, hh, 'y+')
    r += ap
    # scharnierlippen + pinnen
    for side in (-1, 1):
        B = edges[i] if side < 0 else edges[i + 1]
        if abs(B - lo) < 1e-6 or abs(B - hi) < 1e-6:
            cin, cout = B - side * RIM_CLIP_W, B - side * 0.3
        else:
            cin, cout = B - side * CENTER_HALF, B - side * 0.4
        lface = cin - side * 0.2
        la, lb = sorted((lface, lface - side * LUG_T))
        lug = box(la, lb, -3.0, 3.0, AXLE_Z, ROCKER_Z0 + 0.01) + cyl_x(la, lb, 0, AXLE_Z, 2.2)
        pa, pb = sorted((lface, cout))
        lug += cyl_x(pa - 0.01, pb + 0.01, 0, AXLE_Z, PIN_R)
        r += lug
    if xu is None:
        # blind: pootjes op de bodemplaat -> kantelt niet
        for x in (x0 + 6.0, x1 - 6.0):
            for y in (-30.0, 30.0):
                r += cyl_z(x, y, LEG_R, PLATE_Z1 + 0.15, ROCKER_Z0 + 0.01)
        return r
    for y in (-BTN_Y9, BTN_Y9):
        r += Manifold.batch_hull([cyl_z(xu, y, 2.4, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                  cyl_z(xu, y, NUB_PIN_R, ROCKER_Z0 - 1.2, ROCKER_Z0 - 1.19)])
        r += cyl_z(xu, y, NUB_PIN_R, nub_pin_tip(), ROCKER_Z0 - 1.19)
    for s in (-1, 1):
        yc = s * CHOC_Y
        r += Manifold.batch_hull([cyl_z(xu, yc, 3.2, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01),
                                  cyl_z(xu, yc, PEN_R, ROCKER_Z0 - 1.0, ROCKER_Z0 - 0.99)])
        r += cyl_z(xu, yc, PEN_R, pen_tip(), ROCKER_Z0 - 0.99)
    return r


def panels(L):
    return [panel(L, i) for i in range(len(L['slots']))]


# ------------------------------------------------------------------ v10.1: breed montagebakje voor 2 losse modules
from cad8 import WALL_Z, MP_T, PLATE_Z0, H_OUT
from cad import stadium
MOD_GAP = 0.4
MOD_PITCH = W1 + MOD_GAP                       # 86.6: twee enkele schakelaars direct naast elkaar


def mount_tray_2modules():
    """montagebakje (dubbele inbouwdoos, 71 mm) waarop 2 losse enkele schakelaars naast elkaar passen
    (bv. V2_dubbel_1doos + B1_blindplaat_1doos). Buitenmaat 172.8 x 103.4."""
    W = 2 * W1 + MOD_GAP
    z0, z1 = WALL_Z, WALL_Z + MP_T
    zt = PLATE_Z0 - 0.15
    outer = Manifold.batch_hull([rslab(W - 1.0, H_OUT - 1.0, 3.5, z0, z0 + 0.01),
                                 rslab(W, H_OUT, 4.0, z0 + 0.5, zt - 0.5),
                                 rslab(W - 1.0, H_OUT - 1.0, 3.5, zt - 0.01, zt)])
    m = outer - rslab(W - 2 * RIM_T, H_OUT - 2 * RIM_T, 2.0, z1, zt + 1)
    m += box(-2 * RIM_T, 2 * RIM_T, -H_OUT / 2 + 1, H_OUT / 2 - 1, z1 - 0.01, zt)     # middenrib onder de naad
    for bx in (-BOX_PITCH / 2, BOX_PITCH / 2):
        m -= rslab(46.0, 36.0, 6.0, z0 - 1, z1 + 1, cx=bx)
        for (x, y, d) in ((0, -30, 'x'), (0, 30, 'x'), (-30, 0, 'y'), (30, 0, 'y')):
            if d == 'x':
                m -= stadium(bx + x - 3, y, bx + x + 3, y, 2.1, z0 - 1, z1 + 1)
            else:
                m -= stadium(bx + x, y - 3, bx + x, y + 3, 2.1, z0 - 1, z1 + 1)
    for mx in (-MOD_PITCH / 2, MOD_PITCH / 2):
        for (x, y) in SCR1:
            m += cyl_z(mx + x, y, 4.0, z1 - 0.01, zt)
            m -= cyl_z(mx + x, y, 1.3, z0 + 0.6, zt + 1)
    return m
