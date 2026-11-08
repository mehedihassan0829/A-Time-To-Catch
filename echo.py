"""Scenes away from the game: the TIME ECHOES (the past, in black and white, like an old pixelated photograph) and the
opening in the detective's flat (in colour, at night).

Each scene is a real place in the game (the harbourside, Usher's office, the café...) built fresh - as it was, without
the police tape - with the people from the flashback standing in it. Edit SCENES to move people about.
"""
import math
import random
import pygame
import people
import daynight

TILE = 64

# ------------------------------------------------------------------ how the people in the flashbacks look
LOOKS = dict(people.SUSPECTS)       # the suspects and John always look the same (people.SUSPECTS)
LOOKS["shadow"] = dict(people.SUSPECTS["john"], skin=(30, 30, 30), hair=(20, 20, 20), style="hood", hat=(20, 20, 20),
                       shirt=(20, 20, 20), jacket=(20, 20, 20), pants=(20, 20, 20))
LOOKS["worker"] = dict(people.SUSPECTS["usher_young"], skin=(224, 172, 120), hair=(30, 26, 24), glasses=False)
LOOKS["worker2"] = dict(people.SUSPECTS["usher_young"], skin=(198, 134, 88), hair=(196, 150, 84), style="ponytail",
                        glasses=False)

# ------------------------------------------------------------------ the scenes
# world: ("place", name) a map as it was (no police tape)  /  ("room", kind) a room  /  ("cafe",) the café Emily goes to
# people: name -> (look, x, y, facing[, pose])  in tiles; the name is who speaks (John, Usher, Emily, Jack...)
SCENES = {
    "home": dict(world=("room", "home"), centre=(6.0, 4.4), colour=True,
                 people={"detective": ("player", 4.5, 2.9, "down")}),
    "harbour_john": dict(world=("place", "Harbourside"), centre=(47.5, 50.5),
                         people={"john": ("john", 48.5, 51.6, "right"), "shadow": ("shadow", 36.6, 51.6, "right")}),
    "usher_office": dict(world=("room", "usher"), centre=(6.0, 4.8),
                         people={"john": ("john", 4.9, 6.0, "up"), "usher": ("usher_old", 4.4, 3.75, "down")}),
    "cafe_emily": dict(world=("cafe",), centre=(4.0, 5.0),
                       people={"john": ("john", 2.09, 5.88, "right", "sit"), "emily": ("emily", 2.97, 5.88, "left", "sit")}),
    "arcade_1999": dict(world=("place", "Harbourside"), centre=(29.5, 45.0),
                        people={"jack": ("jack", 28.7, 46.75, "right"), "usher": ("usher_young", 30.3, 46.75, "left")}),
    "harbour_push": dict(world=("place", "Harbourside"), centre=(47.0, 43.0),
                         people={"jack": ("jack", 49.3, 43.6, "right"), "usher": ("usher_young", 43.6, 43.6, "right")}),
    "harbour_view": dict(world=("place", "Harbourside"), centre=(46.5, 47.0), people={}),
    "photo1999": dict(world=("place", "Harbourside"), centre=(29.5, 45.3),
                      people={"w1": ("worker", 28.2, 46.4, "down"), "w2": ("jack", 28.9, 46.5, "down"),
                              "w3": ("usher_young", 29.6, 46.4, "down"), "w4": ("worker2", 30.4, 46.5, "down")}),
    "ju_photo": dict(world=("place", "Harbourside"), centre=(29.5, 46.0),
                     people={"jack": ("jack", 29.0, 46.8, "down"), "usher": ("usher_young", 29.95, 46.8, "down")}),
}


class SceneActor(people.NPC):
    """Someone in a flashback. Walks where the script says, nothing else."""

    def __init__(self, name, look, x, y, d, pose=None):
        super().__init__(f"echo_{name}", x, y, "public", "script", d=d)
        self.look = look
        self.frames = {}
        if pose == "sit":
            self.pose = "sit"; self.behaviour = "sit"; self.sort_bias = 8
        self.target = None
        self.speed = 75.0
        self.silhouette = name == "shadow"
        if self.silhouette:
            self.speed = 120.0
        self.sil_cache = {}

    def image(self):
        img = super().image()
        if not self.silhouette:
            return img
        got = self.sil_cache.get(id(img))
        if got is None:
            m = pygame.mask.from_surface(img, 40)
            got = self.sil_cache[id(img)] = m.to_surface(setcolor=(8, 8, 10, 235), unsetcolor=(0, 0, 0, 0))
        return got

    def step(self, dt):
        self.moving = False
        self.t += dt
        if self.target is None:
            return False
        tx, ty = self.target
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 2:
            self.x, self.y = tx, ty
            self.target = None
            return False
        k = min(1.0, self.speed * dt / dist)
        self.x += dx * k; self.y += dy * k
        self.moving = True
        if abs(dx) > abs(dy):
            self.d = "right" if dx > 0 else "left"
        else:
            self.d = "down" if dy > 0 else "up"
        return True


class DetectiveActor:
    """The detective himself in a scene (drawn with the player's own sprite)."""

    def __init__(self, player, x, y, d):
        self.player, self.x, self.y, self.d = player, x, y, d
        self.shown, self.extras, self.sort_bias, self.id = True, [], 0, "echo_detective"
        self.target, self.speed, self.t, self.moving, self.talking = None, 90.0, 0.0, False, False

    def image(self):
        f = int(self.t * 8) % 4 if self.moving else 0
        return self.player.frames[(self.d, f)]

    def update(self, *a):
        pass

    step = SceneActor.step


class Scene:
    def __init__(self, sid, make_world, render, player, cafe_seed=0):
        spec = SCENES[sid]
        self.sid = sid
        self.colour = spec.get("colour", False)
        kind = spec["world"]
        self.world = make_world(kind, cafe_seed)
        self.world.actors = []
        for attr in ("traffic", "vtraffic", "deck"):
            if hasattr(self.world, attr):
                setattr(self.world, attr, None)
        self.render = render
        self.centre = (spec["centre"][0] * TILE, spec["centre"][1] * TILE)
        self.actors = {}
        for name, (look, x, y, d, *pose) in spec["people"].items():
            if look == "player":
                a = DetectiveActor(player, x * TILE, y * TILE, d)
            else:
                a = SceneActor(name, LOOKS[look], x * TILE, y * TILE, d, pose[0] if pose else None)
            self.actors[name] = a
            self.world.actors.append(a)
        self.t = 0.0
        self.flash = 0.7                  # comes in from white
        self.glitch = 0.0
        self.splash = None                # (x, y, time) - someone's gone into the water
        self.fallen = None
        self.ring = False
        self.flame = False
        self.rng = random.Random(4)
        self.buf = None
        self.grain = None
        self.vignette = None
        self.lighting = daynight.Lighting() if self.colour else None
        self.offset = (0, 0)
        self.flames = [daynight.flame(i) for i in range(4)] if self.colour else None

    # ---- the script moves people about
    def move(self, name, to):
        a = self.actors.get(name)
        if a is not None:
            a.target = (to[0] * TILE, to[1] * TILE)

    def push(self):
        """The push: the one pushed stumbles forward over the edge and is gone; the pusher stays put."""
        a = self.actors.get("jack")
        if a is not None:
            a.target = (a.x + 1.05 * TILE, a.y + 6)      # just over the edge of the deck
            a.speed = 190.0
            self.fallen = a

    def settle(self):
        """Clicked on before people got there: put everyone where they were going."""
        for a in self.actors.values():
            if a.target is not None:
                a.x, a.y = a.target; a.target = None
        if self.fallen is not None and self.fallen.shown:
            self.fallen.shown = False
            self.splash = (self.fallen.x, self.fallen.y, 0.0)

    @property
    def walking(self):
        return any(a.target is not None for a in self.actors.values())

    def update(self, dt):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.glitch = max(0.0, self.glitch - dt)
        self.world.time += dt
        for a in self.actors.values():
            a.step(dt)
        if self.fallen is not None and self.fallen.shown and self.fallen.target is None:
            self.fallen.shown = False                         # into the water
            self.splash = (self.fallen.x, self.fallen.y, 0.0)
        if self.splash:
            x, y, st = self.splash
            self.splash = (x, y, st + dt)

    # ---- drawing
    def _surfaces(self, size):
        if self.buf is None or self.buf.get_size() != size:
            self.buf = pygame.Surface(size).convert()
            w, h = size
            self.grain = []
            for k in range(3):
                g = pygame.Surface((w // 2, h // 2), pygame.SRCALPHA)
                rng = random.Random(k)
                for _ in range(w * h // 60):
                    v = rng.randrange(0, 255)
                    g.set_at((rng.randrange(w // 2), rng.randrange(h // 2)), (v, v, v, 34))
                self.grain.append(pygame.transform.scale(g, size))
            self.vignette = pygame.Surface(size, pygame.SRCALPHA)
            for i in range(24):
                a = int(150 * (1 - i / 24) ** 2)
                pygame.draw.rect(self.vignette, (0, 0, 0, a), (i * 8, i * 6, w - i * 16, h - i * 12), 8)

    def draw(self, screen):
        size = screen.get_size()
        self._surfaces(size)
        ox, oy = self.offset = self.render(self.buf, self.world, self.centre)
        if self.splash:                                        # rings on the water
            x, y, st = self.splash
            for k in range(3):
                r = (st * 60 + k * 14) % 60 + 6
                if st < 2.5:
                    pygame.draw.ellipse(self.buf, (236, 240, 246), (x + ox - r, y + oy - r * 0.45, r * 2, r * 0.9), 2)
        if self.colour:
            self._draw_colour(screen, ox, oy)
            return
        w, h = size
        small = pygame.transform.scale(self.buf, (w // 2, h // 2))
        small = pygame.transform.grayscale(small)
        screen.blit(pygame.transform.scale(small, size), (0, 0))
        screen.blit(self.grain[int(self.t * 12) % 3], (0, 0))
        screen.blit(self.vignette, (0, 0))
        if self.glitch > 0:
            self._draw_glitch(screen)
        if self.flash > 0:
            white = pygame.Surface(size); white.fill((255, 255, 255)); white.set_alpha(int(255 * min(1, self.flash / 0.7)))
            screen.blit(white, (0, 0))

    def _draw_glitch(self, screen):
        glitch(screen, self.rng)


    def _draw_colour(self, screen, ox, oy):
        """The opening scene: the flat at night, lamplight, the lighter, the phone."""
        d = self.actors["detective"]
        screen.blit(self.buf, (0, 0))
        lights = [(1.5 * TILE, 5.2 * TILE, 260, (255, 200, 130), 0.9)]           # the floor lamp
        if self.flame:
            fl = self.flames[int(self.t * 11) % 4]
            hx = {"left": -22, "right": 22, "up": 16, "down": 18}[d.d]
            screen.blit(fl, (d.x + hx - fl.get_width() // 2 + ox, d.y - 46 + oy))
            lights.append((d.x + hx, d.y - 40, 150, (255, 170, 80), 0.9))
        self.lighting.apply(screen, (64, 64, 100), lights, ox, oy)
        if self.ring:                                                          # the phone, ringing
            px, py = 6.5 * TILE + ox, 3.0 * TILE + oy
            if int(self.t * 6) % 2 == 0:
                f = pygame.font.SysFont("consolas,menlo,monospace", 22, bold=True)
                t = f.render("RING!", True, (255, 236, 160))
                screen.blit(t, (px - t.get_width() // 2 + self.rng.randrange(-3, 4), py - 40))
                for k in (-1, 1):
                    pygame.draw.line(screen, (255, 236, 160), (px + k * 26, py + 6), (px + k * 40, py - 4), 3)


def glitch(screen, rng):
    """The picture breaking up: torn slices, static, the odd flash of negative."""
    w, h = screen.get_size()
    snap = screen.copy()
    for _ in range(14):                                    # torn slices
        y = rng.randrange(0, h); hh = rng.randrange(4, 40); dx = rng.randrange(-80, 80)
        screen.blit(snap, (dx, y), (0, y, w, hh))
    for _ in range(6):                                     # static bars
        y = rng.randrange(0, h); v = rng.randrange(0, 255)
        screen.fill((v, v, v), (0, y, w, rng.randrange(2, 8)))
    if rng.random() < 0.3:
        inv = pygame.Surface((w, h)); inv.fill((255, 255, 255))
        screen.blit(inv, (0, 0), special_flags=pygame.BLEND_RGB_SUB)


def snapshot(sid, make_world, render, player, size, sepia=True):
    """A still of a scene, as an old photograph (for the photographs you find)."""
    sc = Scene(sid, make_world, render, player)
    buf = pygame.Surface(size).convert()
    render(buf, sc.world, sc.centre)
    w, h = size
    small = pygame.transform.grayscale(pygame.transform.scale(buf, (w // 2, h // 2)))
    out = pygame.transform.scale(small, size)
    if sepia:
        tint = pygame.Surface(size); tint.fill((255, 226, 180))
        out.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    return out
