"""BILRESA dubbele wandschakelaar - parametrisch model.
Alle maten in mm, in 'montage-coordinaten': muur (optie A) op z=-5,
bovenkant bodemplaat z=-2, scharnieras op z=3.6 / y=0.
Scharnier en drukpunten zijn afgeleid van 'IKEA BILRESA Wall Switch Adapter'
(theo.fieber). De klem-uitsparing voor printplaat + batterijen wordt 1-op-1
overgenomen uit de referentie 'IKEABILRESAWallfourBase.stl' (REF_STL).
Hoogte-ijkpunt: het midden van de batterijen ligt op z=0.
"""
import numpy as np
from manifold3d import Manifold, CrossSection, JoinType

SEG = 64
XU = 20.0            # x-positie van het midden van elke BILRESA-unit
BAT_DX = 9.35        # batterij-as t.o.v. unit-midden
BAT_R = 5.52         # straal batterijgoot
PIV_Z = 3.6          # scharnieras hoogte
CHOC_Y = 31.3        # Choc-switch midden (bovenkant)
USE_CHOC = False     # echte printplaat (63x29) loopt tot y=+33.5: geen ruimte voor Choc
SLOT_TRAVEL = 2.0    # verstelruimte schroefsleuven (+/-)
BTN_Y = 18.6         # nokjes op de BILRESA-knopjes (+/-)
NUB_EXT = 1.6        # v4: drukpunten langer (gemeten gat ~2 mm bij klem-bodemplaat)
NUB_Z = 6.0 - NUB_EXT
USE_SPRING = True    # bladveertjes (bruggetjes) in de bodemplaat + drukpennen onder de wip
SPRING_Y = 38.0      # midden van het bruggetje (+/-)
SPRING_PRELOAD = 0.4 # (wip) pen-onderkant ligt 0.4 onder bovenkant plaat
LEAF_L = 16.0        # v5: vrije lengte bladveer (aan 1 kant vast)
LEAF_W = 4.0         # v6: breedte bladveer (y) (was 3.0)
LEAF_INSET = 0.5     # v6: bladveer 0.5 mm naar binnen t.o.v. de pen (stevigere plaatrand)
LEAF_T = 1.0         # v6: dikte bladveer (5 lagen van 0.2) (was 0.8)
LEAF_RAISE = 0.4     # bladveer steekt 0.4 boven de plaat uit -> voorspanning 0.8 mm
LEAF_SLIT = 0.6      # spleet rondom de bladveer
LEAF_GAP = 0.25      # luchtspleet tussen bladveer en uitdrukbaar steunblokje
PLATE = 82.4
REF_STL = 'ref/base4c.stl'   # referentie, gecentreerd
REF_DZ = 3.55       # ref: batterijmidden op z=-3.55 -> hier z=0
REF_UNIT_Y = 22.95  # ref: middenlijn bovenste unit
REF_SCREW_X = 0.4   # ref x -> unit y verschuiving (schroefgat op y=-9.9)
PLATE_Z0, PLATE_Z1 = -9.4 + REF_DZ, -5.0 + REF_DZ   # -5.85 .. -1.45 (4.4 mm, als referentie)
REBATE_IN, REBATE_H = 78.0, 1.3
POST_TOP = 6.5        # v5: 1.7 mm materiaal boven het scharniergat
POST_FOOT_Y = 9.0    # v5: brede voet (lager deel van de pootjes loopt verder door)
POST_FOOT_Z = 4.2    # bovenkant van die voet (blijft onder de randen van de wip)
POST_Y = 5.5
SLOT = 2.2
HOLE_R = 1.2
# wanden (x-intervallen) van de scharnierpoten, rechterhelft; linkerhelft gespiegeld
OUTER_WALLS = [(35.0, 37.0), (39.2, 41.0)]          # spleet 37.0..39.2 (v5: binnenwand 2.0)
CENTER_WALLS = [(-5.0, -3.0), (-0.8, 0.8), (3.0, 5.0)]  # spleten -3..-0.8 en 0.8..3 (v5: wanden 2.0)
ROCKER_GAP = 0.6     # halve spleet tussen de twee wippen
ROCKER_Z0, ROCKER_Z1 = 7.0, 9.0
BRIDGE_T = 4.0       # dikte draagbrug (optie B)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def rrect(w, h, r):
    return CrossSection.square((w - 2 * r, h - 2 * r), center=True).offset(r, JoinType.Round, circular_segments=SEG)


def rslab(w, h, r, z0, z1, cx=0.0, cy=0.0):
    return rrect(w, h, r).extrude(z1 - z0).translate((cx, cy, z0))


def cyl_z(x, y, r, z0, z1, seg=SEG):
    return Manifold.cylinder(z1 - z0, r, r, seg).translate((x, y, z0))


def cyl_x(x0, x1, y, z, r, r2=None, seg=SEG):
    r2 = r if r2 is None else r2
    return Manifold.cylinder(x1 - x0, r, r2, seg).rotate((0, 90, 0)).translate((x0, y, z))


def cyl_y(y0, y1, x, z, r, seg=SEG):
    return Manifold.cylinder(y1 - y0, r, r, seg).rotate((-90, 0, 0)).translate((x, y0, z))


def stadium(x0, y0, x1, y1, r, z0, z1):
    return Manifold.batch_hull([cyl_z(x0, y0, r, z0, z1), cyl_z(x1, y1, r, z0, z1)])


def chamfered_slab(w, h, r, z0, z1, ch, cx=0, cy=0, top=True):
    """afgeronde plaat met afgeschuinde boven- (of onder)rand"""
    if top:
        a = rslab(w, h, r, z0, z1 - ch, cx, cy)
        b = rslab(w - 2 * ch, h - 2 * ch, max(r - ch, 0.2), z1 - 0.01, z1, cx, cy)
    else:
        a = rslab(w, h, r, z0 + ch, z1, cx, cy)
        b = rslab(w - 2 * ch, h - 2 * ch, max(r - ch, 0.2), z0, z0 + 0.01, cx, cy)
    return Manifold.batch_hull([a, b])


# ---------------------------------------------------------------- bodemplaat
def post(walls):
    """scharnierpoot: wanden met doorgaand gat + inloop-afschuining"""
    body = Manifold()
    for (a, b) in walls:
        body += box(a, b, -POST_Y, POST_Y, PLATE_Z1 - 0.01, POST_TOP)
        # brede voet: onderste deel loopt verder door in y, met schuine (printbare) uiteinden
        foot = box(a, b, -POST_FOOT_Y, POST_FOOT_Y, PLATE_Z1 - 0.01, PLATE_Z1)
        foot = Manifold.batch_hull([foot, box(a, b, -POST_FOOT_Y + 2.0, POST_FOOT_Y - 2.0, POST_FOOT_Z - 0.01, POST_FOOT_Z)])
        body += foot
    xs = [w for pair in walls for w in pair]
    body -= cyl_x(min(xs) - 1, max(xs) + 1, 0, PIV_Z, HOLE_R)
    # inloop-afschuining bovenaan elke spleet
    for i in range(len(walls) - 1):
        s0, s1 = walls[i][1], walls[i + 1][0]
        wedge = Manifold.batch_hull([
            box(s0, s1, -POST_Y - 1, POST_Y + 1, POST_TOP - 1.0, POST_TOP - 0.99),
            box(s0 - 0.6, s1 + 0.6, -POST_Y - 1, POST_Y + 1, POST_TOP, POST_TOP + 0.5)])
        body -= wedge
    return body


def choc_cut(cx, cy):
    c = cyl_z(cx, cy, 1.8, -10, 10)                       # middengat 3.6
    for dx in (-5.5, 5.5):
        c += cyl_z(cx + dx, cy, 1.025, -10, 10)           # pootjes 2.05
    for (dx, dy) in ((0, -6.2), (-5.25, -4.58), (5.25, -4.58)):
        c += box(cx + dx - 0.75, cx + dx + 0.75, cy + dy - 0.75, cy + dy + 0.75, -10, 10)  # pinnen
    return c


def unit_cuts(xu):
    c = Manifold()
    for s in (-1, 1):
        c += cyl_y(-22.0, 23.0, xu + s * BAT_DX, 0.0, BAT_R, 96)       # batterijgoten
    c += box(xu - 9.5, xu + 9.5, -28.0, -22.0, -3.0, -1.9)            # uitsparing contactbrug
    c += cyl_z(xu, -9.9, 1.0, -10, 10)                                 # BILRESA-schroef
    if USE_CHOC:
        c += choc_cut(xu, CHOC_Y)
    return c


def unit_adds(xu):
    a = Manifold()
    for s in (-1, 1):   # geleiderails voor de printplaat
        xa, xb = sorted((xu + s * 3.2, xu + s * 4.2))
        a += box(xa, xb, -12.0, 13.0, PLATE_Z1 - 0.01, -1.0)
    return a


_REF_BLOCK = None
REF_BOX = (-39.6, 40.0, 7.0, 39.5)   # unit-gebied in ref-coordinaten (x0,x1,y0,y1)


def ref_unit_block():
    """klem-uitsparing van een unit uit de referentie, gedraaid zodat de lange as langs y loopt
    (ronde kant boven) en op unit-coordinaten (midden x=0, batterijmidden z=0) gezet."""
    global _REF_BLOCK
    if _REF_BLOCK is None:
        import trimesh
        from manifold3d import Mesh
        t = trimesh.load(REF_STL)
        m = Manifold(Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
        x0, x1, y0, y1 = REF_BOX
        m = m ^ box(x0, x1, y0, y1, -20, 20)
        # (x, y) -> (-(y - Yc), x - dx) : rotatie 90 graden
        m = m.translate((-REF_SCREW_X, -REF_UNIT_Y, REF_DZ)).rotate((0, 0, 90))
        _REF_BLOCK = m
    return _REF_BLOCK


def pocket_outline():
    """contour van de printplaat-uitsparing (uit de referentie, unit-coordinaten)"""
    import pickle
    uv = pickle.load(open('ref/pocket_outline_unit.pkl', 'rb'))
    return CrossSection([np.asarray(uv).tolist()])


def ref_unit_footprint():
    x0, x1, y0, y1 = REF_BOX
    return box(x0, x1, y0, y1, -20, 20).translate((-REF_SCREW_X, -REF_UNIT_Y, 0)).rotate((0, 0, 90))


def plate():
    p = rslab(PLATE, PLATE, 2.4, PLATE_Z0, PLATE_Z1)
    for xu in (-XU, XU):   # klem-uitsparing incl. +/- tekens voor de batterijen
        p -= ref_unit_footprint().translate((xu, 0, 0))
        p += ref_unit_block().translate((xu, 0, 0))
    # scharnierpoten
    p += post(OUTER_WALLS)
    p += post([(-b, -a) for (a, b) in reversed(OUTER_WALLS)])
    p += post(CENTER_WALLS)
    # gaten van de scharnierpoten (opnieuw, voor het geval de goot-wand ertegen ligt)
    p -= cyl_x(-42, 42, 0, PIV_Z, HOLE_R)
    # spleten vrijhouden
    for (s0, s1) in [(OUTER_WALLS[0][1], OUTER_WALLS[1][0]), (-OUTER_WALLS[1][0], -OUTER_WALLS[0][1]),
                     (CENTER_WALLS[0][1], CENTER_WALLS[1][0]), (CENTER_WALLS[1][1], CENTER_WALLS[2][0])]:
        p -= box(s0, s1, -POST_Y - 1, POST_Y + 1, PLATE_Z1, POST_TOP + 1)
    # sponning aan de onderrand voor de lip van het frame
    ring = rslab(PLATE + 2, PLATE + 2, 2, PLATE_Z0 - 1, PLATE_Z0 + REBATE_H) - \
        rslab(REBATE_IN, REBATE_IN, 1.5, PLATE_Z0 - 2, PLATE_Z0 + REBATE_H + 1)
    p -= ring
    p = p ^ rslab(PLATE, PLATE, 2.4, PLATE_Z0 - 1, 20)
    # bladveertjes
    if USE_SPRING:
        for xu in (-XU, XU):
            for sgn in (-1, 1):
                void, leaf, column = leaf_spring(xu, sgn)
                p = (p - void) + leaf + column
                # het min-teken dat onder de veer verdwijnt, liggend ernaast terugzetten
                mx = xu + sgn * 8.55
                yy = sorted((sgn * 33.0, sgn * 36.0))
                p -= box(mx - 1.0, mx + 1.0, yy[0], yy[1], PLATE_Z1 + 0.001, PLATE_Z1 + 0.5)   # restje oud teken
                p += box(mx - 1.85, mx + 1.85, sgn * 33.7 - 0.6, sgn * 33.7 + 0.6, PLATE_Z1 - 0.01, PLATE_Z1 + 0.2)
    # schroefsleuven inbouwdoos (boven/onder, 60 mm) - verstelbaar +/-2 mm
    for y in (-30.0, 30.0):
        p -= stadium(-SLOT_TRAVEL, y, SLOT_TRAVEL, y, 2.0, -10, 10)
    return p


# ---------------------------------------------------------------- wip (links, x<0)
def spring_pen(xu, sgn):
    """drukpen onder de wip die op het bruggetje in de bodemplaat rust (met voorspanning)"""
    zb = PLATE_Z1 - SPRING_PRELOAD
    pen = cyl_z(xu, sgn * SPRING_Y, 1.2, zb + 0.6, ROCKER_Z0 + 0.01)
    pen += Manifold.batch_hull([cyl_z(xu, sgn * SPRING_Y, 1.2, zb + 0.6, zb + 0.61), cyl_z(xu, sgn * SPRING_Y, 0.8, zb, zb + 0.01)])
    pen += Manifold.batch_hull([cyl_z(xu, sgn * SPRING_Y, 2.2, ROCKER_Z0 - 0.01, ROCKER_Z0 + 0.01), cyl_z(xu, sgn * SPRING_Y, 1.2, 2.5, 2.51)])
    return pen


def leaf_spring(xu, sgn):
    """bladveer in de bodemplaat onder de drukpen van de wip.
    Vast aan 1 kant, vrij uiteinde onder de pen. Tijdens printen rust het vrije uiteinde
    op een los steunblokje (0.25 mm luchtspleet) dat je na het printen er van achteren uitdrukt.
    Boven: veer loopt naar +x; onder: naar -x (zo blijft bij elke batterij het +teken heel)."""
    y0 = sgn * (SPRING_Y - LEAF_INSET)
    d = sgn                      # richting naar het vaste uiteinde
    xf = xu - d * 1.5            # vrij uiteinde (net voorbij de pen)
    xa = xf + d * LEAF_L         # begin van het vaste deel
    hw = LEAF_W / 2
    z1 = PLATE_Z1 + LEAF_RAISE
    z0 = z1 - LEAF_T
    xs = sorted((xf - d * LEAF_SLIT, xa))
    void = box(xs[0], xs[1], y0 - hw - LEAF_SLIT, y0 + hw + LEAF_SLIT, PLATE_Z0 - 1, z1 + 1)
    xl = sorted((xf, xa + d * 2.0))
    leaf = box(xl[0], xl[1], y0 - hw, y0 + hw, z0, z1)
    xc = sorted((xf, xf + d * 3.0))
    column = box(xc[0], xc[1], y0 - hw + 0.3, y0 + hw - 0.3, PLATE_Z0, z0 - LEAF_GAP)
    return void, leaf, column


def rocker_left():
    x0, x1 = -40.5, -ROCKER_GAP
    w, cx = x1 - x0, (x0 + x1) / 2
    r = chamfered_slab(w, 81.0, 1.5, ROCKER_Z0, ROCKER_Z1, 0.5, cx, 0)
    zs0 = 5.0
    # randen (stijfheid + afscherming), met inkeping bij de scharnierpoten
    skirt = box(x0, x0 + 1.2, -40.5 + 1.0, 40.5 - 1.0, zs0, ROCKER_Z0 + 0.01) + \
        box(x1 - 1.2, x1, -40.5 + 1.0, 40.5 - 1.0, zs0, ROCKER_Z0 + 0.01)
    skirt -= box(-50, 50, -6.5, 6.5, 0, 20)
    skirt += box(x0 + 1.0, x1 - 1.0, 39.3, 40.5 - 0.3, 5.5, ROCKER_Z0 + 0.01)
    skirt += box(x0 + 1.0, x1 - 1.0, -40.5 + 0.3, -39.3, 5.5, ROCKER_Z0 + 0.01)
    r += skirt
    # scharnierlippen met klik-nokjes
    for lx in (-(OUTER_WALLS[0][1] + OUTER_WALLS[1][0]) / 2, (CENTER_WALLS[0][1] + CENTER_WALLS[1][0]) / 2):
        a, b = lx - 1.0, lx + 1.0
        lug = box(a, b, -3.5, 3.5, PIV_Z, ROCKER_Z0 + 0.01) + cyl_x(a, b, 0, PIV_Z, 3.5)
        lug += cyl_x(a + 0.01, b - 0.01, 0, PIV_Z, 1.0)
        lug += cyl_x(b - 0.01, b + 0.5, 0, PIV_Z, 1.0, 0.55)
        lug += cyl_x(a - 0.5, a + 0.01, 0, PIV_Z, 0.55, 1.0)
        r += lug
    # drukpunten op de BILRESA-knopjes en de Choc-switch
    xu = -XU
    for y in (-BTN_Y, BTN_Y):
        r += cyl_z(xu, y, 2.0, 5.6, ROCKER_Z0 + 0.01)            # stevige voet
        r += Manifold.batch_hull([cyl_z(xu, y, 2.0, 5.59, 5.6), cyl_z(xu, y, 1.25, 5.1, 5.11)])
        r += cyl_z(xu, y, 1.25, NUB_Z, 5.11)                      # drukpunt
    if USE_SPRING:
        for sgn in (-1, 1):
            r += spring_pen(xu, sgn)
    if USE_CHOC:
        r += cyl_z(xu, CHOC_Y, 2.0, 6.5, ROCKER_Z0 + 0.01)
    return r


def mirror_x(m):
    return m.mirror((1, 0, 0))


# ---------------------------------------------------------------- frame
def frame(wall_z):
    z0, z1 = wall_z, 6.0
    outer = chamfered_slab(86.2, 86.2, 3.5, z0, z1, 0.6)
    f = outer - rslab(82.8, 82.8, 2.2, z0 - 1, z1 + 1)
    lip_top = PLATE_Z0 + REBATE_H - 0.1
    lip = rslab(82.9, 82.9, 2.2, z0, lip_top) - rslab(REBATE_IN + 0.4, REBATE_IN + 0.4, 1.95, z0 - 1, lip_top + 1)
    return f + lip


# ---------------------------------------------------------------- draagbrug (optie B)
def bridge():
    z0, z1 = PLATE_Z0 - BRIDGE_T, PLATE_Z0
    b = rslab(72.0, 12.0, 4, z0, z1) + rslab(12.0, 71.0, 4, z0, z1)
    for s in (-1, 1):
        b += rslab(14.0, 19.0, 4, z0, z1, cx=s * 30.0)
        # sleuf voor de schroef van de inbouwdoos (links/rechts), verzonken kop
        b -= stadium(s * 30, -4, s * 30, 4, 2.0, z0 - 1, z1 + 1)
        b -= stadium(s * 30, -4, s * 30, 4, 4.0, z1 - 2.7, z1 + 1)
        # M3-gat + moeropsluiting voor de bodemplaat
        b -= cyl_z(0, s * 30.0, 1.6, z0 - 1, z1 + 1)
        b -= cyl_z(0, s * 30.0, 3.2, z0 - 1, z0 + 2.6, seg=6)
    # ondiepe goten: de batterijen steken ~0.3 mm onder de bodemplaat uit
    for xu in (-XU, XU):
        for s in (-1, 1):
            b -= cyl_y(-23.0, 24.0, xu + s * BAT_DX, 0.0, 5.65, 96)
    return b


if __name__ == '__main__':
    import trimesh
    def tm(m):
        g = m.to_mesh()
        return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)
    parts = {
        'bodemplaat': plate(),
        'wip_links': rocker_left(),
        'wip_rechts': mirror_x(rocker_left()),
        'frame_A_schroeven_boven_onder': frame(PLATE_Z0),
        'frame_B_met_draagbrug': frame(PLATE_Z0 - BRIDGE_T),
        'draagbrug_schroeven_links_rechts': bridge(),
    }
    import pickle
    out = {}
    for k, m in parts.items():
        t = tm(m)
        print(f'{k:36s} watertight={t.is_watertight} vol={t.volume:8.0f} bounds={np.round(t.bounds,2).tolist()} genus={m.genus()}')
        out[k] = t
    pickle.dump(out, open('parts.pkl', 'wb'))
