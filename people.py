"""People: unique NPCs who walk the pavements, sit on benches, wait for the bus, and work in the shops
(barber cutting hair, doner man carving, barista making coffee, runners on the treadmills...).
Story characters (the homeless people in the alleys) come from story.py.
"""
import math, random, zlib
import pygame
import pixel_art as pa
from pixel_art import canvas, R, P, shade, up, add_outline, circle, ellipse_fill

TILE = 64

# ------------------------------------------------------------------ looks
SKINS = [(255, 220, 186), (241, 194, 150), (224, 172, 120), (198, 134, 88), (160, 104, 66), (122, 78, 48), (92, 58, 38),
         (250, 206, 170), (214, 160, 112)]
HAIRS = [(30, 26, 24), (60, 40, 28), (96, 64, 38), (150, 100, 54), (196, 150, 84), (230, 200, 130), (170, 60, 30),
         (200, 200, 200), (240, 240, 236), (80, 80, 86), (120, 40, 100), (40, 90, 160), (210, 90, 140)]
CLOTHES = [(200, 52, 52), (40, 90, 170), (240, 240, 236), (50, 52, 58), (60, 140, 90), (230, 180, 50), (150, 156, 166),
           (120, 70, 150), (240, 130, 60), (30, 120, 130), (170, 110, 80), (230, 150, 170), (90, 60, 40), (20, 40, 80),
           (130, 160, 60), (180, 30, 70), (100, 180, 220), (70, 70, 74), (210, 200, 170), (110, 30, 30)]
TROUSERS = [(40, 46, 70), (30, 30, 34), (60, 60, 66), (90, 70, 50), (140, 120, 90), (50, 70, 110), (70, 90, 60),
            (120, 40, 40), (180, 170, 150), (34, 50, 90)]
HAIR_STYLES = ["short", "short", "long", "long", "bun", "bald", "cap", "beanie", "hijab", "afro", "ponytail", "curly", "mohawk"]

FIRST_NAMES = """Aisha Alfie Amara Amir Ana Archie Arjun Ava Ayo Bea Ben Bilal Bronwen Caleb Callum Carys Chen Chloe
Ciaran Dai Dani Darius Dev Eddie Efe Elif Ella Emeka Erin Ezra Fatima Femi Finn Freya Gabe Gwen Hamza Hana Harvey Hiro
Idris Imani Isla Ivy Jack Jada Jamal Jas Jess Joe Jordan Kai Kalani Karim Kasia Kemi Kofi Lena Leo Lewis Liam Lily Lola
Maddie Malik Mara Marek Maya Mehmet Mehedi Mia Milo Mo Nadia Nia Niamh Nico Ola Olly Omar Oscar Paddy Pia Priya Raf
Rhys Rosa Rubi Ruth Sam Sami Sana Seren Shay Sian Sol Sophie Suki Tariq Tess Theo Tom Tomasz Una Viktor Wren Yara Yusuf
Zach Zara Zeynep Zofia Bryn Cerys Dylan Elis Gethin Lowri Owain Tegan Aled Ffion""".split()

_LOOKS = {}          # npc id -> look (so the same person looks the same every time you see them)

# The suspects (and John) always look the same, wherever you meet them - each with something that makes them stand
# out: Daniel's flat cap, PRESS lanyard and satchel; Martin's purple arcade polo, cap and name badge; Emily's red hair,
# yellow raincoat and green scarf; Professor Usher's tweed, bow tie and glasses (and, back in 1999, the arcade uniform);
# Jack's denim jacket over the 1999 uniform. Extra keys: coat (long coat), scarf, bowtie, lanyard, badge, patches.
_PLAIN = dict(shoe=(44, 38, 36), jacket=None, beard=False, glasses=False, bag=None, hat=(0, 0, 0), apron=None)
SUSPECTS = {
    "daniel": dict(_PLAIN, skin=(224, 172, 120), hair=(70, 50, 36), style="flatcap", hat=(92, 78, 62), beard=True,
                   glasses=True, shirt=(206, 220, 238), jacket=(128, 90, 56), pants=(52, 58, 74), shoe=(110, 70, 40),
                   bag=(120, 74, 40), lanyard=(200, 40, 40)),
    "martin": dict(_PLAIN, skin=(160, 104, 66), hair=(30, 26, 24), style="cap", hat=(250, 200, 40),
                   shirt=(120, 50, 170), pants=(30, 30, 34), shoe=(240, 240, 236), badge=(250, 210, 60)),
    "emily": dict(_PLAIN, skin=(255, 220, 186), hair=(190, 84, 36), style="long", shirt=(240, 236, 226),
                  coat=(232, 184, 46), scarf=(50, 140, 90), pants=(40, 46, 70), shoe=(110, 40, 40)),
    "usher_old": dict(_PLAIN, skin=(255, 220, 186), hair=(200, 200, 200), style="short", shirt=(232, 232, 226),
                      jacket=(122, 98, 66), patches=(80, 60, 40), bowtie=(170, 30, 40), pants=(76, 70, 62),
                      shoe=(90, 60, 40), glasses=True),
    "usher_young": dict(_PLAIN, skin=(255, 220, 186), hair=(150, 100, 54), style="short", shirt=(180, 40, 40),
                        pants=(30, 30, 34), glasses=True, badge=(250, 210, 60)),
    "jack": dict(_PLAIN, skin=(241, 194, 150), hair=(60, 40, 28), style="curly", shirt=(180, 40, 40),
                 jacket=(66, 98, 150), pants=(40, 46, 70), beard=True, badge=(250, 210, 60)),
    "john": dict(_PLAIN, skin=(241, 194, 150), hair=(60, 40, 28), style="short", shirt=(200, 60, 60),
                 jacket=(50, 52, 58), pants=(40, 46, 70), shoe=(240, 240, 236)),
}
_LOOKS.update({"crime_daniel": SUSPECTS["daniel"], "daniel": SUSPECTS["daniel"], "emily": SUSPECTS["emily"]})
_USED = set()        # look signatures already given out (everybody is unique)
_NAMES_USED = set()


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _like_a_suspect(lk):
    """True if a random passer-by would look too much like one of the suspects."""
    ginger = lk["hair"][0] > 150 and lk["hair"][1] < 110 and lk["hair"][2] < 80
    if ginger and lk["style"] in ("long", "ponytail", "bun"):                       # Emily's red hair
        return True
    if lk["style"] == "cap" and lk["shirt"][2] > 120 and lk["shirt"][0] > 90 and lk["shirt"][1] < 90:   # Martin's polo
        return True
    if lk["hair"][0] > 190 and lk["glasses"] and lk["jacket"]:                       # Usher's grey hair, glasses, tweed
        return True
    if lk["glasses"] and lk["beard"] and lk["bag"]:                                   # Daniel
        return True
    return False


def make_look(npc_id, seed, role="public", over=None):
    if npc_id in _LOOKS:
        return _LOOKS[npc_id]
    rng = random.Random(seed)
    for _ in range(200):
        lk = dict(
            skin=rng.choice(SKINS), hair=rng.choice(HAIRS[:9] if rng.random() < 0.85 else HAIRS),
            style=rng.choice(HAIR_STYLES), shirt=rng.choice(CLOTHES), pants=rng.choice(TROUSERS),
            shoe=rng.choice([(44, 38, 36), (240, 240, 236), (120, 70, 40), (30, 30, 34), (180, 40, 40)]),
            jacket=rng.choice(CLOTHES) if rng.random() < 0.35 else None,
            beard=rng.random() < 0.2, glasses=rng.random() < 0.22, bag=rng.choice(CLOTHES) if rng.random() < 0.25 else None,
            hat=rng.choice(CLOTHES), apron=None,
        )
        if lk["style"] == "hijab": lk["beard"] = False
        if role in ("barista", "kebab", "bookseller", "shopkeeper", "assistant"):
            lk["apron"] = {"barista": (40, 40, 44), "kebab": (240, 240, 236), "bookseller": (90, 60, 40),
                           "shopkeeper": (40, 90, 170), "assistant": (30, 30, 34)}[role]
        if role == "barber":
            lk["shirt"] = (30, 30, 34); lk["apron"] = (20, 20, 22)
        if role in ("gym", "runner", "lifter"):
            lk["jacket"] = None; lk["bag"] = None
            lk["shirt"] = rng.choice([(200, 52, 52), (40, 90, 170), (30, 30, 34), (240, 130, 60), (60, 140, 90)])
            lk["pants"] = rng.choice([(30, 30, 34), (40, 46, 70)])
        if role in ("shady", "dealer"):
            lk["jacket"] = rng.choice([(30, 30, 34), (40, 44, 52), (50, 40, 40), (34, 46, 40)])
            lk["shirt"] = shade(lk["jacket"], 1.1); lk["pants"] = rng.choice([(30, 30, 34), (44, 46, 56)])
            lk["style"] = "hood" if rng.random() < 0.7 else "cap"; lk["hat"] = (28, 28, 30)
            lk["glasses"] = False; lk["bag"] = None
        if role == "bouncer":
            lk["jacket"] = (20, 20, 22); lk["shirt"] = (20, 20, 22); lk["pants"] = (20, 20, 22)
            lk["style"] = rng.choice(["bald", "short"]); lk["glasses"] = False; lk["bag"] = None
        if role in ("dj", "bartender"):
            lk["shirt"] = (24, 24, 28); lk["jacket"] = None
        if role == "police":                                            # hi-vis jacket, black trousers, black cap
            lk["jacket"] = (214, 226, 40); lk["shirt"] = (240, 240, 240); lk["pants"] = (24, 24, 28)
            lk["shoe"] = (20, 20, 22); lk["bag"] = None; lk["glasses"] = False
            if lk["style"] != "hijab": lk["style"] = "cap"; lk["hat"] = (22, 22, 28)
        if role == "forensic":                                          # white paper suits, hoods up
            lk["jacket"] = (236, 238, 242); lk["shirt"] = (236, 238, 242); lk["pants"] = (230, 232, 238)
            lk["shoe"] = (90, 120, 200); lk["bag"] = None; lk["style"] = "hood"; lk["hat"] = (236, 238, 242)
            lk["beard"] = False
        if role == "journalist":
            lk["jacket"] = (110, 84, 60); lk["shirt"] = (220, 226, 236); lk["pants"] = (52, 58, 74)
            lk["glasses"] = True; lk["bag"] = (90, 60, 40); lk["style"] = "short"; lk["hair"] = (70, 50, 36)
            lk["beard"] = True
        if role == "chef":                                              # whites, a black apron, hair tucked away
            lk["shirt"] = (244, 244, 240); lk["jacket"] = None; lk["apron"] = (30, 30, 34); lk["bag"] = None
            lk["pants"] = (40, 40, 44); lk["glasses"] = False
            if lk["style"] not in ("bald", "hijab"): lk["style"] = "beanie"; lk["hat"] = (244, 244, 240)
        if role == "waiter":
            lk["shirt"] = (24, 24, 28); lk["jacket"] = None; lk["apron"] = (150, 40, 50); lk["bag"] = None
        if role == "stallholder":
            lk["apron"] = rng.choice([(40, 90, 60), (120, 60, 40), (40, 60, 110), (150, 40, 50)]); lk["bag"] = None
        if role == "drunk":
            lk["shirt"] = rng.choice([(240, 240, 236), (200, 52, 52), (40, 90, 170), (230, 150, 170)]); lk["jacket"] = None
        if role == "homeless":
            lk["jacket"] = rng.choice([(70, 60, 50), (60, 70, 56), (50, 56, 70), (80, 60, 40)])
            lk["shirt"] = shade(rng.choice(CLOTHES), 0.7); lk["pants"] = shade(rng.choice(TROUSERS), 0.8)
            lk["style"] = rng.choice(["beanie", "beanie", "long", "short", "curly", "cap"])
            lk["beard"] = rng.random() < 0.6 and lk["style"] != "hijab"
            lk["hat"] = rng.choice([(120, 40, 40), (60, 60, 66), (40, 70, 60), (140, 110, 60)])
        if over:
            if "coat" in over: lk["jacket"] = hexrgb(over["coat"])
            if "hat" in over: lk["hat"] = hexrgb(over["hat"]); lk["style"] = "beanie"
            for k in ("shirt", "pants", "hair", "skin"):
                if k in over: lk[k] = hexrgb(over[k])
        if _like_a_suspect(lk) and not over:
            continue                                     # nobody else gets mistaken for one of the suspects
        sig = tuple(sorted((k, str(v)) for k, v in lk.items()))
        if sig not in _USED:
            break
    _USED.add(sig)
    _LOOKS[npc_id] = lk
    return lk


def make_name(seed):
    rng = random.Random(seed * 7919)
    pool = [n for n in FIRST_NAMES if n not in _NAMES_USED] or FIRST_NAMES
    n = rng.choice(pool)
    _NAMES_USED.add(n)
    return n


# ------------------------------------------------------------------ drawing a person (12 x 18 art pixels)
EYE = (30, 28, 34)


def _head(s, lk, d, ox, oy, closed=False):
    skin, hair, style = lk["skin"], lk["hair"], lk["style"]
    R(s, skin, ox + 3, oy + 1, 6, 6)
    R(s, shade(skin, 0.85), ox + 3, oy + 6, 6, 1)
    if d == "left": P(s, skin, ox + 2, oy + 4)
    if d == "right": P(s, skin, ox + 9, oy + 4)
    hat = lk["hat"]
    if style in ("short", "long", "ponytail", "curly", "mohawk", "afro"):
        if style == "afro":
            R(s, hair, ox + 2, oy - 1, 8, 4); R(s, hair, ox + 2, oy + 3, 1, 2); R(s, hair, ox + 9, oy + 3, 1, 2)
            if d == "up": R(s, hair, ox + 2, oy, 8, 7)
        elif style == "mohawk":
            R(s, hair, ox + 5, oy - 1, 2, 3)
            if d == "up": R(s, hair, ox + 5, oy, 2, 5)
        else:
            if d == "down":
                R(s, hair, ox + 3, oy, 6, 2); P(s, hair, ox + 3, oy + 2); P(s, hair, ox + 8, oy + 2)
            elif d == "up":
                R(s, hair, ox + 3, oy, 6, 6)
            else:
                R(s, hair, ox + 3, oy, 6, 2); R(s, hair, ox + (6 if d == "left" else 3), oy + 2, 3, 3)
            if style == "curly":
                for x in range(3, 9, 2): P(s, shade(hair, 1.25), ox + x, oy)
            if style == "long":
                if d == "up": R(s, hair, ox + 3, oy + 3, 6, 6)
                elif d == "down": R(s, hair, ox + 2, oy + 2, 1, 6); R(s, hair, ox + 9, oy + 2, 1, 6)
                else: R(s, hair, ox + (6 if d == "left" else 3), oy + 3, 3, 6)
            if style == "ponytail":
                if d == "up": R(s, hair, ox + 5, oy + 6, 2, 4)
                elif d == "left": R(s, hair, ox + 9, oy + 2, 2, 4)
                elif d == "right": R(s, hair, ox + 1, oy + 2, 2, 4)
    elif style == "bun":
        R(s, hair, ox + 3, oy, 6, 2)
        if d == "up": R(s, hair, ox + 3, oy, 6, 6)
        circle(s, hair, ox + 6, oy - 1, 1)
    elif style == "cap":
        R(s, hat, ox + 3, oy, 6, 2)
        if d == "down": R(s, shade(hat, 0.7), ox + 3, oy + 2, 6, 1)
        elif d == "left": R(s, shade(hat, 0.7), ox + 1, oy + 2, 3, 1)
        elif d == "right": R(s, shade(hat, 0.7), ox + 8, oy + 2, 3, 1)
        else: R(s, hair, ox + 3, oy + 2, 6, 3)
    elif style == "flatcap":                                         # a tweedy flat cap, peak to the front
        R(s, hat, ox + 3, oy - 1, 6, 3); R(s, shade(hat, 1.2), ox + 3, oy - 1, 6, 1)
        if d == "down": R(s, shade(hat, 0.75), ox + 3, oy + 2, 6, 1)
        elif d == "left": R(s, shade(hat, 0.75), ox + 1, oy + 1, 3, 1); R(s, hair, ox + 7, oy + 2, 2, 2)
        elif d == "right": R(s, shade(hat, 0.75), ox + 8, oy + 1, 3, 1); R(s, hair, ox + 3, oy + 2, 2, 2)
        else: R(s, hair, ox + 3, oy + 2, 6, 3)
    elif style == "beanie":
        R(s, hat, ox + 3, oy - 1, 6, 3); R(s, shade(hat, 1.2), ox + 3, oy + 1, 6, 1); P(s, shade(hat, 1.3), ox + 6, oy - 2)
        if d == "up": R(s, hair, ox + 3, oy + 2, 6, 3)
    elif style == "hood":                                            # hoodie up, face in shadow
        hood = lk["jacket"] or (40, 40, 44)
        R(s, hood, ox + 2, oy, 8, 2); R(s, hood, ox + 2, oy + 2, 1, 5); R(s, hood, ox + 9, oy + 2, 1, 5)
        R(s, shade(skin, 0.55), ox + 3, oy + 2, 6, 2)
        if d == "up": R(s, hood, ox + 2, oy, 8, 7)
        elif d == "left": R(s, hood, ox + 5, oy, 5, 7)
        elif d == "right": R(s, hood, ox + 2, oy, 5, 7)
    elif style == "hijab":
        R(s, hat, ox + 2, oy, 8, 2); R(s, hat, ox + 2, oy + 2, 1, 6); R(s, hat, ox + 9, oy + 2, 1, 6)
        R(s, hat, ox + 3, oy + 7, 6, 2)
        if d == "up": R(s, hat, ox + 2, oy, 8, 9)
        elif d == "left": R(s, hat, ox + 5, oy, 5, 9)
        elif d == "right": R(s, hat, ox + 2, oy, 5, 9)
    if d != "up":
        if lk["beard"]:
            if d == "down": R(s, shade(hair, 0.9), ox + 3, oy + 5, 6, 2)
            else: R(s, shade(hair, 0.9), ox + (3 if d == "left" else 5), oy + 5, 4, 2)
        if closed:
            if d == "down": R(s, EYE, ox + 4, oy + 4, 1, 1); R(s, EYE, ox + 7, oy + 4, 1, 1)
        elif d == "down":
            P(s, EYE, ox + 4, oy + 4); P(s, EYE, ox + 7, oy + 4)
            if lk["glasses"]:
                R(s, (40, 40, 44), ox + 3, oy + 3, 6, 1); P(s, (200, 220, 240), ox + 4, oy + 4)
        else:
            ex = ox + (3 if d == "left" else 8)
            P(s, EYE, ex, oy + 4)
            if lk["glasses"]: R(s, (40, 40, 44), ex - (0 if d == "left" else 1), oy + 3, 2, 1)


def _torso(s, lk, d, ox, oy, h=6):
    shirt = lk["shirt"]
    tw = 6 if d in ("down", "up") else 4
    tx = ox + 6 - tw // 2
    R(s, shirt, tx, oy, tw, h)
    R(s, shade(shirt, 0.78), tx, oy + h - 2, tw, 2)
    R(s, shade(shirt, 1.15), tx, oy, 1, h - 2)
    if lk["jacket"] and d in ("down", "left", "right"):
        j = lk["jacket"]
        if d == "down":
            R(s, j, tx, oy, 2, h); R(s, j, tx + tw - 2, oy, 2, h)
        else:
            R(s, j, tx + (2 if d == "left" else 0), oy, 2, h)
    if lk["jacket"] and d == "up":
        R(s, lk["jacket"], tx, oy, tw, h)
    if lk["apron"] and d != "up":
        a = lk["apron"]
        R(s, a, tx + 1, oy + 1, tw - 2, h + 1)
        if d == "down": P(s, shade(a, 1.3), tx + 1, oy + 1)
    if lk.get("coat"):                                               # a long coat over the top
        c = lk["coat"]
        if d == "up":
            R(s, c, tx, oy, tw, h)
        elif d == "down":
            R(s, c, tx, oy, 2, h); R(s, c, tx + tw - 2, oy, 2, h); R(s, shade(c, 0.8), tx, oy + 3, tw, 1)
        else:
            R(s, c, tx + (1 if d == "left" else 0), oy, 3, h)
    if lk.get("patches") and d in ("left", "right"):                 # elbow patches on the tweed
        P(s, lk["patches"], tx + (1 if d == "left" else 2), oy + 3)
    if d == "down":
        if lk.get("lanyard"):                                       # PRESS lanyard
            P(s, lk["lanyard"], tx + 1, oy); P(s, lk["lanyard"], tx + 4, oy)
            P(s, lk["lanyard"], tx + 2, oy + 1); P(s, lk["lanyard"], tx + 3, oy + 1)
            R(s, (244, 244, 240), tx + 2, oy + 2, 2, 2); P(s, (200, 40, 40), tx + 2, oy + 2)
        if lk.get("badge"):                                         # name badge
            P(s, lk["badge"], tx + 4, oy + 1)
        if lk.get("bowtie"):
            P(s, lk["bowtie"], tx + 2, oy); P(s, lk["bowtie"], tx + 3, oy)
            P(s, shade(lk["bowtie"], 0.7), tx + 1, oy); P(s, shade(lk["bowtie"], 0.7), tx + 4, oy)
    if lk.get("scarf") and d != "up":
        R(s, lk["scarf"], tx, oy, tw, 1)
        if d == "down": R(s, lk["scarf"], tx + 1, oy + 1, 1, 3)
        else: P(s, lk["scarf"], tx + (3 if d == "left" else 0), oy + 1)
    elif lk.get("scarf"):
        R(s, lk["scarf"], tx, oy, tw, 1)
    if lk["bag"] and d in ("up", "left", "right"):
        R(s, lk["bag"], tx + (tw if d == "left" else -2) if d != "up" else tx + 1, oy + 1, 2 if d != "up" else tw - 2, 4)


def person(lk, d="down", f=0, pose="walk", tool=None):
    """One frame of an NPC. pose: walk, stand, run, sit, work, lie, press.  Returns a screen-size surface."""
    pants, shoe, skin = lk["pants"], lk["shoe"], lk["skin"]
    flip = d == "right"
    dd = "left" if flip else d
    if pose == "lie":                                               # in a sleeping bag, eyes shut
        s = canvas(22, 10)
        bag = lk["jacket"] or (70, 60, 50)
        R(s, (150, 120, 80), 0, 6, 22, 4)                           # cardboard
        R(s, shade((150, 120, 80), 0.8), 0, 9, 22, 1)
        R(s, bag, 6, 2, 15, 6); R(s, shade(bag, 1.2), 6, 2, 15, 1)
        for x in range(9, 20, 4): R(s, shade(bag, 0.8), x, 3, 1, 4)
        R(s, skin, 1, 2, 5, 5)                                       # head on its side
        R(s, lk["hat"], 0, 1, 4, 5)
        P(s, EYE, 3, 4)
        if lk["beard"]: R(s, lk["hair"], 2, 6, 3, 1)
        if f % 2: P(s, (230, 230, 240), 7, 0)                       # breathing "z"
        img = up(add_outline(s)).convert_alpha()
        return pygame.transform.flip(img, True, False) if d == "left" else img
    if pose == "press":                                              # lying on the bench, pushing the bar
        s = canvas(20, 12)
        R(s, pants, 12, 7, 6, 2); R(s, shoe, 18, 7, 2, 3)
        R(s, lk["shirt"], 5, 6, 7, 3)
        R(s, skin, 1, 5, 4, 4); R(s, lk["hair"], 0, 5, 2, 4)
        lift = 4 if f % 2 else 1
        for ax in (5, 10):
            R(s, skin, ax, lift, 1, 6 - lift)
        R(s, (170, 174, 182), 0, lift - 1, 20, 1)
        R(s, (30, 30, 34), 0, lift - 3, 2, 5); R(s, (30, 30, 34), 18, lift - 3, 2, 5)
        return up(add_outline(s)).convert_alpha()

    s = canvas(12, 18)
    if pose == "sit":
        oy = 3
        _head(s, lk, dd, 0, oy)
        _torso(s, lk, dd, 0, oy + 6, 5)
        if dd in ("down", "up"):
            R(s, pants, 3, oy + 11, 6, 2)                            # knees towards you
            R(s, pants, 3, oy + 13, 2, 1); R(s, pants, 7, oy + 13, 2, 1)
            R(s, shoe, 3, oy + 14, 2, 1); R(s, shoe, 7, oy + 14, 2, 1)
            for x in (2, 9):
                R(s, shade(lk["shirt"], 0.9), x, oy + 7, 1, 3); P(s, skin, x, oy + 10)
        else:
            R(s, pants, 2, oy + 10, 6, 2)                            # thighs forward
            R(s, pants, 2, oy + 12, 2, 2); R(s, shoe, 1, oy + 14, 3, 1)
            R(s, shade(lk["shirt"], 0.9), 5, oy + 7, 2, 3); P(s, skin, 4, oy + 10)
        if tool == "phone" and dd == "down":
            R(s, (30, 30, 34), 5, oy + 9, 2, 2); P(s, (120, 200, 240), 5, oy + 9)
        if tool == "cup":
            R(s, (240, 236, 226), 8 if dd == "down" else 3, oy + 9, 2, 2)
        if tool == "book":
            R(s, (160, 50, 50), 4, oy + 8, 4, 3); R(s, (240, 236, 220), 5, oy + 8, 2, 2)
        if tool == "can":
            R(s, (200, 50, 50), 8, oy + 9, 1, 2)
        img = up(add_outline(s)).convert_alpha()
        return pygame.transform.flip(img, True, False) if flip else img

    swing = (0, 1, 0, -1)[f % 4] * (2 if pose == "run" else 1)
    if pose in ("stand", "work"): swing = 0
    if pose == "dance": swing = (0, 1, 0, -1)[f % 4]
    bob = (f % 2) if pose in ("walk", "run", "dance") else 0
    if dd in ("down", "up"):
        for side, lift in ((0, swing), (1, -swing)):
            x = 3 + side * 4
            hh = 5 - max(0, lift)
            R(s, pants, x, 12 + bob, 2, hh - bob)
            R(s, shoe, x, 17 - max(0, lift), 2, 1)
    else:
        R(s, shade(pants, 0.8), 5 - swing, 12 + bob, 2, 5 - bob); R(s, shoe, 4 - swing, 17, 3, 1)
        R(s, pants, 5 + swing, 12 + bob, 2, 5 - bob); R(s, shoe, 5 + swing, 17, 3, 1)
    if lk["style"] == "long" and dd == "down":
        R(s, lk["hair"], 2, 2 + bob, 8, 7)
    if lk.get("coat"):                                               # the coat comes down over the knees
        c = lk["coat"]
        if dd in ("down", "up"):
            R(s, c, 3, 12 + bob, 6, 3); R(s, shade(c, 0.8), 3, 14 + bob, 6, 1)
            if dd == "down": P(s, shade(c, 0.7), 6, 12 + bob)
        else:
            R(s, c, 4, 12 + bob, 4, 3); R(s, shade(c, 0.8), 4, 14 + bob, 4, 1)
    _torso(s, lk, dd, 0, 7 + bob)
    arm = shade(lk.get("coat") or lk["jacket"] or lk["shirt"], 0.9)
    if pose == "dance":                                              # hands in the air, taking turns
        k = f % 4
        for x, up_ in ((2, k in (0, 1)), (9, k in (1, 2))):
            if up_:
                R(s, arm, x, 3 + bob, 1, 5); P(s, skin, x, 2 + bob)
            else:
                R(s, arm, x, 7 + bob, 1, 4); P(s, skin, x, 11 + bob)
    elif pose == "work":                                               # arms busy: chopping, cutting, folding
        k = f % 2
        if dd == "down":
            for x in (3, 8):
                R(s, arm, x, 8, 1, 2); P(s, skin, x, 10 - k)
            _tool(s, tool, 5, 9 - k, "down")
        elif dd == "left":
            R(s, arm, 3, 8 + k, 3, 1); P(s, skin, 2, 8 + k)
            _tool(s, tool, 0, 7 + k, "left")
        else:
            R(s, arm, 3, 8, 6, 1)
            P(s, skin, 3, 9 - k); P(s, skin, 8, 9 - k)
    elif dd in ("down", "up"):
        for x, sw in ((2, swing), (9, -swing)):
            R(s, arm, x, 7 + bob + max(0, sw), 1, 4)
            P(s, skin, x, 11 + bob + max(0, sw))
        if tool == "phone" and dd == "down":
            R(s, (30, 30, 34), 9, 9, 1, 2)
    else:
        R(s, arm, 5 + swing, 8 + bob, 2, 4)
        P(s, skin, 5 + swing, 12 + bob)
    _head(s, lk, dd, 0, bob)
    img = up(add_outline(s)).convert_alpha()
    return pygame.transform.flip(img, True, False) if flip else img


def _tool(s, tool, x, y, d):
    steel, steel_l = (180, 186, 196), (230, 236, 244)
    if tool == "scissors":
        P(s, steel_l, x, y - 1); P(s, steel, x + 1, y); P(s, steel_l, x, y + 1)
    elif tool == "knife":
        R(s, steel_l, x - (2 if d == "left" else 0), y, 3, 1); P(s, (60, 40, 30), x + (1 if d == "left" else 3), y)
    elif tool == "cloth":
        R(s, (200, 60, 60), x - 1, y, 4, 2)
    elif tool == "book":
        R(s, (160, 50, 50), x - 1, y, 4, 3); R(s, (240, 236, 220), x, y, 2, 2)
    elif tool == "cup":
        R(s, (240, 236, 226), x, y, 2, 2)
    elif tool == "broom":
        R(s, (150, 110, 60), x, y - 2, 1, 8); R(s, (200, 170, 90), x - 1, y + 6, 3, 2)
    elif tool == "dumbbell":
        R(s, (30, 30, 34), x - 1, y, 4, 1); P(s, (30, 30, 34), x - 1, y - 1); P(s, (30, 30, 34), x + 2, y - 1)


def dog(f=0):
    s = canvas(12, 8)
    fur, dark = (170, 120, 70), (120, 80, 46)
    R(s, fur, 3, 3, 7, 3); R(s, fur, 8, 1, 3, 3); P(s, dark, 9, 0); P(s, (30, 28, 34), 10, 2)
    R(s, dark, 3, 6, 1, 2); R(s, dark, 8, 6, 1, 2)
    R(s, fur, 1 + (f % 2), 2 - (f % 2), 2, 1)                       # wagging tail
    return up(add_outline(s)).convert_alpha()


def cup_sign():
    s = canvas(10, 8)
    R(s, (140, 110, 70), 0, 2, 10, 6); R(s, (90, 80, 70), 1, 4, 8, 1); R(s, (90, 80, 70), 1, 6, 6, 1)   # cardboard sign
    R(s, (230, 226, 216), 7, 0, 3, 3)                                # paper cup
    return up(add_outline(s)).convert_alpha()


# ------------------------------------------------------------------ dialogue
LINES = {
    "public": [
        ["Park Street's murder on the calves.", "Every time. Every single time."], ["Lovely day for it."],
        ["Sorry, can't stop - late for a lecture."], ["Have you tried the new place up the road?", "Can't remember the name."],
        ["I swear this hill gets steeper every year."], ["You lost? Wills is at the top, Green's at the bottom."],
        ["Mind the traffic, they don't stop for anyone."], ["I'm just people-watching. Don't mind me."],
        ["Is it going to rain? It's always going to rain."], ["Seen my dog? Small, brown, answers to Pickle."],
        ["The bus is late again. Shocking."], ["Love the shops round here. Hate the prices."],
        ["I'm meeting a friend at the fountain."], ["Did you hear something odd last night? Near City Hall?"],
    ],
    "barista": [["Morning! What can I get you?", "Oat milk's 40p extra, sorry - not my rules."], ["Flat white? You look like a flat white."]],
    "kebab": [["Chilli sauce? Garlic? Both? Both.", "Best doner on the hill, guaranteed."], ["Careful, it's hot!"]],
    "barber": [["Take a seat, won't be a minute.", "Short back and sides?"], ["Been anywhere nice this year?"]],
    "shopkeeper": [["Alright? Let me know if you need anything."], ["Card machine's playing up, cash is better."]],
    "assistant": [["Hi! Everything on that rail is twenty percent off."], ["Changing rooms are just at the back."]],
    "bookseller": [["Shh - only joking. Browse away.", "Mysteries are on the left."], ["That one's a good read. Bit of a twist."]],
    "gym": [["You here for a session? Sign in at the desk."], ["Don't drop the weights, the neighbours complain."]],
    "customer": [["Just looking, thanks."], ["Can't decide. I never can."], ["This place is my favourite."]],
    "runner": [["Can't... talk... running..."]], "lifter": [["Spot me? ...Kidding."]],
    "shady": [["You didn't see me."], ["Got a light?"], ["Keep walking, mate."], ["What you looking at?"],
              ["Wrong street to be poking about at this time."], ["...", "Not here. Not now."], ["You lost? Shouldn't be out this late."]],
    "bouncer": [["ID, please.", "...Alright, in you go."], ["Not tonight, mate. Come back when you've sobered up."],
                ["Queue's that way. No pushing."]],
    "dj": [["*nods to the beat*", "Request? Sorry, no requests."], ["This next one's a banger, trust me."]],
    "bartender": [["What are you having?", "Card only after midnight."], ["Water's free. Have some water."]],
    "dancer": [["WOOO!"], ["I love this song!"], ["Can't hear you! What?"], ["Best night ever. Every night's the best night ever."],
               ["Have you seen my friend? She's got my coat."]],
    "clubber": [["Is the queue always this long?"], ["My mate's on the list. Allegedly."], ["Freezing out here."]],
    "drunk": [["Where's the... where's the kebab place?"], ["I LOVE this city!"], ["Have you seen my mate? Tall. Very tall."],
              ["Is it Tuesday? It feels like a Tuesday."]],
    "nightowl": [["Bit late to be wandering about, isn't it?"], ["Night shift. Don't ask."], ["Can't sleep. Never can."],
                 ["The street's different at night. Quieter. Stranger."]],
    "client": [["Don't make me laugh, he's got scissors."]],
    "police": [["Sorry, I can't let you past the tape."], ["Forensics will be a while yet."]],
    "forensic": [["Please stay behind the tape."]],
    "journalist": [["..."]],
    "receptionist": [["Welcome to the Night Owl. Bed's yours whenever you need it."]],
    "chef": [["Hot plates! Mind your hands.", "Fresh batch coming up in two minutes."], ["Try the curry. Trust me."],
             ["Everything's cooked right here, in front of you."]],
    "waiter": [["Table for how many?", "Grab a plate and help yourself - drinks are bottomless."],
               ["Your server will bring the bill when you're done."], ["Can I take these plates?"]],
    "diner": [["Third plate. Don't judge me."], ["I always start with dessert here."], ["Have you tried the sushi?"],
              ["Bottomless drinks. Dangerous words."], ["I'm going back for the pizza."]],
    "stallholder": [["Fresh today, all of it!", "Three for a fiver."], ["Have a taste - go on."],
                    ["Card's fine, love."], ["Last ones, going cheap!"]],
    "shopper": [["Just having a look."], ["They do the best bread here."], ["It's always packed at lunchtime."],
                ["Have you seen the flower stall?"]],
}


# ------------------------------------------------------------------ the NPC
class NPC:
    def __init__(self, npc_id, x, y, role="public", behaviour="stand", d="down", pose=None, tool=None, seed=None,
                 name=None, lines=None, look_over=None, speed=60.0):
        self.id = npc_id
        seed = seed if seed is not None else (zlib.crc32(npc_id.encode()) & 0xFFFFFF)
        self.rng = random.Random(seed)
        self.role = role
        self.look = make_look(npc_id, seed, role, look_over)
        self.name = name or make_name(seed)
        self.x, self.y = float(x), float(y)       # feet position, screen pixels
        self.d = d
        self.behaviour = behaviour                # stand, walk_x, path, wander, sit, work, sleep, run, press
        self.pose = pose or {"sit": "sit", "work": "work", "sleep": "lie", "run": "run", "press": "press",
                             "dance": "dance"}.get(behaviour, "stand")
        self.tool = tool
        self.speed = speed * self.rng.uniform(0.8, 1.25)
        self.t = self.rng.uniform(0, 10)
        self.wait = self.rng.uniform(0, 3)
        self.moving = False
        self.frames = {}
        pool = LINES.get(role, LINES["public"])
        self.lines = lines or [self.rng.choice(pool)]
        self.chat = 0                             # which conversation we're on
        self.talking = False
        self.plot = False
        self.flags = {}
        self.extras = []                          # (image_fn, dx, dy, sort_dy) drawn with the NPC (dog, sign)
        self.sort_bias = 0                        # draw a little in front of the chair/bench they're on
        self.hours = (0, 24)                      # when they're out: (from, to) in 24h time; to > 24 = past midnight
        self.shown = True
        self.phases = None                        # story characters: {"day": {...}, "night": {...}}
        self.phase = None
        self.chats = {}
        self.anim_speed = {"work": 3.5, "run": 12.0, "press": 1.4, "lie": 0.8, "dance": 4.5}.get(self.pose, 8.0)
        # movement state
        self.x0 = self.x1 = self.x
        self.y0 = self.y1 = self.y
        self.path = []; self.pi = 0; self.pdir = 1
        self.target = None
        self.blocked = 0.0

    # ---- art
    def image(self):
        if self.moving:
            pose, f = ("run" if self.pose == "run" else "walk"), int(self.t * self.anim_speed) % 4
        elif self.pose in ("work", "lie", "press", "run", "dance"):
            f = int(self.t * self.anim_speed) % (4 if self.pose in ("run", "dance") else 2)
            pose = self.pose
        else:
            pose, f = self.pose, 0
        key = (pose, self.d, f)
        img = self.frames.get(key)
        if img is None:
            img = self.frames[key] = person(self.look, self.d, f, pose, self.tool)
        return img

    def feet_rect(self):
        r = pygame.Rect(0, 0, 22, 12); r.midbottom = (int(self.x), int(self.y)); return r

    def solid(self):
        """The bit of them you bump into (None = you can't, e.g. someone sat on a café chair)."""
        if self.pose == "lie":
            r = pygame.Rect(0, 0, 84, 22); r.midbottom = (int(self.x), int(self.y) + 4); return r
        if self.pose == "sit" and self.role == "homeless":
            r = pygame.Rect(0, 0, 40, 18); r.midbottom = (int(self.x), int(self.y)); return r
        if self.behaviour in ("walk_x", "walk_y", "path", "wander", "stand", "chat") or self.pose in ("stand", "work", "dance"):
            return self.feet_rect()
        return None

    def active(self, hour):
        a, b = self.hours
        if b - a >= 24: return True
        if b <= 24: return a <= hour < b
        return hour >= a or hour < b - 24

    def set_phase(self, name):
        """Story characters behave differently by day and by night (see story.py)."""
        if not self.phases or name == self.phase: return
        if self.phase: self.chats[self.phase] = self.chat
        self.phase = name
        cfg = self.phases[name]
        pose = cfg.get("pose", "sit")
        self.behaviour = {"sit": "sit", "sleep": "sleep"}.get(pose, "stand")
        self.pose = {"sit": "sit", "sleep": "lie"}.get(pose, "stand")
        self.anim_speed = {"lie": 0.8}.get(self.pose, 8.0)
        self.d = cfg.get("facing", "down")
        self.lines = cfg.get("lines") or self.lines
        self.chat = self.chats.get(name, 0)
        self.extras = [e for e in self.extras if e[0] == "dog"]
        if pose == "sit":
            self.extras.append((cup_sign, 30, 4, -1))

    # ---- talking
    def talk(self, player_pos):
        if self.pose in ("stand", "walk") or self.behaviour in ("walk_x", "walk_y", "path", "wander", "stand"):
            dx, dy = player_pos[0] - self.x, player_pos[1] - self.y
            if self.pose not in ("sit", "lie", "press", "run", "work"):
                self.d = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")
        self.talking = True
        conv = self.lines[min(self.chat, len(self.lines) - 1)]
        if isinstance(conv, str): conv = [conv]
        self.chat += 1
        return list(conv)

    # ---- behaviour
    def update(self, dt, world, player_rect):
        self.t += dt
        self.moving = False
        if self.talking:
            return
        b = self.behaviour
        if b == "walk_x":
            self._walk_x(dt, world, player_rect)
        elif b == "walk_y":
            self._walk_y(dt, world, player_rect)
        elif b == "path":
            self._walk_path(dt, world, player_rect)
        elif b == "wander":
            self._wander(dt, world, player_rect)
        elif b == "stand" and self.rng.random() < dt * 0.15:
            self.d = self.rng.choice(["down", "left", "right", "down"])

    def _step(self, dx, dy, world, player_rect):
        nx, ny = self.x + dx, self.y + dy
        r = pygame.Rect(0, 0, 20, 10); r.midbottom = (int(nx), int(ny))
        if r.colliderect(player_rect):
            return False
        for s in world.nearby_solids(r, actors=False):
            if r.colliderect(s):
                return False
        if not (0 < nx < world.pixel_w and 0 < ny < world.pixel_h):
            return False
        self.x, self.y = nx, ny
        self.moving = True
        return True

    def _walk_x(self, dt, world, player_rect):
        if self.wait > 0:
            self.wait -= dt; return
        direction = 1 if self.d == "right" else -1
        if self.d not in ("left", "right"):
            self.d = self.rng.choice(["left", "right"]); return
        ok = self._step(direction * self.speed * dt, 0, world, player_rect)
        if not ok:
            # try to sidestep up or down a little, otherwise turn round
            for dy in (-1, 1):
                if self._step(0, dy * self.speed * dt, world, player_rect) and self.rng.random() < 0.9:
                    return
            self.blocked += dt
            if self.blocked > 0.6:
                self.d = "left" if self.d == "right" else "right"; self.blocked = 0
            return
        self.blocked = 0
        if self.x < self.x0: self.d = "right"
        if self.x > self.x1: self.d = "left"
        if self.rng.random() < dt * 0.06:                 # stop to look in a shop window now and then
            self.wait = self.rng.uniform(1.5, 4.0); self.d = "up" if self.rng.random() < 0.5 else self.d
        if self.d == "up":
            self.d = self.rng.choice(["left", "right"])

    def _walk_y(self, dt, world, player_rect):
        """Up and down a pavement (Frogmore Street runs up the screen)."""
        if self.wait > 0:
            self.wait -= dt; return
        if self.d not in ("up", "down"):
            self.d = self.rng.choice(["up", "down"])
        direction = 1 if self.d == "down" else -1
        if not self._step(0, direction * self.speed * dt, world, player_rect):
            self.blocked += dt
            if self.blocked > 0.6:
                self.d = "up" if self.d == "down" else "down"; self.blocked = 0
            return
        self.blocked = 0
        if self.y < self.y0: self.d = "down"
        if self.y > self.y1: self.d = "up"
        if self.rng.random() < dt * 0.04:
            self.wait = self.rng.uniform(1.0, 3.0)

    def _walk_path(self, dt, world, player_rect):
        if self.wait > 0:
            self.wait -= dt; return
        tx, ty = self.path[self.pi]
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 4:
            self.pi += self.pdir
            if self.pi >= len(self.path) or self.pi < 0:
                self.pdir *= -1; self.pi += 2 * self.pdir
                self.pi = max(0, min(len(self.path) - 1, self.pi))
                self.wait = self.rng.uniform(1, 4)
            return
        step = min(dist, self.speed * dt)
        mx, my = dx / dist * step, dy / dist * step
        self.d = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")
        if not self._step(mx, my, world, player_rect):
            self.blocked += dt
            if self.blocked > 1.0:
                self.pdir *= -1; self.pi = max(0, min(len(self.path) - 1, self.pi + self.pdir)); self.blocked = 0

    def _wander(self, dt, world, player_rect):
        """Shop customers: walk the aisles, stop to browse the shelves."""
        if self.wait > 0:
            self.wait -= dt; return
        if self.target is None:
            free = world.free_floor
            if not free: return
            tx0, ty0 = int(self.x // TILE), int((self.y - 8) // TILE)
            options = [(x, y) for (x, y) in free if (y == ty0 or x == tx0) and (x, y) != (tx0, ty0)
                       and _clear_line(world, tx0, ty0, x, y)]
            if not options:
                self.wait = 1.0; return
            x, y = self.rng.choice(options)
            self.target = (x * TILE + TILE / 2, y * TILE + TILE - 10)
        tx, ty = self.target
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 3:
            self.target = None
            self.wait = self.rng.uniform(1.5, 5.0)
            self.d = self.rng.choice(["up", "up", "left", "right", "down"])
            return
        step = min(dist, self.speed * dt)
        self.d = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")
        if not self._step(dx / dist * step, dy / dist * step, world, player_rect):
            self.blocked += dt
            if self.blocked > 0.8: self.target = None; self.blocked = 0; self.wait = 0.5


def _clear_line(world, x0, y0, x1, y1):
    if y0 == y1:
        return all((x, y0) in world.free_set for x in range(min(x0, x1), max(x0, x1) + 1))
    return all((x0, y) in world.free_set for y in range(min(y0, y1), max(y0, y1) + 1))


# ------------------------------------------------------------------ putting people in the world
def populate_frogmore(world, map_def):
    """Frogmore Street, under the bridge: people walking up and down, the OMG queue and bouncer at night,
    the odd shady character under the arches, and whichever story characters live down here."""
    rng = random.Random(77)
    npcs = []
    for i, x in enumerate(map_def.PAVEMENT_XS * 4):
        top_y, bot_y = getattr(map_def, "WALK_RANGE", (1.2, world.h - 0.6))
        n = NPC(f"fwalk{i}", (x + rng.uniform(-0.2, 0.2)) * TILE, rng.uniform(top_y + 0.5, bot_y - 0.5) * TILE, "public", "walk_y",
                d=rng.choice(["up", "down"]), seed=7000 + i, speed=58)
        n.y0, n.y1 = top_y * TILE, bot_y * TILE
        n.hours = [(7, 20), (8, 22), (10, 19), (19, 27)][i % 4]
        npcs.append(n)
    for k, (x, y, d, role, hours) in enumerate(map_def.EXTRA_PEOPLE):
        n = NPC(f"fx{k}", x * TILE, y * TILE, role, "stand", d=d, seed=7100 + k)
        n.hours = hours
        npcs.append(n)
    try:
        import story
        for c in story.STORY_NPCS:
            if c.get("map") != getattr(map_def, "NAME", ""):
                continue
            sx, sy = c["spot"]
            pose = c.get("pose", "sit")
            n = NPC(c["id"], (sx + 0.5) * TILE, sy * TILE + TILE - 10, "homeless", {"sit": "sit", "sleep": "sleep"}.get(pose, "stand"),
                    d=c.get("facing", "down"), seed=zlib.crc32(c["id"].encode()) & 0xFFFF, name=c["name"],
                    lines=c.get("lines"), look_over=c.get("look"))
            n.plot = True; n.flags = c.get("flags", {})
            if c.get("dog"): n.extras.append(("dog", -36, 6, 0))
            n.phases = dict(day=dict(pose=pose, facing=c.get("facing", "down"), lines=c.get("lines")),
                            night=dict(pose=c.get("night_pose", pose), facing=c.get("night_facing", c.get("facing", "down")),
                                       lines=c.get("night_lines") or c.get("lines")))
            n.set_phase("day")
            npcs.append(n)
    except Exception as e:
        print("story.py:", e)
    return npcs


def populate_harbour(world, map_def):
    """The harbourside: people walking the pavements and the Waterfront, waiting for the ferry, out on the
    pontoons, on the benches, and a few outside the arcade."""
    rng = random.Random(1873)
    npcs = []
    k = 0
    for walker in map_def.WALKERS:
        axis, line, a, b, count = walker[:5]
        role = walker[5] if len(walker) > 5 else "public"
        windows = walker[6] if len(walker) > 6 else [(7, 20), (8, 22), (10, 19), (9, 21), (19, 26)]
        for i in range(count):
            if axis == "x":
                n = NPC(f"hwalk{k}", rng.uniform(a + 0.5, b - 0.5) * TILE, line * TILE, role, "walk_x",
                        d=rng.choice(["left", "right"]), seed=8000 + k, speed=rng.uniform(52, 66))
                n.x0, n.x1 = a * TILE, b * TILE
            else:
                n = NPC(f"hwalk{k}", line * TILE + rng.uniform(-6, 6), rng.uniform(a + 0.5, b - 0.5) * TILE, role, "walk_y",
                        d=rng.choice(["up", "down"]), seed=8000 + k, speed=rng.uniform(52, 66))
                n.y0, n.y1 = a * TILE, b * TILE
            n.hours = windows[(i + k) % len(windows)]
            if rng.random() < 0.15: n.tool = "phone"
            npcs.append(n); k += 1
    for j, extra in enumerate(map_def.EXTRA_PEOPLE):
        x, y, d, role, hours = extra[:5]
        pose = extra[5] if len(extra) > 5 else "stand"
        n = NPC(f"hx{j}", x * TILE, y * TILE, role, pose, d=d, seed=8100 + j,
                tool=("cup" if pose == "sit" and j % 2 else None))
        if pose == "sit":
            n.sort_bias = 4
        n.hours = hours
        npcs.append(n)
    cs = getattr(map_def, "CRIME_SCENE", None)
    if cs:                                                             # the police and forensics at the scene
        ox, oy, od = cs["officer"]
        n = NPC("crime_officer", ox * TILE, oy * TILE, "police", "stand", d=od, seed=7310, name="Police Officer",
                lines=[["We'll be here a while yet.", "The arcade he worked at is just up there - the pink sign."],
                       ["If you find anything, let us know."]])
        n.plot = True
        npcs.append(n)
        gx, gy, gd = cs["guard"]
        npcs.append(NPC("crime_guard", gx * TILE, gy * TILE, "police", "stand", d=gd, seed=7320, name="PC Dunn"))
        for k, (fx, fy, fd) in enumerate(cs["forensics"]):
            f = NPC(f"crime_forensic{k}", fx * TILE, fy * TILE, "forensic", "work", d=fd, seed=7330 + k)
            f.anim_speed = 1.6 + k * 0.5
            npcs.append(f)
        dx, dy, dd = cs["daniel"]
        d = NPC("crime_daniel", dx * TILE, dy * TILE, "journalist", "stand", d=dd, seed=7350, name="Daniel Shaw",
                lines=[["Let me know if you find anything."]])
        d.plot = True
        npcs.append(d)
    for y in range(world.h):                                           # benches
        for x in range(world.w):
            if world.grid[y][x] == "q" and rng.random() < 0.5:
                n = NPC(f"hbench{x}_{y}", x * TILE + 32 + rng.choice((-14, 14)), y * TILE + 46, "public", "sit", d="down",
                        tool=rng.choice([None, "phone", "cup", "book", None]), seed=8300 + x * 31 + y)
                n.sort_bias = 4
                n.hours = rng.choice([(9, 18), (10, 19), (8, 16), (12, 20)])
                npcs.append(n)
    return npcs


def populate_street(world, map_def):
    """Pedestrians on both pavements, people on benches, at café tables and the bus stop, the story characters."""
    rng = random.Random(1856)
    npcs = []
    W = world.w
    # pavement walkers (north side rows 21-22, south side rows 30-31)
    for i in range(30):
        north = i % 3 != 0
        row = rng.choice((21, 22)) if north else rng.choice((30, 31))
        x = rng.uniform(4, W - 4) * TILE
        y = row * TILE + TILE - 12
        kind = "public" if i % 10 < 7 else ("public" if i % 10 < 9 else "nightowl")
        n = NPC(f"walker{i}", x, y, kind, "walk_x", d=rng.choice(["left", "right"]), seed=1000 + i, speed=62)
        n.x0, n.x1 = 2 * TILE, (W - 2) * TILE
        n.hours = [(7, 20), (8, 19), (7.5, 21), (6.5, 18), (9, 20), (8, 22), (7, 19), (11, 23.5), (12, 23), (19, 26.5)][i % 10]
        if rng.random() < 0.15: n.tool = "phone"
        npcs.append(n)
    # College Green: strollers following the paths
    for j, shp in enumerate(s for s in getattr(map_def, "GROUND_SHAPES", []) if s.get("kind") == "path" and "line" in s):
        for k in range(2 if j == 0 else 1):
            pts = [(x * TILE, y * TILE + 16) for x, y in shp["line"]]
            dense = []
            for a, b in zip(pts, pts[1:]):
                steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 48))
                for t in range(steps):
                    dense.append((a[0] + (b[0] - a[0]) * t / steps, a[1] + (b[1] - a[1]) * t / steps))
            dense.append(pts[-1])
            st = rng.randrange(len(dense))
            n = NPC(f"stroller{j}_{k}", dense[st][0], dense[st][1], "public", "path", seed=2000 + j * 10 + k, speed=48)
            n.path, n.pi, n.pdir = dense, st, rng.choice((-1, 1))
            n.hours = (8, 20) if k == 0 else (10, 18.5)
            npcs.append(n)
    # benches, café tables, bus stop
    seats = 0
    for y in range(world.h):
        for x in range(W):
            ch = world.grid[y][x]
            cx, cy = x * TILE + TILE // 2, y * TILE + TILE // 2
            if ch == "q" and rng.random() < 0.55:
                n = NPC(f"bench{x}_{y}", cx + rng.choice((-14, 14)), cy + 14, "public", "sit", d="down",
                        tool=rng.choice([None, "phone", "cup", "book", None]), seed=3000 + x * 31 + y)
                n.sort_bias = 4
                n.hours = rng.choice([(9, 18), (10, 19), (8, 16), (12, 20)])
                npcs.append(n); seats += 1
            elif ch == "J" and world.interior is None and rng.random() < 0.7:
                left = rng.random() < 0.5
                n = NPC(f"cafe{x}_{y}", cx + (-26 if left else 30), y * TILE + TILE - 8, "public", "sit",
                        d="right" if left else "left", tool="cup", seed=3500 + x * 31 + y)
                n.sort_bias = 8
                n.hours = (8, 18)
                npcs.append(n)
            elif ch == "u":
                for k, off in enumerate((-40, 44)):
                    n = NPC(f"busq{x}_{k}", cx + off, cy + 26, "public", "stand", d="left" if k else "down",
                            seed=3900 + k, lines=[["Bus is here, driver's on his break."], ["I always get this one."]])
                    n.hours = (6, 23.5) if k == 0 else (7, 19)
                    npcs.append(n)
    # a few people stood chatting in pairs on the pavement
    for k, xt in enumerate((40, 54, 110)):
        for side in (0, 1):
            n = NPC(f"chat{k}_{side}", (xt + side * 0.7) * TILE, 21 * TILE + 52, "public", "stand",
                    d="right" if side == 0 else "left", seed=4000 + k * 2 + side)
            n.behaviour = "chat"
            n.hours = [(10, 21), (12, 22.5), (9, 18)][k]
            npcs.append(n)
    # ---- after dark: people you'd rather not meet, and students on their way home
    shady_spots = [(46.4, 20.6, "right"), (61.6, 20.5, "left"), (64.2, 31.4, "right"), (100.5, 31.5, "left"),
                   (29.5, 20.5, "down"), (113.0, 39.5, "left"), (32.2, 32.5, "down"), (44.6, 32.4, "down")]
    for k, (sx, sy, d) in enumerate(shady_spots):
        n = NPC(f"shady{k}", sx * TILE, sy * TILE, "shady", "stand", d=d, seed=5000 + k)
        n.hours = [(21, 29), (22, 28.5), (20.5, 29.5), (23, 28), (21.5, 27), (22, 29), (20, 26), (23.5, 29.5)][k]
        npcs.append(n)
    for k in range(3):                                     # two shady types walking slowly about
        n = NPC(f"lurker{k}", rng.uniform(20, W - 20) * TILE, (30 + k % 2) * TILE + 52, "shady", "walk_x",
                d=rng.choice(["left", "right"]), seed=5100 + k, speed=34)
        n.x0, n.x1 = 2 * TILE, (W - 2) * TILE
        n.hours = (21.5, 28.5)
        npcs.append(n)
    for k in range(4):                                     # students heading home from a night out
        n = NPC(f"drunk{k}", rng.uniform(10, 66) * TILE, (21 + k % 2) * TILE + 52, "drunk", "walk_x",
                d=rng.choice(["left", "right"]), seed=5200 + k, speed=40)
        n.x0, n.x1 = 2 * TILE, (W - 2) * TILE
        n.hours = (22.5 + k * 0.3, 27.5)
        npcs.append(n)
    # story characters (homeless, in the alleys)
    try:
        import story
        for c in story.STORY_NPCS:
            if c.get("map", "Park Street") != getattr(map_def, "NAME", "Park Street"):
                continue
            sx, sy = c["spot"]
            px, py = (sx + 0.5) * TILE, sy * TILE + TILE - 10
            pose = c.get("pose", "sit")
            n = NPC(c["id"], px, py, "homeless", {"sit": "sit", "sleep": "sleep"}.get(pose, "stand"),
                    d=c.get("facing", "down"), seed=zlib.crc32(c["id"].encode()) & 0xFFFF, name=c["name"],
                    lines=c.get("lines"), look_over=c.get("look"))
            n.plot = True
            n.flags = c.get("flags", {})
            if c.get("dog"):
                n.extras.append(("dog", -36, 6, 0))
            day = dict(pose=pose, facing=c.get("facing", "down"), lines=c.get("lines"))
            night = dict(pose=c.get("night_pose", pose), facing=c.get("night_facing", c.get("facing", "down")),
                         lines=c.get("night_lines") or c.get("lines"))
            n.phases = dict(day=day, night=night)
            n.set_phase("day")
            npcs.append(n)
    except Exception as e:                      # a typo in story.py shouldn't stop the game starting
        print("story.py:", e)
    return npcs


WORK = {   # shop kind -> (role at the counter, pose, tool, facing)
    "cafe": ("barista", "work", "cup", "down"), "kebab": ("kebab", "work", "knife", "left"),
    "barber": ("barber", "work", "broom", "down"), "corner": ("shopkeeper", "stand", None, "down"),
    "clothes": ("assistant", "work", "cloth", "down"), "books": ("bookseller", "work", "book", "down"),
    "gym": ("gym", "stand", None, "down"), "club": ("bartender", "work", "cup", "down"),
    "arcade": ("attendant", "stand", None, "down"), "zaza": ("waiter", "stand", None, "down"),
    "hostel": ("receptionist", "stand", None, "down"),
}


OPEN_HOURS = {   # when each kind of shop is open (close > 24 = after midnight)
    "cafe": (7, 20), "kebab": (11, 27), "corner": (0, 24), "clothes": (9, 18), "books": (9, 18.5),
    "barber": (9, 18), "gym": (6, 23), "club": (22, 27), "arcade": (10, 26), "zaza": (12, 23),
}


def is_open(kind, hour):
    a, b = OPEN_HOURS.get(kind, (0, 24))
    if b - a >= 24: return True
    return a <= hour < b if b <= 24 else (hour >= a or hour < b - 24)


def opening_text(kind):
    a, b = OPEN_HOURS.get(kind, (0, 24))
    if b - a >= 24: return "open 24 hours"
    fmt = lambda h: f"{int(h % 24):02d}:{int((h % 1) * 60):02d}"
    return f"open {fmt(a)}-{fmt(b)}"


def zaza_busy(hour):
    """How full Za Za Bazaar is (0-1): a lunchtime rush, a quiet afternoon, packed for dinner."""
    h = hour % 24
    if 12 <= h < 14.5: return 0.85
    if 14.5 <= h < 17.5: return 0.35
    if 17.5 <= h < 21: return 1.0
    return 0.4


def populate_zaza(world, seed, hour):
    """Chefs at every station, bartenders, waiters doing the rounds, a queue at the busiest stations, and diners
    at the tables and in the booths - how many depends on the time."""
    rng = random.Random(seed + int(hour * 4))
    zz = world.zaza
    busy = zaza_busy(hour)
    npcs = []
    pid = lambda tag: f"zaza{seed}_{tag}"
    for k, (x, y, name, col) in enumerate(zz["stations"]):
        foot = (y + 1) * TILE - 2
        c = NPC(pid(f"chef{k}"), (x + 2) * TILE + rng.randrange(-30, 30), foot - 62, "chef", "work", d="down", seed=seed + 50 + k)
        c.anim_speed = rng.uniform(2.5, 4.0)
        npcs.append(c)
        for q in range(int(busy * 3 + rng.random())):                  # people queueing with their plates
            n = NPC(pid(f"q{k}_{q}"), (x + 1 + q) * TILE + 20, foot + 34 + q * 6, "diner", "stand", d="up", seed=seed + 100 + k * 5 + q)
            npcs.append(n)
    if zz["bar"]:
        xs = sorted(x for x, y in zz["bar"]); by = zz["bar"][0][1]
        for k, x in enumerate((xs[2], xs[-3])):
            b = NPC(pid(f"barkeep{k}"), x * TILE + 32, by * TILE - 14, "bartender", "work", d="down", tool="cup", seed=seed + 70 + k)
            b.anim_speed = 2.2
            npcs.append(b)
        for k in range(int(busy * 4)):                                  # waiting at the bar
            x = rng.choice(xs)
            npcs.append(NPC(pid(f"bar{k}"), x * TILE + 32, (by + 1) * TILE + 30, "diner", "stand", d="up", seed=seed + 80 + k))
    for k, (dx, foot) in enumerate(zz["drinks"]):
        if rng.random() < busy:
            npcs.append(NPC(pid(f"drinks{k}"), dx, foot + 30, "diner", "stand", d="up", tool="cup", seed=seed + 90 + k))
    for k, row in enumerate((13.5, 18.5, 8.6)):                         # waiters doing the rounds
        w = NPC(pid(f"waiter{k}"), rng.uniform(4, world.w - 5) * TILE, row * TILE, "waiter", "walk_x",
                d=rng.choice(["left", "right"]), seed=seed + 60 + k, speed=58)
        w.x0, w.x1 = 3 * TILE, (world.w - 4) * TILE
        npcs.append(w)
    tools = ["cup", "phone", None, None, "cup"]
    for k, (cx, foot) in enumerate(zz["tables"]):                      # diners: two behind the table, two in front
        if rng.random() > busy * 1.05:
            continue
        for j, (ox, oy, d) in enumerate(((-22, -56, "down"), (22, -56, "down"), (-22, 4, "up"), (22, 4, "up"))):
            if rng.random() < 0.72:
                n = NPC(pid(f"t{k}_{j}"), cx + ox, foot + oy, "diner", "sit", d=d, tool=rng.choice(tools), seed=seed + 200 + k * 7 + j)
                npcs.append(n)
    for k, (x, y) in enumerate(zz["booths"]):
        if rng.random() > busy * 1.05:
            continue
        foot = (y + 1) * TILE - 2
        for j, (ox, oy, d) in enumerate(((40, -52, "down"), (88, -52, "down"), (64, 6, "up"))):
            if rng.random() < 0.7:
                n = NPC(pid(f"b{k}_{j}"), x * TILE + ox, foot + oy, "diner", "sit", d=d, tool=rng.choice(tools), seed=seed + 400 + k * 7 + j)
                npcs.append(n)
    return npcs


def populate_interior(world, kind, seed, hour=12.0):
    if kind == "zaza":
        return populate_zaza(world, seed, hour)
    rng = random.Random(seed)
    late = hour >= 20 or hour < 6
    npcs = []
    pid = lambda tag: f"{kind}{seed}_{tag}"
    for y in range(world.h):
        for x in range(world.w):
            ch = world.grid[y][x]
            cx, foot = x * TILE + TILE // 2, y * TILE + TILE - 2
            if ch == "p":
                role, pose, tool, d = WORK[kind]
                n = NPC(pid("staff"), cx, foot - 8, role, pose if pose != "stand" else "stand", d=d, tool=tool,
                        seed=seed * 3 + 1)
                n.behaviour = "work" if pose == "work" else "stand"
                n.pose = pose
                n.anim_speed = 1.2 if kind == "books" else (2.0 if kind == "barber" else 3.5)
                npcs.append(n)
            elif ch == "G" and x in (1, 5):                          # barber chairs: a customer + a barber cutting
                c = NPC(pid(f"client{x}"), cx, foot - 18, "client", "sit", d="down", seed=seed + x * 11)
                c.sort_bias = 22                                     # sat in the chair, facing you, cape on
                c.look = dict(c.look, jacket=None, shirt=(236, 236, 240))
                b = NPC(pid(f"barber{x}"), cx + 40, foot + 4, "barber", "work", d="left", tool="scissors", seed=seed + x * 13)
                b.anim_speed = 5.0
                npcs += [c, b]
            elif ch == "J" and rng.random() < (0.6 if kind != "books" else 0.5) * (0.4 if late else 1.0):
                left = rng.random() < 0.5
                n = NPC(pid(f"t{x}_{y}"), cx + (-26 if left else 30), foot - 6, "customer", "sit",
                        d="right" if left else "left", tool="book" if kind == "books" else rng.choice(["cup", "phone", "cup"]),
                        seed=seed + x * 7 + y * 5)
                n.sort_bias = 8
                npcs.append(n)
            elif ch == "U" and x in (1, 3):                           # runners on the treadmills
                n = NPC(pid(f"run{x}"), cx, foot - 14, "runner", "run", d="up", seed=seed + x * 17)
                n.sort_bias = 18
                npcs.append(n)
            elif ch == "N" and x == 2:                                # someone on the bench press
                n = NPC(pid("press"), cx, foot - 14, "lifter", "press", d="down", seed=seed + 99)
                n.sort_bias = 18
                npcs.append(n)
            elif ch == "q" and kind == "barber":
                n = NPC(pid("waiting"), cx - 14, foot - 16, "customer", "sit", d="down", tool="phone", seed=seed + 55)
                n.sort_bias = 6
                npcs.append(n)
    if kind == "club":                                                 # the DJ behind the decks, a packed dance floor
        for y in range(world.h):
            for x in range(world.w):
                if world.grid[y][x] == "@" and world.grid[y][x - 1] != "@":
                    n = NPC(pid("dj"), x * TILE + TILE, y * TILE + 6, "dj", "work", d="down", seed=seed + 31)
                    n.anim_speed = 2.2
                    npcs.append(n)
        floor = [(x, y) for y in range(world.h) for x in range(world.w) if world.grid[y][x] == "d"]
        rng.shuffle(floor)
        for k, (x, y) in enumerate(floor[:9]):
            n = NPC(pid(f"dance{k}"), x * TILE + 32 + rng.randrange(-12, 12), y * TILE + TILE - 10, "dancer", "dance",
                    d=rng.choice(["down", "left", "right", "up"]), seed=seed + 400 + k)
            n.anim_speed = rng.uniform(3.5, 5.5)
            npcs.append(n)
        for k, x in enumerate((8, 10)):
            npcs.append(NPC(pid(f"bar{k}"), x * TILE + 32, 4 * TILE + 52, "dancer", "stand", d="up", seed=seed + 480 + k))
    if kind == "wills":                                                # the entrance hall: a porter, students, visitors
        T = TILE
        porter = NPC(pid("porter"), 15.9 * T, 10 * T + 6, "public", "stand", d="down", seed=seed + 3, name="Porter",
                     lines=[["Hello. Lectures are upstairs - Law on the left, Earth Sciences straight through.",
                             "Professor Usher? His office is just there, top left of the hall."]])
        porter.look = dict(porter.look, jacket=(30, 34, 52), shirt=(236, 236, 240), pants=(30, 34, 52), glasses=True)
        npcs.append(porter)
        for k, (tx, ty, d, tool) in enumerate(((6.4, 8.9, "up", "phone"), (7.2, 8.9, "left", None),
                                                (13.5, 9.2, "up", None), (17.2, 6.4, "left", "book"))):
            n = NPC(pid(f"visitor{k}"), tx * T, ty * T, "public", "stand", d=d, tool=tool, seed=seed + 40 + k)
            n.lines = [["It's even bigger inside, isn't it?"], ["I've got a lecture in five minutes..."],
                       ["Which floor's Earth Sciences?"], ["Shh - I'm revising."]][k]
            npcs.append(n)
        w = NPC(pid("walker"), 9.6 * T, 6 * T, "public", "walk_y", d="down", seed=seed + 77)
        w.y0, w.y1 = 3.4 * T, 11.5 * T
        npcs.append(w)
    if kind == "arcade":                                               # people playing some of the machines
        k = 0                                                          # (only along the back wall on the right of
        for y in range(world.h):                                       #  the hall, x 12-16, so every game always
            for x in range(12, min(17, world.w)):                      #  has a free machine)
                if world.grid[y][x] in "1234" and y == 1 and rng.random() < (0.45 if late else 0.75):
                    n = NPC(pid(f"player{k}"), x * TILE + 32, (y + 1) * TILE + 30, "customer", "stand", d="up", seed=seed + 600 + k)
                    npcs.append(n); k += 1
    if kind == "gym":                                                  # dumbbell curls by the rack
        n = NPC(pid("curl"), 8 * TILE + 32, 2 * TILE + 52, "lifter", "work", d="down", tool="dumbbell", seed=seed + 7)
        n.anim_speed = 1.6
        npcs.append(n)
    # browsing customers
    if late and kind == "kebab":                                       # the after-hours queue at the kebab shop
        for k in range(2):
            x, y = 4 + k * 2, 4
            n = NPC(pid(f"latenight{k}"), x * TILE + 32, y * TILE + TILE - 10, "drunk", "stand", d="up", seed=seed + 700 + k)
            npcs.append(n)
    for k in range({"corner": 2, "clothes": 2, "books": 2, "cafe": 1, "kebab": 1, "barber": 0, "gym": 1, "club": 0, "arcade": 1, "zaza": 0}.get(kind, 0) - (1 if late and kind != "club" else 0)):
        free = world.free_floor
        if not free: break
        x, y = rng.choice(free)
        n = NPC(pid(f"browse{k}"), x * TILE + 32, y * TILE + TILE - 10, "customer", "wander", seed=seed + 300 + k, speed=45)
        npcs.append(n)
    return npcs
