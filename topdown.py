"""
Top-Down Town - a small explorable map built from Kenney's Top-down Shooter pack,
drawn at a three-quarter angle (walls and objects have height, things sort front-to-back).

Needs the pack folder next to this file:
    topdown.py
    kenney_top-down-shooter/   <- straight from kenney.nl, unchanged

Controls:
    WASD / Arrow keys  - move
    Shift              - run
    Tab                - switch character
    M                  - switch map (Queens Road / Town)
    F1                 - show / hide hitboxes (handy when editing the map)
    F3                 - show / hide FPS
    Esc                - quit

Editing the map:
    The world is the MAP text below. Each character is one 64x64 tile.
    Change it, save, run again.
"""

import math
import random
from pathlib import Path

import pygame

try:                                   # real Queens Road layout (generated from OpenStreetMap)
    import queens_road_map
except ImportError:
    queens_road_map = None

# ============================================================== settings
SCREEN_W, SCREEN_H = 1280, 720
FPS_CAP = 144
FIXED_DT = 1 / 120             # physics step (fixed timestep = consistent movement)
MAX_FRAME_TIME = 0.25          # clamp after a stall so nothing teleports

TILE = 64
CHUNK_TILES = 8                # ground is drawn in 8x8-tile chunks
WALK_SPEED = 230
RUN_MULTIPLIER = 1.75
CAMERA_SMOOTHING = 7.0
MAP_SEED = 2026                # picks grass/tree variants; same seed = same look

# ---- three-quarter view
WALL_HEIGHT = 44               # how tall walls look (front face height in pixels)
BUILDING_HEIGHT = 120          # street buildings are taller
PLAYER_HITBOX = (24, 14)       # width, height of the "feet" hitbox
TREE_TRUNK = 30
CANOPY_FADE_ALPHA = 110        # tree tops go see-through when you're behind them
SHADOW_ALPHA = 60
DEPTH = {"crate": 14, "big_crate": 16, "rock": 10, "bush": 12, "shrub": 5,
         "sofa": 12, "table": 14, "chair": 10}

BASE_DIR = Path(__file__).resolve().parent
PACK_DIR = BASE_DIR / "kenney_top-down-shooter"
SHEET_PATH = PACK_DIR / "Tilesheet" / "tilesheet_complete.png"
CHARACTERS = ["Man Blue", "Man Brown", "Man Old", "Woman Green", "Survivor 1", "Hitman 1"]

WALL_TOP = (214, 160, 104)
WALL_TOP_EDGE = (150, 100, 56)
WALL_FRONT_TINT = (170, 150, 140)
WALL_BASE = (90, 58, 30)
TRUNK = (120, 82, 46)
TRUNK_DARK = (92, 62, 34)
HUD_TEXT = (240, 242, 246)
HUD_BG = (20, 24, 32)

FRect = getattr(pygame, "FRect", pygame.Rect)

# ============================================================== maps
# Ground:   .  grass     ,  dirt      =  road       -  concrete
#           _  wood floor            ~  water (solid)          #  wall (solid)
# Objects:  T  tree (solid trunk, walk behind the canopy)
#           b  bush      R  rock      C  crate      B  big crate          (solid)
#           S  sofa      K  table     h  chair                            (solid)
#           s  shrub     r  rug                                           (walk over)
#           P  player start
MAP = """
TTTTTTTTTTTTTTTTT.TT.T.TTTTTTTTTTT===TTTTTTTTTTTTT.TT.TTTTTTTTT.TTTTTT.T
TTTT.TTTTTTTTTTTTT.TTT.T.TTT..TTTT===TTTTTTT.TTTTT.T.TTTTTTTTTTTTTTTT.TT
TTs....T...........s..s...........===.................,,,,,,,,,.T.....TT
T..........................R.T....===..............,,,,~~~~~~~,,,,....TT
TT................................===.............,,~~~~~~~~~~~~~,,...TT
TT....#############...............===....T...s...,,~~~~~~~~~~~~~~~,,..T.
TT....#_____#_____#...............===...........,,~~~~~~~~~~~~~~~~~,,sTT
T.....#_S___#__K__#.........T..T..===...........,~~~~~~~~~~~~~~~~~~~,..T
TT....#_____#_____#...............===..s........,~~~~~~~~~~~~~~~~~~~,.TT
TT....#___________#...............===...........,~~~~~~~~~~~~~~~~~~~,.TT
T...T.#___________#...............===...b.......,~~~~~~~~~~~~~~~~~~~,..T
TT....#_____#_____#...........T...===...........,~~~~~~~~~~~~~~~~~~~,.TT
TT....#_____#_____#...............===...........,,~~~~~~~~~~~~~~~~~,,.TT
TT....#_h___#_r_h_#...............===............,,~~~~~~~~~~~~~~~,,...T
......#_____#_____#...............===.....b.......,,~~~~~~~~~~~~~,,....T
TT....########__###.........T.....===..............,,,,~~~~~~~,,,,....TT
T.............,,.........s..s.....===...........s.....,,,,,,,,,.......TT
TT............,,.....b....T.......===.................................TT
.T..........T.,,..............----===----...b......T.................bTT
TT...........T,,..............-C--===---C..................R.......T..TT
.T.bs.........,,..............----===----.......................s.....T.
TT............,,..............----===----.............................TT
========================================================================
========================================================================
========================================================================
.T...........,,...............----===----.............................TT
.T...........,,.............P.----===----.....b.....T............T....TT
TT...........,,.....T.........----===--C-..........s.......b....T......T
T............,,...............----===----....b.....s..........b.......T.
TT...########__######.............===.................................TT
TT...#______________#.........b...===.......##########--#########.....TT
T....#_S________K___#.............===.s.b...#-------------------#.....TT
T....#______________#.............===.......#-CC-------------CC-#.....T.
TT...#______________#.....R.T..T..===.......#-C-----B---------C-#.s...TT
TT...#______________#.............===.......#-----------C-------#.....TT
TT...####__#####_####.............===.----------------------B---#.T...TT
TT...#______________#.............===.--------------------------#.T...TT
TT...#_____K________#...........T.===.......#---C---------------#.....TT
TT...#_r__________h_#..........T..===.......#-------------CC----#.T...TT
.T...#______________#.............===.......#-------------C-----#....TTT
TT...################.............===.......#--B--CC----------C-#.....TT
T.................................===.T.....#-------------------#.....T.
.T......T.........................===.......#####################....RT.
TT.................b...T..........===.....T...........................TT
TT......b.........................===..................T..............TT
T.................................===..........................b....T.TT
TT..T.TT.TTTTTTTTTTTTTTTT.T.TTTTTT===T.TTT.TTTTTTT.TTT.T.TTT.TTTTTTTTTTT
TTTTTTTTTTT.TTTTTTTT.TTTTTTTTTTTTT===T.TTTTTTTT..TT.TTTTTTTTTTTTTTTTTTTT
"""

# ---- Queens Road, Bristol (hand-drawn first pass - used if queens_road_map.py is missing)
#   H  terrace building      V  Victoria Rooms (columned hall)      W  Wills Memorial tower
#   z  zebra crossing     L  lamp post     n  bin     q  bench     F  fountain     v  parked car
#   u  bus shelter
QUEENS_ROAD = """
............................................===-................................................
...TTT......T....T...TT..........b.....Tb.T.===-..T.....T....T....T.............................
.....................b..T...b..T.....b......===-...........T.T.T.....b....T.....WWWWWWWWW....b..
..VVVVVVVVVVVVVVVV.........................-===-................................WWWWWWWWW.......
..VVVVVVVVVVVVVVVV--HHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH--WWWWWWWWWHHHHHHH
..VVVVVVVVVVVVVVVV--HHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH--WWWWWWWWWHHHHHHH
..VVVVVVVVVVVVVVVV--HHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH--WWWWWWWWWHHHHHHH
..VVVVVVVVVVVVVVVV--HHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH--WWWWWWWWWHHHHHHH
..VVVVVVVVVVVVVVVV--HHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH--WWWWWWWWWHHHHHHH
..VVVVVVVVVVVVVVVV--HHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH--WWWWWWWWWHHHHHHH
..VVVVVVVVVVVVVVVV--HHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH--WWWWWWWWWHHHHHHH
--------------n----------------------n--------------------n---------------------------n---------
----------------------------------------P-------------------------------------------------------
---L---T---L-------L---T---L-------L---T---L-------Lu--T---L-------L-------L-------L---T---L----
========v=====v===============zz====v=============v=====v=============zz====v=======v======v====
==============================zz======================================zz========================
==============================zz======================================zz========================
==============================zz======================================zz========================
========================v=====zz========v=============v===============zz========v=======v=======
-----------------------L--u------------L-----T-L-------L-----T-L-------------T-L-------L-----T-L
----------q-------------------------------------------------------------------------------------
----------------------------------------n-----------------------------------n-------------------
----------------------HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
-----T---------T------HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
----------F-----------HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
----------------------HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
----------------------HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
-----T---------T------HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
--------q---q---------HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH-===-HHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
----------------------.......................................-===-..............................
----------------------,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,-===-,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
......................,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,-===-,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
..T.b....T.b.T...............................................-===-..............................
........T...........b.T.T............T.........T..T.T..TT.T..-===-.T.T........T........TT.....T.
.T....T.b.................T....b..T.....T.T.TTb..............-===-..............T..T.......T..b.
.............................................................-===-..............................
"""

MAPS = []                                              # press M in game to switch
MAPS.append(("Queens Road", queens_road_map) if queens_road_map is not None else ("Queens Road (simple)", QUEENS_ROAD))
MAPS.append(("Town", MAP))

# extra characters in the OpenStreetMap version:  Y  traffic light   k  bike rack   o  post box
OBJECT_CHARS = set("TbRsCBSKhrP#HVWLnqFvuzYko")
WINDOW = (64, 80, 104)
STYLE_STONE = {"C": (196, 204, 210), "M": (186, 120, 96), "V": (232, 224, 204), "W": (204, 192, 166),
               "G": (214, 200, 170), "A": (226, 214, 186), "U": (200, 190, 176)}
WINDOW_FRAME = (244, 240, 230)

# building colours: (roof, roof edge, front wall, window)
BUILDING_STYLES = {
    "H": ((150, 96, 80), (110, 66, 56), (226, 206, 170), (70, 90, 120)),
    "V": ((196, 188, 170), (150, 142, 126), (232, 224, 204), (90, 96, 110)),
    "W": ((170, 160, 140), (120, 112, 98), (204, 192, 166), (60, 66, 80)),
}


# ============================================================== art helpers
class Sheet:
    """Cuts tiles out of Kenney's tilesheet by their number (tile_01 = 1, left-to-right, top-to-bottom)."""

    COLS = 27

    def __init__(self, path: Path):
        if not path.is_file():
            raise SystemExit(
                f"Can't find the tilesheet at:\n  {path}\n"
                "Put the 'kenney_top-down-shooter' folder next to topdown.py."
            )
        self.image = pygame.image.load(str(path)).convert_alpha()

    def tile(self, n: int, w: int = 1, h: int = 1) -> pygame.Surface:
        c, r = (n - 1) % self.COLS, (n - 1) // self.COLS
        return self.image.subsurface((c * TILE, r * TILE, w * TILE, h * TILE)).copy()

    def sprite(self, n: int, w: int = 1, h: int = 1) -> pygame.Surface:
        """Same as tile() but trimmed to the visible pixels (for objects)."""
        surf = self.tile(n, w, h)
        return surf.subsurface(surf.get_bounding_rect()).copy()


def darken(img: pygame.Surface, k: float) -> pygame.Surface:
    out = img.copy()
    v = int(255 * k)
    out.fill((v, v, v, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def extrude(img: pygame.Surface, depth: int) -> pygame.Surface:
    """Give a flat top-down sprite a front face: stack darker copies below it."""
    w, h = img.get_size()
    out = pygame.Surface((w, h + depth), pygame.SRCALPHA)
    side = darken(img, 0.62)
    edge = darken(img, 0.45)
    out.blit(edge, (0, depth))
    for i in range(depth - 1, 0, -1):
        out.blit(side, (0, i))
    out.blit(img, (0, 0))
    return out.convert_alpha()


def ellipse_shadow(w: int, h: int) -> pygame.Surface:
    s = pygame.Surface((max(2, w), max(2, h)), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, SHADOW_ALPHA), s.get_rect())
    return s


def make_wall_sprites(wood: pygame.Surface):
    """One wall sprite per combination of neighbouring walls (up/right/down/left).
    The top face is raised, and a front face shows underneath when there's no wall below."""
    H = WALL_HEIGHT
    front_tex = wood.copy()
    front_tex.fill(WALL_FRONT_TINT, special_flags=pygame.BLEND_RGB_MULT)
    sprites = {}
    e = 5
    for mask in range(16):                      # bit 1=up 2=right 4=down 8=left
        s = pygame.Surface((TILE, TILE + H), pygame.SRCALPHA)
        pygame.draw.rect(s, WALL_TOP, (0, 0, TILE, TILE))
        if not mask & 1: pygame.draw.rect(s, WALL_TOP_EDGE, (0, 0, TILE, e))
        if not mask & 8: pygame.draw.rect(s, WALL_TOP_EDGE, (0, 0, e, TILE))
        if not mask & 2: pygame.draw.rect(s, WALL_TOP_EDGE, (TILE - e, 0, e, TILE))
        if not mask & 4:
            pygame.draw.rect(s, WALL_TOP_EDGE, (0, TILE - e, TILE, e))
            s.blit(front_tex, (0, TILE), area=pygame.Rect(0, 0, TILE, H))
            pygame.draw.rect(s, WALL_BASE, (0, TILE + H - 4, TILE, 4))
            if not mask & 8: pygame.draw.rect(s, WALL_BASE, (0, TILE, 3, H))
            if not mask & 2: pygame.draw.rect(s, WALL_BASE, (TILE - 3, TILE, 3, H))
        sprites[mask] = s.convert_alpha()
    return sprites


def make_building_sprite(ch: str, mask: int, x: int) -> pygame.Surface:
    """A tall block for street buildings: flat roof, and a front wall with windows on the bottom row."""
    roof, edge, front, win = BUILDING_STYLES[ch]
    H = BUILDING_HEIGHT
    s = pygame.Surface((TILE, TILE + H), pygame.SRCALPHA)
    pygame.draw.rect(s, roof, (0, 0, TILE, TILE))
    e = 6
    if not mask & 1: pygame.draw.rect(s, edge, (0, 0, TILE, e))
    if not mask & 8: pygame.draw.rect(s, edge, (0, 0, e, TILE))
    if not mask & 2: pygame.draw.rect(s, edge, (TILE - e, 0, e, TILE))
    if not mask & 4:
        pygame.draw.rect(s, edge, (0, TILE - e, TILE, e))
        pygame.draw.rect(s, front, (0, TILE, TILE, H))
        if ch == "V":                                   # columns
            for cx in (8, 40):
                pygame.draw.rect(s, (246, 240, 226), (cx, TILE + 10, 14, H - 14))
                pygame.draw.rect(s, (200, 192, 174), (cx + 10, TILE + 10, 4, H - 14))
        else:
            for wy in (TILE + 14, TILE + 56):
                for wx in (10, 38):
                    pygame.draw.rect(s, win, (wx, wy, 16, 26))
                    pygame.draw.rect(s, (240, 240, 236), (wx, wy, 16, 26), 2)
            if ch == "H" and x % 3 == 0:                 # a door every few buildings
                pygame.draw.rect(s, (60, 40, 30), (22, TILE + H - 34, 20, 34))
        pygame.draw.rect(s, darken_colour(front, 0.6), (0, TILE + H - 4, TILE, 4))
        if not mask & 8: pygame.draw.rect(s, darken_colour(front, 0.7), (0, TILE, 3, H))
        if not mask & 2: pygame.draw.rect(s, darken_colour(front, 0.7), (TILE - 3, TILE, 3, H))
    return s.convert_alpha()


def make_real_building_sprite(b: dict, mask: int, x: int, tower: bool) -> tuple[pygame.Surface, int]:
    """One tile of a real (OpenStreetMap) building: roof on top, and the street face if the tile
    below isn't the same building. Colours and height come from the map file."""
    H = min(int(b["height"]), 170) + (180 if tower else 0)
    roof = b.get("roof") or (96, 96, 104)
    stone = b.get("stone") or STYLE_STONE.get(b.get("style"), (220, 206, 176))
    edge = darken_colour(roof, 0.7)
    s = pygame.Surface((TILE, TILE + H), pygame.SRCALPHA)
    pygame.draw.rect(s, roof, (0, 0, TILE, TILE))
    e = 6
    if not mask & 1: pygame.draw.rect(s, edge, (0, 0, TILE, e))
    if not mask & 8: pygame.draw.rect(s, edge, (0, 0, e, TILE))
    if not mask & 2: pygame.draw.rect(s, edge, (TILE - e, 0, e, TILE))
    if not mask & 4:
        pygame.draw.rect(s, edge, (0, TILE - e, TILE, e))
        pygame.draw.rect(s, stone, (0, TILE, TILE, H))
        floors = max(1, int(b.get("floors", 3))) + (4 if tower else 0)
        fh = (H - 8) // floors
        shop = b.get("shop") and not tower
        for f in range(floors):
            wy = TILE + 6 + f * fh
            if shop and f == floors - 1:
                break
            for wx in (10, 38):
                pygame.draw.rect(s, WINDOW, (wx, wy + 4, 16, max(8, fh - 12)))
                pygame.draw.rect(s, WINDOW_FRAME, (wx, wy + 4, 16, max(8, fh - 12)), 2)
        if shop:                                         # shopfront: big window + awning
            sy = TILE + H - fh
            pygame.draw.rect(s, b.get("awning") or (60, 60, 70), (0, sy, TILE, 10))
            pygame.draw.rect(s, (120, 150, 170), (4, sy + 14, 36, fh - 18))
            pygame.draw.rect(s, (50, 36, 30), (44, sy + 14, 16, fh - 14))
        pygame.draw.rect(s, darken_colour(stone, 0.6), (0, TILE + H - 4, TILE, 4))
        if not mask & 8: pygame.draw.rect(s, darken_colour(stone, 0.75), (0, TILE, 3, H))
        if not mask & 2: pygame.draw.rect(s, darken_colour(stone, 0.75), (TILE - 3, TILE, 3, H))
    return s.convert_alpha(), H


def make_signal() -> pygame.Surface:
    s = pygame.Surface((18, 96), pygame.SRCALPHA)
    pygame.draw.rect(s, (40, 44, 52), (7, 30, 4, 66))
    pygame.draw.rect(s, (30, 32, 36), (2, 0, 14, 34), border_radius=3)
    for i, c in enumerate(((220, 50, 40), (90, 70, 20), (40, 70, 40))):
        pygame.draw.circle(s, c, (9, 6 + i * 11), 4)
    return s.convert_alpha()


def make_bike_rack() -> pygame.Surface:
    s = pygame.Surface((50, 30), pygame.SRCALPHA)
    for bx in (4, 20, 36):
        pygame.draw.rect(s, (150, 156, 164), (bx, 2, 10, 28), 3, border_radius=5)
    return s.convert_alpha()


def make_post_box() -> pygame.Surface:
    s = pygame.Surface((26, 50), pygame.SRCALPHA)
    pygame.draw.rect(s, (200, 30, 30), (2, 6, 22, 44), border_radius=4)
    pygame.draw.ellipse(s, (170, 20, 20), (0, 0, 26, 14))
    pygame.draw.rect(s, (30, 20, 20), (7, 18, 12, 3))
    return s.convert_alpha()


def darken_colour(c, k):
    return tuple(int(v * k) for v in c)


def make_tree(canopy: pygame.Surface) -> tuple[pygame.Surface, int]:
    """Canopy on top of a short trunk. Returns (sprite, distance from sprite top to trunk base)."""
    cw, ch = canopy.get_size()
    trunk_w = 16
    h = ch + TREE_TRUNK
    s = pygame.Surface((cw, h), pygame.SRCALPHA)
    tx = cw // 2 - trunk_w // 2
    pygame.draw.rect(s, TRUNK, (tx, ch - 30, trunk_w, TREE_TRUNK + 30), border_radius=4)
    pygame.draw.rect(s, TRUNK_DARK, (tx + trunk_w - 5, ch - 30, 5, TREE_TRUNK + 30), border_radius=3)
    s.blit(extrude(canopy, 8), (0, 0))
    return s.convert_alpha(), h


def make_lamp() -> pygame.Surface:
    s = pygame.Surface((20, 110), pygame.SRCALPHA)
    pygame.draw.rect(s, (40, 44, 52), (8, 10, 4, 96))
    pygame.draw.rect(s, (40, 44, 52), (4, 104, 12, 6))
    pygame.draw.rect(s, (40, 44, 52), (2, 2, 16, 10), border_radius=3)
    pygame.draw.rect(s, (255, 236, 170), (5, 8, 10, 4))
    return s.convert_alpha()


def make_bin() -> pygame.Surface:
    s = pygame.Surface((24, 34), pygame.SRCALPHA)
    pygame.draw.rect(s, (40, 70, 50), (2, 4, 20, 30), border_radius=3)
    pygame.draw.rect(s, (24, 44, 32), (0, 0, 24, 6), border_radius=2)
    return s.convert_alpha()


def make_bench() -> pygame.Surface:
    s = pygame.Surface((60, 36), pygame.SRCALPHA)
    pygame.draw.rect(s, (130, 86, 50), (0, 0, 60, 8))
    pygame.draw.rect(s, (150, 100, 60), (0, 14, 60, 10))
    for lx in (4, 52):
        pygame.draw.rect(s, (40, 40, 44), (lx, 24, 4, 12))
    return s.convert_alpha()


def make_car(rng) -> pygame.Surface:
    col = rng.choice([(190, 50, 50), (50, 90, 170), (230, 230, 230), (40, 40, 44), (80, 140, 90)])
    s = pygame.Surface((110, 56), pygame.SRCALPHA)
    pygame.draw.rect(s, (20, 20, 24), (12, 40, 18, 14), border_radius=4)
    pygame.draw.rect(s, (20, 20, 24), (80, 40, 18, 14), border_radius=4)
    pygame.draw.rect(s, col, (0, 10, 110, 36), border_radius=10)
    pygame.draw.rect(s, darken_colour(col, 0.75), (0, 34, 110, 12), border_radius=6)
    pygame.draw.rect(s, (150, 190, 220), (28, 0, 52, 20), border_radius=6)
    pygame.draw.rect(s, col, (24, 0, 60, 4), border_radius=2)
    return s.convert_alpha()


def make_shelter() -> pygame.Surface:
    s = pygame.Surface((70, 100), pygame.SRCALPHA)
    pygame.draw.rect(s, (60, 64, 72), (0, 0, 70, 12))
    pygame.draw.rect(s, (170, 210, 230, 120), (4, 12, 62, 80))
    pygame.draw.rect(s, (60, 64, 72), (4, 12, 4, 88))
    pygame.draw.rect(s, (60, 64, 72), (62, 12, 4, 88))
    return s


def make_fountain() -> pygame.Surface:
    s = pygame.Surface((120, 80), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (170, 168, 160), (0, 20, 120, 60))
    pygame.draw.ellipse(s, (70, 140, 200), (10, 28, 100, 42))
    pygame.draw.rect(s, (190, 188, 180), (52, 0, 16, 46))
    pygame.draw.circle(s, (150, 200, 240), (60, 4), 8)
    return s.convert_alpha()


class Sprite:
    """Something drawn in the depth-sorted pass. sort_y = where it touches the ground."""
    __slots__ = ("image", "pos", "sort_y", "fade_rect")

    def __init__(self, image, pos, sort_y, fade_rect=None):
        self.image, self.pos, self.sort_y, self.fade_rect = image, pos, sort_y, fade_rect


# ============================================================== world
class World:
    def __init__(self, map_def, sheet: Sheet):
        self.real = None                              # OpenStreetMap buildings, when the map comes from a module
        if isinstance(map_def, str):
            rows = map_def.strip("\n").splitlines()
        else:
            rows = list(map_def.ROWS)
            alph = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_."
            ids = [[-1 if r[i:i + 2] == "~~" else alph.index(r[i]) * 64 + alph.index(r[i + 1])
                    for i in range(0, len(r), 2)] for r in map_def.BUILDING_IDS]
            self.real = dict(ids=ids, buildings=map_def.BUILDINGS, tower=set(map(tuple, map_def.TOWER_TILES)),
                             attribution=getattr(map_def, "ATTRIBUTION", ""))
        self.h = len(rows)
        self.w = max(len(r) for r in rows)
        self.grid = [list(r.ljust(self.w, ".")) for r in rows]
        self.pixel_w, self.pixel_h = self.w * TILE, self.h * TILE
        self.sheet = sheet
        self.rng = random.Random(MAP_SEED)
        self._load_art()
        self.spawn = (self.pixel_w / 2, self.pixel_h / 2)
        self.sprites: list[Sprite] = []
        self.solids: list[pygame.Rect] = []
        self.decals = []
        self._build()
        self.solid_grid: dict[tuple[int, int], list[pygame.Rect]] = {}
        for r in self.solids:
            for key in self._cells(r):
                self.solid_grid.setdefault(key, []).append(r)
        self.chunks = {}

    def _load_art(self):
        s = self.sheet
        self.grass = [s.tile(n) for n in (1, 2, 3, 4)]
        self.dirt = [s.tile(n) for n in (5, 6)]
        self.concrete = [s.tile(n) for n in (7, 8, 9)]
        self.water = [s.tile(n) for n in (19, 20)]
        self.wood = [s.tile(n) for n in (42, 43, 44)]
        self.road = s.tile(86)
        self.walls = make_wall_sprites(s.tile(42))
        self.trees = [make_tree(s.sprite(181, 2, 2)), make_tree(s.sprite(184, 2, 2))]
        self.tree_shadow = ellipse_shadow(92, 32)
        self.bushes = [s.sprite(183), s.sprite(186)]
        self.shrubs = [s.sprite(235), s.sprite(236)]
        self.rocks = [s.sprite(237), s.sprite(238), s.sprite(239)]
        self.crates = [s.sprite(129), s.sprite(130)]
        self.big_crate = s.sprite(156)
        self.sofa = s.sprite(447, 3, 1)
        self.table = s.sprite(453, 3, 1)
        self.chair = s.sprite(451)
        self.rug = s.sprite(343, 3, 1)
        self.lamp = make_lamp()
        self.bin = make_bin()
        self.bench = make_bench()
        self.shelter = make_shelter()
        self.fountain = make_fountain()
        self.signal = make_signal()
        self.bike_rack = make_bike_rack()
        self.post_box = make_post_box()
        self._extruded = {}
        self._buildings = {}
        self.tallest = BUILDING_HEIGHT

    def _ex(self, img, kind):
        key = (id(img), kind)
        if key not in self._extruded:
            self._extruded[key] = extrude(img, DEPTH[kind])
        return self._extruded[key]

    def at(self, x, y, default="#"):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return default

    def _ground_char(self, x, y):
        """What's underneath an object: whatever ground is most common around it."""
        ch = self.grid[y][x]
        if ch not in OBJECT_CHARS:
            return ch
        if ch == "z":
            return "="
        if ch in "HVW":
            return "-"
        counts = {}
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            n = self.at(x + dx, y + dy, ".")
            if n not in OBJECT_CHARS and n != "~":
                counts[n] = counts.get(n, 0) + 1
        return max(counts, key=counts.get) if counts else "."

    def _add_object(self, img, x, y, kind, solid_w=40, solid_h=20, solid=True):
        cx, foot = x * TILE + TILE // 2, y * TILE + TILE - 6
        img = self._ex(img, kind)
        self.sprites.append(Sprite(img, (cx - img.get_width() // 2, foot - img.get_height()), foot))
        if solid:
            self.solids.append(pygame.Rect(cx - solid_w // 2, foot - solid_h, solid_w, solid_h))

    def _build(self):
        rng = self.rng
        for y in range(self.h):
            for x in range(self.w):
                ch = self.grid[y][x]
                cx = x * TILE + TILE // 2
                tile_rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                if ch == "~":
                    self.solids.append(tile_rect)
                elif ch == "#":
                    self.solids.append(tile_rect)
                    mask = self._mask(x, y, "#")
                    self.sprites.append(Sprite(self.walls[mask], (x * TILE, y * TILE - WALL_HEIGHT), tile_rect.bottom))
                elif ch == "H" and self.real is not None:
                    self._real_building(x, y, tile_rect)
                elif ch in "HVW":
                    self.solids.append(tile_rect)
                    mask = self._mask(x, y, ch)
                    key = (ch, mask, x % 3 == 0)
                    if key not in self._buildings:
                        self._buildings[key] = make_building_sprite(ch, mask, x)
                    self.sprites.append(Sprite(self._buildings[key], (x * TILE, y * TILE - BUILDING_HEIGHT), tile_rect.bottom))
                elif ch == "T":
                    img, base = rng.choice(self.trees)
                    foot = tile_rect.bottom - 8
                    pos = (cx - img.get_width() // 2, foot - base)
                    self.decals.append((self.tree_shadow, (cx - 46, foot - 18)))
                    fade = pygame.Rect(pos[0], pos[1], img.get_width(), base - TREE_TRUNK - 10)
                    self.sprites.append(Sprite(img, pos, foot, fade))
                    self.solids.append(pygame.Rect(cx - 10, foot - 12, 20, 12))
                elif ch == "b":
                    self._add_object(rng.choice(self.bushes), x, y, "bush", 44, 24)
                elif ch == "s":
                    self._add_object(rng.choice(self.shrubs), x, y, "shrub", solid=False)
                elif ch == "R":
                    self._add_object(rng.choice(self.rocks), x, y, "rock", 36, 20)
                elif ch == "C":
                    self._add_object(rng.choice(self.crates), x, y, "crate", 44, 28)
                elif ch == "B":
                    self._add_object(self.big_crate, x, y, "big_crate", 56, 34)
                elif ch == "S":
                    self._add_object(self.sofa, x, y, "sofa", 150, 30)
                elif ch == "K":
                    self._add_object(self.table, x, y, "table", 150, 30)
                elif ch == "h":
                    self._add_object(self.chair, x, y, "chair", 36, 20)
                elif ch == "r":
                    self.decals.append((self.rug, (cx - self.rug.get_width() // 2, y * TILE + 8)))
                elif ch == "L":
                    foot = tile_rect.bottom - 10
                    self.sprites.append(Sprite(self.lamp, (cx - 10, foot - self.lamp.get_height()), foot))
                    self.solids.append(pygame.Rect(cx - 6, foot - 8, 12, 8))
                elif ch == "n":
                    foot = tile_rect.bottom - 10
                    self.sprites.append(Sprite(self.bin, (cx - 12, foot - 34), foot))
                    self.solids.append(pygame.Rect(cx - 12, foot - 12, 24, 12))
                elif ch == "q":
                    foot = tile_rect.bottom - 10
                    self.sprites.append(Sprite(self.bench, (cx - 30, foot - 36), foot))
                    self.solids.append(pygame.Rect(cx - 30, foot - 14, 60, 14))
                elif ch == "u":
                    foot = tile_rect.bottom - 4
                    self.sprites.append(Sprite(self.shelter, (cx - 35, foot - 100), foot))
                    self.solids.append(pygame.Rect(cx - 35, foot - 12, 70, 12))
                elif ch == "F":
                    foot = tile_rect.bottom + 10
                    self.sprites.append(Sprite(self.fountain, (cx - 60, foot - 80), foot))
                    self.solids.append(pygame.Rect(cx - 56, foot - 50, 112, 46))
                elif ch == "v":
                    car = make_car(rng)
                    foot = tile_rect.bottom - 4
                    self.sprites.append(Sprite(car, (cx - 55, foot - 56), foot))
                    self.solids.append(pygame.Rect(cx - 55, foot - 34, 110, 34))
                elif ch in "Yko":
                    img = {"Y": self.signal, "k": self.bike_rack, "o": self.post_box}[ch]
                    foot = tile_rect.bottom - 10
                    self.sprites.append(Sprite(img, (cx - img.get_width() // 2, foot - img.get_height()), foot))
                    self.solids.append(pygame.Rect(cx - img.get_width() // 2, foot - 10, img.get_width(), 10))
                elif ch == "P":
                    self.spawn = (cx, tile_rect.centery)

    def _real_building(self, x, y, tile_rect):
        ids = self.real["ids"]
        bid = ids[y][x] if y < len(ids) and x < len(ids[y]) else -1
        self.solids.append(tile_rect)
        if bid < 0:
            return
        b = self.real["buildings"][bid]
        same = lambda xx, yy: 0 <= yy < len(ids) and 0 <= xx < len(ids[yy]) and ids[yy][xx] == bid
        mask = (1 if same(x, y - 1) else 0) | (2 if same(x + 1, y) else 0) | (4 if same(x, y + 1) else 0) | (8 if same(x - 1, y) else 0)
        tower = (x, y) in self.real["tower"]
        key = (bid, mask, tower)
        if key not in self._buildings:
            self._buildings[key] = make_real_building_sprite(b, mask, x, tower)
        img, H = self._buildings[key]
        self.tallest = max(self.tallest, H)
        self.sprites.append(Sprite(img, (x * TILE, y * TILE - H), tile_rect.bottom))

    def _mask(self, x, y, ch):
        mask = 0
        if self.at(x, y - 1, ".") == ch: mask |= 1
        if self.at(x + 1, y, ".") == ch: mask |= 2
        if self.at(x, y + 1, ".") == ch: mask |= 4
        if self.at(x - 1, y, ".") == ch: mask |= 8
        return mask

    def _ground_tile(self, x, y, rng):
        g = self._ground_char(x, y)
        if g == ".": return rng.choice(self.grass)
        if g == ",": return rng.choice(self.dirt)
        if g == "-": return rng.choice(self.concrete)
        if g == "_": return self.wood[(x + y) % len(self.wood)]
        if g == "~": return rng.choice(self.water)
        if g == "=": return self.road
        return self.grass[0]

    def ground_chunk(self, cx, cy) -> pygame.Surface:
        """The floor is drawn in 8x8-tile chunks the first time they come on screen, then kept."""
        key = (cx, cy)
        surf = self.chunks.get(key)
        if surf is not None:
            return surf
        size = TILE * CHUNK_TILES
        surf = pygame.Surface((size, size)).convert()
        surf.fill((30, 34, 40))
        rng = random.Random(MAP_SEED * 7919 + cx * 131 + cy)
        x0, y0 = cx * CHUNK_TILES, cy * CHUNK_TILES
        for y in range(y0, min(self.h, y0 + CHUNK_TILES)):
            for x in range(x0, min(self.w, x0 + CHUNK_TILES)):
                px, py = (x - x0) * TILE, (y - y0) * TILE
                surf.blit(self._ground_tile(x, y, rng), (px, py))
                if self.grid[y][x] == "z":                       # zebra stripes
                    for k in range(0, TILE, 16):
                        pygame.draw.rect(surf, (236, 236, 236), (px + 6, py + k + 2, TILE - 12, 8))
        area = pygame.Rect(cx * size, cy * size, size, size)
        for img, pos in self.decals:                              # rugs + shadows baked in
            r = img.get_rect(topleft=pos)
            if r.colliderect(area):
                surf.blit(img, (pos[0] - area.x, pos[1] - area.y))
        self.chunks[key] = surf
        return surf

    def draw_ground(self, screen, view: pygame.Rect):
        size = TILE * CHUNK_TILES
        for cy in range(max(0, view.top // size), min((self.h - 1) // CHUNK_TILES, view.bottom // size) + 1):
            for cx in range(max(0, view.left // size), min((self.w - 1) // CHUNK_TILES, view.right // size) + 1):
                screen.blit(self.ground_chunk(cx, cy), (cx * size - view.x, cy * size - view.y))

    # ---------------------------------------------------- collision
    @staticmethod
    def _cells(r):
        for cy in range(r.top // TILE, (r.bottom - 1) // TILE + 1):
            for cx in range(r.left // TILE, (r.right - 1) // TILE + 1):
                yield (cx, cy)

    def nearby_solids(self, rect):
        seen = []
        for key in self._cells(rect.inflate(TILE, TILE)):
            for r in self.solid_grid.get(key, ()):
                if r not in seen:
                    seen.append(r)
        return seen

    def visible_sprites(self, view: pygame.Rect):
        pad = self.tallest + TILE
        v = view.inflate(pad * 2, pad * 2)
        return [s for s in self.sprites if v.collidepoint(s.pos[0], s.sort_y) or v.collidepoint(s.pos)]


# ============================================================== player
def load_character(name: str):
    folder = PACK_DIR / "PNG" / name
    files = sorted(folder.glob("*_stand.png")) if folder.is_dir() else []
    if not files:
        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(s, (47, 111, 237), (20, 20), 18)
        return s
    return pygame.image.load(str(files[0])).convert_alpha()


class Player:
    def __init__(self, x: float, y: float):
        self.pos = pygame.Vector2(x, y)          # feet position
        self.prev_pos = self.pos.copy()
        self.facing = pygame.Vector2(0, 1)
        self.char_index = 0
        self._set_character()

    def _set_character(self):
        self.base_image = load_character(CHARACTERS[self.char_index])
        self.rot_cache = {}

    def next_character(self):
        self.char_index = (self.char_index + 1) % len(CHARACTERS)
        self._set_character()

    def rect(self, pos=None):
        p = pos if pos is not None else self.pos
        w, h = PLAYER_HITBOX
        return FRect(p.x - w / 2, p.y - h, w, h)

    def update(self, dt, keys, world: World):
        self.prev_pos.update(self.pos)
        d = pygame.Vector2(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        if d.length_squared() == 0:
            return
        d.normalize_ip()
        self.facing = d
        speed = WALK_SPEED * (RUN_MULTIPLIER if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1)
        step = d * speed * dt
        for axis in (0, 1):                     # move one axis at a time so you slide along walls
            self.pos[axis] += step[axis]
            r = self.rect()
            for s in world.nearby_solids(pygame.Rect(int(r.x), int(r.y), int(r.w) + 1, int(r.h) + 1)):
                if r.colliderect(s):
                    if axis == 0:
                        self.pos.x = (s.left - r.w / 2) if step.x > 0 else (s.right + r.w / 2)
                    else:
                        self.pos.y = s.top if step.y > 0 else (s.bottom + r.h)
                    r = self.rect()
        w, h = PLAYER_HITBOX
        self.pos.x = max(w, min(world.pixel_w - w, self.pos.x))
        self.pos.y = max(h, min(world.pixel_h, self.pos.y))

    def sprite(self):
        angle = round(-math.degrees(math.atan2(self.facing.y, self.facing.x))) % 360
        img = self.rot_cache.get(angle)
        if img is None:
            img = self.rot_cache[angle] = pygame.transform.rotate(self.base_image, angle)
        return img


class Camera:
    def __init__(self, target):
        self.pos = pygame.Vector2(target)
        self.prev_pos = self.pos.copy()

    def update(self, target, dt, world, view_size):
        self.prev_pos.update(self.pos)
        t = 1 - math.exp(-CAMERA_SMOOTHING * dt)
        self.pos += (pygame.Vector2(target) - self.pos) * t
        hw, hh = view_size[0] / 2, view_size[1] / 2
        self.pos.x = max(hw, min(world.pixel_w - hw, self.pos.x)) if world.pixel_w > view_size[0] else world.pixel_w / 2
        self.pos.y = max(hh - world.tallest, min(world.pixel_h - hh, self.pos.y)) if world.pixel_h > view_size[1] else world.pixel_h / 2


# ============================================================== main
def main() -> None:
    pygame.init()
    flags = pygame.SCALED | pygame.RESIZABLE
    try:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags, vsync=1)
    except pygame.error:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    pygame.display.set_caption("Top-Down Town")

    sheet = Sheet(SHEET_PATH)
    map_index = 0
    world = World(MAPS[map_index][1], sheet)
    player = Player(*world.spawn)
    camera = Camera(player.pos)
    shadow = ellipse_shadow(34, 14)

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,menlo,monospace", 14)
    show_hitboxes = False
    show_fps = True
    accumulator = 0.0
    running = True

    while running:
        accumulator += min(clock.tick(FPS_CAP) / 1000, MAX_FRAME_TIME)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F1:
                    show_hitboxes = not show_hitboxes
                elif event.key == pygame.K_F3:
                    show_fps = not show_fps
                elif event.key == pygame.K_TAB:
                    player.next_character()
                elif event.key == pygame.K_m:
                    map_index = (map_index + 1) % len(MAPS)
                    world = World(MAPS[map_index][1], sheet)
                    player.pos.update(world.spawn); player.prev_pos.update(world.spawn)
                    camera = Camera(player.pos)

        keys = pygame.key.get_pressed()
        while accumulator >= FIXED_DT:
            player.update(FIXED_DT, keys, world)
            camera.update(player.pos, FIXED_DT, world, screen.get_size())
            accumulator -= FIXED_DT

        alpha = accumulator / FIXED_DT
        draw_player = player.prev_pos.lerp(player.pos, alpha)
        draw_cam = camera.prev_pos.lerp(camera.pos, alpha)
        w, h = screen.get_size()
        ox, oy = round(w / 2 - draw_cam.x), round(h / 2 - draw_cam.y)
        view = pygame.Rect(-ox, -oy, w, h)

        screen.fill((30, 34, 40))
        world.draw_ground(screen, view)

        # depth-sorted pass: everything (and you) ordered by where it touches the ground
        pimg = player.sprite()
        prect = pimg.get_rect(center=(round(draw_player.x) + ox, round(draw_player.y) - 16 + oy))
        items = [(s.sort_y, 0, s) for s in world.visible_sprites(view)]
        items.append((draw_player.y, 1, None))
        items.sort(key=lambda t: (t[0], t[1]))
        player_screen = pygame.Rect(prect)
        for _, _, s in items:
            if s is None:
                screen.blit(shadow, (round(draw_player.x) - 17 + ox, round(draw_player.y) - 9 + oy))
                screen.blit(pimg, prect)
                continue
            img = s.image
            if s.fade_rect is not None and s.sort_y > draw_player.y and \
                    s.fade_rect.move(ox, oy).colliderect(player_screen):
                img = img.copy(); img.set_alpha(CANOPY_FADE_ALPHA)      # see yourself behind tree tops
            screen.blit(img, (s.pos[0] + ox, s.pos[1] + oy))

        if show_hitboxes:
            for r in world.solids:
                if view.colliderect(r):
                    pygame.draw.rect(screen, (255, 60, 60), r.move(ox, oy), 1)
            r = player.rect()
            pygame.draw.rect(screen, (60, 255, 60), (r.x + ox, r.y + oy, r.w, r.h), 1)

        if show_fps:
            text = f"{MAPS[map_index][0]}   FPS {clock.get_fps():4.0f}   M map  Tab character  F1 hitboxes"
            surf = font.render(text, True, HUD_TEXT, HUD_BG)
            screen.blit(surf, (12, 10))
        if world.real and world.real["attribution"]:                 # OpenStreetMap's licence asks for this
            surf = font.render(world.real["attribution"], True, HUD_TEXT, HUD_BG)
            screen.blit(surf, (w - surf.get_width() - 10, h - surf.get_height() - 8))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
