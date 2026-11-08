"""Professor Usher's computer, left on in his packed-up office. You use it with the mouse (and keyboard for the
search box): a desktop with a web browser, his email, his documents and the recycle bin.

The train ticket is in the browser's HISTORY, among everything else he's looked at - nothing on the screen says
"ticket", so you have to search well for it. Time stands still while you're at the computer.
run() returns True once you've opened the ticket.
"""
import pygame
import documents

BG, INK, MUTED, BLUE, LINE = (238, 240, 244), (30, 32, 38), (110, 114, 124), (40, 90, 170), (210, 214, 222)
SX, SY, SW, SH = 40, 28, 1200, 620          # the screen inside the monitor (in 1280 x 720)
TICKET_URL = "railsaver.co.uk/account?view=b48213"

# his browser history, newest first: (day, time, title, url). Nothing says "ticket": the booking is one of several
# "My account | RailSaver" pages, and only one of them still has a journey on it.
HISTORY = [
    ("Today", "08:41", "Bristol weather - hourly forecast", "weather.example.co.uk/bristol/hourly"),
    ("Today", "08:36", "how to clear browser history - Search", "search.example.com/?q=how+to+clear+browser+history"),
    ("Today", "08:30", "Staff email - Inbox", "mail.example.ac.uk/inbox"),
    ("Today", "08:22", "Flats to rent in Cork | HomeFinder", "homefinder.example.ie/cork/rent"),
    ("Today", "08:15", "Out of office: how to set it up - IT Help", "it.example.ac.uk/help/out-of-office"),
    ("Today", "08:02", "Long stay parking - how much? - Bristol Parkway", "parking.example.co.uk/bristol-parkway"),
    ("Today", "07:47", "My account | RailSaver", "railsaver.co.uk/account?view=cards"),
    ("Today", "07:39", "Severn Beach line timetable", "railtimes.example.co.uk/severn-beach-line"),
    ("Today", "07:31", "Live departures - Clifton Down", "railtimes.example.co.uk/live/clifton-down"),
    ("Today", "07:24", "Sign in | RailSaver", "railsaver.co.uk/login"),
    ("Today", "07:12", "My account | RailSaver", TICKET_URL),
    ("Today", "07:10", "Payment | RailSaver", "railsaver.co.uk/checkout/payment"),
    ("Today", "07:05", "THE BRISTOL PUSHER IS BACK - The Harbour Gazette", "harbourgazette.example.co.uk/news/pusher"),
    ("Today", "06:58", "Bristol weather - hourly forecast", "weather.example.co.uk/bristol/hourly"),
    ("Today", "06:52", "cheap removal van hire bristol same day - Search", "search.example.com/?q=cheap+removal+van+hire"),
    ("Today", "06:50", "how long do police keep a crime scene - Search", "search.example.com/?q=how+long+crime+scene"),
    ("Today", "01:33", "Body found in the Floating Harbour - The Harbour Gazette", "harbourgazette.example.co.uk/news/body-found"),
    ("Yesterday", "23:58", "tide times bristol harbour - Search", "search.example.com/?q=tide+times+bristol"),
    ("Yesterday", "22:40", "My account | RailSaver", "railsaver.co.uk/account?view=journeys"),
    ("Yesterday", "22:10", "Bristol Arcade - opening hours", "bristolarcade.example.co.uk/visit"),
    ("Yesterday", "21:47", "John Harper - PhD researcher - Department of History", "history.example.ac.uk/people/john-harper"),
    ("Yesterday", "18:20", "Staff email - Inbox", "mail.example.ac.uk/inbox"),
    ("Yesterday", "16:02", "Library catalogue: 'lost businesses of Bristol'", "library.example.ac.uk/search?q=lost+businesses"),
    ("Yesterday", "14:05", "Exam board minutes - October", "staff.example.ac.uk/exam-board/october"),
    ("Yesterday", "11:30", "Booking a room - Wills Memorial Building", "rooms.example.ac.uk/wills"),
    ("Yesterday", "09:12", "Bristol weather - hourly forecast", "weather.example.co.uk/bristol/hourly"),
    ("Last week", "Fri 20:44", "Ferry times - Holyhead to Dublin", "ferries.example.com/holyhead-dublin"),
    ("Last week", "Fri 20:31", "Flats to rent in Cork | HomeFinder", "homefinder.example.ie/cork/rent"),
    ("Last week", "Thu 22:15", "The Bristol Pusher - Bristol Crime Archive", "crimearchive.example.org/bristol-pusher"),
    ("Last week", "Thu 22:02", "Passport renewal - check your application", "passport.example.gov.uk/status"),
    ("Last week", "Wed 13:40", "Lecture 7 slides - Bristol's lost businesses", "staff.example.ac.uk/teaching/lecture-7"),
    ("Last week", "Tue 19:20", "My account | RailSaver", "railsaver.co.uk/account?view=b31977"),
    ("Last week", "Tue 19:05", "Train tickets to London - RailSaver deals", "railsaver.co.uk/deals/london"),
    ("Last week", "Mon 10:12", "Department of History - staff list", "history.example.ac.uk/people"),
]

PAGES = {   # what you see when you open one (anything not here: "this page has expired")
    "weather.example.co.uk/bristol/hourly": ["Bristol: drizzle this morning, clearing later. 11C.",
                                             "Wind from the south-west. Sunset 16:32."],
    "railtimes.example.co.uk/severn-beach-line": ["Severn Beach line: Temple Meads - Clifton Down - Severn Beach.",
                                                  "Trains about every 40 minutes in the evening."],
    "railsaver.co.uk/login": ["Sign in to RailSaver", "You have been signed out for your security."],
    "railsaver.co.uk/checkout/payment": ["This page has expired.", "Your payment has already been taken.",
                                         "You can see your booking in My account."],
    "railsaver.co.uk/account?view=cards": ["My account - saved cards", "Card ending 4417. Expires 09/28."],
    "railsaver.co.uk/account?view=journeys": ["My account - upcoming journeys", "You have no upcoming journeys."],
    "railsaver.co.uk/account?view=b31977": ["My account - booking RS-31977", "Bristol Temple Meads to London Paddington.",
                                            "CANCELLED - refunded to card ending 4417."],
    "railtimes.example.co.uk/live/clifton-down": ["Live departures - Clifton Down",
                                                  "This page shows live times. It was saved this morning."],
    "search.example.com/?q=how+to+clear+browser+history": ["How to clear your browser history: Settings, then Privacy..."],
    "it.example.ac.uk/help/out-of-office": ["Turn on your out of office: Mail, then Settings, then Automatic replies."],
    "harbourgazette.example.co.uk/news/pusher": ["THE BRISTOL PUSHER IS BACK", "...and he will be gone as quick as he came.",
                                                 "By Daniel Shaw, crime reporter."],
    "search.example.com/?q=cheap+removal+van+hire": ["Van hire from today. Same-day collection. No questions asked."],
    "search.example.com/?q=how+long+crime+scene": ["Police cordons usually stay in place for one to three days..."],
    "harbourgazette.example.co.uk/news/body-found": ["BODY FOUND IN THE FLOATING HARBOUR",
                                                     "A man was found in the water beside the harbourside decks..."],
    "search.example.com/?q=tide+times+bristol": ["Bristol: high water 23:41."],
    "bristolarcade.example.co.uk/visit": ["The Bristol Arcade - open 10:00 till 2:00, every day."],
    "history.example.ac.uk/people/john-harper": ["John Harper - PhD researcher",
                                                 "Research: businesses of the Bristol harbourside, 1980-2000.",
                                                 "Supervisor: Professor Peter Usher."],
    "library.example.ac.uk/search?q=lost+businesses": ["3 results. All 3 on loan to: P. USHER."],
    "staff.example.ac.uk/exam-board/october": ["Minutes of the exam board. Apologies: none. Any other business: none."],
    "rooms.example.ac.uk/wills": ["Your booking for Room 2.11 has been cancelled."],
    "ferries.example.com/holyhead-dublin": ["Holyhead - Dublin. Sailings at 02:40, 08:55, 14:10, 20:15."],
    "homefinder.example.ie/cork/rent": ["Flats to rent in Cork. 214 results."],
    "crimearchive.example.org/bristol-pusher": ["The Bristol Pusher",
                                                "Victims found in the city's harbour and river, from 1999.",
                                                "The first: Jack Harper, 31. Nobody has ever been charged."],
    "passport.example.gov.uk/status": ["Your passport has been sent. Expected delivery: 2 to 3 days."],
    "staff.example.ac.uk/teaching/lecture-7": ["Lecture 7: Bristol's lost businesses.",
                                               "Case study: the harbourside arcades (slide 14)."],
    "railsaver.co.uk/deals/london": ["Cheap tickets to London from GBP 19."],
    "history.example.ac.uk/people": ["Department of History - staff list.", "Usher, Prof. P. - Bristol history, 1900-2000."],
    "mail.example.ac.uk/inbox": ["You have been signed out."],
}

EMAILS = [
    ("John Harper", "Re: the 1999 photograph", "Mon 21:02",
     ["Peter,", "I've had another look at the photograph from the arcade. I think I've noticed something.",
      "Can we talk about it after my shift? - John"]),
    ("Exams Office", "Marks due Friday", "Mon 09:00", ["A reminder that all marks are due by Friday at 5pm."]),
    ("Library", "Overdue: 3 items", "Sun 08:00", ["Lost businesses of Bristol (3 copies) are now overdue."]),
    ("Head of Department", "Your leave", "Fri 16:45", ["Peter - I haven't received your leave form. Are you all right?"]),
]
FILES = [
    ("Lecture 7 - lost businesses.pptx", ["Slide 14: the harbourside arcades, 1985-2000."]),
    ("staff_list_1999_scan.pdf", ["The file is empty. It's been scanned and deleted."]),
    ("references for John.docx", ["To whom it may concern: John Harper is a diligent and careful researcher..."]),
    ("budget.xlsx", ["You can't open this kind of file here."]),
]
RECYCLE = [
    ("resignation (draft).docx", ["Dear Head of Department,", "I am writing to tell you that I will be leaving the University",
                                  "with immediate effect, for personal reasons.", "Peter"]),
]


class Computer:
    def __init__(self, screen, clock, time_text):
        self.screen, self.clock = screen, clock
        self.time_text = time_text
        self.window = None                   # None, "browser", "mail", "docs", "bin"
        self.page = None                     # browser: None (home), "history" or a url
        self.search = ""
        self.typing = False
        self.scroll = 0
        self.selected = None                 # mail / docs / bin: which item is open
        self.found = False
        self.hits = []                       # clickable rectangles this frame: (rect, action)
        f = lambda n, b=False: pygame.font.SysFont("segoe ui,arial,helvetica,sans", n, bold=b)
        self.f = dict(s=f(15), m=f(17), mb=f(17, True), l=f(22, True), xl=f(30, True), t=f(13))

    # ---------------------------------------------------------------- the loop
    def run(self):
        pygame.key.start_text_input()
        try:
            while True:
                self.clock.tick(60)
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        return "quit"
                    r = self.event(ev)
                    if r == "leave":
                        return self.found
                self.draw()
                pygame.display.flip()
        finally:
            pygame.key.stop_text_input()

    def event(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                if self.typing:
                    self.typing = False
                elif self.window:
                    self.window = None
                else:
                    return "leave"
            elif ev.key == pygame.K_BACKSPACE and (self.typing or (self.window == "browser" and self.page == "history")):
                self.search = self.search[:-1]; self.scroll = 0
            elif ev.key == pygame.K_h and ev.mod & pygame.KMOD_CTRL:
                self.window, self.page = "browser", "history"
            elif ev.key in (pygame.K_DOWN, pygame.K_PAGEDOWN):
                self.scroll += 1
            elif ev.key in (pygame.K_UP, pygame.K_PAGEUP):
                self.scroll = max(0, self.scroll - 1)
        elif ev.type == pygame.TEXTINPUT and (self.typing or (self.window == "browser" and self.page == "history")):
            self.typing = True
            if len(self.search) < 40:
                self.search += ev.text; self.scroll = 0
        elif ev.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - ev.y)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.typing = False
            for rect, action in reversed(self.hits):
                if rect.collidepoint(ev.pos):
                    return self.do(action)
        return None

    def do(self, action):
        kind, arg = action
        if kind == "leave":
            return "leave"
        if kind == "open":
            self.window, self.selected, self.scroll = arg, None, 0
            if arg == "browser":
                self.page = None
        elif kind == "close":
            self.window = None
        elif kind == "page":
            self.page, self.scroll = arg, 0
            if arg == TICKET_URL:
                self.found = True
        elif kind == "search":
            self.typing = True
        elif kind == "select":
            self.selected = arg
        return None

    # ---------------------------------------------------------------- drawing
    def text(self, s, font, col, x, y, maxw=None):
        img = self.f[font].render(s, True, col)
        if maxw and img.get_width() > maxw:
            while s and self.f[font].size(s + "...")[0] > maxw:
                s = s[:-1]
            img = self.f[font].render(s + "...", True, col)
        self.screen.blit(img, (x, y))
        return img.get_width()

    def wrap(self, s, font, maxw):
        out, cur = [], ""
        for word in s.split(" "):
            t = (cur + " " + word).strip()
            if cur and self.f[font].size(t)[0] > maxw:
                out.append(cur); cur = word
            else:
                cur = t
        return out + [cur]

    def button(self, rect, label, action, font="m", fill=(250, 250, 252), col=INK):
        pygame.draw.rect(self.screen, fill, rect, border_radius=5)
        pygame.draw.rect(self.screen, LINE, rect, 1, border_radius=5)
        img = self.f[font].render(label, True, col)
        self.screen.blit(img, (rect.centerx - img.get_width() // 2, rect.centery - img.get_height() // 2))
        self.hits.append((pygame.Rect(rect), action))

    def draw(self):
        self.hits = []
        scr = self.screen
        scr.fill((14, 14, 18))
        pygame.draw.rect(scr, (36, 38, 44), (SX - 22, SY - 18, SW + 44, SH + 46), border_radius=18)   # the monitor
        desk = pygame.Rect(SX, SY, SW, SH)
        for y in range(SH):                                                  # the desktop
            t = y / SH
            pygame.draw.line(scr, (int(40 + 30 * t), int(70 + 30 * t), int(110 + 20 * t)), (SX, SY + y), (SX + SW, SY + y))
        for i, (key, label, col) in enumerate((("browser", "Web browser", (60, 140, 220)), ("mail", "Mail", (230, 180, 60)),
                                               ("docs", "Documents", (240, 210, 120)), ("bin", "Recycle bin", (160, 170, 180)))):
            r = pygame.Rect(SX + 22, SY + 24 + i * 96, 84, 82)
            pygame.draw.rect(scr, col, (r.x + 22, r.y + 4, 40, 40), border_radius=8)
            pygame.draw.rect(scr, (20, 20, 26), (r.x + 22, r.y + 4, 40, 40), 2, border_radius=8)
            img = self.f["s"].render(label, True, (255, 255, 255))
            scr.blit(img, (r.centerx - img.get_width() // 2, r.y + 52))
            self.hits.append((r, ("open", key)))
        pygame.draw.rect(scr, (24, 28, 40), (SX, SY + SH - 34, SW, 34))       # the taskbar
        self.text(self.time_text, "mb", (240, 240, 240), SX + SW - 70, SY + SH - 28)
        self.text("Department of History - staff PC", "t", (170, 180, 200), SX + SW - 300, SY + SH - 25)
        self.button(pygame.Rect(SX + 8, SY + SH - 30, 210, 26), "Step away from the computer", ("leave", None),
                    font="s", fill=(60, 66, 84), col=(240, 240, 240))
        if self.window:
            {"browser": self.browser, "mail": self.mail, "docs": self.docs, "bin": self.recycle}[self.window]()
        hint = self.f["t"].render("Mouse to click, type to search, scroll wheel to scroll.  Esc closes a window / steps away."
                                  "  (Time stands still while you're here.)", True, (170, 170, 180))
        scr.blit(hint, (SX, SY + SH + 8))

    def frame(self, title):
        win = pygame.Rect(SX + 140, SY + 20, SW - 170, SH - 70)
        pygame.draw.rect(self.screen, (20, 20, 26), win.inflate(4, 4), border_radius=8)
        pygame.draw.rect(self.screen, BG, win, border_radius=7)
        pygame.draw.rect(self.screen, (220, 224, 232), (win.x, win.y, win.w, 34), border_top_left_radius=7,
                         border_top_right_radius=7)
        self.text(title, "mb", INK, win.x + 14, win.y + 7)
        self.button(pygame.Rect(win.right - 40, win.y + 5, 32, 24), "X", ("close", None), font="mb")
        return pygame.Rect(win.x, win.y + 34, win.w, win.h - 34)

    def browser(self):
        body = self.frame("Web browser")
        bar = pygame.Rect(body.x, body.y, body.w, 44)
        pygame.draw.rect(self.screen, (246, 247, 250), bar)
        pygame.draw.line(self.screen, LINE, (bar.x, bar.bottom), (bar.right, bar.bottom))
        self.button(pygame.Rect(bar.x + 10, bar.y + 8, 34, 28), "<", ("page", None))
        url = "about:history" if self.page == "history" else (self.page or "staff.example.ac.uk/portal")
        addr = pygame.Rect(bar.x + 54, bar.y + 8, bar.w - 250, 28)
        pygame.draw.rect(self.screen, (255, 255, 255), addr, border_radius=14)
        pygame.draw.rect(self.screen, LINE, addr, 1, border_radius=14)
        self.text(url, "s", MUTED, addr.x + 14, addr.y + 5, addr.w - 28)
        self.button(pygame.Rect(bar.right - 180, bar.y + 8, 170, 28), "History  (Ctrl+H)", ("page", "history"))
        area = pygame.Rect(body.x + 20, bar.bottom + 14, body.w - 40, body.bottom - bar.bottom - 24)
        if self.page == "history":
            self.history(area)
        elif self.page is None:
            self.text("Staff portal", "xl", INK, area.x, area.y)
            self.text("You have been signed out. Sign in again to see your timetable and email.", "m", MUTED, area.x, area.y + 46)
            self.text("Bookmarks:", "mb", INK, area.x, area.y + 100)
            for i, (label, u) in enumerate((("Weather", "weather.example.co.uk/bristol/hourly"),
                                            ("Library", "library.example.ac.uk/search?q=lost+businesses"),
                                            ("Department", "history.example.ac.uk/people"))):
                self.button(pygame.Rect(area.x + i * 150, area.y + 130, 140, 30), label, ("page", u))
        elif self.page == TICKET_URL:
            self.text("Your booking RS-48213", "l", INK, area.x, area.y)
            doc = documents.ticket(1280, 720, documents.TICKET["time"])
            k = min(1.0, (area.w - 40) / doc.get_width(), (area.h - 90) / doc.get_height())
            if k < 1:
                doc = pygame.transform.smoothscale(doc, (int(doc.get_width() * k), int(doc.get_height() * k)))
            self.screen.blit(doc, (area.x, area.y + 44))
            self.text("Found it. Close the computer when you're done.", "mb", (180, 40, 30), area.x, area.bottom - 22)
        else:
            lines = PAGES.get(self.page, ["This page has expired."])
            y = area.y
            for i, ln in enumerate(lines):
                font = "l" if i == 0 else "m"
                for part in self.wrap(ln, font, area.w):
                    self.text(part, font, INK if i == 0 else (60, 64, 72), area.x, y)
                    y += 50 if i == 0 else 32

    def history(self, area):
        self.text("History", "l", INK, area.x, area.y)
        box = pygame.Rect(area.x + 140, area.y, 360, 32)
        pygame.draw.rect(self.screen, (255, 255, 255), box, border_radius=6)
        pygame.draw.rect(self.screen, BLUE if self.typing else LINE, box, 2, border_radius=6)
        shown = self.search + ("|" if self.typing and pygame.time.get_ticks() // 500 % 2 == 0 else "")
        self.text(shown or "Search history", "m", INK if self.search else MUTED, box.x + 10, box.y + 5)
        self.hits.append((box, ("search", None)))
        q = self.search.strip().lower()
        rows = [h for h in HISTORY if not q or q in h[2].lower() or q in h[3].lower()]
        y = area.y + 46
        lines = []
        last = None
        for day, tm, title, url in rows:
            if day != last:
                lines.append(("day", day)); last = day
            lines.append(("row", (tm, title, url)))
        per = max(1, (area.bottom - y) // 30)
        self.scroll = min(self.scroll, max(0, len(lines) - per))
        if not rows:
            self.text(f'Nothing in the history matches "{self.search}".', "m", MUTED, area.x, y)
        for kind, v in lines[self.scroll:self.scroll + per]:
            if kind == "day":
                self.text(v, "mb", BLUE, area.x, y + 4)
            else:
                tm, title, url = v
                r = pygame.Rect(area.x, y, area.w, 28)
                if r.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(self.screen, (226, 232, 244), r, border_radius=4)
                self.text(tm, "s", MUTED, area.x + 8, y + 5)
                w = self.text(title, "m", INK, area.x + 100, y + 3, area.w - 420)
                self.text(url, "s", MUTED, area.x + 110 + w, y + 5, area.right - (area.x + 110 + w) - 10)
                self.hits.append((r, ("page", url)))
            y += 30
        if len(lines) > per:
            self.text(f"scroll for more ({self.scroll + 1}-{min(len(lines), self.scroll + per)} of {len(lines)})", "t",
                      MUTED, area.right - 230, area.y + 10)

    def listing(self, title, items, empty_text):
        body = self.frame(title)
        left = pygame.Rect(body.x, body.y, 360, body.h)
        pygame.draw.rect(self.screen, (246, 247, 250), left)
        pygame.draw.line(self.screen, LINE, (left.right, left.y), (left.right, left.bottom))
        for i, it in enumerate(items):
            r = pygame.Rect(left.x + 8, left.y + 10 + i * 58, left.w - 16, 52)
            if self.selected == i:
                pygame.draw.rect(self.screen, (220, 230, 248), r, border_radius=5)
            self.text(it[0], "mb", INK, r.x + 10, r.y + 6, r.w - 20)
            if len(it) > 2:
                self.text(f"{it[1]}   {it[2]}", "s", MUTED, r.x + 10, r.y + 28, r.w - 20)
            self.hits.append((r, ("select", i)))
        right = pygame.Rect(left.right + 24, body.y + 20, body.right - left.right - 48, body.h - 40)
        if self.selected is None:
            self.text(empty_text, "m", MUTED, right.x, right.y)
            return
        it = items[self.selected]
        body_lines = it[-1]
        self.text(it[1] if len(it) > 2 else it[0], "l", INK, right.x, right.y)
        y = right.y + 48
        for ln in body_lines:
            for part in self.wrap(ln, "m", right.w):
                self.text(part, "m", (50, 54, 62), right.x, y)
                y += 30

    def mail(self):
        self.listing("Mail - Inbox", EMAILS, "Pick an email to read it.")

    def docs(self):
        self.listing("Documents", [(n, b) for n, b in FILES], "Pick a file to open it.")

    def recycle(self):
        self.listing("Recycle bin", [(n, b) for n, b in RECYCLE], "Pick a file to look at it.")


def run(screen, clock, time_text):
    """Use the computer until you step away. Returns True if you found the ticket, False if not, "quit" if the
    window was closed."""
    return Computer(screen, clock, time_text).run()
