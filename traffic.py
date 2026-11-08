"""Traffic: pelican-crossing lights that change, cars that drive both ways, queue, stop at red lights and
for you, and a double-decker bus waiting at the College Green stop."""
import random
import pygame
import pixel_art as pa

TILE = 64
CYCLE = (("green", 8.0), ("amber", 2.5), ("red", 6.0), ("redamber", 1.2))
CAR_COLOURS = [(200, 52, 52), (40, 90, 170), (240, 240, 236), (50, 52, 58), (60, 140, 90), (230, 180, 50),
               (150, 156, 166), (120, 70, 150), (240, 130, 60), (20, 40, 80), (110, 30, 30), (200, 200, 190)]
VMAX = 210.0
ACCEL, BRAKE = 170.0, 520.0


class Crossing:
    def __init__(self, x_tile, offset):
        self.x0, self.x1 = x_tile * TILE, (x_tile + 1) * TILE
        self.t = offset

    @property
    def state(self):
        t = self.t % sum(d for _, d in CYCLE)
        for name, d in CYCLE:
            if t < d: return name
            t -= d
        return "green"


class Car:
    def __init__(self, lane, x, colour):
        self.lane = lane                     # +1 = eastbound (north lane), -1 = westbound (south lane)
        self.x = x                           # centre
        self.v = VMAX * random.uniform(0.6, 1.0)
        self.colour = colour
        self.vmax = VMAX * random.uniform(0.85, 1.1)

    def front(self, length):
        return self.x + self.lane * length / 2


class Traffic:
    def __init__(self, world, side=None):
        self.world = world
        self.side = side                  # a road that ends at a junction (the harbourside): dict(rows, end)
        self.vt = None
        if side:
            rows = list(range(side["rows"][0], side["rows"][1] + 1))
        else:
            rows = [y for y in range(world.h) if sum(1 for x in range(world.w) if world.grid[y][x] in "=zv") > world.w * 0.6]
        self.ok = len(rows) >= 4
        if not self.ok:
            return
        top, bottom = min(rows), max(rows)
        self.lane_y = {1: (top + 1) * TILE + 54, -1: (bottom - 1) * TILE + 54}      # feet of the car sprites
        cols = sorted({x for y in rows for x in range(world.w) if world.grid[y][x] == "z"})
        self.crossings = [Crossing(x, i * 5.3) for i, x in enumerate(cols)]
        self.signals = list(world.signal_spots)       # (cx, foot, tile x)
        self.sig_img = {}
        self.car_img = {}
        self.length = pa.car(CAR_COLOURS[0], True).get_width() - 8
        self.cars = []
        rng = random.Random(7)
        far = side["end"] * TILE - self.length * 2 if side else world.pixel_w - 100
        for lane in (1, -1):
            x = rng.uniform(0, 300)
            while x < far:
                self.cars.append(Car(lane, x, rng.choice(CAR_COLOURS)))
                x += rng.uniform(420, 900) * (3.5 if (world.hour >= 23 or world.hour < 6) else 1.0)
        self.spawn_timer = {1: 0.0, -1: 0.0}
        self.rng = rng
        self.bus = None
        for y in range(world.h):
            for x in range(world.w):
                if world.grid[y][x] == "u":
                    self.bus = dict(x=(x + 0.5) * TILE - 24, y=(bottom + 1) * TILE - 6)
        self.bus_imgs = [pa.bus(i) for i in range(2)] if self.bus else []
        self.t = 0.0

    # ---- a junction with lights where this road meets a road running up/down the screen (the harbourside)
    JUNCTION = (("main", 9.0), ("main_amber", 2.0), ("all_red", 2.0), ("side", 7.0), ("side_amber", 1.5), ("all_red", 2.0))

    def join(self, vt):
        """Link this road to the one it meets: eastbound cars turn left (up the screen) onto it when their light
        is green, and some of the cars coming up it turn left (west) onto this road."""
        self.vt = vt
        self.up_lane = next(i for i, (x, d) in enumerate(vt.lanes) if d < 0)
        self.up_x = vt.lanes[self.up_lane][0]
        self.jt = 0.0
        y0, y1 = self.side["rows"]
        vt.hold_lines = {i: (y0 * TILE - 6 if d > 0 else (y1 + 1) * TILE + 6) for i, (x, d) in enumerate(vt.lanes)}
        vt.light = lambda: self.junction_state()

    def junction_state(self):
        t = self.jt % sum(d for _, d in self.JUNCTION)
        for name, d in self.JUNCTION:
            if t < d: return name
            t -= d
        return "main"

    def junction_light(self, who):
        """The colour of a junction light: who = 'main' (the road up/down the screen) or 'side' (this road)."""
        st = self.junction_state()
        if st == who: return "green"
        if st == who + "_amber": return "amber"
        if st == "all_red" and self.jt % sum(d for _, d in self.JUNCTION) > 18 and who == "main":
            return "redamber"
        return "red"

    def _slot_free(self):
        """Room in the up lane for a car turning into it (nothing in the way just above or below)."""
        vt, ly = self.vt, self.lane_y[1]
        new_y = ly + 10
        for c in vt.cars:
            if c.lane == self.up_lane and new_y - vt.length - 40 < c.y < new_y + vt.length + 40:
                return False
        return True

    def _junction(self, dt):
        vt = self.vt
        self.jt += dt
        ly_e, ly_w = self.lane_y[1], self.lane_y[-1]
        for car in [c for c in self.cars if c.lane == 1 and c.x >= self.up_x]:     # turned left onto the main road
            self.cars.remove(car)
            vc = VCar(self.up_lane, ly_e + 10, car.colour, VMAX * 0.85)
            vc.v = car.v * 0.7; vc.turn = False
            vt.cars.append(vc)
        for vc in [c for c in vt.cars if c.lane == self.up_lane]:                  # coming up from the south
            if getattr(vc, "turn", None) is None:
                vc.turn = self.rng.random() < 0.45
            if vc.turn and vc.y - vt.length / 2 <= ly_w - 20:
                if all(c.x < self.up_x - self.length * 2 for c in self.cars if c.lane == -1):
                    vt.cars.remove(vc)
                    car = Car(-1, self.up_x, vc.colour); car.v = vc.v * 0.7
                    self.cars.append(car)
                else:
                    vc.turn = False                                                # no room: carry straight on

    def signal_state(self, cx, foot, tx):
        """What a traffic light shows: a junction light (side road / main road) or a pelican crossing's."""
        if self.vt is not None and tx >= self.side["end"] - 1:
            on_side = tx < self.side["end"] and foot < self.side["rows"][0] * TILE
            return self.junction_light("side" if on_side else "main")
        return self.light_for(tx)

    def light_for(self, x_tile):
        best = min(self.crossings, key=lambda c: abs(c.x0 - x_tile * TILE)) if self.crossings else None
        return best.state if best else "green"

    def update(self, dt, player_rect, hour=12.0):
        if not self.ok: return
        self.hour = hour
        self.t += dt
        for c in self.crossings: c.t += dt
        L = self.length
        W = self.world.pixel_w
        for lane in (1, -1):
            cars = sorted((c for c in self.cars if c.lane == lane), key=lambda c: c.x * lane, reverse=True)
            ly = self.lane_y[lane]
            band = pygame.Rect(0, ly - 54, W, 64)
            for i, car in enumerate(cars):
                front = car.front(L)
                limit = 1e9
                if i > 0:                                         # the car in front
                    ahead = cars[i - 1]
                    limit = min(limit, abs(ahead.x - car.x) - L - 30)
                for cr in self.crossings:                         # red / amber lights
                    line = cr.x0 - 8 if lane == 1 else cr.x1 + 8
                    dist = (line - front) * lane
                    st = cr.state
                    if dist >= -2 and (st in ("red", "redamber") or (st == "amber" and dist > car.v * car.v / (2 * BRAKE) + 6)):
                        limit = min(limit, dist)
                if self.vt is not None and lane == 1:              # the lights at the junction
                    line = self.side["end"] * TILE - 6
                    dist = line - front
                    light = self.junction_light("side")
                    stop = light == "red" or (light == "amber" and dist > car.v * car.v / (2 * BRAKE) + 6) or not self._slot_free()
                    if dist >= -4 and stop:
                        limit = min(limit, max(0.0, dist))
                if player_rect.colliderect(band):                # don't run anyone over
                    dist = ((player_rect.left if lane == 1 else player_rect.right) - front) * lane - 26
                    if dist > -L:
                        limit = min(limit, max(0, dist))
                allowed = (2 * BRAKE * max(0.0, limit)) ** 0.5
                target = min(car.vmax, allowed)
                car.v = min(target, car.v + ACCEL * dt) if car.v < target else max(target, car.v - BRAKE * dt)
                car.x += car.v * lane * dt
            # leave at one end, come back at the other
            if self.vt is not None and lane == -1:
                for car in list(cars):
                    if car.x + L < -60:
                        self.cars.remove(car)
                continue                                          # westbound cars only come round the corner
            for car in list(cars):
                if (lane == 1 and car.x - L > W + 60) or (lane == -1 and car.x + L < -60):
                    self.cars.remove(car)
            self.spawn_timer[lane] -= dt
            if self.spawn_timer[lane] <= 0:
                entry = -L if lane == 1 else W + L
                if sum(1 for c in self.cars if c.lane == lane) < 16 and all(abs(c.x - entry) > L * 2.5 for c in self.cars if c.lane == lane):
                    self.cars.append(Car(lane, entry, self.rng.choice(CAR_COLOURS)))
                quiet = hour >= 23 or hour < 6                    # far fewer cars late at night
                self.spawn_timer[lane] = self.rng.uniform(7.0, 16.0) if quiet else self.rng.uniform(1.5, 5.0)
                if self.side:                                      # a quieter road that ends at a junction
                    self.spawn_timer[lane] *= 2.6
        if self.vt is not None:
            self._junction(dt)

    def lights(self, dark):
        """Headlights, tail lights, the lit-up bus and the traffic lights, once it gets dark."""
        if not self.ok or dark < 0.15: return []
        out, L = [], self.length
        for car in self.cars:
            ly = self.lane_y[car.lane]
            out.append((car.x + car.lane * (L / 2 + 50), ly - 22, 110, (255, 244, 210), 0.85 * dark))
            out.append((car.x - car.lane * L / 2, ly - 26, 34, (255, 40, 30), 0.8 * dark))
        if self.bus:
            out.append((self.bus["x"], self.bus["y"] - 90, 210, (255, 236, 190), 0.6 * dark))
        col = {"green": (60, 255, 120), "amber": (255, 180, 40), "red": (255, 50, 40), "redamber": (255, 120, 40)}
        for cx, foot, tx in self.signals:
            out.append((cx, foot - 92, 40, col[self.signal_state(cx, foot, tx)], 0.9 * dark))
        return out

    def solids(self):
        if not self.ok: return []
        out = []
        for car in self.cars:
            r = pygame.Rect(0, 0, self.length - 10, 34); r.midbottom = (int(car.x), int(self.lane_y[car.lane] - 2)); out.append(r)
        if self.bus:
            w = self.bus_imgs[0].get_width()
            out.append(pygame.Rect(int(self.bus["x"] - w / 2 + 8), int(self.bus["y"] - 44), w - 16, 42))
        return out

    def sprites(self, view):
        """(image, pos, sort_y) for everything that moves."""
        if not self.ok: return
        for car in self.cars:
            key = (car.colour, car.lane == 1)
            img = self.car_img.get(key)
            if img is None:
                img = self.car_img[key] = pa.car(car.colour, facing_right=car.lane == 1)
            foot = self.lane_y[car.lane]
            pos = (car.x - img.get_width() / 2, foot - img.get_height())
            if view.colliderect(pygame.Rect(pos, img.get_size())):
                yield img, pos, foot
        for cx, foot, tx in self.signals:
            st = self.signal_state(cx, foot, tx)
            img = self.sig_img.get(st)
            if img is None:
                img = self.sig_img[st] = pa.traffic_signal(st)
            yield img, (cx - img.get_width() / 2, foot - img.get_height()), foot
        if self.bus:
            img = self.bus_imgs[int(self.t * 3) % 2]                # engine ticking over
            yield img, (self.bus["x"] - img.get_width() / 2, self.bus["y"] - img.get_height()), self.bus["y"]


# ------------------------------------------------------------------ the road under the bridge (Frogmore Street)
class VCar:
    def __init__(self, lane_i, y, colour, vmax):
        self.lane, self.y, self.colour = lane_i, y, colour
        self.v = vmax * random.uniform(0.6, 1.0)
        self.vmax = vmax


class VerticalTraffic:
    """Cars driving up and down the screen (seen from above). On Park Street they're down in the cutting,
    so they're drawn darker and only where you can see over the parapet (clips); on Frogmore Street they're
    right next to you and they stop if you step out in front of them."""
    def __init__(self, world, cfg):
        self.world = world
        self.lanes = [(x * TILE, d) for x, d in cfg["lanes"]]          # (centre x px, +1 down / -1 up)
        self.y0, self.y1 = cfg["y0"] * TILE, cfg["y1"] * TILE
        self.clips = [pygame.Rect(x0 * TILE, y0 * TILE, (x1 - x0) * TILE, (y1 - y0) * TILE) for x0, y0, x1, y1 in cfg.get("clips", [])]
        self.tint = cfg.get("tint", 1.0)
        self.solid = cfg.get("solid", True)
        self.img = {}
        self.length = pa.car_vertical(CAR_COLOURS[0]).get_height() - 16
        self.cars = []
        self.rng = random.Random(cfg.get("seed", 3))
        for i, (x, d) in enumerate(self.lanes):
            y = self.y0 + self.rng.uniform(0, 300)
            while y < self.y1:
                self.cars.append(VCar(i, y, self.rng.choice(CAR_COLOURS), VMAX * 0.85))
                y += self.rng.uniform(380, 800)
        self.timer = [0.0 for _ in self.lanes]
        self.light = None                     # set when this road has a junction with lights (Traffic.join)
        self.hold_lines = {}

    def _image(self, colour, down):
        key = (colour, down)
        img = self.img.get(key)
        if img is None:
            img = pa.car_vertical(colour, down)
            if self.tint < 1:
                img = img.copy()
                k = int(255 * self.tint)
                img.fill((k, k, min(255, int(k * 1.08)), 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.img[key] = img
        return img

    def update(self, dt, player_rect, hour=12.0):
        L = self.length
        for i, (lx, d) in enumerate(self.lanes):
            cars = sorted((c for c in self.cars if c.lane == i), key=lambda c: c.y * d, reverse=True)
            band = pygame.Rect(lx - 46, 0, 92, self.world.pixel_h)
            for k, car in enumerate(cars):
                limit = 1e9
                if k > 0:
                    limit = abs(cars[k - 1].y - car.y) - L - 30
                if self.light is not None:                          # traffic lights at a junction
                    st = self.light()
                    front = car.y if d > 0 else car.y - L
                    line = self.hold_lines[i]
                    dist = (line - front) * d
                    if dist >= -4 and (st in ("all_red", "side", "side_amber") or
                                       (st == "main_amber" and dist > car.v * car.v / (2 * BRAKE) + 6)):
                        limit = min(limit, max(0.0, dist))
                if self.solid and player_rect.colliderect(band):
                    front = car.y if d > 0 else car.y - L
                    dist = ((player_rect.top - front) if d > 0 else (front - player_rect.bottom)) - 24
                    if dist > -L:
                        limit = min(limit, max(0.0, dist))
                allowed = (2 * BRAKE * max(0.0, limit)) ** 0.5
                target = min(car.vmax, allowed)
                car.v = min(target, car.v + ACCEL * dt) if car.v < target else max(target, car.v - BRAKE * dt)
                car.y += car.v * d * dt
            for car in list(cars):
                if (d > 0 and car.y - L > self.y1 + 40) or (d < 0 and car.y < self.y0 - 40):
                    self.cars.remove(car)
            self.timer[i] -= dt
            if self.timer[i] <= 0:
                entry = self.y0 - 10 if d > 0 else self.y1 + L
                if sum(1 for c in self.cars if c.lane == i) < 10 and all(abs(c.y - entry) > L * 2.4 for c in self.cars if c.lane == i):
                    self.cars.append(VCar(i, entry, self.rng.choice(CAR_COLOURS), VMAX * 0.85))
                quiet = hour >= 23 or hour < 6
                self.timer[i] = self.rng.uniform(6, 14) if quiet else self.rng.uniform(1.5, 4.5)

    def solids(self):
        if not self.solid: return []
        out = []
        for car in self.cars:
            lx, d = self.lanes[car.lane]
            out.append(pygame.Rect(int(lx - 34), int(car.y - self.length + 8), 68, self.length - 4))
        return out

    def sprites(self, view):
        for car in self.cars:
            lx, d = self.lanes[car.lane]
            img = self._image(car.colour, d > 0)
            pos = (int(lx - img.get_width() / 2), int(car.y - img.get_height() + 8))
            r = pygame.Rect(pos, img.get_size())
            if not r.colliderect(view): continue
            if not self.clips:
                yield img, pos, car.y
                continue
            for c in self.clips:                                        # only the bits you can see over the parapet
                part = r.clip(c)
                if part.w > 0 and part.h > 0:
                    yield img.subsurface(part.move(-r.x, -r.y)), part.topleft, min(car.y, c.bottom - 4)

    def lights(self, dark):
        if dark < 0.15: return []
        out = []
        for car in self.cars:
            lx, d = self.lanes[car.lane]
            vis = not self.clips or any(c.collidepoint(lx, car.y - 40) for c in self.clips)
            if not vis: continue
            head = car.y + 40 if d > 0 else car.y - self.length - 40
            tail = car.y - self.length if d > 0 else car.y
            out.append((lx, head, 100, (255, 244, 210), 0.8 * dark * (self.tint + 0.3)))
            out.append((lx, tail, 30, (255, 40, 30), 0.7 * dark))
        return out


class DeckTraffic:
    """Park Street traffic crossing the bridge, seen from Frogmore Street below (drawn on top of the deck)."""
    def __init__(self, world, cfg):
        self.world = world
        self.lanes = [(y * TILE - cfg["lift"], d) for y, d in cfg["lanes"]]
        self.sort = cfg["sort"]
        self.rng = random.Random(9)
        self.cars = []
        self.img = {}
        W = world.pixel_w
        for i in range(len(self.lanes)):
            x = self.rng.uniform(-200, W)
            self.cars.append([i, x, self.rng.choice(CAR_COLOURS), self.rng.uniform(0.7, 1.0) * VMAX])
        self.timer = [0.0, 0.0]

    def update(self, dt, player_rect=None, hour=12.0):
        W = self.world.pixel_w
        for car in list(self.cars):
            i, x, col, v = car
            car[1] = x + v * self.lanes[i][1] * dt
            if car[1] < -300 or car[1] > W + 300:
                self.cars.remove(car)
        for i in range(len(self.lanes)):
            self.timer[i] -= dt
            if self.timer[i] <= 0:
                d = self.lanes[i][1]
                self.cars.append([i, -200 if d > 0 else W + 200, self.rng.choice(CAR_COLOURS), self.rng.uniform(0.7, 1.0) * VMAX])
                quiet = hour >= 23 or hour < 6
                self.timer[i] = self.rng.uniform(5, 12) if quiet else self.rng.uniform(1.2, 3.5)

    def sprites(self, view):
        for i, x, col, v in self.cars:
            y, d = self.lanes[i]
            key = (col, d > 0)
            img = self.img.get(key)
            if img is None:
                img = self.img[key] = pa.car(col, facing_right=d > 0)
            pos = (x - img.get_width() / 2, y - img.get_height())
            if view.colliderect(pygame.Rect(pos, img.get_size())):
                yield img, pos, self.sort + y / 1000

    def lights(self, dark):
        if dark < 0.15: return []
        out = []
        for i, x, col, v in self.cars:
            y, d = self.lanes[i]
            out.append((x + d * 110, y - 22, 100, (255, 244, 210), 0.8 * dark))
        return out
