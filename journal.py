"""The detective's case journal: the suspects' faces and names, crossed off once you've spoken to them, with a short
note under each. It opens by itself after the police officer at the crime scene ("These will be the suspects you are
investigating.") and again every time you meet one of them (the meet= stage direction in quest_script.py). It's in
your pocket too: J, or Enter on it in the pocket.

  Arrows / Tab / click    choose a suspect
  type                    write a note under them (Backspace deletes)
  Enter / click the box   cross them off (only once you've spoken to them)
  Esc                     close
"""
import pygame
import people
from pixel_art import canvas, R, P, up, add_outline

NOTE_MAX = 110                      # notes are meant to be short
PAPER, PAPER_D, INK, RULE = (244, 236, 214), (214, 204, 178), (40, 36, 60), (196, 186, 160)
RED, GOLD, GREEN, GREY = (190, 40, 40), (200, 160, 70), (60, 130, 70), (140, 130, 116)


def journal_icon():
    """A brown leather journal with a strap (for the pocket)."""
    s = canvas(12, 14)
    R(s, (84, 56, 34), 1, 0, 10, 14); R(s, (110, 76, 46), 2, 0, 9, 1)
    R(s, (236, 226, 200), 10, 1, 1, 12)                              # the page edges
    R(s, (40, 30, 22), 1, 6, 10, 2)                                  # the strap
    P(s, (220, 190, 100), 9, 6); P(s, (220, 190, 100), 9, 7)         # the clasp
    return up(add_outline(s)).convert_alpha()


class Journal:
    def __init__(self, suspects):
        self.suspects = [dict(s, met=False, crossed=False, notes="") for s in suspects]
        self.open = False
        self.sel = 0
        self.message = ""
        self.flash = None                 # [text, until (ms)]
        self.fonts = None
        self.faces = {}
        self.rects = []                   # per suspect: (card, cross-off box)
        self.close_rect = None

    # ---- the story
    def index(self, sid):
        for i, s in enumerate(self.suspects):
            if s["id"] == sid:
                return i
        return None

    def name(self, sid):
        i = self.index(sid)
        return self.suspects[i]["name"] if i is not None else sid

    def met(self, sid):
        i = self.index(sid)
        return i is not None and self.suspects[i]["met"]

    def meet(self, sid):
        i = self.index(sid)
        if i is not None:
            self.suspects[i]["met"] = True

    def show(self, message="", focus=None):
        self.open = True
        self.message = message
        i = self.index(focus) if focus else None
        if i is not None:
            self.sel = i
        pygame.key.start_text_input()

    def close(self):
        self.open = False
        pygame.key.stop_text_input()

    # ---- input
    def _rows(self):
        return max(1, (len(self.suspects) + 1) // 2)

    def _say(self, text, secs=2.5):
        self.flash = [text, pygame.time.get_ticks() + int(secs * 1000)]

    def toggle(self, i):
        s = self.suspects[i]
        if not s["met"] and not s["crossed"]:
            self._say(f"You haven't spoken to {s['name']} yet.")
            return
        s["crossed"] = not s["crossed"]

    def handle(self, ev):
        """Returns True if the event was used (while it's open, everything is)."""
        n = len(self.suspects)
        if ev.type == pygame.TEXTINPUT:
            s = self.suspects[self.sel]
            text = ev.text.replace("\n", " ")
            if len(s["notes"]) + len(text) <= NOTE_MAX:
                s["notes"] += text
            else:
                self._say("Keep it short - there's only room for a line or two.")
            return True
        if ev.type == pygame.KEYDOWN:
            rows = self._rows()
            k = ev.key
            if k == pygame.K_ESCAPE:
                self.close()
            elif k == pygame.K_BACKSPACE:
                s = self.suspects[self.sel]
                s["notes"] = s["notes"][:-1]
            elif k == pygame.K_RETURN:
                self.toggle(self.sel)
            elif k == pygame.K_TAB:
                self.sel = (self.sel + 1) % n
            elif k == pygame.K_UP:
                self.sel = max(0, self.sel - 1)
            elif k == pygame.K_DOWN:
                self.sel = min(n - 1, self.sel + 1)
            elif k == pygame.K_LEFT:
                self.sel = max(0, self.sel - rows) if self.sel >= rows else self.sel
            elif k == pygame.K_RIGHT:
                self.sel = min(n - 1, self.sel + rows) if self.sel + rows < n else self.sel
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.close_rect and self.close_rect.collidepoint(ev.pos):
                self.close()
                return True
            for i, (card, box) in enumerate(self.rects):
                if box.collidepoint(ev.pos):
                    self.sel = i
                    self.toggle(i)
                elif card.collidepoint(ev.pos):
                    self.sel = i
            return True
        return ev.type in (pygame.KEYUP, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL)

    # ---- drawing
    def _fonts(self):
        if self.fonts is None:
            self.fonts = dict(
                head=pygame.font.SysFont("georgia,times new roman,serif", 24, italic=True),
                name=pygame.font.SysFont("georgia,times new roman,serif", 21, bold=True),
                small=pygame.font.SysFont("consolas,menlo,monospace", 14),
                label=pygame.font.SysFont("consolas,menlo,monospace", 14, bold=True),
                hand=pygame.font.SysFont("segoe print,comic sans ms,bradley hand,consolas,monospace", 16),
            )
        return self.fonts

    def face(self, look, size):
        """Head and shoulders of a suspect, like a photo pinned in the journal."""
        key = (look, size)
        got = self.faces.get(key)
        if got is None:
            img = people.person(people.SUSPECTS[look], "down", 0, "stand")
            bb = img.get_bounding_rect()
            crop = pygame.Rect(bb.x - 4, bb.y - 2, bb.w + 8, min(bb.h, bb.w + 8)).clip(img.get_rect())
            head = pygame.transform.scale(img.subsurface(crop), (size, size * crop.h // max(1, crop.w)))
            got = pygame.Surface((size, size))
            got.fill((206, 192, 160))
            got.blit(head, (0, size - head.get_height() + 6))
            self.faces[key] = got
        return got

    @staticmethod
    def _wrap(font, text, width):
        out, line = [], ""
        for word in text.split(" "):
            cand = f"{line} {word}" if line else word
            if font.size(cand)[0] > width and line:
                out.append(line); line = word
            else:
                line = cand
        out.append(line)
        return out

    def draw(self, screen):
        f = self._fonts()
        w, h = screen.get_size()
        dim = pygame.Surface((w, h), pygame.SRCALPHA); dim.fill((0, 0, 0, 150)); screen.blit(dim, (0, 0))
        bw, bh = min(1040, w - 40), min(620, h - 50)
        x0, y0 = (w - bw) // 2, (h - bh) // 2 - 6
        pygame.draw.rect(screen, (60, 40, 26), (x0 - 14, y0 - 14, bw + 28, bh + 28), border_radius=8)   # leather
        pygame.draw.rect(screen, (84, 56, 34), (x0 - 10, y0 - 10, bw + 20, bh + 20), border_radius=6)
        pygame.draw.rect(screen, PAPER_D, (x0 + 4, y0 + 4, bw, bh))
        pygame.draw.rect(screen, PAPER, (x0, y0, bw, bh))
        mid = x0 + bw // 2
        for k in range(8):                                                       # the spine's shadow
            pygame.draw.line(screen, (226 - k * 4, 216 - k * 4, 192 - k * 4), (mid - 8 + k, y0), (mid - 8 + k, y0 + bh))
            pygame.draw.line(screen, (226 - k * 4, 216 - k * 4, 192 - k * 4), (mid + 8 - k, y0), (mid + 8 - k, y0 + bh))
        head = f["head"].render(self.message or "Suspects", True, INK)
        screen.blit(head, (mid - head.get_width() // 2, y0 + 14))
        c = f["label"].render("x close", True, (120, 90, 80))
        self.close_rect = c.get_rect(topright=(x0 + bw - 14, y0 + 10)).inflate(10, 6)
        screen.blit(c, (self.close_rect.x + 5, self.close_rect.y + 3))
        top = y0 + 56
        rows = self._rows()
        page_w = bw // 2 - 40
        card_h = (bh - (top - y0) - 40) // rows
        self.rects = []
        blink = (pygame.time.get_ticks() // 500) % 2 == 0
        for i, s in enumerate(self.suspects):
            col, row = divmod(i, rows)
            cx = x0 + 20 + col * (bw // 2 + 4)
            cy = top + row * card_h
            card = pygame.Rect(cx, cy, page_w, card_h - 12)
            if i == self.sel:
                pygame.draw.rect(screen, (250, 244, 226), card)
                pygame.draw.rect(screen, GOLD, card, 3)
            else:
                pygame.draw.rect(screen, RULE, card, 1)
            size = min(104, card.h - 70)
            face = self.face(s["look"], size)
            fx, fy = card.x + 12, card.y + 12
            pygame.draw.rect(screen, (250, 250, 246), (fx - 5, fy - 5, size + 10, size + 10))   # the photo's border
            screen.blit(face, (fx, fy))
            if not s["met"]:
                veil = pygame.Surface((size, size), pygame.SRCALPHA); veil.fill((240, 232, 210, 90))
                screen.blit(veil, (fx, fy))
            tx = fx + size + 18
            name = f["name"].render(s["name"], True, INK)
            screen.blit(name, (tx, fy))
            role = f["small"].render(s["role"], True, (90, 80, 70))
            screen.blit(role, (tx, fy + 30))
            status, scol = (("Spoken to", GREEN) if s["met"] else ("Not met yet", GREY))
            screen.blit(f["label"].render(status, True, scol), (tx, fy + 52))
            box = pygame.Rect(tx, fy + 76, 22, 22)                               # the cross-off box
            pygame.draw.rect(screen, (252, 248, 236), box)
            pygame.draw.rect(screen, INK if s["met"] else GREY, box, 2)
            lab = f["small"].render("crossed off" if s["crossed"] else "cross off (Enter)", True,
                                    INK if s["met"] else GREY)
            screen.blit(lab, (box.right + 8, box.y + 3))
            self.rects.append((card, box.inflate(lab.get_width() + 12, 6).move(lab.get_width() // 2 + 6, 0)))
            if s["crossed"]:                                                     # crossed off: a big red X
                pygame.draw.line(screen, RED, box.topleft, box.bottomright, 3)
                pygame.draw.line(screen, RED, box.topright, box.bottomleft, 3)
                pygame.draw.line(screen, RED, (fx - 4, fy - 4), (fx + size + 4, fy + size + 4), 5)
                pygame.draw.line(screen, RED, (fx + size + 4, fy - 4), (fx - 4, fy + size + 4), 5)
                pygame.draw.line(screen, RED, (tx - 2, fy + name.get_height() // 2 + 1),
                                 (tx + name.get_width() + 2, fy + name.get_height() // 2 + 1), 3)
            ny = fy + size + 14                                                  # the notes, under the photo and name
            screen.blit(f["label"].render("Notes:", True, (120, 90, 80)), (card.x + 12, ny))
            lines = self._wrap(f["hand"], s["notes"], card.w - 100)
            lh = f["hand"].get_linesize()
            for k, ln in enumerate(lines[:3]):
                ly = ny - 4 + k * lh
                pygame.draw.line(screen, RULE, (card.x + 76, ly + lh - 2), (card.right - 12, ly + lh - 2))
                screen.blit(f["hand"].render(ln, True, INK), (card.x + 78, ly))
            if i == self.sel and blink:                                          # the cursor
                last = lines[min(len(lines), 3) - 1]
                k = min(len(lines), 3) - 1
                pygame.draw.rect(screen, INK, (card.x + 80 + f["hand"].size(last)[0], ny - 2 + k * lh, 2, lh - 6))
        tip = "Arrows / click: choose  |  type: notes  |  Enter / click the box: cross off  |  Esc: close"
        if self.flash and pygame.time.get_ticks() < self.flash[1]:
            tip = self.flash[0]
        t = f["small"].render(tip, True, (236, 232, 220))
        screen.blit(t, ((w - t.get_width()) // 2, y0 + bh + 18))
