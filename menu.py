"""The main menu (when the game starts) and the pause menu (Esc during the game - everything stops while it's open).

Up / Down (or W / S, or the mouse) to choose, Enter / click to pick. Left / Right changes the music volume.
"""
import math
import pygame

TITLE_RED = (220, 30, 30)        # the same red as the title at the end of the film
CONTROLS = [
    ("WASD / arrow keys", "walk"), ("Shift", "run"), ("E", "talk, look at things, play an arcade machine"),
    ("Click / E / Space", "next line in a cut scene"), ("I", "your pocket (Enter to use / read things)"),
    ("N", "notebook"), ("F", "lighter"), ("T (hold)", "make time pass faster"),
    ("Esc", "pause menu"), ("F11", "fullscreen / window"),
]


class Menu:
    def __init__(self, music, display=None):
        self.music = music
        self.display = display          # (is_fullscreen(), toggle()) - the Display option
        self.fonts = None

    def _f(self):
        if self.fonts is None:
            self.fonts = dict(
                title=pygame.font.SysFont("georgia,times new roman,serif", 76, bold=True),
                sub=pygame.font.SysFont("georgia,times new roman,serif", 20, italic=True),
                item=pygame.font.SysFont("georgia,times new roman,serif", 32, bold=True),
                small=pygame.font.SysFont("consolas,menlo,monospace", 15),
                key=pygame.font.SysFont("consolas,menlo,monospace", 18, bold=True),
            )
        return self.fonts

    def title(self, screen, clock, background):
        """The main menu. background(surface, t) draws whatever's behind it. Returns 'play' or 'quit'."""
        return self._run(screen, clock, ["Start", "Controls", "music", "display", "Quit"], background, paused=False)

    def pause(self, screen, clock):
        """The pause menu, over a still of the game. Returns 'resume', 'title' or 'quit'."""
        still = screen.copy()
        r = self._run(screen, clock, ["Resume", "Controls", "music", "display", "Main menu", "Quit game"],
                      lambda s, t: s.blit(still, (0, 0)), paused=True)
        return r

    def _run(self, screen, clock, items, background, paused):
        f = self._f()
        sel = 0
        showing_controls = False
        t = 0.0
        self.music.want("menu")
        rects = []
        while True:
            dt = min(clock.tick(60) / 1000, 0.05)
            t += dt
            self.music.update(dt)
            choice = None
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return "quit"
                if showing_controls:
                    if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        showing_controls = False
                    continue
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11 and self.display:
                    self.display[1]()
                    screen = pygame.display.get_surface()
                    continue
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        sel = (sel - 1) % len(items)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        sel = (sel + 1) % len(items)
                    elif ev.key in (pygame.K_LEFT, pygame.K_a) and items[sel] == "music":
                        self.music.set_volume(self.music.volume - 0.1)
                    elif ev.key in (pygame.K_RIGHT, pygame.K_d) and items[sel] == "music":
                        self.music.set_volume(self.music.volume + 0.1)
                    elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                        choice = items[sel]
                    elif ev.key == pygame.K_ESCAPE and paused:
                        choice = "Resume"
                elif ev.type == pygame.MOUSEMOTION:
                    for i, r in enumerate(rects):
                        if r.collidepoint(ev.pos):
                            sel = i
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    for i, r in enumerate(rects):
                        if r.collidepoint(ev.pos):
                            sel = i; choice = items[i]
            if choice == "music":                       # clicking the volume steps it up (and round to off)
                v = self.music.volume + 0.1
                self.music.set_volume(0.0 if v > 1.05 else v)
            elif choice == "display":
                if self.display:
                    self.display[1]()
                    screen = pygame.display.get_surface()
            elif choice == "Controls":
                showing_controls = True
            elif choice:
                return {"Start": "play", "Quit": "quit", "Resume": "resume", "Main menu": "title",
                        "Quit game": "quit"}[choice]

            w, h = screen.get_size()
            background(screen, t)
            dim = pygame.Surface((w, h), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 200 if paused else 120))
            screen.blit(dim, (0, 0))
            if showing_controls:
                self._controls(screen, f, w, h)
                pygame.display.flip()
                continue
            # the title
            ty = 110 if not paused else 90
            band = pygame.Surface((w, 150 if not paused else 110), pygame.SRCALPHA)
            band.fill((0, 0, 0, 120))
            screen.blit(band, (0, ty - 16))
            if paused:
                head = f["title"].render("PAUSED", True, (240, 236, 220))
            else:
                head = f["title"].render("A TIME TO CATCH", True, TITLE_RED)
                shadow = f["title"].render("A TIME TO CATCH", True, (20, 0, 0))
                screen.blit(shadow, ((w - shadow.get_width()) // 2 + 4, ty + 4))
            screen.blit(head, ((w - head.get_width()) // 2, ty))
            if not paused:
                sub = f["sub"].render("Bristol. The Bristol Pusher is back.", True, (230, 220, 200))
                screen.blit(sub, ((w - sub.get_width()) // 2, ty + head.get_height() + 6))
            # the items
            rects = []
            y = ty + (170 if not paused else 150)
            for i, it in enumerate(items):
                if it == "music":
                    label = f"Music volume:  < {int(round(self.music.volume * 100))}% >"
                elif it == "display":
                    label = "Display:  " + ("Full screen" if self.display and self.display[0]() else "Window")
                else:
                    label = it
                on = i == sel
                img = f["item"].render(label, True, (255, 236, 170) if on else (220, 214, 200))
                r = img.get_rect(center=(w // 2, y))
                if on:
                    glow = pygame.Surface((r.w + 60, r.h + 14), pygame.SRCALPHA)
                    glow.fill((0, 0, 0, 150))
                    pygame.draw.rect(glow, (*TITLE_RED, 255), glow.get_rect(), 2)
                    screen.blit(glow, (r.x - 30, r.y - 7))
                    bob = int(3 * math.sin(t * 5))
                    pygame.draw.polygon(screen, TITLE_RED, [(r.x - 52 + bob, r.centery - 9), (r.x - 52 + bob, r.centery + 9),
                                                            (r.x - 38 + bob, r.centery)])
                screen.blit(img, r)
                rects.append(r.inflate(60, 14))
                y += 62 if not paused else 56
            hint = f["small"].render("Up / Down to choose,  Enter or click to pick,  Left / Right: music volume", True,
                                     (200, 196, 186))
            screen.blit(hint, ((w - hint.get_width()) // 2, h - 40))
            pygame.display.flip()

    def _controls(self, screen, f, w, h):
        bw, bh = 720, 80 + len(CONTROLS) * 38
        x0, y0 = (w - bw) // 2, max(20, (h - bh) // 2 - 50)
        panel = pygame.Surface((bw, bh), pygame.SRCALPHA)
        panel.fill((14, 16, 24, 235))
        pygame.draw.rect(panel, TITLE_RED, panel.get_rect(), 2)
        screen.blit(panel, (x0, y0))
        head = f["item"].render("Controls", True, (240, 236, 220))
        screen.blit(head, ((w - head.get_width()) // 2, y0 + 14))
        for i, (k, what) in enumerate(CONTROLS):
            y = y0 + 70 + i * 38
            screen.blit(f["key"].render(k, True, (255, 220, 140)), (x0 + 40, y))
            screen.blit(f["small"].render(what, True, (230, 230, 236)), (x0 + 280, y + 2))
        back = f["small"].render("press any key to go back", True, (180, 176, 168))
        screen.blit(back, ((w - back.get_width()) // 2, y0 + bh + 10))
