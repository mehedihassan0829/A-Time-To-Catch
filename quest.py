"""The story as you play it: where to go next, the compass that gets you there, cut scenes and the newspaper.

  - Objectives are in OBJECTIVES, in order. Each one is a place on a map (or a shop to walk into).
  - The compass at the top of the screen points along the shortest WALKING route to the objective: a
    breadth-first search over the tiles you can actually stand on (up, down, left, right - so it goes round
    buildings, the water and the police tape, never straight through them). When the objective's on another
    map it leads you to the way there (the edge of the map, the steps, the door you came in by).
  - Cut scenes are lists of lines (who's speaking, what they say) with a few stage directions mixed in.
    Click (or press E / Space / Enter) for the next line.
  - The newspaper: buy one at Park Stores on your way (optional).
"""
import math
from collections import deque
import pygame

TILE = 64

# ------------------------------------------------------------------ the story, in order
OBJECTIVES = [
    dict(id="crime_scene", label="Get to the crime scene at the harbourside", place="Harbourside", near="crime_officer"),
    dict(id="arcade", label="Go to the Bristol Arcade, where John worked", place="Harbourside", door=(29, 45), shop="arcade"),
]

INTRO = [
    ("", "Bristol. The next morning."),
    ("", "A body has been pulled out of the harbour. The call came last night - the detective is wanted at the scene."),
    ("", "Follow the compass at the top of the screen to the harbourside. Park Stores sells the morning papers, if you "
         "want one on the way."),
]

CRIME_SCENE = [
    ("", "The detective arrives at the crime scene. There are police officers, forensic investigators and a small "
         "cordoned-off area beside the water. John's body has already been removed, but the scene is still being investigated."),
    ("Detective", "What happened?", dict(face="crime_officer")),
    ("Police Officer", "John Harper died from drowning after being pushed into the harbourside river."),
    ("Detective", "Well, who's that over by the cordon strip?", dict(face="crime_daniel")),
    ("Police Officer", "Daniel Shaw. Journalist. He's been asking questions about the Bristol Pusher for a while. "
                       "Apparently, he knew the victim."),
    ("", "The detective approaches him.", dict(walk="approach", face="crime_daniel")),
    ("Detective", "Daniel Shaw?"),
    ("Daniel", "That's me. You're the detective investigating John?"),
    ("Detective", "You knew him?"),
    ("Daniel", "We spoke a few times. He contacted me about some research he was doing into Bristol's history. "
               "Old buildings, businesses, things that have disappeared over the years."),
    ("Detective", "What did that have to do with the Pusher?"),
    ("Daniel", "That's what I wondered. He started asking about the older cases, particularly the first one. "
               "He seemed convinced there was something people had overlooked."),
    ("Detective", "Did he tell you what he'd found?"),
    ("Daniel", "No. But he mentioned the arcade where he worked more than once. Might be worth looking into."),
    ("", "Daniel hands the detective his number.", dict(give="daniel_number")),
    ("Daniel", "Here's my number. Let me know if you find anything."),
    ("Detective", "I will."),
    ("", "Daniel walks away.", dict(leave="crime_daniel")),
]

NEWSPAPER_BUY = [
    ("Shopkeeper", "Morning. Paper? They're flying off the shelf today - have you seen the front page?"),
    ("Detective", "I'll take one.", dict(give="newspaper")),
]

SPEAKERS = {   # name -> (label colour, who it is in the world: "player" or an NPC id)
    "Detective": ((240, 196, 90), "player"),
    "Police Officer": ((120, 170, 255), "crime_officer"),
    "Daniel": ((130, 210, 140), "crime_daniel"),
    "Shopkeeper": ((230, 150, 120), "shopkeeper"),
}

DANIEL_NUMBER = "07700 900 417"

# ------------------------------------------------------------------ the morning paper
PAPER = dict(
    masthead="THE HARBOUR GAZETTE",
    dateline="SATURDAY 7 NOVEMBER 2026", price="90p",
    kicker="BODY FOUND IN THE FLOATING HARBOUR",
    headline="THE BRISTOL PUSHER IS BACK",
    standfirst="...and he will be gone as quick as he came",
    byline="By our crime reporter",
    body=[
        "A man found in the water beside the harbourside decks in the early hours of yesterday morning has been "
        "named locally as John Harper, 29, of Bristol.",
        "Police say Mr Harper drowned, and that they believe he was pushed. Officers have cordoned off part of the "
        "waterfront off Anchor Road while forensic teams examine the scene.",
        "It is the first death linked to the so-called Bristol Pusher in eleven years. The killer, who has never "
        "been caught, is thought to have claimed a first victim in the same harbour in 1999.",
        "Mr Harper worked at an arcade on the harbourside and is believed to have been walking home along the "
        "water after his shift. A colleague described him as \"a quiet lad, always reading up on old Bristol.\"",
        "Detectives are appealing for anyone who was near Anchor Road or the harbourside decks late on Thursday "
        "night to come forward.",
    ],
    caption="Police at the scene on the harbourside decks",
    inside=["Harbourside market back this weekend - p4", "Clifton Down: trains delayed again - p7",
            "Weather: drizzle, 11C"],
)


# ================================================================== the compass: shortest walking route
class Compass:
    def __init__(self):
        self.walk_cache = {}         # id(world) -> (world, (east, south)) where you can walk
        self.field_cache = {}        # (id(world), targets) -> distance grid
        self.angle = None
        self.steps = None
        self.final = None            # once you're there: which way to keep walking (into a door / off the map edge)

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
        """Steps from every tile to the nearest target, walking only up/down/left/right where the way is clear."""
        lk = self.links(world)
        INF = 1 << 30
        dist = [[INF] * world.w for _ in range(world.h)]
        q = deque()
        for x, y in targets:
            if 0 <= x < world.w and 0 <= y < world.h:
                dist[y][x] = 0; q.append((x, y))
        while q:
            x, y = q.popleft()
            d = dist[y][x] + 1
            for nx, ny in self.steps_from(world, lk, x, y):
                if dist[ny][nx] > d and (nx, ny) not in blocked:
                    dist[ny][nx] = d; q.append((nx, ny))
        return dist

    def field(self, world, targets):
        key = (id(world), targets)
        got = self.field_cache.get(key)
        if got is None:
            got = self.field_cache[key] = self.bfs(world, targets)
        return got

    def next_tile(self, world, dist, x, y):
        """One step along the route from (x, y), or None if you're there (or it's no use)."""
        best = None
        for nx, ny in self.steps_from(world, self.links(world), x, y):
            if dist[ny][nx] < dist[y][x] and (best is None or dist[ny][nx] < dist[best[1]][best[0]]):
                best = (nx, ny)
        return best

    def point(self, world, pos, targets, dt):
        """Update the needle: aim a few steps along the route from where you're standing."""
        if not targets:
            self.steps = None; return
        dist = self.field(world, targets)
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
        if best is None:
            self.steps = None; return
        self.steps, x, y = best
        for _ in range(4):                              # walk the route a few tiles ahead
            nxt = self.next_tile(world, dist, x, y) if dist[y][x] > 0 else None
            if nxt is None:
                break
            x, y = nxt
        aim = ((x + 0.5) * TILE - pos[0], (y + 0.6) * TILE - pos[1])
        if self.steps == 0 and self.final:
            want = {"right": 0.0, "down": math.pi / 2, "left": math.pi, "up": -math.pi / 2}[self.final]
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
    def __init__(self, lines, story, title=None):
        self.lines = lines
        self.story = story
        self.i = 0
        self.shown = 0.0                 # how much of the current line has been typed out
        self.t = 0.0
        self.bars = 0.0                  # the black bars sliding in
        self.walk_to = None
        self.walk_time = 0.0
        self.walk_stuck = 0.0
        self.walk_best = 1e9
        self.walk_field = None
        self.done = False
        self.title = title
        self._enter_line()

    def line(self):
        return self.lines[self.i]

    def _enter_line(self):
        ln = self.line()
        stage = ln[2] if len(ln) > 2 else {}
        self.shown = 0.0
        self.story.stage_direction(stage, self)

    def advance(self):
        if self.done:
            return
        text = self.line()[1]
        if self.shown < len(text):       # finish typing the line first
            self.shown = len(text); return
        if self.walk_to is not None:     # still walking: get there now
            self.story.snap_player(self.walk_to); self.walk_to = None
        self.i += 1
        if self.i >= len(self.lines):
            self.done = True
        else:
            self._enter_line()

    def update(self, dt):
        self.t += dt
        self.bars = min(1.0, self.bars + dt * 3)
        self.shown += dt * 55
        if self.walk_to is not None:
            self.walk_time += dt
            self.walk_stuck += dt

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
    def __init__(self, pocket, item_cls, icons):
        self.pocket = pocket
        self.Item = item_cls
        self.icons = icons                  # name -> icon function
        self.obj = 0
        self.cutscene = None
        self.reading_paper = False
        self.compass = Compass()
        self.flags = set()
        self.world = None
        self.player = None
        self.place = None
        self.places = {}
        self.face_after_walk = None
        self.toasts = []                    # [text, time left], shown one after another
        self.fonts = None
        self.paper_img = None
        self.cutscene = Cutscene(INTRO, self)

    # ---- what's going on
    @property
    def busy(self):
        """True while a cut scene or the newspaper has the screen (no walking about, no other keys)."""
        return self.cutscene is not None or self.reading_paper

    def say(self, text, secs):
        self.toasts.append([text, secs])

    def objective(self):
        return OBJECTIVES[self.obj] if self.obj < len(OBJECTIVES) else None

    def complete(self, toast=None):
        self.obj += 1
        nxt = self.objective()
        self.say(toast or (f"New objective: {nxt['label']}" if nxt else "To be continued..."), 5.0)
        self.compass.angle = None
        self.compass.steps = None

    # ---- each frame
    def update(self, dt, world, place, player, places):
        self.world, self.player, self.place, self.places = world, player, place, places
        if self.toasts and not self.busy:
            self.toasts[0][1] -= dt
            if self.toasts[0][1] <= 0:
                self.toasts.pop(0)
        for a in list(world.actors):                                  # Daniel walking off along the water
            if getattr(a, "leaving", False):
                a.talking = False; a.moving = True
                if a.y < a.leave_y:
                    a.y = min(a.leave_y, a.y + 60 * dt); a.d = "down"
                else:
                    a.x -= 72 * dt; a.d = "left"
                if a.x < a.leave_x:
                    world.actors.remove(a)
        if self.cutscene:
            self.cutscene.update(dt)
            if self.cutscene.done:
                self._end_cutscene()
            return
        if "daniel_left" in self.flags and world.interior is None:   # Daniel's gone (even if the map's rebuilt)
            world.actors = [a for a in world.actors if a.id != "crime_daniel" or getattr(a, "leaving", False)]
        ob = self.objective()
        if ob is None:
            self.compass.steps = None
            return
        if ob["id"] == "crime_scene" and place == ob["place"] and world.interior is None:
            cs = getattr(world._map_def, "CRIME_SCENE", None)
            officer = self._actor("crime_officer")
            if cs and officer and math.hypot(player.pos.x - officer.x, player.pos.y - officer.y) < cs["trigger"] * TILE:
                self.compass.steps = None
                self.start(CRIME_SCENE)
                return
        at_door = False
        if ob.get("door") and place == ob["place"] and world.interior is None:
            dx, dy = ob["door"]
            at_door = math.hypot(player.pos.x - (dx + 0.5) * TILE, player.pos.y - (dy + 1.4) * TILE) < 0.9 * TILE
        if at_door or (ob.get("shop") and world.interior is not None and world.interior.get("kind") == ob["shop"]
                       and place == ob["place"]):
            self.complete("You've reached the Bristol Arcade. To be continued...")
            return
        self.compass.point(world, (player.pos.x, player.pos.y), self.targets(world, place, places), dt)

    def targets(self, world, place, places):
        """The tiles the compass is heading for, on the map you're on now."""
        ob = self.objective()
        self.compass.final = None
        if ob is None:
            return ()
        if world.interior is not None:                  # in a shop: back out the door first
            self.compass.final = "down"
            if world.exit_tile:
                return (tuple(world.exit_tile),)
            return ()
        if place != ob["place"]:                        # another map: head for the way there
            hop = self._next_hop(place, ob["place"], places)
            out = []
            for pt in world.portals:
                if pt.get("to") == hop:
                    self.compass.final = pt.get("dir", "up")
                    a = pt["area"]
                    for ty in range(a.top // TILE, (a.bottom - 1) // TILE + 1):
                        for tx in range(a.left // TILE, (a.right - 1) // TILE + 1):
                            out.append((tx, ty))
            return tuple(out)
        if ob.get("near"):
            a = self._actor(ob["near"])
            if a is None:
                return ()
            cx, cy = int(a.x // TILE), int(a.y // TILE)
            return tuple((cx + dx, cy + dy) for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2) if abs(dx) + abs(dy) <= 2)
        if ob.get("door"):
            dx, dy = ob["door"]
            self.compass.final = "up"
            return ((dx, dy + 1),)
        return ()

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
    def start(self, lines):
        if self.pocket.reading:
            self.pocket.close_notebook()
        self.pocket.open = False
        self.cutscene = Cutscene(lines, self)

    def route(self, gx, gy):
        """Steps to (gx, gy) from every tile, going round walls AND the people standing about."""
        w = self.world
        blocked = {(int(a.x // TILE), int(a.y // TILE)) for a in w.actors} - {(gx, gy)}
        return self.compass.bfs(w, ((gx, gy),), blocked)

    def _end_cutscene(self):
        lines = self.cutscene.lines
        self.cutscene = None
        for a in (self.world.actors if self.world else []):
            a.talking = False
        if lines is CRIME_SCENE:
            self.complete()
        elif lines is NEWSPAPER_BUY:
            self.open_paper()

    def stage_direction(self, stage, cs):
        if not stage:
            return
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
        if stage.get("give") == "daniel_number":
            self.flags.add("daniel_number")
            self.pocket.add(self.Item("daniel_number", "Daniel's number",
                                      f"Daniel Shaw, journalist. {DANIEL_NUMBER}. He knew John Harper.", self.icons["card"]))
            nb = self.pocket.notebook
            if DANIEL_NUMBER not in "".join(nb.pages):
                note = f"Daniel Shaw (journalist) - {DANIEL_NUMBER}. Knew John Harper. Said look at the arcade."
                nb.page = len(nb.pages) - 1
                nb.type(("\n" if nb.pages[nb.page].strip() else "") + note)
                nb.save()
            self.say("Daniel's number is in your pocket (and your notebook)", 4.0)
        if stage.get("give") == "newspaper":
            self.flags.add("newspaper")
            it = self.Item("newspaper", "Newspaper", "The Harbour Gazette. THE BRISTOL PUSHER IS BACK. Enter to read it.",
                           self.icons["newspaper"])
            it.use = self.open_paper
            self.pocket.add(it)
        if stage.get("leave"):
            a = self._actor(stage["leave"])
            if a is not None:
                a.leaving = True
                a.leave_y = min(self.world.pixel_h - 24, a.y + 0.8 * TILE)   # step down past the detective...
                a.leave_x = a.x - 14 * TILE                                    # ...then off along the water
                a.behaviour = "stand"
            self.flags.add("daniel_left")

    def face_player(self, aid):
        """Turn the detective (and whoever they're talking to) to face each other."""
        a = self._actor(aid)
        if a is None or self.player is None:
            return
        dx, dy = a.x - self.player.pos.x, a.y - self.player.pos.y
        self.player.direction = ("right" if dx > 0 else "left") if abs(dx) > abs(dy) else ("down" if dy > 0 else "up")
        a.d = ("left" if dx > 0 else "right") if abs(dx) > abs(dy) else ("up" if dy > 0 else "down")
        a.talking = True

    def snap_player(self, pos):
        self.player.pos.update(pos); self.player.prev_pos.update(pos)

    def keys(self, player):
        return self.cutscene.keys(player) if self.cutscene else ScriptKeys()

    # ---- buying the paper
    def can_buy_paper(self, world, place, player):
        if "newspaper" in self.flags or world.interior is None or world.interior.get("kind") != "corner":
            return False
        for a in world.actors:                                  # standing by the shopkeeper / the counter
            if a.id.endswith("staff") and math.hypot(player.pos.x - a.x, player.pos.y - a.y) < 2.2 * TILE:
                return True
        tx, ty = int(player.pos.x // TILE), int(player.pos.y // TILE)
        return any(world.at(tx + dx, ty + dy, " ") in "XQ" for dx in (-1, 0, 1) for dy in (-1, 0, 1))

    def buy_paper(self, world):
        for a in world.actors:
            if a.id.endswith("staff"):
                a.talking = True
                SPEAKERS["Shopkeeper"] = (SPEAKERS["Shopkeeper"][0], a.id)
        self.start(NEWSPAPER_BUY)

    def open_paper(self):
        self.reading_paper = True

    # ---- input
    def handle(self, ev):
        """Called with every event while busy. Returns 'quit' if the window was closed."""
        if ev.type == pygame.QUIT:
            return "quit"
        advance = (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1) or \
                  (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN))
        if self.reading_paper:
            if advance or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                self.reading_paper = False
            return None
        if self.cutscene and advance:
            self.cutscene.advance()
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
        if self.cutscene:
            self._draw_cutscene(screen, f, w, h, view_offset)
        elif self.objective() and self.compass.steps is not None:
            self._draw_compass(screen, f, w)
        if self.toasts and not self.busy:
            t = f["label"].render(self.toasts[0][0], True, (250, 236, 200))
            a = min(1.0, self.toasts[0][1] / 0.6)
            box = pygame.Surface((t.get_width() + 28, t.get_height() + 14), pygame.SRCALPHA)
            box.fill((20, 22, 32, int(220 * a)))
            pygame.draw.rect(box, (200, 170, 90, int(255 * a)), box.get_rect(), 2)
            t.set_alpha(int(255 * a))
            box.blit(t, (14, 7))
            screen.blit(box, (w // 2 - box.get_width() // 2, 168))
        if self.reading_paper:
            self._draw_paper(screen, w, h)

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
        ob = self.objective()
        metres = self.compass.steps * 2.5
        dist = f"{int(metres)} m" if metres < 1000 else f"{metres / 1000:.1f} km"
        t1 = f["label"].render(ob["label"], True, (250, 240, 214))
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
        words, lines, cur = text.split(), [], ""
        for wd in words:
            if font.size((cur + " " + wd).strip())[0] > width:
                lines.append(cur); cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            lines.append(cur)
        return lines

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
        ox, oy = view_offset                               # keep the box off the people talking
        feet = [self.player.pos.y + oy] if self.player is not None else []
        for aid in ("crime_officer", "crime_daniel"):
            a = self._actor(aid)
            if a is not None and getattr(a, "talking", False):
                feet.append(a.y + oy)
        if feet and max(feet) > by - 10:
            by = bar + 26
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((14, 16, 24, 236) if not narration else (24, 20, 16, 230))
        col = SPEAKERS.get(who, ((220, 220, 220), None))[0]
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
        if cs.shown >= len(text) and (int(cs.t * 2) % 2 == 0):
            more = "click to continue >" if cs.i < len(cs.lines) - 1 else "click to finish >"
            m = f["small"].render(more, True, (190, 186, 170))
            screen.blit(m, (bx + bw - m.get_width() - 14, by + bh - m.get_height() - 8))
        # a little marker over whoever's speaking
        tgt = SPEAKERS.get(who, (None, None))[1]
        if tgt:
            ox, oy = view_offset
            if tgt == "player":
                px, py = self.player.pos.x, self.player.pos.y
            else:
                a = self._actor(tgt)
                px, py = (a.x, a.y) if a else (None, None)
            if px is not None:
                sx, sy = int(px + ox), int(py + oy - 112 + 4 * math.sin(cs.t * 5))
                pygame.draw.polygon(screen, (20, 20, 24), [(sx - 9, sy - 2), (sx + 9, sy - 2), (sx, sy + 10)])
                pygame.draw.polygon(screen, col, [(sx - 7, sy), (sx + 7, sy), (sx, sy + 8)])

    # ---- the newspaper, full screen
    def _paper(self, w, h):
        if self.paper_img is not None and self.paper_img.get_size() == (min(980, w - 60), min(680, h - 40)):
            return self.paper_img
        W, H = min(980, w - 60), min(680, h - 40)
        s = pygame.Surface((W, H))
        s.fill((238, 232, 214))
        ink = (28, 26, 24)
        serif = lambda n, b=False, i=False: pygame.font.SysFont("georgia,times new roman,serif", n, bold=b, italic=i)
        mast = serif(48, True).render(PAPER["masthead"], True, ink)
        s.blit(mast, (W // 2 - mast.get_width() // 2, 14))
        pygame.draw.line(s, ink, (24, 74), (W - 24, 74), 3)
        dl = serif(15).render(PAPER["dateline"], True, ink)
        pr = serif(15).render(PAPER["price"], True, ink)
        s.blit(dl, (26, 80)); s.blit(pr, (W - 26 - pr.get_width(), 80))
        pygame.draw.line(s, ink, (24, 102), (W - 24, 102), 1)
        kk = serif(17, True).render(PAPER["kicker"], True, (150, 30, 30))
        s.blit(kk, (26, 112))
        hfont = serif(64, True)
        hl = hfont.render(PAPER["headline"], True, ink)
        if hl.get_width() > W - 48:
            hl = pygame.transform.smoothscale(hl, (W - 48, int(hl.get_height() * (W - 48) / hl.get_width())))
        s.blit(hl, (24, 134))
        y = 134 + hl.get_height() + 4
        sf = serif(26, False, True).render(PAPER["standfirst"], True, (60, 56, 52))
        s.blit(sf, (26, y)); y += sf.get_height() + 10
        pygame.draw.line(s, ink, (24, y), (W - 24, y), 1); y += 10
        # the photo: the scene on the decks, in newsprint grey
        pw, ph = int(W * 0.42), int((H - y - 30) * 0.62)
        photo = pygame.Surface((pw, ph))
        photo.fill((120, 124, 128))
        for k in range(0, ph, 6):                                  # the water
            pygame.draw.line(photo, (98 + (k * 7) % 20, 102 + (k * 7) % 20, 106 + (k * 7) % 20), (0, k), (pw, k), 3)
        deck = int(pw * 0.42)
        pygame.draw.rect(photo, (160, 156, 148), (0, 0, deck, ph))
        for k in range(0, ph, 10):
            pygame.draw.line(photo, (130, 126, 118), (0, k), (deck, k), 1)
        ty_ = int(ph * 0.3)
        pygame.draw.line(photo, (230, 230, 230), (0, ty_), (pw, ty_ - 8), 3)          # the tape
        for k in range(0, pw, 14):
            pygame.draw.line(photo, (60, 60, 60), (k, ty_ - k * 8 // pw), (k + 6, ty_ - (k + 6) * 8 // pw), 3)
        for px_ in (int(pw * 0.1), int(pw * 0.55)):
            pygame.draw.line(photo, (40, 40, 40), (px_, ty_ - 6), (px_, ty_ + 40), 3)
        for fx, fy in ((int(pw * 0.25), int(ph * 0.62)), (int(pw * 0.33), int(ph * 0.58))):   # figures
            pygame.draw.rect(photo, (230, 230, 230), (fx - 6, fy - 26, 12, 26))
            pygame.draw.circle(photo, (230, 230, 230), (fx, fy - 30), 6)
        pygame.draw.rect(photo, (210, 210, 210), (int(pw * 0.05), int(ph * 0.42), int(pw * 0.18), int(ph * 0.22)))   # tent
        for yy in range(0, ph, 3):                                 # halftone-ish
            for xx in range((yy // 3) % 2 * 2, pw, 4):
                c = photo.get_at((xx, yy))
                photo.set_at((xx, yy), (max(0, c.r - 22), max(0, c.g - 22), max(0, c.b - 22)))
        pygame.draw.rect(photo, ink, photo.get_rect(), 2)
        s.blit(photo, (26, y))
        cap = serif(13, False, True)
        cy_ = y + ph + 4
        for ln in self._wrap(cap, PAPER["caption"], pw):
            s.blit(cap.render(ln, True, (60, 56, 52)), (26, cy_)); cy_ += 16
        # the story, in two columns beside the photo, then across the bottom
        body = serif(16)
        by_ = serif(14, True).render(PAPER["byline"], True, ink)
        colx = 26 + pw + 22
        s.blit(by_, (colx, y)); yy = y + 22
        colw = W - colx - 26
        paras = [self._wrap(body, p_, colw) for p_ in PAPER["body"]]
        x0, maxy = colx, H - 70
        for lines in paras:
            for ln in lines:
                if yy > maxy:
                    break
                s.blit(body.render(ln, True, ink), (x0, yy)); yy += 20
            yy += 6
        pygame.draw.line(s, ink, (24, H - 56), (W - 24, H - 56), 1)
        ins = serif(14, True).render("INSIDE:", True, (150, 30, 30))
        s.blit(ins, (26, H - 46))
        xx = 26 + ins.get_width() + 10
        for item in PAPER["inside"]:
            t = serif(14).render(item, True, ink)
            s.blit(t, (xx, H - 46)); xx += t.get_width() + 24
        hint = serif(13, False, True).render("click to put the paper away", True, (90, 86, 80))
        s.blit(hint, (W - 26 - hint.get_width(), H - 24))
        pygame.draw.rect(s, (180, 172, 150), s.get_rect(), 3)
        self.paper_img = s
        return s

    def _draw_paper(self, screen, w, h):
        dim = pygame.Surface((w, h), pygame.SRCALPHA); dim.fill((0, 0, 0, 170))
        screen.blit(dim, (0, 0))
        p = self._paper(w, h)
        screen.blit(p, (w // 2 - p.get_width() // 2, h // 2 - p.get_height() // 2))
