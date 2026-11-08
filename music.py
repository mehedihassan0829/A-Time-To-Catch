"""The game's music (art/music): which track plays where, fading from one to the next.

    menu         the main menu and the pause menu
    detective    the story's cut scenes and time echoes
    day / night  out and about (night from dusk till dawn)
    arcade       inside the Bristol Arcade
    arcade_game  while you're playing one of the arcade machines

The volume is saved in saves/settings.json (change it in the menu).
"""
import json
from pathlib import Path
import pygame

TRACKS = {
    "menu": "menu_music.mp3",
    "detective": "detective.mp3",
    "day": "daytime.mp3",
    "night": "nightime.mp3",
    "arcade": "arcade_theme.mp3",
    "arcade_game": "arcade_game_music.mp3",
}
FADE_OUT = 0.7          # seconds to fade the old track out before the new one starts
FADE_IN_MS = 1200


class Music:
    def __init__(self, folder, save_dir):
        self.folder = Path(folder)
        self.settings = Path(save_dir) / "settings.json"
        self.volume = 0.6
        try:
            self.volume = float(json.loads(self.settings.read_text())["music"])
        except (OSError, ValueError, KeyError, TypeError):
            pass
        self.ok = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            self.ok = False                          # no sound card: the game just runs quietly
        self.current = None                          # the track playing (or fading in)
        self.wanted = None                           # the track that should be playing
        self.fading = 0.0                            # >0 while the old track fades out

    # ---- what should be playing
    def want(self, key):
        """Ask for a track (None = silence). Changes over with a fade; asking again for the same one does nothing."""
        if key == self.wanted:
            return
        self.wanted = key
        if self.current is not None and self.ok:
            self.fading = FADE_OUT
        else:
            self._start(key)

    def update(self, dt):
        if not self.ok:
            return
        if self.fading > 0:
            self.fading -= dt
            pygame.mixer.music.set_volume(self.volume * max(0.0, self.fading / FADE_OUT))
            if self.fading <= 0:
                self._start(self.wanted)
        elif self.current is not None and not pygame.mixer.music.get_busy():
            self.current = None                      # something else stopped it (MVB Kombat): start again
            self._start(self.wanted)

    def _start(self, key):
        self.current = None
        if not self.ok:
            return
        try:
            pygame.mixer.music.stop()
            if key is None or key not in TRACKS:
                return
            pygame.mixer.music.load(str(self.folder / TRACKS[key]))
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1, fade_ms=FADE_IN_MS)
            self.current = key
        except pygame.error as e:
            print("Couldn't play the music:", e)

    def now(self, key):
        """Switch straight away, no fade (e.g. going into an arcade machine)."""
        self.wanted = key
        self.fading = 0.0
        self._start(key)

    def stop(self):
        self.now(None)

    def lost(self):
        """Something else used the music player (MVB Kombat): start ours again next time."""
        self.current = None
        self.wanted = None

    # ---- the volume (menu)
    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, round(v, 2)))
        if self.ok and self.fading <= 0:
            pygame.mixer.music.set_volume(self.volume)
        try:
            self.settings.parent.mkdir(parents=True, exist_ok=True)
            save_setting(self.settings, "music", self.volume)
        except OSError:
            pass


def load_setting(path, key, default):
    try:
        return json.loads(Path(path).read_text()).get(key, default)
    except (OSError, ValueError, AttributeError):
        return default


def save_setting(path, key, value):
    """Change one setting in saves/settings.json, keeping the others."""
    path = Path(path)
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    data[key] = value
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    except OSError:
        pass
