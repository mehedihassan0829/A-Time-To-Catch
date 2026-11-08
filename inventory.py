"""Your pocket (a small inventory for little things) and the notebook you can write in.

  I        open / close your pocket.  Left/Right (or A/D) to choose, Enter or E to use.
  N        open the notebook straight away.
  F        flick your lighter on / off (a little light to see by at night).
  In the notebook: just type. Enter = new line, Backspace = delete,
  Page Up / Page Down (or Ctrl + Left/Right) = turn the page, Esc = close.
The notebook is saved to saves/notebook.json next to the game, so it's still there next time.
"""
import json, time
from pathlib import Path
import pygame
import pixel_art as pa
import daynight

POCKET_SLOTS = 8
PAPER, PAPER_D, INK, LINE, RED = (244, 236, 214), (214, 204, 178), (40, 36, 60), (176, 196, 220), (200, 90, 90)


class Item:
    def __init__(self, item_id, name, description, icon_fn):
        self.id, self.name, self.description = item_id, name, description
        self.icon = icon_fn()
        self.use = None              # what Enter does with it in the pocket (None = nothing)


class Notebook:
    LINES_PER_PAGE = 13
    CHARS_PER_LINE = 34

    def __init__(self, save_dir):
        self.path = Path(save_dir) / "notebook.json"
        self.pages = [""]
        self.page = 0
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.pages = data.get("pages") or [""]
            self.page = min(data.get("page", 0), len(self.pages) - 1)
        except (OSError, ValueError):
            pass
        self.dirty = False
        self.last_save = 0.0
        self.measure = None          # font.size, set once the notebook font exists (wraps by real width)
        self.max_w = 470

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"pages": self.pages, "page": self.page}, indent=1), encoding="utf-8")
            self.dirty = False
        except OSError as e:
            print("Couldn't save the notebook:", e)

    # wrap text into the page's lines
    def layout(self, text):
        out = []
        for para in text.split("\n"):
            line = ""
            for word in para.split(" "):
                while len(word) > self.CHARS_PER_LINE:
                    if line: out.append(line); line = ""
                    out.append(word[:self.CHARS_PER_LINE]); word = word[self.CHARS_PER_LINE:]
                cand = f"{line} {word}" if line else word
                too_wide = (self.measure(cand)[0] > self.max_w) if self.measure else len(cand) > self.CHARS_PER_LINE
                if too_wide and line:
                    out.append(line); line = word
                else:
                    line = f"{line} {word}" if line else word
            out.append(line)
        return out

    def type(self, text):
        page = self.pages[self.page] + text
        if len(self.layout(page)) > self.LINES_PER_PAGE:            # page full: carry on over the page
            if self.page == len(self.pages) - 1:
                self.pages.append("")
            self.page += 1
            self.pages[self.page] = text.lstrip("\n") + self.pages[self.page]
        else:
            self.pages[self.page] = page
        self.dirty = True

    def backspace(self):
        if self.pages[self.page]:
            self.pages[self.page] = self.pages[self.page][:-1]
        elif self.page > 0:
            if self.page == len(self.pages) - 1:
                self.pages.pop()
            self.page -= 1
        self.dirty = True

    def turn(self, step):
        self.page = max(0, self.page + step)
        while self.page >= len(self.pages):
            self.pages.append("")
        while len(self.pages) > 1 and self.pages[-1] == "" and self.page < len(self.pages) - 1:
            self.pages.pop()
        self.dirty = True


class Pocket:
    def __init__(self, save_dir):
        self.notebook = Notebook(save_dir)
        self.items = [Item("notebook", "Notebook", "A battered little notebook. Press Enter to write in it.", pa.notebook_icon),
                      Item("lighter", "Lighter", "A cheap red lighter. Enter (or F) to flick it on or off - a little light in the dark.",
                           daynight.lighter_icon),
                      Item("watch", "Watch", "Your wristwatch. The time's always on it, top right of the screen.", daynight.watch_icon)]
        self.lighter_on = False
        self.open = False            # pocket panel showing
        self.reading = False         # notebook open
        self.sel = 0
        self.font = None
        self.small = None
        self.blink = 0.0

    @property
    def busy(self):
        """True while the pocket or notebook is open (the player shouldn't walk about)."""
        return self.open or self.reading

    def add(self, item):
        if len(self.items) < POCKET_SLOTS:
            self.items.append(item); return True
        return False

    def open_notebook(self):
        self.open = False
        self.reading = True
        pygame.key.start_text_input()

    def close_notebook(self):
        self.reading = False
        pygame.key.stop_text_input()
        self.notebook.save()

    def handle(self, ev):
        """Returns True if the event was used here."""
        if self.reading:
            nb = self.notebook
            if ev.type == pygame.TEXTINPUT:
                nb.type(ev.text); return True
            if ev.type == pygame.KEYDOWN:
                ctrl = ev.mod & pygame.KMOD_CTRL
                if ev.key == pygame.K_ESCAPE: self.close_notebook()
                elif ev.key == pygame.K_RETURN: nb.type("\n")
                elif ev.key == pygame.K_BACKSPACE: nb.backspace()
                elif ev.key == pygame.K_PAGEDOWN or (ctrl and ev.key == pygame.K_RIGHT): nb.turn(1)
                elif ev.key == pygame.K_PAGEUP or (ctrl and ev.key == pygame.K_LEFT): nb.turn(-1)
                elif ev.key == pygame.K_TAB: nb.type("    ")
                return True
            return ev.type in (pygame.KEYUP,)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_i:
                self.open = not self.open; return True
            if ev.key == pygame.K_n:
                self.open_notebook(); return True
            if ev.key == pygame.K_f and any(it.id == "lighter" for it in self.items):
                self.lighter_on = not self.lighter_on; return True
            if self.open:
                if ev.key in (pygame.K_ESCAPE,):
                    self.open = False
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    self.sel = (self.sel - 1) % POCKET_SLOTS
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.sel = (self.sel + 1) % POCKET_SLOTS
                elif ev.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
                    if self.sel < len(self.items) and self.items[self.sel].id == "notebook":
                        self.open_notebook()
                    elif self.sel < len(self.items) and self.items[self.sel].id == "lighter":
                        self.lighter_on = not self.lighter_on; self.open = False
                    elif self.sel < len(self.items) and getattr(self.items[self.sel], "use", None):
                        self.open = False                              # e.g. read the newspaper again
                        self.items[self.sel].use()
                return True
        return False

    def update(self, dt):
        self.blink += dt
        nb = self.notebook
        if nb.dirty and time.time() - nb.last_save > 3:              # autosave every few seconds while writing
            nb.save(); nb.last_save = time.time()

    # ------------------------------------------------------------ drawing
    def _fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont("segoe print,comic sans ms,bradley hand,consolas,monospace", 18)
            self.small = pygame.font.SysFont("consolas,menlo,monospace", 14)
            self.notebook.measure = self.font.size

    def draw(self, screen):
        self._fonts()
        w, h = screen.get_size()
        if self.open:
            self._draw_pocket(screen, w, h)
        if self.reading:
            self._draw_notebook(screen, w, h)

    def _draw_pocket(self, screen, w, h):
        slot = 64
        pw = POCKET_SLOTS * (slot + 8) + 24
        ph = slot + 76
        x0, y0 = (w - pw) // 2, h - ph - 70
        denim, denim_d, stitch = (52, 76, 120), (34, 50, 86), (226, 170, 80)
        pygame.draw.rect(screen, denim_d, (x0 - 4, y0 - 4, pw + 8, ph + 8))
        pygame.draw.rect(screen, denim, (x0, y0, pw, ph))
        for x in range(x0 + 6, x0 + pw - 6, 12):                     # stitching round the pocket
            pygame.draw.rect(screen, stitch, (x, y0 + 6, 6, 2)); pygame.draw.rect(screen, stitch, (x, y0 + ph - 8, 6, 2))
        title = self.small.render("POCKET   (I to close, Enter to use)", True, (236, 236, 240))
        screen.blit(title, (x0 + 12, y0 + 12))
        for i in range(POCKET_SLOTS):
            sx, sy = x0 + 12 + i * (slot + 8), y0 + 34
            pygame.draw.rect(screen, denim_d, (sx, sy, slot, slot))
            if i == self.sel:
                pygame.draw.rect(screen, stitch, (sx - 3, sy - 3, slot + 6, slot + 6), 3)
            if i < len(self.items):
                ic = self.items[i].icon
                screen.blit(ic, (sx + (slot - ic.get_width()) // 2, sy + (slot - ic.get_height()) // 2))
        if self.sel < len(self.items):
            it = self.items[self.sel]
            txt = self.small.render(f"{it.name} - {it.description}", True, (236, 236, 240))
        else:
            txt = self.small.render("(empty)", True, (170, 180, 200))
        screen.blit(txt, (x0 + 12, y0 + ph - 30))

    def _draw_notebook(self, screen, w, h):
        nb = self.notebook
        dim = pygame.Surface((w, h), pygame.SRCALPHA); dim.fill((0, 0, 0, 120)); screen.blit(dim, (0, 0))
        bw, bh = 560, 520
        x0, y0 = (w - bw) // 2, (h - bh) // 2
        pygame.draw.rect(screen, (90, 30, 30), (x0 - 14, y0 - 14, bw + 28, bh + 28))           # leather cover
        pygame.draw.rect(screen, (120, 44, 40), (x0 - 10, y0 - 10, bw + 20, bh + 20))
        pygame.draw.rect(screen, PAPER_D, (x0 + 4, y0 + 4, bw, bh))
        pygame.draw.rect(screen, PAPER, (x0, y0, bw, bh))
        top = y0 + 56
        lh = 32
        for i in range(nb.LINES_PER_PAGE + 1):
            pygame.draw.rect(screen, LINE, (x0 + 10, top + i * lh + lh - 4, bw - 20, 2))
        pygame.draw.rect(screen, RED, (x0 + 52, y0 + 8, 2, bh - 16))  # margin
        for k in range(10):                                           # spiral rings
            pygame.draw.circle(screen, (150, 150, 156), (x0 + 18, y0 + 30 + k * 50), 7, 3)
        head = self.small.render(f"NOTEBOOK   page {nb.page + 1} of {len(nb.pages)}", True, (120, 90, 80))
        screen.blit(head, (x0 + 64, y0 + 16))
        lines = nb.layout(nb.pages[nb.page])
        for i, line in enumerate(lines[:nb.LINES_PER_PAGE]):
            screen.blit(self.font.render(line, True, INK), (x0 + 64, top + i * lh + 2))
        if int(self.blink * 2) % 2 == 0:                              # blinking cursor
            last = lines[min(len(lines), nb.LINES_PER_PAGE) - 1] if lines else ""
            cx = x0 + 64 + self.font.size(last)[0] + 2
            cy = top + (min(len(lines), nb.LINES_PER_PAGE) - 1) * lh + 4
            pygame.draw.rect(screen, INK, (cx, cy, 2, 22))
        tip = self.small.render("Type to write  |  Enter new line  |  PgUp/PgDn turn page  |  Esc close", True, (236, 236, 240))
        screen.blit(tip, ((w - tip.get_width()) // 2, y0 + bh + 22))
