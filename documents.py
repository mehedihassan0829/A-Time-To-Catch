"""The things you read in the story, drawn full screen: the newspapers, John's locker, the store-room shelf, the staff
records, the photographs and Usher's computer. The words are in quest_script.py."""
import math
import pygame
import pixel_art as pa
import quest_script as S

INK = (28, 26, 24)
_cache = {}


def serif(n, b=False, i=False):
    return pygame.font.SysFont("georgia,times new roman,serif", n, bold=b, italic=i)


def mono(n, b=False):
    return pygame.font.SysFont("courier new,consolas,menlo,monospace", n, bold=b)


def hand(n):
    return pygame.font.SysFont("segoe print,bradley hand,comic sans ms,georgia", n, italic=True)


def wrap(font, text, width):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        if font.size((cur + " " + wd).strip())[0] > width:
            lines.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return lines


def get(view, size, photos, now_hour=12.0):
    """The finished document for a view id, sized to fit the screen. photos(sid) gives a still of a scene."""
    key = (view, size, int(now_hour * 6) if view == "computer" else 0)
    got = _cache.get(key)
    if got is None:
        w, h = size
        fn = {"paper2026": lambda: newspaper(S.PAPER, w, h, None),
              "paper1999": lambda: newspaper(S.PAPER_1999, w, h, photos("harbour_view"), old=True),
              "locker": lambda: locker(w, h), "shelf": lambda: shelf(w, h),
              "record1998": lambda: record("1998", S.STAFF_1998, ["P. Usher"], w, h),
              "record1999": lambda: record("1999", S.STAFF_1999, ["P. Usher", "J. Harper"], w, h),
              "photo1999": lambda: photograph(photos("photo1999"), w, h, "Summer '99", tilt=-3),
              "ju_photo": lambda: photograph(photos("ju_photo"), w, h, None, tilt=2, zoom=1.6),
              "ju_back": lambda: photo_back(w, h), "computer": lambda: computer(w, h, now_hour)}[view]
        got = _cache[key] = fn()
    return got


# ------------------------------------------------------------------ newspapers
def _news_photo(pw, ph):
    """The 2026 front-page picture: the cordon on the decks, in newsprint grey."""
    photo = pygame.Surface((pw, ph))
    photo.fill((120, 124, 128))
    for k in range(0, ph, 6):                                      # the water
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
    return photo


def _halftone(photo):
    pw, ph = photo.get_size()
    dots = pygame.Surface((pw, ph), pygame.SRCALPHA)
    for yy in range(0, ph, 3):
        for xx in range((yy // 3) % 2 * 2, pw, 4):
            dots.set_at((xx, yy), (0, 0, 0, 40))
    photo.blit(dots, (0, 0))


def newspaper(P, w, h, picture, old=False):
    W, H = min(980, w - 60), min(680, h - 40)
    s = pygame.Surface((W, H))
    s.fill((222, 206, 168) if old else (238, 232, 214))
    ink = (40, 34, 26) if old else INK
    mast = serif(48, True).render(P["masthead"], True, ink)
    s.blit(mast, (W // 2 - mast.get_width() // 2, 14))
    pygame.draw.line(s, ink, (24, 74), (W - 24, 74), 3)
    dl = serif(15).render(P["dateline"], True, ink)
    pr = serif(15).render(P["price"], True, ink)
    s.blit(dl, (26, 80)); s.blit(pr, (W - 26 - pr.get_width(), 80))
    pygame.draw.line(s, ink, (24, 102), (W - 24, 102), 1)
    kk = serif(17, True).render(P["kicker"], True, (120, 40, 30) if old else (150, 30, 30))
    s.blit(kk, (26, 112))
    hl = serif(64 if not old else 52, True).render(P["headline"], True, ink)
    if hl.get_width() > W - 48:
        hl = pygame.transform.smoothscale(hl, (W - 48, int(hl.get_height() * (W - 48) / hl.get_width())))
    s.blit(hl, (24, 134))
    y = 134 + hl.get_height() + 4
    sf = serif(24, False, True).render(P["standfirst"], True, shade(ink, 1.8))
    s.blit(sf, (26, y)); y += sf.get_height() + 10
    pygame.draw.line(s, ink, (24, y), (W - 24, y), 1); y += 10
    pw, ph = int(W * 0.42), int((H - y - 30) * 0.62)
    if picture is None:
        photo = _news_photo(pw, ph)
    else:
        photo = pygame.transform.smoothscale(_crop(picture, pw / ph), (pw, ph))
        photo = pygame.transform.grayscale(photo)
    _halftone(photo)
    if old:
        tint = pygame.Surface((pw, ph)); tint.fill((236, 220, 180))
        photo.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    pygame.draw.rect(photo, ink, photo.get_rect(), 2)
    s.blit(photo, (26, y))
    cap = serif(13, False, True)
    cy_ = y + ph + 4
    for ln in wrap(cap, P["caption"], pw):
        s.blit(cap.render(ln, True, shade(ink, 1.8)), (26, cy_)); cy_ += 16
    body = serif(16)
    by_ = serif(14, True).render(P["byline"], True, ink)
    colx = 26 + pw + 22
    s.blit(by_, (colx, y)); yy = y + 22
    colw = W - colx - 26
    for para in P["body"]:
        for ln in wrap(body, para, colw):
            if yy > H - 70:
                break
            s.blit(body.render(ln, True, ink), (colx, yy)); yy += 20
        yy += 6
    pygame.draw.line(s, ink, (24, H - 56), (W - 24, H - 56), 1)
    ins = serif(14, True).render("INSIDE:", True, (150, 30, 30))
    s.blit(ins, (26, H - 46))
    xx = 26 + ins.get_width() + 10
    for item in P["inside"]:
        t = serif(14).render(item, True, ink)
        s.blit(t, (xx, H - 46)); xx += t.get_width() + 24
    if old:                                                       # yellowed edges and a fold
        edge = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(14):
            pygame.draw.rect(edge, (120, 90, 40, 10), (i, i, W - 2 * i, H - 2 * i), 1)
        pygame.draw.line(edge, (120, 100, 70, 60), (W // 2, 0), (W // 2, H), 2)
        s.blit(edge, (0, 0))
    pygame.draw.rect(s, (180, 172, 150), s.get_rect(), 3)
    return s


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def _crop(img, aspect):
    w, h = img.get_size()
    if w / h > aspect:
        nw = int(h * aspect)
        return img.subsurface(((w - nw) // 2, 0, nw, h)).copy()
    nh = int(w / aspect)
    return img.subsurface((0, (h - nh) // 2, w, nh)).copy()


# ------------------------------------------------------------------ John's locker
def locker(w, h):
    W, H = min(820, w - 80), min(520, h - 80)
    s = pygame.Surface((W, H))
    s.fill((70, 78, 92))
    pygame.draw.rect(s, (52, 58, 70), (20, 20, W - 40, H - 40))
    pygame.draw.rect(s, (90, 100, 116), (20, 20, W - 40, H - 40), 4)
    pygame.draw.rect(s, (90, 100, 116), (20, int(H * 0.62), W - 40, 8))       # the shelf
    for k in range(5):                                                        # vents along the top
        pygame.draw.rect(s, (40, 44, 54), (W // 2 - 120 + k * 52, 34, 36, 6))
    f = serif(22, True)
    items = [(pa.token_icon(), "Arcade token"), (pa.photo_icon(), "Old photograph"), (pa.notes_icon(), "Notes")]
    col = (W - 80) // 3                                                     # three columns, each label fits its own
    for k, (ic, label) in enumerate(items):
        big = pygame.transform.scale(ic, (ic.get_width() * 2, ic.get_height() * 2))
        cx = 40 + col * k + col // 2
        s.blit(big, (cx - big.get_width() // 2, int(H * 0.62) - big.get_height() - 6))
        size = 22
        while serif(size, True).size(label)[0] > col - 16 and size > 12:
            size -= 1
        t = serif(size, True).render(label, True, (236, 236, 240))
        s.blit(t, (cx - t.get_width() // 2, int(H * 0.62) + 24))
    sub = serif(16, False, True).render("...the notes cite Professor Peter Usher, University of Bristol, on every page",
                                        True, (200, 204, 214))
    s.blit(sub, (W // 2 - sub.get_width() // 2, H - 70))
    return s


# ------------------------------------------------------------------ the store-room shelf: the gap where 1999 should be
def shelf(w, h):
    W, H = min(980, w - 60), min(560, h - 80)
    s = pygame.Surface((W, H))
    s.fill((96, 104, 120))
    pygame.draw.rect(s, (72, 78, 92), (16, 16, W - 32, H - 32))
    pygame.draw.rect(s, (150, 160, 176), (0, H - 60, W, 14))                    # the shelf
    years = ["1994", "1995", "1996", "1997", "1998", None, "2000", "2001"]
    cols = [(40, 70, 130), (140, 40, 40), (40, 100, 70), (120, 90, 40)]
    bw = (W - 80) // len(years)
    big = serif(46, True)
    for k, yr in enumerate(years):
        x = 40 + k * bw
        top, bot = 40, H - 60
        if yr is None:
            pygame.draw.rect(s, (60, 64, 76), (x + 4, top + 20, bw - 8, bot - top - 20))
            pygame.draw.rect(s, (150, 150, 140), (x + 4, bot - 6, bw - 8, 6))          # the clean line in the dust
            q = serif(18, False, True).render("1999?", True, (170, 170, 180))
            s.blit(q, (x + bw // 2 - q.get_width() // 2, (top + bot) // 2))
            continue
        c = cols[int(yr) % 4]
        pygame.draw.rect(s, (20, 20, 24), (x + 4, top, bw - 8, bot - top))
        pygame.draw.rect(s, c, (x + 8, top + 4, bw - 16, bot - top - 4))
        pygame.draw.rect(s, (236, 230, 210), (x + 14, top + 26, bw - 28, bot - top - 110))
        for j, ch in enumerate(yr):                                                  # the year, big, down the spine
            t = big.render(ch, True, INK)
            s.blit(t, (x + bw // 2 - t.get_width() // 2, top + 34 + j * 52))
        pygame.draw.circle(s, (20, 20, 24), (x + bw // 2, bot - 40), 12)               # finger hole
    return s


# ------------------------------------------------------------------ the staff records
def record(year, staff, circled, w, h):
    W, H = min(760, w - 120), min(600, h - 60)
    s = pygame.Surface((W, H))
    s.fill((214, 180, 120))                                                     # manila folder
    page = pygame.Rect(30, 24, W - 60, H - 40)
    pygame.draw.rect(s, (246, 242, 230), page)
    t = mono(26, True).render(f"BRISTOL ARCADE - STAFF {year}", True, INK)
    s.blit(t, (page.x + 30, page.y + 30))
    pygame.draw.line(s, INK, (page.x + 30, page.y + 70), (page.right - 30, page.y + 70), 2)
    f = mono(22)
    for k, line in enumerate(staff):
        y = page.y + 96 + k * 44
        img = f.render(line, True, INK)
        s.blit(img, (page.x + 40, y))
        if any(line.startswith(c) for c in circled):                             # ringed in red pen
            r = pygame.Rect(page.x + 14, y - 12, img.get_width() + 54, img.get_height() + 22)
            pygame.draw.ellipse(s, (200, 40, 40), r, 3)
    foot = mono(16).render("Wages paid weekly. Uniform to be returned on leaving.", True, (110, 104, 96))
    s.blit(foot, (page.x + 30, page.bottom - 40))
    return s


# ------------------------------------------------------------------ photographs
def photograph(img, w, h, caption, tilt=0, zoom=1.0):
    W, H = min(760, w - 160), min(540, h - 120)
    pic = img
    if zoom != 1.0:
        pw, ph = img.get_size()
        cw, ch = int(pw / zoom), int(ph / zoom)
        pic = pygame.transform.scale(img.subsurface(((pw - cw) // 2, (ph - ch) // 2, cw, ch)), (pw, ph))
    border = 22
    pic = pygame.transform.smoothscale(_crop(pic, (W - 2 * border) / (H - 2 * border - 40)), (W - 2 * border, H - 2 * border - 40))
    card = pygame.Surface((W, H), pygame.SRCALPHA)
    card.fill((240, 234, 220, 255))
    pygame.draw.rect(card, (200, 190, 170, 255), card.get_rect(), 2)
    card.blit(pic, (border, border))
    if caption:
        c = hand(24).render(caption, True, (60, 60, 90))
        card.blit(c, (border + 6, H - border - 34))
    return pygame.transform.rotate(card, tilt).convert_alpha() if tilt else card


def photo_back(w, h):
    W, H = min(760, w - 160), min(540, h - 120)
    card = pygame.Surface((W, H), pygame.SRCALPHA)
    card.fill((236, 228, 210, 255))
    for i in range(10):
        pygame.draw.rect(card, (226 - i, 216 - i, 196 - i), (i * 3, i * 3, W - i * 6, H - i * 6), 3)
    f = hand(34)
    y = H // 2 - 70
    for ln in ["I know what you did Peter,", "come clear this up with me", "- Jack"]:
        t = f.render(ln, True, (40, 50, 110))
        card.blit(t, (W // 2 - t.get_width() // 2 + (60 if ln.startswith("-") else 0), y)); y += 56
    return pygame.transform.rotate(card, 2).convert_alpha()


# ------------------------------------------------------------------ Usher's computer: the train times
def computer(w, h, now_hour):
    W, H = min(900, w - 80), min(580, h - 80)
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(s, (40, 42, 48), (0, 0, W, H - 50), border_radius=14)                 # the monitor
    pygame.draw.rect(s, (60, 62, 70), (W // 2 - 70, H - 50, 140, 30))
    pygame.draw.rect(s, (50, 52, 60), (W // 2 - 140, H - 22, 280, 18), border_radius=6)
    scr = pygame.Rect(24, 24, W - 48, H - 100)
    pygame.draw.rect(s, (236, 240, 246), scr)
    pygame.draw.rect(s, (30, 60, 110), (scr.x, scr.y, scr.w, 50))
    t = serif(24, True).render("Train times - departures from Clifton Down", True, (255, 255, 255))
    s.blit(t, (scr.x + 18, scr.y + 12))
    f, fb = mono(22), mono(22, True)
    y = scr.y + 76
    for k, head in enumerate(("Time", "To", "Platform", "")):
        s.blit(fb.render(head, True, (30, 60, 110)), (scr.x + 20 + (0, 130, 470, 640)[k], y))
    y += 40
    mins = int(now_hour * 60) + 20
    for k, (frm, to, plat) in enumerate(S.TRAINS):
        m = mins + k * 2
        row = pygame.Rect(scr.x + 10, y - 6, scr.w - 20, 36)
        pygame.draw.rect(s, (255, 236, 160), row)
        s.blit(f.render(f"{(m // 60) % 24:02d}:{m % 60:02d}", True, INK), (scr.x + 20, y))
        s.blit(f.render(to, True, INK), (scr.x + 150, y))
        s.blit(f.render(plat, True, INK), (scr.x + 490, y))
        s.blit(f.render("On time", True, (40, 120, 60)), (scr.x + 660, y))
        y += 48
    y += 20
    note = serif(18, False, True).render("Ticket bought this morning: 1 adult, single, from Clifton Down",
                                         True, (90, 90, 100))
    s.blit(note, (scr.x + 20, y))
    return s
