"""
Pixel-art drawing for Top-Down Town.

Everything here is drawn at a small "logical" size (16 x 16 pixels per tile) with hand-placed pixels,
outlines and shading, then scaled up 4x with hard edges, so every object in the game shares one
chunky pixel grid. All art is generated in code - there are no image files to load.
"""

import math
import random
import pygame

PX = 4                  # each art pixel becomes a 4x4 block on screen
L = 16                  # logical tile size (16 * 4 = 64 screen pixels)

OUTLINE = (44, 36, 40)
WHITE = (240, 238, 228)


# ============================================================== helpers
def up(s: pygame.Surface) -> pygame.Surface:
    """Scale logical art to screen size with hard pixel edges."""
    return pygame.transform.scale(s, (s.get_width() * PX, s.get_height() * PX))


def canvas(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def R(s, c, x, y, w, h):
    if w > 0 and h > 0:
        s.fill(c, (x, y, w, h))


def P(s, c, x, y):
    if 0 <= x < s.get_width() and 0 <= y < s.get_height():
        s.set_at((x, y), c)


def speckle(s, rng, colours, density, area=None):
    x0, y0, w, h = area or (0, 0, s.get_width(), s.get_height())
    for _ in range(int(w * h * density)):
        P(s, rng.choice(colours), x0 + rng.randrange(w), y0 + rng.randrange(h))


def add_outline(s, colour=OUTLINE):
    """1px outline around every opaque pixel (canvas grows by 1 on each side)."""
    w, h = s.get_size()
    out = canvas(w + 2, h + 2)
    m = pygame.mask.from_surface(s, 127)
    sil = m.to_surface(setcolor=colour + (255,), unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        out.blit(sil, (dx, dy))
    out.blit(s, (1, 1))
    return out


def circle(s, c, cx, cy, r):
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            if x * x + y * y <= r * r + r * 0.6:
                P(s, c, cx + x, cy + y)


def ellipse_fill(s, c, cx, cy, rx, ry):
    for y in range(-ry, ry + 1):
        for x in range(-rx, rx + 1):
            if (x / max(rx, 0.5)) ** 2 + (y / max(ry, 0.5)) ** 2 <= 1.0:
                P(s, c, cx + x, cy + y)


def pixelize(img: pygame.Surface) -> pygame.Surface:
    """Turn a smooth sprite into chunky pixels on the same 4x grid."""
    w, h = img.get_size()
    sw, sh = max(1, w // PX), max(1, h // PX)
    small = pygame.transform.smoothscale(img, (sw, sh))
    arr = pygame.PixelArray(small)
    for x in range(sw):
        for y in range(sh):
            c = small.unmap_rgb(arr[x, y])
            arr[x, y] = (c.r, c.g, c.b, 255 if c.a > 110 else 0)
    del arr
    return up(small).convert_alpha()


# ============================================================== ground
GRASS = [(96, 166, 72), (82, 150, 64), (120, 186, 86), (66, 130, 58), (140, 200, 96)]
SLAB = (182, 176, 164)
SLAB_J = (150, 145, 136)
SLAB_L = (200, 195, 184)
TARMAC = (70, 72, 78)
YELLOW = (232, 192, 52)


def grass_tile(v):
    rng = random.Random(1000 + v)
    s = canvas(L, L)
    s.fill(GRASS[0])
    for _ in range(3):                                          # soft patches of lighter / darker grass
        cx, cy = rng.randrange(L), rng.randrange(L)
        col = GRASS[1] if rng.random() < 0.6 else GRASS[2]
        for _ in range(14):
            P(s, col, (cx + rng.randrange(-3, 4)) % L, (cy + rng.randrange(-2, 3)) % L)
    speckle(s, rng, [GRASS[1]], 0.12)
    speckle(s, rng, [GRASS[2]], 0.05)
    for _ in range(3 + v % 3):                                  # tufts of blades, dark at the root
        x, y = rng.randrange(1, L - 4), rng.randrange(3, L - 1)
        P(s, GRASS[3], x, y); P(s, GRASS[3], x + 1, y); P(s, GRASS[3], x + 2, y); P(s, GRASS[3], x + 3, y)
        P(s, GRASS[1], x, y - 1); P(s, GRASS[2], x + 1, y - 1); P(s, GRASS[2], x + 2, y - 1); P(s, GRASS[1], x + 3, y - 1)
        P(s, GRASS[4], x + 1, y - 2); P(s, GRASS[2], x + 3, y - 2); P(s, GRASS[4], x, y - 2)
    if v % 3 == 0:                                              # a few flowers
        for _ in range(2):
            x, y = rng.randrange(2, L - 3), rng.randrange(2, L - 3)
            col = rng.choice([(236, 120, 160), (250, 226, 90), (248, 248, 240), (170, 140, 230)])
            P(s, col, x, y); P(s, col, x + 1, y); P(s, col, x, y + 1); P(s, col, x + 1, y + 1)
            P(s, (250, 200, 60), x, y)
    return up(s).convert()


def paving_tile(v, base=SLAB):
    """Grey York-stone style pavement slabs."""
    rng = random.Random(2000 + v)
    s = canvas(L, L)
    joint, light = shade(base, 0.83), shade(base, 1.09)
    for sy, row_off in ((0, 0), (8, 4)):
        for sx in range(-8, L, 8):
            x0 = sx + row_off
            tone = shade(base, rng.uniform(0.95, 1.04))
            R(s, tone, x0, sy, 8, 8)
            R(s, light, x0, sy, 8, 1)
            R(s, light, x0, sy, 1, 8)
            R(s, joint, x0 + 7, sy, 1, 8)
            R(s, joint, x0, sy + 7, 8, 1)
    speckle(s, rng, [shade(base, 0.9), shade(base, 1.05)], 0.06)
    return up(s).convert()


def tarmac_tile(v):
    rng = random.Random(3000 + v)
    s = canvas(L, L)
    s.fill(TARMAC)
    speckle(s, rng, [shade(TARMAC, 0.86), shade(TARMAC, 1.14)], 0.22)
    if v % 5 == 0:                                              # repaired patch
        R(s, shade(TARMAC, 0.92), rng.randrange(0, 8), rng.randrange(0, 8), 6, 5)
    return s


def road_tile(v, mark=None):
    s = tarmac_tile(v)
    if mark == "h":                                             # dashed white centre line
        R(s, WHITE, 2, 7, 8, 2)
        R(s, shade(WHITE, 0.85), 2, 8, 8, 1)
    elif mark == "v":
        R(s, WHITE, 7, 2, 2, 8)
    elif mark == "zebra":
        for y in (1, 9):
            R(s, WHITE, 1, y, 14, 5)
            R(s, shade(WHITE, 0.88), 1, y + 4, 14, 1)
    return up(s).convert()


def gravel_tile(v):
    rng = random.Random(4000 + v)
    s = canvas(L, L)
    base = (196, 170, 120)
    s.fill(base)
    speckle(s, rng, [shade(base, 0.85), shade(base, 1.1), (170, 150, 110)], 0.3)
    for _ in range(4):
        x, y = rng.randrange(1, L - 2), rng.randrange(1, L - 2)
        P(s, (230, 220, 200), x, y); P(s, shade(base, 0.7), x + 1, y + 1)
    return up(s).convert()


def water_tile(v):
    rng = random.Random(5000 + v)
    s = canvas(L, L)
    base = (66, 140, 196)
    s.fill(base)
    speckle(s, rng, [shade(base, 0.9)], 0.15)
    for _ in range(2):
        x, y = rng.randrange(0, L - 5), rng.randrange(1, L - 1)
        R(s, (150, 206, 236), x, y, 4, 1)
    return up(s).convert()


def wood_floor_tile(v):
    rng = random.Random(6000 + v)
    s = canvas(L, L)
    base = (186, 132, 82)
    for i, y in enumerate(range(0, L, 4)):
        tone = shade(base, rng.uniform(0.92, 1.06))
        R(s, tone, 0, y, L, 4)
        R(s, shade(base, 0.75), 0, y + 3, L, 1)
        R(s, shade(base, 0.75), (i * 7 + v * 3) % L, y, 1, 3)
    return up(s).convert()


def kerb_and_lines(surf, px, py, sides, yellow=True):
    """Draw kerb stones (and double yellow lines) on a road tile already blitted at (px, py) in a chunk.
    sides: set of 'n','s','w','e' where the neighbour is not road."""
    T = L * PX
    kerb, kerb_d = (196, 192, 182), (110, 108, 104)
    for side in sides:
        if side == "n":
            surf.fill(kerb, (px, py, T, 2 * PX)); surf.fill(kerb_d, (px, py + 2 * PX, T, PX))
            if yellow:
                surf.fill(YELLOW, (px, py + 4 * PX, T, PX)); surf.fill(YELLOW, (px, py + 6 * PX, T, PX))
        elif side == "s":
            surf.fill(kerb_d, (px, py + T - 3 * PX, T, PX)); surf.fill(kerb, (px, py + T - 2 * PX, T, 2 * PX))
            if yellow:
                surf.fill(YELLOW, (px, py + T - 5 * PX, T, PX)); surf.fill(YELLOW, (px, py + T - 7 * PX, T, PX))
        elif side == "w":
            surf.fill(kerb, (px, py, 2 * PX, T)); surf.fill(kerb_d, (px + 2 * PX, py, PX, T))
        elif side == "e":
            surf.fill(kerb_d, (px + T - 3 * PX, py, PX, T)); surf.fill(kerb, (px + T - 2 * PX, py, 2 * PX, T))


def wall_shadow(surf, px, py):
    """Soft shadow at the foot of a building front, on the ground tile below it."""
    T = L * PX
    sh = pygame.Surface((T, 4 * PX), pygame.SRCALPHA)
    sh.fill((20, 16, 30, 70), (0, 0, T, 2 * PX))
    sh.fill((20, 16, 30, 35), (0, 2 * PX, T, 2 * PX))
    surf.blit(sh, (px, py))


# ============================================================== buildings
# Bath stone and the other materials of Queens Road
GLASS = (52, 66, 88)
GLASS_M = (78, 104, 132)
GLASS_L = (160, 196, 218)
FRAME = (238, 234, 222)
IRON = (34, 36, 42)
SLATE = (94, 104, 120)

FLOOR_H = 9          # logical pixels per upper storey
GROUND_H = 17        # shop / ground floor (tall enough for a fascia sign)
CORNICE_H = 4


def building_height(b):
    """Facade height in logical pixels for a building record."""
    if b.get("h"):                                                   # set by hand in the map (e.g. a low wall)
        return int(b["h"])
    st = b["style"]
    if st == "H":
        floors = max(2, min(4, int(b.get("floors", 3))))
        return GROUND_H + floors * FLOOR_H + CORNICE_H
    if st == "U":
        floors = max(2, min(5, int(b.get("floors", 4))))
        return GROUND_H + floors * FLOOR_H + 2
    return {"V": 46, "A": 42, "M": 48, "G": 42, "W": 52, "C": 44, "K": 44, "D": 54, "X": 30, "O": 44, "P": 22,
            "R": 46, "B": 40, "Z": 30}[st]


TOWER_H = 104        # logical height of the Wills Memorial tower facade


def _ashlar(s, base, rng, x0=0, y0=0, w=None, h=None, course=3):
    """Bath-stone blockwork: courses with staggered joints and a little texture."""
    w = w or s.get_width(); h = h or s.get_height()
    R(s, base, x0, y0, w, h)
    joint, light = shade(base, 0.86), shade(base, 1.05)
    for i, y in enumerate(range(y0 + course - 1, y0 + h, course)):
        R(s, joint, x0, y, w, 1)
        off = 0 if i % 2 else 3
        for x in range(x0 + off, x0 + w, 6):
            P(s, joint, x, y - 1)
            P(s, light, x + 1, y - course + 1)
    speckle(s, rng, [shade(base, 0.95), shade(base, 1.03)], 0.05, (x0, y0, w, h))


def _sash(s, x, y, w=6, h=7, arch=False, stone=(220, 200, 156)):
    """Georgian sash window with white frame, glazing bars, stone lintel and sill."""
    R(s, shade(stone, 1.08), x - 1, y - 1, w + 2, 1)             # lintel
    R(s, FRAME, x, y, w, h)
    R(s, GLASS, x + 1, y + 1, w - 2, h - 2)
    R(s, GLASS_M, x + 1, y + 1, w - 2, 1)
    P(s, GLASS_L, x + 1, y + 1)
    R(s, FRAME, x, y + h // 2, w, 1)                              # meeting rail
    R(s, FRAME, x + w // 2, y + 1, 1, h - 2)
    R(s, shade(stone, 0.78), x - 1, y + h, w + 2, 1)              # sill
    if arch:
        P(s, (0, 0, 0, 0), x, y); P(s, (0, 0, 0, 0), x + w - 1, y)
        R(s, shade(stone, 1.1), x, y - 2, w, 1)
        P(s, shade(stone, 0.8), x + w // 2, y - 2)                 # keystone


def _cornice(s, stone, y=0, balustrade=False):
    w = s.get_width()
    R(s, shade(stone, 0.62), 0, y, w, 1)
    R(s, shade(stone, 1.12), 0, y + 1, w, 1)
    R(s, stone, 0, y + 2, w, 1)
    for x in range(0, w, 2):                                       # dentils
        P(s, shade(stone, 0.72), x, y + 2)
    R(s, shade(stone, 0.7), 0, y + 3, w, 1)
    if balustrade:
        for x in range(1, w, 3):
            P(s, shade(stone, 0.75), x, y + 1)


def _shopfront(s, y, colour, lx, door, rng):
    """Ground-floor shop: painted fascia with lettering, big display window or a door."""
    w = s.get_width()
    R(s, shade(colour, 0.6), 0, y, w, 1)
    R(s, colour, 0, y + 1, w, 3)
    if lx % 2 == 0:
        for x in range(2, w - 2, 2):
            if rng.random() < 0.8:
                P(s, FRAME, x, y + 2)
    R(s, shade(colour, 0.55), 0, y + 4, w, 1)
    body = y + 5
    hgt = GROUND_H - 5 - 1
    R(s, (40, 38, 44), 0, body, w, hgt)
    if door:
        R(s, shade(colour, 0.8), 5, body + 1, 6, hgt - 1)
        R(s, GLASS_M, 6, body + 2, 4, 4)
        P(s, (240, 210, 90), 9, body + 6)
    else:
        R(s, GLASS, 1, body + 1, w - 2, hgt - 2)
        R(s, GLASS_M, 1, body + 1, w - 2, 2)
        for i in range(3):                                         # reflection streak
            P(s, GLASS_L, 3 + i, body + 4 - i)
        for gx in range(2, w - 3, 4):                              # goods on display
            R(s, rng.choice([(220, 200, 160), colour, (236, 236, 226), (180, 90, 70)]), gx, body + hgt - 4, 3, 2)
        R(s, (90, 86, 82), 1, body + hgt - 2, w - 2, 1)            # stall riser


def _veranda(s, y):
    """The iron-and-glass shop canopy Queens Road is known for."""
    w = s.get_width()
    green, light = (44, 96, 82), (120, 178, 166)
    R(s, shade(green, 0.7), 0, y, w, 1)
    R(s, green, 0, y + 1, w, 2)
    for x in range(1, w, 4):
        R(s, light, x, y + 1, 2, 1)
    R(s, shade(green, 0.6), 0, y + 3, w, 1)
    for x in (2, w - 3):
        P(s, IRON, x, y + 4); P(s, IRON, x + 1, y + 5)


_SIGN_CACHE = {}


def facade_terrace(b, lx, bw, shop, door, below_pavement):
    """Front of one tile of an ordinary Queens Road building (Bath-stone terrace)."""
    rng = random.Random(b["seed"] * 31 + lx)
    stone = tuple(b["stone"])
    H = building_height(b)
    s = canvas(L, H)
    _ashlar(s, stone, rng)
    v = b["variant"]
    _cornice(s, stone, 0, balustrade=v in (1, 3))
    floors = (H - GROUND_H - CORNICE_H) // FLOOR_H
    for f in range(floors):
        y = CORNICE_H + f * FLOOR_H + 1
        first = f == floors - 1
        if v == 1:                                                 # Victorian: pilasters and arched windows
            R(s, shade(stone, 1.08), 0, y - 1, 1, FLOOR_H)
            R(s, shade(stone, 0.85), 15, y - 1, 1, FLOOR_H)
            _sash(s, 5, y + 1, 6, 7 if not first else 7, arch=first, stone=stone)
        elif v == 2 and first and lx % 2 == 0:                    # canted bay window
            R(s, shade(stone, 0.8), 2, y, 12, 8)
            R(s, stone, 3, y, 10, 7)
            for wx in (3, 7, 11):
                R(s, FRAME, wx, y + 1, 3, 5); R(s, GLASS if wx != 7 else GLASS_M, wx + 1 - (wx == 11), y + 2, 1 + (wx == 7), 3)
            R(s, shade(stone, 0.7), 2, y + 7, 12, 1)
        else:
            _sash(s, 5, y + 1, 6, 7, stone=stone)
            if v == 3 and first:                                   # cast-iron balcony
                R(s, IRON, 2, y + 5, 12, 1); R(s, IRON, 2, y + 8, 12, 1)
                for x in range(2, 14, 2):
                    P(s, IRON, x, y + 6); P(s, IRON, x, y + 7)
    gy = H - GROUND_H
    R(s, shade(stone, 1.1), 0, gy - 1, L, 1)                       # string course
    R(s, shade(stone, 0.75), 0, gy, L, 1)
    if shop:
        _shopfront(s, gy, tuple(b["awning"]), lx, door, rng)
        if b.get("veranda"):
            _veranda(s, gy + 4)
        if b.get("brand"):                                         # this shop's own sign across its front
            key = (b["seed"], bw)
            sign = _SIGN_CACHE.get(key)
            if sign is None:
                sign = _SIGN_CACHE[key] = shop_sign(b["brand"], bw * L)
            s.blit(sign.subsurface((lx * L, 0, L, SIGN_H)), (0, gy))
    else:
        if door:
            R(s, shade(stone, 0.8), 3, gy + 2, 10, GROUND_H - 2)
            circle(s, FRAME, 8, gy + 5, 3)                          # fanlight
            circle(s, GLASS, 8, gy + 5, 2)
            R(s, ((40, 56, 92), (120, 36, 44), (34, 80, 56), (30, 30, 34))[v], 5, gy + 6, 6, GROUND_H - 8)
            P(s, (230, 200, 90), 9, gy + 9)
            R(s, shade(stone, 1.1), 3, H - 2, 10, 1)                # step
        else:
            _sash(s, 5, gy + 3, 6, 7, stone=stone)
            R(s, IRON, 0, H - 4, L, 1)                              # area railings
            for x in range(0, L, 2):
                P(s, IRON, x, H - 3)
    R(s, shade(stone, 0.5), 0, H - 1, L, 1)
    return s


def facade_modern(b, lx, bw, shop, door, below_pavement):
    """University / later buildings: plainer stone with regular windows."""
    rng = random.Random(b["seed"] * 17 + lx)
    stone = tuple(b["stone"])
    H = building_height(b)
    s = canvas(L, H)
    R(s, stone, 0, 0, L, H)
    speckle(s, rng, [shade(stone, 0.95)], 0.05)
    R(s, shade(stone, 0.7), 0, 0, L, 1); R(s, shade(stone, 1.1), 0, 1, L, 1)
    for y in range(3, H - GROUND_H, FLOOR_H):
        for x in (2, 9):
            R(s, (60, 62, 70), x, y, 5, 7)
            R(s, GLASS_M, x + 1, y + 1, 3, 5); P(s, GLASS_L, x + 1, y + 1)
    gy = H - GROUND_H
    R(s, shade(stone, 0.8), 0, gy, L, 1)
    if door:
        R(s, (50, 52, 58), 3, gy + 3, 10, GROUND_H - 3); R(s, GLASS_M, 4, gy + 4, 8, GROUND_H - 5)
    else:
        R(s, (60, 62, 70), 1, gy + 3, 14, 7); R(s, GLASS, 2, gy + 4, 12, 5); P(s, GLASS_L, 2, gy + 4)
    R(s, shade(stone, 0.5), 0, H - 1, L, 1)
    return s


# ---- landmarks --------------------------------------------------------------
BATH = (226, 208, 166)
BATH_PALE = (234, 222, 190)
PENNANT = (118, 112, 106)


def _column(s, x, y0, y1, stone, w=3):
    R(s, shade(stone, 1.12), x, y0, w, y1 - y0)
    R(s, shade(stone, 0.78), x + w - 1, y0, 1, y1 - y0)
    for yy in range(y0, y1, 2):
        P(s, shade(stone, 0.95), x + 1, yy)                        # fluting
    R(s, shade(stone, 1.15), x - 1, y0 - 2, w + 2, 2)              # capital
    P(s, shade(stone, 0.7), x - 1, y0 - 1); P(s, shade(stone, 0.7), x + w, y0 - 1)
    R(s, shade(stone, 0.85), x - 1, y1, w + 2, 1)                  # base


def _pointed(s, x, y, w, h, frame, glass=GLASS, tracery=True, head=None):
    hd = w // 2 if head is None else head                          # head=None: pointed; small head: Tudor arch
    for yy in range(h):
        if yy < hd:
            inset = round((hd - yy) * (w / 2) / hd) if head is not None else w // 2 - yy
            R(s, frame, x + inset - 1, y + yy, w - 2 * inset + 2, 1)
            R(s, glass, x + inset, y + yy, max(0, w - 2 * inset), 1)
        else:
            R(s, frame, x - 1, y + yy, w + 2, 1)
            R(s, glass, x, y + yy, w, 1)
    if tracery and w >= 3:
        R(s, frame, x + w // 2, y + w // 2, 1, h - w // 2)
    P(s, GLASS_L, x + max(0, w // 2 - 1), y + w // 2 + 1)


_HARBOUR_FRONTS = {}


def facade_landmark(b, lx, bw, tower):
    st = b["style"]
    if st in ("X", "P"):                                            # board-marked concrete (bridge walls, piers)
        return _concrete(b, lx, bw)
    if st == "O":                                                   # OMG nightclub
        return _omg_front(bw, b.get("variant", 0)).subsurface((lx * L, 0, L, building_height(b))).copy()
    if st in ("R", "B", "Z"):                                       # harbourside: arcade, brick sheds, restaurant shed
        key = (st, bw, b["seed"], b.get("sign"))
        img = _HARBOUR_FRONTS.get(key)
        if img is None:
            Hh = building_height(b)
            img = _HARBOUR_FRONTS[key] = (_arcade_front(bw, Hh, b.get("sign") or "BRISTOL ARCADE") if st == "R" else
                                         _warehouse_front(bw, Hh, b["seed"]) if st == "B" else
                                         _shed_front(bw, Hh, b["seed"], b.get("sign")))
        return img.subsurface((lx * L, 0, L, img.get_height())).copy()
    rng = random.Random(b["seed"] * 7 + lx)
    H = TOWER_H if tower else building_height(b)
    s = canvas(L, H)
    gx = lx * L                                                    # x within the whole building
    centre = bw * L / 2

    if st == "V":                                                  # Victoria Rooms
        stone = BATH_PALE
        _ashlar(s, stone, rng, course=4)
        portico = abs(gx + L / 2 - centre) < L * 3.2
        # entablature + pediment across the portico
        R(s, shade(stone, 0.7), 0, 10, L, 1); R(s, shade(stone, 1.1), 0, 11, L, 2); R(s, shade(stone, 0.75), 0, 13, L, 1)
        if portico:
            half = L * 3.2
            for x in range(L):
                t = 1 - abs(gx + x - centre) / half
                if t > 0:
                    top = int(10 - t * 9)
                    R(s, shade(stone, 0.65), x, top, 1, 1)
                    R(s, shade(stone, 1.06), x, top + 1, 1, max(0, 9 - (top + 1)))
                    if top + 3 < 9 and (gx + x) % 3 == 0:          # carved figures in the tympanum
                        P(s, shade(stone, 0.85), x, 7)
                        P(s, shade(stone, 0.85), x, 8)
            R(s, shade(stone, 0.55), 0, 14, L, H - 22)             # deep shade behind the columns
            R(s, (60, 54, 52), 6, H - 20, 4, 10)                   # doorway
            for cx in (1, 9):
                _column(s, cx, 16, H - 7, stone, w=4)
        else:
            for y in (17, 29):
                _sash(s, 5, y, 6, 8, stone=stone)
            R(s, shade(stone, 1.1), 0, 15, 1, H - 22)
        for i, y in enumerate(range(H - 6, H)):                    # broad steps
            R(s, shade(stone, 1.08 if i % 2 == 0 else 0.86), 0, y, L, 1)
        return s

    if st == "A":                                                  # Royal West of England Academy
        stone = BATH
        _ashlar(s, stone, rng)
        R(s, shade(stone, 1.1), 0, 0, L, 4)                         # balustrade with statues
        for x in range(1, L, 3):
            R(s, shade(stone, 0.75), x, 1, 1, 2)
        if lx % 3 == 1:
            R(s, BATH_PALE, 7, -0 + 0, 2, 1)
        R(s, shade(stone, 0.65), 0, 4, L, 1)
        R(s, shade(stone, 1.12), 0, 5, L, 1)
        for x in (1, 12):                                          # paired columns on the upper floor
            _column(s, x, 8, 22, stone, w=2)
        R(s, shade(stone, 0.55), 5, 8, 6, 13)                      # statue niche
        circle(s, BATH_PALE, 8, 11, 1)
        R(s, BATH_PALE, 7, 13, 3, 6)
        R(s, shade(stone, 0.7), 0, 23, L, 1)
        for y in range(25, H - 1, 3):                              # rusticated ground floor
            R(s, shade(stone, 0.78), 0, y, L, 1)
        _sash(s, 5, 28, 6, 8, arch=True, stone=stone)
        R(s, shade(stone, 0.5), 0, H - 1, L, 1)
        return s

    if st == "M":                                                  # City Museum & Art Gallery
        stone = (214, 198, 160)
        _ashlar(s, stone, rng, course=4)
        R(s, shade(stone, 1.1), 0, 0, L, 4)
        for x in range(1, L, 2):
            R(s, shade(stone, 0.72), x, 1, 1, 2)
        R(s, shade(stone, 0.62), 0, 4, L, 1)
        entrance = abs(gx + L / 2 - centre) < L
        if entrance:
            R(s, shade(stone, 1.1), 1, 8, 14, H - 8)
            R(s, (64, 50, 40), 3, 14, 10, H - 14)
            for yy in range(4):                                    # round arch head
                R(s, shade(stone, 1.1), 3, 14 + yy, 4 - yy, 1); R(s, shade(stone, 1.1), 9 + yy, 14 + yy, 4 - yy, 1)
            R(s, (232, 214, 170), 7, 10, 2, 4)                     # carved keystone
            R(s, (90, 100, 90), 6, 6, 4, 4)                        # sculpture group (bronze-green)
        else:
            for y, h in ((9, 14), (H - 22, 15)):
                R(s, FRAME, 4, y, 8, h)
                R(s, GLASS, 5, y + 2, 6, h - 2)
                R(s, FRAME, 5, y + 1, 6, 1)
                P(s, (0, 0, 0, 0), 4, y); P(s, (0, 0, 0, 0), 11, y)
                R(s, shade(stone, 0.82), 7, y - 2, 2, 2)           # keystone
                P(s, GLASS_L, 5, y + 3)
            R(s, shade(stone, 1.12), 0, 6, 2, H - 7); R(s, shade(stone, 0.8), 14, 6, 2, H - 7)
        R(s, shade(stone, 0.5), 0, H - 1, L, 1)
        return s

    if st == "G":                                                  # Brown's: Venetian Gothic, red and cream
        red, cream = (176, 82, 62), (232, 216, 180)
        R(s, red, 0, 0, L, H)
        for y in range(0, H, 6):
            R(s, cream, 0, y, L, 2)
        speckle(s, rng, [shade(red, 0.9)], 0.05)
        for wy in (5, H - 17):
            for wx in (2, 9):
                _pointed(s, wx, wy, 5, 12, cream)
                for i in range(0, 5, 2):                            # striped voussoirs
                    P(s, red, wx + i, wy + 1)
        R(s, shade(red, 0.5), 0, H - 1, L, 1)
        return s

    if st == "C":                                                  # Gothic church in grey Pennant stone
        stone, dress = PENNANT, BATH_PALE
        _ashlar(s, stone, rng, course=3)
        for x in (0, 15):
            R(s, dress, x, 0, 1, H)
        _pointed(s, 4, 8, 8, 24, dress)
        R(s, dress, 4, 20, 8, 1)
        R(s, (70, 56, 50), 5, H - 12, 6, 11)
        R(s, shade(stone, 0.6), 0, H - 1, L, 1)
        return s

    if st == "K":                                                  # City Hall: red brick, pale stone dressings, gold unicorns
        brick, brick_d, stone = (166, 76, 56), (136, 60, 46), (226, 220, 204)
        R(s, brick, 0, 0, L, H)
        for y in range(1, H, 3):                                   # Flemish-bond brick courses
            R(s, brick_d, 0, y, L, 1)
            for x in range((y // 3) % 2 * 2, L, 4):
                P(s, shade(brick, 1.1), x, y - 1)
        speckle(s, rng, [shade(brick, 0.9)], 0.04)
        R(s, stone, 0, 6, L, 3); R(s, shade(stone, 0.75), 0, 8, L, 1)          # cornice
        for x in range(1, L, 3):                                   # balustrade
            R(s, stone, x, 3, 1, 3)
        R(s, stone, 0, 2, L, 1)
        if lx in (0, bw - 1):                                      # gilded unicorn on the roof end
            gold, gold_d = (232, 190, 70), (180, 136, 40)
            R(s, gold, 5, 0, 6, 2); R(s, gold_d, 5, 1, 6, 1)
            P(s, gold, 11, 0); P(s, (250, 230, 150), 12, 0)        # head + horn
            R(s, gold_d, 6, 2, 1, 1); R(s, gold_d, 10, 2, 1, 1)
        for y, h in ((12, 9), (H - 20, 10)):                       # windows with stone surrounds
            R(s, stone, 4, y - 1, 8, h + 2)
            R(s, GLASS, 5, y, 6, h)
            R(s, FRAME, 5, y + h // 2, 6, 1); R(s, FRAME, 8, y, 1, h)
            P(s, GLASS_L, 5, y)
        R(s, stone, 0, H - 8, L, 1)
        if lx in (0, bw - 1):                                      # stone quoins at the corners
            for y in range(9, H, 4):
                R(s, stone, 0 if lx == 0 else L - 3, y, 3, 2)
        if abs(gx + L / 2 - centre) < L:                           # main entrance
            R(s, stone, 3, H - 12, 10, 12)
            R(s, (60, 44, 34), 5, H - 10, 6, 10)
        R(s, shade(brick, 0.5), 0, H - 1, L, 1)
        return s

    if st == "D":                                                  # Bristol Cathedral: pale Gothic limestone
        stone = (206, 202, 190)
        _ashlar(s, stone, rng, course=4)
        for x in (0, 13):                                          # buttresses with pinnacles
            R(s, shade(stone, 1.08), x, 2, 3, H - 2)
            R(s, shade(stone, 0.78), x + 2, 2, 1, H - 2)
            R(s, shade(stone, 1.15), x + 1, 0, 1, 3)
        for x in range(3, 13, 3):                                  # pierced parapet
            R(s, shade(stone, 0.7), x, 1, 1, 2)
        _pointed(s, 4, 8, 8, 30, shade(stone, 0.65))               # tall traceried window
        R(s, shade(stone, 0.65), 4, 22, 8, 1)
        R(s, shade(stone, 0.65), 6, 15, 1, 15); R(s, shade(stone, 0.65), 9, 15, 1, 15)
        if abs(gx + L / 2 - centre) < L:
            _pointed(s, 4, H - 14, 8, 13, shade(stone, 0.6), glass=(70, 54, 42), tracery=False)
        R(s, shade(stone, 0.5), 0, H - 1, L, 1)
        return s

    # W: Wills Memorial Building, Perpendicular Gothic in pale stone
    if tower:
        return _wills_tower(bw).subsurface((lx * L, 0, L, H)).copy()
    return _wills_wing(lx, H, rng)


WILLS_STONE = (224, 208, 168)
_TOWER_CACHE = {}


def _perp_window(s, x, y, w, h, stone, mullions=3, transoms=(), glass=GLASS):
    """Perpendicular Gothic window: pointed head, stone mullions, transoms, little cusped lights."""
    dark = shade(stone, 0.62)
    head = w // 2 if w <= 12 else max(6, w // 4)
    _pointed(s, x, y, w, h, dark, glass=glass, tracery=False, head=head if w > 12 else None)
    for i in range(1, mullions + 1):
        mx = x + i * w // (mullions + 1)
        R(s, shade(stone, 0.95), mx, y + head - 1, 1, h - head + 1)
    for t in transoms:
        R(s, shade(stone, 0.95), x, y + t, w, 1)
        for i in range(mullions + 1):                               # cusps under each transom
            lx0 = x + i * w // (mullions + 1) + 1
            P(s, shade(stone, 0.8), lx0, y + t + 1)
    for i in range(0, w, 2):                                        # tracery in the head
        yy = y + head // 2 + (i % 4) // 2
        if 0 < i < w - 1: P(s, shade(stone, 0.9), x + i, yy)
    R(s, shade(stone, 1.12), x - 2, y + h, w + 4, 1)                # sill
    # hood mould
    for yy in range(head + 1):
        inset = round((head - yy) * (w / 2) / head)
        P(s, shade(stone, 1.15), x + inset - 2, y + yy - 1)
        P(s, shade(stone, 0.8), x + w - inset + 1, y + yy - 1)


def _battlements(s, y, stone, w):
    R(s, shade(stone, 1.06), 0, y + 3, w, 3)
    R(s, shade(stone, 0.7), 0, y + 6, w, 1)
    for x in range(0, w, 5):
        R(s, shade(stone, 1.1), x, y, 3, 3)
        R(s, shade(stone, 0.8), x + 2, y, 1, 3)


def _shield(s, x, y, field, charge):
    R(s, OUTLINE, x - 1, y - 1, 7, 8)
    R(s, field, x, y, 5, 5)
    R(s, field, x + 1, y + 5, 3, 1)
    P(s, field, x + 2, y + 6)
    R(s, charge, x + 1, y + 2, 3, 1); P(s, charge, x + 2, y + 1); P(s, charge, x + 2, y + 3)
    R(s, (240, 214, 110), x - 1, y - 2, 7, 1)                       # gilded crest line


def _wills_tower(bw):
    """The whole front of the Wills tower (all its tiles at once, so the great window spans them)."""
    if bw in _TOWER_CACHE:
        return _TOWER_CACHE[bw]
    rng = random.Random(1925)
    w, H = bw * L, TOWER_H
    st = WILLS_STONE
    s = canvas(w, H)
    _ashlar(s, st, rng, course=4)
    t = 10                                                          # corner turret width
    for x0, k in ((0, 1.06), (w - t, 0.9)):                         # octagonal corner turrets
        R(s, shade(st, k), x0, 0, t, H)
        R(s, shade(st, k * 1.08), x0 + 1, 0, 2, H)
        R(s, shade(st, k * 0.8), x0 + t - 2, 0, 2, H)
        for y in range(10, H - 14, 16):                             # blind panelling + set-offs
            _pointed(s, x0 + 4, y, 3, 12, shade(st, k * 0.78), glass=shade(st, k * 0.86), tracery=False)
            R(s, shade(st, k * 0.72), x0, y + 14, t, 1)
        for x in range(x0, x0 + t, 3):                              # turret crown
            R(s, shade(st, k * 1.1), x, 0, 2, 3)
    cx0, cx1 = t, w - t
    cw = cx1 - cx0
    _battlements(s, 0, st, w)
    # belfry stage: twin louvred lancets
    lw = max(6, cw // 2 - 6)
    for i in range(2):
        lx0 = cx0 + 3 + i * (cw // 2)
        _pointed(s, lx0, 9, lw, 26, shade(st, 0.62), glass=(84, 76, 70), tracery=True)
        for y in range(9 + lw // 2 + 2, 35, 2):
            R(s, (110, 100, 90), lx0, y, lw, 1)                     # louvres
    R(s, shade(st, 1.12), cx0, 37, cw, 1); R(s, shade(st, 0.7), cx0, 38, cw, 1)
    # three gilded coats of arms over the great window
    arms = [((214, 172, 58), (176, 40, 40)), ((236, 236, 228), (180, 36, 44)), ((214, 172, 58), (40, 60, 140))]
    for i, (field, charge) in enumerate(arms):
        _shield(s, cx0 + cw * (i + 1) // 4 - 2, 41, field, charge)
    # the great window
    gw = cw - 10
    _perp_window(s, cx0 + 5, 50, gw, 28, st, mullions=4, transoms=(12, 20), glass=(56, 70, 92))
    for y in range(52 + gw // 4, 78, 3):                            # leaded lights
        for x in range(cx0 + 6, cx0 + 5 + gw, 4):
            P(s, (82, 100, 124), x, y)
    # pierced parapet with pinnacles over the porch
    R(s, shade(st, 1.1), cx0, 80, cw, 2); R(s, shade(st, 0.7), cx0, 82, cw, 1)
    for x in range(cx0 + 1, cx1 - 1, 3):
        P(s, shade(st, 0.7), x, 81)
    for x in (cx0 + 1, cx0 + cw // 2 - 1, cx1 - 3):
        R(s, shade(st, 1.15), x, 76, 2, 6); P(s, shade(st, 1.2), x, 75)
    # great doorway with deep mouldings, oak doors
    dw = 14
    dx = cx0 + (cw - dw) // 2
    for k, c in enumerate((shade(st, 0.85), shade(st, 0.7), shade(st, 0.55))):
        _pointed(s, dx - 3 + k, 84 + k, dw + 6 - 2 * k, H - 87 - k, c, glass=c, tracery=False)
    _pointed(s, dx, 87, dw, H - 90, (70, 46, 32), glass=(92, 60, 40), tracery=False)
    R(s, (60, 40, 28), dx + dw // 2, 94, 1, H - 97)
    for y in (96, 99): R(s, (60, 40, 28), dx, y, dw, 1)
    P(s, (220, 190, 90), dx + dw // 2 - 2, 97); P(s, (220, 190, 90), dx + dw // 2 + 2, 97)   # door handles
    R(s, shade(st, 0.92), cx0 + 2, 88, 6, 4); R(s, shade(st, 0.92), cx1 - 8, 88, 6, 4)   # carved name panels
    for i in range(3):                                              # steps
        R(s, shade(st, 1.08 if i % 2 == 0 else 0.84), 0, H - 3 + i, w, 1)
    R(s, shade(st, 0.5), 0, H - 1, w, 1)
    _TOWER_CACHE[bw] = s
    return s


def _wills_wing(lx, H, rng):
    """One tile of the Wills wings: battlements, buttressed bays, tall Perpendicular windows."""
    st = WILLS_STONE
    s = canvas(L, H)
    _ashlar(s, st, rng, course=4)
    _battlements(s, 0, st, L)
    if lx % 2 == 0:                                                 # buttress between bays
        R(s, shade(st, 1.1), 0, 4, 3, H - 4)
        R(s, shade(st, 0.78), 2, 4, 1, H - 4)
        for y in range(14, H, 12):
            R(s, shade(st, 0.72), 0, y, 3, 1)
        R(s, shade(st, 1.15), 0, 0, 3, 4); P(s, shade(st, 1.2), 1, 0)   # pinnacle
        _perp_window(s, 6, 10, 8, 20, st, mullions=1, transoms=(12,))
        _perp_window(s, 6, 35, 8, 12, st, mullions=1)
    else:
        _perp_window(s, 3, 10, 8, 20, st, mullions=1, transoms=(12,))
        _perp_window(s, 3, 35, 8, 12, st, mullions=1)
    R(s, shade(st, 1.1), 0, 32, L, 1); R(s, shade(st, 0.72), 0, 33, L, 1)   # string course
    R(s, shade(st, 0.8), 0, H - 3, L, 2)                            # plinth
    R(s, shade(st, 0.5), 0, H - 1, L, 1)
    return s


# ---- roofs ------------------------------------------------------------------
def roof_tile(b, mask, tower, chimney, dormer, seed):
    """Top face of one building tile."""
    rng = random.Random(seed)
    s = canvas(L, L)
    st = b["style"]
    if tower:
        stone = (210, 194, 154)
        R(s, stone, 0, 0, L, L)
        R(s, shade(stone, 0.8), 3, 3, 10, 10)
        R(s, shade(stone, 0.65), 6, 6, 4, 4)
        edge = stone
    elif st == "D":                                                # Cathedral: lead roof, Gothic parapets
        lead = (128, 134, 140)
        R(s, lead, 0, 0, L, L)
        for x in range(1, L, 4):
            R(s, shade(lead, 1.16), x, 0, 1, L); R(s, shade(lead, 0.84), x + 1, 0, 1, L)
        R(s, shade(lead, 1.25), 0, 7, L, 1); R(s, shade(lead, 0.8), 0, 8, L, 1)   # ridge
        speckle(s, rng, [shade(lead, 0.94)], 0.05)
        edge = (206, 202, 190)
    elif st == "R":                                                # the arcade's white tensile roof (the old aquarium's)
        base = (234, 238, 242)                                     # one fabric peak per tile, pulled up on a mast
        for y in range(L):
            for x in range(L):
                dx, dy = x - 7.5, y - 7.5
                if abs(dy) >= abs(dx):
                    k = 1.0 if dy < 0 else 0.86
                else:
                    k = 0.95 if dx < 0 else 0.9
                if abs(abs(dx) - abs(dy)) < 0.6:
                    k -= 0.06                                      # the seams down from the peak
                s.set_at((x, y), shade(base, k))
        R(s, (150, 156, 170), 7, 7, 2, 2); P(s, (90, 96, 110), 7, 7)  # mast cap
        R(s, shade(base, 0.8), 0, L - 1, L, 1); R(s, shade(base, 0.8), L - 1, 0, 1, L)
        edge = (60, 52, 80)
    elif st == "Z":                                                # corrugated metal
        base = (112, 128, 140)
        for x in range(0, L, 2):
            R(s, shade(base, 1.1 if x % 4 == 0 else 0.92), x, 0, 2, L)
        edge = (80, 92, 104)
    elif st in ("H", "C", "K", "B") or (st == "G"):
        slate = SLATE if st not in ("C", "B") else ((86, 92, 104) if st == "C" else (78, 84, 92))
        for i, y in enumerate(range(0, L, 3)):                     # rows of slates
            R(s, shade(slate, rng.uniform(0.96, 1.04)), 0, y, L, 3)
            R(s, shade(slate, 1.22), 0, y, L, 1)
            for x in range((i % 2) * 2, L, 4):
                P(s, shade(slate, 0.78), x, y + 1); P(s, shade(slate, 0.78), x, y + 2)
        edge = (150, 66, 50) if st == "B" else (tuple(b["stone"]) if b.get("stone") else ((226, 220, 204) if st == "K" else BATH_PALE))
    else:                                                          # lead flats with rolls
        lead = (150, 156, 164)
        R(s, lead, 0, 0, L, L)
        for x in (3, 11):
            R(s, shade(lead, 1.15), x, 0, 1, L); R(s, shade(lead, 0.85), x + 1, 0, 1, L)
        speckle(s, rng, [shade(lead, 0.95)], 0.05)
        if st in ("M", "W") and seed % 5 == 0:                      # roof light
            R(s, (90, 96, 104), 5, 5, 6, 5); R(s, GLASS_M, 6, 6, 4, 3); P(s, GLASS_L, 6, 6)
        if st in ("X", "P", "O"):                                  # flat concrete / felt roofs
            top = (52, 46, 58) if st == "O" else (tuple(b["stone"]) if st == "P" and b.get("stone") else (128, 128, 126))
            R(s, top, 0, 0, L, L)
            speckle(s, rng, [shade(top, 0.9), shade(top, 1.1)], 0.14)
            if st == "O" and seed % 23 == 0:                       # a few air-con units and skylights
                R(s, OUTLINE, 3, 3, 10, 8); R(s, (120, 124, 132), 4, 4, 8, 6); R(s, (90, 94, 102), 4, 9, 8, 1)
                circle(s, (70, 74, 82), 8, 6, 2); P(s, (40, 40, 46), 8, 6)
            elif st == "O" and seed % 23 == 11:
                R(s, OUTLINE, 5, 4, 6, 6); R(s, (90, 110, 140), 6, 5, 4, 4); P(s, (160, 190, 220), 6, 5)
            if st == "P":                                          # rough-cut stone blocks
                for yy in range(3, L, 5): R(s, shade(top, 0.8), 0, yy, L, 1)
                for xx in range((yy_ := 0) % 2 * 4, L, 8): R(s, shade(top, 0.8), xx, 0, 1, L)
        edge = {"X": (170, 168, 162), "P": (120, 114, 108), "O": (70, 60, 78),
                "V": BATH_PALE, "A": BATH, "M": (214, 198, 160), "U": tuple(b["stone"]) if b.get("stone") else BATH,
                "W": (222, 206, 166), "D": (206, 202, 190)}.get(st, BATH)
    # parapets / coping where the roof meets another building or the street
    cope, cope_d = shade(edge, 1.08), shade(edge, 0.75)
    if not mask & 1: R(s, cope, 0, 0, L, 2); R(s, cope_d, 0, 2, L, 1)
    if not mask & 8: R(s, cope, 0, 0, 2, L); R(s, cope_d, 2, 0, 1, L)
    if not mask & 2: R(s, cope_d, L - 3, 0, 1, L); R(s, cope, L - 2, 0, 2, L)
    if not mask & 4: R(s, cope_d, 0, L - 3, L, 1); R(s, cope, 0, L - 2, L, 2)
    if not mask & 1: R(s, OUTLINE, 0, 0, L, 1)
    if not mask & 8: R(s, OUTLINE, 0, 0, 1, L)
    if not mask & 2: R(s, OUTLINE, L - 1, 0, 1, L)
    if st == "D":                                                  # pierced parapet + pinnacles
        stone = (206, 202, 190)
        for side, (rx, ry, rw, rh) in ((1, (0, 0, L, 3)), (4, (0, L - 3, L, 3)), (8, (0, 0, 3, L)), (2, (L - 3, 0, 3, L))):
            if not mask & side:
                R(s, stone, rx, ry, rw, rh)
                for k in range(1, max(rw, rh), 3):
                    P(s, shade(stone, 0.6), rx + (k if rw > rh else 1), ry + (1 if rw > rh else k))
        if not mask & 1 or not mask & 4:
            for px_ in (1, 9):
                R(s, OUTLINE, px_, 2 if not mask & 1 else L - 8, 4, 6)
                R(s, shade(stone, 1.1), px_ + 1, 2 if not mask & 1 else L - 8, 2, 5)
    if chimney:                                                    # stone stack with clay pots
        sx = 2 if not mask & 8 else 10
        stone = tuple(b["stone"]) if b.get("stone") else BATH
        R(s, OUTLINE, sx - 1, 3, 7, 9)
        R(s, stone, sx, 6, 5, 5)
        R(s, shade(stone, 0.75), sx, 9, 5, 2)
        R(s, shade(stone, 1.1), sx, 4, 5, 2)
        for px_ in (sx + 1, sx + 3):
            R(s, (196, 112, 70), px_, 2, 1, 3)
            P(s, (60, 40, 32), px_, 2)
    if dormer:                                                     # little dormer window
        R(s, OUTLINE, 5, 9, 7, 7)
        R(s, SLATE, 6, 9, 5, 2)
        R(s, FRAME, 6, 11, 5, 4)
        R(s, GLASS, 7, 12, 3, 2)
    return s


def building_tile(b, mask, tower, chimney, dormer, seed, facade):
    """Roof (top face) plus, on a building's front row, its facade below it. Returns screen-size art."""
    roof = roof_tile(b, mask, tower, chimney, dormer, seed)
    if facade is None:
        return up(roof).convert_alpha()
    H = facade.get_height()
    s = canvas(L, L + H)
    s.blit(roof, (0, 0))
    s.blit(facade, (0, L))
    R(s, OUTLINE, 0, L, L, 1)
    if not mask & 8: R(s, OUTLINE, 0, L, 1, H)
    if not mask & 2: R(s, OUTLINE, L - 1, L, 1, H)
    return up(s).convert_alpha()


# ============================================================== props
LEAF = [(52, 112, 56), (70, 140, 64), (98, 168, 76), (136, 196, 92), (36, 84, 48)]
BARK = (110, 76, 48)


def tree(kind=0, seed=0):
    """Leafy street tree (London plane / lime look). Returns (screen surface, foot offset from top)."""
    rng = random.Random(seed * 13 + kind)
    w, h = 30, 38
    s = canvas(w, h)
    # trunk and roots
    R(s, BARK, 13, 20, 4, 15)
    R(s, shade(BARK, 1.25), 13, 20, 1, 15)
    R(s, shade(BARK, 0.7), 16, 20, 1, 15)
    for x, y in ((11, 34), (12, 33), (18, 34), (17, 33)):
        P(s, BARK, x, y)
    if kind == 1:                                                   # plane tree bark patches
        for _ in range(5):
            P(s, (178, 168, 120), 14 + rng.randrange(2), 22 + rng.randrange(11))
    # canopy: overlapping blobs, dark underneath, light on top-left
    leaf = LEAF if kind != 2 else [(60, 120, 50), (84, 150, 58), (120, 180, 70), (170, 210, 96), (44, 92, 40)]
    if kind == 3:                                                   # autumn acer: crimson / orange, like outside Wills
        leaf = [(112, 26, 34), (150, 36, 40), (186, 60, 46), (226, 118, 64), (84, 22, 30)]
    blobs = [(15, 13, 10), (8, 16, 7), (22, 16, 7), (11, 8, 7), (19, 8, 7), (15, 20, 7)]
    for cx, cy, r in blobs:
        circle(s, leaf[0], cx, cy + 1, r)
    for cx, cy, r in blobs:
        circle(s, leaf[1], cx, cy, r - 1)
    for cx, cy, r in blobs:
        circle(s, leaf[2], cx - 1, cy - 2, r - 3)
    for _ in range(26):                                             # leaf clusters
        x, y = rng.randrange(4, 26), rng.randrange(2, 22)
        if s.get_at((x, y)).a:
            col = leaf[3] if y < 12 and x < 18 else leaf[2]
            P(s, col, x, y); P(s, col, x + 1, y)
            P(s, leaf[0], x, y + 1)
    for _ in range(14):
        x, y = rng.randrange(4, 26), rng.randrange(10, 26)
        if s.get_at((x, y)).a:
            P(s, leaf[4], x, y)
    if kind == 3:
        for _ in range(10):                                         # a few leaves still green
            x, y = rng.randrange(4, 26), rng.randrange(6, 22)
            if s.get_at((x, y)).a: P(s, (110, 120, 52), x, y)
    s = add_outline(s, (30, 52, 34) if kind != 3 else (60, 20, 26))
    return up(s).convert_alpha(), (h + 1) * PX - 4 * PX


def lamp_post(style="modern"):
    """Street lamp. 'modern' = tall grey Bristol lamp; 'heritage' = black swan-neck lamp (Park Street)."""
    if style == "heritage":
        s = canvas(12, 34)
        black, hi = (30, 30, 34), (84, 86, 96)
        R(s, black, 3, 8, 2, 24); R(s, hi, 3, 8, 1, 24)
        R(s, black, 2, 29, 4, 4)                                    # fluted base
        R(s, hi, 2, 29, 1, 4)
        R(s, black, 4, 5, 1, 3); R(s, black, 5, 3, 3, 2); R(s, black, 8, 4, 1, 2)   # swan neck
        R(s, black, 7, 5, 4, 2)                                     # lantern hood
        R(s, (255, 224, 140), 8, 7, 2, 3); P(s, (255, 248, 210), 8, 7)
        R(s, black, 7, 10, 4, 1)
        return up(add_outline(s)).convert_alpha()
    s = canvas(10, 34)
    grey, grey_l, grey_d = (70, 74, 82), (110, 116, 126), (46, 48, 54)
    R(s, grey, 4, 6, 2, 26)
    R(s, grey_l, 4, 6, 1, 26)
    R(s, grey_d, 3, 30, 4, 3)                                       # base
    R(s, grey, 5, 5, 4, 1)                                          # bracket arm
    R(s, grey_d, 6, 2, 4, 3)                                        # lantern hood
    R(s, (255, 226, 140), 7, 5, 2, 2)                               # lamp
    P(s, (255, 248, 200), 7, 5)
    return up(add_outline(s)).convert_alpha()


def bin_():
    s = canvas(7, 9)
    black, gold = (40, 42, 46), (206, 170, 70)
    R(s, black, 0, 1, 7, 8)
    R(s, shade(black, 1.5), 1, 1, 1, 7)
    R(s, gold, 0, 3, 7, 1)
    R(s, (24, 24, 28), 1, 0, 5, 1)
    return up(add_outline(s)).convert_alpha()


def bench():
    s = canvas(16, 9)
    wood, iron = (176, 118, 64), (44, 44, 50)
    for y in (0, 2):
        R(s, wood, 1, y, 14, 1); R(s, shade(wood, 1.2), 1, y, 14, 1)
    R(s, shade(wood, 0.8), 1, 1, 14, 1)
    for y in (4, 5):
        R(s, wood if y == 4 else shade(wood, 0.8), 0, y, 16, 1)
    for x in (1, 14):
        R(s, iron, x, 0, 1, 9)
    return up(add_outline(s)).convert_alpha()


def post_box():
    """Red Royal Mail pillar box."""
    s = canvas(6, 11)
    red, red_d, red_l = (200, 34, 38), (150, 24, 30), (236, 90, 80)
    R(s, red, 0, 2, 6, 8)
    R(s, red_l, 1, 2, 1, 7)
    R(s, red_d, 5, 2, 1, 8)
    R(s, red, 1, 0, 4, 2); R(s, red_l, 1, 0, 2, 1)                  # domed cap
    R(s, (30, 26, 28), 1, 4, 4, 1)                                  # posting slot
    R(s, (250, 220, 120), 2, 6, 2, 1)                               # plate
    R(s, (36, 30, 32), 0, 10, 6, 1)                                 # black base
    return up(add_outline(s)).convert_alpha()


def bike_rack():
    """Pair of Sheffield cycle stands (Queens Road has lots)."""
    s = canvas(14, 8)
    steel, steel_l = (120, 126, 136), (186, 192, 200)
    for x in (1, 8):
        R(s, steel, x, 1, 1, 7); R(s, steel, x + 4, 1, 1, 7); R(s, steel, x, 0, 5, 1)
        P(s, steel_l, x + 1, 0); P(s, steel_l, x, 1)
    return up(add_outline(s)).convert_alpha()


def bus_shelter():
    s = canvas(32, 22)
    frame, glass = (70, 74, 82), (170, 214, 230, 120)
    g = canvas(30, 14); g.fill(glass)
    s.blit(g, (1, 4))
    R(s, frame, 0, 1, 32, 3); R(s, (110, 116, 126), 0, 1, 32, 1)    # roof
    for x in (0, 15, 31):
        R(s, frame, x, 4, 1, 18)
    R(s, (176, 118, 64), 4, 15, 22, 2)                              # seat
    R(s, (40, 90, 160), 22, 6, 7, 8)                                # timetable / map panel
    R(s, (240, 240, 236), 23, 7, 5, 2)
    return up(add_outline(s)).convert_alpha()


def traffic_signal(state=None):
    """Pelican crossing pole. state: None (static), 'green', 'amber', 'red' or 'redamber'.
    The little box lower down is the red / green man for people crossing."""
    s = canvas(5, 26)
    R(s, (60, 64, 70), 2, 8, 1, 18)
    R(s, (30, 30, 34), 0, 0, 5, 9)
    lit = {None: (0,), "green": (2,), "amber": (1,), "red": (0,), "redamber": (0, 1)}[state]
    for i, c in enumerate(((220, 50, 40), (240, 170, 40), (60, 200, 90))):
        on = i in lit
        R(s, c if on else shade(c, 0.35), 1, 1 + i * 3, 3, 2)
        if on: P(s, shade(c, 1.4), 1, 1 + i * 3)
    R(s, (30, 30, 34), 0, 12, 5, 5)                                 # the man
    walk = state == "red"
    man = (90, 230, 120) if walk else (230, 60, 50)
    P(s, man, 2, 13); R(s, man, 2, 14, 1, 2)
    if walk: P(s, man, 1, 15); P(s, man, 3, 14)
    else: P(s, man, 1, 14); P(s, man, 3, 14)
    R(s, (40, 40, 44), 1, 23, 3, 3)
    R(s, (200, 200, 190), 1, 18, 3, 2)                              # push-button box
    return up(add_outline(s)).convert_alpha()


def bus(frame=0):
    """Double-decker bus, side on, facing left, waiting at the stop with its doors open."""
    w, h = 76, 46
    s = canvas(w, h + 1)
    body, band, roof = (24, 104, 112), (236, 224, 180), (200, 204, 206)
    y0 = frame % 2                                                   # engine shudder
    R(s, body, 2, y0 + 2, w - 3, h - 8)
    R(s, roof, 3, y0, w - 5, 3)
    R(s, shade(body, 1.18), 2, y0 + 3, w - 3, 1)
    R(s, band, 2, y0 + 19, w - 3, 3)                                 # cream band between the decks
    for wy, wh in ((y0 + 5, 10), (y0 + 24, 9)):                       # window bands
        R(s, (36, 44, 54), 4, wy, w - 7, wh)
        for x in range(12, w - 4, 10):
            R(s, shade(body, 0.8), x, wy, 1, wh)
        for x in range(6, w - 6, 10):
            R(s, (110, 140, 160), x, wy + 1, 3, 1)
    R(s, (60, 80, 96), 2, y0 + 5, 4, 15); R(s, (60, 80, 96), 2, y0 + 24, 5, 12)   # front windscreen
    R(s, (20, 20, 22), 6, y0 + 4, 40, 7)                            # destination blind
    R(s, (36, 44, 54), 10, y0 + 24, 10, 13)                          # doors open
    R(s, (200, 200, 190), 10, y0 + 24, 1, 13); R(s, (200, 200, 190), 19, y0 + 24, 1, 13)
    R(s, (220, 220, 210), 12, y0 + 36, 6, 1)                         # step
    R(s, shade(body, 0.7), 2, h - 8 + y0, w - 3, 2)
    for wx in (10, w - 16):                                          # wheels
        circle(s, (24, 24, 26), wx + 3, h - 4, 4); circle(s, (120, 124, 130), wx + 3, h - 4, 1)
    R(s, (250, 240, 200), 1, y0 + 36, 2, 2); R(s, (220, 60, 50), w - 2, y0 + 36, 1, 2)   # lights
    R(s, (240, 200, 60), 30, y0 + 28, 10, 5); R(s, (20, 20, 22), 31, y0 + 29, 8, 3)       # route number panel
    draw_text(s, "8 CLIFTON", 8, y0 + 5, (250, 180, 60))
    draw_text(s, "8", 34, y0 + 28, (250, 180, 60))
    return up(add_outline(s)).convert_alpha()


def cascade(frame=0, tiles_w=2, tiles_h=5):
    """The waterfall at the end of City Hall's pool: the water runs to a stone lip, drops in a white-streaked
    curtain, churns into foam and spreads out across a plunge pool. Animated (8 frames).
    Covers tiles_w x tiles_h tiles; drawn 3 art-pixels wider on each side for its stone walls."""
    ww = tiles_w * L
    w, h = ww + 6, tiles_h * L
    s = canvas(w, h)
    rng = random.Random(frame * 7 + 3)
    stone, stone_l, stone_d = (196, 190, 176), (222, 216, 202), (140, 134, 122)
    pool, pool_d, pool_l = (66, 140, 196), (52, 116, 172), (150, 206, 236)
    deep, curtain, curtain_l, foam = (40, 92, 150), (96, 170, 220), (186, 226, 246), (244, 250, 255)
    x0 = 3
    lip, fall_end = 14, 46
    basin_top, kerb = 52, h - 4
    # side walls, from just above the lip down (above that it's simply the pool carrying on)
    for xs in (0, w - 3):
        R(s, stone, xs, lip - 4, 3, h - lip + 4)
        R(s, stone_l if xs == 0 else stone_d, xs + (0 if xs == 0 else 2), lip - 4, 1, h - lip + 4)
        R(s, stone_l, xs, lip - 4, 3, 1)
        for y in range(lip + 2, h, 6):
            R(s, stone_d, xs, y, 3, 1)
    # 1. the end of the pool, flowing towards the lip
    R(s, pool, x0, 0, ww, lip)
    for i in range(10):
        x = x0 + (i * 7 + 3) % (ww - 4)
        y = (i * 5 + frame * 2) % lip
        R(s, pool_l, x, y, 3, 1)
    R(s, pool_d, x0, lip - 3, ww, 2)
    # 2. the lip: water bulging over the stone edge
    R(s, stone_d, x0, lip, ww, 2)
    R(s, curtain_l, x0, lip, ww, 1)
    for x in range(x0, x0 + ww, 2):
        P(s, foam, x + (frame % 2), lip)
    # 3. the falling curtain, streaks running down
    offs = [rng.randrange(9) for _ in range(ww)] if False else [((x * 37) % 11) for x in range(ww)]
    for xi in range(ww):
        x = x0 + xi
        edge = xi < 2 or xi >= ww - 2
        for y in range(lip + 2, fall_end):
            t = (y - lip) / (fall_end - lip)
            c = curtain if t < 0.55 else shade(curtain, 0.88)
            if edge: c = shade(c, 0.8)
            k = (y - frame * 3 + offs[xi] * 2) % 16                       # long, sparse streaks
            if not edge and xi % 3 != 1 and k < 4:
                c = foam if k == 0 else curtain_l
            elif (xi + y // 4) % 5 == 0:
                c = shade(c, 0.86)
            P(s, c, x, y)
    # 4. where it lands: churning foam and spray
    R(s, pool, x0, fall_end, ww, basin_top - fall_end)
    for i in range(9):
        cx = x0 + 2 + (i * 5 + frame * 3) % (ww - 4)
        cy = fall_end + 1 + (i * 3 + frame) % 5
        circle(s, foam, cx, cy, 1 + (i + frame) % 2)
    for i in range(7):                                                   # spray thrown up in front of the fall
        P(s, foam, x0 + (i * 9 + frame * 5) % ww, fall_end - 2 - (i + frame) % 4)
    # 5. the plunge pool, ripples spreading out
    R(s, pool, x0, basin_top, ww, kerb - basin_top)
    R(s, deep, x0, basin_top, ww, 2)
    for ring in range(3):
        r = ((frame + ring * 3) % 9) + 2
        cy = basin_top + 2 + r // 2
        if cy < kerb - 1:
            for x in range(max(x0, x0 + ww // 2 - r * 2), min(x0 + ww, x0 + ww // 2 + r * 2)):
                if (x + ring) % 2 == 0:
                    P(s, pool_l if r < 7 else shade(pool_l, 0.9), x, cy)
    for i in range(6):
        P(s, pool_l, x0 + (i * 11 + frame) % ww, basin_top + 6 + (i * 4) % (kerb - basin_top - 7))
    # 6. stone kerb at the front, dark edge round the stonework (not across the top, where the pool flows in)
    R(s, stone_l, 0, kerb, w, 1); R(s, stone, 0, kerb + 1, w, 2); R(s, stone_d, 0, h - 1, w, 1)
    R(s, OUTLINE, 0, lip - 4, 1, h - lip + 4); R(s, OUTLINE, w - 1, lip - 4, 1, h - lip + 4); R(s, OUTLINE, 0, h - 1, w, 1)
    return up(s).convert_alpha()


def city_fountain(frame=0):
    """The fountain at the end of City Hall's pool: a raised octagonal basin of weathered yellow Bath stone,
    one jet throwing water up that rains back into the basin. Animated (8 frames). Returns screen-size art."""
    W, Hh = 50, 62
    s = canvas(W, Hh)
    cx, rim_y = W // 2, 40                                          # centre of the basin, height of the rim
    rx, ry, wall = 23, 9, 12
    stone, stone_l, stone_d = (208, 172, 78), (236, 206, 120), (150, 118, 50)
    grime, rim_c, rim_d = (150, 136, 70), (226, 204, 146), (176, 150, 92)
    water, water_d, water_l = (112, 150, 150), (82, 118, 122), (176, 206, 204)
    foam, spray = (240, 248, 250), (206, 230, 240)
    oct_ = [(cx + round(rx * math.cos(a)), rim_y + round(ry * math.sin(a))) for a in [k * math.pi / 4 + math.pi / 8 for k in range(8)]]
    # shadow + low plinth
    pygame.draw.ellipse(s, (0, 0, 0, 70), (cx - rx - 2, rim_y + wall - 3, 2 * rx + 4, 2 * ry + 2))
    # front wall: the four facets facing you, each lit a little differently
    front = [oct_[i] for i in (7, 0, 1, 2, 3, 4)]                    # right ... left along the bottom half
    shades = [0.78, 0.9, 1.06, 1.0, 0.86]
    for (x1, y1), (x2, y2), k in zip(front, front[1:], shades):
        pygame.draw.polygon(s, shade(stone, k), [(x1, y1), (x2, y2), (x2, y2 + wall), (x1, y1 + wall)])
    for (x1, y1) in front[1:-1]:                                     # darker joints between facets
        pygame.draw.line(s, stone_d, (x1, y1), (x1, y1 + wall))
    rng = random.Random(11)
    for _ in range(26):                                              # weathering: green-brown streaks running down
        x = rng.randrange(cx - rx + 2, cx + rx - 2)
        y0 = rim_y + 2 + rng.randrange(0, 5)
        for y in range(y0, y0 + rng.randrange(3, 9)):
            if s.get_at((x, y)).a: P(s, grime if rng.random() < 0.7 else stone_d, x, y)
    for x in range(cx - rx, cx + rx + 1):                            # base line
        for y in range(rim_y, rim_y + wall + ry + 1):
            if s.get_at((x, y)).a and (y + 1 >= Hh or not s.get_at((x, y + 1)).a or s.get_at((x, y + 1))[:3] == (0, 0, 0)):
                pass
    # rim (top of the wall) and the water inside
    pygame.draw.polygon(s, rim_c, oct_)
    pygame.draw.lines(s, rim_d, True, oct_)
    inner = [(cx + round((rx - 3) * math.cos(a)), rim_y + round((ry - 2) * math.sin(a))) for a in [k * math.pi / 4 + math.pi / 8 for k in range(8)]]
    pygame.draw.polygon(s, water, inner)
    pygame.draw.polygon(s, water_d, [inner[4], inner[5], inner[6], inner[7], (cx, rim_y - 1)])   # far side darker
    for ring in range(3):                                             # ripples spreading from the jet
        r = (frame + ring * 3) % 9 + 3
        pygame.draw.ellipse(s, water_l, (cx - r * 2, rim_y - r // 2 - 1, r * 4, r + 2), 1)
    pygame.draw.polygon(s, water_d, inner, 1)
    for i in range(5):                                                # rim highlights
        P(s, stone_l, oct_[i % 8][0], oct_[i % 8][1])
    s = add_outline(s)                                                # outline the stonework only, not the water
    cx += 1; rim_y += 1                                               # the outline grew the canvas by 1
    # the jet: a column that bursts at the top and falls back as spray
    hgt = (30, 33, 31, 34, 32, 29, 33, 31)[frame % 8]
    top = rim_y - hgt
    R(s, spray, cx - 1, top + 3, 3, hgt - 4); R(s, foam, cx, top + 2, 1, hgt - 4)
    circle(s, foam, cx, top + 2, 2)
    for i in range(22):                                               # droplets arcing outwards and down
        side = -1 if i % 2 else 1
        t = ((i * 7 + frame * 3) % 16) / 16
        spread = 4 + (i % 5) * 3
        x = cx + side * round(spread * t * 1.6)
        y = top + 2 + round(hgt * (t * t) * 0.95) - round(6 * t * (1 - t) * 4)
        if y < rim_y + 1:
            P(s, foam if t < 0.5 else spray, x, y)
    for i in range(8):                                                # splashes where it lands
        x = cx + ((i * 9 + frame * 5) % 30) - 15
        P(s, foam, x, rim_y + ((i + frame) % 3) - 1)
    pygame.draw.ellipse(s, foam, (cx - 4, rim_y - 2, 8, 3), 1)
    mist = canvas(W + 2, Hh + 2)                                      # a soft haze of spray round the jet
    mr = random.Random(frame * 97 + 5)
    for i in range(46):
        t = mr.random()
        x = cx + round(mr.uniform(-1, 1) * (2 + 16 * t))
        y = top + 3 + round(hgt * t * 0.95) + mr.randrange(-2, 3)
        if y < rim_y: P(mist, (230, 242, 248, 110), x, y)
    s.blit(mist, (0, 0))
    return up(s).convert_alpha()


def jet(frame=0):
    """A fountain jet in City Hall's pool: a column of water that falls back in droplets."""
    s = canvas(14, 34)
    water, light, foam = (110, 180, 228), (180, 224, 246), (244, 250, 255)
    hgt = (26, 29, 27, 30, 28, 25)[frame % 6]
    top = 33 - hgt
    R(s, water, 6, top + 2, 2, hgt - 3); R(s, light, 6, top + 2, 1, hgt - 3)
    R(s, foam, 6, top, 2, 2)
    for i in range(10):                                                  # droplets falling back down
        side = -1 if i % 2 else 1
        k = (i * 3 + frame * 2) % 12
        x = 6 + side * (1 + k // 3)
        y = top + 1 + k + (i % 3)
        if y < 32: P(s, foam if k < 5 else light, x, y)
    R(s, foam, 3, 31, 8, 1); R(s, light, 2, 32, 10, 1)                  # splash ring
    return up(s).convert_alpha()


def steam(frame=0):
    s = canvas(8, 10)
    for i in range(3):
        y = 9 - ((frame * 2 + i * 3) % 9)
        x = 3 + ((i + frame) % 3) - 1
        P(s, (236, 236, 240, 200), x, y); P(s, (236, 236, 240, 140), x + 1, y - 1)
    return up(s).convert_alpha()


def doner(frame=0):
    """Rotating doner spit with the grill glowing behind it."""
    s = _prop(14, 26)
    R(s, (70, 74, 82), 0, 2, 3, 22); R(s, (240, 120, 40), 1, 4, 1, 18)   # grill element
    R(s, (90, 94, 104), 3, 24, 10, 2)                                # base
    R(s, (190, 192, 198), 7, 0, 1, 24)                               # skewer
    meat = [(150, 86, 46), (176, 108, 60), (126, 70, 36)]
    for y in range(3, 22):
        wdt = 3 + (y - 3) // 3 if y < 15 else 8 - (y - 15) // 2
        for x in range(7 - wdt // 2 - 1, 7 + wdt // 2 + 1):
            P(s, meat[(x + y + frame) % 3], x, y)
    for y in range(4, 22, 3):
        P(s, (220, 160, 90), 7 - ((y + frame) % 3), y)
    return up(add_outline(s)).convert_alpha()


def notebook_icon():
    s = canvas(12, 14)
    R(s, (120, 40, 40), 1, 0, 10, 14); R(s, (150, 56, 52), 2, 0, 9, 1)
    R(s, (240, 232, 210), 10, 1, 1, 12)
    R(s, (60, 20, 20), 3, 0, 1, 14)                                  # spine strap
    R(s, (230, 200, 120), 5, 4, 4, 2)                                # label
    return up(add_outline(s)).convert_alpha()


def fountain():
    """Victoria Rooms fountain with the bronze statue of Edward VII on a plinth.
    Returns (surface, foot offset from top in screen px)."""
    s = canvas(52, 44)
    stone, stone_d = BATH_PALE, (190, 176, 140)
    water, water_l = (70, 140, 196), (160, 208, 236)
    ellipse_fill(s, OUTLINE, 26, 34, 26, 9)                        # basin rim (front face)
    ellipse_fill(s, stone_d, 26, 33, 25, 8)
    ellipse_fill(s, stone, 26, 30, 25, 8)
    ellipse_fill(s, water, 26, 30, 22, 6)
    for x0, y0 in ((10, 30), (34, 32), (20, 33), (38, 28)):
        R(s, water_l, x0, y0, 4, 1)
    R(s, OUTLINE, 21, 8, 10, 24)                                    # plinth
    R(s, stone, 22, 9, 8, 22)
    R(s, shade(stone, 0.8), 28, 9, 2, 22)
    R(s, shade(stone, 1.1), 21, 9, 10, 2)
    bronze, bronze_l = (64, 88, 78), (100, 132, 116)               # weathered bronze figure
    R(s, bronze, 24, 0, 4, 9)
    R(s, bronze_l, 24, 0, 2, 3)
    R(s, bronze, 23, 3, 6, 4)
    for x in (12, 40):                                              # water jets
        R(s, water_l, x, 22, 1, 6)
        P(s, water_l, x - 1, 22); P(s, water_l, x + 1, 22)
    return up(s).convert_alpha(), 43 * PX


# ============================================================== characters
def character_frames(look):
    """Upright pixel-art person: 4 directions x 4 walk frames, from a colour 'look' dict."""
    def rgb(h):
        h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    shirt, skin, pants = rgb(look["shirt"]), rgb(look["skin"]), rgb(look["pants"])
    hair = rgb(look["hair"]) if look["hair"] else None
    style = look["style"]
    shoe = (44, 38, 36)
    frames = {}
    for d in ("down", "up", "left"):
        for f in range(4):
            s = canvas(12, 18)
            swing = (0, 1, 0, -1)[f]
            bob = f % 2
            # legs
            if d in ("down", "up"):
                for side, lift in ((0, swing), (1, -swing)):
                    x = 3 + side * 4
                    hh = 5 - max(0, lift)
                    R(s, pants, x, 12 + bob, 2, hh - bob)
                    R(s, shoe, x, 17 - max(0, lift), 2, 1)
            else:
                R(s, shade(pants, 0.8), 5 - swing, 12 + bob, 2, 5 - bob); R(s, shoe, 4 - swing, 17, 3, 1)
                R(s, pants, 5 + swing, 12 + bob, 2, 5 - bob); R(s, shoe, 5 + swing, 17, 3, 1)
            # a long coat (the detective's trench coat) down over the knees
            coat = rgb(look["coat"]) if look.get("coat") else None
            if coat:
                if d in ("down", "up"):
                    R(s, coat, 2, 12 + bob, 8, 3); R(s, shade(coat, 0.8), 2, 14 + bob, 8, 1)
                    if d == "down": R(s, shade(coat, 0.72), 6, 12 + bob, 1, 3)        # where it opens
                else:
                    R(s, coat, 3, 12 + bob, 6, 3); R(s, shade(coat, 0.8), 3, 14 + bob, 6, 1)
            # long hair / backpack behind
            if style == "long" and d == "down":
                R(s, hair, 2, 2 + bob, 8, 7)
            if look.get("pack") and d in ("up", "left"):
                R(s, rgb(look["pack"]), 3 if d == "up" else 7, 7 + bob, 6 if d == "up" else 3, 5)
            # torso
            tw = 6 if d != "left" else 4
            tx = 6 - tw // 2
            top = coat or shirt
            R(s, top, tx, 7 + bob, tw, 6)
            R(s, shade(top, 0.78), tx, 11 + bob, tw, 2)
            R(s, shade(top, 1.15), tx, 7 + bob, 1, 4)
            if coat:
                if d == "down":
                    R(s, shirt, 5, 7 + bob, 2, 3)                               # shirt and tie in the open front
                    P(s, (120, 30, 34), 5, 8 + bob); P(s, (120, 30, 34), 5, 9 + bob)
                    P(s, shade(coat, 1.2), 3, 7 + bob); P(s, shade(coat, 1.2), 8, 7 + bob)   # collar turned up
                R(s, shade(coat, 0.62), tx, 10 + bob, tw, 1)                    # the belt
                if d == "down": P(s, (200, 170, 90), 6, 10 + bob)               # buckle
                if d == "up": P(s, shade(coat, 0.62), 5, 11 + bob); P(s, shade(coat, 0.62), 6, 12 + bob)
            if look.get("collar") and d == "down":
                P(s, rgb(look["collar"]), 5, 7 + bob); P(s, rgb(look["collar"]), 6, 7 + bob)
            # arms
            sleeve = shade(top, 0.9)
            if d in ("down", "up"):
                for x, sw in ((2, swing), (9, -swing)):
                    R(s, sleeve, x, 7 + bob + max(0, sw), 1, 4)
                    P(s, skin, x, 11 + bob + max(0, sw))
            else:
                R(s, sleeve, 5 + swing, 8 + bob, 2, 4)
                P(s, skin, 5 + swing, 12 + bob)
            # head
            if style == "robot":
                metal = skin
                R(s, metal, 3, 1 + bob, 6, 6)
                R(s, shade(metal, 0.8), 3, 5 + bob, 6, 2)
                if d == "down": R(s, hair, 4, 3 + bob, 4, 1)
                elif d == "left": R(s, hair, 3, 3 + bob, 2, 1)
                P(s, metal, 6, 0 + bob)
            else:
                R(s, skin, 3, 1 + bob, 6, 6)
                R(s, shade(skin, 0.85), 3, 6 + bob, 6, 1)
                if d == "left":
                    P(s, skin, 2, 4 + bob)                          # nose
                if hair is not None:
                    if style in ("short", "long"):
                        if d == "down":
                            R(s, hair, 3, 0 + bob, 6, 2); P(s, hair, 3, 2 + bob); P(s, hair, 8, 2 + bob)
                        elif d == "up":
                            R(s, hair, 3, 0 + bob, 6, 6)
                        else:
                            R(s, hair, 3, 0 + bob, 6, 2); R(s, hair, 6, 2 + bob, 3, 3)
                        if style == "long" and d in ("up", "left"):
                            R(s, hair, 3 if d == "up" else 6, 3 + bob, 6 if d == "up" else 3, 6)
                    elif style == "helmet":
                        R(s, hair, 2, 0 + bob, 8, 3); R(s, shade(hair, 0.75), 2, 3 + bob, 8, 1)
                        if d == "up": R(s, hair, 3, 4 + bob, 6, 2)
                    elif style == "cap":
                        R(s, hair, 3, 0 + bob, 6, 2)
                        if d == "down": R(s, shade(hair, 0.7), 3, 2 + bob, 6, 1)
                        elif d == "left": R(s, shade(hair, 0.7), 1, 2 + bob, 3, 1)
                        else: R(s, hair, 3, 2 + bob, 6, 3)
                if d == "down":
                    P(s, (30, 28, 34), 4, 4 + bob); P(s, (30, 28, 34), 7, 4 + bob)
                elif d == "left":
                    P(s, (30, 28, 34), 3, 4 + bob)
                if look.get("cig") and d != "up":                        # a cigarette, always, with a glowing tip
                    ember = (255, 120, 40) if f % 2 == 0 else (255, 196, 80)
                    if d == "down":
                        R(s, (244, 242, 236), 7, 5 + bob, 3, 1); P(s, ember, 10, 5 + bob)
                    else:
                        R(s, (244, 242, 236), 1, 5 + bob, 2, 1); P(s, ember, 0, 5 + bob)
            img = up(add_outline(s)).convert_alpha()
            frames[(d, f)] = img
            if d == "left":
                frames[("right", f)] = pygame.transform.flip(img, True, False)
    return frames


# ============================================================== cars
def car(colour, facing_right=True, seed=0):
    """Parked car seen from the side and a little above. Returns screen-size art (about 2 tiles wide)."""
    s = canvas(30, 16)
    body, dark, light = colour, shade(colour, 0.72), shade(colour, 1.18)
    R(s, body, 1, 6, 28, 6)                                         # lower body
    R(s, light, 1, 6, 28, 1)
    R(s, dark, 1, 11, 28, 1)
    R(s, body, 7, 2, 15, 5)                                         # cabin
    R(s, light, 8, 2, 13, 1)
    R(s, GLASS, 8, 3, 6, 3); R(s, GLASS, 15, 3, 6, 3)               # windows
    P(s, GLASS_L, 8, 3); P(s, GLASS_L, 15, 3)
    R(s, body, 14, 3, 1, 3)
    R(s, (250, 230, 150), 28, 7, 1, 2)                              # headlight
    R(s, (200, 50, 50), 1, 7, 1, 2)                                 # tail light
    for x in (4, 21):                                               # wheels
        R(s, (28, 28, 30), x, 10, 5, 5)
        R(s, (130, 132, 140), x + 1, 11, 3, 3)
        P(s, (60, 60, 64), x + 2, 12)
    s = add_outline(s)
    if not facing_right:
        s = pygame.transform.flip(s, True, False)
    return up(s).convert_alpha()


# ============================================================== shop doors & signs (street side)
def door_mat():
    s = canvas(L, L)
    R(s, (90, 62, 40), 3, 2, 10, 5)
    R(s, (120, 84, 54), 4, 3, 8, 3)
    return up(s).convert_alpha()


def hanging_sign(colour, kind):
    """Bracket sign that sticks out over the pavement, with a little icon for the shop type."""
    s = canvas(12, 12)
    iron = (34, 34, 38)
    R(s, iron, 0, 0, 12, 1); R(s, iron, 1, 0, 1, 3); R(s, iron, 10, 0, 1, 3)
    R(s, shade(colour, 0.6), 1, 3, 10, 8)
    R(s, colour, 2, 4, 8, 6)
    ic = (244, 236, 214)
    if kind == "cafe":                                              # cup
        R(s, ic, 4, 6, 4, 3); P(s, ic, 8, 7); P(s, ic, 5, 5); P(s, ic, 6, 4)
    elif kind == "corner":                                          # basket
        R(s, ic, 3, 7, 6, 2); P(s, ic, 4, 6); P(s, ic, 7, 6); R(s, ic, 4, 5, 4, 1)
    elif kind == "clothes":                                         # coat hanger
        P(s, ic, 6, 5); R(s, ic, 4, 7, 5, 1); P(s, ic, 5, 6); P(s, ic, 7, 6); P(s, ic, 3, 8); P(s, ic, 9, 8)
    elif kind == "books":                                           # open book
        R(s, ic, 3, 6, 3, 3); R(s, ic, 7, 6, 3, 3); P(s, shade(colour, 0.6), 6, 7)
    elif kind == "barber":                                          # barber pole stripes
        R(s, ic, 5, 5, 3, 4); P(s, (200, 40, 40), 5, 6); P(s, (200, 40, 40), 6, 7); P(s, (60, 80, 180), 7, 8)
    elif kind == "gym":                                             # dumbbell
        R(s, ic, 3, 6, 2, 3); R(s, ic, 8, 6, 2, 3); R(s, ic, 5, 7, 3, 1)
    return up(add_outline(s)).convert_alpha()


# ============================================================== interiors
def floor_tile(kind, v=0):
    rng = random.Random(7000 + v)
    s = canvas(L, L)
    if kind == "dance":                                              # light-up club dance floor
        cols = [(70, 30, 110), (140, 40, 140), (30, 60, 140), (20, 18, 30)]
        for i in range(2):
            for j in range(2):
                c = cols[(i + j * 2 + v) % 4]
                R(s, c, i * 8, j * 8, 8, 8); R(s, shade(c, 1.3), i * 8, j * 8, 8, 1)
                R(s, shade(c, 0.6), i * 8 + 7, j * 8, 1, 8)
        return up(s).convert()
    if kind == "checker":                                           # café / barber tiles
        a, b = (232, 226, 210), (60, 64, 72)
        for y in range(0, L, 8):
            for x in range(0, L, 8):
                R(s, a if (x + y) // 8 % 2 == 0 else b, x, y, 8, 8)
        speckle(s, rng, [(210, 204, 190)], 0.03)
    elif kind == "rubber":                                          # gym floor
        s.fill((58, 60, 66))
        speckle(s, rng, [(76, 80, 88), (46, 48, 52)], 0.25)
        R(s, (44, 46, 50), 0, L - 1, L, 1); R(s, (44, 46, 50), L - 1, 0, 1, L)
    elif kind == "shop":                                            # light shop vinyl
        s.fill((214, 214, 206))
        R(s, (196, 196, 188), 0, L - 1, L, 1); R(s, (196, 196, 188), L - 1, 0, 1, L)
        speckle(s, rng, [(204, 204, 196)], 0.08)
    elif kind == "carpet":
        s.fill((122, 60, 58))
        speckle(s, rng, [(136, 70, 66), (108, 52, 50)], 0.3)
    return up(s).convert()


def interior_wall(mask, colour=(232, 220, 196)):
    """Indoor wall piece (same 3/4 shape as outdoor walls): plaster face, skirting, dark top."""
    WH = 11                                                         # wall face height in logical px
    s = canvas(L, L + WH)
    top = (70, 58, 54)
    R(s, top, 0, 0, L, L)
    R(s, shade(top, 1.25), 0, 0, L, 1)
    if not mask & 4:
        R(s, colour, 0, L, L, WH)
        R(s, shade(colour, 1.08), 0, L, L, 1)
        R(s, shade(colour, 0.85), 0, L + WH - 4, L, 1)               # dado line
        R(s, (110, 84, 60), 0, L + WH - 3, L, 3)                     # skirting
        R(s, OUTLINE, 0, L - 1, L, 1)
    if not mask & 8: R(s, OUTLINE, 0, 0, 1, L + (WH if not mask & 4 else 0))
    if not mask & 2: R(s, OUTLINE, L - 1, 0, 1, L + (WH if not mask & 4 else 0))
    if not mask & 1: R(s, OUTLINE, 0, 0, L, 1)
    return up(s).convert_alpha(), WH * PX


def _prop(w, h):
    return canvas(w, h)


def counter(kind="wood", till=False, end=None):
    """One tile of shop counter; 'end' = 'l'/'r' for rounded ends."""
    s = _prop(L, 14)
    top, front = ((214, 200, 170), (150, 104, 66)) if kind == "wood" else ((230, 232, 236), (90, 96, 108))
    R(s, top, 0, 2, L, 4); R(s, shade(top, 1.1), 0, 2, L, 1)
    R(s, front, 0, 6, L, 8); R(s, shade(front, 0.8), 0, 12, L, 2)
    for x in range(2, L, 5):
        R(s, shade(front, 0.88), x, 7, 1, 5)
    if till:                                                        # cash register
        R(s, (40, 42, 48), 4, 0, 8, 4); R(s, (110, 200, 140), 5, 0, 4, 1); R(s, (180, 180, 186), 5, 2, 6, 1)
    if end == "l": R(s, OUTLINE, 0, 2, 1, 12)
    if end == "r": R(s, OUTLINE, L - 1, 2, 1, 12)
    return up(s).convert_alpha()


def coffee_machine():
    s = _prop(L, 16)
    R(s, (150, 104, 66), 0, 8, L, 8); R(s, (214, 200, 170), 0, 6, L, 3)
    R(s, (190, 192, 198), 3, 0, 10, 7); R(s, (230, 232, 236), 3, 0, 10, 1)
    R(s, (40, 40, 44), 5, 3, 2, 3); R(s, (40, 40, 44), 9, 3, 2, 3)
    R(s, (240, 236, 226), 5, 6, 2, 1); R(s, (240, 236, 226), 9, 6, 2, 1)
    return up(add_outline(s)).convert_alpha()


def shelf(kind="corner", seed=0):
    """Wall shelving full of goods; kind picks what's on it."""
    rng = random.Random(seed)
    s = _prop(L, 22)
    wood = (138, 96, 62) if kind != "books" else (110, 72, 48)
    R(s, wood, 0, 0, L, 22); R(s, shade(wood, 0.75), 0, 0, 1, 22); R(s, shade(wood, 0.75), L - 1, 0, 1, 22)
    for y in (6, 13, 20):
        R(s, shade(wood, 1.2), 0, y, L, 1)
    for row_y in (1, 8, 15):
        x = 1
        while x < L - 1:
            if kind == "books":
                w = rng.choice((1, 1, 2))
                c = rng.choice([(150, 40, 40), (40, 70, 130), (40, 110, 70), (200, 170, 60), (90, 60, 120), (220, 210, 190)])
                R(s, c, x, row_y + rng.randrange(0, 2), w, 5 - rng.randrange(0, 2))
                x += w
            else:
                w = rng.choice((2, 2, 3))
                c = rng.choice([(220, 60, 50), (250, 200, 60), (60, 140, 220), (90, 180, 80), (240, 240, 230), (240, 140, 40)])
                R(s, c, x, row_y + 1, w, 4); R(s, shade(c, 1.2), x, row_y + 1, w, 1)
                x += w + 1
    return up(s).convert_alpha()


def fridge(seed=0):
    rng = random.Random(seed)
    s = _prop(L, 24)
    R(s, (200, 204, 210), 0, 0, L, 24); R(s, (230, 232, 236), 0, 0, L, 2)
    R(s, (150, 210, 230), 2, 3, 12, 19)
    for y in (8, 14):
        R(s, (210, 230, 236), 2, y, 12, 1)
    for row in (4, 9, 15):
        for x in range(3, 13, 3):
            c = rng.choice([(220, 60, 50), (60, 140, 220), (240, 200, 60), (90, 180, 80), (240, 240, 240)])
            R(s, c, x, row + 1, 2, 4)
    P(s, (240, 248, 255), 3, 4)
    return up(add_outline(s)).convert_alpha()


def cafe_table(seed=0):
    """Small round café table with two chairs."""
    rng = random.Random(seed)
    s = _prop(20, 14)
    wood = (150, 104, 66)
    for cx in (2, 16):                                              # chairs
        R(s, (60, 64, 72), cx, 2, 3, 9); R(s, (90, 96, 108), cx, 6, 3, 1)
    ellipse_fill(s, (110, 76, 48), 10, 6, 6, 3)
    ellipse_fill(s, wood, 10, 5, 6, 3)
    R(s, (110, 76, 48), 9, 8, 2, 5)
    R(s, (240, 236, 226), 7, 3, 2, 2)                               # cup
    if rng.random() < 0.6:
        R(s, (220, 180, 100), 12, 4, 2, 1)                          # pastry
    return up(add_outline(s)).convert_alpha()


def clothes_rail(seed=0):
    rng = random.Random(seed)
    s = _prop(L, 20)
    chrome = (170, 174, 182)
    R(s, chrome, 1, 1, 14, 1); R(s, chrome, 1, 1, 1, 19); R(s, chrome, 14, 1, 1, 19)
    for x in range(2, 14, 2):
        c = rng.choice([(40, 60, 110), (180, 50, 50), (230, 220, 200), (60, 110, 70), (30, 30, 34), (200, 150, 60)])
        R(s, c, x, 2, 2, 12 + rng.randrange(0, 3)); R(s, shade(c, 1.2), x, 2, 1, 10)
    return up(add_outline(s)).convert_alpha()


def barber_chair():
    s = _prop(L, 18)
    R(s, (140, 30, 36), 3, 0, 10, 8); R(s, (180, 44, 50), 4, 1, 8, 2)   # back
    R(s, (140, 30, 36), 2, 8, 12, 4)                                # seat
    R(s, (190, 192, 198), 7, 12, 2, 4); R(s, (160, 162, 170), 3, 16, 10, 2)
    return up(add_outline(s)).convert_alpha()


def mirror():
    s = _prop(L, 12)
    R(s, (200, 170, 90), 2, 0, 12, 12)
    R(s, (190, 220, 232), 3, 1, 10, 10)
    P(s, (240, 250, 255), 4, 2); P(s, (240, 250, 255), 5, 2); P(s, (240, 250, 255), 4, 3)
    return up(add_outline(s)).convert_alpha()


def treadmill():
    s = _prop(L, 20)
    R(s, (40, 42, 48), 1, 6, 14, 14); R(s, (24, 24, 28), 3, 8, 10, 11)
    R(s, (70, 74, 82), 1, 0, 2, 8); R(s, (70, 74, 82), 13, 0, 2, 8)
    R(s, (70, 74, 82), 1, 0, 14, 2); R(s, (110, 200, 140), 6, 0, 4, 1)
    return up(add_outline(s)).convert_alpha()


def weights_rack():
    s = _prop(L, 14)
    R(s, (70, 74, 82), 0, 4, L, 2); R(s, (70, 74, 82), 0, 9, L, 2)
    R(s, (70, 74, 82), 1, 4, 1, 10); R(s, (70, 74, 82), 14, 4, 1, 10)
    for i, x in enumerate(range(2, 14, 3)):
        c = (30, 30, 34)
        R(s, c, x, 1 + (i % 2), 2, 3); R(s, c, x, 7, 2, 3)
    return up(add_outline(s)).convert_alpha()


def bench_press():
    s = _prop(20, 14)
    R(s, (30, 30, 34), 3, 6, 14, 3); R(s, (140, 30, 36), 4, 6, 12, 2)
    R(s, (70, 74, 82), 4, 9, 1, 5); R(s, (70, 74, 82), 15, 9, 1, 5)
    R(s, (70, 74, 82), 1, 0, 1, 7); R(s, (70, 74, 82), 18, 0, 1, 7)
    R(s, (170, 174, 182), 0, 2, 20, 1)                              # bar
    R(s, (30, 30, 34), 0, 0, 2, 5); R(s, (30, 30, 34), 18, 0, 2, 5)  # plates
    return up(add_outline(s)).convert_alpha()


def plant():
    s = _prop(12, 16)
    R(s, (180, 100, 70), 3, 10, 6, 6); R(s, (210, 130, 90), 3, 10, 6, 1)
    for cx, cy, r in ((6, 6, 4), (3, 7, 2), (9, 7, 2), (6, 3, 2)):
        circle(s, LEAF[1], cx, cy, r)
    for x, y in ((5, 3), (7, 5), (4, 7), (8, 8)):
        P(s, LEAF[3], x, y)
    return up(add_outline(s)).convert_alpha()


def rug(colour=(60, 90, 140)):
    s = canvas(L * 3, L * 2)
    R(s, shade(colour, 0.7), 2, 2, L * 3 - 4, L * 2 - 4)
    R(s, colour, 3, 3, L * 3 - 6, L * 2 - 6)
    for x in range(4, L * 3 - 4, 3):
        P(s, (230, 220, 190), x, 2); P(s, (230, 220, 190), x, L * 2 - 3)
    R(s, shade(colour, 1.25), 8, 8, L * 3 - 16, L * 2 - 16)
    return up(s).convert_alpha()


def exit_mat():
    s = canvas(L, L)
    R(s, (60, 46, 36), 1, 4, 14, 9)
    R(s, (90, 70, 52), 2, 5, 12, 7)
    for x in (5, 8, 11):                                            # arrow pointing out (down)
        P(s, (240, 220, 160), x - 1, 7)
    R(s, (240, 220, 160), 7, 6, 2, 4); P(s, (240, 220, 160), 6, 9); P(s, (240, 220, 160), 9, 9)
    return up(s).convert_alpha()


def railing():
    """Black iron railings with spear finials (one tile long; tiles join up into a run)."""
    s = canvas(L, 14)
    iron, hi = (28, 28, 32), (78, 80, 90)
    R(s, iron, 0, 3, L, 1); R(s, iron, 0, 11, L, 1)
    R(s, (120, 116, 108), 0, 12, L, 2)                              # low stone kerb wall
    R(s, (90, 86, 80), 0, 13, L, 1)
    for x in range(1, L, 3):
        R(s, iron, x, 1, 1, 11)
        P(s, hi, x, 1)
        P(s, iron, x, 0)                                            # spear tip
    return up(s).convert_alpha()


def statue(seed=0):
    """Bronze figure on a stone plinth. Returns (surface, foot offset)."""
    s = canvas(18, 40)
    stone = (214, 208, 194)
    R(s, OUTLINE, 2, 22, 14, 18)
    R(s, stone, 3, 23, 12, 16)
    R(s, shade(stone, 1.1), 2, 22, 14, 2); R(s, shade(stone, 0.78), 12, 24, 3, 15)
    R(s, shade(stone, 0.85), 5, 28, 8, 4)                           # inscription panel
    R(s, shade(stone, 1.1), 1, 37, 16, 3)                           # base step
    bronze, bl, bd = (64, 92, 80), (104, 140, 120), (40, 60, 52)
    R(s, OUTLINE, 5, 1, 8, 22)
    R(s, bronze, 6, 7, 6, 15)                                       # robed figure
    R(s, bd, 10, 7, 2, 15)
    R(s, bl, 6, 7, 1, 12)
    circle(s, bronze, 9, 4, 2); P(s, bl, 8, 3)                      # head
    if seed % 2: R(s, bronze, 12, 9, 2, 6)                          # outstretched arm
    else: R(s, bronze, 4, 10, 2, 5)
    return up(s).convert_alpha(), 40 * PX


def unicorn(flip=False):
    """Gilded unicorn, as on each end of City Hall's roof."""
    s = canvas(18, 16)
    gold, gl, gd = (232, 190, 70), (252, 230, 150), (176, 132, 40)
    R(s, OUTLINE, 3, 5, 11, 7)
    R(s, gold, 4, 6, 9, 5)                                          # body
    R(s, gl, 4, 6, 9, 1)
    R(s, OUTLINE, 11, 1, 5, 6)
    R(s, gold, 12, 2, 3, 4)                                         # head + neck
    P(s, gl, 12, 2)
    R(s, (250, 240, 200), 15, 0, 1, 2); P(s, (250, 240, 200), 16, 0)   # horn
    for lx_ in (4, 6, 10, 12):                                      # legs (rearing front pair)
        R(s, gd, lx_, 11, 1, 3 if lx_ < 9 else 2)
    R(s, gd, 12, 9, 2, 1)
    R(s, gd, 1, 6, 3, 1); P(s, gd, 1, 7)                            # tail
    R(s, (150, 146, 136), 2, 14, 13, 2)                             # plinth
    img = up(s).convert_alpha()
    return pygame.transform.flip(img, True, False) if flip else img


# ============================================================== shop signs with made-up brand names
# a tiny 5-pixel-tall capital font ('#' = ink)
FONT = {
    'A': ".#./#.#/###/#.#/#.#", 'B': "##./#.#/##./#.#/##.", 'C': ".##/#../#../#../.##", 'D': "##./#.#/#.#/#.#/##.",
    'E': "###/#../##./#../###", 'F': "###/#../##./#../#..", 'G': ".##/#../#.#/#.#/.##", 'H': "#.#/#.#/###/#.#/#.#",
    'I': "###/.#./.#./.#./###", 'J': "..#/..#/..#/#.#/.#.", 'K': "#.#/#.#/##./#.#/#.#", 'L': "#../#../#../#../###",
    'M': "#...#/##.##/#.#.#/#...#/#...#", 'N': "#..#/##.#/#.##/#..#/#..#", 'O': ".#./#.#/#.#/#.#/.#.",
    'P': "##./#.#/##./#../#..", 'Q': ".#./#.#/#.#/##./.##", 'R': "##./#.#/##./#.#/#.#", 'S': ".##/#../.#./..#/##.",
    'T': "###/.#./.#./.#./.#.", 'U': "#.#/#.#/#.#/#.#/###", 'V': "#.#/#.#/#.#/#.#/.#.", 'W': "#...#/#...#/#.#.#/##.##/#...#",
    'X': "#.#/#.#/.#./#.#/#.#", 'Y': "#.#/#.#/.#./.#./.#.", 'Z': "###/..#/.#./#../###",
    '&': ".#../#.#./.#../#.##/.##.", "'": "#/#/././.", '-': ".../.../###/.../...", '.': "./././././#"[:9],
    '1': ".#./##./.#./.#./###", '2': "##./..#/.#./#../###", '3': "##./..#/.#./..#/##.", '4': "#.#/#.#/###/..#/..#",
    '5': "###/#../##./..#/##.", '7': "###/..#/.#./.#./.#.", '9': ".#./#.#/.##/..#/##.", '0': ".#./#.#/#.#/#.#/.#.",
    '6': ".##/#../##./#.#/.#.", '8': ".#./#.#/.#./#.#/.#.",
    ' ': "../../../../..",
}
FONT['.'] = "././././#"


def text_width(text):
    return sum(len(FONT.get(ch, FONT[' ']).split('/')[0]) for ch in text.upper()) + max(0, len(text) - 1)


def draw_text(s, text, x, y, colour, shadow=None):
    for ch in text.upper():
        rows = FONT.get(ch, FONT[' ']).split('/')
        for ry, row in enumerate(rows):
            for rx, c in enumerate(row):
                if c == '#':
                    if shadow: P(s, shadow, x + rx + 1, y + ry + 1)
                    P(s, colour, x + rx, y + ry)
        x += len(rows[0]) + 1


SIGN_H = 9


def _sign_board(s, x, y, w, h, brand):
    """The board itself, in the shop's own style."""
    bg, fg, style = tuple(brand['bg']), tuple(brand['fg']), brand['style']
    R(s, OUTLINE, x, y, w, h)
    R(s, bg, x + 1, y + 1, w - 2, h - 2)
    R(s, shade(bg, 1.2), x + 1, y + 1, w - 2, 1)                  # top highlight
    R(s, shade(bg, 0.7), x + 1, y + h - 2, w - 2, 1)
    if style == 1:                                                 # gilded trim
        R(s, (214, 178, 80), x + 1, y + 1, w - 2, 1); R(s, (170, 130, 50), x + 1, y + h - 2, w - 2, 1)
        R(s, (214, 178, 80), x + 1, y + 1, 1, h - 2); R(s, (214, 178, 80), x + w - 2, y + 1, 1, h - 2)
    elif style == 2:                                               # inset double line
        R(s, shade(fg, 0.85), x + 2, y + 2, w - 4, 1); R(s, shade(fg, 0.85), x + 2, y + h - 3, w - 4, 1)
    elif style == 3:                                               # rounded ends
        for (px_, py_) in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
            P(s, (0, 0, 0, 0), px_, py_)
    elif style == 4:                                               # striped awning edge underneath
        for i in range(0, w, 4):
            R(s, fg, x + i, y + h - 2, 2, 1)
    elif style == 5:                                               # bulb lights along the top
        for i in range(2, w - 2, 3):
            P(s, (250, 230, 150), x + i, y + 1)


def shop_sign(brand, width):
    """Fascia board right across a shopfront, with the brand name centred on it."""
    s = canvas(width, SIGN_H)
    _sign_board(s, 0, 0, width, SIGN_H, brand)
    tw = text_width(brand['name'])
    icon = width - tw >= 16
    x = (width - tw) // 2 + (3 if icon else 0)
    if icon:                                                       # little shop-type icon on the left
        _sign_icon(s, x - 7, 2, brand['kind'], tuple(brand['fg']))
    draw_text(s, brand['name'], x, 2, tuple(brand['fg']), shadow=shade(tuple(brand['bg']), 0.55))
    return s


def _sign_icon(s, x, y, kind, c):
    pics = {"cafe": "....#/###.#/####./###../.#...", "corner": "#..../####./####./.#.#.",
            "clothes": ".#.#./#####/.###./.###./.###.", "books": "##.##/##.##/##.##/##.##/#####",
            "barber": "#...#/.#.#./..#../.#.#./#...#", "gym": "#...#/#####/#...#"}
    for ry, row in enumerate(pics.get(kind, "").split('/')):
        for rx, ch in enumerate(row):
            if ch == '#': P(s, c, x + rx, y + ry)


def roof_sign(brand):
    """Sign board up on posts above a far-side shop's roof, so you can read it from the street."""
    tw = text_width(brand['name'])
    w = tw + 6
    h = SIGN_H + 5
    s = canvas(w, h)
    iron = (34, 34, 38)
    for px_ in (3, w - 4):                                         # posts
        R(s, iron, px_, SIGN_H - 1, 1, 6)
    R(s, iron, 2, h - 1, 3, 1); R(s, iron, w - 5, h - 1, 3, 1)
    _sign_board(s, 0, 0, w, SIGN_H, brand)
    draw_text(s, brand['name'], 3, 2, tuple(brand['fg']), shadow=shade(tuple(brand['bg']), 0.55))
    return up(s).convert_alpha()



# ============================================================== the Frogmore Street bridge, stairs and OMG
CONCRETE = (172, 170, 164)


def _concrete(b, lx, bw):
    """Board-marked concrete wall, a bit stained, with the odd bit of graffiti.
    (style P with a 'pennant' flag = rubble Pennant stone with moss, optionally a green door.)"""
    H = building_height(b)
    s = canvas(L, H)
    if b.get("pennant"):
        rng = random.Random(b["seed"] * 5 + lx)
        base = tuple(b.get("stone") or (96, 92, 88))
        R(s, base, 0, 0, L, H)
        for y in range(0, H, 3):
            off = (y // 3 + lx) % 2 * 3
            for x in range(off, L, 6): R(s, shade(base, 0.72), x, y, 1, 2)
            R(s, shade(base, 0.84), 0, y + 2, L, 1)
        for _ in range(10): P(s, rng.choice([(80, 120, 60), (100, 140, 70)]), rng.randrange(L), rng.randrange(H))
        R(s, shade(base, 1.2), 0, 0, L, 1)
        if lx == b.get("door_lx", -1):                            # the green door in the wall
            R(s, (24, 60, 44), 4, H - 15, 8, 15); R(s, (40, 96, 70), 5, H - 14, 6, 13)
            R(s, (180, 210, 190), 6, H - 12, 4, 4); P(s, (220, 190, 90), 9, H - 7)
            R(s, (150, 146, 136), 3, H - 16, 10, 1)
        R(s, shade(base, 0.5), 0, H - 1, L, 1)
        return s
    rng = random.Random(b["seed"] * 13 + lx)
    CONCRETE = tuple(b.get("stone") or (172, 170, 164))
    R(s, CONCRETE, 0, 0, L, H)
    for y in range(2, H, 4):                                         # shuttering board lines
        R(s, shade(CONCRETE, 0.9), 0, y, L, 1)
    for x in range(0, L, 8):
        R(s, shade(CONCRETE, 0.86), x, 0, 1, H)
    speckle(s, rng, [shade(CONCRETE, 0.92), shade(CONCRETE, 1.05)], 0.1)
    for _ in range(4):                                               # rain stains running down from the top
        x = rng.randrange(L); h = rng.randrange(4, H // 2)
        R(s, shade(CONCRETE, 0.78), x, 0, 1, h)
    if b.get("graffiti") and rng.random() < 0.6:                     # random spray-paint tags (made up)
        col = rng.choice([(220, 60, 120), (60, 160, 230), (250, 200, 50), (90, 210, 110), (240, 240, 240)])
        y = rng.randrange(H // 3, H - 8)
        for i in range(rng.randrange(6, 12)):
            P(s, col, 2 + i, y + round(2 * math.sin(i * 1.3 + lx)))
            if i % 3 == 0: P(s, col, 2 + i, y + 1 + round(2 * math.sin(i * 1.3 + lx)))
    R(s, shade(CONCRETE, 1.1), 0, 0, L, 1)
    R(s, shade(CONCRETE, 0.55), 0, H - 1, L, 1)
    return s


_OMG_CACHE = {}


def _omg_front(bw, variant=0):
    """OMG's frontage: black and purple, a big pink neon OMG, a canopy over the door (variant 1 = no door)."""
    key = (bw, variant)
    if key in _OMG_CACHE: return _OMG_CACHE[key]
    w, H = bw * L, 44
    s = canvas(w, H)
    rng = random.Random(4)
    wall, wall_l, purple = (36, 30, 44), (52, 44, 62), (90, 40, 120)
    R(s, wall, 0, 0, w, H)
    for y in range(3, H, 4):
        R(s, wall_l, 0, y, w, 1)
    R(s, purple, 0, 0, w, 3); R(s, shade(purple, 1.3), 0, 0, w, 1)
    # neon OMG: letters drawn at double size with a glow round them
    txt = canvas(text_width("OMG"), 5)
    draw_text(txt, "OMG", 0, 0, (255, 120, 220))
    big = pygame.transform.scale(txt, (txt.get_width() * 3, 15))
    gx = (w - big.get_width()) // 2
    glow = pygame.transform.scale(txt, (txt.get_width() * 3 + 4, 19))
    glow.fill((255, 60, 180, 90), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(glow, (gx - 2, 5))
    s.blit(big, (gx, 7))
    for x in range(gx - 4, gx + big.get_width() + 4, 2):             # neon tube border
        P(s, (120, 230, 255), x, 4); P(s, (120, 230, 255), x, 24)
    if variant == 2:                                               # the yard side: painted black, covered in tags
        R(s, (204, 196, 176), 0, 0, w, H // 3)
        R(s, (30, 30, 34), 0, H // 3, w, H - H // 3)
        _tags(s, rng, 0, H // 3, w, H - H // 3, n=bw * 3)
        R(s, (200, 200, 196), w - 6, 0, 1, H)
        R(s, (40, 40, 44), 0, H - 1, w, 1)
        _OMG_CACHE[key] = s
        return s
    if variant == 0:
        dx = w // 2 - 6
        R(s, (20, 18, 24), dx, H - 15, 12, 15)                       # double doors
        R(s, (60, 54, 70), dx + 1, H - 14, 4, 13); R(s, (60, 54, 70), dx + 7, H - 14, 4, 13)
        R(s, purple, dx - 5, H - 19, 22, 3); R(s, shade(purple, 1.4), dx - 5, H - 19, 22, 1)   # canopy
        for x in range(dx - 4, dx + 17, 3): P(s, (255, 230, 140), x, H - 17)
        R(s, (230, 30, 60), dx - 6, H - 9, 1, 9); R(s, (230, 30, 60), dx + 17, H - 9, 1, 9)    # red rope posts
    else:
        for x in range(4, w - 4, 10):                                # blacked-out windows
            R(s, (24, 22, 30), x, H - 14, 6, 9); R(s, (70, 50, 90), x, H - 14, 6, 1)
    R(s, shade(wall, 0.6), 0, H - 1, w, 1)
    _OMG_CACHE[key] = s
    return s


def stairs_tile(k=1.0, v=0):
    """Stone steps (treads with darker risers). k darkens them as they go down into the cutting."""
    s = canvas(L, L)
    stone = shade((122, 114, 106), k)                              # dark, worn stone
    rng = random.Random(900 + v)
    for i, y in enumerate(range(0, L, 4)):
        R(s, shade(stone, 1.08), 0, y, L, 2)                         # tread
        R(s, shade(stone, 0.8), 0, y + 2, L, 1)                      # nosing shadow
        R(s, shade(stone, 0.68), 0, y + 3, L, 1)                     # riser
    speckle(s, rng, [shade(stone, 0.92)], 0.06)
    R(s, shade(stone, 0.6), 0, 0, 1, L); R(s, shade(stone, 0.6), L - 1, 0, 1, L)
    return up(s).convert()


def deep_road_tile(v=0, centre=False, k=0.58):
    """Tarmac seen down in the cutting below the bridge: darker, optional dashed centre line."""
    s = tarmac_tile(v)
    if centre:
        for y in range(1, L, 8): R(s, WHITE, 0, y, 1, 4)
    dim = canvas(L, L); dim.fill((int(255 * k), int(255 * k), int(255 * k * 1.06), 255))
    s.blit(dim, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    return up(s).convert()


def railing_v():
    """Iron railing running up the screen (along the edge of the stairs)."""
    s = canvas(4, L + 10)
    iron = (28, 28, 32)
    R(s, iron, 1, 0, 1, L + 10)
    for y in range(2, L + 10, 3):
        R(s, iron, 0, y, 3, 1)
    R(s, (78, 80, 90), 1, 0, 1, 3)
    return up(s).convert_alpha()


def car_vertical(colour, down=True, seed=0):
    """Car seen from above, driving up or down the screen (towards you = you see its front)."""
    w, h = 18, 28
    s = canvas(w, h)
    body, dark, light = colour, shade(colour, 0.7), shade(colour, 1.2)
    glass, glass_l = (50, 62, 80), (120, 150, 176)
    R(s, body, 2, 1, 14, 22)                                         # body seen from above
    R(s, light, 3, 1, 12, 1)
    R(s, dark, 2, 21, 14, 2)
    for wy in (4, 17):                                               # wheels peeking out
        R(s, (24, 24, 26), 0, wy, 2, 5); R(s, (24, 24, 26), 16, wy, 2, 5)
    if down:
        R(s, glass, 4, 4, 10, 3); P(s, glass_l, 5, 4)               # rear window (far end)
        R(s, light, 4, 7, 10, 6)                                     # roof
        R(s, glass, 3, 13, 12, 4); R(s, glass_l, 4, 13, 4, 1)       # windscreen (near end)
        R(s, body, 2, 23, 14, 4)                                     # front face
        R(s, (250, 240, 200), 3, 24, 3, 2); R(s, (250, 240, 200), 12, 24, 3, 2)   # headlights
        R(s, (40, 40, 44), 6, 24, 6, 2)                              # grille
    else:
        R(s, glass, 3, 4, 12, 4); R(s, glass_l, 4, 4, 4, 1)         # windscreen (far end)
        R(s, light, 4, 8, 10, 6)
        R(s, glass, 4, 14, 10, 3); P(s, glass_l, 5, 14)             # rear window (near end)
        R(s, body, 2, 23, 14, 4)
        R(s, (220, 40, 40), 3, 24, 3, 2); R(s, (220, 40, 40), 12, 24, 3, 2)       # tail lights
        R(s, (230, 230, 220), 7, 24, 4, 1)                           # number plate
    R(s, (30, 30, 34), 2, 27, 14, 1)
    return up(add_outline(s)).convert_alpha()


def bridge_fascia(v=0, h=26):
    """The concrete edge of the Park Street bridge, seen from underneath."""
    s = canvas(L, h)
    rng = random.Random(700 + v)
    R(s, (150, 148, 142), 0, 0, L, h)
    R(s, (186, 184, 178), 0, 0, L, 3)                                # parapet coping
    R(s, (120, 118, 112), 0, 3, L, 1)
    R(s, (110, 108, 104), 0, h - 6, L, 6)                            # underside in shadow
    R(s, (70, 68, 66), 0, h - 2, L, 2)
    for _ in range(3):
        x = rng.randrange(L); R(s, (128, 126, 120), x, 4, 1, rng.randrange(4, h - 8))
    return up(s).convert_alpha()


def dj_booth():
    s = _prop(32, 18)
    R(s, (24, 22, 28), 0, 6, 32, 12); R(s, (60, 40, 90), 0, 6, 32, 2)
    for cx in (7, 25):                                               # two decks
        ellipse_fill(s, (40, 40, 46), cx, 4, 5, 2); ellipse_fill(s, (20, 20, 22), cx, 4, 3, 1)
    R(s, (60, 64, 72), 13, 1, 6, 4); R(s, (90, 200, 255), 14, 2, 4, 2)   # laptop
    for x in range(3, 30, 3): P(s, (255, 80, 200), x, 10)            # LED strip
    return up(add_outline(s)).convert_alpha()


def speaker():
    s = _prop(12, 24)
    R(s, (20, 20, 24), 0, 0, 12, 24); R(s, (44, 44, 50), 0, 0, 12, 1)
    for cy, r in ((6, 3), (16, 4)):
        circle(s, (50, 50, 56), 6, cy, r); circle(s, (14, 14, 16), 6, cy, r - 1)
    return up(add_outline(s)).convert_alpha()



def stair_wall(side="left"):
    """A low dark-stone wall down the side of the stairwell (drawn on the ground, a tile tall)."""
    s = canvas(4, L)
    stone, top, dark = (78, 72, 68), (118, 110, 104), (46, 42, 40)
    R(s, stone, 0, 0, 4, L)
    R(s, top if side == "left" else dark, 0, 0, 1, L)
    R(s, dark if side == "left" else top, 3, 0, 1, L)
    for y in range(3, L, 5):
        R(s, dark, 0, y, 4, 1)
    return up(s).convert_alpha()


def omg_side(rows=13, door_row=7):
    """OMG's side wall, facing the pavement: the entrance with its canopy, and a neon blade sign
    sticking out over the pavement. A narrow strip drawn down the building's left edge."""
    w, h = 16, rows * L
    s = canvas(w, h)
    wall, trim, purple = (32, 26, 40), (60, 44, 76), (110, 50, 150)
    R(s, wall, 10, 0, 6, h)                                          # the wall, end-on
    R(s, trim, 10, 0, 1, h)
    for y in range(4, h, 6): R(s, shade(wall, 1.3), 11, y, 5, 1)
    # entrance at door_row: lit doorway with a canopy over it
    dy = door_row * L
    R(s, (255, 210, 240), 11, dy + 2, 4, L - 3)                      # light spilling out of the door
    R(s, (60, 54, 70), 12, dy + 3, 3, L - 5)
    R(s, purple, 2, dy - 2, 14, 4); R(s, shade(purple, 1.4), 2, dy - 2, 14, 1)   # canopy over the pavement
    for x in range(3, 15, 3): P(s, (255, 230, 140), x, dy + 1)
    R(s, (230, 30, 60), 4, dy + 4, 1, 8); R(s, (230, 30, 60), 4, dy + 14, 1, 2)  # rope post
    # neon blade sign: O / M / G stacked, glowing pink
    top = (door_row - 4) * L
    R(s, (18, 14, 22), 1, top, 9, 30); R(s, (120, 230, 255), 1, top, 9, 1); R(s, (120, 230, 255), 1, top + 29, 9, 1)
    for i, ch in enumerate("OMG"):
        letter = canvas(5, 5)
        draw_text(letter, ch, 0 if ch == "M" else 1, 0, (255, 120, 220))
        glow = letter.copy(); glow.fill((255, 60, 180, 110), special_flags=pygame.BLEND_RGBA_MULT)
        s.blit(glow, (3, top + 3 + i * 9)); s.blit(letter, (3, top + 2 + i * 9))
    R(s, (60, 60, 66), 9, top + 4, 2, 1); R(s, (60, 60, 66), 9, top + 24, 2, 1)   # brackets to the wall
    return up(s).convert_alpha()


# ============================================================== Frogmore Street frontages (walls facing the road)
def _tags(s, rng, x0, y0, w, h, n=6):
    """Made-up graffiti tags: coloured squiggles and blobby letters."""
    cols = [(230, 60, 120), (60, 170, 240), (250, 210, 60), (90, 210, 120), (240, 240, 240), (240, 120, 40), (170, 90, 230)]
    for _ in range(n):
        c = rng.choice(cols)
        x, y = rng.randrange(x0, x0 + max(1, w - 6)), rng.randrange(y0, y0 + max(1, h - 4))
        ln = rng.randrange(4, 10)
        for i in range(ln):
            yy = y + round(1.5 * math.sin(i * 1.1 + x))
            if x0 <= x + i < x0 + w: P(s, c, x + i, yy)
            if rng.random() < 0.4 and x0 <= x + i < x0 + w: P(s, shade(c, 0.6), x + i, yy + 1)


def side_strip(kind, rows, doors=(), facing="east", seed=0, sign=None):
    """The front of a building that faces across the road (seen end-on from above): a narrow strip down
    the building's edge with its doors, windows, awnings and signs sticking out over the pavement.
    facing='east' = building on the left of the road; 'west' = building on the right (mirrored)."""
    w, h = 14, rows * L
    s = canvas(w, h)
    rng = random.Random(seed * 17 + len(kind))
    if kind == "brick":
        brick, mortar = (150, 70, 52), (110, 52, 40)
        R(s, brick, 0, 0, 6, h)
        for y in range(1, h, 3): R(s, mortar, 0, y, 6, 1)
        R(s, shade(brick, 1.2), 5, 0, 1, h)
        for r in range(rows):                                     # sash windows end-on, a downpipe
            if r not in doors:
                R(s, (236, 232, 222), 5, r * L + 4, 2, 8); R(s, (60, 72, 90), 6, r * L + 5, 1, 6)
        R(s, (40, 40, 44), 2, 0, 1, h)
        for r in doors:
            R(s, (30, 70, 50) if r % 2 else (30, 30, 36), 4, r * L + 4, 4, 11); P(s, (220, 190, 90), 7, r * L + 10)
            R(s, (180, 176, 166), 5, r * L + 15, 5, 1)            # front step
    elif kind == "restaurant":
        green, cream, red = (34, 92, 60), (236, 230, 210), (190, 40, 56)
        R(s, green, 0, 0, 6, h); R(s, shade(green, 1.3), 5, 0, 1, h)
        for r in range(rows):                                     # lit windows, red pilasters, awnings, planters
            y = r * L
            R(s, (255, 220, 150), 5, y + 4, 2, 9); R(s, red, 5, y, 2, 3)
            R(s, cream, 2, y + 1, 10, 3)
            for x in range(2, 12, 2): P(s, shade(cream, 0.8), x, y + 4)
            for x in (3, 7, 10): circle(s, (70, 150, 70), x, y, 1)
        for r in doors:
            R(s, (60, 40, 30), 5, r * L + 5, 2, 10)
        if sign:                                                  # tall blade sign with the name down it
            R(s, green, 7, 6, 6, 6 * len(sign) + 2); R(s, red, 7, 6, 6, 1); R(s, red, 7, 6 * len(sign) + 7, 6, 1)
            for i, ch in enumerate(sign):
                letter = canvas(5, 5); draw_text(letter, ch, 1 if ch not in "MW" else 0, 0, cream)
                s.blit(letter, (8, 8 + i * 6))
        for r in range(rows):                                     # chalkboards on the pavement
            if r % 2 == 1:
                R(s, (40, 40, 44), 11, r * L + 9, 3, 5); P(s, (230, 230, 230), 12, r * L + 10)
    elif kind == "graffiti":
        black, cream = (30, 30, 34), (204, 196, 176)
        R(s, cream, 0, 0, 6, h)
        R(s, black, 0, h // 3, 6, h - h // 3)
        _tags(s, rng, 0, h // 3, 6, h - h // 3, n=rows * 3)
        R(s, (200, 200, 196), 3, 0, 1, h)                          # drainpipe
        R(s, shade(cream, 1.1), 5, 0, 1, h // 3)
    elif kind == "stone":                                          # Pennant rubble stone, moss in the joints
        base = (96, 92, 88)
        R(s, base, 0, 0, 6, h)
        for y in range(0, h, 3):
            off = (y // 3) % 2 * 2
            for x in range(off, 6, 4): P(s, shade(base, 0.7), x, y)
            R(s, shade(base, 0.82), 0, y + 2, 6, 1)
        for _ in range(rows * 3):
            P(s, (80, 120, 60), rng.randrange(6), rng.randrange(h))
        R(s, shade(base, 1.25), 5, 0, 1, h)
        for r in doors:                                            # the green door in the wall
            dy = r * L
            R(s, (24, 60, 44), 3, dy + 1, 5, 14); R(s, (40, 96, 70), 4, dy + 2, 4, 12)
            R(s, (180, 210, 190), 5, dy + 4, 2, 3); P(s, (220, 190, 90), 7, dy + 9)
            R(s, (150, 146, 136), 3, dy + 15, 6, 1)
    elif kind == "omg":
        pink, pink_d, black = (220, 60, 140), (170, 40, 106), (24, 22, 28)
        R(s, pink, 0, 0, 6, h); R(s, pink_d, 0, 0, 1, h); R(s, shade(pink, 1.25), 5, 0, 1, h)
        for y in range(5, h, 8): R(s, pink_d, 0, y, 6, 1)
        for r in doors:
            dy = r * L
            R(s, black, 4, dy + 2, 3, L - 2); R(s, (255, 210, 240), 5, dy + 3, 1, L - 5)
            R(s, black, 0, dy - 2, 14, 4); R(s, pink, 0, dy - 2, 14, 1)          # canopy
            for x in range(1, 13, 3): P(s, (255, 230, 140), x, dy + 1)
            R(s, (230, 30, 60), 12, dy + 4, 1, 9)                                  # rope post
        top = max(0, (doors[0] if doors else 2) * L - 40)
        R(s, black, 6, top, 8, 30); R(s, (120, 230, 255), 6, top, 8, 1); R(s, (120, 230, 255), 6, top + 29, 8, 1)
        for i, ch in enumerate("OMG"):
            letter = canvas(5, 5)
            draw_text(letter, ch, 0 if ch == "M" else 1, 0, (255, 120, 220))
            glow = letter.copy(); glow.fill((255, 60, 180, 110), special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(glow, (8, top + 3 + i * 9)); s.blit(letter, (8, top + 2 + i * 9))
    img = up(s).convert_alpha()
    return pygame.transform.flip(img, True, False) if facing == "west" else img


def wheelie_bin(colour=(40, 44, 40), lid=None):
    s = _prop(12, 16)
    lid = lid or shade(colour, 1.2)
    R(s, colour, 1, 4, 10, 11); R(s, shade(colour, 0.75), 9, 4, 2, 11)
    R(s, lid, 0, 1, 12, 3); R(s, shade(lid, 1.2), 0, 1, 12, 1)
    R(s, (24, 24, 26), 1, 14, 2, 2); R(s, (24, 24, 26), 9, 14, 2, 2)
    R(s, (230, 230, 230), 3, 7, 3, 2)                               # sticker
    return up(add_outline(s)).convert_alpha()


def stairs_tile_v(k=1.0, v=0):
    """Steps climbing towards the left: each tread is a lit strip, each riser a dark one."""
    s = canvas(L, L)
    stone = shade((122, 114, 106), k)
    rng = random.Random(950 + v)
    for i, x in enumerate(range(0, L, 5)):
        R(s, shade(stone, 1.12), x, 0, 3, L)                       # tread (lit)
        R(s, shade(stone, 0.95), x + 3, 0, 1, L)
        R(s, shade(stone, 0.6), x + 4, 0, 1, L)                    # riser (shadow)
    speckle(s, rng, [shade(stone, 0.9), (70, 104, 56)], 0.05)
    R(s, shade(stone, 0.55), 0, 0, L, 1); R(s, shade(stone, 0.55), 0, L - 1, L, 1)
    return up(s).convert()



def greyed(img, k=0.7):
    """The same picture washed out to grey - for things on the other level (you can see them, not reach them)."""
    g = pygame.transform.grayscale(img).convert_alpha()
    g.fill((214, 214, 222, 255), special_flags=pygame.BLEND_RGBA_MULT)
    out = img.copy().convert_alpha()
    g.set_alpha(int(255 * k))
    out.blit(g, (0, 0))
    return out


# ============================================================== the harbour: flowing water, pontoons, boats
WATER_FRAMES = 8
_WATER_PAL = {
    "clear": [(44, 104, 168), (56, 124, 186), (70, 142, 200), (98, 170, 220), (170, 214, 240)],
    "harbour": [(30, 72, 84), (38, 88, 100), (48, 104, 114), (70, 128, 134), (150, 196, 196)],
}


WATER_SPAN = 4                     # the water pattern covers 4 x 4 tiles before it repeats


def water_frames(kind="clear"):
    """Moving water, 8 frames, each a 4 x 4 tile sheet (so the pattern doesn't look like a grid).
    Slow swells roll across it and little ripples catch the light, grow and fade as the frames go round."""
    pal = _WATER_PAL.get(kind, _WATER_PAL["clear"])
    S = L * WATER_SPAN
    tau = math.tau
    rng = random.Random(4242 if kind == "harbour" else 4343)
    ripples = [(rng.randrange(S), rng.randrange(S), rng.randrange(WATER_FRAMES), rng.choice((2, 3, 3, 4))) for _ in range(46)]
    out = []
    for f in range(WATER_FRAMES):
        ph = f / WATER_FRAMES
        s = canvas(S, S)
        for y in range(S):
            for x in range(S):
                v = (math.sin(tau * ((x + 2 * y) / S - ph)) * 0.6 +
                     math.sin(tau * ((3 * x - y) / S + ph)) * 0.4 +
                     math.sin(tau * ((x + 5 * y) / S * 1 - 2 * ph)) * 0.25)
                c = pal[0] if v < -0.7 else pal[1] if v < 0.15 else pal[2] if v < 0.85 else pal[3]
                s.set_at((x, y), c)
        for rx, ry, off, ln in ripples:                              # a ripple: grows, drifts right, fades
            p = (f + off) % WATER_FRAMES
            if p >= 6:
                continue
            w = (1, 2, ln, ln, 2, 1)[p]
            col = pal[4] if p in (2, 3) else pal[3]
            for k in range(w):
                s.set_at(((rx + p + k) % S, ry), col)
            if p in (2, 3) and ln >= 3:
                s.set_at(((rx + p + 1) % S, (ry + 1) % S), shade(pal[2], 1.05))
        out.append(up(s).convert())
    return out


def water_edge(mask, frame):
    """Foam lapping against the quay on the sides where the water meets land (mask: 1 top, 2 right, 4 bottom, 8 left)."""
    s = canvas(L, L)
    foam, foam2, wall = (226, 238, 236), (176, 206, 206), (92, 86, 80)
    lap = (0, 1, 1, 2, 1, 1, 0, 0)[frame % 8]
    for side in (1, 2, 4, 8):
        if not mask & side:
            continue
        for i in range(L):
            wob = lap + ((i + frame) % 4 == 0)
            if side == 1:
                R(s, wall, i, 0, 1, 2); R(s, foam, i, 2, 1, wob); P(s, foam2, i, 2 + wob)
            elif side == 4:
                R(s, foam, i, L - 1 - wob, 1, wob); P(s, foam2, i, L - 2 - wob)
            elif side == 8:
                R(s, foam, 0, i, 1 + wob, 1); P(s, foam2, 1 + wob, i)
            else:
                R(s, foam, L - 1 - wob, i, 1 + wob, 1); P(s, foam2, L - 2 - wob, i)
    return up(s).convert_alpha()


def pontoon_tile(v=0):
    """Floating pontoon: grey-brown boards with dark gaps and a metal edge strip."""
    rng = random.Random(8800 + v)
    s = canvas(L, L)
    base = (150, 132, 108)
    for i, y in enumerate(range(0, L, 4)):
        R(s, shade(base, rng.uniform(0.9, 1.06)), 0, y, L, 3)
        R(s, (40, 46, 50), 0, y + 3, L, 1)                           # gap between boards
        for x in range(rng.randrange(2, 6), L, rng.randrange(5, 9)):
            P(s, shade(base, 0.8), x, y + 1)
    for y in range(1, L, 8):                                          # bolts
        P(s, (190, 190, 196), 1, y); P(s, (190, 190, 196), L - 2, y)
    return up(s).convert()


BOAT_COLOURS = [(196, 40, 44), (30, 90, 70), (36, 60, 120), (240, 236, 226), (230, 180, 40), (40, 40, 48)]


def boat(kind, colour, frame=0, flip=False):
    """A moored boat, side-on to the camera (bow pointing right), bobbing on the water. 4 frames."""
    bob = (0, 1, 1, 0)[frame % 4]
    hull_d = shade(colour, 0.7)
    if kind == "narrow":                                             # narrowboat: long, painted, with a cabin
        W, H = 44, 16
        s = canvas(W, H + 2)
        y0 = 6 + bob
        R(s, OUTLINE, 0, y0 + 3, W, 6); R(s, colour, 1, y0 + 4, W - 2, 3); R(s, hull_d, 1, y0 + 7, W - 2, 1)
        R(s, (240, 210, 90), 1, y0 + 4, W - 2, 1)                     # coach line
        R(s, OUTLINE, 6, y0 - 3, W - 14, 7); R(s, (36, 80, 60), 7, y0 - 2, W - 16, 5)
        for wx in range(10, W - 10, 6):
            R(s, (200, 220, 230), wx, y0 - 1, 3, 2)
        R(s, (90, 60, 40), W - 6, y0 - 4, 2, 2)                       # chimney
        P(s, (150, 150, 156), W - 6, y0 - 5)
    elif kind == "yacht":                                            # small sailing boat with its sail furled
        W, H = 30, 28
        s = canvas(W, H + 2)
        y0 = 18 + bob
        pygame.draw.polygon(s, OUTLINE, [(0, y0), (W - 1, y0), (W - 5, y0 + 7), (4, y0 + 7)])
        pygame.draw.polygon(s, colour, [(1, y0 + 1), (W - 2, y0 + 1), (W - 6, y0 + 6), (5, y0 + 6)])
        R(s, (240, 240, 244), 2, y0, W - 4, 1)
        R(s, OUTLINE, 9, y0 - 4, 11, 5); R(s, (232, 232, 236), 10, y0 - 3, 9, 3); R(s, (120, 170, 210), 12, y0 - 3, 5, 1)
        R(s, (200, 200, 206), 14, 0 + bob, 1, y0)                     # mast
        R(s, (40, 70, 140), 9, y0 - 6, 10, 2)                         # furled sail on the boom
    elif kind == "ferry":                                            # the yellow-and-blue harbour ferry
        W, H = 40, 22
        s = canvas(W, H + 2)
        y0 = 12 + bob
        pygame.draw.polygon(s, OUTLINE, [(0, y0), (W - 1, y0), (W - 6, y0 + 8), (3, y0 + 8)])
        pygame.draw.polygon(s, (250, 200, 40), [(1, y0 + 1), (W - 2, y0 + 1), (W - 7, y0 + 7), (4, y0 + 7)])
        R(s, (30, 70, 140), 3, y0 + 5, W - 10, 2)
        R(s, OUTLINE, 6, y0 - 9, 26, 10); R(s, (240, 240, 236), 7, y0 - 8, 24, 8)
        for wx in range(8, 30, 5):
            R(s, (120, 170, 210), wx, y0 - 6, 3, 3)
        R(s, (30, 70, 140), 6, y0 - 10, 26, 2)
    else:                                                            # little motor launch
        W, H = 24, 14
        s = canvas(W, H + 2)
        y0 = 8 + bob
        pygame.draw.polygon(s, OUTLINE, [(0, y0), (W - 1, y0 + 1), (W - 4, y0 + 6), (2, y0 + 6)])
        pygame.draw.polygon(s, colour, [(1, y0 + 1), (W - 2, y0 + 2), (W - 5, y0 + 5), (3, y0 + 5)])
        R(s, OUTLINE, 5, y0 - 4, 8, 5); R(s, (220, 220, 224), 6, y0 - 3, 6, 3); R(s, (120, 170, 210), 7, y0 - 3, 3, 1)
    # ripples round the waterline
    rip = (170, 210, 214)
    wl = s.get_height() - 3
    for x in range(-2 + frame % 3, s.get_width(), 6):
        R(s, rip, max(0, x), wl + (frame + x) % 2, 3, 1)
    img = up(s).convert_alpha()
    return pygame.transform.flip(img, True, False) if flip else img


def arcade_carpet(v=0):
    """That arcade carpet: dark blue with neon squiggles and stars."""
    rng = random.Random(9100 + v)
    s = canvas(L, L)
    s.fill((22, 20, 52))
    cols = [(240, 60, 180), (60, 220, 240), (250, 220, 60), (120, 240, 120)]
    for _ in range(3):
        c = rng.choice(cols); x, y = rng.randrange(1, L - 4), rng.randrange(1, L - 3)
        for k in range(4):
            P(s, c, x + k, y + (k % 2))
    for _ in range(2):
        c = rng.choice(cols); x, y = rng.randrange(1, L - 2), rng.randrange(1, L - 2)
        P(s, c, x, y); P(s, c, x + 1, y); P(s, c, x, y + 1)
    speckle(s, rng, [(36, 32, 76)], 0.12)
    return up(s).convert()


# ---- building fronts for the harbourside
def _arcade_front(bw, H, name="BRISTOL ARCADE"):
    """The old aquarium, now an arcade: glass front, the cabinets glowing inside, a big neon sign."""
    W = bw * L
    s = canvas(W, H)
    R(s, (40, 34, 58), 0, 0, W, H)                                   # dark cladding
    R(s, (28, 24, 42), 0, 0, W, 14)                                  # sign band
    # glass curtain wall
    gl = (54, 70, 104)
    R(s, OUTLINE, 3, 16, W - 6, H - 17)
    R(s, gl, 4, 17, W - 8, H - 18)
    for x in range(4, W - 4, 8):
        R(s, (90, 96, 116), x, 17, 1, H - 18)                        # mullions
    R(s, (90, 96, 116), 4, 30, W - 8, 1)
    rng = random.Random(bw * 13)
    cols = [(240, 60, 180), (60, 220, 240), (250, 220, 60), (120, 240, 120), (250, 120, 50)]
    for x in range(8, W - 10, 11):                                   # the machines inside, screens lit
        c = rng.choice(cols)
        R(s, (20, 18, 30), x, H - 14, 6, 13); R(s, c, x + 1, H - 12, 4, 3); R(s, shade(c, 0.6), x + 1, H - 6, 4, 1)
    # doors in the middle
    dx = (bw // 2) * L + 2
    R(s, OUTLINE, dx - 1, H - 15, 14, 15); R(s, (150, 200, 230), dx, H - 14, 12, 14)
    R(s, (60, 70, 90), dx + 5, H - 14, 2, 14); R(s, (220, 220, 230), dx + 3, H - 8, 1, 3); R(s, (220, 220, 230), dx + 8, H - 8, 1, 3)
    # neon sign
    tw = text_width(name)
    sc = 2 if tw * 2 + 8 < W else 1
    sign = canvas(tw + 2, 7)
    draw_text(sign, name, 0, 0, (255, 90, 200))
    sign = pygame.transform.scale(sign, (sign.get_width() * sc, sign.get_height() * sc))
    sx = (W - sign.get_width()) // 2
    glow = canvas(sign.get_width() + 4, sign.get_height() + 4)
    glow.fill((255, 90, 200, 60))
    s.blit(glow, (sx - 2, 1))
    s.blit(sign, (sx, 3))
    for x in range(2, W - 2, 4):                                     # chaser bulbs along the top
        P(s, (250, 230, 120) if (x // 4) % 2 else (90, 230, 250), x, 0)
    return s


def _warehouse_front(bw, H, seed):
    """Red-brick transit sheds (the Watershed): tall round-arched windows, cream bands."""
    W = bw * L
    s = canvas(W, H)
    brick, mortar, cream = (150, 66, 50), (120, 52, 40), (226, 206, 170)
    R(s, brick, 0, 0, W, H)
    rng = random.Random(seed)
    for y in range(0, H, 3):
        R(s, mortar, 0, y, W, 1)
        for x in range((y // 3 % 2) * 3, W, 6):
            P(s, mortar, x, y + 1)
    speckle(s, rng, [shade(brick, 0.9), shade(brick, 1.08)], 0.08)
    R(s, cream, 0, 3, W, 2); R(s, cream, 0, H - 14, W, 1)
    for x in range(3, W - 8, 12):                                    # round-arched windows
        R(s, OUTLINE, x, 9, 8, 22); R(s, (60, 80, 100), x + 1, 10, 6, 20)
        circle(s, OUTLINE, x + 4, 11, 4); circle(s, (60, 80, 100), x + 4, 11, 3)
        R(s, (60, 80, 100), x + 1, 11, 6, 3)
        R(s, cream, x - 1, 31, 10, 1)
        R(s, (110, 130, 150), x + 4, 10, 1, 20); P(s, (150, 190, 220), x + 2, 13)
    for x in range(8, W - 10, 36):                                   # doors on the quay
        R(s, OUTLINE, x, H - 12, 12, 12); R(s, (60, 70, 74), x + 1, H - 11, 10, 11); R(s, (90, 100, 104), x + 6, H - 11, 1, 11)
    return s


def _shed_front(bw, H, seed, sign=None):
    """A long harbourside shed turned into restaurants: steel frame, big windows, warm light inside,
    and (if it has one) its name in big lit letters over the windows."""
    W = bw * L
    s = canvas(W, H)
    steel, glass, warm = (70, 84, 96), (60, 78, 92), (250, 196, 110)
    R(s, steel, 0, 0, W, H)
    R(s, (150, 160, 168), 0, 0, W, 3)
    top = 6 if not sign else 15
    R(s, OUTLINE, 2, top, W - 4, H - top - 1); R(s, glass, 3, top + 1, W - 6, H - top - 2)
    rng = random.Random(seed)
    for x in range(3, W - 3, 7):
        R(s, steel, x, top + 1, 1, H - top - 2)
        if rng.random() < 0.7:
            R(s, warm, x + 2, H - 10, 3, 3)                         # lamps / tables inside
    R(s, steel, 3, min(H - 6, top + 12), W - 6, 1)
    if sign:                                                        # the way in, in the middle
        dx = (bw // 2) * L + 2
        R(s, OUTLINE, dx - 1, H - 15, 14, 15); R(s, (250, 210, 140), dx, H - 14, 12, 14)
        R(s, (90, 70, 50), dx + 5, H - 14, 2, 14); R(s, (60, 50, 40), dx + 3, H - 8, 1, 3); R(s, (60, 50, 40), dx + 8, H - 8, 1, 3)
        R(s, (36, 30, 26), 2, 4, W - 4, 10)                         # the sign board
        tw = text_width(sign)
        sc = 2 if tw * 2 + 8 < W else 1
        img = canvas(tw + 2, 7)
        draw_text(img, sign, 0, 0, (255, 206, 90))
        img = pygame.transform.scale(img, (img.get_width() * sc, img.get_height() * sc))
        s.blit(img, ((W - img.get_width()) // 2, 9 - img.get_height() // 2))
        for x in range(4, W - 4, 5):                                # bulbs round the board
            P(s, (255, 236, 160), x, 4); P(s, (255, 236, 160), x, 13)
    return s


STALL_AWNINGS = [(200, 52, 52), (46, 130, 80), (50, 96, 180), (226, 170, 40), (130, 70, 160), (220, 110, 40)]
STALL_GOODS = ["fruit", "bread", "flowers", "jars", "books", "hats", "cheese", "veg"]


def market_stall_layers(v=0):
    """The stall in two layers: (awning, poles and back) and (the table with its goods) - so the stallholder can
    stand between them."""
    full = market_stall(v)
    W, H = full.get_size()
    cut = 17 * PX                                                   # the top of the table
    back = full.copy()
    back.fill((0, 0, 0, 0), (PX * 2, cut, W - PX * 4, H - cut))     # keep the poles, drop the table
    front = pygame.Surface((W, H), pygame.SRCALPHA)
    front.blit(full, (PX * 2, cut), (PX * 2, cut, W - PX * 4, H - cut))
    return back, front


def market_stall(v=0):
    """A market stall, two tiles wide: striped awning on poles, a table with a cloth and the goods out on it."""
    rng = random.Random(v * 31 + 7)
    W, H = 30, 30
    s = canvas(W, H)
    aw = STALL_AWNINGS[v % len(STALL_AWNINGS)]
    goods = STALL_GOODS[(v * 3 + 1) % len(STALL_GOODS)]
    pole = (70, 56, 44)
    R(s, (58, 48, 40), 2, 9, W - 4, 11)                               # the back of the stall, in the shade
    R(s, shade((58, 48, 40), 1.2), 2, 9, W - 4, 1)
    for x in (1, W - 3):
        R(s, OUTLINE, x, 6, 2, H - 6); R(s, pole, x, 7, 1, H - 8)  # poles
    # awning: stripes, with a scalloped edge
    R(s, OUTLINE, 0, 1, W, 9)
    for x in range(1, W - 1):
        c = aw if (x // 4) % 2 == 0 else (244, 240, 230)
        R(s, c, x, 2, 1, 6)
        R(s, shade(c, 1.12), x, 2, 1, 1)
        if x % 4 in (1, 2):
            P(s, c, x, 8); P(s, OUTLINE, x, 9)
        else:
            P(s, OUTLINE, x, 8)
    R(s, OUTLINE, 1, 0, W - 2, 1)
    # the table, with a cloth hanging down the front
    cloth = shade(aw, 0.7) if goods != "flowers" else (230, 226, 210)
    R(s, OUTLINE, 2, 18, W - 4, 11)
    R(s, cloth, 3, 19, W - 6, 9)
    R(s, shade(cloth, 1.15), 3, 19, W - 6, 1)
    for x in range(5, W - 5, 4):
        P(s, shade(cloth, 0.85), x, 24)
    # what's on the table
    cols = {"fruit": [(220, 40, 40), (250, 160, 30), (120, 190, 50), (240, 220, 60)],
            "bread": [(196, 140, 70), (220, 170, 100), (170, 110, 50)],
            "flowers": [(240, 80, 140), (250, 220, 70), (160, 90, 220), (250, 250, 250)],
            "jars": [(200, 120, 40), (150, 40, 50), (230, 190, 60)],
            "books": [(60, 90, 160), (160, 50, 50), (60, 130, 80), (220, 200, 150)],
            "hats": [(70, 70, 80), (180, 150, 100), (150, 60, 60)],
            "cheese": [(246, 214, 90), (250, 236, 170), (230, 180, 60)],
            "veg": [(240, 130, 40), (90, 160, 60), (150, 60, 120), (230, 230, 200)]}[goods]
    for x in range(4, W - 5, 3):
        c = rng.choice(cols)
        h = 2 if goods in ("fruit", "veg", "cheese") else 3
        R(s, OUTLINE, x, 17 - h, 3, h + 1); R(s, c, x, 17 - h + 1, 2, h)
        P(s, shade(c, 1.3), x, 17 - h + 1)
        if goods == "flowers":
            P(s, (60, 140, 60), x + 1, 17)
    R(s, (120, 96, 70), 3, 17, W - 6, 1)                                # table top edge
    return up(s)


# ============================================================== the harbourside market (back view) and the plaza
def market_stall_back(v=0):
    """A market stall seen from behind (it faces up the screen, across the aisle): the back of the awning
    sloping down to us, the back cloth, the poles and the crates the stallholder keeps their stock in."""
    rng = random.Random(v * 17 + 3)
    W, H = 30, 24
    s = canvas(W, H)
    aw = STALL_AWNINGS[v % len(STALL_AWNINGS)]
    pole = (70, 56, 44)
    for x in (1, W - 3):
        R(s, OUTLINE, x, 4, 2, H - 4); R(s, pole, x, 5, 1, H - 6)
    # the awning from behind: stripes running away from us, shading towards the near edge
    R(s, OUTLINE, 0, 0, W, 10)
    for x in range(1, W - 1):
        c = aw if (x // 4) % 2 == 0 else (244, 240, 230)
        for y in range(1, 9):
            P(s, shade(c, 1.06 - y * 0.03), x, y)
    R(s, OUTLINE, 0, 9, W, 1)
    # the back cloth hanging down to the ground
    back = shade(aw, 0.55)
    R(s, OUTLINE, 2, 10, W - 4, H - 11)
    R(s, back, 3, 10, W - 6, H - 12)
    for x in range(5, W - 5, 5):
        R(s, shade(back, 0.85), x, 11, 1, H - 13)
    # crates of stock on the ground behind
    for x in (4, 13, 21):
        c = rng.choice([(150, 110, 70), (120, 90, 60), (160, 130, 90)])
        R(s, OUTLINE, x, H - 7, 7, 6); R(s, c, x + 1, H - 6, 5, 4); R(s, shade(c, 0.8), x + 1, H - 4, 5, 1)
        R(s, rng.choice([(220, 60, 50), (240, 170, 40), (110, 180, 60)]), x + 1, H - 6, 5, 1)
    return up(s)


def setts_tile(v=0):
    """Granite setts laid in fans: the decorative ring round the plaza."""
    rng = random.Random(900 + v)
    s = canvas(L, L)
    base = (128, 132, 140)
    R(s, shade(base, 0.7), 0, 0, L, L)
    for row in range(4):
        off = (row % 2) * 2
        for col in range(-1, 5):
            x, y = col * 4 + off, row * 4
            c = shade(base, rng.uniform(0.88, 1.12))
            R(s, c, x, y, 3, 3)
            P(s, shade(c, 1.15), x, y)
    return up(s).convert()


def compass_rose(r=3):
    """The plaza's centrepiece set into the paving: a brass-edged compass rose (r = radius in tiles)."""
    n = r * 2 * L
    s = canvas(n, n)
    c = n / 2 - 0.5
    rr = n / 2 - 1
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - c, y - c)
            if d <= rr:
                col = (226, 220, 204) if d < rr - 3 else ((196, 160, 70) if d > rr - 1.5 else (60, 66, 80))
                if rr - 9 < d < rr - 7:
                    col = (196, 160, 70)
                s.set_at((x, y), col)
    # the points of the star
    def tri(a, length, width, col):
        ax, ay = math.cos(a), math.sin(a)
        px_, py_ = -ay, ax
        pts = [(c + ax * length, c + ay * length), (c + px_ * width, c + py_ * width), (c - px_ * width, c - py_ * width)]
        pygame.draw.polygon(s, col, pts)
        pygame.draw.polygon(s, shade(col, 0.7), [pts[0], (c, c), pts[1]])
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        tri(a, rr - 10, 3, (90, 100, 120))
    for k in range(4):
        a = k * math.pi / 2 - math.pi / 2
        tri(a, rr - 4, 5, (190, 70, 60) if k == 0 else (60, 70, 90))
    circle(s, (196, 160, 70), int(c), int(c), 3); circle(s, (240, 220, 150), int(c), int(c), 1)
    # N at the top
    draw_text(s, "N", int(c) - 2, 2, (190, 70, 60))
    return up(s).convert_alpha()


# ============================================================== inside Za Za Bazaar
ZAZA_STATIONS = [("DESSERTS", (220, 90, 150)), ("SALADS", (110, 180, 70)), ("FAR EAST", (220, 60, 50)),
                 ("TEX MEX", (240, 150, 40)), ("EUROPEAN", (70, 130, 210)), ("INDIAN", (230, 180, 40))]
_STATION_FOOD = {
    "DESSERTS": [(250, 240, 230), (120, 70, 40), (240, 120, 160), (250, 220, 120)],
    "SALADS": [(110, 180, 60), (220, 60, 50), (240, 230, 200), (250, 200, 60)],
    "FAR EAST": [(240, 230, 210), (200, 90, 40), (90, 150, 60), (250, 250, 250)],
    "TEX MEX": [(200, 70, 40), (240, 200, 90), (90, 150, 60), (150, 90, 50)],
    "EUROPEAN": [(240, 200, 120), (200, 60, 40), (250, 240, 220), (120, 160, 70)],
    "INDIAN": [(230, 150, 40), (200, 80, 30), (250, 240, 220), (150, 90, 40)],
}


def zaza_station(name, colour):
    """One of the open-kitchen food stations, four tiles wide: a sign hanging high on rods (white letters on
    black, as on the map they give you at the door), heat lamps on long cords, then the steel serving counter
    with the hot trays under a sneeze guard and a coloured stripe along the front. The chef stands in the gap
    between the sign and the counter."""
    W, H = 4 * L, 58
    s = canvas(W, H)
    steel = (176, 182, 190)
    R(s, (60, 60, 66), 10, 0, 1, 3); R(s, (60, 60, 66), W - 11, 0, 1, 3)
    R(s, OUTLINE, 4, 2, W - 8, 11); R(s, (24, 24, 28), 5, 3, W - 10, 9)
    tw = text_width(name)
    draw_text(s, name, (W - tw) // 2, 4, (240, 240, 240))
    R(s, colour, 5, 11, W - 10, 1)
    for x in range(8, W - 8, 12):                                   # heat lamps on cords
        R(s, (40, 40, 44), x + 2, 13, 1, 16)
        R(s, OUTLINE, x, 29, 6, 3); R(s, (90, 90, 96), x + 1, 29, 4, 2); R(s, (255, 170, 80), x + 1, 31, 4, 1)
    R(s, (200, 230, 240), 2, 37, W - 4, 1)                          # sneeze guard glass
    R(s, (60, 66, 76), 2, 37, 1, 4); R(s, (60, 66, 76), W - 3, 37, 1, 4)
    R(s, OUTLINE, 0, 40, W, H - 40)
    R(s, steel, 1, 41, W - 2, 3)                                    # the top, where the trays sit
    food = _STATION_FOOD.get(name, [(200, 150, 90)])
    for i, x in enumerate(range(3, W - 8, 8)):
        R(s, OUTLINE, x, 40, 7, 4); R(s, (200, 204, 210), x + 1, 41, 5, 2)
        R(s, food[i % len(food)], x + 1, 41, 5, 1); P(s, shade(food[i % len(food)], 1.25), x + 2, 41)
    R(s, shade(steel, 0.85), 1, 44, W - 2, H - 45)                  # the brushed-steel front
    for x in range(3, W - 2, 6):
        R(s, shade(steel, 0.78), x, 45, 1, H - 47)
    R(s, colour, 1, 48, W - 2, 3); R(s, shade(colour, 1.2), 1, 48, W - 2, 1)
    R(s, (60, 60, 66), 1, H - 2, W - 2, 1)
    R(s, OUTLINE, W - 7, 36, 5, 5); R(s, (244, 244, 244), W - 6, 37, 3, 3); R(s, (210, 210, 216), W - 6, 39, 3, 1)   # plates
    return up(s).convert_alpha()


def zaza_bar(end=None, v=0):
    """A tile of the long bar: copper top, dark panelled front lit along the bottom; end = 'l'/'r'."""
    s = canvas(L, 22)
    copper, wood = (190, 110, 60), (60, 40, 34)
    R(s, OUTLINE, 0, 4, L, 18)
    R(s, copper, 0, 5, L, 3); R(s, shade(copper, 1.25), 0, 5, L, 1)
    R(s, wood, 0, 8, L, 13)
    R(s, shade(wood, 0.8), 0, 8, L, 1)
    for x in (3, 11):
        R(s, shade(wood, 1.2), x, 10, 3, 8); R(s, shade(wood, 0.8), x, 17, 3, 1)
    R(s, (255, 190, 110), 0, 19, L, 1)                              # the strip light under the lip
    if v % 3 == 0:                                                  # beer taps / glasses on the top
        R(s, (210, 210, 220), 6, 0, 1, 5); R(s, (40, 40, 44), 5, 0, 3, 2)
        R(s, (230, 160, 40), 11, 2, 2, 3)
    else:
        R(s, (220, 236, 240), 4, 2, 2, 3); R(s, (150, 40, 60), 10, 2, 2, 3)
    if end == "l": R(s, OUTLINE, 0, 4, 1, 18)
    if end == "r": R(s, OUTLINE, L - 1, 4, 1, 18)
    return up(s).convert_alpha()


def zaza_back_bar(v=0):
    """The shelves behind the bar, against the wall: rows of lit bottles from 'five continents'."""
    rng = random.Random(v * 11 + 5)
    s = canvas(L, 21)
    R(s, OUTLINE, 0, 0, L, 21); R(s, (40, 30, 30), 1, 1, L - 2, 19)
    for y in (9, 18):
        R(s, (150, 100, 60), 1, y, L - 2, 1)
        R(s, (255, 200, 120), 1, y + 1, L - 2, 1) if y == 18 else None
        x = 2
        while x < L - 3:
            c = rng.choice([(60, 140, 70), (150, 60, 40), (220, 200, 120), (90, 60, 140), (230, 230, 230), (180, 120, 40)])
            h = rng.choice([5, 6, 7])
            R(s, c, x, y - h, 2, h); P(s, shade(c, 1.4), x, y - h + 1); P(s, (40, 40, 40), x, y - h - 1)
            x += 3
    return up(s).convert_alpha()


def zaza_booth_back(v=0):
    """The back half of a booth: the tall buttoned backrest and the seat (drawn behind whoever's sitting in it)."""
    W = 2 * L
    s = canvas(W, 16)
    leather = [(150, 40, 44), (120, 70, 40), (60, 90, 80)][v % 3]
    R(s, OUTLINE, 0, 0, W, 16)
    R(s, leather, 1, 1, W - 2, 14)
    for y in (4, 9):
        for x in range(3 + (y % 2) * 2, W - 2, 5):
            P(s, shade(leather, 0.7), x, y)
    R(s, shade(leather, 1.25), 1, 1, W - 2, 1)
    R(s, shade(leather, 0.8), 1, 12, W - 2, 3)
    return up(s).convert_alpha()


def zaza_booth_front(v=0):
    """The front half of a booth: the table laid for dinner and the low near bench."""
    rng = random.Random(v * 7 + 1)
    W, H = 2 * L, 30
    s = canvas(W, H)
    leather = [(150, 40, 44), (120, 70, 40), (60, 90, 80)][v % 3]
    R(s, OUTLINE, 4, 13, W - 8, 8); R(s, (130, 90, 60), 5, 14, W - 10, 6); R(s, (160, 116, 80), 5, 14, W - 10, 1)
    for x in range(8, W - 10, 9):
        circle(s, (240, 240, 240), x + 2, 17, 2)
        P(s, rng.choice([(200, 80, 40), (110, 170, 60), (230, 180, 60), (200, 60, 50)]), x + 2, 17)
    R(s, (230, 236, 240), W // 2 - 1, 14, 2, 3)
    R(s, OUTLINE, 1, 21, W - 2, 8); R(s, leather, 2, 22, W - 4, 3); R(s, shade(leather, 0.7), 2, 25, W - 4, 3)
    return up(s).convert_alpha()


def zaza_booth(v=0):
    """A booth against the wall, two tiles wide: tall buttoned leather back, a table laid for dinner, the near
    bench low so you can see over it."""
    rng = random.Random(v * 7 + 1)
    W, H = 2 * L, 30
    s = canvas(W, H)
    leather = [(150, 40, 44), (120, 70, 40), (60, 90, 80)][v % 3]
    R(s, OUTLINE, 0, 0, W, 16)
    R(s, leather, 1, 1, W - 2, 14)
    for y in (4, 9):
        for x in range(3 + (y % 2) * 2, W - 2, 5):
            P(s, shade(leather, 0.7), x, y)
    R(s, shade(leather, 1.25), 1, 1, W - 2, 1)
    R(s, shade(leather, 0.8), 1, 12, W - 2, 3)                       # the seat
    # table
    R(s, OUTLINE, 4, 13, W - 8, 8); R(s, (130, 90, 60), 5, 14, W - 10, 6); R(s, (160, 116, 80), 5, 14, W - 10, 1)
    for x in range(8, W - 10, 9):
        circle(s, (240, 240, 240), x + 2, 17, 2)
        P(s, rng.choice([(200, 80, 40), (110, 170, 60), (230, 180, 60), (200, 60, 50)]), x + 2, 17)
    R(s, (230, 236, 240), W // 2 - 1, 14, 2, 3)                     # a glass
    # the near bench
    R(s, OUTLINE, 1, 21, W - 2, 8); R(s, leather, 2, 22, W - 4, 3); R(s, shade(leather, 0.7), 2, 25, W - 4, 3)
    return up(s).convert_alpha()


def zaza_chairs_back(v=0):
    """The two chairs on the far side of a table (drawn behind the people sitting on them)."""
    W = 26
    s = canvas(W, 10)
    chair = [(60, 60, 66), (150, 60, 40), (40, 90, 110)][v % 3]
    for x in (4, 15):
        R(s, OUTLINE, x, 0, 7, 10); R(s, chair, x + 1, 1, 5, 8); R(s, shade(chair, 1.25), x + 1, 1, 5, 1)
    return up(s).convert_alpha()


def zaza_table(v=0, back_chairs=True):
    """A table for four: two chairs behind it (we see their backs over the top), two in front, plates out."""
    rng = random.Random(v * 13 + 2)
    W, H = 26, 24
    s = canvas(W, H)
    chair = [(60, 60, 66), (150, 60, 40), (40, 90, 110)][v % 3]
    if back_chairs:
        for x in (4, 15):
            R(s, OUTLINE, x, 0, 7, 8); R(s, chair, x + 1, 1, 5, 6); R(s, shade(chair, 1.25), x + 1, 1, 5, 1)
    R(s, OUTLINE, 1, 6, W - 2, 10); R(s, (176, 136, 92), 2, 7, W - 4, 7); R(s, (200, 160, 114), 2, 7, W - 4, 1)
    R(s, (120, 86, 56), 2, 13, W - 4, 2)
    for x in (6, 17):
        circle(s, (244, 244, 244), x + 1, 10, 2)
        if rng.random() < 0.8:
            P(s, rng.choice([(200, 80, 40), (110, 170, 60), (230, 180, 60), (90, 60, 40)]), x + 1, 10)
    R(s, (220, 230, 236), 12, 8, 2, 3)
    for x in (4, 15):                                                # front chairs
        R(s, OUTLINE, x, 15, 7, 8); R(s, shade(chair, 0.8), x + 1, 16, 5, 3); R(s, chair, x + 1, 19, 5, 3)
    return up(s).convert_alpha()


def zaza_pillar(v=0):
    """A concrete pillar with a band of street art and fairy lights wound round it."""
    rng = random.Random(v * 3 + 9)
    W, H = 10, 52
    s = canvas(W, H)
    con = (150, 148, 144)
    R(s, OUTLINE, 0, 0, W, H); R(s, con, 1, 1, W - 2, H - 2)
    R(s, shade(con, 1.12), 1, 1, 2, H - 2); R(s, shade(con, 0.82), W - 3, 1, 2, H - 2)
    speckle(s, rng, [shade(con, 0.9), shade(con, 1.08)], 0.12, (1, 1, W - 2, H - 2))
    for y in range(26, 40):                                          # spray paint
        for x in range(1, W - 1):
            if rng.random() < 0.55:
                P(s, rng.choice([(240, 80, 150), (60, 200, 230), (250, 220, 60), (120, 230, 120)]), x, y)
    for y in range(4, H - 6, 5):                                     # fairy lights spiralling down
        P(s, (255, 236, 160), 2 + (y // 5) % (W - 4), y)
    return up(s).convert_alpha()


def string_lights(width_px, sag=10, seed=0):
    """A string of warm bulbs hanging between two pillars (width in screen px)."""
    w = max(4, width_px // PX)
    h = sag + 4
    s = canvas(w, h)
    pts = []
    for x in range(w):
        t = x / (w - 1)
        y = int(1 + sag * 4 * t * (1 - t))
        pts.append((x, y))
        P(s, (40, 36, 34), x, y)
    for i, (x, y) in enumerate(pts):
        if i % 5 == 2:
            P(s, (255, 232, 150), x, y + 1); P(s, (255, 250, 210), x, y + 2)
    return up(s).convert_alpha()


def zaza_drinks():
    """The drinks station: bottomless soft drinks, a steel unit with the dispensers and stacks of glasses."""
    W, H = 2 * L, 30
    s = canvas(W, H)
    steel = (176, 182, 190)
    R(s, OUTLINE, 0, 0, W, H); R(s, (40, 44, 52), 1, 1, W - 2, 14)
    cols = [(200, 30, 40), (40, 40, 44), (250, 200, 40), (60, 170, 70), (240, 120, 30), (60, 120, 200)]
    for i, x in enumerate(range(3, W - 4, 5)):
        R(s, cols[i % len(cols)], x, 3, 4, 5); R(s, (230, 230, 230), x + 1, 8, 2, 4)   # labels, nozzles
    R(s, OUTLINE, 0, 15, W, 1)
    R(s, steel, 1, 16, W - 2, 3)
    for x in range(3, W - 3, 4):
        R(s, (220, 236, 240), x, 13, 2, 3)                           # glasses
    R(s, shade(steel, 0.8), 1, 19, W - 2, H - 20)
    R(s, (30, 30, 34), 4, 22, W - 8, 4)
    draw_text(s, "DRINKS", (W - text_width("DRINKS")) // 2, 22, (240, 240, 240))
    return up(s).convert_alpha()


def zaza_wc_door(accessible=False):
    """A toilet door on the back wall, with its sign."""
    s = canvas(L, 30)
    R(s, OUTLINE, 2, 4, 12, 26); R(s, (70, 76, 86), 3, 5, 10, 25); R(s, shade((70, 76, 86), 1.2), 3, 5, 10, 1)
    R(s, (200, 200, 210), 11, 18, 1, 3)
    R(s, OUTLINE, 3, 0, 10, 6); R(s, (240, 240, 240), 4, 1, 8, 4)
    if accessible:
        circle(s, (40, 90, 200), 8, 3, 1); P(s, (40, 90, 200), 6, 2)
    else:
        P(s, (40, 40, 44), 6, 1); R(s, (40, 40, 44), 5, 2, 3, 2)     # the little people
        P(s, (40, 40, 44), 10, 1); R(s, (40, 40, 44), 9, 2, 3, 2)
    return up(s).convert_alpha()


def zaza_graffiti(v=0):
    """A panel of street art for the rough-rendered walls (one tile wide, the height of the wall face)."""
    rng = random.Random(v * 29 + 4)
    s = canvas(L, 11)
    cols = [(240, 80, 150), (60, 200, 230), (250, 220, 60), (120, 230, 120), (250, 120, 40), (160, 90, 230)]
    a, b = rng.sample(cols, 2)
    for x in range(L):
        y = int(5 + 3 * math.sin(x / 2.2 + v))
        for yy in range(max(0, y - 2), min(11, y + 2)):
            P(s, a, x, yy)
        if rng.random() < 0.3:
            P(s, b, x, rng.randrange(1, 10))
    for x in range(1, L - 2, 4):
        P(s, (250, 250, 250), x + rng.randrange(0, 2), rng.randrange(2, 8))
    return up(s).convert_alpha()


def zaza_neon():
    """The pink-and-gold ZA ZA sign for the wall above the bar."""
    name = "ZA ZA BAZAAR"
    tw = text_width(name)
    s = canvas(tw + 10, 11)
    R(s, (30, 20, 34), 0, 0, s.get_width(), 11)
    draw_text(s, name, 5, 2, (255, 120, 200))
    for x in range(1, s.get_width() - 1, 3):
        P(s, (250, 210, 90), x, 0); P(s, (250, 210, 90), x, 10)
    return up(s).convert_alpha()


def concrete_floor(v=0):
    """Polished concrete, with soft reflections of the lights."""
    rng = random.Random(400 + v)
    s = canvas(L, L)
    base = (112, 110, 112)
    R(s, base, 0, 0, L, L)
    speckle(s, rng, [shade(base, 0.94), shade(base, 1.06), shade(base, 1.12)], 0.12)
    if v % 3 == 0:
        for k in range(3):
            P(s, (150, 140, 130), rng.randrange(L), rng.randrange(L))
    if v % 4 == 1:
        R(s, shade(base, 0.9), 0, L - 1, L, 1)                       # a saw cut joint
    return up(s).convert()


# ============================================================== the crime scene by the water
def _tape_colour(i):
    return (40, 80, 200) if (i // 2) % 2 == 0 else (245, 245, 245)


def police_tape_h(tiles=1):
    """Blue-and-white police tape running across the screen at waist height (no posts)."""
    W = tiles * L
    s = canvas(W, 4)
    for x in range(W):
        P(s, OUTLINE, x, 0)
        P(s, _tape_colour(x), x, 1); P(s, shade(_tape_colour(x), 0.85), x, 2)
        if x % 7 == 3: P(s, OUTLINE, x, 3)                             # it sags a touch between posts
    return up(s).convert_alpha()


def police_tape_v(tiles=1):
    """Police tape running up the screen (seen end-on it's a thin stripy line)."""
    H = tiles * L
    s = canvas(3, H)
    for y in range(H):
        P(s, OUTLINE, 0, y); P(s, _tape_colour(y), 1, y); P(s, OUTLINE, 2, y)
    return up(s).convert_alpha()


def tape_post():
    """A metal post the tape is tied to."""
    s = canvas(4, 14)
    R(s, OUTLINE, 1, 0, 2, 13); R(s, (150, 156, 166), 1, 1, 1, 11)
    R(s, OUTLINE, 0, 12, 4, 2); R(s, (90, 96, 106), 0, 12, 4, 1)
    R(s, (40, 80, 200), 0, 3, 4, 1)                                    # the knot of tape
    return up(s).convert_alpha()


def evidence_marker(n=1):
    """A yellow numbered evidence tent."""
    s = canvas(7, 7)
    pygame.draw.polygon(s, OUTLINE, [(0, 6), (3, 0), (6, 6)])
    pygame.draw.polygon(s, (250, 210, 40), [(1, 6), (3, 1), (5, 6)])
    R(s, shade((250, 210, 40), 0.75), 4, 3, 1, 3)
    s = up(s)
    f = pygame.font.Font(None, 16)
    t = f.render(str(n), True, OUTLINE)
    s.blit(t, (s.get_width() // 2 - t.get_width() // 2, 11))
    return s.convert_alpha()


def forensic_tent():
    """A white forensic tent (two tiles square), the front flap tied half open."""
    W, H = 2 * L, 28
    s = canvas(W, H)
    white, shadow = (236, 238, 242), (196, 200, 210)
    pygame.draw.polygon(s, OUTLINE, [(0, 10), (W // 2, 0), (W - 1, 10)])
    pygame.draw.polygon(s, white, [(1, 10), (W // 2, 1), (W - 2, 10)])
    pygame.draw.polygon(s, shadow, [(W // 2, 1), (W - 2, 10), (W // 2, 10)])
    R(s, OUTLINE, 0, 10, W, H - 10); R(s, white, 1, 11, W - 2, H - 12)
    R(s, shadow, W - 6, 11, 5, H - 12)
    R(s, (40, 50, 70), 11, 15, 10, H - 16)                              # the open flap, dark inside
    pygame.draw.polygon(s, shadow, [(11, 15), (16, 15), (11, H - 2)])
    R(s, (40, 80, 200), 1, 11, W - 2, 1)
    return up(s).convert_alpha()


def appeal_board():
    """The yellow police appeal board: INCIDENT / APPEAL FOR WITNESSES."""
    s = canvas(18, 22)
    R(s, OUTLINE, 2, 14, 1, 8); R(s, OUTLINE, 15, 14, 1, 8)
    R(s, OUTLINE, 0, 0, 18, 15); R(s, (250, 214, 40), 1, 1, 16, 13)
    R(s, (20, 50, 140), 1, 1, 16, 4)
    draw_text(s, "POLICE", 1, 0, (250, 250, 250)) if text_width("POLICE") <= 16 else None
    for y in (7, 9, 11):
        R(s, OUTLINE, 3, y, 12 - (y % 3) * 2, 1)
    return up(s).convert_alpha()


def newspaper_icon():
    s = canvas(14, 12)
    R(s, (236, 232, 220), 0, 1, 13, 11); R(s, (210, 204, 190), 12, 1, 1, 11)
    R(s, (40, 40, 44), 1, 2, 11, 2)                                      # the masthead
    for y in (5, 7, 9):
        R(s, (120, 120, 126), 1, y, 5, 1); R(s, (120, 120, 126), 7, y, 5, 1)
    return up(add_outline(s)).convert_alpha()


def card_icon():
    s = canvas(14, 9)
    R(s, (244, 240, 230), 0, 0, 14, 9)
    R(s, (60, 60, 70), 2, 2, 7, 1); R(s, (140, 140, 150), 2, 4, 9, 1); R(s, (140, 140, 150), 2, 6, 6, 1)
    return up(add_outline(s)).convert_alpha()


# ============================================================== the story's rooms: offices, the arcade store room, home
STEEL, STEEL_D, STEEL_L = (120, 132, 150), (84, 94, 112), (160, 172, 188)
CARD, CARD_D = (196, 156, 104), (160, 122, 78)


def records_shelf(labels=("1994", "1995")):
    """Grey store-room shelving with fat lever-arch binders, a year in big numbers down each spine.
    A label of None leaves a gap (a binder that's gone), just a clean patch in the dust."""
    s = canvas(L, 27)
    R(s, OUTLINE, 0, 0, L, 27)
    R(s, STEEL_D, 1, 1, L - 2, 25)
    for y in (13, 25):                                                   # the shelves
        R(s, STEEL_L, 0, y, L, 1); R(s, STEEL, 0, y + 1, L, 1)
    R(s, STEEL, 0, 0, 1, 27); R(s, STEEL, L - 1, 0, 1, 27)
    cols = [(40, 70, 130), (140, 40, 40), (40, 100, 70), (120, 90, 40)]
    for k, lab in enumerate(labels):
        x = 1 + k * 7
        if lab is None:
            R(s, shade(STEEL_D, 0.8), x, 2, 7, 11)                           # an empty slot
            R(s, (150, 150, 140), x, 12, 7, 1)                               # a line of dust where it stood
            continue
        c = cols[int(lab) % 4]
        R(s, OUTLINE, x, 1, 7, 12); R(s, c, x + 1, 2, 5, 11)
        R(s, shade(c, 1.25), x + 1, 2, 1, 11)
        R(s, (236, 232, 214), x + 1, 3, 5, 9)                                # the white label...
        draw_text(s, lab[2:], x + 1, 5, OUTLINE)                             # ...with the year, big ('98)
        R(s, OUTLINE, x + 3, 11, 1, 1)                                       # finger hole
    for x in range(1, L - 1, 5):                                          # archive boxes on the bottom shelf
        R(s, OUTLINE, x, 16, 5, 9); R(s, CARD, x + 1, 17, 3, 8); R(s, (236, 232, 214), x + 1, 19, 3, 2)
    return up(s).convert_alpha()


def locker(tag=False, seed=0):
    """A pair of tall staff lockers. tag = John's, with a strip of tape and his initials."""
    s = canvas(L, 28)
    R(s, OUTLINE, 0, 0, L, 28)
    for x in (1, 8):
        R(s, STEEL, x, 1, 7, 26); R(s, STEEL_L, x, 1, 7, 1); R(s, STEEL_D, x + 6, 1, 1, 26)
        for y in (3, 5, 7):
            R(s, STEEL_D, x + 2, y, 3, 1)                                    # vents
        R(s, (210, 210, 200), x + 5, 13, 1, 3)                               # handle
        R(s, STEEL_D, x, 23, 7, 1)
    if tag:
        R(s, (236, 232, 214), 2, 10, 5, 3); draw_text(s, "J", 3, 9, OUTLINE) if False else None
        R(s, (40, 40, 44), 3, 11, 1, 1); R(s, (40, 40, 44), 5, 11, 1, 1)    # J.H. in marker pen
    return up(s).convert_alpha()


def boxes(seed=0, open_=False):
    """A stack of cardboard boxes, taped up (or one left open, half packed)."""
    rng = random.Random(seed)
    s = canvas(L, 20)
    def box(x, y, w, h, opened=False):
        R(s, OUTLINE, x, y, w, h); R(s, CARD, x + 1, y + 1, w - 2, h - 2)
        R(s, CARD_D, x + 1, y + 1, w - 2, 2)
        if opened:
            R(s, (60, 46, 36), x + 2, y + 1, w - 4, 2)                       # dark inside, flaps up
            R(s, CARD, x - 1, y - 2, 3, 3); R(s, CARD, x + w - 2, y - 2, 3, 3)
            R(s, (240, 236, 226), x + 3, y - 1, 3, 2)                        # papers sticking out
        else:
            R(s, (200, 180, 140), x + w // 2, y + 1, 1, h - 2)               # parcel tape
    box(0, 9, 9, 11); box(8, 11, 8, 9)
    box(2 + rng.randrange(0, 3), 1, 9, 9, open_)
    return up(s).convert_alpha()


def desk(kind="usher", seed=0):
    """An office desk, two tiles wide, and what's on it:
    usher = green banker's lamp, papers, books;  packed = drawers out, papers everywhere, no laptop;
    gazette = a computer and a pile of newspapers."""
    rng = random.Random(seed)
    W = 2 * L
    s = canvas(W, 20)
    wood, wood_d, wood_l = (122, 80, 50), (88, 56, 36), (150, 104, 68)
    R(s, OUTLINE, 0, 6, W, 14)
    R(s, wood_l, 1, 7, W - 2, 4); R(s, wood, 1, 11, W - 2, 8)                # top and front
    for x in (2, W - 11):                                                    # drawer stacks
        R(s, wood_d, x, 12, 9, 7)
        for y in (13, 16):
            R(s, wood, x + 1, y, 7, 2); R(s, (220, 190, 120), x + 4, y + 1, 1, 1)
    if kind == "packed":
        R(s, OUTLINE, W - 12, 17, 11, 4); R(s, wood_l, W - 11, 18, 9, 2)     # a drawer pulled right out
    if kind in ("usher", "packed"):
        if kind == "usher":
            R(s, OUTLINE, 3, 0, 7, 3); R(s, (40, 130, 70), 4, 0, 5, 2)       # green banker's lamp
            R(s, (200, 170, 80), 6, 3, 1, 4); R(s, (200, 170, 80), 4, 6, 5, 1)
        for k in range(3 if kind == "usher" else 6):                         # papers
            px_, py_ = rng.randrange(10, W - 8), rng.randrange(7, 9)
            R(s, (240, 236, 226), px_, py_, 5, 2); R(s, (180, 176, 168), px_ + 1, py_, 3, 1)
        if kind == "usher":
            R(s, OUTLINE, W - 9, 3, 6, 4); R(s, (130, 40, 40), W - 8, 4, 4, 1); R(s, (40, 70, 120), W - 8, 5, 4, 1)  # books
    if kind == "gazette":
        R(s, OUTLINE, 10, 0, 12, 8); R(s, (40, 44, 52), 11, 1, 10, 6); R(s, (110, 170, 210), 12, 2, 8, 4)  # monitor
        R(s, (60, 64, 72), 15, 7, 2, 1)
        R(s, OUTLINE, 3, 4, 7, 4); R(s, (226, 222, 210), 4, 4, 5, 3); R(s, (90, 90, 96), 4, 5, 5, 1)    # newspapers
        R(s, (240, 240, 236), W - 7, 5, 3, 3); R(s, (150, 60, 50), W - 7, 5, 3, 1)                       # mug
    return up(s).convert_alpha()


def office_chair(leather=True):
    s = canvas(10, 14)
    c = (90, 40, 30) if leather else (40, 44, 52)
    R(s, OUTLINE, 1, 0, 8, 9); R(s, c, 2, 1, 6, 7); R(s, shade(c, 1.3), 2, 1, 6, 1)
    R(s, OUTLINE, 0, 7, 10, 3); R(s, shade(c, 0.8), 1, 8, 8, 1)
    R(s, OUTLINE, 4, 10, 2, 3); R(s, OUTLINE, 1, 13, 8, 1)
    return up(s).convert_alpha()


def bookcase(seed=0, gaps=False):
    """Floor-to-ceiling oak bookcase. gaps = half emptied (someone's been packing)."""
    rng = random.Random(seed)
    s = canvas(L, 30)
    wood = (104, 68, 44)
    R(s, OUTLINE, 0, 0, L, 30); R(s, wood, 1, 1, L - 2, 28); R(s, shade(wood, 1.2), 1, 1, L - 2, 1)
    for y in (8, 15, 22, 29):
        R(s, shade(wood, 0.7), 1, y, L - 2, 1)
    for row_y in (2, 9, 16, 23):
        x = 1
        while x < L - 1:
            w = rng.choice((1, 1, 2))
            if gaps and rng.random() < 0.55:
                x += w; continue
            c = rng.choice([(130, 40, 40), (40, 70, 130), (40, 100, 70), (190, 160, 70), (90, 60, 110), (210, 200, 180)])
            hgt = 6 - rng.randrange(0, 2)
            R(s, c, x, row_y + 6 - hgt, w, hgt)
            x += w
    return up(s).convert_alpha()


def filing_cabinet(open_=False):
    s = canvas(12, 20)
    R(s, OUTLINE, 0, 0, 12, 20); R(s, (150, 140, 120), 1, 1, 10, 18)
    for y in (2, 8, 14):
        R(s, (120, 112, 96), 1, y + 5, 10, 1); R(s, (210, 200, 170), 4, y + 2, 4, 1)
    if open_:
        R(s, OUTLINE, 0, 8, 12, 6); R(s, (170, 160, 140), 1, 9, 10, 4)
        for x in (2, 5, 8):
            R(s, (240, 236, 226), x, 7, 2, 3)
    return up(s).convert_alpha()


def sofa():
    """A worn two-seater (two tiles wide)."""
    W = 2 * L
    s = canvas(W, 16)
    c = (110, 60, 50)
    R(s, OUTLINE, 0, 0, W, 16)
    R(s, c, 1, 1, W - 2, 7); R(s, shade(c, 1.2), 1, 1, W - 2, 1)               # back
    R(s, shade(c, 0.8), 1, 8, W - 2, 7)                                       # seat
    R(s, shade(c, 1.1), 2, 8, 13, 3); R(s, shade(c, 1.1), 17, 8, 13, 3)      # cushions
    R(s, OUTLINE, 0, 4, 3, 12); R(s, c, 1, 5, 1, 10)                          # arms
    R(s, OUTLINE, W - 3, 4, 3, 12); R(s, c, W - 2, 5, 1, 10)
    return up(s).convert_alpha()


def side_table(ring=0):
    """Little table with an old phone on it; ring > 0 = shaking (ringing)."""
    s = canvas(12, 16)
    wood = (120, 84, 56)
    R(s, OUTLINE, 0, 6, 12, 3); R(s, wood, 1, 6, 10, 2)
    R(s, OUTLINE, 2, 8, 1, 8); R(s, OUTLINE, 9, 8, 1, 8)
    dx = (-1, 1, 0)[ring % 3] if ring else 0
    R(s, OUTLINE, 3 + dx, 2, 6, 4); R(s, (30, 30, 34), 4 + dx, 3, 4, 2)       # the phone
    R(s, OUTLINE, 3 + dx, 1, 6, 1)                                            # handset
    R(s, (220, 60, 50), 6 + dx, 3, 1, 1)                                      # a light
    R(s, (236, 230, 210), 1, 5, 3, 1)                                         # ashtray
    return up(s).convert_alpha()


def floor_lamp():
    s = canvas(10, 28)
    R(s, OUTLINE, 1, 0, 8, 7); R(s, (236, 214, 160), 2, 1, 6, 5)
    R(s, OUTLINE, 4, 7, 2, 19); R(s, OUTLINE, 2, 26, 6, 2)
    return up(s).convert_alpha()


def armchair():
    s = canvas(14, 16)
    c = (60, 80, 70)
    R(s, OUTLINE, 0, 0, 14, 16); R(s, c, 1, 1, 12, 7); R(s, shade(c, 1.2), 1, 1, 12, 1)
    R(s, shade(c, 0.8), 1, 8, 12, 7); R(s, OUTLINE, 0, 5, 3, 11); R(s, OUTLINE, 11, 5, 3, 11)
    R(s, c, 1, 6, 1, 9); R(s, c, 12, 6, 1, 9)
    return up(s).convert_alpha()


def papers_decal(seed=0):
    """Papers dropped on the floor (a tile's worth)."""
    rng = random.Random(seed)
    s = canvas(L, L)
    for _ in range(5):
        x, y = rng.randrange(0, L - 5), rng.randrange(0, L - 4)
        R(s, (200, 196, 186), x, y + 1, 5, 4); R(s, (244, 240, 230), x, y, 5, 4)
        R(s, (170, 166, 156), x + 1, y + 1, 3, 1)
    return up(s).convert_alpha()


# ---- pocket icons for the story's evidence
def recorder_icon():
    s = canvas(8, 13)
    R(s, (40, 42, 50), 0, 0, 8, 13); R(s, (70, 74, 86), 1, 1, 6, 4)
    for y in (2, 3):
        R(s, (30, 30, 34), 2, y, 4, 1)
    R(s, (200, 50, 50), 1, 7, 2, 2); R(s, (150, 156, 170), 4, 7, 3, 1); R(s, (150, 156, 170), 4, 9, 3, 1)
    return up(add_outline(s)).convert_alpha()


def token_icon():
    s = canvas(11, 11)
    ellipse_fill(s, (150, 110, 40), 5, 5, 5, 5)
    ellipse_fill(s, (220, 180, 80), 5, 5, 4, 4)
    ellipse_fill(s, (190, 150, 60), 5, 5, 2, 2)
    R(s, (250, 230, 150), 3, 2, 2, 1)
    return up(add_outline(s)).convert_alpha()


def photo_icon(tint=(150, 130, 100)):
    s = canvas(13, 11)
    R(s, (244, 240, 230), 0, 0, 13, 11)
    R(s, tint, 1, 1, 11, 7)
    R(s, shade(tint, 0.6), 2, 4, 2, 4); R(s, shade(tint, 0.6), 6, 3, 2, 5); R(s, shade(tint, 0.6), 9, 4, 2, 4)  # people
    return up(add_outline(s)).convert_alpha()


def notes_icon():
    s = canvas(11, 13)
    R(s, (240, 236, 214), 0, 0, 11, 13)
    for y in range(2, 12, 2):
        R(s, (90, 100, 150), 1, y, 8 - (y % 4), 1)
    R(s, (200, 70, 60), 0, 0, 1, 13)
    return up(add_outline(s)).convert_alpha()


def folder_icon(colour=(40, 70, 130), year="98"):
    s = canvas(11, 14)
    R(s, colour, 0, 0, 11, 14); R(s, shade(colour, 1.25), 0, 0, 1, 14)
    R(s, (236, 232, 214), 2, 3, 7, 7)
    draw_text(s, year, 2, 4, OUTLINE)
    return up(add_outline(s)).convert_alpha()


def cutting_icon():
    s = canvas(12, 12)
    R(s, (226, 212, 176), 0, 0, 12, 12)
    R(s, (60, 50, 40), 1, 1, 10, 2)
    for y in (5, 7, 9):
        R(s, (130, 116, 96), 1, y, 4, 1); R(s, (130, 116, 96), 6, y, 5, 1)
    return up(add_outline(s)).convert_alpha()


def bunk_bed(seed=0):
    """A hostel bunk bed: metal frame, two mattresses, a different blanket on each."""
    rng = random.Random(seed)
    s = canvas(L, 26)
    frame = (70, 76, 88)
    for x in (0, L - 2):
        R(s, OUTLINE, x, 0, 2, 26); R(s, frame, x, 1, 1, 24)
    for y, blanket in ((2, rng.choice([(60, 90, 150), (150, 50, 50), (60, 120, 80)])),
                       (14, rng.choice([(200, 150, 60), (110, 70, 140), (40, 110, 120)]))):
        R(s, OUTLINE, 1, y, L - 2, 9)
        R(s, (236, 232, 222), 2, y + 1, L - 4, 3)                      # pillow end / sheet
        R(s, (250, 248, 244), 3, y + 1, 4, 2)                          # pillow
        R(s, blanket, 2, y + 4, L - 4, 4); R(s, shade(blanket, 1.2), 2, y + 4, L - 4, 1)
        R(s, frame, 1, y + 8, L - 2, 1)
    R(s, frame, 4, 11, 1, 3); R(s, frame, 4, 12, 3, 1)                 # the ladder
    return up(s).convert_alpha()


# ============================================================== the Wills Memorial Building's entrance hall
WILLS_STONE, WILLS_STONE_D, WILLS_STONE_L = (214, 200, 168), (176, 160, 128), (232, 222, 196)


def hall_floor(v=0):
    """Polished stone flags, a soft shine on them."""
    rng = random.Random(8100 + v)
    s = canvas(L, L)
    base = (200, 186, 156)
    R(s, shade(base, rng.uniform(0.96, 1.04)), 0, 0, L, L)
    R(s, shade(base, 0.82), 0, 15, L, 1); R(s, shade(base, 0.82), 15, 0, 1, L)
    R(s, shade(base, 1.08), 0, 0, L, 1)
    for _ in range(4):
        P(s, shade(base, rng.uniform(0.9, 1.1)), rng.randrange(1, 15), rng.randrange(1, 15))
    if v % 2 == 0:
        R(s, shade(base, 1.12), 3 + v % 5, 4, 4, 1)                      # the shine from the lights
    return up(s).convert()


def wills_back_wall(tiles=20, door_x=2, arch=(8, 12)):
    """The great back wall of the hall, two tiles tall: tall stone panelling, three gothic windows with the
    city / university shields under them, the arch through to the corridor, and Professor Usher's office door."""
    W, H = tiles * L, 2 * L
    s = canvas(W, H)
    R(s, WILLS_STONE, 0, 0, W, H)
    for x in range(0, W, 4):                                              # tall stone panelling
        R(s, WILLS_STONE_L, x, 0, 1, H); R(s, WILLS_STONE_D, x + 3, 0, 1, H)
    for y in (9, 21):
        R(s, WILLS_STONE_D, 0, y, W, 1); R(s, WILLS_STONE_L, 0, y + 1, W, 1)
    R(s, WILLS_STONE_D, 0, H - 3, W, 3)                                   # skirting
    ax0, ax1 = arch[0] * L, arch[1] * L
    for i, cx in enumerate((ax0 - 30, (ax0 + ax1) // 2, ax1 + 30)):          # windows and shields
        R(s, OUTLINE, cx - 7, 1, 14, 9); R(s, (60, 70, 96), cx - 6, 2, 12, 7)
        for k in (cx - 2, cx + 2):
            R(s, WILLS_STONE_D, k, 2, 1, 7)
        R(s, (250, 230, 160), cx - 5, 3, 2, 2); R(s, (250, 230, 160), cx + 3, 3, 2, 2)   # lit inside
        R(s, OUTLINE, cx - 3, 11, 6, 7)
        colours = [(170, 40, 40), (240, 240, 236), (170, 40, 40)]
        R(s, colours[i], cx - 2, 12, 4, 5); P(s, colours[i], cx - 1, 17); P(s, colours[i], cx, 17)
        R(s, (220, 180, 60) if i != 1 else (180, 30, 30), cx - 1, 13, 2, 2)
    # the arch through to the corridor (dark, a glass door at the end)
    R(s, OUTLINE, ax0, 8, ax1 - ax0, H - 8)
    R(s, (54, 50, 62), ax0 + 1, 9, ax1 - ax0 - 2, H - 9)
    pygame.draw.polygon(s, WILLS_STONE, [(ax0, 8), (ax0 + (ax1 - ax0) // 2, 2), (ax1, 8)])
    pygame.draw.lines(s, OUTLINE, False, [(ax0, 8), (ax0 + (ax1 - ax0) // 2, 2), (ax1 - 1, 8)])
    gx = (ax0 + ax1) // 2
    R(s, (150, 176, 196), gx - 6, 18, 12, H - 21); R(s, (210, 226, 236), gx - 6, 18, 12, 1)
    R(s, OUTLINE, gx, 18, 1, H - 21)
    R(s, (240, 230, 200), gx - 3, 14, 6, 2)                                # the light in the corridor
    # Professor Usher's door: dark oak, a pointed top, a brass plate
    dx = door_x * L
    R(s, OUTLINE, dx + 2, 12, 12, H - 14)
    R(s, (96, 60, 36), dx + 3, 13, 10, H - 15)
    pygame.draw.polygon(s, OUTLINE, [(dx + 2, 12), (dx + 8, 8), (dx + 13, 12)])
    pygame.draw.polygon(s, (96, 60, 36), [(dx + 4, 12), (dx + 8, 9), (dx + 11, 12)])
    R(s, (70, 44, 26), dx + 8, 13, 1, H - 15)
    R(s, (210, 176, 90), dx + 10, 21, 1, 2)                                # handle
    R(s, OUTLINE, dx + 2, 4, 12, 4); R(s, (210, 176, 90), dx + 3, 5, 10, 2)   # name plate
    return up(s).convert_alpha()


def grand_stairs(flip=False):
    """One of the two great staircases (5 tiles wide, 5 deep): stone steps rising to the back wall,
    a stone balustrade on the inner side and big square newel posts at the bottom."""
    W, H = 5 * L, 5 * L + 6
    s = canvas(W, H)
    for i in range(16):                                                   # the steps, darker as they go up
        y = 6 + i * 5
        k = 0.8 + i * 0.012
        R(s, shade(WILLS_STONE_L, k + 0.18), 3, y, W - 6, 3)                # tread
        R(s, shade(WILLS_STONE_D, k), 3, y + 3, W - 6, 2)                   # riser (the face of the next step)
    R(s, OUTLINE, 0, 6, 4, H - 6); R(s, WILLS_STONE_L, 1, 6, 2, H - 6)      # balustrades either side
    R(s, OUTLINE, W - 4, 6, 4, H - 6); R(s, WILLS_STONE_L, W - 3, 6, 2, H - 6)
    for x in (0, W - 7):                                                  # newel posts at the bottom
        R(s, OUTLINE, x, H - 18, 7, 18); R(s, WILLS_STONE, x + 1, H - 17, 5, 16)
        R(s, WILLS_STONE_L, x + 1, H - 17, 5, 2); R(s, WILLS_STONE_D, x + 1, H - 4, 5, 3)
    R(s, (90, 70, 60), W // 2 - 8, 8, 16, H - 26)
    for i in range(16):
        R(s, (70, 52, 46), W // 2 - 8, 10 + i * 5, 16, 1)
    img = up(s).convert_alpha()
    return pygame.transform.flip(img, True, False) if flip else img


def rope_barrier(tiles=5):
    """Black posts with a red rope between (keeps people off the stairs)."""
    W = tiles * L
    s = canvas(W, 14)
    posts = list(range(1, W, (W - 3) // max(1, tiles - 1)))
    for i, x in enumerate(posts):
        R(s, OUTLINE, x, 2, 2, 12); R(s, (40, 40, 44), x - 1, 12, 4, 2)
        R(s, (200, 200, 210), x, 2, 2, 1)
        if i + 1 < len(posts):
            nx = posts[i + 1]
            for xx in range(x + 2, nx):
                sag = int(2 * math.sin(math.pi * (xx - x) / max(1, nx - x)))
                P(s, (190, 30, 40), xx, 4 + sag); P(s, (140, 20, 30), xx, 5 + sag)
    return up(s).convert_alpha()


def directory_sign():
    """The tall black directory board: WILLS MEMORIAL BUILDING, floor by floor."""
    s = canvas(10, 34)
    R(s, OUTLINE, 1, 0, 8, 32); R(s, (34, 34, 40), 2, 1, 6, 30)
    R(s, (230, 230, 230), 2, 2, 6, 1)
    for y in range(5, 29, 4):
        R(s, (210, 210, 214), 3, y, 4, 2)
    R(s, (60, 60, 66), 0, 32, 10, 2)
    return up(s).convert_alpha()


def bust_on_plinth():
    s = canvas(10, 26)
    R(s, OUTLINE, 1, 10, 8, 16); R(s, (70, 64, 66), 2, 11, 6, 15); R(s, (100, 92, 94), 2, 11, 6, 1)   # marble plinth
    ellipse_fill(s, OUTLINE, 5, 6, 3, 4); ellipse_fill(s, (60, 52, 44), 5, 6, 2, 3)                   # bronze head
    R(s, OUTLINE, 3, 9, 4, 2); R(s, (60, 52, 44), 3, 9, 4, 1)
    P(s, (110, 96, 80), 4, 5)
    return up(s).convert_alpha()


def display_case():
    """A glass cabinet of old university things."""
    s = canvas(L, 22)
    R(s, OUTLINE, 0, 0, L, 22); R(s, (130, 92, 60), 1, 14, L - 2, 7)
    R(s, (176, 206, 220), 1, 1, L - 2, 13); R(s, (220, 236, 244), 1, 1, L - 2, 1)
    for x, c in ((3, (180, 150, 90)), (7, (120, 120, 130)), (11, (160, 60, 50))):
        R(s, c, x, 8, 2, 5)
    R(s, (100, 70, 44), 1, 18, L - 2, 1)
    return up(s).convert_alpha()


def roll_banner():
    """A roll-up banner on its stand (Earth Sciences this way)."""
    s = canvas(9, 28)
    R(s, OUTLINE, 0, 0, 9, 26); R(s, (40, 80, 150), 1, 1, 7, 24)
    R(s, (240, 240, 240), 2, 4, 5, 1); R(s, (240, 240, 240), 2, 6, 3, 1)
    R(s, (200, 120, 60), 2, 10, 5, 6); R(s, (90, 140, 200), 2, 17, 5, 5)
    R(s, (60, 60, 66), 0, 26, 9, 2)
    return up(s).convert_alpha()


def computer_desk(seed=0, on=True):
    """A desk with a computer on it, the screen still on (two tiles wide)."""
    W = 2 * L
    s = canvas(W, 20)
    wood, wood_d, wood_l = (122, 80, 50), (88, 56, 36), (150, 104, 68)
    R(s, OUTLINE, 0, 6, W, 14)
    R(s, wood_l, 1, 7, W - 2, 4); R(s, wood, 1, 11, W - 2, 8)
    R(s, wood_d, W - 11, 12, 9, 7)
    for y in (13, 16):
        R(s, wood, W - 10, y, 7, 2); R(s, (220, 190, 120), W - 7, y + 1, 1, 1)
    R(s, OUTLINE, 8, 0, 14, 9); R(s, (40, 44, 52), 9, 1, 12, 7)                # monitor
    R(s, (120, 190, 230) if on else (30, 34, 40), 10, 2, 10, 5)
    if on:
        R(s, (230, 240, 250), 11, 3, 6, 1); R(s, (200, 220, 240), 11, 5, 4, 1)
    R(s, (60, 64, 72), 14, 8, 2, 1)
    R(s, OUTLINE, 9, 9, 10, 2); R(s, (200, 200, 206), 10, 9, 8, 1)              # keyboard
    R(s, (240, 240, 236), 22, 7, 3, 3); R(s, (90, 60, 40), 22, 7, 3, 1)        # mug
    return up(s).convert_alpha()
