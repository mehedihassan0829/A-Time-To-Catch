"""Day and night: the game clock, the lighting (darkness + every light in the street), and your watch.

One game hour passes every 30 real seconds (a whole day is 12 minutes). Hold T to make time fly.
"""
import json, math, random
from pathlib import Path
import pygame
import pixel_art as pa
from pixel_art import canvas, R, P, shade, up, circle

REAL_SECONDS_PER_HOUR = 30.0
FAST_FORWARD = 40.0                      # how much faster time goes while you hold T
START_HOUR = 17.5                        # a new game starts at half five in the evening

# (hour, ambient light colour) - the light level through the day; colours in between are blended
AMBIENT = [(0.0, (46, 54, 98)), (4.5, (46, 54, 98)), (6.0, (150, 120, 140)), (7.5, (255, 236, 220)), (9.0, (255, 255, 255)),
           (17.0, (255, 255, 255)), (18.6, (255, 206, 160)), (19.6, (170, 120, 140)), (20.8, (70, 74, 120)),
           (22.0, (46, 54, 98)), (24.0, (46, 54, 98))]


class GameClock:
    def __init__(self, save_dir):
        self.path = Path(save_dir) / "clock.json"
        self.hours = START_HOUR                      # hours since the game started (keeps counting past 24)
        try:
            self.hours = float(json.loads(self.path.read_text())["hours"])
        except (OSError, ValueError, KeyError):
            pass
        self.fast = False

    @property
    def hour(self):
        return self.hours % 24.0

    @property
    def day(self):
        return int(self.hours // 24) + 1

    def update(self, dt):
        self.hours += dt / REAL_SECONDS_PER_HOUR * (FAST_FORWARD if self.fast else 1.0)

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"hours": self.hours}))
        except OSError:
            pass

    def text(self):
        h = self.hour
        return f"{int(h):02d}:{int((h % 1) * 60):02d}"

    def ambient(self):
        h = self.hour
        for (h0, c0), (h1, c1) in zip(AMBIENT, AMBIENT[1:]):
            if h0 <= h <= h1:
                t = (h - h0) / (h1 - h0) if h1 > h0 else 0
                return tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))
        return (255, 255, 255)

    def darkness(self):
        """0 in full daylight, 1 in the middle of the night."""
        a = self.ambient()
        return max(0.0, min(1.0, (255 - sum(a) / 3) / (255 - 66)))

    def is_night(self):
        h = self.hour
        return h >= 20.5 or h < 5.5

    def lamps_on(self):
        h = self.hour
        return h >= 18.8 or h < 6.8


# ------------------------------------------------------------------ lights
_LIGHT_CACHE = {}


def light_sprite(radius, colour, strength):
    """A soft pool of light, stepped like pixel art. Added on to the light map."""
    key = (radius, colour, round(strength, 1))
    img = _LIGHT_CACHE.get(key)
    if img is not None:
        return img
    lr = max(2, radius // pa.PX)
    s = pygame.Surface((lr * 2, lr * 2))
    s.fill((0, 0, 0))
    for y in range(lr * 2):
        for x in range(lr * 2):
            d = math.hypot(x + 0.5 - lr, y + 0.5 - lr) / lr
            if d < 1:
                v = (1 - d) ** 1.5
                v = round(v * 6) / 6                                  # banded, like pixel-art lighting
                s.set_at((x, y), tuple(max(0, min(255, int(c * v * strength))) for c in colour))
    img = pygame.transform.scale(s, (lr * 2 * pa.PX, lr * 2 * pa.PX))
    _LIGHT_CACHE[key] = img
    return img


class Lighting:
    """Darkens the screen by the time of day, then lets every light shine through."""
    def __init__(self):
        self.map = None

    def apply(self, screen, ambient, lights, ox, oy):
        if ambient == (255, 255, 255) and not lights:
            return
        size = screen.get_size()
        if self.map is None or self.map.get_size() != size:
            self.map = pygame.Surface(size).convert()
        self.map.fill(ambient)
        w, h = size
        for (x, y, radius, colour, strength) in lights:
            sx, sy = x + ox, y + oy
            if -radius < sx < w + radius and -radius < sy < h + radius:
                img = light_sprite(int(radius), colour, strength)
                self.map.blit(img, (sx - img.get_width() // 2, sy - img.get_height() // 2), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(self.map, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


# ------------------------------------------------------------------ watch + lighter art
def watch_face(hour):
    """Your wristwatch: a little analogue face with the time underneath. Returns screen-size art."""
    s = canvas(26, 22)
    strap, strap_d = (70, 46, 34), (50, 32, 24)
    R(s, strap, 0, 6, 26, 8); R(s, strap_d, 0, 13, 26, 1)
    for x in (2, 5, 20, 23): P(s, strap_d, x, 9)
    circle(s, (150, 120, 60), 13, 10, 9)                              # brass case
    circle(s, (236, 230, 210), 13, 10, 8)
    for i in range(12):                                               # hour marks
        a = i / 12 * math.tau
        P(s, (60, 56, 60), 13 + round(math.sin(a) * 7), 10 - round(math.cos(a) * 7))
    hr = (hour % 12) / 12 * math.tau
    mn = (hour % 1) * math.tau
    for ang, ln, col in ((hr, 4, (30, 30, 34)), (mn, 6, (60, 60, 70))):
        for k in range(1, ln + 1):
            P(s, col, 13 + round(math.sin(ang) * k), 10 - round(math.cos(ang) * k))
    P(s, (200, 60, 50), 13, 10)
    night = hour >= 20 or hour < 6
    P(s, (90, 110, 200) if night else (240, 190, 60), 13, 5)          # little moon / sun dot
    return up(pa.add_outline(s)).convert_alpha()


def lighter_icon():
    s = canvas(8, 14)
    R(s, (200, 40, 50), 1, 5, 6, 9); R(s, (230, 80, 80), 1, 5, 1, 9)
    R(s, (180, 184, 192), 1, 2, 6, 3); R(s, (120, 124, 132), 5, 1, 2, 2)
    return up(pa.add_outline(s)).convert_alpha()


def watch_icon():
    s = canvas(12, 14)
    R(s, (70, 46, 34), 4, 0, 4, 14)
    circle(s, (150, 120, 60), 6, 7, 4); circle(s, (236, 230, 210), 6, 7, 3)
    P(s, (30, 30, 34), 6, 6); P(s, (30, 30, 34), 6, 5); P(s, (30, 30, 34), 7, 7)
    return up(pa.add_outline(s)).convert_alpha()


def flame(frame=0):
    s = canvas(6, 9)
    sway = (0, 1, 0, -1)[frame % 4]
    R(s, (200, 40, 50), 1, 6, 4, 3)                                   # the lighter in your hand
    R(s, (255, 150, 40), 2 + sway, 2, 2, 4)
    P(s, (255, 230, 120), 2 + sway, 3); P(s, (255, 230, 120), 2 + sway, 4)
    P(s, (255, 120, 30), 2 + sway, 1)
    return up(s).convert_alpha()
