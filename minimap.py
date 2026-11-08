"""The mini-map in the bottom-left corner: the streets around you from above, with you on it.

It's drawn once per place (roads, pavements, grass, water, buildings, shop doors, the ways to other places),
then each frame it's just cut out around you, with the cars and you drawn on top.
"""
import math
import pygame

TILE = 64
BOX_W, BOX_H = 236, 150          # the map window (inside the frame)
SCALE = 3                        # px per tile out in the streets (rooms get as big as fits)

GROUND = {
    '~': (52, 112, 130), '+': (176, 150, 112), '=': (78, 80, 88), 'z': (226, 226, 226), 'v': (78, 80, 88),
    '-': (206, 198, 182), '.': (110, 162, 86), '`': (48, 50, 58), '/': (156, 146, 132), '(': (156, 146, 132),
    ')': (156, 146, 132), '|': (60, 60, 64), '!': (120, 160, 186), '%': (120, 170, 220),
    'T': (64, 132, 62), 't': (176, 90, 44), '^': (60, 120, 100),
}
STYLE = {   # buildings, by style
    'H': (146, 152, 174), 'W': (204, 186, 140), 'C': (118, 122, 134), 'K': (168, 92, 72), 'D': (220, 210, 182),
    'P': (112, 106, 100), 'X': (126, 126, 124), 'O': (78, 58, 92), 'R': (232, 92, 196), 'B': (164, 74, 54),
    'Z': (92, 120, 140), 'U': (150, 156, 170), 'V': (150, 140, 120), 'A': (150, 140, 120), 'M': (150, 140, 120),
    'G': (150, 140, 120),
}
INSIDE = {   # rooms
    '#': (40, 38, 50), 'E': (110, 200, 120), 'Q': (150, 104, 60), 'X': (150, 104, 60), 'M': (120, 120, 130),
    'p': (230, 210, 150), 'g': (80, 150, 80), '1': (255, 90, 160), '2': (90, 200, 255), '3': (255, 150, 60),
    '4': (120, 255, 120),
    # Za Za Bazaar
    'i': (118, 116, 118), 'S': (190, 196, 204), 'x': (190, 196, 204), 'B': (190, 110, 60), 'K': (70, 44, 40),
    'b': (150, 40, 44), 'h': (150, 40, 44), 'T': (176, 136, 92), 'P': (160, 158, 154), 'F': (60, 120, 200),
    'W': (70, 76, 86), 'V': (70, 120, 200),
    # the story's rooms
    '5': (120, 132, 150), '6': (120, 132, 150), '7': (196, 156, 104), '8': (122, 80, 50), '9': (122, 80, 50),
    '0': (104, 68, 44), '[': (150, 140, 120), '<': (110, 60, 50), '>': (110, 60, 50), '?': (120, 84, 56),
    ']': (60, 80, 70),
}
FLOOR = (196, 176, 150)
EDGE = (40, 42, 54)
DOOR = (255, 226, 90)
EXIT = (80, 150, 255)


def _base(world):
    """The whole place drawn small, once."""
    W, H = world.w, world.h
    if world.interior is not None:
        s = max(3, min(BOX_W // W, BOX_H // H, 10))
    else:
        s = SCALE
    surf = pygame.Surface((W * s, H * s))
    surf.fill((206, 198, 182))
    real = world.real
    for y in range(H):
        for x in range(W):
            ch = world.grid[y][x]
            if world.interior is not None:
                c = INSIDE.get(ch, FLOOR)
            elif ch == 'H' and real is not None and real["ids"][y][x] >= 0:
                c = STYLE.get(real["buildings"][real["ids"][y][x]].get("style", "H"), STYLE['H'])
            elif ch == 'H':
                c = STYLE['H']
            else:
                c = GROUND.get(ch, GROUND.get(world.ground[y][x], (206, 198, 182)))
            surf.fill(c, (x * s, y * s, s, s))
    # College Green's grass and paths
    for sh in (getattr(world._map_def, "GROUND_SHAPES", []) if not isinstance(world._map_def, str) else []):
        col = GROUND['.'] if sh["kind"] == "grass" else (214, 204, 180)
        if "poly" in sh:
            pygame.draw.polygon(surf, col, [(a * s, b * s) for a, b in sh["poly"]])
        if "line" in sh:
            pygame.draw.lines(surf, col, False, [(a * s, b * s) for a, b in sh["line"]], max(1, int(sh.get("width", 1) * s)))
        if "circle" in sh:
            cx, cy, r = sh["circle"]; pygame.draw.circle(surf, col, (cx * s, cy * s), r * s)
    # outlines where one building meets another or the street, so the blocks read as buildings
    if world.interior is None and real is not None:
        ids = real["ids"]
        def bid(x, y):
            return ids[y][x] if 0 <= x < W and 0 <= y < H and world.grid[y][x] == 'H' else -1
        for y in range(H):
            for x in range(W):
                b = bid(x, y)
                if b < 0:
                    continue
                if bid(x, y - 1) != b: surf.fill(EDGE, (x * s, y * s, s, 1))
                if bid(x, y + 1) != b: surf.fill(EDGE, (x * s, y * s + s - 1, s, 1))
                if bid(x - 1, y) != b: surf.fill(EDGE, (x * s, y * s, 1, s))
                if bid(x + 1, y) != b: surf.fill(EDGE, (x * s + s - 1, y * s, 1, s))
    # boats moored in the harbour
    for bx, by, kind, colour, flip in (getattr(world._map_def, "BOATS", []) if not isinstance(world._map_def, str) else []):
        wdt = {'narrow': 2.75, 'yacht': 1.9, 'launch': 1.5, 'ferry': 2.5}.get(kind, 2.0)
        r = pygame.Rect(int((bx - wdt / 2) * s), int((by - 0.6) * s), max(3, int(wdt * s)), max(2, int(0.6 * s)))
        surf.fill((240, 240, 236), r)
        surf.fill((60, 60, 70), (r.x, r.bottom - 1, r.w, 1))
    # shop doors and the ways to other places
    for (dx, dy), shop in world.doors.items():
        yy = dy * s + s - 2 if shop.get("side") == "south" else dy * s
        surf.fill(DOOR, (dx * s, yy, s, 2))
    for pt in world.portals:
        a = pt["area"]
        r = pygame.Rect(a.x * s // TILE, a.y * s // TILE, max(2, a.w * s // TILE), max(2, a.h * s // TILE))
        surf.fill(EXIT, r)
    return surf, s


class MiniMap:
    def __init__(self):
        self.cache = {}                  # id(world) -> (surface, scale, world)
        self.frame = None
        self.font = pygame.font.SysFont("consolas,menlo,monospace", 12, bold=True)

    def draw(self, screen, world, player, name):
        key = id(world)
        got = self.cache.get(key)
        if got is None or got[2] is not world:
            if len(self.cache) > 12:
                self.cache.clear()
            base, s = _base(world)
            got = self.cache[key] = (base, s, world)
        base, s, _ = got
        sw, sh = screen.get_size()
        fx, fy = 12, sh - BOX_H - 12 - 22            # frame: a title strip on top of the map window
        # the window into the map, centred on you (or the whole room / small street, centred in the box)
        px, py = player.pos.x / TILE * s, player.pos.y / TILE * s
        bw, bh = base.get_size()
        vx = (bw - BOX_W) / 2 if bw <= BOX_W else min(max(0, px - BOX_W / 2), bw - BOX_W)
        vy = (bh - BOX_H) / 2 if bh <= BOX_H else min(max(0, py - BOX_H / 2), bh - BOX_H)
        vx, vy = int(vx), int(vy)
        win = pygame.Surface((BOX_W, BOX_H))
        win.fill((24, 26, 34))
        win.blit(base, (-vx, -vy))
        # cars
        for tr in (world.traffic, world.vtraffic):
            if tr is None or not getattr(tr, "ok", True):
                continue
            for car in tr.cars:
                if hasattr(car, "x") and not hasattr(car, "y"):
                    cx, cy = car.x, tr.lane_y[car.lane] - 20
                else:
                    cx, cy = tr.lanes[car.lane][0] * TILE, car.y - tr.length / 2
                x, y = cx / TILE * s - vx, cy / TILE * s - vy
                if -4 < x < BOX_W + 4 and -4 < y < BOX_H + 4:
                    pygame.draw.rect(win, tuple(car.colour), (int(x) - 2, int(y) - 2, 4, 4))
        # you: a dot with an arrow for the way you're facing, pulsing gently
        x, y = int(px - vx), int(py - vy)
        t = pygame.time.get_ticks() / 1000
        r = 7 + 2 * math.sin(t * 4)
        ring = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(ring, (255, 255, 255, 90), (12, 12), int(r))
        win.blit(ring, (x - 12, y - 12))
        d = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(getattr(player, "direction", "down"), (0, 1))
        tip = (x + d[0] * 8, y + d[1] * 8)
        side = (-d[1], d[0])
        pygame.draw.polygon(win, (20, 20, 28), [(tip[0] + d[0], tip[1] + d[1]), (x + side[0] * 5 - d[0], y + side[1] * 5 - d[1]),
                                                (x - side[0] * 5 - d[0], y - side[1] * 5 - d[1])])
        pygame.draw.polygon(win, (255, 80, 70), [tip, (x + side[0] * 4, y + side[1] * 4), (x - side[0] * 4, y - side[1] * 4)])
        pygame.draw.circle(win, (20, 20, 28), (x, y), 4)
        pygame.draw.circle(win, (255, 255, 255), (x, y), 3)
        # frame
        pygame.draw.rect(screen, (14, 16, 24), (fx - 3, fy - 3, BOX_W + 6, BOX_H + 22 + 6), border_radius=6)
        pygame.draw.rect(screen, (34, 38, 52), (fx, fy, BOX_W, 22), border_top_left_radius=4, border_top_right_radius=4)
        label = self.font.render(name.upper(), True, (236, 238, 244))
        if label.get_width() > BOX_W - 12:
            label = self.font.render(name.upper()[:28] + "...", True, (236, 238, 244))
        screen.blit(label, (fx + 8, fy + 11 - label.get_height() // 2))
        screen.blit(win, (fx, fy + 22))
        pygame.draw.rect(screen, (120, 140, 170), (fx - 1, fy - 1, BOX_W + 2, BOX_H + 22 + 2), 1, border_radius=5)
