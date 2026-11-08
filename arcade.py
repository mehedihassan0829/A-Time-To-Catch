"""The arcade on the harbourside: the machines, and the games you play on them.

Walk up to a machine in the arcade and press E. The game fills your screen, framed by the
machine's own cabinet round the edge. ESC (or BACKSPACE) takes you back into the arcade.

  SEAGULL       Flappy-bird style, but you're a Bristol gull dodging Cabot Tower and the harbour cranes.
  HOOPS         Basketball with real ball physics. Baskets in a row score more and more.
  INVADERS      Space Invaders.
  MVB KOMBAT    The MVB Kombat fighting game (in the mvb_kombat folder), running inside the machine.

High scores are kept in saves/highscores.json.
"""
import json, math, os, random, sys
from pathlib import Path
import pygame

GW, GH = 384, 216                       # the machines' screens are drawn at this size, then scaled up (x3 on 1280x720)

# ------------------------------------------------------------------ the machines
MACHINES = {
    "seagull": dict(title="SEAGULL BIRD", short="SEAGULL", body=(36, 120, 170), trim=(250, 214, 70), glow=(120, 200, 255)),
    "hoops": dict(title="HOOP SHOT", short="HOOPS", body=(200, 90, 30), trim=(250, 240, 230), glow=(255, 160, 60)),
    "invaders": dict(title="INVADERS", short="INVADERS", body=(40, 40, 52), trim=(90, 255, 120), glow=(90, 255, 120)),
    "kombat": dict(title="MVB KOMBAT", short="MVB KOMBAT", body=(120, 24, 30), trim=(250, 200, 60), glow=(255, 80, 60)),
}

# ------------------------------------------------------------------ a little pixel font (5 high) with everything the screens need
_F = {
    'A': ".#./#.#/###/#.#/#.#", 'B': "##./#.#/##./#.#/##.", 'C': ".##/#../#../#../.##", 'D': "##./#.#/#.#/#.#/##.",
    'E': "###/#../##./#../###", 'F': "###/#../##./#../#..", 'G': ".##/#../#.#/#.#/.##", 'H': "#.#/#.#/###/#.#/#.#",
    'I': "###/.#./.#./.#./###", 'J': "..#/..#/..#/#.#/.#.", 'K': "#.#/#.#/##./#.#/#.#", 'L': "#../#../#../#../###",
    'M': "#...#/##.##/#.#.#/#...#/#...#", 'N': "#..#/##.#/#.##/#..#/#..#", 'O': ".#./#.#/#.#/#.#/.#.",
    'P': "##./#.#/##./#../#..", 'Q': ".#./#.#/#.#/##./.##", 'R': "##./#.#/##./#.#/#.#", 'S': ".##/#../.#./..#/##.",
    'T': "###/.#./.#./.#./.#.", 'U': "#.#/#.#/#.#/#.#/###", 'V': "#.#/#.#/#.#/#.#/.#.", 'W': "#...#/#...#/#.#.#/##.##/#...#",
    'X': "#.#/#.#/.#./#.#/#.#", 'Y': "#.#/#.#/.#./.#./.#.", 'Z': "###/..#/.#./#../###",
    '0': ".#./#.#/#.#/#.#/.#.", '1': ".#./##./.#./.#./###", '2': "##./..#/.#./#../###", '3': "##./..#/.#./..#/##.",
    '4': "#.#/#.#/###/..#/..#", '5': "###/#../##./..#/##.", '6': ".##/#../##./#.#/.#.", '7': "###/..#/.#./.#./.#.",
    '8': ".#./#.#/.#./#.#/.#.", '9': ".#./#.#/.##/..#/##.", ' ': "../../../../..", '.': "./././././#"[:9],
    ':': "./#/./#/.", '!': "#/#/#/./#", '?': "##./..#/.#./.../.#.", '-': ".../.../###/.../...", '+': ".../.#./###/.#./...",
    '/': "..#/..#/.#./#../#..", '=': ".../###/.../###/...", '(': ".#/#./#./#./.#", ')': "#./.#/.#/.#/#.", "'": "#/#/././.", 'x': ".../#.#/.#./#.#/...", '&': ".#../#.#./.#../#.##/.##.",
}
_F['.'] = "././././#"
_glyph_cache = {}


def text_w(text, scale=1):
    w = 0
    for ch in text:
        g = _F.get(ch, _F.get(ch.upper(), _F[' ']))
        w += len(g.split('/')[0]) + 1
    return max(0, w - 1) * scale


def text(surf, s, x, y, colour, scale=1, centre=False, shadow=None):
    """Pixel text. With centre=True, x is the middle."""
    if centre:
        x -= text_w(s, scale) // 2
    key = (s, colour, scale, shadow)
    img = _glyph_cache.get(key)
    if img is None:
        w = text_w(s) + 2
        img = pygame.Surface((max(1, w), 7), pygame.SRCALPHA)
        cx = 0
        for ch in s:
            rows = _F.get(ch, _F.get(ch.upper(), _F[' '])).split('/')
            for ry, row in enumerate(rows):
                for rx, c in enumerate(row):
                    if c == '#':
                        if shadow:
                            img.set_at((cx + rx + 1, ry + 1), shadow)
                        img.set_at((cx + rx, ry), colour)
            cx += len(rows[0]) + 1
        if scale != 1:
            img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
        if len(_glyph_cache) > 600:
            _glyph_cache.clear()
        _glyph_cache[key] = img
    surf.blit(img, (x, y))


# ------------------------------------------------------------------ high scores
class Scores:
    def __init__(self, save_dir):
        self.path = Path(save_dir) / "highscores.json"
        self.best = {}
        try:
            self.best = json.loads(self.path.read_text())
        except (OSError, ValueError):
            pass

    def get(self, game):
        return int(self.best.get(game, 0))

    def submit(self, game, score):
        """Records the score. Returns True if it's a new best."""
        if score > self.get(game):
            self.best[game] = int(score)
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(json.dumps(self.best, indent=1))
            except OSError:
                pass
            return True
        return False


# ------------------------------------------------------------------ the cabinet round the edge of your screen
def screen_rect(size):
    """Where the machine's screen goes inside the window (16:9, with room for the cabinet round it)."""
    w, h = size
    top, bottom, side = max(36, h // 18), max(30, h // 22), max(40, w // 20)
    sw, sh = w - 2 * side, h - top - bottom
    if sw * 9 > sh * 16:
        sw = sh * 16 // 9
    else:
        sh = sw * 9 // 16
    return pygame.Rect((w - sw) // 2, top + (h - top - bottom - sh) // 2, sw, sh)


_bezel_cache = {}


def bezel(size, machine, hint):
    """The cabinet: coloured body, chrome trim, the marquee with the game's name, control hints at the bottom."""
    key = (size, machine, hint)
    if key in _bezel_cache:
        return _bezel_cache[key]
    m = MACHINES[machine]
    w, h = size
    r = screen_rect(size)
    s = pygame.Surface(size, pygame.SRCALPHA)
    body, trim = m["body"], m["trim"]
    dark = tuple(int(c * 0.55) for c in body)
    s.fill(body)
    for i in range(0, h, 6):                                        # wood-grain / plastic texture
        pygame.draw.line(s, tuple(min(255, int(c * (0.92 + 0.08 * ((i // 6) % 2)))) for c in body), (0, i), (w, i), 2)
    pygame.draw.rect(s, dark, (0, 0, w, h), 10)                     # cabinet edge
    pygame.draw.rect(s, trim, (4, 4, w - 8, h - 8), 3)
    # the marquee along the top
    mq = pygame.Rect(r.x + r.w // 4, 3, r.w // 2, r.y - 8)
    pygame.draw.rect(s, (20, 20, 26), mq, border_radius=6)
    pygame.draw.rect(s, trim, mq, 2, border_radius=6)
    sc = max(2, (mq.h - 8) // 6)
    text(s, m["title"], mq.centerx, mq.y + (mq.h - 5 * sc) // 2, m["glow"], sc, centre=True, shadow=(10, 10, 14))
    # screen surround: dark glass edge + chrome
    pygame.draw.rect(s, (8, 8, 10), r.inflate(16, 16), border_radius=14)
    pygame.draw.rect(s, (150, 150, 160), r.inflate(20, 20), 2, border_radius=16)
    s.fill((0, 0, 0, 0), r)                                          # hole for the screen
    # control hints at the bottom
    hsc = max(2, (h - r.bottom - 12) // 6)
    text(s, hint, w // 2, r.bottom + (h - r.bottom - 5 * hsc) // 2 + 2, (235, 235, 240), hsc, centre=True, shadow=(0, 0, 0))
    s = s.convert_alpha()
    _bezel_cache[key] = s
    return s


_glass_cache = {}


def glass(size):
    """CRT look over the screen: faint scanlines and darker corners."""
    if size in _glass_cache:
        return _glass_cache[size]
    w, h = size
    g = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(0, h, 3):
        pygame.draw.line(g, (0, 0, 0, 34), (0, y), (w, y))
    for i in range(18):                                              # vignette
        a = int(70 * (1 - i / 18) ** 2)
        pygame.draw.rect(g, (0, 0, 0, a), (i * 2, i * 2, w - i * 4, h - i * 4), 2, border_radius=18)
    pygame.draw.line(g, (255, 255, 255, 18), (w * 0.08, h * 0.06), (w * 0.4, h * 0.06), 3)   # a little glare
    _glass_cache[size] = g
    return g


def present(window, canvas, machine, hint, smooth=False):
    """Draw the machine's screen into the window, inside the cabinet."""
    r = screen_rect(window.get_size())
    img = (pygame.transform.smoothscale if smooth else pygame.transform.scale)(canvas, r.size)
    window.blit(img, r)
    window.blit(glass(r.size), r)
    window.blit(bezel(window.get_size(), machine, hint), (0, 0))


# ================================================================== SEAGULL BIRD
def _gull_frames():
    """The gull: 16x12, wings up / level / down."""
    out = []
    W, G, D, Y, K, O = (250, 250, 252), (176, 184, 196), (120, 128, 140), (250, 196, 40), (30, 30, 36), (220, 110, 40)
    for wing in (-1, 0, 1):
        s = pygame.Surface((16, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(s, W, (2, 4, 11, 6))                    # body
        pygame.draw.rect(s, G, (1, 6, 4, 2))                        # tail
        pygame.draw.circle(s, W, (12, 5), 3)                        # head
        s.set_at((13, 4), K)                                        # eye
        pygame.draw.polygon(s, Y, [(14, 5), (16, 6), (14, 7)])      # beak
        s.set_at((15, 6), O)
        if wing < 0:
            pygame.draw.polygon(s, G, [(5, 6), (9, 6), (7, 0), (4, 1)]); pygame.draw.line(s, D, (4, 1), (7, 0))
        elif wing == 0:
            pygame.draw.polygon(s, G, [(4, 6), (10, 6), (8, 4), (2, 4)]); pygame.draw.line(s, D, (2, 4), (4, 4))
        else:
            pygame.draw.polygon(s, G, [(5, 6), (9, 6), (8, 11), (5, 10)]); pygame.draw.line(s, D, (5, 10), (8, 11))
        out.append(s)
    return out


def _cabot_tower(h):
    """Cabot Tower (Brandon Hill) - the obstacle growing up from the bottom. 28 wide."""
    s = pygame.Surface((28, h), pygame.SRCALPHA)
    stone, light, dark, mortar = (186, 120, 96), (210, 146, 118), (140, 88, 70), (160, 104, 84)
    pygame.draw.rect(s, stone, (4, 10, 20, h - 10))
    pygame.draw.rect(s, light, (4, 10, 4, h - 10)); pygame.draw.rect(s, dark, (20, 10, 4, h - 10))
    for y in range(14, h, 6):
        pygame.draw.line(s, mortar, (5, y), (22, y))
    for y in range(24, h - 6, 22):                                  # little arched windows
        pygame.draw.rect(s, (40, 36, 44), (12, y, 4, 7)); pygame.draw.circle(s, (40, 36, 44), (14, y), 2)
    pygame.draw.rect(s, (200, 196, 186), (1, 4, 26, 7))             # the balcony/battlements
    for x in range(1, 27, 4):
        pygame.draw.rect(s, (200, 196, 186), (x, 0, 2, 4))
    pygame.draw.rect(s, (120, 116, 110), (1, 10, 26, 2))
    return s


def _crane(h):
    """A harbourside crane (like the ones outside M Shed) hanging down from the top. 28 wide."""
    s = pygame.Surface((28, h), pygame.SRCALPHA)
    red, dred, blk = (190, 40, 36), (130, 24, 22), (36, 32, 36)
    pygame.draw.rect(s, red, (8, 0, 12, h - 16))
    for y in range(0, h - 18, 8):                                   # lattice
        pygame.draw.line(s, dred, (8, y), (19, y + 8)); pygame.draw.line(s, dred, (19, y), (8, y + 8))
    pygame.draw.rect(s, dred, (8, 0, 2, h - 16)); pygame.draw.rect(s, dred, (18, 0, 2, h - 16))
    pygame.draw.rect(s, blk, (2, h - 18, 24, 8))                    # cab
    pygame.draw.rect(s, (150, 190, 220), (5, h - 16, 6, 4))
    pygame.draw.line(s, blk, (14, h - 10), (14, h - 3))             # hook
    pygame.draw.arc(s, blk, (11, h - 6, 6, 6), 3.14, 6.28, 1)
    return s


class Seagull:
    id = "seagull"
    hint = "SPACE / UP / CLICK: FLAP     ESC: LEAVE MACHINE"
    GAP = 70

    def __init__(self, scores):
        self.scores = scores
        self.frames = _gull_frames()
        self.bg = self._backdrop()
        self.houses = self._houses()
        self.reset(); self.state = "title"

    def _backdrop(self):
        """Sky, the Avon Gorge and Clifton Suspension Bridge."""
        s = pygame.Surface((GW, GH))
        for y in range(GH):
            t = y / GH
            s.fill((int(120 + 120 * t), int(170 + 50 * t), int(230 - 30 * t)), (0, y, GW, 1))
        rock, rock2, tree = (150, 120, 100), (120, 96, 82), (70, 120, 70)
        pygame.draw.polygon(s, rock, [(0, 70), (60, 64), (92, 80), (110, 140), (110, GH), (0, GH)])
        pygame.draw.polygon(s, rock2, [(GW, 76), (300, 66), (276, 84), (262, 140), (262, GH), (GW, GH)])
        for x in range(0, 96, 7):
            pygame.draw.circle(s, tree, (x, 66 + (x * 7) % 5), 6)
        for x in range(282, GW, 7):
            pygame.draw.circle(s, tree, (x, 70 + (x * 3) % 5), 6)
        c, t = (60, 64, 74), (40, 44, 52)                            # the bridge
        for tx in (96, 272):
            pygame.draw.rect(s, (196, 186, 166), (tx - 6, 38, 12, 34)); pygame.draw.rect(s, (160, 150, 130), (tx - 6, 38, 12, 4))
            pygame.draw.rect(s, (120, 110, 100), (tx - 3, 50, 6, 12))
        pygame.draw.line(s, t, (90, 78), (278, 78), 3)               # deck
        for k in range(0, 177, 1):                                    # the chains
            x = 96 + k
            y = 40 + int(34 * (1 - ((k - 88) / 88) ** 2))
            s.set_at((x, y), c); s.set_at((x, y + 1), c)
            if k % 8 == 0:
                pygame.draw.line(s, c, (x, y), (x, 77))
        return s

    def _houses(self):
        """Cliftonwood's coloured houses on the hill - a strip that repeats as you fly."""
        s = pygame.Surface((256, 60), pygame.SRCALPHA)
        cols = [(236, 120, 150), (250, 200, 80), (120, 190, 220), (150, 210, 130), (240, 150, 90), (190, 150, 220), (245, 240, 230)]
        x = 0; i = 0
        while x < 256:
            w = 14 + (i * 5) % 8; hgt = 22 + (i * 7) % 12
            pygame.draw.rect(s, cols[i % len(cols)], (x, 60 - hgt, w, hgt))
            pygame.draw.polygon(s, (90, 70, 70), [(x - 1, 60 - hgt), (x + w // 2, 60 - hgt - 6), (x + w, 60 - hgt)])
            for wy in range(60 - hgt + 4, 56, 7):
                for wx in range(x + 3, x + w - 3, 5):
                    pygame.draw.rect(s, (60, 70, 90), (wx, wy, 2, 3))
            x += w; i += 1
        return s

    def reset(self):
        self.y, self.vy = GH * 0.45, 0.0
        self.t = 0.0; self.scroll = 0.0
        self.pipes = []; self.next_pipe = 0.6
        self.score = 0; self.new_best = False
        self.balloons = [[random.uniform(0, GW), random.uniform(20, 60), random.choice([(230, 60, 60), (250, 190, 40), (90, 160, 230)])] for _ in range(3)]

    def flap(self):
        if self.state == "title":
            self.state = "play"; self.reset()
        if self.state == "play":
            self.vy = -168
        elif self.state == "over" and self.t > 0.6:
            self.state = "play"; self.reset(); self.vy = -168

    def event(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w, pygame.K_RETURN):
            self.flap()
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.flap()

    def update(self, dt):
        self.t += dt
        for b in self.balloons:
            b[0] -= dt * 6
            if b[0] < -12: b[0] = GW + 12
        if self.state != "play":
            self.scroll += dt * 20
            return
        speed = 78 + min(40, self.score * 1.2)
        self.scroll += dt * speed
        self.vy = min(260, self.vy + 520 * dt)
        self.y += self.vy * dt
        self.next_pipe -= dt
        if self.next_pipe <= 0:
            gap = max(52, self.GAP - self.score // 3)
            cy = random.uniform(48, GH - 40 - 18)
            self.pipes.append([GW + 4, cy, gap, False])
            self.next_pipe = 1.7 * 78 / speed
        gull = pygame.Rect(60 - 6, int(self.y) - 4, 12, 8)
        for p in self.pipes:
            p[0] -= speed * dt
            top = pygame.Rect(int(p[0]) + 6, 0, 16, int(p[1] - p[2] / 2))
            bot = pygame.Rect(int(p[0]) + 5, int(p[1] + p[2] / 2), 18, GH)
            if gull.colliderect(top) or gull.colliderect(bot):
                self._die()
            if not p[3] and p[0] + 28 < 54:
                p[3] = True; self.score += 1
        self.pipes = [p for p in self.pipes if p[0] > -40]
        if self.y < 6:                                               # bump the top of the screen
            self.y, self.vy = 6, max(0.0, self.vy)
        if self.y > GH - 18:
            self._die()

    def _die(self):
        if self.state == "play":
            self.state = "over"; self.t = 0.0
            self.new_best = self.scores.submit(self.id, self.score)

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        for bx, by, col in self.balloons:                            # hot-air balloons over the gorge
            pygame.draw.circle(s, col, (int(bx), int(by)), 6)
            pygame.draw.line(s, (90, 70, 50), (int(bx) - 3, int(by) + 5), (int(bx) - 2, int(by) + 10))
            pygame.draw.line(s, (90, 70, 50), (int(bx) + 3, int(by) + 5), (int(bx) + 2, int(by) + 10))
            pygame.draw.rect(s, (120, 80, 40), (int(bx) - 2, int(by) + 10, 4, 3))
        hx = -int(self.scroll * 0.35) % 256
        for k in (-1, 0, 1):
            s.blit(self.houses, (hx + k * 256, GH - 74))
        for p in self.pipes:                                         # cranes from the top, Cabot Tower from below
            th = int(p[1] - p[2] / 2)
            if th > 4:
                s.blit(_crane_cached(th), (int(p[0]), 0))
            bh = GH - 14 - int(p[1] + p[2] / 2)
            if bh > 4:
                s.blit(_tower_cached(bh), (int(p[0]), int(p[1] + p[2] / 2)))
        # the harbour along the bottom
        pygame.draw.rect(s, (40, 90, 130), (0, GH - 16, GW, 16))
        off = int(self.scroll) % 12
        for x in range(-off, GW, 12):
            pygame.draw.line(s, (120, 180, 220), (x, GH - 13 + (x // 12) % 2 * 4), (x + 5, GH - 13 + (x // 12) % 2 * 4))
        pygame.draw.rect(s, (110, 100, 90), (0, GH - 18, GW, 3))
        f = self.frames[int(self.t * 10) % 3] if self.state == "play" and self.vy < 60 else self.frames[1]
        ang = max(-30, min(60, self.vy / 4)) if self.state != "title" else math.sin(self.t * 3) * 8
        img = pygame.transform.rotate(f, -ang)
        gy = self.y if self.state != "title" else GH * 0.45 + math.sin(self.t * 3) * 6
        s.blit(img, img.get_rect(center=(60, int(gy))))
        if self.state == "play":
            text(s, str(self.score), GW // 2, 10, (255, 255, 255), 3, centre=True, shadow=(30, 40, 60))
        elif self.state == "title":
            _panel(s, "SEAGULL BIRD", ["FLY THE GULL ROUND BRISTOL", "DODGE THE CRANES AND CABOT TOWER", "",
                                       "PRESS SPACE TO FLAP"], self.scores.get(self.id), (250, 214, 70))
        else:
            _game_over(s, self.score, self.scores.get(self.id), self.new_best, "SPACE TO FLY AGAIN")


_tower_c, _crane_c = {}, {}


def _tower_cached(h):
    h = max(12, h)
    if h not in _tower_c:
        _tower_c[h] = _cabot_tower(h)
    return _tower_c[h]


def _crane_cached(h):
    h = max(20, h)
    if h not in _crane_c:
        _crane_c[h] = _crane(h)
    return _crane_c[h]


def _panel(s, title, lines, best, colour):
    """Title card for a machine's attract screen."""
    w = max(text_w(title, 3), max(text_w(l) for l in lines)) + 28
    h = 26 + 9 * len(lines) + 22
    r = pygame.Rect((GW - w) // 2, (GH - h) // 2, w, h)
    sh = pygame.Surface(r.size, pygame.SRCALPHA); sh.fill((10, 12, 20, 200)); s.blit(sh, r)
    pygame.draw.rect(s, colour, r, 1)
    text(s, title, GW // 2, r.y + 7, colour, 3, centre=True, shadow=(0, 0, 0))
    for i, l in enumerate(lines):
        text(s, l, GW // 2, r.y + 30 + i * 9, (235, 235, 240), 1, centre=True)
    text(s, f"HI-SCORE {best}", GW // 2, r.bottom - 12, (255, 220, 90), 1, centre=True)


def _game_over(s, score, best, new_best, again):
    r = pygame.Rect(GW // 2 - 90, GH // 2 - 40, 180, 80)
    sh = pygame.Surface(r.size, pygame.SRCALPHA); sh.fill((10, 12, 20, 210)); s.blit(sh, r)
    pygame.draw.rect(s, (255, 255, 255), r, 1)
    text(s, "GAME OVER", GW // 2, r.y + 8, (255, 90, 80), 2, centre=True, shadow=(0, 0, 0))
    text(s, f"SCORE {score}", GW // 2, r.y + 30, (255, 255, 255), 1, centre=True)
    if new_best and (pygame.time.get_ticks() // 300) % 2 == 0:
        text(s, "NEW HI-SCORE!", GW // 2, r.y + 42, (255, 220, 90), 1, centre=True)
    elif not new_best:
        text(s, f"HI-SCORE {best}", GW // 2, r.y + 42, (255, 220, 90), 1, centre=True)
    text(s, again, GW // 2, r.y + 62, (170, 200, 255), 1, centre=True)


# ================================================================== HOOP SHOT
class Hoops:
    """Side-on basketball. Drag back from the ball and let go to shoot (or aim with the arrows and hold SPACE)."""
    id = "hoops"
    hint = "DRAG BACK + LET GO  -  OR ARROWS + HOLD SPACE     ESC: LEAVE MACHINE"
    R = 6                                   # ball radius
    G = 430                                 # gravity, px/s^2
    FLOOR = GH - 22
    BOARD_X, BOARD_TOP, BOARD_BOT = 352, 54, 104
    RIM_Y, RIM_FRONT, RIM_BACK = 92, 318, 348
    ROUND = 60.0

    def __init__(self, scores):
        self.scores = scores
        self.court = self._court()
        self.state = "title"; self.t = 0.0
        self.reset()

    def _court(self):
        s = pygame.Surface((GW, GH))
        for y in range(GH - 22):                                      # dusk sky over a harbourside court
            t = y / GH
            s.fill((int(40 + 60 * t), int(40 + 50 * t), int(90 + 40 * t)), (0, y, GW, 1))
        for i, (x, w, h, col) in enumerate([(0, 40, 70, (60, 56, 80)), (36, 50, 96, (70, 64, 90)), (82, 36, 60, (56, 52, 74)),
                                            (114, 60, 110, (66, 60, 86)), (170, 44, 80, (60, 56, 80)), (210, 70, 100, (72, 66, 92))]):
            pygame.draw.rect(s, col, (x, GH - 22 - h, w, h))
            for wy in range(GH - 22 - h + 6, GH - 30, 9):
                for wx in range(x + 4, x + w - 4, 8):
                    if (wx * 7 + wy * 3) % 5 < 3:
                        pygame.draw.rect(s, (250, 210, 120), (wx, wy, 3, 4))
        wall = pygame.Rect(250, GH - 22 - 120, GW - 250, 120)       # graffiti wall behind the hoop
        pygame.draw.rect(s, (110, 74, 64), wall)
        for y in range(wall.y, wall.bottom, 6):
            pygame.draw.line(s, (96, 64, 56), (wall.x, y), (wall.right, y))
        for i, col in enumerate([(240, 90, 160), (90, 210, 240), (250, 210, 60), (120, 230, 120)]):
            pygame.draw.circle(s, col, (270 + i * 26, GH - 60 + (i % 2) * 14), 10, 3)
        text(s, "BRISTOL", 262, GH - 100, (250, 210, 60), 2, shadow=(40, 20, 20))
        pygame.draw.rect(s, (170, 96, 50), (0, GH - 22, GW, 22))      # court floor
        for x in range(0, GW, 24):
            pygame.draw.line(s, (150, 82, 42), (x, GH - 22), (x - 10, GH))
        pygame.draw.line(s, (240, 240, 240), (0, GH - 22), (GW, GH - 22), 2)
        pygame.draw.rect(s, (90, 90, 96), (self.BOARD_X + 6, self.BOARD_TOP, 4, GH - 22 - self.BOARD_TOP))   # pole
        return s

    def reset(self):
        self.score = 0; self.streak = 0; self.time = self.ROUND; self.new_best = False
        self.popups = []; self.new_ball()

    def new_ball(self):
        self.bx = random.uniform(40, 220); self.by = self.FLOOR - self.R
        self.vx = self.vy = 0.0
        self.flying = False; self.scored = False; self.air_t = 0.0
        self.aim_angle, self.aim_power = 52.0, 0.55
        self.drag = None; self.charging = False; self.prev_y = self.by
        self.net_wobble = 0.0

    # --- input
    def event(self, ev):
        if self.state != "play":
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_RETURN) or \
                    ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.state == "title" or self.t > 0.8:
                    self.state = "play"; self.reset()
            return
        if self.flying:
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.drag = (ev.pos, ev.pos)
        elif ev.type == pygame.MOUSEMOTION and self.drag:
            self.drag = (self.drag[0], ev.pos)
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.drag:
            (x0, y0), (x1, y1) = self.drag
            self.drag = None
            dx, dy = x0 - x1, y0 - y1
            if math.hypot(dx, dy) > 6:
                self._shoot(dx * 4.2, dy * 4.2)
        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
            self.charging = True; self.aim_power = 0.2
        elif ev.type == pygame.KEYUP and ev.key == pygame.K_SPACE and self.charging:
            self.charging = False
            v = 140 + 300 * self.aim_power; a = math.radians(self.aim_angle)
            self._shoot(math.cos(a) * v, -math.sin(a) * v)

    def _shoot(self, vx, vy):
        sp = math.hypot(vx, vy)
        if sp > 470:
            vx, vy = vx * 470 / sp, vy * 470 / sp
        self.vx, self.vy = vx, vy
        self.flying = True; self.air_t = 0.0; self.scored = False

    def _launch_velocity(self):
        if self.drag:
            (x0, y0), (x1, y1) = self.drag
            vx, vy = (x0 - x1) * 4.2, (y0 - y1) * 4.2
        else:
            v = 140 + 300 * self.aim_power; a = math.radians(self.aim_angle)
            vx, vy = math.cos(a) * v, -math.sin(a) * v
        sp = math.hypot(vx, vy)
        if sp > 470:
            vx, vy = vx * 470 / sp, vy * 470 / sp
        return vx, vy

    # --- physics
    def _collide_point(self, px, py, bounce=0.72):
        dx, dy = self.bx - px, self.by - py
        d = math.hypot(dx, dy)
        if d < self.R + 1 and d > 0:
            nx, ny = dx / d, dy / d
            self.bx, self.by = px + nx * (self.R + 1), py + ny * (self.R + 1)
            vn = self.vx * nx + self.vy * ny
            if vn < 0:
                self.vx -= (1 + bounce) * vn * nx; self.vy -= (1 + bounce) * vn * ny
                self.vx *= 0.96
                self.net_wobble = 0.4

    def update(self, dt):
        self.t += dt
        for p in self.popups:
            p[2] -= dt; p[1] -= dt * 20
        self.popups = [p for p in self.popups if p[2] > 0]
        if self.state != "play":
            return
        self.time -= dt
        if self.time <= 0 and not self.flying:
            self.time = 0; self.state = "over"; self.t = 0.0
            self.new_best = self.scores.submit(self.id, self.score)
            return
        keys = pygame.key.get_pressed()
        if not self.flying:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.aim_angle = min(85, self.aim_angle + 40 * dt)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.aim_angle = max(15, self.aim_angle - 40 * dt)
            if keys[pygame.K_UP] or keys[pygame.K_w]: self.aim_power = min(1, self.aim_power + 0.6 * dt)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.aim_power = max(0.1, self.aim_power - 0.6 * dt)
            if self.charging:
                self.aim_power = 0.2 + 0.8 * (0.5 - 0.5 * math.cos(self.t * 3.2))
            return
        self.net_wobble = max(0, self.net_wobble - dt)
        self.air_t += dt
        steps = 6
        for _ in range(steps):
            h = dt / steps
            self.prev_y = self.by
            self.vy += self.G * h
            self.bx += self.vx * h; self.by += self.vy * h
            # backboard (a thick vertical line)
            if self.BOARD_TOP - self.R < self.by < self.BOARD_BOT + self.R and self.bx + self.R > self.BOARD_X and self.bx < self.BOARD_X + 6:
                if self.vx > 0:
                    self.bx = self.BOARD_X - self.R; self.vx = -self.vx * 0.7
            self._collide_point(self.RIM_FRONT, self.RIM_Y)            # front of the rim
            self._collide_point(self.RIM_BACK, self.RIM_Y)             # back of the rim (at the board)
            # through the hoop, going down?
            if not self.scored and self.prev_y < self.RIM_Y <= self.by and self.vy > 0 and \
                    self.RIM_FRONT + 2 < self.bx < self.RIM_BACK - 2:
                self.scored = True; self.streak += 1
                pts = 2 * self.streak
                self.score += pts; self.net_wobble = 0.6
                self.popups.append([self.bx, self.RIM_Y - 10, 1.2, f"+{pts}" + (f"  x{self.streak} STREAK!" if self.streak > 1 else "")])
            if self.by > self.FLOOR - self.R:                          # floor
                self.by = self.FLOOR - self.R
                self.vy = -self.vy * 0.62; self.vx *= 0.85
                if abs(self.vy) < 30: self.vy = 0
            if self.bx < self.R:
                self.bx = self.R; self.vx = -self.vx * 0.7
            if self.bx > GW - self.R:
                self.bx = GW - self.R; self.vx = -self.vx * 0.7
        resting = self.by >= self.FLOOR - self.R - 0.5 and abs(self.vy) < 1 and abs(self.vx) < 12
        if resting or self.air_t > 4.5:
            if not self.scored:
                if self.streak > 1:
                    self.popups.append([self.bx, self.by - 14, 1.0, "STREAK LOST"])
                self.streak = 0
            self.new_ball()

    def draw(self, s):
        s.blit(self.court, (0, 0))
        bb = pygame.Rect(self.BOARD_X, self.BOARD_TOP, 6, self.BOARD_BOT - self.BOARD_TOP)
        pygame.draw.rect(s, (240, 240, 245), bb); pygame.draw.rect(s, (200, 40, 40), (bb.x + 1, self.RIM_Y - 16, 3, 14), 1)
        # net
        wob = math.sin(self.t * 30) * 2 * self.net_wobble
        for i in range(7):
            x0 = self.RIM_FRONT + i * (self.RIM_BACK - self.RIM_FRONT) / 6
            x1 = self.RIM_FRONT + 6 + i * (self.RIM_BACK - self.RIM_FRONT - 12) / 6 + wob
            pygame.draw.line(s, (235, 235, 240), (x0, self.RIM_Y), (x1, self.RIM_Y + 16))
        for k in (6, 11, 16):
            pygame.draw.line(s, (220, 220, 228), (self.RIM_FRONT + k * 0.35 + wob, self.RIM_Y + k), (self.RIM_BACK - k * 0.35 + wob, self.RIM_Y + k))
        # ball
        bx, by = int(self.bx), int(self.by)
        pygame.draw.circle(s, (230, 110, 30), (bx, by), self.R)
        pygame.draw.circle(s, (120, 50, 10), (bx, by), self.R, 1)
        rot = (self.bx / self.R)
        pygame.draw.line(s, (120, 50, 10), (bx + math.cos(rot) * self.R, by + math.sin(rot) * self.R), (bx - math.cos(rot) * self.R, by - math.sin(rot) * self.R))
        pygame.draw.line(s, (255, 170, 90), (bx - 2, by - 3), (bx, by - 4))
        pygame.draw.line(s, (220, 60, 40), (self.RIM_FRONT, self.RIM_Y), (self.RIM_BACK, self.RIM_Y), 2)   # rim in front
        # aim guide
        if self.state == "play" and not self.flying:
            vx, vy = self._launch_velocity()
            x, y = self.bx, self.by
            for i in range(26):
                for _ in range(3):
                    vy += self.G * 0.012; x += vx * 0.012; y += vy * 0.012
                if i % 2 == 0 and y < self.FLOOR:
                    s.fill((255, 255, 255), (int(x), int(y), 2, 2))
            if not self.drag:
                pygame.draw.rect(s, (30, 30, 40), (10, GH - 16, 60, 6))
                pygame.draw.rect(s, (90, 230, 120) if self.aim_power < 0.75 else (250, 200, 60), (11, GH - 15, int(58 * self.aim_power), 4))
        for x, y, life, msg in self.popups:
            text(s, msg, int(x) - 30, int(y), (255, 230, 90) if "LOST" not in msg else (255, 120, 110), 1, shadow=(0, 0, 0))
        # scoreboard
        pygame.draw.rect(s, (16, 16, 22), (GW // 2 - 76, 4, 152, 20))
        text(s, f"{self.score:04d}", GW // 2 - 66, 8, (255, 90, 70), 2)
        text(s, f"{int(math.ceil(self.time)):02d}", GW // 2 + 30, 8, (255, 220, 80), 2)
        if self.streak > 1:
            text(s, f"x{self.streak} STREAK", GW // 2, 28, (255, 230, 90), 1, centre=True, shadow=(0, 0, 0))
        if self.state == "title":
            _panel(s, "HOOP SHOT", ["60 SECONDS ON THE CLOCK", "DRAG BACK FROM THE BALL AND LET GO",
                                    "OR AIM WITH ARROWS AND HOLD SPACE", "BASKETS IN A ROW SCORE MORE: 2 4 6 8..."],
                   self.scores.get(self.id), (255, 160, 60))
        elif self.state == "over":
            _game_over(s, self.score, self.scores.get(self.id), self.new_best, "SPACE / CLICK TO PLAY AGAIN")


# ================================================================== INVADERS
_INV = {
    0: ["..#..#..", "...##...", "..####..", ".##..##.", "########", "#.####.#", "#......#", ".#....#."],
    1: ["..#..#..", "#..##..#", "#.####.#", "###..###", "########", ".######.", "..#..#..", ".#....#."],
    2: ["...##...", "..####..", ".######.", "##.##.##", "########", "..#..#..", ".#.##.#.", "#.#..#.#"],
    3: ["...##...", "..####..", ".######.", "##.##.##", "########", ".#.##.#.", "#......#", ".#....#."],
    4: ["..####..", ".######.", "########", "##.##.##", "########", "..#..#..", ".#.##.#.", "..#..#.."],
    5: ["..####..", ".######.", "########", "##.##.##", "########", ".##..##.", "##....##", "..#..#.."],
}


def _sprite(rows, col, scale=1):
    s = pygame.Surface((len(rows[0]), len(rows)), pygame.SRCALPHA)
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c == '#':
                s.set_at((x, y), col)
    return pygame.transform.scale(s, (s.get_width() * scale, s.get_height() * scale)) if scale != 1 else s


class Invaders:
    id = "invaders"
    hint = "LEFT/RIGHT: MOVE     SPACE: FIRE     ESC: LEAVE MACHINE"
    COLS, ROWS = 11, 5

    def __init__(self, scores):
        self.scores = scores
        cols = [(255, 90, 200), (90, 220, 255), (90, 220, 255), (120, 255, 120), (120, 255, 120)]
        self.inv_img = {}
        for row in range(5):
            kind = 0 if row == 0 else (1 if row < 3 else 2)
            base = {0: (2, 3), 1: (0, 1), 2: (4, 5)}[kind]
            self.inv_img[row] = [_sprite(_INV[base[0]], cols[row]), _sprite(_INV[base[1]], cols[row])]
        self.ship = _sprite(["...#...", "..###..", ".#####.", "#######", "#######"], (120, 255, 140))
        self.ufo = _sprite(["...####...", ".########.", "##.##.##.#", "##########", "..#....#.."], (255, 80, 80))
        self.stars = [(random.randrange(GW), random.randrange(GH), random.choice([60, 100, 160])) for _ in range(70)]
        self.state = "title"; self.t = 0.0
        self.score = 0; self.lives = 3; self.wave = 0; self.new_best = False
        self.start_wave()

    def start_wave(self):
        self.aliens = [[c, r, True] for r in range(self.ROWS) for c in range(self.COLS)]
        self.ox, self.oy = 60.0, 34.0 + min(5, self.wave) * 6
        self.dir = 1; self.step_t = 0.0; self.anim = 0
        self.px = GW / 2; self.shot = None; self.bombs = []
        self.ufo_x = None; self.ufo_t = random.uniform(12, 22)
        self.dead_t = 0.0; self.booms = []
        self.bunkers = []
        for k in range(4):                                           # four bunkers made of little blocks you can chip away
            bx = 60 + k * 82
            for y in range(12):
                for x in range(22):
                    if y < 3 and (x < 3 - y or x > 18 + y):
                        continue
                    if y > 8 and 6 < x < 15:
                        continue
                    self.bunkers.append(pygame.Rect(bx + x, GH - 52 + y, 1, 1))

    def alive(self):
        return [a for a in self.aliens if a[2]]

    def pos(self, a):
        return self.ox + a[0] * 20, self.oy + a[1] * 14

    def event(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_UP, pygame.K_w):
            if self.state == "title" or (self.state == "over" and self.t > 0.8):
                self.score = 0; self.lives = 3; self.wave = 0; self.new_best = False
                self.state = "play"; self.start_wave()
            elif self.state == "play" and self.shot is None and self.dead_t <= 0:
                self.shot = [self.px, GH - 26]

    def update(self, dt):
        self.t += dt
        for b in self.booms:
            b[2] -= dt
        self.booms = [b for b in self.booms if b[2] > 0]
        if self.state != "play":
            return
        if self.dead_t > 0:
            self.dead_t -= dt
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.px = max(10, self.px - 110 * dt)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.px = min(GW - 10, self.px + 110 * dt)
        alive = self.alive()
        if not alive:
            self.wave += 1; self.start_wave(); return
        # the march: faster as there are fewer of them
        self.step_t -= dt
        if self.step_t <= 0:
            self.step_t = max(0.04, 0.6 * len(alive) / (self.COLS * self.ROWS)) * (0.85 ** min(5, self.wave))
            self.anim ^= 1
            xs = [self.pos(a)[0] for a in alive]
            if (self.dir > 0 and max(xs) + 12 + 4 > GW - 6) or (self.dir < 0 and min(xs) - 4 < 6):
                self.dir = -self.dir; self.oy += 6
            else:
                self.ox += 4 * self.dir
        # bombs from the bottom alien in a random column
        if random.random() < dt * (0.9 + 0.25 * self.wave):
            col = random.choice(alive)[0]
            low = max((a for a in alive if a[0] == col), key=lambda a: a[1])
            x, y = self.pos(low)
            self.bombs.append([x + 4, y + 8])
        # UFO
        self.ufo_t -= dt
        if self.ufo_x is None and self.ufo_t <= 0:
            self.ufo_x = -12.0; self.ufo_t = random.uniform(15, 25)
        if self.ufo_x is not None:
            self.ufo_x += 50 * dt
            if self.ufo_x > GW + 12: self.ufo_x = None
        # your shot
        if self.shot:
            self.shot[1] -= 260 * dt
            sr = pygame.Rect(int(self.shot[0]), int(self.shot[1]), 1, 5)
            if self.shot[1] < 10:
                self.shot = None
            else:
                hit = sr.collidelist(self.bunkers)
                if hit >= 0:
                    self._chip(self.bunkers[hit].center); self.shot = None
            if self.shot:
                for a in alive:
                    x, y = self.pos(a)
                    if sr.colliderect(pygame.Rect(x, y, 8, 8)):
                        a[2] = False; self.shot = None
                        self.score += (30, 20, 20, 10, 10)[a[1]]
                        self.booms.append([x + 4, y + 4, 0.25]); break
            if self.shot and self.ufo_x is not None and sr.colliderect(pygame.Rect(int(self.ufo_x), 14, 10, 5)):
                pts = random.choice([50, 100, 150, 300]); self.score += pts
                self.booms.append([self.ufo_x + 5, 16, 0.6]); self.ufo_x = None; self.shot = None
        # bombs
        ship = pygame.Rect(int(self.px) - 4, GH - 22, 7, 5)
        for b in self.bombs:
            b[1] += 110 * dt
        keep = []
        for b in self.bombs:
            br = pygame.Rect(int(b[0]), int(b[1]), 1, 4)
            hit = br.collidelist(self.bunkers)
            if hit >= 0:
                self._chip(self.bunkers[hit].center); continue
            if br.colliderect(ship):
                self.lives -= 1; self.booms.append([self.px, GH - 20, 0.8]); self.dead_t = 1.2; self.bombs = []
                if self.lives <= 0:
                    self._over()
                return
            if b[1] < GH:
                keep.append(b)
        self.bombs = keep
        # they reached you
        if any(self.pos(a)[1] + 8 >= GH - 26 for a in alive):
            self.lives = 0; self._over()

    def _chip(self, c):
        self.bunkers = [b for b in self.bunkers if (b.x - c[0]) ** 2 + (b.y - c[1]) ** 2 > 5 or random.random() < 0.25]

    def _over(self):
        self.state = "over"; self.t = 0.0
        self.new_best = self.scores.submit(self.id, self.score)

    def draw(self, s):
        s.fill((4, 4, 12))
        for x, y, b in self.stars:
            s.set_at((x, y), (b, b, b + 20))
        for a in self.alive():
            x, y = self.pos(a)
            s.blit(self.inv_img[a[1]][self.anim], (int(x), int(y)))
        for b in self.bunkers:
            s.fill((80, 230, 90), b)
        if self.ufo_x is not None:
            s.blit(self.ufo, (int(self.ufo_x), 14))
        if self.shot:
            s.fill((255, 255, 255), (int(self.shot[0]), int(self.shot[1]), 1, 5))
        for b in self.bombs:
            off = int(self.t * 20) % 2
            s.fill((255, 240, 120), (int(b[0]) + off, int(b[1]), 1, 2)); s.fill((255, 240, 120), (int(b[0]) + 1 - off, int(b[1]) + 2, 1, 2))
        for x, y, life in self.booms:
            for k in range(8):
                a = k * math.pi / 4
                r = 6 * (1 - life)
                s.set_at((int(x + math.cos(a) * r), int(y + math.sin(a) * r)), (255, 220, 120))
        if self.state == "play" and (self.dead_t <= 0 or int(self.t * 10) % 2):
            s.blit(self.ship, (int(self.px) - 3, GH - 22))
        pygame.draw.line(s, (80, 230, 90), (0, GH - 14), (GW, GH - 14))
        text(s, f"SCORE {self.score}", 8, 4, (255, 255, 255))
        text(s, f"HI-SCORE {max(self.score, self.scores.get(self.id))}", GW // 2, 4, (255, 220, 90), centre=True)
        for i in range(max(0, self.lives - 1)):
            s.blit(self.ship, (GW - 30 + i * 10, GH - 10))
        text(s, f"LIVES {self.lives}", 8, GH - 10, (120, 255, 140))
        if self.state == "title":
            _panel(s, "INVADERS", ["DEFEND BRISTOL FROM SPACE", "LEFT / RIGHT TO MOVE  SPACE TO FIRE", "",
                                   "30  20  10 POINTS   UFO = MYSTERY"], self.scores.get(self.id), (90, 255, 120))
        elif self.state == "over":
            _game_over(s, self.score, self.scores.get(self.id), self.new_best, "SPACE TO PLAY AGAIN")


GAMES = {"seagull": Seagull, "hoops": Hoops, "invaders": Invaders}


# ================================================================== running a machine
def _to_screen_coords(pos, window_size, w, h):
    r = screen_rect(window_size)
    return (int((pos[0] - r.x) * w / r.w), int((pos[1] - r.y) * h / r.h))


def play(window, clock, machine, save_dir, base_dir, goal=None):
    """Play a machine until you leave it. Returns 'quit' if the window was closed.
    goal = (score, label): a score to beat for the story (e.g. John's high score). Once a game ends with a score
    above it, the machine shows it for a moment and play() returns 'won'."""
    if machine == "kombat":
        return play_kombat(window, clock, Path(base_dir) / "mvb_kombat")
    scores = Scores(save_dir)
    game = GAMES[machine](scores)
    canvas = pygame.Surface((GW, GH)).convert()
    pygame.key.set_repeat()
    won_t = None
    while True:
        dt = min(clock.tick(60) / 1000, 0.05)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return None
            if won_t is not None:
                continue
            if hasattr(ev, "pos") and ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                ev = pygame.event.Event(ev.type, dict(ev.dict, pos=_to_screen_coords(ev.pos, window.get_size(), GW, GH)))
            game.event(ev)
        if won_t is None:
            game.update(dt)
        game.draw(canvas)
        if goal:
            score, label = goal
            if won_t is None and getattr(game, "state", None) == "over" and game.score > score:
                won_t = 0.0
            if won_t is not None:
                won_t += dt
                r = pygame.Rect(GW // 2 - 90, GH // 2 - 22, 180, 44)
                canvas.fill((20, 20, 30), r); pygame.draw.rect(canvas, (255, 220, 90), r, 1)
                text(canvas, "NEW HIGH SCORE!", GW // 2, r.y + 10, (255, 220, 90), 1, centre=True)
                text(canvas, f"YOU BEAT {label}", GW // 2, r.y + 26, (240, 240, 240), 1, centre=True)
                if won_t > 2.2:
                    return "won"
            else:
                text(canvas, f"TO BEAT: {label} {score}", GW - 4 - text_w(f"TO BEAT: {label} {score}"), 4, (255, 220, 90), 1,
                     shadow=(20, 20, 30))
        window.fill((0, 0, 0))
        present(window, canvas, machine, game.hint)
        pygame.display.flip()


class _Leave(Exception):
    pass


def play_kombat(window, clock, folder):
    """Runs MVB Kombat inside the machine: its window becomes the machine's screen.
    The game's own code isn't changed - it draws to an off-screen 1024x576 picture that we show in the cabinet."""
    folder = Path(folder)
    src = folder / "game.py"
    if not src.is_file():
        return _missing(window, clock, "kombat", f"MVB KOMBAT ISN'T INSTALLED")
    KW, KH = 1024, 576
    off = pygame.Surface((KW, KH)).convert()
    hint = "ESC: PAUSE     BACKSPACE: LEAVE MACHINE"
    real = dict(set_mode=pygame.display.set_mode, update=pygame.display.update, flip=pygame.display.flip,
                get=pygame.event.get, get_pos=pygame.mouse.get_pos, quit=pygame.quit, caption=pygame.display.get_caption(),
                set_caption=pygame.display.set_caption)
    state = {"quit": False}

    def to_k(pos):
        return _to_screen_coords(pos, window.get_size(), KW, KH)

    def get_events(*a, **k):
        out = []
        for ev in real["get"](*a, **k):
            if ev.type == pygame.QUIT:
                state["quit"] = True; raise _Leave()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_BACKSPACE:
                raise _Leave()
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                ev = pygame.event.Event(ev.type, dict(ev.dict, pos=to_k(ev.pos)))
            out.append(ev)
        return out

    def show(*a, **k):
        window.fill((0, 0, 0))
        present(window, off, "kombat", hint, smooth=False)
        real["flip"]()

    old_cwd = os.getcwd()
    try:
        pygame.display.set_mode = lambda *a, **k: off
        pygame.display.update = show
        pygame.display.flip = show
        pygame.event.get = get_events
        pygame.mouse.get_pos = lambda: to_k(real["get_pos"]())
        pygame.quit = lambda: None
        pygame.display.set_caption = lambda *a, **k: None
        os.chdir(folder)
        sys.path.insert(0, str(folder))
        code = compile(src.read_text(encoding="utf-8"), str(src), "exec")
        exec(code, {"__name__": "mvb_kombat", "__file__": str(src)})
    except (_Leave, SystemExit):
        pass
    finally:
        os.chdir(old_cwd)
        if sys.path and sys.path[0] == str(folder):
            sys.path.pop(0)
        pygame.display.set_mode = real["set_mode"]; pygame.display.update = real["update"]; pygame.display.flip = real["flip"]
        pygame.event.get = real["get"]; pygame.mouse.get_pos = real["get_pos"]; pygame.quit = real["quit"]
        pygame.display.set_caption = real["set_caption"]
        pygame.display.set_caption(*real["caption"][:1])
        try:
            pygame.mixer.music.stop(); pygame.mixer.music.unload()
            pygame.mixer.stop()
        except pygame.error:
            pass
        try:                                                         # forget MVB Kombat's sliders and toggles
            from pygame_widgets.widget import WidgetHandler
            WidgetHandler._widgets.clear()
        except Exception:
            pass
    return "quit" if state["quit"] else None


def _missing(window, clock, machine, msg):
    canvas = pygame.Surface((GW, GH)).convert()
    while True:
        clock.tick(30)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type == pygame.KEYDOWN:
                return None
        canvas.fill((0, 0, 30))
        text(canvas, msg, GW // 2, GH // 2 - 10, (255, 255, 255), 1, centre=True)
        text(canvas, "PRESS ANY KEY", GW // 2, GH // 2 + 6, (150, 170, 255), 1, centre=True)
        present(window, canvas, machine, "ESC: LEAVE MACHINE")
        pygame.display.flip()


# ================================================================== the machines as they stand in the arcade
def cabinet(machine, frame=0, px=4):
    """A machine in the arcade, seen from the front at the game's three-quarter angle: name on the marquee,
    the game playing on its screen. 22 x 40 art pixels, scaled by px."""
    m = MACHINES[machine]
    W, H = 22, 40
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    body, trim, glow = m["body"], m["trim"], m["glow"]
    dark = tuple(int(c * 0.6) for c in body)
    ol = (24, 20, 26)
    pygame.draw.rect(s, ol, (0, 0, W, H))
    pygame.draw.rect(s, body, (1, 1, W - 2, H - 2))
    pygame.draw.rect(s, dark, (1, 1, 2, H - 2)); pygame.draw.rect(s, dark, (W - 3, 1, 2, H - 2))
    # marquee (lit)
    pygame.draw.rect(s, (16, 16, 22), (2, 2, W - 4, 7))
    pygame.draw.rect(s, glow, (2, 2, W - 4, 1))
    # screen
    pygame.draw.rect(s, (10, 10, 14), (3, 11, W - 6, 13))
    scr = pygame.Rect(4, 12, W - 8, 11)
    _mini_screen(s, machine, scr, frame)
    # control panel
    pygame.draw.polygon(s, trim, [(1, 26), (W - 1, 26), (W - 1, 30), (1, 30)])
    pygame.draw.rect(s, (30, 30, 34), (5, 27, 2, 2)); s.set_at((6, 26), (220, 40, 40))     # joystick
    for i, c in enumerate([(240, 60, 60), (60, 140, 240), (250, 210, 60)]):
        s.set_at((11 + i * 3, 28), c)
    pygame.draw.rect(s, dark, (2, 31, W - 4, H - 33))
    pygame.draw.rect(s, (30, 26, 30), (W // 2 - 3, 33, 6, 4))                                 # coin slot
    s.fill((250, 210, 60), (W // 2 - 1, 34, 2, 2))
    img = pygame.transform.scale(s, (W * px, H * px))
    # the name on the marquee, in proper pixel letters on top
    name = m["short"]
    sc = 1 if text_w(name) > (W - 6) else 1
    lab = pygame.Surface((text_w(name) + 2, 7), pygame.SRCALPHA)
    text(lab, name, 0, 0, glow, 1, shadow=(0, 0, 0))
    lw = min(lab.get_width() * px // 2, (W - 4) * px)
    lab = pygame.transform.scale(lab, (lw, int(lab.get_height() * lw / lab.get_width())))
    img.blit(lab, ((W * px - lw) // 2, 2 * px + (7 * px - lab.get_height()) // 2))
    return img


def _mini_screen(s, machine, r, frame):
    """A tiny version of each game playing on the machine's screen."""
    if machine == "seagull":
        s.fill((120, 180, 236), r)
        s.fill((40, 90, 130), (r.x, r.bottom - 2, r.w, 2))
        tx = r.x + 9 - frame % 4
        s.fill((186, 120, 96), (tx, r.y + 6, 3, 5)); s.fill((190, 40, 36), (tx, r.y, 3, 3))
        gy = r.y + 4 + (1 if frame % 2 else 0)
        s.fill((255, 255, 255), (r.x + 3, gy, 3, 2)); s.set_at((r.x + 6, gy), (250, 196, 40))
    elif machine == "hoops":
        s.fill((60, 50, 90), r)
        s.fill((170, 96, 50), (r.x, r.bottom - 2, r.w, 2))
        s.fill((240, 240, 245), (r.right - 2, r.y + 1, 1, 5)); s.fill((220, 60, 40), (r.right - 5, r.y + 4, 3, 1))
        bx = r.x + 2 + frame % 8; by = r.y + 8 - [0, 2, 3, 4, 4, 3, 2, 0][frame % 8]
        s.fill((230, 110, 30), (bx, by, 2, 2))
    elif machine == "invaders":
        s.fill((4, 4, 12), r)
        for i in range(4):
            for j in range(2):
                s.fill((120, 255, 120) if j else (255, 90, 200), (r.x + 2 + i * 3 + frame % 2, r.y + 1 + j * 3, 2, 2))
        s.fill((120, 255, 140), (r.x + 4 + frame % 6, r.bottom - 2, 3, 1))
    elif machine == "kombat":
        s.fill((200, 120, 60), r)
        s.fill((90, 60, 40), (r.x, r.bottom - 2, r.w, 2))
        a = frame % 4
        s.fill((40, 40, 60), (r.x + 3, r.y + 3, 2, 6)); s.fill((240, 200, 160), (r.x + 3, r.y + 2, 2, 1))
        s.fill((140, 30, 30), (r.right - 5, r.y + 3, 2, 6)); s.fill((240, 200, 160), (r.right - 5, r.y + 2, 2, 1))
        if a in (1, 2):
            s.fill((40, 40, 60), (r.x + 5, r.y + 4, 2 + a, 1))
        s.fill((250, 220, 60), (r.x + 2, r.y + 1, 3, 1)); s.fill((250, 220, 60), (r.right - 5, r.y + 1, 3, 1))
