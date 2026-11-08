"""The story as you play it: where to go next, the compass that gets you there, the cut scenes, the time echoes and
the things you read. The words are all in quest_script.py; the flashback scenes are in echo.py; the documents in
documents.py.

  - Objectives are in quest_script.OBJECTIVES, in order.
  - The compass at the top of the screen points along the shortest WALKING route to the objective: a breadth-first
    search over the tiles you can actually walk between (up, down, left, right - so it goes round buildings, the water
    and the police tape, never straight through them). When the objective's on another map, or you're in a shop,
    it leads you to the way out / the way there first.
  - Cut scenes: click (or E / Space / Enter) for the next line.
"""
import heapq
import math
import random
from collections import deque
import pygame

import quest_script as S
import documents
import echo

TILE = 64

# where the places in the story are: name -> (place, door tile, shop kind)
DOORS = {
    "arcade": ("Harbourside", (29, 45), "arcade"),
    "usher": ("Park Street", (11, 18), "wills"),       # the Wills Memorial Building (his office is off the hall)
    "gazette": ("Park Street", (122, 19), "gazette"),
    "hostel": ("Park Street", (38, 19), "hostel"),
}
OFFICE_DOOR = (2, 1)              # in the Wills hall: Professor Usher's door (stand below it and walk up)
# Things to look at in Usher's packed-up office (the last visit): id -> (where to stand, how close, what it says)
HOTSPOTS = {
    "desk": ((4.0, 5.0), 1.25, "E: search the desk"),
    "computer": ((8.0, 3.0), 1.2, "E: use the computer"),
    "cabinet": ((6.0, 2.2), 0.95, "E: look in the filing cabinet"),
    "bookcase": ((2.3, 2.3), 1.2, "E: look at the bookcase"),
    "bookcase2": ((10.0, 2.4), 0.9, "E: look at the bookcase"),
    "box1": ((3.5, 3.1), 0.8, "E: look in the box"),
    "box2": ((8.5, 4.2), 0.85, "E: look in the box"),
    "box3": ((6.5, 6.1), 0.85, "E: look in the box"),
    "armchair": ((9.5, 7.5), 1.0, "E: look at the armchair"),
}
SEAGULL_FRONT = (3, 2)            # in the arcade: in front of the Seagull Bird machine on the back wall
LOCKER_FRONT = (21, 5)            # in the store room: in front of John's locker
SHELF_FRONT = (19, 2)             # in the store room: in front of the staff records
BUS_STOP = ("Park Street", (95, 29), (98, 29))   # the College Green bus stop: where you wait (tiles), the bus to Clifton Down
VIEW_ITEMS = {"newspaper": "paper2026", "old_photo": "photo1999", "emily_photo": "photo1999", "cutting": "paper1999",
              "record1998": "record1998", "record1999": "record1999", "ju_photo": "ju_photo"}


def story_start(hours):
    """Every run the story starts the next morning at half eight."""
    return (int(hours // 24) + 1) * 24 + 8.5


# ================================================================== the compass: shortest walking route
class Compass:
    def __init__(self):
        self.walk_cache = {}         # id(world) -> (world, (east, south)) where you can walk
        self.field_cache = {}        # (id(world), targets) -> distance grid
        self.angle = None
        self.steps = None
        self.final = None            # once you're there: which way to keep walking (into a door / off the map edge)
        self.finals = {}             # ...or per target tile, when the targets are doors facing different ways
        self._len_key, self._len = None, 0

    def links(self, world):
        """Where you can walk between neighbouring tiles. east[y][x]: from (x, y) to (x+1, y) the way's clear for a
        person (your feet box, plus a little room) walking middle to middle; south[y][x]: from (x, y) down to (x, y+1)."""
        got = self.walk_cache.get(id(world))
        if got is not None and got[0] is world:
            return got[1]
        east = [[False] * world.w for _ in range(world.h)]
        south = [[False] * world.w for _ in range(world.h)]

        def clear(r):
            return not any(r.colliderect(s) for s in world.nearby_solids(r, actors=False))
        for y in range(world.h):
            for x in range(world.w):
                if x + 1 < world.w:
                    east[y][x] = clear(pygame.Rect(x * TILE + 18, y * TILE + 23, TILE + 28, 18))
                if y + 1 < world.h:
                    south[y][x] = clear(pygame.Rect(x * TILE + 18, y * TILE + 23, 28, TILE + 18))
        if len(self.walk_cache) > 8:
            self.walk_cache.clear(); self.field_cache.clear()
        self.walk_cache[id(world)] = (world, (east, south))
        return east, south

    @staticmethod
    def steps_from(world, links, x, y):
        """The tiles you can walk to in one step from (x, y)."""
        east, south = links
        if x + 1 < world.w and east[y][x]: yield x + 1, y
        if x > 0 and east[y][x - 1]: yield x - 1, y
        if y + 1 < world.h and south[y][x]: yield x, y + 1
        if y > 0 and south[y - 1][x]: yield x, y - 1

    def bfs(self, world, targets, blocked=()):
        """Cost to the nearest target from every tile, walking only up/down/left/right where the way is clear.
        Pavements cost 1 a step, roads cost more (so the route keeps to the pavement and crosses the road straight
        over, at a crossing where there is one) - like a person would walk."""
        lk = self.links(world)
        INF = 1 << 30
        dist = [[INF] * world.w for _ in range(world.h)]
        ground = getattr(world, "ground", None)
        heap = []
        for x, y in targets:
            if 0 <= x < world.w and 0 <= y < world.h:
                dist[y][x] = 0; heap.append((0, x, y))
        heapq.heapify(heap)
        while heap:
            d0, x, y = heapq.heappop(heap)
            if d0 > dist[y][x]:
                continue
            for nx, ny in self.steps_from(world, lk, x, y):
                if (nx, ny) in blocked:
                    continue
                d = d0 + (4 if ground is not None and ground[ny][nx] in "=`" else 1)
                if d < dist[ny][nx]:
                    dist[ny][nx] = d; heapq.heappush(heap, (d, nx, ny))
        return dist

    def path_len(self, world, dist, x, y):
        """How many steps it really is along the route from (x, y)."""
        n = 0
        while dist[y][x] > 0 and n < 2000:
            nxt = self.next_tile(world, dist, x, y)
            if nxt is None:
                break
            x, y = nxt; n += 1
        return n

    STILL = ("stand", "sit", "work", "press", "sleep", "dance", "script")

    def field(self, world, targets):
        """Steps to the targets from everywhere - going round walls, and round people standing still (customers at
        the machines, people chatting) as if they were furniture."""
        blocked = frozenset((int(a.x // TILE), int(a.y // TILE)) for a in world.actors
                            if getattr(a, "behaviour", "") in self.STILL and getattr(a, "shown", True)
                            and not getattr(a, "moving", False)) - frozenset(targets)
        key = (id(world), targets, blocked)
        got = self.field_cache.get(key)
        if got is None:
            if len(self.field_cache) > 40:
                self.field_cache.clear()
            got = self.field_cache[key] = self.bfs(world, targets, blocked)
        return got

    def next_tile(self, world, dist, x, y):
        """One step along the route from (x, y), or None if you're there (or it's no use)."""
        best = None
        for nx, ny in self.steps_from(world, self.links(world), x, y):
            if dist[ny][nx] < dist[y][x] and (best is None or dist[ny][nx] < dist[best[1]][best[0]]):
                best = (nx, ny)
        return best

    def nearest(self, world, dist, pos):
        """The closest tile with a route from it, near where you're standing: (steps, x, y) or None."""
        INF = 1 << 30
        tx, ty = int(pos[0] // TILE), int(pos[1] // TILE)
        best = None
        for r in range(0, 3):                          # you might be standing half on a blocked tile
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    x, y = tx + dx, ty + dy
                    if 0 <= x < world.w and 0 <= y < world.h and dist[y][x] < INF:
                        if best is None or dist[y][x] + abs(dx) + abs(dy) < best[0]:
                            best = (dist[y][x] + abs(dx) + abs(dy), x, y)
            if best:
                break
        return best

    def point(self, world, pos, targets, dt):
        """Update the needle: aim a few steps along the route from where you're standing."""
        if not targets:
            self.steps = None; return
        dist = self.field(world, targets)
        best = self.nearest(world, dist, pos)
        if best is None:
            self.steps = None; return
        _, x, y = best
        key = (id(dist), x, y)
        if self._len_key != key:
            self._len_key, self._len = key, self.path_len(world, dist, x, y)
        self.steps = self._len
        for _ in range(4):                              # walk the route a few tiles ahead
            nxt = self.next_tile(world, dist, x, y) if dist[y][x] > 0 else None
            if nxt is None:
                break
            x, y = nxt
        aim = ((x + 0.5) * TILE - pos[0], (y + 0.6) * TILE - pos[1])
        final = self.finals.get((best[1], best[2]), self.final)
        if self.steps == 0 and final:
            want = {"right": 0.0, "down": math.pi / 2, "left": math.pi, "up": -math.pi / 2}[final]
        elif abs(aim[0]) < 4 and abs(aim[1]) < 4:
            return
        else:
            want = math.atan2(aim[1], aim[0])
        if self.angle is None:
            self.angle = want
        else:                                           # turn smoothly the short way round
            diff = (want - self.angle + math.pi) % (2 * math.pi) - math.pi
            self.angle += diff * min(1.0, dt * 8)


# ================================================================== keys pressed for you during a cut scene
class ScriptKeys:
    def __init__(self, held=()):
        self.held = set(held)

    def __getitem__(self, k):
        return k in self.held


class Cutscene:
    def __init__(self, lines, story, then=None):
        self.lines = lines
        self.story = story
        self.then = then                 # what happens when it's over
        self.i = 0
        self.shown = 0.0                 # how much of the current line has been typed out
        self.t = 0.0
        self.t_line = 0.0
        self.bars = 0.0                  # the black bars sliding in
        self.auto = None                 # this line moves on by itself after this long
        self.walk_to = None
        self.walk_time = 0.0
        self.walk_stuck = 0.0
        self.walk_best = 1e9
        self.walk_field = None
        self.done = False
        self._enter_line()

    def line(self):
        return self.lines[self.i]

    def _enter_line(self):
        ln = self.line()
        stage = ln[2] if len(ln) > 2 else {}
        self.shown = 0.0
        self.t_line = 0.0
        self.auto = stage.get("glitch") or stage.get("auto")
        self.story.stage_direction(stage, self)

    def advance(self):
        if self.done:
            return
        text = self.line()[1]
        if self.shown < len(text):       # finish typing the line first
            self.shown = len(text); return
        self.story.settle(self)          # anyone still walking: get them there now
        self.i += 1
        if self.i >= len(self.lines):
            self.done = True
        else:
            self._enter_line()

    def update(self, dt):
        self.t += dt
        self.t_line += dt
        self.bars = min(1.0, self.bars + dt * 3)
        self.shown += dt * 55
        if self.walk_to is not None:
            self.walk_time += dt
            self.walk_stuck += dt
        if self.auto is not None and self.t_line >= self.auto:
            self.shown = len(self.line()[1])
            self.advance()

    def keys(self, player):
        """Walk the detective to wherever the scene says, along the walking route (round people and things)."""
        if self.walk_to is None:
            return ScriptKeys()
        tx, ty = self.walk_to
        px, py = player.pos.x, player.pos.y
        left = math.hypot(tx - px, ty - py)
        if left < self.walk_best - 2:
            self.walk_best, self.walk_stuck = left, 0.0
        if left < 6 or self.walk_stuck > 1.2 or self.walk_time > 7.0:
            if left >= 6:
                self.story.snap_player(self.walk_to)
            self.walk_to = None
            if self.story.face_after_walk:
                self.story.face_player(self.story.face_after_walk)
            return ScriptKeys()
        wx, wy = tx, ty
        dist = self.walk_field
        if dist is not None:
            cx, cy = int(px // TILE), int(py // TILE)
            h, w = len(dist), len(dist[0])
            if 0 <= cx < w and 0 <= cy < h and 1 < dist[cy][cx] < (1 << 30):
                nxt = self.story.compass.next_tile(self.story.world, dist, cx, cy)
                if nxt is not None:
                    wx, wy = (nxt[0] + 0.5) * TILE, (nxt[1] + 0.5) * TILE
        held = set()
        if wx - px > 4: held.add(pygame.K_d)
        elif wx - px < -4: held.add(pygame.K_a)
        if wy - py > 4: held.add(pygame.K_s)
        elif wy - py < -4: held.add(pygame.K_w)
        return ScriptKeys(held)


# ================================================================== the story
class Story:
    def __init__(self, pocket, item_cls, icons, player, hooks):
        """hooks: render (draws a world for a scene), make_world (builds a place/room for a scene), clock (the game
        clock), places (every map by name)."""
        self.pocket = pocket
        self.Item = item_cls
        self.icons = icons                  # name -> icon function (pixel_art)
        self.player = player
        self.hooks = hooks
        self.clock = hooks["clock"]
        self.obj = 0
        self.cutscene = None
        self.reading = None                 # a document open outside a cut scene (re-reading something)
        self.view = None                    # the document shown during the cut scene
        self.scene = None                   # a time echo / the opening, instead of the game
        self.black = False
        self.live_glitch = 0.0
        self.rng = random.Random(9)
        self.compass = Compass()
        self.flags = set()
        self.world = None
        self.world_id = None
        self.place = None
        self.places = hooks["places"]
        self.shop = None                    # the shop you're in (its door etc.)
        self.shop_place = None
        self.face_after_walk = None
        self.toasts = []                    # [text, time left], shown one after another
        self.got = []                       # [text, time left]: things you've just been given (top right)
        self.hint = None                    # [text, time left] - a hint pop-up
        self.fonts = None
        self.walkers = []                   # [actor, field] people walking over to the detective
        self.later = []                     # [time, fn]: things that happen in a moment
        self.cafes_asked = []               # (place, door) of each café you've asked about Emily in
        self.emily_cafe = None              # (place, shop) - where Emily goes at six
        self.fade = 0.0                     # waiting: fade to black and back
        self.fade_fn = None
        self.photos = {}
        self.ids = {}                       # who's who in the world now: "martin", "barista", "daniel", ...
        self.ended = False                  # the story's over: time for the film
        self.want_computer = False          # E at Usher's computer: the game opens it (and stops the clock)
        self.ticket_time = None             # the train on Usher's ticket (fixed once you've seen it)
        self.choice = None                  # a question with options on screen (the hostel: sleep until when?)
        self.hide_player = False            # the detective's on the bus
        self.cutscene = Cutscene(S.OPENING, self)

    # ---- what's going on
    @property
    def busy(self):
        """True while a cut scene, a document or a fade has the screen (no walking about, no other keys)."""
        return self.cutscene is not None or self.reading is not None or self.fade > 0 or self.choice is not None

    def objective(self):
        return S.OBJECTIVES[self.obj] if self.obj < len(S.OBJECTIVES) else None

    def oid(self):
        ob = self.objective()
        return ob["id"] if ob else None

    def say(self, text, secs):
        self.toasts.append([text, secs])

    def complete(self, toast=None):
        self.obj += 1
        nxt = self.objective()
        self.toasts = []                    # an old "new objective" pop-up is out of date now
        self.say(toast or (f"New objective: {nxt['label']}" if nxt else "To be continued..."), 5.0)
        self.compass.angle = None
        self.compass.steps = None

    def label(self):
        ob = self.objective()
        if ob is None:
            return ""
        text = ob["label"]
        if ob["id"] == "wait_emily" and self.emily_cafe:
            text = f"Wait for Emily Carter at {self.emily_cafe[1]['brand'].title()} (she comes in at 6pm)"
            if not self._open("cafe"):
                text = "Emily comes in at 6pm and the café's shut - rest at the Night Owl hostel until then"
        if ob["id"] == "search":
            n = sum(1 for k in ("record1999", "ju_photo", "ticket") if k in self.flags)
            text = f"Search Professor Usher's office - walk up to things, E to look ({n} of 3 clues found)"
        if ob["id"] in ("arcade", "high_score", "locker", "records") and not self._open("arcade"):
            text += " (the arcade opens at 10:00 - rest at the Night Owl hostel, or hold T)"
        return text

    def _open(self, kind):
        import people
        return people.is_open(kind, self.clock.hour)

    # ---- each frame
    def update(self, dt, world, place, player, places):
        self.player, self.place, self.places = player, place, places
        if world is not self.world:
            self.world = world
            self._prepare(world)
        self.live_glitch = max(0.0, self.live_glitch - dt)
        if self.got:
            self.got[0][1] -= dt
            if self.got[0][1] <= 0:
                self.got.pop(0)
        if self.toasts and not self.busy:
            self.toasts[0][1] -= dt
            if self.toasts[0][1] <= 0:
                self.toasts.pop(0)
        if self.hint and not self.busy:
            self.hint[1] -= dt
            if self.hint[1] <= 0:
                self.hint = None
        for item in list(self.later):
            item[0] -= dt
            if item[0] <= 0:
                self.later.remove(item); item[1]()
        if self.fade > 0:                                   # waiting for six o'clock
            before = self.fade
            self.fade = max(0.0, self.fade - dt)
            if before > 1.0 >= self.fade and self.fade_fn:
                fn, self.fade_fn = self.fade_fn, None
                fn()
        self._walk_people(dt, world)
        if self.scene:
            self.scene.update(dt)
        if self.cutscene:
            self.cutscene.update(dt)
            if self.cutscene.done:
                self._end_cutscene()
            return
        if self.busy:
            return
        self._check(world, place, player)
        if self.cutscene:
            return
        ob = self.objective()
        if ob is None:
            self.compass.steps = None
            return
        self.compass.point(world, (player.pos.x, player.pos.y), self.targets(world, place), dt)

    def _prepare(self, world):
        """A new place/room: make the people the story needs (and take away the ones who've gone)."""
        import people
        self.ids = {}
        kind = (world.interior or {}).get("kind")
        if world.interior is None and "daniel_left" in self.flags:
            world.actors = [a for a in world.actors if a.id != "crime_daniel"]
        for a in world.actors:
            if a.id.endswith("_staff"):
                if kind == "arcade":
                    a.name = "Martin Bell"; a.lines = [["Enjoy the games."]]; self.ids["martin"] = a.id
                    a.look = people.SUSPECTS["martin"]; a.frames = {}
                elif kind == "cafe":
                    self.ids["barista"] = a.id
                elif kind == "corner":
                    self.ids["shopkeeper"] = a.id
        if kind == "gazette":                       # a couple of reporters - and Daniel, once he's left the harbour
            def sitter(nid, tx, ty, role, name=None, lines=None):
                n = people.NPC(nid, tx * TILE + 32, ty * TILE + 52, role, "sit", d="down", name=name, lines=lines)
                n.pose = "sit"; n.sort_bias = 4
                world.actors.append(n)
                return n
            if "daniel_left" in self.flags:
                sitter("daniel", 7, 5, "journalist", "Daniel Shaw", [["Let me know if you find anything."]])
                self.ids["daniel"] = "daniel"
            sitter("reporter1", 2, 2, "public")
            sitter("reporter2", 7, 2, "public")
        if kind == "cafe" and self.oid() == "wait_emily" and self.emily_cafe and self.shop is self.emily_cafe[1] \
                and 18 <= self.clock.hour < 19.9:
            self.later.append([1.2, self._emily_arrives])

    def entered(self, shop):
        """Called by the game when you walk into a shop (None when you come back out)."""
        self.shop = shop
        if shop is not None:
            self.shop_place = self.place            # the street the shop's on

    # ---- reaching things
    def _check(self, world, place, player):
        o = self.oid()
        kind = (world.interior or {}).get("kind")
        px, py = player.pos.x, player.pos.y
        if o == "crime_scene" and place == "Harbourside" and kind is None:
            cs = getattr(world._map_def, "CRIME_SCENE", None)
            officer = self._actor("crime_officer")
            if cs and officer and math.hypot(px - officer.x, py - officer.y) < cs["trigger"] * TILE:
                self.compass.steps = None
                self.start(S.CRIME_SCENE, self._after_crime_scene)
        elif o == "arcade" and kind == "arcade":
            self.later.append([0.5, lambda: self.start(S.ARCADE_ENTER, self._after_arcade_enter)])
            self.flags.add("in_arcade"); self.complete_quiet()
        elif o == "usher" and kind == "usher":
            self.start(S.USHER_OFFICE, lambda: self.complete())
        elif o == "usher2" and kind == "usher":
            self.start(S.USHER_GONE, lambda: self.complete())
        elif o == "daniel" and kind == "gazette":
            d = self._actor("daniel")
            if d is not None and math.hypot(px - d.x, py - d.y) < 2.4 * TILE:
                self.start(S.DANIEL, lambda: self.complete())
        elif o == "wait_emily" and kind == "cafe" and self.emily_cafe and self.shop is self.emily_cafe[1] \
                and 18 <= self.clock.hour < 19.9 and "emily_here" not in self.flags and not self.later:
            self.later.append([0.8, self._emily_arrives])

    def _the_end(self):
        self.obj = len(S.OBJECTIVES)
        self.compass.steps = None
        self.ended = True                    # the game plays the film, then goes back to the main menu

    def complete_quiet(self):
        """Move on without the 'new objective' pop-up (the next scene says it)."""
        self.obj += 1
        self.compass.angle = None; self.compass.steps = None

    def _after_crime_scene(self):
        self.later.append([1.0, lambda: self.start(S.RECORDER, lambda: self.complete())])

    def _after_arcade_enter(self):
        self.hint = [S.ARCADE_HINT, 9.0]

    # ---- things you press E for (returns the prompt to show, or None)
    def prompt(self, world, place, player):
        if self.busy:
            return None
        o = self.oid()
        kind = (world.interior or {}).get("kind")
        px, py = player.pos.x, player.pos.y
        near = lambda tx, ty, r: math.hypot(px - (tx + 0.5) * TILE, py - (ty + 0.5) * TILE) < r * TILE
        if kind == "corner" and "newspaper" not in self.flags and self._near_staff(world, player):
            return "E: buy the morning paper"
        if o == "station" and kind is None and place == BUS_STOP[0] and world.traffic is not None \
                and world.traffic.bus_at_stop():
            b = world.traffic.bus
            if abs(px - b["x"]) < 3.5 * TILE and abs(py - b["y"]) < 2.5 * TILE:
                return "E: get on the bus to Clifton Down"
        if kind == "hostel":
            tx, ty = int(px // TILE), int(py // TILE)
            bed = any(world.at(tx + dx, ty + dy, " ") == "e" for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            if bed or self._near_staff(world, player):
                return "E: get some rest (choose how long)"
        if o == "search" and kind == "usher":
            best = None
            for hid, ((hx, hy), r, text) in HOTSPOTS.items():
                d = math.hypot(px - hx * TILE, py - hy * TILE)
                if d < r * TILE and (best is None or d < best[0]):
                    best = (d, hid, text)
            if best:
                if best[1] == "desk" and "record1999" in self.flags:
                    return "E: open the desk drawers" if "ju_photo" not in self.flags else "E: search the desk"
                return best[2]
        if o == "locker" and kind == "arcade" and near(*LOCKER_FRONT, 1.3):
            return "E: open John's locker"
        if o == "records" and kind == "arcade" and py < 3.4 * TILE and 17.5 * TILE < px < 22.5 * TILE:
            return "E: look through the staff records"
        if o == "find_emily" and kind == "cafe" and self._near_staff(world, player) and \
                self._cafe_key() not in self.cafes_asked:
            return "E: ask about Emily"
        if o == "wait_emily" and kind == "cafe" and self.emily_cafe and self.shop is self.emily_cafe[1] \
                and "emily_here" not in self.flags and not (18 <= self.clock.hour < 19.9):
            return "E: sit down and wait for Emily (6pm)"
        return None

    def interact(self, world, place, player):
        """E pressed with a prompt showing: do it. Returns True if the story used the key."""
        p = self.prompt(world, place, player)
        if p is None:
            return False
        if p.startswith("E: get on the bus"):
            world.traffic.board_bus()
            self.hide_player = True                  # on the bus: it pulls away with you on it
            self.start(S.BUS_RIDE, lambda: self.start(S.ENDING, self._the_end))
            return True
        if p.startswith("E: get some rest"):
            self.rest_menu()
            return True
        if self.oid() == "search" and (world.interior or {}).get("kind") == "usher":
            self._search(p, world, player)
            return True
        if p.startswith("E: buy"):
            self.start(S.NEWSPAPER_BUY, lambda: self.open_view("paper2026"), talking=self.ids.get("shopkeeper"))
        elif p.startswith("E: open John's"):
            self.start(S.LOCKER, lambda: self.complete())
        elif p.startswith("E: look through"):
            self.start(S.RECORDS, lambda: self.complete())
        elif p.startswith("E: ask"):
            key = self._cafe_key()
            if key in self.cafes_asked:
                self.start(S.CAFE_ASKED_AGAIN, talking=self.ids.get("barista"))
            else:
                self.cafes_asked.append(key)
                n = len(self.cafes_asked)
                lines = S.CAFE_ASKS[min(n, len(S.CAFE_ASKS)) - 1]
                then = None
                if n >= len(S.CAFE_ASKS):
                    self.emily_cafe = (self.shop_place, self.shop)
                    then = lambda: self.complete()
                self.start(lines, then, talking=self.ids.get("barista"))
        elif p.startswith("E: sit"):
            def six():
                h = self.clock.hours
                day = int(h // 24) * 24
                self.clock.hours = day + 18.0 if h % 24 < 18 else day + 24 + 18.0
                self.later.append([1.6, self._emily_arrives])
            self.fade, self.fade_fn = 2.0, six
            self.say("Later...", 2.0)
        return True

    # ---- searching Usher's office (the last visit): it's up to you
    def _search(self, p, world, player):
        if p == "E: use the computer":
            if not self.ticket_time:                 # the next train, from now (time stops at the computer, and
                m = (int(self.clock.hour * 60) + 50) // 5 * 5      # it's fixed once you've found the ticket)
                documents.TICKET["time"] = f"{(m // 60) % 24:02d}:{m % 60:02d}"
            self.want_computer = True
            return
        if p in ("E: search the desk", "E: open the desk drawers"):
            if "record1999" not in self.flags:
                self.start(S.SEARCH_RECORD, self._search_progress)
            elif "ju_photo" not in self.flags:
                self.start(S.SEARCH_DRAWER, self._search_progress)
            else:
                self.start(S.SEARCH_DESK_EMPTY)
            return
        px, py = player.pos.x, player.pos.y
        hid = min((h for h in HOTSPOTS if h not in ("desk", "computer")),
                  key=lambda h: math.hypot(px - HOTSPOTS[h][0][0] * TILE, py - HOTSPOTS[h][0][1] * TILE))
        self.start(S.SEARCH_LOOKS[hid.rstrip("2")])

    def computer_closed(self, found):
        """Back from Usher's computer. found = you opened the ticket in his browser history."""
        if found and "ticket" not in self.flags:
            self.ticket_time = documents.TICKET["time"]
            self.flags.add("ticket")
            self.start(S.SEARCH_TICKET, self._search_progress)

    def _search_progress(self):
        if all(k in self.flags for k in ("record1999", "ju_photo", "ticket")):
            self.start(S.SEARCH_DONE, lambda: self.complete())
        else:
            n = sum(1 for k in ("record1999", "ju_photo", "ticket") if k in self.flags)
            self.say(f"{n} of 3 clues found. Keep looking.", 3.0)

    # ---- passing the time (the hostel)
    def rest_menu(self):
        """Sleep until the morning, until the arcade opens, or until the evening."""
        def until(hour, words):
            def go():
                def jump():
                    h = self.clock.hours
                    day = int(h // 24) * 24
                    t = day + hour
                    if t <= h + 0.05:
                        t += 24
                    self.clock.hours = t
                    self.say(f"You {words}. It's {int(hour):02d}:00.", 3.5)
                self.fade, self.fade_fn = 2.0, jump
            return go
        self.choice = dict(title="Get some rest - until when?", sel=0, options=[
            ("The morning (08:00)", until(8, "sleep until morning")),
            ("The arcade opens (10:00)", until(10, "rest until ten")),
            ("The evening (18:00)", until(18, "rest until six")),
            ("Never mind", lambda: None)])

    def _cafe_key(self):
        return (self.shop_place, tuple(self.shop["door"])) if self.shop else None

    def _near_staff(self, world, player):
        for a in world.actors:
            if a.id.endswith("_staff") and math.hypot(player.pos.x - a.x, player.pos.y - a.y) < 2.2 * TILE:
                return True
        tx, ty = int(player.pos.x // TILE), int(player.pos.y // TILE)
        return any(world.at(tx + dx, ty + dy, " ") in "XQ" for dx in (-1, 0, 1) for dy in (-1, 0, 1))

    def _emily_arrives(self):
        import people
        w = self.world
        if "emily_here" in self.flags or w is None or (w.interior or {}).get("kind") != "cafe":
            return
        self.flags.add("emily_here")
        n = people.NPC("emily", w.spawn[0], w.spawn[1], "public", "script", d="up", name="Emily Carter")
        n.look = echo.LOOKS["emily"]; n.frames = {}
        n.lines = [["I hope you find whoever did this."]]
        w.actors.append(n)
        self.ids["emily"] = "emily"
        self.start(S.EMILY, lambda: self.complete())

    # ---- the arcade machine
    def arcade_goal(self, machine):
        if self.oid() == "high_score" and machine == S.JOHN_MACHINE:
            return (S.JOHN_SCORE, "J.HARPER")
        return None

    def won(self, machine):
        if self.oid() == "high_score" and machine == S.JOHN_MACHINE:
            self.start(S.MARTIN, lambda: self.complete())

    def room(self, kind):
        """Which layout a room has now (Usher's office is packed up by the end)."""
        if kind == "usher" and self.oid() in ("usher2", "search", "station", None):
            return "usher_packed", "packed"
        return kind, None

    # ---- where the compass points
    def targets(self, world, place):
        o = self.oid()
        self.compass.final = None
        self.compass.finals = {}
        if o is None:
            return ()
        kind = (world.interior or {}).get("kind")

        def exit_():
            self.compass.final = "down"
            return (tuple(world.exit_tile),) if world.exit_tile else ()

        def go_to(goal_place, tiles, final=None):
            if kind is not None:
                return exit_()
            if place != goal_place:
                return self._hop_targets(world, place, goal_place)
            self.compass.final = final
            return tuple(tiles)

        def door(name):
            p, (dx, dy), k = DOORS[name]
            if name == "usher" and kind == "wills":                  # in the hall: his door, top left
                self.compass.final = "up"
                return ((OFFICE_DOOR[0], OFFICE_DOOR[1] + 1),)
            if kind is not None and kind != k:
                return exit_()
            return go_to(p, [(dx, dy + 1)], "up")

        if o == "crime_scene":
            a = self._actor("crime_officer") if place == "Harbourside" else None
            if place == "Harbourside" and kind is None and a is not None:
                cx, cy = int(a.x // TILE), int(a.y // TILE)
                return tuple((cx + dx, cy + dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2) if abs(dx) + abs(dy) <= 2)
            return go_to("Harbourside", [])
        if o == "search":
            if kind == "usher":
                return ()                                            # no pointing: you're the detective
            return door("usher")
        if o in ("arcade", "usher", "usher2", "daniel"):
            name = {"arcade": "arcade", "usher": "usher", "usher2": "usher", "daniel": "gazette"}[o]
            if o == "daniel" and kind == "gazette":
                d = self._actor("daniel")
                return ((int(d.x // TILE), int(d.y // TILE) + 2),) if d else ()
            return door(name)
        if o in ("high_score", "locker", "records"):
            if kind == "arcade":
                self.compass.final = "up"
                return {"high_score": (SEAGULL_FRONT,), "locker": (LOCKER_FRONT,),
                        "records": (SHELF_FRONT, (SHELF_FRONT[0] + 1, SHELF_FRONT[1]))}[o]
            return door("arcade")
        if o == "find_emily":
            if kind == "cafe":
                if self._cafe_key() not in self.cafes_asked:
                    for a in world.actors:
                        if a.id.endswith("_staff"):
                            return ((int(a.x // TILE), int(a.y // TILE) + 2),)
                return exit_()
            if kind is not None:
                return exit_()
            out = []
            for shop in getattr(world._map_def, "SHOPS", []) if not isinstance(world._map_def, str) else []:
                if shop["kind"] == "cafe" and (place, tuple(shop["door"])) not in self.cafes_asked:
                    dx, dy = shop["door"]
                    tile = (dx, dy + 1) if shop["side"] == "south" else (dx, dy - 1)
                    out.append(tile)
                    self.compass.finals[tile] = "up" if shop["side"] == "south" else "down"
            if out:
                return tuple(out)
            return self._hop_targets(world, place, "Park Street") if place != "Park Street" else ()
        if o == "wait_emily":
            ep, shop = self.emily_cafe
            if not self._open("cafe"):                     # shut: go and rest at the hostel till the evening
                if kind == "hostel":
                    return ()
                return door("hostel")
            if kind == "cafe" and self.shop is shop:
                return ()
            dx, dy = shop["door"]
            if kind is not None:
                return exit_()
            side = shop["side"]
            return go_to(ep, [(dx, dy + 1) if side == "south" else (dx, dy - 1)], "up" if side == "south" else "down")
        if o == "station":
            p, a, b = BUS_STOP
            return go_to(p, [(x, a[1]) for x in range(a[0], b[0] + 1)], None)
        return ()

    def _hop_targets(self, world, place, goal):
        hop = self._next_hop(place, goal, self.places)
        out = []
        for pt in world.portals:
            if pt.get("to") == hop:
                self.compass.final = pt.get("dir", "up")
                a = pt["area"]
                for ty in range(a.top // TILE, (a.bottom - 1) // TILE + 1):
                    for tx in range(a.left // TILE, (a.right - 1) // TILE + 1):
                        out.append((tx, ty))
        return tuple(out)

    @staticmethod
    def _next_hop(here, goal, places):
        """Which place to go to next to get from here to there (breadth-first over the ways between maps)."""
        prev = {here: None}
        q = deque([here])
        while q:
            p = q.popleft()
            if p == goal:
                break
            for pt in getattr(places.get(p), "PORTALS", []) or []:
                n = pt.get("to")
                if n in places and n not in prev:
                    prev[n] = p; q.append(n)
        if goal not in prev:
            return None
        step = goal
        while prev[step] != here and prev[step] is not None:
            step = prev[step]
        return step

    def _actor(self, aid):
        if self.world is None:
            return None
        for a in self.world.actors:
            if a.id == aid:
                return a
        return None

    # ---- cut scenes
    def start(self, lines, then=None, talking=None):
        if self.pocket.reading:
            self.pocket.close_notebook()
        self.pocket.open = False
        if talking:
            a = self._actor(talking)
            if a is not None:
                self._face_each_other(a)
        self.cutscene = Cutscene(lines, self, then)

    def _end_cutscene(self):
        cs = self.cutscene
        self.cutscene = None
        self.view = None
        self.black = False
        self.scene = None
        for a in (self.world.actors if self.world else []):
            a.talking = False
        if cs.then:
            cs.then()

    def settle(self, cs):
        """The player clicked on: anyone still walking gets where they're going."""
        if cs.walk_to is not None:
            self.snap_player(cs.walk_to); cs.walk_to = None
            if self.face_after_walk:
                self.face_player(self.face_after_walk)
        if self.scene is not None:
            self.scene.settle()
        for actor, _ in list(self.walkers):
            self._arrive(actor, snap=True)

    def stage_direction(self, stage, cs):
        self.black = bool(stage.get("black"))
        if not stage:
            return
        if "scene" in stage:
            self.scene = echo.Scene(stage["scene"], self.hooks["make_world"], self.hooks["render"], self.player,
                                    self._cafe_seed())
        if "cut" in stage:
            self.scene = echo.Scene(stage["cut"], self.hooks["make_world"], self.hooks["render"], self.player,
                                    self._cafe_seed())
            self.scene.flash = 0.0
        if stage.get("end_scene"):
            self.scene = None
        if stage.get("glitch"):
            if self.scene is not None:
                self.scene.glitch = stage["glitch"]
            else:
                self.live_glitch = stage["glitch"]
        if self.scene is not None:
            if "move" in stage:
                self.scene.move(*stage["move"])
            if stage.get("push"):
                self.scene.push()
            if "ring" in stage:
                self.scene.ring = stage["ring"]
            if "flame" in stage:
                self.scene.flame = stage["flame"]
        if "view" in stage:
            self.view = stage["view"]
        if "face" in stage and stage.get("walk") is None:
            self.face_player(stage["face"])
        if stage.get("walk") == "approach":
            cs_def = getattr(self.world._map_def, "CRIME_SCENE", None)
            if cs_def:
                ax, ay = cs_def["approach"]
                cs.walk_to = (ax * TILE, ay * TILE)
                cs.walk_time = cs.walk_stuck = 0.0
                cs.walk_best = 1e9
                cs.walk_field = self.route(int(ax), int(ay))
                self.face_after_walk = stage.get("face")
        if "give" in stage:
            gives = stage["give"] if isinstance(stage["give"], tuple) else (stage["give"],)
            for g in gives:
                self.give(g)
        if stage.get("leave"):
            a = self._actor(stage["leave"])
            if a is not None:
                a.leaving = True
                a.behaviour = "script"
                a.leave_y = min(self.world.pixel_h - 24, a.y + 0.8 * TILE)   # step down past the detective...
                a.leave_x = a.x - 14 * TILE                                    # ...then off along the water
            self.flags.add("daniel_left")
        if stage.get("walk_to_player"):
            a = self._actor(self.ids.get(stage["walk_to_player"], stage["walk_to_player"]))
            if a is not None:
                self._send_to_player(a)

    def give(self, g):
        if g in self.flags:
            return
        self.flags.add(g)
        name, desc, icon = S.ITEMS[g]
        it = self.Item(g, name, desc, self.icons[icon])
        if g in VIEW_ITEMS:
            it.use = (lambda v=VIEW_ITEMS[g]: self.open_view(v))
        self.pocket.add(it)
        if g == "daniel_number":
            nb = self.pocket.notebook
            if S.DANIEL_NUMBER not in "".join(nb.pages):
                note = f"Daniel Shaw (journalist) - {S.DANIEL_NUMBER}. Knew John Harper. Said look at the arcade."
                nb.page = len(nb.pages) - 1
                nb.type(("\n" if nb.pages[nb.page].strip() else "") + note)
                nb.save()
            self.got.append(["+ Daniel's number (in your pocket and your notebook)", 3.5])
        else:
            self.got.append([f"+ {name} (in your pocket)", 3.0])

    def _cafe_seed(self):
        if self.emily_cafe:
            dx, dy = self.emily_cafe[1]["door"]
            return dx * 31 + dy * 17
        return 7

    # ---- people walking over / away
    def _send_to_player(self, a):
        w = self.world
        tx, ty = int(self.player.pos.x // TILE), int(self.player.pos.y // TILE)
        blocked = {(int(o.x // TILE), int(o.y // TILE)) for o in w.actors if o is not a}
        goals = [(tx + dx, ty + dy) for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1))
                 if 0 <= tx + dx < w.w and 0 <= ty + dy < w.h and (tx + dx, ty + dy) not in blocked]
        a.behaviour = "script"; a.talking = False
        self.walkers.append([a, self.compass.bfs(w, tuple(goals), blocked)])

    def _walk_people(self, dt, world):
        for a in list(world.actors):                                  # Daniel walking off along the water
            if getattr(a, "leaving", False):
                a.talking = False; a.moving = True; a.t += dt
                if a.y < a.leave_y:
                    a.y = min(a.leave_y, a.y + 60 * dt); a.d = "down"
                else:
                    a.x -= 72 * dt; a.d = "left"
                if a.x < a.leave_x:
                    world.actors.remove(a)
        for entry in list(self.walkers):
            a, dist = entry
            if a not in world.actors:
                self.walkers.remove(entry); continue
            cx, cy = int(a.x // TILE), int(a.y // TILE)
            INF = 1 << 30
            if not (0 <= cx < world.w and 0 <= cy < world.h) or dist[cy][cx] >= INF:
                self._arrive(a, snap=True); continue
            if dist[cy][cx] == 0:
                wx, wy = (cx + 0.5) * TILE, (cy + 0.5) * TILE + 12
            else:
                nxt = self.compass.next_tile(world, dist, cx, cy)
                if nxt is None:
                    self._arrive(a, snap=True); continue
                wx, wy = (nxt[0] + 0.5) * TILE, (nxt[1] + 0.5) * TILE + 12
            dx, dy = wx - a.x, wy - a.y
            d = math.hypot(dx, dy)
            if dist[cy][cx] == 0 and d < 4:
                self._arrive(a); continue
            k = min(1.0, 110 * dt / max(d, 0.01))
            a.x += dx * k; a.y += dy * k
            a.moving = True; a.t += dt
            a.d = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")

    def _arrive(self, a, snap=False):
        for entry in list(self.walkers):
            if entry[0] is a:
                self.walkers.remove(entry)
        if snap:                                                        # straight to the detective's side
            w = self.world
            tx, ty = int(self.player.pos.x // TILE), int(self.player.pos.y // TILE)
            for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                x, y = tx + dx, ty + dy
                r = pygame.Rect(x * TILE + 20, y * TILE + 26, 24, 24)
                if 0 <= x < w.w and 0 <= y < w.h and not any(r.colliderect(s) for s in w.nearby_solids(r, actors=False)):
                    a.x, a.y = (x + 0.5) * TILE, (y + 0.5) * TILE + 12
                    break
        a.moving = False
        self._face_each_other(a)

    def _face_each_other(self, a):
        dx, dy = a.x - self.player.pos.x, a.y - self.player.pos.y
        self.player.direction = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")
        if getattr(a, "pose", "stand") not in ("sit", "lie", "work"):
            a.d = ("left" if dx > 0 else "right") if abs(dx) > abs(dy) else ("up" if dy > 0 else "down")
        a.talking = True

    def face_player(self, aid):
        """Turn the detective (and whoever they're talking to) to face each other."""
        a = self._actor(self.ids.get(aid, aid))
        if a is not None and self.player is not None:
            self._face_each_other(a)

    def route(self, gx, gy):
        """Steps to (gx, gy) from every tile, going round walls AND the people standing about."""
        w = self.world
        blocked = {(int(a.x // TILE), int(a.y // TILE)) for a in w.actors} - {(gx, gy)}
        return self.compass.bfs(w, ((gx, gy),), blocked)

    def snap_player(self, pos):
        self.player.pos.update(pos); self.player.prev_pos.update(pos)

    def keys(self, player):
        return self.cutscene.keys(player) if self.cutscene else ScriptKeys()

    # ---- documents
    def open_view(self, view):
        self.reading = view

    def photo(self, sid):
        if sid not in self.photos:
            self.photos[sid] = echo.snapshot(sid, self.hooks["make_world"], self.hooks["render"], self.player, (960, 640))
        return self.photos[sid]

    # ---- input
    def handle(self, ev):
        """Called with every event while busy. Returns 'quit' if the window was closed."""
        if ev.type == pygame.QUIT:
            return "quit"
        advance = (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1) or \
                  (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN))
        if self.choice is not None:
            c = self.choice
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    c["sel"] = (c["sel"] - 1) % len(c["options"])
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    c["sel"] = (c["sel"] + 1) % len(c["options"])
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                    self.choice = None; c["options"][c["sel"]][1]()
                elif ev.key == pygame.K_ESCAPE:
                    self.choice = None
                elif pygame.K_1 <= ev.key <= pygame.K_9 and ev.key - pygame.K_1 < len(c["options"]):
                    self.choice = None; c["options"][ev.key - pygame.K_1][1]()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(c.get("rects", [])):
                    if r.collidepoint(ev.pos):
                        self.choice = None; c["options"][i][1]()
            elif ev.type == pygame.MOUSEMOTION:
                for i, r in enumerate(c.get("rects", [])):
                    if r.collidepoint(ev.pos):
                        c["sel"] = i
            return None
        if self.cutscene:
            if advance:
                self.cutscene.advance()
            return None
        if self.reading is not None:
            if advance or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                self.reading = None
        return None

    # ================================================================ drawing
    def _fonts_(self):
        if self.fonts is None:
            self.fonts = dict(
                name=pygame.font.SysFont("consolas,menlo,monospace", 18, bold=True),
                text=pygame.font.SysFont("consolas,menlo,monospace", 19),
                narr=pygame.font.SysFont("georgia,times new roman,serif", 21, italic=True),
                small=pygame.font.SysFont("consolas,menlo,monospace", 14),
                label=pygame.font.SysFont("consolas,menlo,monospace", 15, bold=True),
            )
        return self.fonts

    def draw(self, screen, view_offset):
        f = self._fonts_()
        w, h = screen.get_size()
        offset = view_offset
        if self.scene is not None:
            self.scene.draw(screen)
            offset = None
        if self.black:
            screen.fill((0, 0, 0))
        if self.live_glitch > 0 and self.scene is None:
            echo.glitch(screen, self.rng)
        if self.view is not None and self.cutscene:
            self._draw_doc(screen, self.view, w, h, lift=60)
        if self.cutscene:
            self._draw_cutscene(screen, f, w, h, offset)
        elif self.reading is None and self.fade <= 0:
            if self.objective() and self.compass.steps is not None:
                self._draw_compass(screen, f, w)
            elif self.objective():
                self._draw_label(screen, f, w, 40)
            if self.hint:
                self._draw_hint(screen, f, w)
            if self.toasts:
                t = f["label"].render(self.toasts[0][0], True, (250, 236, 200))
                a = min(1.0, self.toasts[0][1] / 0.6)
                box = pygame.Surface((t.get_width() + 28, t.get_height() + 14), pygame.SRCALPHA)
                box.fill((20, 22, 32, int(220 * a)))
                pygame.draw.rect(box, (200, 170, 90, int(255 * a)), box.get_rect(), 2)
                t.set_alpha(int(255 * a))
                box.blit(t, (14, 7))
                screen.blit(box, (w // 2 - box.get_width() // 2, 168))
        if self.got:                                         # "+ Arcade token" in the top right corner
            t = f["label"].render(self.got[0][0], True, (30, 24, 10))
            a = min(1.0, self.got[0][1] / 0.4)
            box = pygame.Surface((t.get_width() + 24, t.get_height() + 12), pygame.SRCALPHA)
            box.fill((250, 214, 90, int(235 * a)))
            t.set_alpha(int(255 * a))
            box.blit(t, (12, 6))
            screen.blit(box, (w - box.get_width() - 16, 76 if self.cutscene else 110))
        if self.reading is not None:
            self._draw_doc(screen, self.reading, w, h)
            m = f["small"].render("click (or Esc) to put it away", True, (220, 216, 200))
            screen.blit(m, (w // 2 - m.get_width() // 2, h - 24))
        if self.choice is not None:
            self._draw_choice(screen, f, w, h)
        if self.fade > 0:
            a = min(1.0, (2.0 - self.fade) / 0.6) if self.fade > 1.0 else min(1.0, self.fade / 0.6)
            dark = pygame.Surface((w, h)); dark.fill((0, 0, 0)); dark.set_alpha(int(255 * a))
            screen.blit(dark, (0, 0))

    def _draw_choice(self, screen, f, w, h):
        c = self.choice
        bw = 520
        bh = 70 + len(c["options"]) * 44
        x0, y0 = (w - bw) // 2, (h - bh) // 2
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((14, 16, 24, 236))
        pygame.draw.rect(panel, (230, 190, 90), panel.get_rect(), 2)
        screen.blit(panel, (x0, y0))
        t = f["name"].render(c["title"], True, (240, 220, 160))
        screen.blit(t, ((w - t.get_width()) // 2, y0 + 18))
        c["rects"] = []
        for i, (label, _) in enumerate(c["options"]):
            r = pygame.Rect(x0 + 30, y0 + 56 + i * 44, bw - 60, 36)
            if i == c["sel"]:
                pygame.draw.rect(screen, (60, 52, 30), r)
                pygame.draw.rect(screen, (230, 190, 90), r, 2)
            img = f["text"].render(f"{i + 1}.  {label}", True, (255, 240, 200) if i == c["sel"] else (220, 220, 226))
            screen.blit(img, (r.x + 14, r.y + (r.h - img.get_height()) // 2))
            c["rects"].append(r)
        m = f["small"].render("Up / Down and Enter, a number, or click  -  Esc: never mind", True, (180, 176, 168))
        screen.blit(m, ((w - m.get_width()) // 2, y0 + bh + 8))

    def _draw_doc(self, screen, view, w, h, lift=0):
        dim = pygame.Surface((w, h), pygame.SRCALPHA); dim.fill((0, 0, 0, 170))
        screen.blit(dim, (0, 0))
        if lift:                               # in a cut scene: between the black bar and the dialogue box
            doc = documents.get(view, (w, h - 170), self.photo, self.clock.hour)
            y = 70 + max(0, (h - 240 - doc.get_height()) // 2)
        else:
            doc = documents.get(view, (w, h), self.photo, self.clock.hour)
            y = max(8, h // 2 - doc.get_height() // 2)
        screen.blit(doc, (w // 2 - doc.get_width() // 2, y))

    def _draw_label(self, screen, f, w, y):
        t1 = f["label"].render(self.label(), True, (250, 240, 214))
        bw = t1.get_width() + 24
        box = pygame.Surface((bw, 26), pygame.SRCALPHA)
        box.fill((20, 22, 32, 205))
        box.blit(t1, (12, 5))
        screen.blit(box, (w // 2 - bw // 2, y))

    def _draw_hint(self, screen, f, w):
        t = f["label"].render(self.hint[0], True, (30, 24, 10))
        a = min(1.0, self.hint[1] / 0.6)
        box = pygame.Surface((t.get_width() + 32, t.get_height() + 18), pygame.SRCALPHA)
        box.fill((250, 214, 90, int(240 * a)))
        pygame.draw.rect(box, (120, 90, 20, int(255 * a)), box.get_rect(), 3)
        t.set_alpha(int(255 * a))
        box.blit(t, (16, 9))
        screen.blit(box, (w // 2 - box.get_width() // 2, 210))

    def _draw_compass(self, screen, f, w):
        cx, cy, r = w // 2, 62, 25
        dial = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        c = r + 4
        pygame.draw.circle(dial, (20, 22, 30, 230), (c, c), r + 3)
        pygame.draw.circle(dial, (196, 160, 70), (c, c), r + 3, 3)
        pygame.draw.circle(dial, (236, 228, 206), (c, c), r - 2)
        for k in range(8):
            a = k * math.pi / 4
            ln = 6 if k % 2 == 0 else 3
            p1 = (c + math.cos(a) * (r - 3), c + math.sin(a) * (r - 3))
            p2 = (c + math.cos(a) * (r - 3 - ln), c + math.sin(a) * (r - 3 - ln))
            pygame.draw.line(dial, (110, 100, 80), p1, p2, 2)
        a = self.compass.angle if self.compass.angle is not None else -math.pi / 2
        tip = (c + math.cos(a) * (r - 6), c + math.sin(a) * (r - 6))
        tail = (c - math.cos(a) * (r - 10), c - math.sin(a) * (r - 10))
        side = (math.cos(a + math.pi / 2) * 7, math.sin(a + math.pi / 2) * 7)
        pygame.draw.polygon(dial, (200, 50, 50), [tip, (c + side[0], c + side[1]), (c - side[0], c - side[1])])
        pygame.draw.polygon(dial, (60, 64, 80), [tail, (c + side[0], c + side[1]), (c - side[0], c - side[1])])
        pygame.draw.circle(dial, (196, 160, 70), (c, c), 4)
        screen.blit(dial, (cx - c, cy - c))
        metres = self.compass.steps * 2.5
        dist = f"{int(metres)} m" if metres < 1000 else f"{metres / 1000:.1f} km"
        t1 = f["label"].render(self.label(), True, (250, 240, 214))
        t2 = f["small"].render(dist + " walk", True, (200, 196, 180))
        bw = max(t1.get_width(), t2.get_width()) + 24
        box = pygame.Surface((bw, 44), pygame.SRCALPHA)
        box.fill((20, 22, 32, 205))
        box.blit(t1, ((bw - t1.get_width()) // 2, 5)); box.blit(t2, ((bw - t2.get_width()) // 2, 24))
        screen.blit(box, (cx - bw // 2, cy + r + 8))
        if self.obj == 0 and "newspaper" not in self.flags:
            t3 = f["small"].render("Optional: pick up the morning paper at Park Stores", True, (190, 186, 170))
            b3 = pygame.Surface((t3.get_width() + 20, 22), pygame.SRCALPHA); b3.fill((20, 22, 32, 170))
            b3.blit(t3, (10, 3))
            screen.blit(b3, (cx - b3.get_width() // 2, cy + r + 54))

    def _wrap(self, font, text, width):
        return documents.wrap(font, text, width)

    def _who(self, who):
        """Where the person speaking is (for the little marker over their head): (x, y) on screen, or None."""
        if not who:
            return None
        if self.scene is not None:
            a = self.scene.actors.get(who.lower())
            if a is None or not a.shown:
                return None
            ox, oy = self.scene.offset
            return a.x + ox, a.y + oy
        return None

    def _draw_cutscene(self, screen, f, w, h, view_offset):
        cs = self.cutscene
        bar = int(64 * cs.bars)
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, w, bar))
        pygame.draw.rect(screen, (0, 0, 0), (0, h - bar, w, bar))
        who, text = cs.line()[0], cs.line()[1]
        shown = text[:int(cs.shown)]
        bw = min(900, w - 60)
        narration = who == ""
        font = f["narr"] if narration else f["text"]
        lines = self._wrap(font, text, bw - 48)
        bh = 40 + len(lines) * (font.get_linesize() + 2) + (26 if not narration else 10)
        bx, by = (w - bw) // 2, h - bar - bh - 14
        # keep the box off the people talking
        feet = []
        if view_offset is not None:
            ox, oy = view_offset
            feet.append(self.player.pos.y + oy)
            for a in self.world.actors if self.world else []:
                if getattr(a, "talking", False):
                    feet.append(a.y + oy)
        elif self.scene is not None:
            ox, oy = self.scene.offset
            feet = [a.y + oy for a in self.scene.actors.values() if a.shown]
        if self.view is None and not self.black and feet and max(feet) > by - 10:
            by = bar + 26
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((14, 16, 24, 236) if not narration else (24, 20, 16, 230))
        col = S.SPEAKERS.get(who, (220, 220, 220))
        pygame.draw.rect(panel, col if not narration else (150, 130, 100), panel.get_rect(), 2)
        screen.blit(panel, (bx, by))
        yy = by + 16
        if not narration:
            tag = f["name"].render(who, True, (20, 20, 24))
            pygame.draw.rect(screen, col, (bx + 18, by - 12, tag.get_width() + 18, tag.get_height() + 6))
            screen.blit(tag, (bx + 27, by - 9))
            yy = by + 22
        left = len(shown)
        for ln in lines:                                   # type the line out
            part = ln[:max(0, left)]
            left -= len(ln) + 1
            if part:
                img = font.render(part, True, (236, 238, 244) if not narration else (232, 222, 200))
                x = bx + 24 if not narration else bx + (bw - font.size(ln)[0]) // 2
                screen.blit(img, (x, yy))
            yy += font.get_linesize() + 2
        if cs.shown >= len(text) and cs.auto is None and (int(cs.t * 2) % 2 == 0):
            more = "click to continue >" if cs.i < len(cs.lines) - 1 else "click to finish >"
            m = f["small"].render(more, True, (190, 186, 170))
            screen.blit(m, (bx + bw - m.get_width() - 14, by + bh - m.get_height() - 8))
        # a little marker over whoever's speaking
        pos = None
        if self.scene is not None:
            pos = self._who(who)
        elif view_offset is not None and who and self.view is None and not self.black:
            ox, oy = view_offset
            if who == "Detective":
                pos = (self.player.pos.x + ox, self.player.pos.y + oy)
            else:
                aid = {"Police Officer": "crime_officer", "Daniel": "crime_daniel"}.get(who)
                a = self._actor(aid) if aid else None
                if a is None:
                    a = self._actor(self.ids.get(who.lower(), "")) or (self._actor("daniel") if who == "Daniel" else None)
                if a is not None:
                    pos = (a.x + ox, a.y + oy)
        if pos is not None and not self.black and self.view is None:
            sx, sy = int(pos[0]), int(pos[1] - 112 + 4 * math.sin(cs.t * 5))
            pygame.draw.polygon(screen, (20, 20, 24), [(sx - 9, sy - 2), (sx + 9, sy - 2), (sx, sy + 10)])
            pygame.draw.polygon(screen, col, [(sx - 7, sy), (sx + 7, sy), (sx, sy + 8)])
