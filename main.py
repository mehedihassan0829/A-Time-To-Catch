"""
A Time To Catch - a top-down pixel-art game set on Park Street and Frogmore Street, Bristol,
drawn at a three-quarter angle (walls and objects have height, things sort front-to-back).
All the art is drawn in code (pixel_art.py, people.py).

Controls:
    WASD / Arrow keys  - move
    Shift              - run
    E                  - talk / play an arcade machine
    I / N / F          - pocket / notebook / lighter
    T (hold)           - make time pass faster
    Tab                - switch character
    M                  - switch map (Park Street / Queens Road)
    F1                 - show / hide hitboxes (handy when editing the map)
    F3                 - show / hide FPS
    F5 / F6 / F7       - (testing) jump to the Frogmore steps / the Park Street stairwell / the arcade
    In the arcade: walk up to a machine and press E to play it (Esc or Backspace to step away)
    Click / E / Space  - next line in a cut scene (and put the newspaper away)
    Esc                - quit

The story (quest.py): you start on Park Street every time. The compass at the top of the screen points
along the walking route to wherever you need to go next - first the crime scene at the harbourside.
On the way you can buy the morning paper at Park Stores (E at the counter); it stays in your pocket to re-read.
"""

import math
import random
from collections import OrderedDict
from pathlib import Path

def _ensure_libraries():
    """First run on a new computer: install whatever's in requirements.txt, then carry on."""
    try:
        import pygame  # noqa: F401
        import pygame_widgets  # noqa: F401   (MVB Kombat in the arcade uses it)
        return
    except ImportError:
        pass
    import subprocess, sys
    req = Path(__file__).resolve().parent / "requirements.txt"
    print("Installing the libraries the game needs (one-off)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])


_ensure_libraries()
import pygame

import pixel_art as pa                 # all the pixel-art drawing (pixel_art.py, next to this file)
import people                          # NPCs (people.py) - story characters are in story.py
import traffic                         # traffic lights, cars, the bus (traffic.py)
import inventory                       # your pocket + notebook (inventory.py)
import daynight                        # the clock, day/night lighting and your watch (daynight.py)

try:                                   # real Queens Road layout (from OpenStreetMap)
    import queens_road_map
except ImportError:
    queens_road_map = None
try:                                   # Frogmore Street, down the steps under the Park Street bridge
    import frogmore_map
except ImportError:
    frogmore_map = None
try:                                   # real Park Street + College Green layout (from OpenStreetMap)
    import park_street_map
except ImportError:
    park_street_map = None
try:                                   # the harbourside, off the end of College Green (with the arcade)
    import harbourside_map
except ImportError:
    harbourside_map = None
import arcade                          # the arcade machines and their games (arcade.py)
import quest                           # objectives, the compass, cut scenes, the newspaper (quest.py)

# ============================================================== settings
SCREEN_W, SCREEN_H = 1280, 720
FPS_CAP = 144
FIXED_DT = 1 / 120             # physics step (fixed timestep = consistent movement)
MAX_FRAME_TIME = 0.25          # clamp after a stall so nothing teleports

TILE = 64
CHUNK_TILES = 8                # ground is pre-rendered in 8x8-tile chunks
WALK_SPEED = 230
RUN_MULTIPLIER = 1.75
CAMERA_SMOOTHING = 7.0
CAMERA_LOOK_UP = 140            # px: frame the view a little above the player
MAP_SEED = 2026                # picks grass/tree variants; same seed = same look

# ---- three-quarter view
WALL_HEIGHT = 44               # how tall walls look (front face height in pixels)
PLAYER_HITBOX = (24, 14)       # width, height of the "feet" hitbox
TREE_TRUNK = 30                # visible trunk height under the canopy
CANOPY_FADE_ALPHA = 110        # tree tops go see-through when you're behind them
SHADOW_ALPHA = 60

BASE_DIR = Path(__file__).resolve().parent


WALL_TOP = (214, 160, 104)
WALL_TOP_EDGE = (150, 100, 56)
WALL_FRONT_TINT = (170, 150, 140)   # multiplies the wood texture for the front face
WALL_BASE = (90, 58, 30)
TRUNK = (120, 82, 46)
TRUNK_DARK = (92, 62, 34)
HUD_TEXT = (240, 242, 246)
HUD_BG = (20, 24, 32)

FRect = getattr(pygame, "FRect", pygame.Rect)   # FRect = float rect (pygame-ce)

# ============================================================== maps
# Ground:   .  grass     ,  dirt      =  road       -  paving
#           _  wood floor            ~  water (solid)          #  wall (solid)
# Objects:  T  tree      L  lamp     P  player start      (the street maps add more - see park_street_map.py)

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
if park_street_map is not None:
    MAPS.append(("Park Street", park_street_map))
PLACES = {name: m for name, m in MAPS}       # every place you can be, by name (stairs etc. link them up)
if frogmore_map is not None:
    PLACES["Frogmore Street"] = frogmore_map
if harbourside_map is not None:
    PLACES["Harbourside"] = harbourside_map
MAPS.append(("Queens Road", queens_road_map) if queens_road_map is not None else ("Queens Road (simple)", QUEENS_ROAD))

OBJECT_CHARS = set("TbRsCBSKhrP#HVWLnqFvuokY" "QXMZIJAGOUNDpgyE " "|t^!$%@*&" "1234" "mjx" "056789<>?[]{}")
STORY_PROPS = "056789<>?[]{}"     # the story's rooms (see INTERIORS): 5 records shelf  6 lockers  7 boxes  8 desk (9 = its
                                  # right half)  0 bookcase  [ filing cabinet  { office chair  < sofa (> = right half)
                                  # ? side table with the phone  ] armchair  } floor lamp
RECORD_YEARS = [("1994", "1995"), ("1996", "1997"), ("1998", None), ("2000", "2001")]   # the arcade's staff records

# ============================================================== shop interiors
# Each shop you can walk into gets one of these rooms. Characters:
#   #  wall      (space)  nothing (solid)      E  way out (the door)      p  shopkeeper
#   floors:  _ wood   c checker tiles   f shop vinyl   ; gym rubber   w carpet
#   things:  Q counter   X counter with till   M coffee machine   Z shelf   I fridge   J café table
#            A clothes rail   G barber chair   O mirror   U treadmill   N bench press   D weights rack
#            g plant   y rug   q bench
#   arcade:  a carpet   1 MVB Kombat   2 Seagull Bird   3 Hoop Shot   4 Invaders   (machines: walk up, press E)
SHOP_NAMES = {"cafe": "Café", "corner": "Corner Shop", "clothes": "Clothes Shop", "books": "Bookshop",
              "barber": "Barber", "gym": "Gym", "kebab": "Kebab Shop", "club": "Nightclub", "arcade": "Arcade",
              "zaza": "Restaurant", "usher": "Professor Usher's Office", "gazette": "Newspaper Office", "home": "Home"}
ZAZA_CHARS = "SxBKbhTPFWV"     # Za Za Bazaar: S station (4 wide, x = the rest), B bar, K back bar, b booth (2 wide, h = rest),
                               # T table for four, P pillar, F drinks station (2 wide), W / V toilets; i = polished concrete
ARCADE_MACHINES = {"1": "kombat", "2": "seagull", "3": "hoops", "4": "invaders"}
INTERIORS = {
    # Professor Usher's office in the Wills Memorial Building: oak bookcases, filing cabinets, his desk, a rug
    "usher": [
        "############",
        "#0000[[0000#",
        "#__________#",
        "#___{______#",
        "#__89___y__#",
        "#__________#",
        "#________]_#",
        "#__________#",
        "#g________g#",
        "#####E######",
    ],
    # ...and the same office once he's packed up to run: boxes, half-empty shelves, papers on the floor
    "usher_packed": [
        "############",
        "#0000[[0000#",
        "#__7_______#",
        "#___{___7__#",
        "#__89______#",
        "#_____7____#",
        "#________]_#",
        "#_7________#",
        "#g_____77_g#",
        "#####E######",
    ],
    # The Gazette's newsroom, where Daniel works
    "gazette": [
        "############",
        "#00[[g00[[0#",
        "#w{wwww{www#",
        "#w89www89ww#",
        "#wwwwwwwwww#",
        "#w{wwww{www#",
        "#w89www89ww#",
        "#wwwwwwwwww#",
        "#gwwwwwwwwg#",
        "#####E######",
    ],
    # The detective's flat (only seen in the opening scene)
    "home": [
        "############",
        "#00___[_g__#",
        "#__________#",
        "#_<>__?____#",
        "#__________#",
        "#____y_____#",
        "#}_______]_#",
        "#__________#",
        "#####E######",
    ],
    # Za Za Bazaar, laid out like the map they hand you at the door: the bar along the back wall, the six food
    # stations in a row in front of it (desserts, salads, far east, tex mex, european, indian), the drinks station
    # by the salads, toilets top right, the way in bottom left, and the dining hall with booths, tables for four and
    # concrete pillars strung with lights.
    "zaza": [
        "####################################",
        "#giiiiiiiiiiKKKKKKKKKKiiiiiiiiWWViig#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#iiiiiiiiiiBBBBBBBBBBBBiiiiiiiiiiiii#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#iiSxxxiSxxxiSxxxiSxxxiSxxxiSxxxiiii#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#bhiiiiiiFxiiiiiiiiiiiiiiiiiiiiiiibh#",
        "#iiiiTiiiiiiiPiiiTiiiTiiiPiiiTiiiTii#",
        "#bhiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiibh#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#bhiiTiiiTiiiiiiiTiiiTiiiiiiiTiiiTbh#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#bhiiiiiiiiiiPiiiiiiiiiiiPiiiiiiiibh#",
        "#iiiiTiiiTiiiiiiiTiiiTiiiiiiiTiiiTii#",
        "#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii#",
        "#giiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiig#",
        "###E################################",
    ],
    "arcade": [                      # the arcade, and the old store room through the gap on the right
        "########################",
        "#1a2a3a4aa1a2a3a4#55557#",
        "#aaaaaaaaaaaaaaaa#iiiii#",
        "#aaaaaaaaaaaaaaaa#iiiii#",
        "#a4a3a2a1aaaaapaaiiii66#",
        "#aaaaaaaaaaaQXQQa#iiiii#",
        "#aaaaaaaaaaaaaaaa#7iii7#",
        "#gaaaaaaaaaaaaaag#77ii7#",
        "########E###############",
    ],
    "club": [
        "############",
        "#*___*ZZZZg#",
        "#__@@__p___#",
        "#ddddddXQQQ#",
        "#dddddd____#",
        "#dddddd_J_J#",
        "#dddddd____#",
        "#dddddd_J_J#",
        "#__________#",
        "#####E######",
    ],
    "kebab": [
        "############",
        "#ZZZ__IIZZg#",
        "#cc$pcccccc#",
        "#cQQXQQcccc#",
        "#cccccccccc#",
        "#cJcccJcccJ#",
        "#cccccccccc#",
        "#cJcccJcccJ#",
        "#cccccccccc#",
        "#####E######",
    ],
    "cafe": [
        "############",
        "#ZZZ__IIZZg#",
        "#cc_p_cccc #",
        "#cMQQXQcccc#",
        "#cccccccccc#",
        "#cJcccJcccJ#",
        "#cccccccccc#",
        "#cJcccJcccJ#",
        "#cccccccccc#",
        "#####E######",
    ],
    "corner": [
        "############",
        "#ZZZZZIIIZZ#",
        "#ffffffffff#",
        "#fZZfZZfZZf#",
        "#ffffffffff#",
        "#fZZfZZfZZf#",
        "#fpffffffff#",
        "#fXQQffffgf#",
        "#ffffffffff#",
        "#####E######",
    ],
    "clothes": [
        "############",
        "#ZZZZ_g_ZZZ#",
        "#__________#",
        "#_AA__AA__A#",
        "#__________#",
        "#_AA_y__AA_#",
        "#__________#",
        "#_pXQ____g_#",
        "#__________#",
        "#####E######",
    ],
    "books": [
        "############",
        "#ZZZZZZZZZZ#",
        "#wwwwwwwwww#",
        "#wZZwwwwZZw#",
        "#wwwwwwwwww#",
        "#wZZwJwwZZw#",
        "#wwwwwwwwww#",
        "#wpXQwwwwgw#",
        "#wwwwwwwwww#",
        "#####E######",
    ],
    "barber": [
        "############",
        "#OcOcOcOccg#",
        "#GcGcGcGccc#",
        "#cccccccccc#",
        "#ccpccccccc#",
        "#ccXQcccqcc#",
        "#cccccccccc#",
        "#ccccccccgc#",
        "#cccccccccc#",
        "#####E######",
    ],
    "gym": [
        "############",
        "#UUUU;;DDDD#",
        "#;;;;;;;;;;#",
        "#;N;;;N;;;;#",
        "#;;;;;;;;;;#",
        "#;;;;;;;N;;#",
        "#;;;;;;;;;;#",
        "#;pXQ;;;;g;#",
        "#;;;;;;;;;;#",
        "#####E######",
    ],
}
INTERIOR_WALLS = [(232, 220, 196), (210, 224, 206), (206, 220, 232), (232, 204, 188), (240, 236, 226), (220, 208, 230)]


# ============================================================== art helpers
def ellipse_shadow(w: int, h: int) -> pygame.Surface:
    s = pygame.Surface((max(2, w), max(2, h)), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, SHADOW_ALPHA), s.get_rect())
    return s


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# The looks you can switch between with Tab.  hair=None means bald.
# style: "short", "long" (hair to shoulders), "helmet", "cap", "bald", "robot"
CHARACTER_LOOKS = {
    "Jay":         dict(shirt="#2f95d0", skin="#c48647", hair="#333333", pants="#3b4250", style="short"),
    "Sam":         dict(shirt="#cd8c4a", skin="#ffd0a3", hair="#80582e", pants="#4a3a2c", style="short"),
    "Old Ted":     dict(shirt="#414141", skin="#ffd0a3", hair="#cccccc", pants="#2e2e2e", style="short"),
    "Rosa":        dict(shirt="#27ae60", skin="#ffd0a3", hair="#c48647", pants="#1b7b43", style="long"),
    "Cadet":       dict(shirt="#447746", skin="#c48647", hair="#39643b", pants="#305431", style="helmet", pack="#9f6d39"),
    "Courier":     dict(shirt="#6376a3", skin="#987047", hair="#8c7a6c", pants="#475577", style="cap"),
    "Suit":        dict(shirt="#414141", skin="#ffd0a3", hair=None, pants="#2e2e2e", style="bald", collar="#f2f2f2"),
    "Robot":       dict(shirt="#b3d9db", skin="#9cc0c2", hair="#f77118", pants="#728c8e", style="robot"),
    "Zombie":      dict(shirt="#c48647", skin="#5cbf7f", hair="#666666", pants="#9a6937", style="short"),
}

CHAR_W, CHAR_H = 44, 64          # logical size of one frame (feet at the bottom)
SUPERSAMPLE = 3                  # drawn 3x bigger then scaled down = smooth edges
WALK_FPS = 9


def draw_character(look: dict, direction: str, frame: int) -> pygame.Surface:
    """direction: 'down' | 'up' | 'left' | 'right'.  frame 0-3 (0 and 2 = legs together)."""
    if direction == "right":
        return pygame.transform.flip(draw_character(look, "left", frame), True, False)

    S = SUPERSAMPLE
    shirt, skin, pants = _rgb(look["shirt"]), _rgb(look["skin"]), _rgb(look["pants"])
    hair = _rgb(look["hair"]) if look["hair"] else None
    style = look["style"]
    shirt_d, skin_d, pants_d = _shade(shirt, 0.78), _shade(skin, 0.8), _shade(pants, 0.75)
    shoe = (40, 36, 34) if style != "robot" else _shade(pants, 0.6)

    surf = pygame.Surface((CHAR_W * S, CHAR_H * S), pygame.SRCALPHA)

    def R(x, y, w, h, c, r=0):
        pygame.draw.rect(surf, c, (round(x * S), round(y * S), round(w * S), round(h * S)), border_radius=round(r * S))

    def C(x, y, rad, c):
        pygame.draw.circle(surf, c, (round(x * S), round(y * S)), round(rad * S))

    def E(x, y, w, h, c):
        pygame.draw.ellipse(surf, c, (round(x * S), round(y * S), round(w * S), round(h * S)))

    swing = (0, 1, 0, -1)[frame % 4]      # leg/arm swing
    bob = 1 if frame % 2 else 0           # body dips on stride frames
    cx = CHAR_W / 2
    feet = CHAR_H - 2
    leg_top = 44
    head_y = 17 + bob
    head_r = 12.5
    body_top = 28 + bob

    # ---------------- legs
    if direction in ("down", "up"):
        for side, lift in ((-1, swing), (1, -swing)):
            lx = cx + side * 5 - 4
            ly = leg_top + bob
            lh = feet - ly - max(0, lift * 3)
            R(lx, ly, 8, lh, pants, 3)
            R(lx - 0.5, ly + lh - 4, 9, 5, shoe, 2)
    else:  # side view: legs stride forward/back
        for off, col in ((-swing * 4, pants_d), (swing * 4, pants)):
            lx = cx - 4 + off
            R(lx, leg_top + bob, 8, feet - leg_top - bob, col, 3)
            R(lx - 2, feet - 4, 11, 5, shoe, 2)

    # ---------------- back things (long hair / backpack) drawn behind the body
    if style == "long" and direction == "down":
        R(cx - 13, head_y - 2, 26, 22, hair, 8)
    if look.get("pack") and direction == "left":
        R(cx + 6, body_top + 1, 9, 15, _rgb(look["pack"]), 3)

    # ---------------- arms behind (side view back arm)
    arm_len = 15
    if direction == "left":
        R(cx - 3 - swing * 3, body_top + 2, 6, arm_len, shirt_d, 3)
        C(cx - swing * 3, body_top + arm_len + 1, 3, skin_d)

    # ---------------- torso
    tw = 24 if direction in ("down", "up") else 16
    R(cx - tw / 2, body_top, tw, 18, shirt, 7)
    R(cx - tw / 2, body_top + 13, tw, 5, shirt_d, 3)          # belt-line shading
    if look.get("collar") and direction == "down":
        pygame.draw.polygon(surf, _rgb(look["collar"]),
                            [((cx - 4) * S, body_top * S), ((cx + 4) * S, body_top * S), (cx * S, (body_top + 7) * S)])
    if look.get("pack") and direction == "up":
        R(cx - 9, body_top + 1, 18, 15, _rgb(look["pack"]), 4)
        R(cx - 9, body_top + 10, 18, 3, _shade(_rgb(look["pack"]), 0.8), 1)
    if style == "robot":
        C(cx, body_top + 8, 3, _rgb(look["hair"])) if direction == "down" else None

    # ---------------- arms in front
    if direction in ("down", "up"):
        for side, s in ((-1, swing), (1, -swing)):
            ax = cx + side * (tw / 2 + 2) - 3
            ay = body_top + 2 + s * 1.5
            R(ax, ay, 6, arm_len, shirt_d if direction == "up" else shirt, 3)
            C(ax + 3, ay + arm_len, 3.2, skin)
    else:
        R(cx - 3 + swing * 3, body_top + 2, 6, arm_len, shirt, 3)
        C(cx + swing * 3, body_top + arm_len + 1, 3.2, skin)

    # ---------------- head
    if style == "robot":
        metal, metal_d = skin, skin_d
        R(cx - 12, head_y - 12, 24, 22, metal, 7)
        R(cx - 12, head_y + 5, 24, 5, metal_d, 3)
        accent = _rgb(look["hair"])
        if direction == "down":
            R(cx - 9, head_y - 3, 18, 6, accent, 3)
        elif direction == "left":
            R(cx - 12, head_y - 3, 9, 6, accent, 3)
        R(cx - 1.5, head_y - 17, 3, 6, metal_d)                 # antenna
        C(cx, head_y - 17, 2.5, accent)
        return _finish(surf)

    C(cx, head_y, head_r, skin)                                  # face / head
    if direction == "left":
        C(cx - head_r + 1, head_y + 1, 2.5, skin)                # nose

    if hair is not None:
        if style in ("short", "long"):
            if direction == "down":
                R(cx - head_r, head_y - head_r, head_r * 2, head_r * 0.95, hair, 9)
                R(cx - head_r, head_y - 4, 4, 7, hair, 2)            # sideburns
                R(cx + head_r - 4, head_y - 4, 4, 7, hair, 2)
            elif direction == "up":
                C(cx, head_y, head_r, hair)
            else:
                R(cx - head_r + 3, head_y - head_r, head_r * 2 - 3, head_r * 0.95, hair, 9)
                R(cx + 1, head_y - 6, head_r - 1, 12, hair, 6)        # back of head
            if style == "long" and direction in ("up", "left"):
                R(cx - (11 if direction == "up" else -2), head_y, 22 if direction == "up" else 11, 16, hair, 6)
        elif style == "helmet":
            C(cx, head_y - 2, head_r + 1.5, hair)
            if direction != "up":
                R(cx - head_r - 1.5, head_y - 2, (head_r + 1.5) * 2, 4, _shade(hair, 0.8), 2)
            if direction == "down":
                R(cx - head_r + 2, head_y + 1, head_r * 2 - 4, 10, skin, 5)
            elif direction == "left":
                R(cx - head_r, head_y + 1, head_r, 10, skin, 5)
        elif style == "cap":
            R(cx - head_r, head_y - head_r - 1, head_r * 2, head_r + 1, hair, 9)
            if direction == "down":
                R(cx - head_r + 1, head_y - 3, head_r * 2 - 2, 3, _shade(hair, 0.75), 1)
            elif direction == "left":
                R(cx - head_r - 5, head_y - 3, 10, 3, _shade(hair, 0.75), 1)   # peak
            else:
                C(cx, head_y, head_r, hair)

    # eyes
    eye = (32, 30, 34)
    if direction == "down":
        R(cx - 6, head_y + 1, 3, 4, eye, 1)
        R(cx + 3, head_y + 1, 3, 4, eye, 1)
    elif direction == "left":
        R(cx - head_r + 3, head_y + 1, 3, 4, eye, 1)

    return _finish(surf)


def _finish(surf):
    """Scale down for smooth edges, then add a soft dark outline."""
    small = pygame.transform.smoothscale(surf, (CHAR_W, CHAR_H))
    mask = pygame.mask.from_surface(small, 60)
    outline = mask.to_surface(setcolor=(30, 30, 36, 150), unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface((CHAR_W + 2, CHAR_H + 2), pygame.SRCALPHA)
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        out.blit(outline, (dx, dy))
    out.blit(small, (1, 1))
    return out.convert_alpha()


def build_character_frames(look):
    return pa.character_frames(look)


# ============================================================== street art (Queens Road)
# Everything here is drawn in code in the same flat, outlined, three-quarter style as the rest.

BUILDING_STYLES = {
    # terrace: pale Georgian stone, slate roofs, shops on the ground floor
    "H": dict(height=128, stone=(236, 226, 200), stone_d=(204, 190, 160), roof=(92, 100, 114), roof_l=(110, 118, 132)),
    # columned hall
    "V": dict(height=150, stone=(240, 233, 214), stone_d=(206, 196, 172), roof=(150, 156, 162), roof_l=(166, 172, 178)),
    # stone tower
    "W": dict(height=232, stone=(214, 186, 134), stone_d=(176, 148, 102), roof=(196, 170, 120), roof_l=(214, 188, 138)),
}
BUILDING_CHARS = set(BUILDING_STYLES)
MAX_RISE = max(s["height"] for s in BUILDING_STYLES.values()) + TILE

SHOP_COLOURS = [(176, 48, 48), (36, 58, 104), (34, 110, 72), (28, 120, 130),
                (112, 52, 104), (196, 150, 40), (44, 44, 50), (200, 96, 40)]
GLASS = (64, 84, 104)
GLASS_L = (120, 150, 172)
FRAME = (246, 244, 236)
DARK = (40, 38, 42)


def _window(s, x, y, w, h, arch=False):
    pygame.draw.rect(s, FRAME, (x - 2, y - 2, w + 4, h + 4), border_radius=(w // 2 + 2) if arch else 1)
    pygame.draw.rect(s, GLASS, (x, y, w, h), border_radius=(w // 2) if arch else 0)
    pygame.draw.line(s, GLASS_L, (x + 3, y + h - 4), (x + w - 4, y + 4 if not arch else y + w // 2), 2)
    if not arch:
        pygame.draw.line(s, FRAME, (x, y + h // 2), (x + w, y + h // 2), 2)        # glazing bar


def make_facade(style: str, x: int, rear: bool) -> pygame.Surface:
    """The front (south-facing) face of one building tile, TILE wide and the style's height tall."""
    st = BUILDING_STYLES[style]
    Hh = st["height"]
    s = pygame.Surface((TILE, Hh), pygame.SRCALPHA)
    s.fill(st["stone"])
    for y in range(12, Hh, 14):                                   # stone courses
        pygame.draw.line(s, st["stone_d"], (0, y), (TILE, y), 1)
    pygame.draw.rect(s, st["stone_d"], (0, 0, TILE, 8))           # cornice
    pygame.draw.line(s, FRAME, (0, 8), (TILE, 8), 2)

    if style == "H":
        shop_h = 56
        for fy in range(16, Hh - shop_h - 30, 36):                 # upper-floor sash windows
            _window(s, 21, fy, 22, 26)
            pygame.draw.rect(s, st["stone_d"], (18, fy + 28, 28, 4))
        if rear:
            _window(s, 23, Hh - 44, 18, 22)
        else:
            colour = SHOP_COLOURS[((x // 3) * 5 + 3) % len(SHOP_COLOURS)]
            top = Hh - shop_h
            pygame.draw.rect(s, colour, (0, top, TILE, 12))                       # sign band
            pygame.draw.line(s, _shade(colour, 0.7), (0, top + 12), (TILE, top + 12), 2)
            for i in range(0, TILE, 16):                                          # striped awning
                pygame.draw.rect(s, colour, (i, top + 14, 8, 10))
                pygame.draw.rect(s, FRAME, (i + 8, top + 14, 8, 10))
            pygame.draw.line(s, _shade(colour, 0.6), (0, top + 24), (TILE, top + 24), 2)
            body = top + 26
            if x % 3 == 1:                                                         # shop door
                pygame.draw.rect(s, DARK, (16, body, 32, Hh - body - 4))
                pygame.draw.rect(s, _shade(colour, 0.8), (20, body + 3, 24, Hh - body - 7))
                pygame.draw.rect(s, GLASS, (24, body + 6, 16, 12))
                pygame.draw.circle(s, (230, 200, 90), (40, body + 18), 2)
            else:                                                                  # shop window
                pygame.draw.rect(s, DARK, (2, body, TILE - 4, Hh - body - 6))
                pygame.draw.rect(s, GLASS, (5, body + 3, TILE - 10, Hh - body - 12))
                pygame.draw.line(s, GLASS_L, (10, Hh - 12), (26, body + 6), 2)
                pygame.draw.line(s, GLASS_L, (20, Hh - 12), (34, body + 8), 1)
    elif style == "V":
        for px in (6, 38):                                                         # columns
            pygame.draw.rect(s, FRAME, (px, 16, 18, Hh - 28))
            pygame.draw.rect(s, st["stone_d"], (px + 13, 16, 5, Hh - 28))
            pygame.draw.rect(s, st["stone_d"], (px - 2, 12, 22, 6))
        _window(s, 26, 34, 10, 40)
        for i in range(3):                                                         # steps
            pygame.draw.rect(s, st["stone_d"] if i % 2 else FRAME, (0, Hh - 12 + i * 4, TILE, 4))
    elif style == "W":
        pygame.draw.rect(s, st["stone_d"], (0, 0, 6, Hh))                          # buttresses
        pygame.draw.rect(s, st["stone_d"], (TILE - 6, 0, 6, Hh))
        for fy in range(26, Hh - 50, 64):
            _window(s, 16, fy, 10, 40, arch=True)
            _window(s, 38, fy, 10, 40, arch=True)
        _window(s, 24, Hh - 44, 16, 36, arch=True)

    pygame.draw.rect(s, DARK, (0, Hh - 4, TILE, 4))                               # plinth line
    return s


def make_building_sprite(style: str, mask: int, facade) -> pygame.Surface:
    """Raised roof (top face) plus, when nothing is in front, the facade below it."""
    st = BUILDING_STYLES[style]
    Hh = st["height"]
    s = pygame.Surface((TILE, TILE + Hh), pygame.SRCALPHA)
    if style == "H":
        s.fill(st["roof"], (0, 0, TILE, TILE))
        for y in range(4, TILE, 12):                              # slate rows
            pygame.draw.line(s, st["roof_l"], (0, y), (TILE, y), 2)
    else:
        s.fill(st["roof"], (0, 0, TILE, TILE))
        pygame.draw.rect(s, st["roof_l"], (8, 8, TILE - 16, TILE - 16))
    edge = st["stone"]
    e = 7
    if not mask & 1: pygame.draw.rect(s, edge, (0, 0, TILE, e)); pygame.draw.line(s, DARK, (0, 0), (TILE, 0), 2)
    if not mask & 8: pygame.draw.rect(s, edge, (0, 0, e, TILE)); pygame.draw.line(s, DARK, (0, 0), (0, TILE), 2)
    if not mask & 2: pygame.draw.rect(s, edge, (TILE - e, 0, e, TILE)); pygame.draw.line(s, DARK, (TILE - 2, 0), (TILE - 2, TILE), 2)
    if style == "W":                                              # battlements on the tower edges
        for i in range(0, TILE, 16):
            if not mask & 1: pygame.draw.rect(s, st["stone_d"], (i, 0, 8, e))
            if not mask & 4: pygame.draw.rect(s, st["stone_d"], (i, TILE - e, 8, e))
    if not mask & 4:
        pygame.draw.rect(s, edge, (0, TILE - e, TILE, e))
        s.blit(facade, (0, TILE))
        pygame.draw.line(s, DARK, (0, TILE), (TILE, TILE), 2)
        if not mask & 8: pygame.draw.line(s, DARK, (0, TILE), (0, TILE + Hh), 2)
        if not mask & 2: pygame.draw.line(s, DARK, (TILE - 2, TILE), (TILE - 2, TILE + Hh), 2)
    return s.convert_alpha()


def make_zebra(road: pygame.Surface) -> pygame.Surface:
    s = road.copy()
    for y in (6, 38):
        pygame.draw.rect(s, (240, 240, 236), (4, y, TILE - 8, 20))
    return s


def make_lamp():
    s = pygame.Surface((24, 104), pygame.SRCALPHA)
    pole, pole_l = (34, 52, 44), (60, 86, 72)
    pygame.draw.rect(s, pole, (9, 18, 6, 80))
    pygame.draw.rect(s, pole_l, (10, 18, 2, 80))
    pygame.draw.rect(s, pole, (5, 94, 14, 8), border_radius=2)
    pygame.draw.polygon(s, pole, [(2, 8), (22, 8), (12, 0)])                    # cap
    pygame.draw.rect(s, pole, (4, 8, 16, 14))
    pygame.draw.rect(s, (255, 226, 140), (6, 10, 12, 10))                       # warm glass
    pygame.draw.rect(s, pole, (11, 10, 2, 10))
    return s.convert_alpha()


def make_bin():
    s = pygame.Surface((24, 34), pygame.SRCALPHA)
    body, body_d = (38, 74, 52), (28, 56, 40)
    pygame.draw.rect(s, body, (2, 8, 20, 24), border_radius=4)
    pygame.draw.rect(s, body_d, (2, 22, 20, 10), border_radius=4)
    pygame.draw.rect(s, (200, 170, 70), (2, 16, 20, 3))
    pygame.draw.ellipse(s, body_d, (0, 2, 24, 12))
    pygame.draw.ellipse(s, (20, 24, 22), (5, 5, 14, 6))
    return s.convert_alpha()


def make_bench():
    s = pygame.Surface((60, 40), pygame.SRCALPHA)
    wood, wood_d, iron = (176, 118, 64), (136, 88, 46), (44, 44, 48)
    for y in (2, 10):
        pygame.draw.rect(s, wood, (2, y, 56, 6), border_radius=2)
    pygame.draw.rect(s, wood_d, (2, 18, 56, 4))
    for y in (20, 26):
        pygame.draw.rect(s, wood, (2, y, 56, 5), border_radius=2)
    for x in (6, 50):
        pygame.draw.rect(s, iron, (x, 2, 4, 36))
    return s.convert_alpha()


def make_fountain():
    w, h, depth = 200, 136, 16
    s = pygame.Surface((w, h + depth + 70), pygame.SRCALPHA)
    oy = 70
    stone, stone_d, water, water_l = (226, 216, 192), (180, 168, 140), (70, 140, 200), (150, 200, 235)
    pygame.draw.ellipse(s, stone_d, (0, oy + depth, w, h))                      # rim front face
    pygame.draw.rect(s, stone_d, (0, oy + h // 2, w, depth))
    pygame.draw.ellipse(s, stone, (0, oy, w, h))                                # rim top
    pygame.draw.ellipse(s, water, (14, oy + 10, w - 28, h - 20))
    for i, (rx, ry) in enumerate(((60, 30), (100, 46), (140, 32))):
        pygame.draw.ellipse(s, water_l, (14 + w // 2 - rx, oy + h // 2 - ry // 2 + i * 6 - 6, rx * 2 - 28, ry), 2)
    cx = w // 2                                                                 # centre column + bowl
    pygame.draw.rect(s, stone_d, (cx - 9, oy + 10, 18, h // 2))
    pygame.draw.rect(s, stone, (cx - 9, oy + 10, 12, h // 2))
    pygame.draw.ellipse(s, stone_d, (cx - 34, oy + 4, 68, 22))
    pygame.draw.ellipse(s, stone, (cx - 34, oy, 68, 20))
    pygame.draw.ellipse(s, water, (cx - 26, oy + 4, 52, 12))
    for i, (dx, top) in enumerate(((0, 6), (-14, 26), (14, 26))):               # water jets
        pygame.draw.line(s, water_l, (cx + dx, oy + 8), (cx + dx * 2, top), 3)
    return s.convert_alpha(), oy + depth + h


def make_car(colour, facing_right):
    s = pygame.Surface((124, 78), pygame.SRCALPHA)
    dark = _shade(colour, 0.7)
    light = tuple(min(255, int(c * 1.15) + 10) for c in colour)
    for x in (18, 84):                                                          # wheels
        pygame.draw.ellipse(s, (26, 26, 28), (x, 54, 24, 22))
        pygame.draw.ellipse(s, (120, 120, 126), (x + 7, 61, 10, 8))
    pygame.draw.rect(s, dark, (2, 30, 120, 34), border_radius=10)               # side face
    pygame.draw.rect(s, colour, (2, 4, 120, 46), border_radius=14)              # top face
    pygame.draw.rect(s, GLASS, (30, 8, 64, 38), border_radius=8)                # windows
    pygame.draw.rect(s, light, (38, 12, 48, 30), border_radius=6)               # roof
    pygame.draw.line(s, GLASS_L, (34, 40), (40, 12), 2)
    pygame.draw.rect(s, (255, 236, 160), (114, 40, 6, 8), border_radius=2)      # headlight
    pygame.draw.rect(s, (200, 50, 50), (4, 40, 6, 8), border_radius=2)          # tail light
    if not facing_right:
        s = pygame.transform.flip(s, True, False)
    return s.convert_alpha()


def make_shelter():
    s = pygame.Surface((132, 92), pygame.SRCALPHA)
    frame = (60, 64, 72)
    glass = pygame.Surface((120, 56), pygame.SRCALPHA)
    glass.fill((170, 210, 230, 110))
    s.blit(glass, (6, 14))
    pygame.draw.rect(s, frame, (0, 4, 132, 12), border_radius=3)                # roof
    pygame.draw.rect(s, (90, 96, 106), (0, 0, 132, 6), border_radius=3)
    for x in (4, 64, 124):
        pygame.draw.rect(s, frame, (x, 14, 4, 76))
    pygame.draw.rect(s, (176, 118, 64), (20, 66, 92, 8), border_radius=2)       # seat
    pygame.draw.rect(s, (30, 90, 160), (90, 22, 26, 34))                        # timetable panel
    pygame.draw.rect(s, (240, 240, 240), (94, 26, 18, 6))
    return s.convert_alpha()


CAR_COLOURS = [(200, 52, 52), (40, 90, 170), (240, 240, 236), (50, 52, 58), (60, 140, 90), (230, 180, 50), (150, 156, 166)]


# ============================================================== real-street buildings (Queens Road from OpenStreetMap)
# Each OSM building gets its own colours, height and window style; the five landmarks get their own facades.

TOWER_HEIGHT = 330
IRON = (34, 36, 40)
SLATE_LINE = (126, 134, 146)
LANDMARK_STONE = {
    "V": ((238, 230, 210), (204, 192, 166)),     # Victoria Rooms - pale Bath stone
    "A": ((236, 226, 202), (200, 186, 156)),     # Royal West of England Academy
    "M": ((210, 196, 168), (170, 154, 124)),     # City Museum - grey-honey stone
    "G": ((196, 92, 70), (236, 220, 190)),       # Brown's - red with cream bands
    "W": ((214, 188, 138), (174, 148, 104)),     # Wills Memorial - honey stone
}


def _paving():
    s = pygame.Surface((TILE, TILE)).convert()
    s.fill((196, 196, 190))
    for i in range(0, TILE, 32):
        pygame.draw.line(s, (172, 172, 166), (i, 0), (i, TILE), 2)
        pygame.draw.line(s, (172, 172, 166), (0, i), (TILE, i), 2)
    pygame.draw.line(s, (210, 210, 204), (2, 2), (28, 2), 1)
    pygame.draw.line(s, (210, 210, 204), (34, 34), (60, 34), 1)
    return s


def _pointed(s, x, y, w, h, frame, glass=GLASS):
    """Gothic pointed-arch window."""
    pts = [(x - 2, y + h + 2), (x - 2, y + w // 2), (x + w // 2, y - 4), (x + w + 2, y + w // 2), (x + w + 2, y + h + 2)]
    pygame.draw.polygon(s, frame, pts)
    pts = [(x, y + h), (x, y + w // 2), (x + w // 2, y), (x + w, y + w // 2), (x + w, y + h)]
    pygame.draw.polygon(s, glass, pts)
    pygame.draw.line(s, frame, (x + w // 2, y + 2), (x + w // 2, y + h), 1)


def _balustrade(s, y, stone, dark):
    pygame.draw.rect(s, stone, (0, y, TILE, 12))
    for i in range(3, TILE, 8):
        pygame.draw.rect(s, dark, (i, y + 3, 3, 7))
    pygame.draw.line(s, dark, (0, y + 11), (TILE, y + 11), 1)


def make_osm_facade(b, lx, bw, tower, shopfront, door):
    """Front face of one tile of a real building.  lx = column within the building, bw = building width (tiles)."""
    style = b["style"]
    Hh = TOWER_HEIGHT if tower else b["height"]
    s = pygame.Surface((TILE, Hh), pygame.SRCALPHA)

    if style in ("H", "U"):
        stone = tuple(b["stone"])
        dark = _shade(stone, 0.84)
        s.fill(stone)
        for y in range(14, Hh, 15):
            pygame.draw.line(s, dark, (0, y), (TILE, y), 1)
        pygame.draw.rect(s, dark, (0, 0, TILE, 7))
        pygame.draw.line(s, FRAME, (0, 7), (TILE, 7), 2)
        ground = 54
        upper_top, upper_bottom = 14, Hh - ground - 6
        floors = max(1, (upper_bottom - upper_top) // 34)
        for f in range(floors):
            fy = upper_top + f * 34 + 4
            if style == "U":
                for wx in (8, 36):
                    pygame.draw.rect(s, FRAME, (wx - 1, fy - 1, 22, 26))
                    pygame.draw.rect(s, GLASS, (wx + 1, fy + 1, 18, 22))
                    pygame.draw.line(s, GLASS_L, (wx + 3, fy + 20), (wx + 12, fy + 4), 1)
                continue
            first = f == floors - 1                  # the floor just above the shops
            if b["variant"] == 2 and first and lx % 2 == 0:
                # bay window
                pygame.draw.rect(s, dark, (10, fy - 2, 44, 32))
                pygame.draw.rect(s, FRAME, (12, fy, 40, 28))
                for i, wx in enumerate((14, 27, 40)):
                    pygame.draw.rect(s, GLASS if i != 1 else _shade(GLASS, 1.15), (wx, fy + 2, 10, 24))
                continue
            arch = b["variant"] == 3 and f == 0
            _window(s, 21, fy, 22, 26, arch=arch)
            pygame.draw.rect(s, dark, (18, fy + 28, 28, 4))
            if b["variant"] == 1 and first:
                # cast-iron balcony
                pygame.draw.rect(s, IRON, (12, fy + 18, 40, 2))
                pygame.draw.rect(s, IRON, (12, fy + 30, 40, 2))
                for i in range(14, 52, 5):
                    pygame.draw.line(s, IRON, (i, fy + 18), (i, fy + 31), 1)
        gtop = Hh - ground
        if shopfront:
            colour = tuple(b["awning"])
            pygame.draw.rect(s, colour, (0, gtop, TILE, 12))
            pygame.draw.line(s, _shade(colour, 0.7), (0, gtop + 12), (TILE, gtop + 12), 2)
            if lx % 2 == 0:                                  # fake lettering on the fascia
                for i in range(6, 58, 7):
                    pygame.draw.rect(s, FRAME, (i, gtop + 4, 4, 4))
            for i in range(0, TILE, 16):
                pygame.draw.rect(s, colour, (i, gtop + 14, 8, 9))
                pygame.draw.rect(s, FRAME, (i + 8, gtop + 14, 8, 9))
            pygame.draw.line(s, _shade(colour, 0.6), (0, gtop + 23), (TILE, gtop + 23), 2)
            body = gtop + 25
            if door:
                pygame.draw.rect(s, DARK, (16, body, 32, Hh - body - 4))
                pygame.draw.rect(s, _shade(colour, 0.85), (20, body + 3, 24, Hh - body - 7))
                pygame.draw.rect(s, GLASS, (24, body + 6, 16, 12))
                pygame.draw.circle(s, (230, 200, 90), (40, body + 18), 2)
            else:
                pygame.draw.rect(s, DARK, (2, body, TILE - 4, Hh - body - 6))
                pygame.draw.rect(s, GLASS, (5, body + 3, TILE - 10, Hh - body - 12))
                pygame.draw.line(s, GLASS_L, (10, Hh - 12), (26, body + 6), 2)
                # goods in the window
                for i, c in enumerate(((220, 200, 160), colour, (240, 240, 230))):
                    pygame.draw.rect(s, c, (10 + i * 15, Hh - 20, 10, 8))
        else:
            if b["variant"] == 3:                            # rusticated ground floor
                for y in range(gtop, Hh, 9):
                    pygame.draw.line(s, dark, (0, y), (TILE, y), 2)
            if door:
                pygame.draw.rect(s, dark, (14, gtop + 4, 36, Hh - gtop - 4))
                pygame.draw.ellipse(s, FRAME, (18, gtop + 4, 28, 16))
                pygame.draw.ellipse(s, GLASS, (21, gtop + 7, 22, 10))
                door_col = ((32, 44, 70), (90, 30, 34), (30, 60, 44), (24, 24, 28))[b["variant"]]
                pygame.draw.rect(s, door_col, (20, gtop + 16, 24, Hh - gtop - 22))
                pygame.draw.circle(s, (210, 180, 80), (39, gtop + 32), 2)
                pygame.draw.rect(s, dark, (12, Hh - 8, 40, 4))   # step
            else:
                _window(s, 21, gtop + 10, 22, 30)
                # basement railings
                pygame.draw.rect(s, IRON, (0, Hh - 16, TILE, 2))
                for i in range(2, TILE, 6):
                    pygame.draw.line(s, IRON, (i, Hh - 16), (i, Hh - 5), 1)
        pygame.draw.rect(s, DARK, (0, Hh - 4, TILE, 4))
        return s

    stone, dark = LANDMARK_STONE[style]
    s.fill(stone)
    cx_global = lx * TILE + TILE // 2
    centre = bw * TILE / 2

    if style == "V":                                         # Victoria Rooms: Corinthian portico + pediment
        for y in range(10, Hh, 16):
            pygame.draw.line(s, dark, (0, y), (TILE, y), 1)
        mid = abs(cx_global - centre) < TILE * 3
        if mid:
            for px in (4, 36):
                pygame.draw.rect(s, FRAME, (px, 34, 20, Hh - 52))
                pygame.draw.rect(s, dark, (px + 14, 34, 6, Hh - 52))
                pygame.draw.rect(s, dark, (px - 3, 28, 26, 8))      # capital
                pygame.draw.rect(s, dark, (px - 3, Hh - 20, 26, 6))  # base
            pygame.draw.rect(s, _shade(dark, 0.7), (26, 40, 8, Hh - 62))
        else:
            _window(s, 18, 40, 28, 44)
            _window(s, 20, Hh - 62, 24, 34)
        # pediment across the middle
        ped_half = TILE * 3
        for x in range(TILE):
            gx = lx * TILE + x
            t = 1 - abs(gx - centre) / ped_half
            if t > 0:
                top = int(28 - t * 26)
                pygame.draw.line(s, dark, (x, top), (x, 30))
                if top + 3 < 28:
                    pygame.draw.line(s, stone, (x, top + 3), (x, 26))
        pygame.draw.rect(s, dark, (0, 28, TILE, 5))
        for i in range(4):                                        # steps
            pygame.draw.rect(s, FRAME if i % 2 else dark, (0, Hh - 14 + i * 3, TILE, 3))

    elif style == "A":                                       # Royal West of England Academy
        for y in range(Hh - 60, Hh, 9):                           # rusticated ground floor
            pygame.draw.line(s, dark, (0, y), (TILE, y), 2)
        _window(s, 20, Hh - 52, 24, 34, arch=True)
        _balustrade(s, 0, stone, dark)
        pygame.draw.rect(s, dark, (0, 12, TILE, 4))
        for px in (6, 46):                                        # paired columns
            pygame.draw.rect(s, FRAME, (px, 22, 12, Hh - 90))
            pygame.draw.rect(s, dark, (px + 8, 22, 4, Hh - 90))
        pygame.draw.rect(s, _shade(dark, 0.8), (22, 30, 20, 44), border_radius=10)   # statue niche
        pygame.draw.ellipse(s, FRAME, (26, 38, 12, 12))
        pygame.draw.rect(s, FRAME, (27, 48, 10, 22), border_radius=3)
        pygame.draw.rect(s, dark, (0, Hh - 66, TILE, 6))

    elif style == "M":                                       # City Museum & Art Gallery
        _balustrade(s, 0, stone, dark)
        pygame.draw.rect(s, dark, (0, 12, TILE, 5))
        for y in range(Hh - 70, Hh, 10):
            pygame.draw.line(s, dark, (0, y), (TILE, y), 1)
        entrance = abs(cx_global - centre) < TILE
        if entrance:
            pygame.draw.rect(s, FRAME, (6, 30, 52, Hh - 34), border_radius=26)
            pygame.draw.rect(s, (60, 46, 34), (12, 38, 40, Hh - 42), border_radius=20)
            pygame.draw.rect(s, (230, 200, 120), (28, 30, 8, 10))               # keystone
        else:
            for wx, wy, ww, wh in ((18, 30, 28, 46), (18, Hh - 62, 28, 46)):
                _window(s, wx, wy, ww, wh, arch=True)
                pygame.draw.rect(s, (226, 212, 180), (wx + ww // 2 - 4, wy - 6, 8, 8))   # keystone
            pygame.draw.rect(s, FRAME, (0, 26, 6, Hh - 30))
            pygame.draw.rect(s, FRAME, (TILE - 6, 26, 6, Hh - 30))

    elif style == "G":                                       # Brown's: Venetian gothic, red with cream bands
        for y in range(10, Hh, 22):
            pygame.draw.rect(s, dark, (0, y, TILE, 5))
        for wy in (24, Hh - 70):
            _pointed(s, 10, wy, 18, 40, dark)
            _pointed(s, 36, wy, 18, 40, dark)
        pygame.draw.rect(s, dark, (0, 0, TILE, 8))

    elif style == "W":                                       # Wills Memorial Building: Gothic revival
        pygame.draw.rect(s, dark, (0, 0, 7, Hh))                  # buttresses
        pygame.draw.rect(s, dark, (TILE - 7, 0, 7, Hh))
        for y in range(16, Hh, 18):
            pygame.draw.line(s, dark, (7, y), (TILE - 7, y), 1)
        if tower:
            for i in range(0, TILE, 12):                          # battlements
                pygame.draw.rect(s, dark, (i, 0, 6, 10))
            for x in (16, 36):                                    # belfry louvres
                _pointed(s, x, 22, 12, 60, dark, glass=(70, 60, 54))
                for ly in range(44, 82, 6):
                    pygame.draw.line(s, dark, (x, ly), (x + 12, ly), 1)
            _pointed(s, 20, 110, 24, 110, dark)                   # tall lancet
            pygame.draw.line(s, dark, (20, 170), (44, 170), 2)
            _pointed(s, 14, Hh - 80, 36, 76, dark, glass=(60, 46, 36))   # great doorway
        else:
            _pointed(s, 22, 26, 20, 60, dark)
            _pointed(s, 22, Hh - 74, 20, 56, dark)

    pygame.draw.rect(s, DARK, (0, Hh - 4, TILE, 4))
    return s


def make_osm_roof(b, mask, tower, chimney):
    """Top face of one building tile (TILE x TILE)."""
    s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    style = b["style"]
    if style == "H":
        roof = tuple(b["roof"])
        s.fill(roof)
        for y in range(4, TILE, 10):
            pygame.draw.line(s, _shade(roof, 1.18), (0, y), (TILE, y), 2)
        edge = tuple(b["stone"])
    elif style == "U":                                        # flat roof with standing seams
        s.fill((150, 152, 156))
        for x in (0, 32):
            pygame.draw.line(s, (172, 174, 178), (x + 1, 0), (x + 1, TILE), 2)
        edge = tuple(b["stone"])
    elif style == "G":                                        # Brown's: slate roof, cream parapet
        s.fill((88, 94, 106))
        for y in range(4, TILE, 10):
            pygame.draw.line(s, (108, 114, 126), (0, y), (TILE, y), 2)
        edge = LANDMARK_STONE["G"][1]
    else:                                                     # lead roof with standing seams
        stone, dark = LANDMARK_STONE[style]
        s.fill((150, 156, 162))
        for x in (0, 32):
            pygame.draw.line(s, (176, 182, 188), (x + 1, 0), (x + 1, TILE), 2)
            pygame.draw.line(s, (128, 134, 140), (x + 3, 0), (x + 3, TILE), 1)
        edge = stone
        if tower:
            s.fill(LANDMARK_STONE["W"][1])
            pygame.draw.rect(s, (120, 110, 96), (16, 16, 32, 32))
    e = 7
    if not mask & 1: pygame.draw.rect(s, edge, (0, 0, TILE, e)); pygame.draw.line(s, DARK, (0, 0), (TILE, 0), 2)
    if not mask & 8: pygame.draw.rect(s, edge, (0, 0, e, TILE)); pygame.draw.line(s, DARK, (0, 0), (0, TILE), 2)
    if not mask & 2: pygame.draw.rect(s, edge, (TILE - e, 0, e, TILE)); pygame.draw.line(s, DARK, (TILE - 2, 0), (TILE - 2, TILE), 2)
    if not mask & 4: pygame.draw.rect(s, edge, (0, TILE - e, TILE, e))
    if tower and not mask & 1:
        for i in range(0, TILE, 16):
            pygame.draw.rect(s, LANDMARK_STONE["W"][1], (i, 0, 8, e + 2))
    if chimney:                                                   # chimney stack with pots
        brick, brick_d = (150, 86, 64), (112, 62, 46)
        pygame.draw.rect(s, brick_d, (4, 18, 20, 22))
        pygame.draw.rect(s, brick, (4, 14, 20, 18))
        for px in (8, 16):
            pygame.draw.rect(s, (190, 110, 70), (px, 8, 5, 8))
            pygame.draw.rect(s, (60, 40, 30), (px + 1, 8, 3, 2))
    return s


def make_osm_tile(b, mask, tower, chimney, facade):
    roof = make_osm_roof(b, mask, tower, chimney)
    if facade is None:
        return roof.convert_alpha()
    Hh = facade.get_height()
    s = pygame.Surface((TILE, TILE + Hh), pygame.SRCALPHA)
    s.blit(roof, (0, 0))
    s.blit(facade, (0, TILE))
    pygame.draw.line(s, DARK, (0, TILE), (TILE, TILE), 2)
    if not mask & 8: pygame.draw.line(s, DARK, (0, TILE), (0, TILE + Hh), 2)
    if not mask & 2: pygame.draw.line(s, DARK, (TILE - 2, TILE), (TILE - 2, TILE + Hh), 2)
    return s.convert_alpha()


# ============================================================== world
class Sprite:
    """Anything drawn in the depth-sorted layer: walls, trees, props.
    image can be None with a `make` function: it's then drawn the first time it comes on screen."""
    __slots__ = ("image", "pos", "sort_y", "faded", "rect", "make", "cut", "cut_img")

    def __init__(self, image, pos, sort_y, fade=False, size=None, make=None):
        self.image = image
        self.make = make
        self.pos = (round(pos[0]), round(pos[1]))
        self.sort_y = sort_y
        self.rect = pygame.Rect(self.pos, size or image.get_size())
        self.faded = None
        self.cut = False                    # far-side building: turns see-through when you walk behind it
        self.cut_img = None
        if fade:
            self.faded = image.copy()
            self.faded.set_alpha(CANOPY_FADE_ALPHA)


class World:
    def __init__(self, map_def, sheet=None, interior=None, hour=12.0, past=False):
        self.real = None                              # OpenStreetMap data for real streets
        self._map_def = map_def
        self.shapes = [] if isinstance(map_def, str) else list(getattr(map_def, "GROUND_SHAPES", []))
        self.interior = interior                      # dict(kind, seed) when this world is inside a shop
        self.lamp_style = getattr(map_def, "LAMP_STYLE", "modern") if not isinstance(map_def, str) else "modern"
        self.doors = {}                               # (x, y) of a shop's door tile -> shop info
        self.signal_spots = []                        # traffic lights (drawn by the traffic system)
        self.anims = []                               # animated things: (frames, pos, sort_y, fps)
        self.actors = []                              # NPCs
        self.traffic = None
        self.vtraffic = None
        self.deck = None
        self.extra_solids = []                        # moving things you can bump into (cars, people)
        self.time = 0.0
        self.hour = hour
        self.lamp_spots = []                          # street lamps (light up at night)
        self.feature_lights = []                      # floodlights, the lit waterfall...
        self.exit_tile = None
        self.cabinets = []                            # arcade machines: (front area you stand in, machine)
        self.zaza = dict(stations=[], bar=[], booths=[], tables=[], pillars=[], drinks=[], bulbs=[], neon=None)
        if not isinstance(map_def, str):
            for shop in getattr(map_def, "SHOPS", []):
                self.doors[tuple(shop["door"])] = shop
        if isinstance(map_def, str):
            rows = map_def.strip("\n").splitlines()
        else:
            rows = list(map_def.ROWS)
            alph = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_."
            ids = [[-1 if r[i:i + 2] == "~~" else alph.index(r[i]) * 64 + alph.index(r[i + 1])
                    for i in range(0, len(r), 2)] for r in map_def.BUILDING_IDS]
            self.real = dict(ids=ids, buildings=map_def.BUILDINGS,
                             tower=set(map(tuple, map_def.TOWER_TILES)),
                             attribution=getattr(map_def, "ATTRIBUTION", ""))
        self.h = len(rows)
        self.w = max(len(r) for r in rows)
        self.grid = [list(r.ljust(self.w, ".")) for r in rows]
        self.pixel_w, self.pixel_h = self.w * TILE, self.h * TILE
        self.sheet = sheet
        self.rng = random.Random(MAP_SEED)

        self._load_art()
        self.spawn = (self.pixel_w / 2, self.pixel_h / 2)
        self.ground = [[self._ground_char(x, y) for x in range(self.w)] for y in range(self.h)]

        self.sprites: list[Sprite] = []
        self.solids: list[pygame.Rect] = []
        self.decals: list[tuple[pygame.Surface, tuple[int, int]]] = []   # rugs + shadows, baked into ground
        for kind_, dcx, dcy, r in (getattr(map_def, "DECALS", []) if not isinstance(map_def, str) else []):
            if kind_ == "compass":                        # set into the paving, under everything else
                img = pa.compass_rose(r)
                self.decals.insert(0, (img, (int(dcx * TILE - img.get_width() / 2), int(dcy * TILE - img.get_height() / 2))))
        self._build()
        if self.interior is not None and self.interior["kind"] == "zaza":
            self._zaza_finish()
        if not isinstance(map_def, str) and getattr(map_def, "CRIME_SCENE", None) and not past:
            self._crime_scene(map_def.CRIME_SCENE)
        if (self.interior or {}).get("variant") == "packed":          # papers all over the floor
            prng = random.Random(5)
            for y in range(1, self.h - 1):
                for x in range(1, self.w - 1):
                    if self.grid[y][x] == "_" and prng.random() < 0.13:
                        self.decals.append((self.real_cache.setdefault(("papers", (x + y) % 4), pa.papers_decal((x + y) % 4)),
                                            (x * TILE, y * TILE)))

        if not isinstance(map_def, str):
            for orn in getattr(map_def, "ORNAMENTS", []):
                ox_, oy_ = orn["tile"]
                b = self.real["buildings"][self.real["ids"][oy_][ox_]]
                img = self.real_cache.setdefault(("orn", orn["kind"], orn.get("flip", False)),
                                                 pa.unicorn(orn.get("flip", False)))
                top = oy_ * TILE - pa.building_height(b) * pa.PX
                self.sprites.append(Sprite(img, (ox_ * TILE + TILE // 2 - img.get_width() // 2, top - img.get_height() + 28),
                                           oy_ * TILE + TILE + 1))

        if not isinstance(map_def, str) and getattr(map_def, "BRIDGE", None):
            self._build_bridge(map_def.BRIDGE)
        st = getattr(map_def, "STAIRS", None) if not isinstance(map_def, str) else None
        self.stairs = None
        if st and "rect" in st:
            x0, y0, x1, y1 = st["rect"]
            self.stairs = dict(st, area=pygame.Rect(int(x0 * TILE), int(y0 * TILE), int((x1 - x0) * TILE), int((y1 - y0) * TILE)))
            if st.get("path"):                                 # stairs with turns: segments from the top down
                segs = []
                for (sx0, sy0, sx1, sy1, high) in st["path"]:
                    r = pygame.Rect(int(sx0 * TILE), int(sy0 * TILE), int((sx1 - sx0) * TILE), int((sy1 - sy0) * TILE))
                    segs.append((r, high, 0 if high == "flat" else (r.w if high in ("left", "right") else r.h)))
                self.stairs["segments"] = segs
                self.stairs["path_len"] = sum(n for _, _, n in segs)
            if st.get("turn"):
                tx0, ty0, tx1, ty1 = st["turn"]
                self.stairs["turn_area"] = pygame.Rect(int(tx0 * TILE), int(ty0 * TILE), int((tx1 - tx0) * TILE), int((ty1 - ty0) * TILE))
            if st.get("mode") == "rise" and not st.get("open_top"):   # can't walk off the top of the stairs (only up through the portal)
                a = self.stairs["area"]
                if st.get("axis") == "x":
                    self.solids.append(pygame.Rect(a.x - 14, a.y, 14, a.h))
                elif st.get("climb") == "up":                  # climbing up the screen: the top end is the edge
                    self.solids.append(pygame.Rect(a.x, a.top - 10, a.w, 14))
                else:
                    self.solids.append(pygame.Rect(a.x, a.bottom - 4, a.w, 14))
        for x0, y0, x1, y1 in (getattr(map_def, "BLOCKERS", []) if not isinstance(map_def, str) else []):
            self.solids.append(pygame.Rect(int(x0 * TILE), int(y0 * TILE), int((x1 - x0) * TILE), int((y1 - y0) * TILE)))
        for x0, y0, x1, y1 in (getattr(map_def, "GREY_AREAS", []) if not isinstance(map_def, str) else []):
            wash = pygame.Surface((int((x1 - x0) * TILE), int((y1 - y0) * TILE)), pygame.SRCALPHA)
            wash.fill((196, 196, 204, 150))                 # the upper level: seen, but greyed out
            self.decals.append((wash, (int(x0 * TILE), int(y0 * TILE))))
        for rx, ry0, ry1 in (getattr(map_def, "RAILS_V", []) if not isinstance(map_def, str) else []):
            img = pa.railing_v()
            for ry in range(ry0, ry1 + 1):
                self.sprites.append(Sprite(img, (rx * TILE - img.get_width() // 2, ry * TILE - 36), (ry + 1) * TILE - 2))
        for k_, ss in enumerate(getattr(map_def, "SIDE_STRIPS", []) if not isinstance(map_def, str) else []):
            img = pa.side_strip(ss["kind"], ss["rows"], tuple(r - ss["y0"] for r in ss.get("doors", ())),
                                ss.get("facing", "east"), k_, ss.get("sign"))
            x0 = ss["x"] * TILE if ss.get("facing", "east") == "east" else ss["x"] * TILE - img.get_width()
            for r in range(ss["rows"]):                      # one slice per row so people sort in front/behind properly
                part = img.subsurface((0, r * TILE, img.get_width(), TILE))
                self.sprites.append(Sprite(part, (x0, (ss["y0"] + r) * TILE), (ss["y0"] + r + 1) * TILE - 6 + ss.get("sort_dy", 0)))
        for (wx0, wx1, wy) in (getattr(map_def, "STAIR_WALLS_H", []) if not isinstance(map_def, str) else []):
            img = pygame.transform.rotate(pa.stair_wall("left"), 90)       # same dark stone as the stairwell walls
            for wx in range(wx0, wx1):
                top = wy * TILE - img.get_height() // 2
                self.sprites.append(Sprite(img, (wx * TILE, top), wy * TILE + img.get_height() // 2))
                self.solids.append(pygame.Rect(wx * TILE, top, TILE, img.get_height()))
        for wf in (getattr(map_def, "WALL_FACES", []) if not isinstance(map_def, str) else []):
            b = dict(style="P", pennant=True, stone=wf.get("stone", (112, 106, 100)), seed=wf.get("seed", 5),
                     door_lx=wf.get("door_lx", -1), h=wf["h"] * pa.L)
            for lx in range(wf["w"]):
                img = pa.up(pa._concrete(b, lx, wf["w"])).convert_alpha()
                self.sprites.append(Sprite(img, ((wf["x"] + lx) * TILE, wf["y"] * TILE), (wf["y"] + wf["h"]) * TILE - 6))
            self.solids.append(pygame.Rect(wf["x"] * TILE, wf["y"] * TILE, wf["w"] * TILE, wf["h"] * TILE))
        for se in (getattr(map_def, "SIDE_ENTRANCES", []) if not isinstance(map_def, str) else []):
            img = pa.omg_side(se["rows"], se["door_row"] - se["y0"])
            self.sprites.append(Sprite(img, (se["x"] * TILE - img.get_width(), se["y0"] * TILE), (se["door_row"] + 1) * TILE + 20))
        self.portals = []
        for pt in (getattr(map_def, "PORTALS", []) if not isinstance(map_def, str) else []):
            x0, y0, x1, y1 = pt["rect"]
            self.portals.append(dict(pt, area=pygame.Rect(int(x0 * TILE), int(y0 * TILE), int((x1 - x0) * TILE), int((y1 - y0) * TILE))))

        # ---- the water: every water tile and which of its sides are land (for the foam / quay edge)
        self.water_cells = {}
        for y in range(self.h):
            for x in range(self.w):
                if self.ground[y][x] == "~":
                    land = lambda xx, yy: 0 <= xx < self.w and 0 <= yy < self.h and self.ground[yy][xx] != "~"
                    self.water_cells[(x, y)] = (1 if land(x, y - 1) else 0) | (2 if land(x + 1, y) else 0) | \
                                               (4 if land(x, y + 1) else 0) | (8 if land(x - 1, y) else 0)
        for bx, by, kind, colour, flip in (getattr(map_def, "BOATS", []) if not isinstance(map_def, str) else []):
            col = pa.BOAT_COLOURS[colour % len(pa.BOAT_COLOURS)]
            frames = self.real_cache.setdefault(("boat", kind, col, flip), [pa.boat(kind, col, f, flip) for f in range(4)])
            foot = by * TILE
            self.anims.append((frames, (bx * TILE - frames[0].get_width() / 2, foot - frames[0].get_height() + 8), foot, 2.5))

        self.solid_grid: dict[tuple[int, int], list[pygame.Rect]] = {}
        for r in self.solids:
            for key in self._cells(r):
                self.solid_grid.setdefault(key, []).append(r)
        size = TILE * CHUNK_TILES
        self.sprite_chunks: dict[tuple[int, int], list[Sprite]] = {}
        for sp in self.sprites:
            key = (sp.rect.centerx // size, sp.rect.centery // size)
            self.sprite_chunks.setdefault(key, []).append(sp)

        self.chunk_cache: "OrderedDict[tuple[int, int], pygame.Surface]" = OrderedDict()

        # ---- life: NPCs, traffic, fountains
        floor = set("cf_;wyai")
        self.free_floor = [(x, y) for y in range(self.h) for x in range(self.w)
                           if self.grid[y][x] in floor and not any(r.colliderect(pygame.Rect(x * TILE + 8, y * TILE + 8, TILE - 16, TILE - 16))
                                                                    for r in self.solid_grid.get((x, y), ()))]
        self.free_set = set(self.free_floor)
        if self.interior is not None:
            self.actors = people.populate_interior(self, self.interior["kind"], self.interior["seed"], hour)
        elif self.real is not None:
            if getattr(map_def, "NAME", "") == "Frogmore Street":
                self.actors = people.populate_frogmore(self, map_def)
            elif getattr(map_def, "NAME", "") == "Harbourside":
                self.actors = people.populate_harbour(self, map_def)
            else:
                self.actors = people.populate_street(self, map_def)
            self.traffic = traffic.Traffic(self, getattr(map_def, "SIDE_ROAD", None))
            self.vtraffic = traffic.VerticalTraffic(self, map_def.LOWER_ROAD) if getattr(map_def, "LOWER_ROAD", None) else None
            if self.traffic.ok and getattr(map_def, "SIDE_ROAD", None):
                self.traffic.join(self.vtraffic)                      # cars turn between the two roads at the junction
            self.deck = traffic.DeckTraffic(self, map_def.BRIDGE_TRAFFIC) if getattr(map_def, "BRIDGE_TRAFFIC", None) else None
            night = hour >= 20.5 or hour < 5.5
            for n in self.actors:
                n.shown = n.active(hour)
                n.set_phase("night" if night else "day")
            self._collect_lights()
            jets = [pa.jet(i) for i in range(6)]
            for jx, jy in getattr(map_def, "FOUNTAIN_JETS", []):
                foot = jy * TILE
                self.anims.append((jets, (jx * TILE - jets[0].get_width() / 2, foot - jets[0].get_height()), foot + 2, 8))

    # ---------------------------------------------------- art
    def _load_art(self):
        pz = pa.pixelize
        self.grass = [pa.grass_tile(i) for i in range(8)]
        self.dirt = [pa.gravel_tile(i) for i in range(3)]
        kind = getattr(self._map_def, "WATER", "clear") if not isinstance(self._map_def, str) else "clear"
        self.water_anim = pa.water_frames(kind)          # running water: redrawn every frame over the ground
        self.water = [self.water_anim[0].subsurface((0, 0, TILE, TILE))]
        self.water_edges = {}                             # (land sides mask, frame) -> foam overlay
        self.pontoon = [pa.pontoon_tile(i) for i in range(3)]
        self.paving = [pa.paving_tile(i) for i in range(4)]
        self.concrete = [pa.paving_tile(i, base=(176, 180, 182)) for i in range(2)]
        self.wood = [pa.wood_floor_tile(i) for i in range(3)]
        self.road = [pa.road_tile(i) for i in range(6)]
        self.road_line_h = pa.road_tile(1, "h")
        self.road_line_v = pa.road_tile(1, "v")
        self.zebra = pa.road_tile(2, "zebra")
        self.real_cache = {}

        self.trees = [pa.tree(k, k) for k in (0, 1, 2)]
        self.tree_shadow = pz(ellipse_shadow(92, 32))

        # street pieces
        self.lamp = pa.lamp_post(self.lamp_style)
        self.path_tiles = [pa.paving_tile(i, base=(214, 206, 186)) for i in range(3)]
        self.setts = [pa.setts_tile(i) for i in range(4)]
        self.mat = pa.door_mat()
        self.exit_mat = pa.exit_mat()
        self.stairs_tiles = {}
        self.deep_road = [pa.deep_road_tile(i) for i in range(3)]
        self.deep_road_c = pa.deep_road_tile(1, centre=True)
        self.floors = {"d": [pa.floor_tile("dance", i) for i in range(4)],
                       "c": [pa.floor_tile("checker", 0)], ";": [pa.floor_tile("rubber", i) for i in range(2)],
                       "f": [pa.floor_tile("shop", 0)], "w": [pa.floor_tile("carpet", i) for i in range(2)],
                       "a": [pa.arcade_carpet(i) for i in range(4)], "i": [pa.concrete_floor(i) for i in range(6)]}
        self.void = pygame.Surface((TILE, TILE)).convert(); self.void.fill((0, 0, 0))
        self.car_cache = {}
        self.bin = pa.bin_()
        self.bench = pa.bench()
        self.fountain, self.fountain_base = pa.fountain()
        self.shelter = pa.bus_shelter()
        self.post_box = pa.post_box()
        self.bike_rack = pa.bike_rack()
        self.signal = pa.traffic_signal()
        self.railing = pa.railing()
        self.statues = [pa.statue(i) for i in range(2)]
        self.autumn = [pa.tree(3, k) for k in range(3)]
        self.building_cache = {}

    # ---------------------------------------------------- building
    def at(self, x, y, default="#"):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return default

    def _ground_char(self, x, y):
        ch = self.grid[y][x]
        if ch not in OBJECT_CHARS:
            return ch
        if ch == "H" and self.real is not None:
            return "-"                       # under a building (seen through see-through roofs): paving
        if ch in "LnquokYTPF|^Jg&" and any(self.at(x + dx, y + dy, ".") == "-" for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))):
            return "-"                       # street furniture stands on the pavement, never on the road
        counts = {}
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            n = self.at(x + dx, y + dy, ".")
            if n not in OBJECT_CHARS and n != "~":
                counts[n] = counts.get(n, 0) + 1
        return max(counts, key=counts.get) if counts else "."

    def _build(self):
        rng = self.rng
        for y in range(self.h):
            for x in range(self.w):
                ch = self.grid[y][x]
                cx, cy = x * TILE + TILE // 2, y * TILE + TILE // 2
                tile_rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)

                if ch in ZAZA_CHARS and self.interior is not None and self.interior["kind"] == "zaza":
                    self._zaza_prop(ch, x, y, cx, cy, tile_rect)
                elif ch == "~":
                    self.solids.append(tile_rect)
                elif ch == "#":
                    self.solids.append(tile_rect)
                    mask = 0
                    if self.at(x, y - 1, ".") == "#": mask |= 1
                    if self.at(x + 1, y, ".") == "#": mask |= 2
                    if self.at(x, y + 1, ".") == "#": mask |= 4
                    if self.at(x - 1, y, ".") == "#": mask |= 8
                    seed = self.interior["seed"] if self.interior is not None else 0
                    colour = INTERIOR_WALLS[seed % len(INTERIOR_WALLS)]
                    if self.interior is not None and self.interior["kind"] == "zaza":
                        colour = (172, 164, 152)                       # rough-rendered walls
                    key = ("wall", mask, colour)
                    if key not in self.real_cache:
                        self.real_cache[key] = pa.interior_wall(mask, colour)
                    img, wh = self.real_cache[key]
                    self.sprites.append(Sprite(img, (x * TILE, y * TILE - wh), tile_rect.bottom))
                elif ch == " ":
                    self.solids.append(tile_rect)
                elif ch == "E":
                    self.exit_tile = (x, y)
                    self.decals.append((self.exit_mat, tile_rect.topleft))
                    self.spawn = (cx, cy - TILE + 8)
                elif ch in ARCADE_MACHINES and self.interior is not None:     # an arcade machine
                    machine = ARCADE_MACHINES[ch]
                    frames = self.real_cache.setdefault(("cabinet", machine), [arcade.cabinet(machine, f) for f in range(8)])
                    foot = tile_rect.bottom - 4
                    self.anims.append((frames, (cx - frames[0].get_width() / 2, foot - frames[0].get_height()), foot, 5))
                    self.solids.append(pygame.Rect(cx - 40, foot - 44, 80, 44))
                    self._shadow(cx, foot - 4, 96, 16)
                    self.cabinets.append((pygame.Rect(cx - 60, foot - 6, 120, 60), machine))
                elif ch in "QXMZIJAGOUNDpgy@*":
                    self._interior_prop(ch, x, y, cx, cy, tile_rect)
                elif ch in STORY_PROPS:
                    self._story_prop(ch, x, y, cx, cy, tile_rect)
                elif ch == "P":
                    self.spawn = (cx, cy)
                elif ch == "T":
                    img, base = self.trees[rng.randrange(len(self.trees))]
                    foot_y = cy + 14
                    self.sprites.append(Sprite(img, (cx - img.get_width() / 2, foot_y - base), foot_y, fade=True))
                    trunk = pygame.Rect(0, 0, 22, 14); trunk.midbottom = (cx, foot_y)
                    self.solids.append(trunk)
                    self.decals.append((self.tree_shadow, self.tree_shadow.get_rect(center=(cx, foot_y - 4)).topleft))
                elif ch == "t":                                  # red autumn acer
                    img, base = self.autumn[(x * 7 + y * 3) % len(self.autumn)]
                    foot_y = cy + 14
                    self.sprites.append(Sprite(img, (cx - img.get_width() / 2, foot_y - base), foot_y, fade=True))
                    trunk = pygame.Rect(0, 0, 22, 14); trunk.midbottom = (cx, foot_y)
                    self.solids.append(trunk)
                    self.decals.append((self.tree_shadow, self.tree_shadow.get_rect(center=(cx, foot_y - 4)).topleft))
                elif ch == "|":                                  # iron railings: a solid line you can't pass
                    img = self.railing
                    foot = cy + 8
                    self.sprites.append(Sprite(img, (x * TILE, foot - img.get_height()), foot))
                    self.solids.append(pygame.Rect(x * TILE, foot - 20, TILE, 20))
                elif ch == "^":
                    img, base = self.statues[(x + y) % 2]
                    foot = cy + 20
                    self.sprites.append(Sprite(img, (cx - img.get_width() / 2, foot - base), foot))
                    self.solids.append(pygame.Rect(cx - 30, foot - 26, 60, 26))
                    self._shadow(cx, foot - 6, 76, 18)
                elif ch == "!":
                    self.solids.append(tile_rect)
                elif ch == "&":                                    # wheelie bin
                    cols = [((40, 44, 40), None), ((40, 40, 44), (190, 50, 50)), ((60, 70, 60), (110, 76, 50)), ((30, 30, 34), None)]
                    col, lid = cols[(x * 3 + y) % len(cols)]
                    img = self.real_cache.setdefault(("wbin", col, lid), pa.wheelie_bin(col, lid))
                    foot = cy + 22
                    self.sprites.append(Sprite(img, (cx - img.get_width() / 2, foot - img.get_height()), foot))
                    self.solids.append(pygame.Rect(cx - 22, foot - 18, 44, 18))
                    self._shadow(cx, foot - 4, 48, 12)
                elif ch == "`":                                    # down in the cutting: you can't step off the edge
                    self.solids.append(tile_rect)
                elif ch == "/" and (getattr(self._map_def, "STAIRS", None) or {}).get("axis") == "x":
                    for side in (-1, 1):                           # steps running sideways: walls above and below
                        if self.at(x, y + side, ".") != "/":
                            img = self.real_cache.setdefault(("stairwall_h", side), pygame.transform.rotate(pa.stair_wall("left"), 90))
                            wy = y * TILE if side < 0 else (y + 1) * TILE - img.get_height()
                            self.decals.append((img, (x * TILE, wy)))
                            self.solids.append(pygame.Rect(x * TILE, wy, TILE, img.get_height()))
                elif ch == ")":                                    # turning steps: a low wall along the bottom edge
                    if self.at(x, y + 1, ".") not in "/)(" and not getattr(self._map_def, "STAIR_WALLS_H", None):
                        img = self.real_cache.setdefault(("stairwall_h", 1), pygame.transform.rotate(pa.stair_wall("left"), 90))
                        wy = (y + 1) * TILE - img.get_height()
                        self.decals.append((img, (x * TILE, wy)))
                        self.solids.append(pygame.Rect(x * TILE, wy, TILE, img.get_height()))
                elif ch == "/":                                    # stairwell: stone walls either side
                    splits = getattr(self._map_def, "STAIR_SPLITS", ())   # x lines with a wall between two flights side by side
                    for side in (-1, 1):
                        if (x, y, side) in getattr(self._map_def, "STAIR_OPEN", ()):   # a gap in the wall: the way off the steps
                            continue
                        if self.at(x + side, y, ".") != "/" or (x + (side > 0)) in splits:
                            img = self.real_cache.setdefault(("stairwall", side), pa.stair_wall("left" if side < 0 else "right"))
                            wx = x * TILE if side < 0 else (x + 1) * TILE - img.get_width()
                            self.decals.append((img, (wx, y * TILE)))
                            self.solids.append(pygame.Rect(wx, y * TILE, img.get_width(), TILE))
                elif self.real is not None and ch == "H" and self.real["ids"][y][x] >= 0:
                    self._real_building(x, y, tile_rect)
                elif ch in BUILDING_CHARS:
                    self._building(ch, x, y, tile_rect)
                elif ch == "L":
                    foot = tile_rect.bottom - 6
                    self.lamp_spots.append((cx, foot))
                    self.sprites.append(Sprite(self.lamp, (cx - 12, foot - self.lamp.get_height()), foot))
                    base = pygame.Rect(0, 0, 12, 8); base.midbottom = (cx, foot)
                    self.solids.append(base)
                    self._shadow(cx, foot - 2, 26, 10)
                elif ch == "n":
                    foot = cy + 16
                    self.sprites.append(Sprite(self.bin, (cx - 12, foot - self.bin.get_height()), foot))
                    base = pygame.Rect(0, 0, 20, 10); base.midbottom = (cx, foot)
                    self.solids.append(base)
                    self._shadow(cx, foot - 3, 28, 10)
                elif ch == "m":                                       # a market stall (two tiles wide, from here right)
                    v = (x * 7 + y * 13) % 48
                    back, img = self.real_cache.setdefault(("stall", v), pa.market_stall_layers(v))
                    foot = tile_rect.bottom - 6
                    left = tile_rect.left + 4
                    self.sprites.append(Sprite(back, (left, foot - img.get_height()), foot - 60))   # behind the stallholder
                    self.sprites.append(Sprite(img, (left, foot - img.get_height()), foot))
                    self.solids.append(pygame.Rect(left + 4, foot - 40, img.get_width() - 8, 40))
                    self._shadow(left + img.get_width() // 2, foot - 2, img.get_width() + 6, 18)
                elif ch == "j":                                       # a market stall facing up the screen (seen from behind)
                    v = (x * 7 + y * 13) % 48
                    img = self.real_cache.setdefault(("stallb", v), pa.market_stall_back(v))
                    foot = tile_rect.bottom - 6
                    left = tile_rect.left + 4
                    self.sprites.append(Sprite(img, (left, foot - img.get_height()), foot))
                    self.solids.append(pygame.Rect(left + 4, foot - 52, img.get_width() - 8, 52))
                    self._shadow(left + img.get_width() // 2, foot - 2, img.get_width() + 6, 18)
                elif ch == "q":
                    foot = cy + 16
                    self.sprites.append(Sprite(self.bench, (cx - 30, foot - self.bench.get_height()), foot))
                    base = pygame.Rect(0, 0, 56, 12); base.midbottom = (cx, foot)
                    self.solids.append(base)
                    self._shadow(cx, foot - 4, 62, 14)
                elif ch == "u":
                    foot = tile_rect.bottom - 4
                    self.sprites.append(Sprite(self.shelter, (cx - 66, foot - self.shelter.get_height()), foot))
                    base = pygame.Rect(0, 0, 128, 12); base.midbottom = (cx, foot)
                    self.solids.append(base)
                    self._shadow(cx, foot - 4, 136, 18)
                elif ch == "F":
                    img = self.fountain
                    foot = cy + 76
                    self.sprites.append(Sprite(img, (cx - img.get_width() / 2, foot - self.fountain_base), foot))
                    base = pygame.Rect(0, 0, 176, 96); base.midbottom = (cx, foot - 10)
                    self.solids.append(base)
                    self._shadow(cx, foot - 30, 214, 70)
                elif ch == "Y" and self.real is not None:          # traffic light: the traffic system draws it
                    foot = cy + 18
                    self.signal_spots.append((cx, foot, x))
                    base = pygame.Rect(0, 0, 14, 10); base.midbottom = (cx, foot)
                    self.solids.append(base)
                    self._shadow(cx, foot - 3, 26, 10)
                elif ch == "$":                                    # doner kebab spit
                    frames = [pa.doner(i) for i in range(3)]
                    foot = tile_rect.bottom - 2
                    self.anims.append((frames, (cx - frames[0].get_width() / 2, foot - frames[0].get_height()), foot, 4))
                    self.solids.append(pygame.Rect(x * TILE + 8, y * TILE + 8, TILE - 16, TILE - 8))
                elif ch == "%":                                    # City Hall's fountain at the end of the pool
                    ft = getattr(self._map_def, "FOUNTAIN", dict(cx=x + 1.0, cy=y + 2.6))
                    frames = [pa.city_fountain(i) for i in range(8)]
                    fx, foot = ft["cx"] * TILE, ft["cy"] * TILE
                    self.anims.append((frames, (fx - frames[0].get_width() / 2, foot - frames[0].get_height()), foot, 9))
                    self.solids.append(pygame.Rect(fx - 90, foot - 92, 180, 84))
                    self.feature_lights.append((fx, foot - 70, 170, (200, 220, 255), 0.75))
                elif ch in "okY":
                    img = {"o": self.post_box, "k": self.bike_rack, "Y": self.signal}[ch]
                    foot = cy + 18
                    self.sprites.append(Sprite(img, (cx - img.get_width() / 2, foot - img.get_height()), foot))
                    base = pygame.Rect(0, 0, min(img.get_width() - 8, 48), 10); base.midbottom = (cx, foot)
                    self.solids.append(base)
                    self._shadow(cx, foot - 3, img.get_width() + 6, 12)
                elif ch == "v":
                    colour = CAR_COLOURS[(x * 5 + y * 3) % len(CAR_COLOURS)]
                    key = (colour, y % 2 == 0)
                    if key not in self.car_cache:
                        self.car_cache[key] = pa.car(colour, facing_right=key[1])
                    img = self.car_cache[key]
                    foot = tile_rect.bottom - 4
                    self.sprites.append(Sprite(img, (cx - img.get_width() // 2, foot - img.get_height()), foot))
                    base = pygame.Rect(0, 0, img.get_width() - 16, 36); base.midbottom = (cx, foot - 2)
                    self.solids.append(base)
                    self._shadow(cx, foot - 8, img.get_width(), 22)

    def _zaza_prop(self, ch, x, y, cx, cy, tile_rect):
        """Za Za Bazaar's fittings (see INTERIORS["zaza"])."""
        cache = self.real_cache
        foot = tile_rect.bottom - 2
        zz = self.zaza
        if ch in "xh":                                   # the rest of a wide piece: its first tile draws it
            return
        if ch == "S":
            k = sum(1 for xx in range(x) if self.grid[y][xx] == "S")
            name, col = pa.ZAZA_STATIONS[k % len(pa.ZAZA_STATIONS)]
            img = cache.setdefault(("zstation", name), pa.zaza_station(name, col))
            self.sprites.append(Sprite(img, (x * TILE, foot - img.get_height()), foot))
            self.solids.append(pygame.Rect(x * TILE, foot - 30, 4 * TILE, 30))
            zz["stations"].append((x, y, name, col))
            return
        if ch == "B":
            end = "l" if self.at(x - 1, y, " ") != "B" else ("r" if self.at(x + 1, y, " ") != "B" else None)
            img = cache.setdefault(("zbar", end, x % 3), pa.zaza_bar(end, x))
            self.sprites.append(Sprite(img, (x * TILE, foot - img.get_height()), foot))
            self.solids.append(pygame.Rect(x * TILE, foot - 44, TILE, 44))
            zz["bar"].append((x, y))
            return
        if ch == "K":
            img = cache.setdefault(("zbackbar", x % 4), pa.zaza_back_bar(x))
            self.sprites.append(Sprite(img, (x * TILE, foot - img.get_height()), foot))
            self.solids.append(pygame.Rect(x * TILE, y * TILE, TILE, TILE))
            return
        if ch == "b":
            v = (x + y) % 3
            back = cache.setdefault(("zboothb", v), pa.zaza_booth_back(v))
            img = cache.setdefault(("zboothf", v), pa.zaza_booth_front(v))
            self.sprites.append(Sprite(back, (x * TILE, foot - img.get_height()), foot - 80))   # behind the people in it
            self.sprites.append(Sprite(img, (x * TILE, foot - img.get_height()), foot))
            self.solids.append(pygame.Rect(x * TILE + 4, foot - 64, 2 * TILE - 8, 64))
            self._shadow(x * TILE + TILE, foot - 4, 2 * TILE, 16)
            zz["booths"].append((x, y))
            return
        if ch == "T":
            v = (x * 3 + y) % 3
            img = cache.setdefault(("ztable", v), pa.zaza_table(v, back_chairs=False))
            chairs = cache.setdefault(("zchairs", v), pa.zaza_chairs_back(v))
            left = cx - img.get_width() // 2
            self.sprites.append(Sprite(chairs, (left, foot - img.get_height()), foot - 80))      # behind the diners
            self.sprites.append(Sprite(img, (left, foot - img.get_height()), foot))
            self.solids.append(pygame.Rect(cx - 48, foot - 70, 96, 64))
            self._shadow(cx, foot - 6, img.get_width() + 8, 22)
            zz["tables"].append((cx, foot))
            return
        if ch == "P":
            img = cache.setdefault(("zpillar", (x + y) % 4), pa.zaza_pillar(x + y))
            self.sprites.append(Sprite(img, (cx - img.get_width() // 2, foot - img.get_height()), foot))
            self.solids.append(pygame.Rect(cx - 20, foot - 26, 40, 26))
            self._shadow(cx, foot - 4, 56, 14)
            zz["pillars"].append((cx, foot))
            return
        if ch == "F":
            img = cache.setdefault("zdrinks", pa.zaza_drinks())
            self.sprites.append(Sprite(img, (x * TILE, foot - img.get_height()), foot))
            self.solids.append(pygame.Rect(x * TILE + 4, foot - 44, 2 * TILE - 8, 44))
            zz["drinks"].append((x * TILE + TILE, foot))
            return
        if ch in "WV":                                   # toilet doors set into the back wall
            img = cache.setdefault(("zwc", ch), pa.zaza_wc_door(ch == "V"))
            ft = tile_rect.top + 24
            self.sprites.append(Sprite(img, (x * TILE, ft - img.get_height()), ft))
            self.solids.append(pygame.Rect(x * TILE, tile_rect.top, TILE, 30))
            return

    def _crime_scene(self, cs):
        """Where John Harper went into the water: police tape round three sides (the fourth is the harbour),
        a forensic tent, numbered evidence markers and the yellow appeal board."""
        cache = self.real_cache
        x0, y0, x1, y1 = cs["tape"]
        post = cache.setdefault("tape_post", pa.tape_post())
        ph = post.get_height()
        lift = 9 * pa.PX                                    # the tape's height above the ground
        for y in (y0, y1):                                  # the top and bottom runs
            img = cache.setdefault(("tape_h", x1 - x0), pa.police_tape_h(x1 - x0))
            foot = y * TILE
            self.sprites.append(Sprite(img, (x0 * TILE, foot - lift), foot + 1))
            self.solids.append(pygame.Rect(x0 * TILE, foot - 8, (x1 - x0) * TILE, 16))
            for px in range(x0, x1 + 1, 2):
                self.sprites.append(Sprite(post, (px * TILE - post.get_width() // 2, foot - ph + 4), foot + 2))
        img = cache.setdefault(("tape_v", y1 - y0), pa.police_tape_v(y1 - y0))   # the left side
        self.sprites.append(Sprite(img, (x0 * TILE - img.get_width() // 2, y0 * TILE - lift), y0 * TILE))
        self.solids.append(pygame.Rect(x0 * TILE - 8, y0 * TILE, 16, (y1 - y0) * TILE))
        for py in range(y0, y1 + 1, 2):
            self.sprites.append(Sprite(post, (x0 * TILE - post.get_width() // 2, py * TILE - ph + 4), py * TILE + 2))
        tx, ty = cs["tent"]
        tent = cache.setdefault("ftent", pa.forensic_tent())
        foot = (ty + 2) * TILE - 4
        self.sprites.append(Sprite(tent, (tx * TILE, foot - tent.get_height()), foot))
        self.solids.append(pygame.Rect(tx * TILE + 4, foot - 70, 2 * TILE - 8, 70))
        self._shadow(tx * TILE + TILE, foot - 4, 2 * TILE + 8, 22)
        for mx, my, n in cs["markers"]:
            img = cache.setdefault(("marker", n), pa.evidence_marker(n))
            self.sprites.append(Sprite(img, (mx * TILE - img.get_width() // 2, my * TILE - img.get_height()), my * TILE))
        sx, sy = cs["sign"]
        img = cache.setdefault("appeal", pa.appeal_board())
        self.sprites.append(Sprite(img, (sx * TILE - img.get_width() // 2, sy * TILE - img.get_height()), sy * TILE))
        self.solids.append(pygame.Rect(sx * TILE - 30, sy * TILE - 12, 60, 12))
        self._shadow(sx * TILE, sy * TILE - 3, 70, 12)

    def _zaza_finish(self):
        """After the room's built: string lights between the pillars, street art on the walls, the neon sign."""
        zz = self.zaza
        rows = {}
        for cx, foot in zz["pillars"]:
            rows.setdefault(foot, []).append(cx)
        for foot, xs in rows.items():                     # pillars on the same row, and out to the side walls
            xs = sorted(xs)
            pts = [TILE + 8] + xs + [(self.w - 1) * TILE - 8]
            for a, b in zip(pts, pts[1:]):
                img = self.real_cache.setdefault(("zlights", b - a), pa.string_lights(b - a, sag=8 + (b - a) // 160))
                top = foot - 196
                self.sprites.append(Sprite(img, (a, top), foot + 1))
                zz["bulbs"] += [(a + (b - a) * t, top + 28 + 20 * math.sin(math.pi * t)) for t in (0.25, 0.5, 0.75)]
        bar_x = [x for x, y in zz["bar"]] or [self.w // 2]
        back = [x for x in range(self.w) if self.grid[1][x] == "K"] or bar_x
        neon = self.real_cache.setdefault("zneon", pa.zaza_neon())
        mid = (min(back) + max(back) + 1) * TILE // 2
        top = 2 * TILE + 6                                # hanging over the bar, in front of the shelves
        rods = pygame.Surface((neon.get_width(), 10), pygame.SRCALPHA)
        rods.fill((50, 46, 50, 255), (16, 0, 4, 10)); rods.fill((50, 46, 50, 255), (neon.get_width() - 20, 0, 4, 10))
        self.sprites.append(Sprite(rods, (mid - neon.get_width() // 2, top - 10), 2 * TILE + 49))
        self.sprites.append(Sprite(neon, (mid - neon.get_width() // 2, top), 2 * TILE + 50))
        zz["neon"] = (mid, top + 20)
        for x in range(1, self.w - 1):                    # street art on the walls between things
            if self.grid[1][x] == "i" and (x * 7) % 3 != 1:
                img = self.real_cache.setdefault(("zgraf", x % 6), pa.zaza_graffiti(x))
                self.sprites.append(Sprite(img, (x * TILE, TILE - img.get_height()), TILE + 1))

    def _interior_prop(self, ch, x, y, cx, cy, tile_rect):
        seed = self.interior["seed"] if self.interior else 0
        kind = self.interior["kind"] if self.interior else "corner"
        key = (ch, x if ch in "QX" else 0)
        cache = self.real_cache
        if ch == "y":
            rug_col = {"usher": (120, 36, 40), "home": (54, 70, 110)}.get(kind, INTERIOR_WALLS[seed % len(INTERIOR_WALLS)][::-1])
            img = cache.setdefault(("rug", seed, kind), pa.rug(rug_col))
            self.decals.append((img, (x * TILE, y * TILE)))
            return
        if ch == "p" and self.interior is not None:        # staff are NPCs now (people.py)
            return
        if ch == "p":                                       # shopkeeper
            looks = [v for k, v in CHARACTER_LOOKS.items() if k not in ("Robot 1", "Zombie 1")]   # people only behind the counter
            look = looks[seed % len(looks)]
            img = cache.setdefault(("npc", seed), pa.character_frames(look)[("down", 0)])
            foot = tile_rect.bottom - 6
            self.sprites.append(Sprite(img, (cx - img.get_width() // 2, foot - img.get_height()), foot))
            base = pygame.Rect(0, 0, 26, 14); base.midbottom = (cx, foot)
            self.solids.append(base)
            self._shadow(cx, foot - 2, 30, 12)
            return
        if ch in "QX":
            left = self.at(x - 1, y, " ") not in "QXM"
            right = self.at(x + 1, y, " ") not in "QXM"
            img = cache.setdefault(("counter", ch, left, right),
                                   pa.counter("wood" if kind != "gym" else "steel", till=ch == "X",
                                              end="l" if left else ("r" if right else None)))
        elif ch == "@":                                     # DJ booth (two tiles wide)
            self.solids.append(pygame.Rect(x * TILE, y * TILE + 12, TILE, TILE - 12))
            if self.at(x - 1, y, " ") == "@":
                return
            img = cache.setdefault("djbooth", pa.dj_booth())
            foot = tile_rect.bottom - 2
            self.sprites.append(Sprite(img, (x * TILE + TILE - img.get_width() // 2, foot - img.get_height()), foot))
            return
        elif ch == "*": img = cache.setdefault("speaker", pa.speaker())
        elif ch == "M":
            img = cache.setdefault("coffee", pa.coffee_machine())
            steam = cache.setdefault("steam", [pa.steam(i) for i in range(5)])
            top = tile_rect.bottom - 2 - img.get_height()
            self.anims.append((steam, (cx - 16, top - steam[0].get_height() + 12), tile_rect.bottom, 6))
        elif ch == "Z": img = cache.setdefault(("shelf", kind, x % 4), pa.shelf("books" if kind == "books" else kind, seed + x))
        elif ch == "I": img = cache.setdefault(("fridge", x % 3), pa.fridge(seed + x))
        elif ch == "J": img = cache.setdefault(("table", x % 3), pa.cafe_table(seed + x))
        elif ch == "A": img = cache.setdefault(("rail", x % 4), pa.clothes_rail(seed + x * 3))
        elif ch == "G": img = cache.setdefault("bchair", pa.barber_chair())
        elif ch == "O": img = cache.setdefault("mirror", pa.mirror())
        elif ch == "U": img = cache.setdefault("tread", pa.treadmill())
        elif ch == "N": img = cache.setdefault("bench_press", pa.bench_press())
        elif ch == "D": img = cache.setdefault("weights", pa.weights_rack())
        else:           img = cache.setdefault("plant", pa.plant())
        foot = tile_rect.bottom - 2
        self.sprites.append(Sprite(img, (cx - img.get_width() // 2, foot - img.get_height()), foot))
        if ch in "QXMZIOUD":
            base = pygame.Rect(x * TILE, y * TILE + 8, TILE, TILE - 8)
        else:
            base = pygame.Rect(0, 0, min(img.get_width() - 8, TILE + 16), 24); base.midbottom = (cx, foot)
        self.solids.append(base)
        if ch not in "QXMZO":
            self._shadow(cx, foot - 4, img.get_width(), 14)

    def _story_prop(self, ch, x, y, cx, cy, tile_rect):
        """Furniture in the story's rooms: the store room, the offices, the detective's flat."""
        cache = self.real_cache
        variant = (self.interior or {}).get("variant")
        foot = tile_rect.bottom - 2
        wide = False
        if ch == "9" or ch == ">":                          # right halves of the desk / sofa: just solid
            self.solids.append(pygame.Rect(x * TILE, y * TILE + 10, TILE, TILE - 14))
            return
        if ch == "5":
            first = x
            while self.at(first - 1, y, " ") == "5":
                first -= 1
            labels = RECORD_YEARS[min(x - first, len(RECORD_YEARS) - 1)]
            img = cache.setdefault(("records", labels), pa.records_shelf(labels))
        elif ch == "6":
            tag = self.at(x - 1, y, " ") != "6"            # John's is the first one
            img = cache.setdefault(("locker", tag), pa.locker(tag))
        elif ch == "7":
            img = cache.setdefault(("boxes", x + y, variant == "packed"), pa.boxes(x * 3 + y, variant == "packed" and (x + y) % 2 == 0))
        elif ch == "8":
            kind = "packed" if variant == "packed" else self.interior["kind"]
            img = cache.setdefault(("desk", kind, x + y), pa.desk(kind, x * 7 + y))
            wide = True
        elif ch == "0":
            img = cache.setdefault(("bookcase", x % 5, variant == "packed"), pa.bookcase(x * 5 + 1, variant == "packed"))
        elif ch == "[":
            img = cache.setdefault(("filing", variant == "packed" and x % 2 == 0), pa.filing_cabinet(variant == "packed" and x % 2 == 0))
        elif ch == "{":
            img = cache.setdefault(("ochair", self.interior["kind"]), pa.office_chair(self.interior["kind"] == "usher"))
            self.sprites.append(Sprite(img, (cx - img.get_width() // 2, foot - 6 - img.get_height()), foot - 30))
            return                                          # someone may sit in it: not solid, drawn behind them
        elif ch == "<":
            img = cache.setdefault("sofa", pa.sofa())
            wide = True
        elif ch == "?":
            img = cache.setdefault(("sidetable", 0), pa.side_table(0))
        elif ch == "]":
            img = cache.setdefault("armchair", pa.armchair())
        else:
            img = cache.setdefault("floorlamp", pa.floor_lamp())
        left = x * TILE + (TILE if wide else TILE // 2) - img.get_width() // 2
        self.sprites.append(Sprite(img, (left, foot - img.get_height()), foot))
        if ch in "560[":                                    # against the wall: the whole tile
            self.solids.append(pygame.Rect(x * TILE, y * TILE + 8, TILE, TILE - 8))
        else:
            base = pygame.Rect(0, 0, min(img.get_width() - 8, TILE * 2), 24)
            base.midbottom = (left + img.get_width() // 2, foot)
            self.solids.append(base)
            self._shadow(left + img.get_width() // 2, foot - 4, img.get_width(), 14)
        if variant == "packed" and ch == "7":
            pass

    def _shadow(self, cx, cy, w, h):
        sh = ellipse_shadow(w, h)
        self.decals.append((sh, sh.get_rect(center=(cx, cy)).topleft))

    def _real_building(self, x, y, tile_rect):
        """One tile of a real (OpenStreetMap) building. Drawn lazily: only when it first comes on screen."""
        ids = self.real["ids"]
        i = ids[y][x]
        b = self.real["buildings"][i]
        self.solids.append(tile_rect)
        same = lambda xx, yy: 0 <= xx < self.w and 0 <= yy < self.h and ids[yy][xx] == i
        mask = (1 if same(x, y - 1) else 0) | (2 if same(x + 1, y) else 0) | (4 if same(x, y + 1) else 0) | (8 if same(x - 1, y) else 0)
        tower = (x, y) in self.real["tower"]
        if tower:
            # treat the tower as its own block so its walls rise above the rest of the building
            tw = self.real["tower"]
            mask = (1 if (x, y - 1) in tw else 0) | (2 if (x + 1, y) in tw else 0) | (4 if (x, y + 1) in tw else 0) | (8 if (x - 1, y) in tw else 0)
        st = b["style"]
        # chimney stacks sit on the party walls (left/right edges) of terrace roofs
        chimney = st in ("H", "C") and bool(mask & 4) and (not mask & 8 or not mask & 2) and (x + y) % 2 == 0
        if st == "K":
            chimney = bool(mask & 4) and (x * 3 + y) % 7 == 0
        dormer = (st == "K" and not mask & 2 and mask & 5 == 5 and y % 2 == 0) or st == "H" and mask & 4 and same(x, y + 1) and not same(x, y + 2) and (x + b["seed"]) % 3 == 0 and mask & 10 == 10
        height = (pa.TOWER_H if tower else pa.building_height(b)) * pa.PX
        front = not mask & 4
        seed = b["seed"] + x * 7 + y * 13
        if front:
            lx = 0
            while same(x - lx - 1, y): lx += 1
            bw = lx + 1
            while same(x - lx + bw, y): bw += 1
            if tower:                                       # the tower's own front, so its great window spans it
                tw = self.real["tower"]
                lx = 0
                while (x - lx - 1, y) in tw: lx += 1
                bw = lx + 1
                while (x - lx + bw, y) in tw: bw += 1
            below = self.at(x, y + 1, ".")
            shopfront = b["shop"] and below in "-=zLTnqukoYP ,:Jg|t^"
            if b["shop"] and any(sh["building"] == i for sh in self.doors.values()):
                door = (x, y) in self.doors                         # the real door of a walk-in shop
            else:
                door = (lx % 3 == 1) if shopfront else (lx == bw // 2)
            branded = bool(b.get("brand")) and shopfront
            key = (i, mask, tower, lx if (st in "VMAWRBZ" or branded) else lx % 6, bw if (st in "VMAWRBZ" or branded) else 0, shopfront, door)
            size = (TILE, TILE + height)
            pos = (x * TILE, y * TILE - height)
            def make(b=b, mask=mask, tower=tower, lx=lx, bw=bw, shopfront=shopfront, door=door, key=key, seed=seed):
                img = self.real_cache.get(key)
                if img is None:
                    if b["style"] == "H":
                        facade = pa.facade_terrace(b, lx, bw, shopfront, door, True)
                    elif b["style"] == "U":
                        facade = pa.facade_modern(b, lx, bw, shopfront, door, True)
                    else:
                        facade = pa.facade_landmark(b, lx, bw, tower)
                    img = self.real_cache[key] = pa.building_tile(b, mask, tower, False, False, seed, facade)
                return img
        else:
            key = (i, mask, tower, bool(chimney), bool(dormer), seed % 5 == 0, seed % 23 if st == "O" and seed % 23 in (0, 11) else -1)
            size = (TILE, TILE)
            pos = (x * TILE, y * TILE - height)
            def make(b=b, mask=mask, tower=tower, chimney=bool(chimney), dormer=bool(dormer), key=key, seed=seed):
                img = self.real_cache.get(key)
                if img is None:
                    img = self.real_cache[key] = pa.building_tile(b, mask, tower, chimney, dormer, seed, None)
                return img
        sp = Sprite(None, pos, tile_rect.bottom, size=size, make=make)
        sp.cut = bool(b.get("away"))
        self.sprites.append(sp)
        shop = self.doors.get((x, y))
        if shop is not None and shop["side"] == "north":
            # This shop faces away from the camera: hang its sign over the roof edge so you can find it
            if b.get("brand"):                              # the shop's own sign board, up on posts above the roof
                sign = self.real_cache.setdefault(("roofsign", b["brand"]["name"]), pa.roof_sign(b["brand"]))
                cx_sign = shop.get("centre", x + 0.5) * TILE
                self.sprites.append(Sprite(sign, (cx_sign - sign.get_width() // 2, y * TILE - height - sign.get_height() + 20),
                                           tile_rect.bottom + 1))
            else:
                colour = tuple(b["awning"]) if b.get("awning") else (40, 40, 44)
                sign = self.real_cache.setdefault(("sign", colour, shop["kind"]), pa.hanging_sign(colour, shop["kind"]))
                self.sprites.append(Sprite(sign, (x * TILE + TILE // 2 - sign.get_width() // 2, y * TILE - height - sign.get_height() + 8),
                                           tile_rect.bottom + 1))
            self.decals.append((self.mat, (x * TILE, (y - 1) * TILE + 20)))
        elif shop is not None and shop["side"] in ("west", "east"):
            pass                                              # side entrance: drawn by the map's SIDE_ENTRANCES
        elif shop is not None:
            self.decals.append((self.mat, (x * TILE, (y + 1) * TILE - 24)))

    def _building(self, ch, x, y, tile_rect):
        """One tile of a building: solid, with a raised roof and (on its front row) a facade."""
        self.solids.append(tile_rect)
        mask = 0
        if self.at(x, y - 1, ".") == ch: mask |= 1
        if self.at(x + 1, y, ".") == ch: mask |= 2
        if self.at(x, y + 1, ".") == ch: mask |= 4
        if self.at(x - 1, y, ".") == ch: mask |= 8
        rear = False
        facade_key = None
        if not mask & 4:
            # Shops face the road; a terrace whose front row looks onto gardens shows its plain back
            below = self.at(x, y + 1, ".")
            rear = ch == "H" and below in ".,T"
            facade_key = (x % 3 == 1, ((x // 3) * 5 + 3) % len(SHOP_COLOURS)) if ch == "H" and not rear else x % 2
        key = (ch, mask, rear, facade_key)
        img = self.building_cache.get(key)
        if img is None:
            facade = make_facade(ch, x, rear) if not mask & 4 else None
            img = self.building_cache[key] = pa.pixelize(make_building_sprite(ch, mask, facade))
        height = BUILDING_STYLES[ch]["height"]
        self.sprites.append(Sprite(img, (x * TILE, y * TILE - height), tile_rect.bottom))

    @staticmethod
    def _cells(rect):
        for cy in range(rect.top // TILE, (rect.bottom - 1) // TILE + 1):
            for cx in range(rect.left // TILE, (rect.right - 1) // TILE + 1):
                yield cx, cy

    # ---------------------------------------------------- collision
    def _build_bridge(self, br):
        """Park Street crossing overhead (Frogmore Street map): the deck is drawn lifted up, in front of
        anything underneath it, and goes see-through when you walk below."""
        y0, y1, lift = br["y0"], br["y1"], br["lift"]
        sort = (y1 + 1) * TILE + 2
        grey = (lambda im: pa.greyed(im, 0.75)) if br.get("grey") else (lambda im: im)
        layout = {y0: "p", y0 + 1: "p", y0 + 2: "rn", y0 + 3: "rc", y0 + 4: "rs", y0 + 5: "p", y0 + 6: "p", y1: "p"}
        cache = {}
        for y in range(y0, y1 + 1):
            for x in range(self.w):
                kind = layout.get(y, "p")
                v = (x * 7 + y) % 4
                key = (kind, v)
                img = cache.get(key)
                if img is None:
                    if kind == "p":
                        img = self.paving[v].copy()
                    else:
                        img = (self.road_line_h if kind == "rc" else self.road[v]).copy()
                        if kind in ("rn", "rs"):
                            pa.kerb_and_lines(img, 0, 0, {"n" if kind == "rn" else "s"}, yellow=True)
                    img = grey(img)
                    cache[key] = img
                sp = Sprite(img, (x * TILE, y * TILE - lift), sort)
                sp.cut = True
                self.sprites.append(sp)
                shade_ = pygame.Surface((TILE, TILE), pygame.SRCALPHA); shade_.fill((0, 0, 12, 110))
                self.decals.append((shade_, (x * TILE, y * TILE)))            # gloomy underneath
        fascia = grey(pa.bridge_fascia(0, lift // pa.PX))
        bars = pa.railing()
        rail = pa.paving_tile(0).subsurface((0, 0, TILE, bars.get_height())).copy().convert_alpha()
        rail.blit(bars, (0, 0))                                            # pavement showing between the bars
        rail = grey(rail)
        for x in range(self.w):
            sp = Sprite(fascia, (x * TILE, (y1 + 1) * TILE - lift), sort)
            sp.cut = True
            self.sprites.append(sp)
            rx = br.get("rail_x")                                             # railing only over the cutting (as seen from up top)
            if rx and not (rx[0] <= x <= rx[1]):
                continue
            for yy, sy in ((y0, sort), (y1 + 1, sort + 1)):                    # parapets on both edges
                r = Sprite(rail, (x * TILE, yy * TILE - lift - rail.get_height() + 12), sy)
                r.cut = True
                self.sprites.append(r)

    def _collect_lights(self):
        """Where light comes from at night: shop windows, signs, flats upstairs, the Wills tower floodlights."""
        self.window_lights = []          # (x, y, radius, colour, strength, shop kind or None)
        rng = random.Random(77)
        for (dx, dy), shop in self.doors.items():
            b = self.real["buildings"][shop["building"]]
            cx = shop.get("centre", dx + 0.5) * TILE
            h = pa.building_height(b) * pa.PX
            if shop["side"] in ("west", "east"):
                continue
            if shop["side"] == "south":                               # shopfront facing you: lit window
                self.window_lights.append((cx, (dy + 1) * TILE - 30, 120, (255, 214, 150), 0.75, shop["kind"]))
                if rng.random() < 0.45:                               # someone home in the flat upstairs
                    self.window_lights.append((cx + rng.uniform(-30, 30), (dy + 1) * TILE - h + 60, 70, (255, 200, 120), 0.55, None))
            else:                                                     # far side: the roof sign is lit
                self.window_lights.append((cx, dy * TILE - h - 20, 80, (255, 226, 170), 0.6, shop["kind"]))
        md = self._map_def
        for x, y, r, c, st in getattr(md, "NEON", []):                 # neon signs etc. (tile units)
            self.feature_lights.append((x * TILE, y * TILE, r, c, st))
        tw = self.real["tower"]
        if tw:                                                        # Wills tower is floodlit at night
            xs = [x for x, _ in tw]; ys = [y for _, y in tw]
            cx, front = (min(xs) + max(xs) + 1) / 2 * TILE, (max(ys) + 1) * TILE
            self.feature_lights.append((cx, front - 220, 300, (255, 236, 200), 0.8))
            self.feature_lights.append((cx, front - 40, 160, (255, 230, 190), 0.6))

    def lights(self, dark, hour, lamps_on):
        if self.interior is not None and self.interior["kind"] == "club":     # club lights sweeping the dance floor
            t = self.time
            out = []
            for i, col in enumerate(((255, 60, 200), (60, 200, 255), (160, 80, 255), (255, 200, 80))):
                a = t * (0.9 + i * 0.25) + i * 1.7
                out.append((3.6 * TILE + math.cos(a) * 150, 5.5 * TILE + math.sin(a * 1.3) * 110, 150, col, 0.95))
            out.append((4 * TILE, 2 * TILE + 40, 110, (120, 80, 255), 0.8))
            out.append((9 * TILE, 3 * TILE, 180, (255, 200, 140), 0.8))
            out.append((9 * TILE, 6.5 * TILE, 160, (255, 170, 120), 0.6))
            return out
        if self.interior is not None and self.interior["kind"] == "zaza":     # a night market indoors
            zz = self.zaza
            out = [(bx, by, 90, (255, 214, 150), 0.55) for bx, by in zz["bulbs"]]
            for x, y, name, col in zz["stations"]:
                out.append(((x + 2) * TILE, (y + 1) * TILE - 120, 170, (255, 170, 90), 0.75))
            if zz["bar"]:
                xs = [x for x, y in zz["bar"]]
                for x in range(min(xs), max(xs) + 1, 3):
                    out.append((x * TILE + TILE, zz["bar"][0][1] * TILE, 150, (255, 196, 130), 0.6))
            if zz["neon"]:
                out.append((zz["neon"][0], zz["neon"][1] + 40, 220, (255, 100, 200), 0.7))
            return out
        if self.interior is not None and self.interior["kind"] == "arcade":   # each machine lights up the carpet in front
            out = []
            for area, machine in self.cabinets:
                m = arcade.MACHINES[machine]
                out.append((area.centerx, area.top - 70, 130, m["glow"], 0.85))
            out.append((13.5 * TILE, 4.5 * TILE, 200, (255, 220, 170), 0.8))     # the prize counter
            return out
        if self.interior is not None or self.real is None or dark < 0.05:
            return []
        out = []
        if lamps_on:
            for cx, foot in self.lamp_spots:
                out.append((cx, foot - 34, 210, (255, 206, 130), 0.9 * dark))
                out.append((cx + 14, foot - 118, 40, (255, 236, 170), 1.0 * dark))
        for x, y, r, c, st, kind in self.window_lights:
            if kind is None or people.is_open(kind, hour):
                out.append((x, y, r, c, st * dark))
        for x, y, r, c, st in self.feature_lights:
            out.append((x, y, r, c, st * dark))
        if self.traffic is not None:
            out.extend(self.traffic.lights(dark))
        if self.vtraffic is not None:
            out.extend(self.vtraffic.lights(dark))
        if self.deck is not None:
            out.extend(self.deck.lights(dark))
        return out

    def update(self, dt, player_rect, hour=None, night=False):
        """Move the people and the traffic; send people home (or out) as the day goes on."""
        self.time += dt
        if hour is not None:
            self.hour = hour
        if self.traffic is not None:
            self.traffic.update(dt, player_rect, self.hour)
        if self.vtraffic is not None:
            self.vtraffic.update(dt, player_rect, self.hour)
        if self.deck is not None:
            self.deck.update(dt, player_rect, self.hour)
        px, py = player_rect.center
        for n in self.actors:
            want = n.active(self.hour)
            if want != n.shown and (abs(n.x - px) > 760 or abs(n.y - py) > 480):   # only swap people while you can't see
                n.shown = want
            if n.phases:
                if abs(n.x - px) > 700 or abs(n.y - py) > 450 or n.phase is None:
                    n.set_phase("night" if night else "day")
            if n.shown:
                n.update(dt, self, player_rect)
        extra = self.traffic.solids() if self.traffic is not None else []
        if self.vtraffic is not None:
            extra.extend(self.vtraffic.solids())
        for n in self.actors:
            if n.shown:
                r = n.solid()
                if r is not None:
                    extra.append(r)
        self.extra_solids = extra

    def dynamic_sprites(self, view):
        for frames, pos, sort_y, fps in self.anims:
            img = frames[int(self.time * fps) % len(frames)]
            r = pygame.Rect(pos, img.get_size())
            if r.colliderect(view):
                yield Sprite(img, pos, sort_y)
        for system in (self.traffic, self.vtraffic, self.deck):
            if system is not None:
                for img, pos, sort_y in system.sprites(view):
                    yield Sprite(img, pos, sort_y)
        for n in self.actors:
            if not n.shown:
                continue
            img = n.image()
            pos = (n.x - img.get_width() / 2, n.y - img.get_height() + 4)
            if not view.colliderect(pygame.Rect(pos, img.get_size())):
                continue
            for fn, dx, dy, sdy in n.extras:
                ex = people.dog(int(self.time * 3)) if fn == "dog" else self.real_cache.setdefault(("extra", fn), fn())
                yield Sprite(ex, (n.x + dx - ex.get_width() / 2, n.y + dy - ex.get_height()), n.y + sdy)
            yield Sprite(img, pos, n.y + n.sort_bias)

    def stair_height(self, x, y):
        """On stairs with turns: 1 at the top, 0 at the bottom (None when not on them)."""
        st = self.stairs
        if not st or not st.get("segments"):
            return None
        done = 0
        for r, high, n in st["segments"]:
            if r.collidepoint(x, y):
                d = {"left": x - r.left, "right": r.right - x, "top": y - r.top, "bottom": r.bottom - y, "flat": 0}[high]
                return 1 - (done + d) / st["path_len"]
            done += n
        return None

    def stair_offset(self, x, y):
        """How far below (+) or above (-) street level you are while on the stairs, in pixels."""
        st = self.stairs
        if not st:
            return 0.0
        if st.get("segments"):
            h = self.stair_height(x, y)
            if h is None:
                return 0.0
            return -(h * st.get("depth", 40) + 3 * abs(math.sin(((x + y) / 16.0) * math.pi)))
        if st.get("turn_area") is not None and st["turn_area"].collidepoint(x, y):   # the bend at the bottom
            ta, a = st["turn_area"], st["area"]
            share = ta.w / (ta.w + a.h)
            frac = (ta.right - x) / ta.w * share
            return -(frac * st.get("depth", 100) + 3 * abs(math.sin((x / 16.0) * math.pi)))
        if not st["area"].collidepoint(x, y):
            return 0.0
        a = st["area"]
        if st.get("axis") == "x":                                     # steps climbing towards the left
            bob = 3 * abs(math.sin((x / 16.0) * math.pi))
            frac = (a.right - x) / a.w
            return -(frac * st.get("depth", 100) + bob) if st.get("mode") == "rise" else frac * st.get("depth", 56) + bob
        bob = 3 * abs(math.sin((y / 16.0) * math.pi))                 # a little dip on every step
        if st.get("mode") == "sink":
            frac = (a.bottom - y) / a.h
            return frac * st.get("depth", 56) + bob
        frac = (a.bottom - y) / a.h if st.get("climb") == "up" else (y - a.top) / a.h
        if st.get("turn_area") is not None:                           # the bend took the first part of the climb
            share = st["turn_area"].w / (st["turn_area"].w + a.h)
            frac = share + (1 - share) * frac
        return -(frac * st.get("depth", 100) + bob)

    def draw_water(self, screen, view, ox, oy):
        """The running water, over the ground chunks: ripples drifting along, foam lapping at the edges."""
        if not self.water_cells:
            return
        f = int(self.time * 5) % pa.WATER_FRAMES
        img = self.water_anim[f]
        for ty in range(max(0, view.top // TILE), min(self.h, view.bottom // TILE + 1)):
            for tx in range(max(0, view.left // TILE), min(self.w, view.right // TILE + 1)):
                mask = self.water_cells.get((tx, ty))
                if mask is None:
                    continue
                pos = (tx * TILE + ox, ty * TILE + oy)
                screen.blit(img, pos, ((tx % pa.WATER_SPAN) * TILE, (ty % pa.WATER_SPAN) * TILE, TILE, TILE))
                if mask:
                    edge = self.water_edges.get((mask, f))
                    if edge is None:
                        edge = self.water_edges[(mask, f)] = pa.water_edge(mask, f)
                    screen.blit(edge, pos)

    def cabinet_near(self, pos):
        """The arcade machine you're standing at (in front of it), if any."""
        here = [(abs(area.centerx - pos[0]), machine) for area, machine in self.cabinets if area.collidepoint(pos)]
        return min(here)[1] if here else None

    def npc_near(self, pos, reach=80):
        best, bd = None, reach
        for n in self.actors:
            if not n.shown:
                continue
            d = math.hypot(n.x - pos[0], n.y - pos[1])
            if d < bd:
                best, bd = n, d
        return best

    def nearby_solids(self, rect, actors=True):
        found, ids = [], set()
        for key in self._cells(rect):
            for s in self.solid_grid.get(key, ()):
                if id(s) not in ids:
                    ids.add(id(s))
                    found.append(s)
        if actors:
            found.extend(r for r in self.extra_solids if r.colliderect(rect))
        return found

    # ---------------------------------------------------- ground rendering
    def _ground_tile(self, x, y):
        ch = self.ground[y][x]
        v = (x * 73856093 ^ y * 19349663 ^ MAP_SEED) & 0xFFFF
        if ch == ",": return self.dirt[v % len(self.dirt)]
        if ch == "/":                                         # stairs, darker the further down they go
            st = getattr(self._map_def, "STAIRS", None) if not isinstance(self._map_def, str) else None
            k = 1.0
            along_x = bool(st) and st.get("axis") == "x"
            hh = self.stair_height((x + 0.5) * TILE, (y + 0.5) * TILE) if getattr(self, "stairs", None) else None
            if hh is not None:
                k = st["k_dark"] + (1 - st["k_dark"]) * hh
            elif st:
                c = x if along_x else y
                t = (c - st["y_dark"]) / ((st["y_light"] - st["y_dark"]) or 1)
                k = st["k_dark"] + (1 - st["k_dark"]) * max(0.0, min(1.0, t))
            k = round(k * 10) / 10
            img = self.stairs_tiles.get((k, v % 2, along_x))
            if img is None:
                img = self.stairs_tiles[(k, v % 2, along_x)] = (pa.stairs_tile_v if along_x else pa.stairs_tile)(k, v % 2)
            return img
        if ch == "(":                                         # steps climbing towards the right
            st = getattr(self._map_def, "STAIRS", None) or {}
            hh = self.stair_height((x + 0.5) * TILE, (y + 0.5) * TILE) if getattr(self, "stairs", None) else None
            kd = st.get("k_dark", 0.7)
            k = round((kd + (1 - kd) * (hh if hh is not None else 1)) * 10) / 10
            img = self.stairs_tiles.get((k, v % 2, "r"))
            if img is None:
                img = self.stairs_tiles[(k, v % 2, "r")] = pygame.transform.flip(pa.stairs_tile_v(k, v % 2), True, False)
            return img
        if ch == ")":                                         # bottom of the stairs, turning: steps climb towards the left
            st = getattr(self._map_def, "STAIRS", None) or {}
            hh = self.stair_height((x + 0.5) * TILE, (y + 0.5) * TILE) if getattr(self, "stairs", None) else None
            if hh is not None:
                t = hh
                k = round((st.get("k_dark", 0.7) + (1 - st.get("k_dark", 0.7)) * t) * 10) / 10
            else:
                tx0, _, tx1, _ = st.get("turn", (x, 0, x + 1, 0))
                t = (tx1 - 1 - x) / max(1, tx1 - 1 - tx0)        # 0 at the bottom (right), 1 where it meets the main flight
                k = round((st.get("k_dark", 0.7) + 0.15 * t) * 10) / 10
            img = self.stairs_tiles.get((k, v % 2, True))
            if img is None:
                img = self.stairs_tiles[(k, v % 2, True)] = pa.stairs_tile_v(k, v % 2)
            return img
        if ch == "`":                                         # the road down in the cutting
            lr = getattr(self._map_def, "LOWER_ROAD", None)
            if lr and x == lr.get("centre_x"):
                return self.deep_road_c
            return self.deep_road[v % len(self.deep_road)]
        if ch == "~": return self.water[0]
        if ch == "+": return self.pontoon[v % len(self.pontoon)]
        if ch == "-": return (self.paving if self.real is not None else self.concrete)[v % 4 % (4 if self.real is not None else 2)]
        if ch == "_": return self.wood[v % len(self.wood)]
        if ch == ":": return self.path_tiles[v % len(self.path_tiles)]
        if ch == " ": return self.void
        if ch in self.floors: return self.floors[ch][v % len(self.floors[ch])]
        if ch == "E": return self.wood[0]
        if ch == "z":
            return self.zebra
        if ch == "=":
            # Centre line on the middle lane of a straight road; plain tarmac at junctions
            def road(xx, yy):
                return 0 <= xx < self.w and 0 <= yy < self.h and self.ground[yy][xx] in "=z"
            up = down = left = right = 0
            while road(x, y - up - 1) and up < 9: up += 1
            while road(x, y + down + 1) and down < 9: down += 1
            while road(x - left - 1, y) and left < 9: left += 1
            while road(x + right + 1, y) and right < 9: right += 1
            vlen, hlen = up + down + 1, left + right + 1
            if vlen <= 7 and hlen > vlen and vlen % 2 == 1 and up == down:
                return self.road_line_h
            if hlen <= 7 and vlen > hlen and hlen % 2 == 1 and left == right:
                return self.road_line_v
            return self.road[v % len(self.road)]
        return self.grass[v % len(self.grass)]

    def _is_building(self, x, y):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return False
        ch = self.grid[y][x]
        return ch == "#" or ch in BUILDING_CHARS

    def chunk(self, cx, cy):
        key = (cx, cy)
        surf = self.chunk_cache.get(key)
        if surf is None:
            size = TILE * CHUNK_TILES
            surf = pygame.Surface((size, size)).convert()
            surf.fill((0, 0, 0))
            x0, y0 = cx * CHUNK_TILES, cy * CHUNK_TILES
            for ty in range(y0, min(y0 + CHUNK_TILES, self.h)):
                for tx in range(x0, min(x0 + CHUNK_TILES, self.w)):
                    px, py = (tx - x0) * TILE, (ty - y0) * TILE
                    surf.blit(self._ground_tile(tx, ty), (px, py))
                    if self.ground[ty][tx] in "=z":                  # kerb stones (+ double yellows) at the road edge
                        sides = set()
                        for dx, dy, side in ((0, -1, "n"), (0, 1, "s"), (-1, 0, "w"), (1, 0, "e")):
                            nx, ny = tx + dx, ty + dy
                            if 0 <= nx < self.w and 0 <= ny < self.h and self.ground[ny][nx] not in "=z":
                                sides.add(side)
                        if sides:
                            pa.kerb_and_lines(surf, px, py, sides, yellow=self.real is not None and self.ground[ty][tx] == "=")
                    elif self.ground[ty][tx] == "`":                 # the cutting: shadowed walls either side
                        for dx_ in (-1, 1):
                            if 0 <= tx + dx_ < self.w and self.ground[ty][tx + dx_] != "`":
                                sh = pygame.Surface((14, TILE), pygame.SRCALPHA); sh.fill((0, 0, 10, 120))
                                surf.blit(sh, (px if dx_ < 0 else px + TILE - 14, py))
                        if ty > 0 and self.ground[ty - 1][tx] != "`":
                            sh = pygame.Surface((TILE, 16), pygame.SRCALPHA); sh.fill((0, 0, 10, 120))
                            surf.blit(sh, (px, py))
                    elif self._is_building(tx, ty - 1) and not self._is_building(tx, ty):
                        pa.wall_shadow(surf, px, py)
            area = pygame.Rect(cx * size, cy * size, size, size)
            if self.shapes:
                self._draw_shapes(surf, area)
            for img, pos in self.decals:
                if area.colliderect(pygame.Rect(pos, img.get_size())):
                    surf.blit(img, (pos[0] - area.x, pos[1] - area.y))
            self.chunk_cache[key] = surf
            if len(self.chunk_cache) > 48:          # keep memory bounded on big maps
                self.chunk_cache.popitem(last=False)
        else:
            self.chunk_cache.move_to_end(key)
        return surf

    def _shape_texture(self, kind, area):
        """A chunk-sized sheet of grass / path paving lined up with the tile grid."""
        key = ("shape_tex", kind)
        tex = self.real_cache.get(key)
        if tex is None:
            size = TILE * CHUNK_TILES
            tex = pygame.Surface((size, size), pygame.SRCALPHA)
            tiles = self.grass if kind == "grass" else (self.path_tiles if kind == "path" else
                                                        (self.setts if kind == "setts" else self.paving))
            for ty in range(CHUNK_TILES):
                for tx in range(CHUNK_TILES):
                    tex.blit(tiles[(tx * 5 + ty * 3) % len(tiles)], (tx * TILE, ty * TILE))
            self.real_cache[key] = tex
        return tex

    def _draw_shapes(self, surf, area):
        """Grass and paths as smooth shapes (pixel-stepped edges), so diagonals aren't staircases."""
        px = pa.PX
        lo = TILE // px                                     # logical pixels per tile
        n = area.width // px
        ox, oy = area.x / px, area.y / px
        edge_cols = {"grass": (150, 146, 132), "path": (164, 154, 124), "plaza": (150, 146, 136), "setts": (96, 100, 108)}
        for shp in self.shapes:
            kind = shp["kind"]
            for layer in ("edge", "fill"):
                grow = 1 if layer == "edge" else 0
                mask = pygame.Surface((n, n), pygame.SRCALPHA)
                col = (255, 255, 255, 255)
                if "poly" in shp:
                    pts = [(x * lo - ox, y * lo - oy) for x, y in shp["poly"]]
                    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                    if max(xs) < -2 or min(xs) > n + 2 or max(ys) < -2 or min(ys) > n + 2: break
                    pygame.draw.polygon(mask, col, pts)
                    if grow: pygame.draw.polygon(mask, col, pts, 3)
                elif "line" in shp:
                    pts = [(x * lo - ox, y * lo - oy) for x, y in shp["line"]]
                    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
                    if max(xs) < -lo or min(xs) > n + lo or max(ys) < -lo or min(ys) > n + lo: break
                    wd = shp.get("width", 1) * lo + 2 * grow
                    for a, b in zip(pts, pts[1:]):
                        pygame.draw.line(mask, col, a, b, max(1, int(wd)))
                    for p in pts:
                        pygame.draw.circle(mask, col, p, wd / 2)
                else:
                    x, y, r = shp["circle"]
                    c = (x * lo - ox, y * lo - oy); rr = r * lo + grow
                    if c[0] + rr < 0 or c[0] - rr > n or c[1] + rr < 0 or c[1] - rr > n: break
                    pygame.draw.circle(mask, col, c, rr)
                mask = pygame.transform.scale(mask, (area.width, area.height))
                if layer == "edge":
                    if kind == "grass":
                        continue                            # grass edges: a soft darker rim instead
                    layer_img = pygame.Surface(area.size, pygame.SRCALPHA)
                    layer_img.fill(edge_cols[kind])
                else:
                    layer_img = self._shape_texture(kind, area).copy()
                layer_img.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(layer_img, (0, 0))

    def visible_sprites(self, view: pygame.Rect):
        size = TILE * CHUNK_TILES
        for cy in range(view.top // size - 1, view.bottom // size + 2):
            for cx in range(view.left // size - 1, view.right // size + 2):
                for sp in self.sprite_chunks.get((cx, cy), ()):
                    if sp.rect.colliderect(view):
                        yield sp


# ============================================================== player & camera
class Player:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)          # position of the FEET
        self.prev_pos = self.pos.copy()
        self.direction = "down"                 # down / up / left / right
        self.moving = False
        self.anim_time = 0.0
        self.names = list(CHARACTER_LOOKS)
        self.index = 0
        self.frames = build_character_frames(CHARACTER_LOOKS[self.names[0]])
        self.shadow = ellipse_shadow(30, 12)
        self.ghost_cache = {}

    @property
    def name(self):
        return self.names[self.index]

    def next_character(self):
        self.index = (self.index + 1) % len(self.names)
        self.frames = build_character_frames(CHARACTER_LOOKS[self.name])

    def hitbox(self):
        w, h = PLAYER_HITBOX
        r = FRect(0, 0, w, h)
        r.midbottom = (self.pos.x, self.pos.y + h / 2)
        return r

    def update(self, dt, keys, world: World):
        self.prev_pos.update(self.pos)
        d = pygame.Vector2(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        self.moving = d.length_squared() > 0
        if not self.moving:
            self.anim_time = 0.0
            return
        # Face the way you're going (sideways wins on diagonals)
        if d.x:
            self.direction = "right" if d.x > 0 else "left"
        else:
            self.direction = "down" if d.y > 0 else "up"
        d.normalize_ip()
        running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        speed = WALK_SPEED * (RUN_MULTIPLIER if running else 1)
        self.anim_time += dt * (RUN_MULTIPLIER if running else 1)
        step = d * speed * dt

        # Move one axis at a time so you slide along walls instead of sticking
        hw, hh = PLAYER_HITBOX[0] / 2, PLAYER_HITBOX[1] / 2
        self.pos.x += step.x
        box = self.hitbox()
        for s in world.nearby_solids(pygame.Rect(box).inflate(4, 4)):
            if box.colliderect(s):
                self.pos.x = s.left - hw if step.x > 0 else s.right + hw
                box = self.hitbox()
        self.pos.y += step.y
        box = self.hitbox()
        for s in world.nearby_solids(pygame.Rect(box).inflate(4, 4)):
            if box.colliderect(s):
                self.pos.y = s.top - hh if step.y > 0 else s.bottom + hh
                box = self.hitbox()

        self.pos.x = max(hw, min(world.pixel_w - hw, self.pos.x))
        self.pos.y = max(hh, min(world.pixel_h - hh, self.pos.y))

    def sprite(self):
        frame = int(self.anim_time * WALK_FPS) % 4 if self.moving else 0
        return self.frames[(self.direction, frame)]


class Camera:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.prev_pos = self.pos.copy()

    def update(self, target, dt, view_size, world: World):
        self.prev_pos.update(self.pos)
        t = 1 - math.exp(-CAMERA_SMOOTHING * dt)
        target = pygame.Vector2(target.x, target.y - CAMERA_LOOK_UP)   # see a bit more above you (tall buildings)
        self.pos += (target - self.pos) * t
        for i, (lim, view) in enumerate(((world.pixel_w, view_size[0]), (world.pixel_h, view_size[1]))):
            if lim <= view:
                self.pos[i] = lim / 2
            else:
                self.pos[i] = max(view / 2, min(lim - view / 2, self.pos[i]))


# ============================================================== main
def _brand(name):
    """Shop names as you'd write them: 'Bagel Box', but short ones like OMG stay in capitals."""
    return name if len(name) <= 4 else name.title()


class _NoKeysT:
    def __getitem__(self, k): return False
_NoKeys = _NoKeysT()


def render_scene(screen, world, centre, extra=()):
    """Draw a world (ground, water, everything depth-sorted, no player) centred on a point - for cut scenes and
    time echoes. extra = more Sprites to sort in (e.g. the detective in the opening scene)."""
    w, h = screen.get_size()
    ox, oy = round(w / 2 - centre[0]), round(h / 2 - centre[1])
    ox = min(0, max(w - world.pixel_w, ox)) if world.pixel_w >= w else (w - world.pixel_w) // 2
    oy = min(0, max(h - world.pixel_h, oy)) if world.pixel_h >= h else (h - world.pixel_h) // 2
    view = pygame.Rect(-ox, -oy, w, h)
    chunk_px = TILE * CHUNK_TILES
    screen.fill((0, 0, 0))
    for cy in range(max(0, view.top // chunk_px), min(world.h * TILE - 1, view.bottom) // chunk_px + 1):
        for cx in range(max(0, view.left // chunk_px), min(world.w * TILE - 1, view.right) // chunk_px + 1):
            screen.blit(world.chunk(cx, cy), (cx * chunk_px + ox, cy * chunk_px + oy))
    world.draw_water(screen, view, ox, oy)
    layer = list(world.visible_sprites(view.inflate(0, (pa.TOWER_H * pa.PX + TILE) * 2)))
    layer.extend(world.dynamic_sprites(view.inflate(128, 256)))
    layer.extend(extra)
    layer.sort(key=lambda sp: sp.sort_y)
    for sp in layer:
        img = sp.image
        if img is None:
            img = sp.image = sp.make()
        screen.blit(img, (sp.pos[0] + ox, sp.pos[1] + oy))
    return ox, oy


# TEMPORARY (for testing): jump straight to the stairs instead of walking there. Delete when done.
DEV_TELEPORTS = {
    pygame.K_F5: ("Frogmore Street", (9.6, 10.4), "left"),     # bottom of the Frogmore steps
    pygame.K_F6: ("Park Street", (69.0, 20.6), "up"),         # top of the Park Street stairwell
    pygame.K_F7: ("Harbourside", (29.5, 46.8), "up"),         # outside the arcade
}


def main():
    pygame.init()
    flags = pygame.SCALED | pygame.RESIZABLE
    try:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags, vsync=1)
    except pygame.error:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    pygame.display.set_caption("A Time To Catch")
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT, pygame.MOUSEBUTTONDOWN])
    pygame.key.stop_text_input()

    sheet = None
    map_index = 0
    clock_ = daynight.GameClock(BASE_DIR / "saves")
    clock_.hours = quest.story_start(clock_.hours)          # the story starts the next morning, every time
    world = World(MAPS[map_index][1], sheet, hour=clock_.hour)
    player = Player(world.spawn)
    camera = Camera(player.pos)
    camera.update(player.pos, 1, screen.get_size(), world)
    camera.prev_pos.update(camera.pos)

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,menlo,monospace", 15)
    hud_cache = {}

    def hud(text):
        surf = hud_cache.get(text)
        if surf is None:
            if len(hud_cache) > 64:
                hud_cache.clear()
            surf = hud_cache[text] = font.render(f" {text} ", True, HUD_TEXT, HUD_BG)
        return surf

    show_fps, show_hitboxes = False, False
    accumulator = 0.0
    running = True
    chunk_px = TILE * CHUNK_TILES
    outside = []                     # stack of (world, position) while you're inside a shop
    fade = 0.0                       # black fade after walking through a door
    door_lock = False                # just came out of a shop: let go of the key before a door works again
    fade_surf = pygame.Surface(screen.get_size()).convert(); fade_surf.fill((0, 0, 0))
    place_name = MAPS[map_index][0]
    pocket = inventory.Pocket(BASE_DIR / "saves")
    lighting = daynight.Lighting()
    def scene_world(kind, seed=7):
        """A place or room for a cut scene / time echo, built fresh (as it was: no police tape, nobody about)."""
        if kind[0] == "place":
            return World(PLACES[kind[1]], sheet, hour=12.0, past=True)
        room = "cafe" if kind[0] == "cafe" else kind[1]
        return World("\n".join(INTERIORS[room]), sheet, interior=dict(kind=room, seed=seed), hour=12.0)

    icons = {name: getattr(pa, name) for name in ("card_icon", "newspaper_icon", "recorder_icon", "token_icon", "photo_icon",
                                                  "notes_icon", "folder_icon", "cutting_icon")}
    story = quest.Story(pocket, inventory.Item, icons, player,
                        dict(render=render_scene, make_world=scene_world, clock=clock_, places=PLACES))
    watch_cache = {}
    flames = [daynight.flame(i) for i in range(4)]
    last_clock_save = 0.0
    talk = None                      # dict(npc, lines, i) while you're talking to someone
    talk_font = pygame.font.SysFont("consolas,menlo,monospace", 18)
    name_font = pygame.font.SysFont("consolas,menlo,monospace", 16, bold=True)

    named_worlds = {}                # places you've been (so people and cars carry on where they were)
    portal_lock = False
    portal_hold = False                  # after changing place: let go of the keys before another portal works

    def put_player(pos, direction=None):
        nonlocal accumulator
        player.pos.update(pos); player.prev_pos.update(pos)
        if direction: player.direction = direction
        camera.pos.update(pos)
        camera.update(player.pos, 1, screen.get_size(), world)
        camera.prev_pos.update(camera.pos)
        accumulator = 0.0

    def door_near():
        """The shop door the player is standing at, and whether they're walking into it."""
        if not world.doors:
            return None, False
        tx, ty = int(player.pos.x // TILE), int(player.pos.y // TILE)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                shop = world.doors.get((tx + dx, ty + dy))
                if shop is None:
                    continue
                door = pygame.Rect((tx + dx) * TILE, (ty + dy) * TILE, TILE, TILE)
                box = player.hitbox()
                if shop["side"] == "south" and dy == -1 and door.left - 8 <= box.centerx <= door.right + 8 and box.top - door.bottom < 10:
                    return shop, keys_now[pygame.K_w] or keys_now[pygame.K_UP]
                if shop["side"] == "north" and dy == 1 and door.left - 8 <= box.centerx <= door.right + 8 and door.top - box.bottom < 10:
                    return shop, keys_now[pygame.K_s] or keys_now[pygame.K_DOWN]
                if shop["side"] == "west" and dx == 1 and door.top - 6 <= box.centery <= door.bottom + 6 and door.left - box.right < 12:
                    return shop, keys_now[pygame.K_d] or keys_now[pygame.K_RIGHT]
                if shop["side"] == "east" and dx == -1 and door.top - 6 <= box.centery <= door.bottom + 6 and box.left - door.right < 12:
                    return shop, keys_now[pygame.K_a] or keys_now[pygame.K_LEFT]
        return None, False

    keys_now = pygame.key.get_pressed()

    while running:
        accumulator += min(clock.tick(FPS_CAP) / 1000, MAX_FRAME_TIME)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif story.busy:                                  # a cut scene / the newspaper: click to go on
                if talk is not None:
                    talk["npc"].talking = False; talk = None
                if story.handle(event) == "quit":
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pass
            elif talk is None and pocket.handle(event):
                pass                                          # the pocket / notebook used the key
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN) and talk is not None:
                talk["i"] += 1
                if talk["i"] >= len(talk["lines"]):
                    talk["npc"].talking = False; talk = None
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e and story.prompt(world, place_name, player):
                story.interact(world, place_name, player)            # the story: a locker, a shelf, a question...
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e and world.cabinet_near(player.pos) is not None:
                machine = world.cabinet_near(player.pos)            # play the machine: it takes over the screen
                result = arcade.play(screen, clock, machine, BASE_DIR / "saves", BASE_DIR, goal=story.arcade_goal(machine))
                if result == "quit":
                    running = False
                elif result == "won":
                    story.won(machine)
                pygame.event.clear()
                clock.tick()
                accumulator = 0.0
                keys_now = pygame.key.get_pressed()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                npc = world.npc_near((player.pos.x, player.pos.y))
                if npc is not None:
                    talk = dict(npc=npc, lines=npc.talk((player.pos.x, player.pos.y)), i=0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if talk is not None:
                        talk["npc"].talking = False; talk = None
                    else:
                        running = False
                elif event.key == pygame.K_TAB:
                    player.next_character()
                elif event.key == pygame.K_F1:
                    show_hitboxes = not show_hitboxes
                elif event.key == pygame.K_m:
                    map_index = (map_index + 1) % len(MAPS)
                    outside.clear()
                    named_worlds.clear()
                    world = World(MAPS[map_index][1], sheet, hour=clock_.hour)
                    place_name = MAPS[map_index][0]
                    put_player(world.spawn)
                    fade = 0.3
                elif event.key == pygame.K_F3:
                    show_fps = not show_fps
                elif event.key in DEV_TELEPORTS and not world.interior and talk is None:   # testing shortcut
                    to, (tx, ty), facing_ = DEV_TELEPORTS[event.key]
                    if to in PLACES:
                        named_worlds[place_name] = world
                        place_name = to
                        world = named_worlds.get(place_name) or World(PLACES[place_name], sheet, hour=clock_.hour)
                        put_player((tx * TILE, ty * TILE), facing_)
                        portal_lock = True
                        portal_hold = True
                        fade = 0.3

        keys = keys_now = pygame.key.get_pressed()
        clock_.fast = bool(keys[pygame.K_t]) and not pocket.reading
        clock_.update(min(clock.get_time() / 1000, 0.1))
        if pygame.time.get_ticks() / 1000 - last_clock_save > 20:
            clock_.save(); last_clock_save = pygame.time.get_ticks() / 1000
        if pocket.busy or talk is not None:
            keys = keys_now = _NoKeys
        if story.busy:                                       # the cut scene walks you about (or you stand still)
            keys = story.keys(player)
            keys_now = _NoKeys
        view_size = screen.get_size()
        pocket.update(clock.get_time() / 1000)
        world.update(min(clock.get_time() / 1000, 0.05), pygame.Rect(player.hitbox()), clock_.hour, clock_.is_night())
        story.update(min(clock.get_time() / 1000, 0.05), world, place_name, player, PLACES)
        if talk is not None and math.hypot(talk["npc"].x - player.pos.x, talk["npc"].y - player.pos.y) > 140:
            talk["npc"].talking = False; talk = None
        while accumulator >= FIXED_DT:
            player.update(FIXED_DT, keys, world)
            camera.update(player.pos, FIXED_DT, view_size, world)
            accumulator -= FIXED_DT

        # ---- walking into a shop / back out to the street
        near_shop, entering = door_near()
        if door_lock and not any(keys_now[k] for k in (pygame.K_w, pygame.K_s, pygame.K_UP, pygame.K_DOWN)):
            door_lock = False
        # ---- stairs between Park Street and Frogmore Street
        in_portal = None
        if portal_hold and not any(keys_now[k] for k in (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, pygame.K_UP,
                                                          pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)):
            portal_hold = False
        for pt in world.portals:
            if pt["area"].collidepoint(player.pos.x, player.pos.y):
                in_portal = pt
        if in_portal is None:
            portal_lock = False
            portal_hold = False                              # you've stepped clear of where you came in
        elif not portal_lock and not portal_hold and not world.interior:
            want = {"up": (pygame.K_w, pygame.K_UP), "down": (pygame.K_s, pygame.K_DOWN),
                    "left": (pygame.K_a, pygame.K_LEFT), "right": (pygame.K_d, pygame.K_RIGHT)}[in_portal.get("dir", "up")]
            if any(keys_now[k] for k in want) and in_portal["to"] in PLACES:
                named_worlds[place_name] = world
                place_name = in_portal["to"]
                world = named_worlds.get(place_name) or World(PLACES[place_name], sheet, hour=clock_.hour)
                sx, sy = in_portal["spawn"]
                if in_portal.get("keep") == "y":                # walking off the edge of the map: same place up/down
                    sy = player.pos.y / TILE
                put_player((sx * TILE, sy * TILE), in_portal.get("facing"))
                fade = 0.35
                portal_lock = True
                portal_hold = True
                near_shop = None
        shop_closed = near_shop is not None and not people.is_open(near_shop["kind"], clock_.hour)
        if entering and near_shop is not None and not door_lock and not shop_closed:
            outside.append((world, player.pos.copy(), near_shop, place_name))
            seed = near_shop["door"][0] * 31 + near_shop["door"][1] * 17
            layout, variant = story.room(near_shop["kind"])
            world = World("\n".join(INTERIORS[layout]), sheet,
                          interior=dict(kind=near_shop["kind"], seed=seed, variant=variant), hour=clock_.hour)
            story.entered(near_shop)
            place_name = _brand(near_shop.get("brand", "")) or SHOP_NAMES[near_shop["kind"]]
            if near_shop.get("brand"):
                place_name += f" ({SHOP_NAMES[near_shop['kind']]})"
            put_player(world.spawn, "up")
            fade = 0.35
        elif world.interior is not None and world.exit_tile is not None:
            ex, ey = world.exit_tile
            if player.hitbox().bottom > ey * TILE + TILE * 0.6:
                world, pos, shop, place_name = outside.pop()
                story.entered(None)
                dx, dy = shop["door"]
                if shop["side"] == "west":
                    put_player(((dx - 1) * TILE + TILE / 2 - 6, dy * TILE + TILE / 2 + 8), "left")
                elif shop["side"] == "east":
                    put_player(((dx + 1) * TILE + TILE / 2 + 6, dy * TILE + TILE / 2 + 8), "right")
                elif shop["side"] == "south":
                    put_player((dx * TILE + TILE / 2, (dy + 1) * TILE + TILE / 2), "down")
                else:
                    put_player((dx * TILE + TILE / 2, (dy - 1) * TILE + TILE / 2 - 4), "up")
                fade = 0.35
                door_lock = True

        alpha = accumulator / FIXED_DT
        p = player.prev_pos.lerp(player.pos, alpha)
        c = camera.prev_pos.lerp(camera.pos, alpha)
        w, h = view_size
        ox, oy = round(w / 2 - c.x), round(h / 2 - c.y)
        view = pygame.Rect(-ox, -oy, w, h)

        # ---- ground (pre-rendered chunks with shadows + rugs baked in)
        screen.fill((0, 0, 0))
        for cy in range(max(0, view.top // chunk_px), min(world.h * TILE - 1, view.bottom) // chunk_px + 1):
            for cx in range(max(0, view.left // chunk_px), min(world.w * TILE - 1, view.right) // chunk_px + 1):
                screen.blit(world.chunk(cx, cy), (cx * chunk_px + ox, cy * chunk_px + oy))
        world.draw_water(screen, view, ox, oy)

        # ---- player shadow sits on the ground (or on the step you're on)
        px, py = round(p.x), round(p.y)
        stair_dy = world.stair_offset(px, py)
        if stair_dy < 10:
            screen.blit(player.shadow, player.shadow.get_rect(center=(px + ox, py + oy + 4 + min(0, stair_dy))))

        # ---- depth-sorted layer: whatever is lower on screen is drawn in front
        sprite = player.sprite()
        p_rect = sprite.get_rect(midbottom=(px, py + 5))
        p_sort = py + PLAYER_HITBOX[1] / 2
        layer = list(world.visible_sprites(view.inflate(0, (pa.TOWER_H * pa.PX + TILE) * 2)))
        layer.extend(world.dynamic_sprites(view.inflate(128, 256)))
        layer.append(None)                                   # None = the player
        layer.sort(key=lambda s: p_sort if s is None else s.sort_y)
        hidden = False
        drawn_player = False
        reveal = p_rect.inflate(200, 150)                    # x-ray window through far-side roofs
        for sp in layer:
            if sp is None:
                if stair_dy > 0:                             # going down: you sink below the steps in front of you
                    d = int(stair_dy)
                    vis = max(0, sprite.get_height() - d)
                    screen.blit(sprite, p_rect.move(ox, oy + d), area=pygame.Rect(0, 0, sprite.get_width(), vis))
                else:                                        # going up: you rise with the steps
                    screen.blit(sprite, p_rect.move(ox, oy + int(stair_dy)))
                if pocket.lighter_on:                        # lighter held out in front
                    fl = flames[int(pygame.time.get_ticks() / 90) % 4]
                    hx = {"left": -22, "right": 22, "up": 16, "down": 18}[player.direction]
                    if stair_dy <= 30:
                        screen.blit(fl, (px + hx - fl.get_width() // 2 + ox, py - 46 + oy + int(stair_dy)))
                drawn_player = True
            else:
                img = sp.image
                if img is None:
                    img = sp.image = sp.make()
                if sp.cut and drawn_player and sp.rect.colliderect(reveal):
                    if sp.cut_img is None:
                        sp.cut_img = img.copy(); sp.cut_img.set_alpha(70)
                    screen.blit(sp.cut_img, (sp.pos[0] + ox, sp.pos[1] + oy))
                    continue
                if drawn_player and sp.faded is None and sp.rect.colliderect(p_rect):
                    hidden = True
                if sp.faded is not None and sp.sort_y > p_sort and sp.rect.colliderect(p_rect):
                    img = sp.faded                           # see the player through tree tops
                screen.blit(img, (sp.pos[0] + ox, sp.pos[1] + oy))

        if hidden:                                           # see-through silhouette when a building hides you
            ghost = player.ghost_cache.get(id(sprite))
            if ghost is None:
                ghost = sprite.copy(); ghost.set_alpha(120)
                player.ghost_cache[id(sprite)] = ghost
            screen.blit(ghost, p_rect.move(ox, oy))

        if show_hitboxes:
            for s in world.nearby_solids(view):
                pygame.draw.rect(screen, (255, 60, 60), s.move(ox, oy), 1)
            pygame.draw.rect(screen, (60, 255, 120), pygame.Rect(player.hitbox()).move(ox, oy), 1)

        # ---- day / night lighting
        dark = clock_.darkness()
        lit = list(world.lights(dark, clock_.hour, clock_.lamps_on()))
        if pocket.lighter_on:
            flick = 0.85 + 0.15 * math.sin(pygame.time.get_ticks() / 70) * math.sin(pygame.time.get_ticks() / 23)
            lit.append((px, py - 40, 170, (255, 170, 80), max(0.25, dark) * flick))
        ambient = clock_.ambient()
        if world.interior is not None and world.interior["kind"] == "club":
            ambient = (44, 32, 66)                           # it's dark in a club, whatever the time
        elif world.interior is not None and world.interior["kind"] == "arcade":
            ambient = (92, 80, 126)                          # lights down low, the machines glowing
        elif world.interior is not None and world.interior["kind"] == "zaza":
            ambient = (132, 112, 104)                        # dim, like a market at night, under the string lights
        elif world.interior is not None:                     # indoors the lights are on
            ambient = tuple(max(a, b) for a, b in zip(ambient, (236, 226, 206)))
        lighting.apply(screen, ambient, lit, ox, oy)

        # ---- HUD (not during a cut scene: the black bars and the dialogue have the screen)
        if story.cutscene is None:
            screen.blit(hud(f"{place_name}  |  WASD move  Shift run  E talk  I pocket  N notebook  F lighter  T time  Tab character  M map"), (12, 10))
        if story.cutscene is None:
            minute = int(clock_.hours * 60)
            face = watch_cache.get(minute)
            if face is None:
                watch_cache.clear(); face = watch_cache[minute] = daynight.watch_face(clock_.hour)
            screen.blit(face, (w - face.get_width() - 12, 8))
            wt = hud(f"Day {clock_.day}  {clock_.text()}" + ("  >>" if clock_.fast else ""))
            screen.blit(wt, (w - face.get_width() - wt.get_width() - 18, 8 + face.get_height() // 2 - wt.get_height() // 2))
        machine_here = world.cabinet_near(player.pos) if world.interior is not None else None
        story_tip = None if (pocket.busy or talk is not None) else story.prompt(world, place_name, player)
        if story.busy:
            pass
        elif story_tip:
            tip = hud(story_tip)
            screen.blit(tip, (w // 2 - tip.get_width() // 2, h - 96))
        elif machine_here is not None and talk is None and not pocket.busy:
            tip = hud(f"E: play {arcade.MACHINES[machine_here]['title']}")
            screen.blit(tip, (w // 2 - tip.get_width() // 2, h - 96))
        elif talk is None and not pocket.busy:
            npc = world.npc_near((player.pos.x, player.pos.y))
            if npc is not None and near_shop is None:
                tip = hud(f"E: talk to {npc.name}")
                screen.blit(tip, (w // 2 - tip.get_width() // 2, h - 96))
        if near_shop is not None and world.interior is None:
            arrow = {"south": "Up", "north": "Down", "west": "Right", "east": "Left"}[near_shop["side"]]
            where = (f"{_brand(near_shop['brand'])} ({SHOP_NAMES[near_shop['kind']]})" if near_shop.get("brand")
                     else f"the {SHOP_NAMES[near_shop['kind']]}")
            tip = hud(f"{arrow}: walk into {where}") if not shop_closed else hud(
                f"{where} is closed ({people.opening_text(near_shop['kind'])})")
            screen.blit(tip, (w // 2 - tip.get_width() // 2, h - 60))
        elif world.interior is not None:
            tip = hud("Walk out through the door at the bottom to leave")
            screen.blit(tip, (w // 2 - tip.get_width() // 2, h - 40))
        if show_fps:
            screen.blit(hud(f"FPS {clock.get_fps():.0f}"), (12, 34))
        if talk is not None:                                  # dialogue box
            bw_, bh_ = min(760, w - 40), 110
            bx, by = (w - bw_) // 2, h - bh_ - 20
            pygame.draw.rect(screen, (14, 16, 24), (bx - 3, by - 3, bw_ + 6, bh_ + 6))
            pygame.draw.rect(screen, (34, 38, 52), (bx, by, bw_, bh_))
            pygame.draw.rect(screen, (230, 190, 90) if talk["npc"].plot else (120, 140, 170), (bx, by, bw_, bh_), 2)
            screen.blit(name_font.render(talk["npc"].name, True, (240, 210, 120)), (bx + 16, by + 12))
            text = talk["lines"][talk["i"]]
            words, line, yy = text.split(), "", by + 40
            for wd in words:
                if talk_font.size(line + " " + wd)[0] > bw_ - 32:
                    screen.blit(talk_font.render(line, True, (236, 238, 244)), (bx + 16, yy)); yy += 24; line = wd
                else:
                    line = f"{line} {wd}".strip()
            screen.blit(talk_font.render(line, True, (236, 238, 244)), (bx + 16, yy))
            more = "E: next" if talk["i"] < len(talk["lines"]) - 1 else "E: done"
            m = hud(more); screen.blit(m, (bx + bw_ - m.get_width() - 10, by + bh_ - m.get_height() - 8))
        story.draw(screen, (ox, oy))
        pocket.draw(screen)
        if fade > 0:
            fade = max(0.0, fade - clock.get_time() / 1000)
            if fade_surf.get_size() != (w, h):
                fade_surf = pygame.Surface((w, h)).convert(); fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(int(255 * min(1.0, fade / 0.35)))
            screen.blit(fade_surf, (0, 0))

        pygame.display.flip()

    clock_.save()
    pocket.notebook.save()
    pygame.quit()


if __name__ == "__main__":
    main()
