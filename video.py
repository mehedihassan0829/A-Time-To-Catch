"""Plays the film at the end of the story (art/videos).

The original is art/videos/final.mp4. The game plays a lighter copy made from it (final_720p.mp4: 1280x720, H.264,
which decodes quickly on any computer) with its sound track as final_audio.ogg, using OpenCV (opencv-python) for the
pictures and pygame for the sound. Without OpenCV it shows a "TO BE CONTINUED" card instead.
Esc / Enter / Space / click skips it (after the first second).
"""
from pathlib import Path
import pygame


def play(screen, clock, folder, name="final"):
    """Returns 'quit' if the window was closed, otherwise None when it's over."""
    folder = Path(folder)
    try:
        import cv2
    except ImportError:
        print("opencv-python isn't installed, so the film can't play (pip install opencv-python)")
        return _card(screen, clock, "TO BE CONTINUED...")
    cap = cv2.VideoCapture(str(folder / f"{name}_720p.mp4"))
    if not cap.isOpened():
        cap = cv2.VideoCapture(str(folder / f"{name}.mp4"))       # fall back on the original
    if not cap.isOpened():
        return _card(screen, clock, "TO BE CONTINUED...")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    sound = False
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(folder / f"{name}_audio.ogg"))
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            sound = True
    except pygame.error:
        sound = False
    hint_font = pygame.font.SysFont("consolas,menlo,monospace", 14)
    start = pygame.time.get_ticks()
    shown = -1
    frame_img = None
    result = None
    while True:
        clock.tick(120)
        t = (pygame.time.get_ticks() - start) / 1000
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                result = "quit"
            skip = (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE)) or \
                   (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1)
            if skip and t > 1.0:
                result = "skip"
        if result:
            break
        want = int(t * fps)                                       # keep the pictures with the sound
        ended = False
        while shown < want:
            ok, frame = cap.read()
            if not ok:
                ended = True
                break
            shown += 1
            if shown == want:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = rgb.shape[:2]
                frame_img = pygame.image.frombuffer(rgb.tobytes(), (w, h), "RGB")
        if ended:
            break
        sw, sh = screen.get_size()
        screen.fill((0, 0, 0))
        if frame_img is not None:
            k = min(sw / frame_img.get_width(), sh / frame_img.get_height())
            size = (int(frame_img.get_width() * k), int(frame_img.get_height() * k))
            img = frame_img if size == frame_img.get_size() else pygame.transform.smoothscale(frame_img, size)
            screen.blit(img, ((sw - size[0]) // 2, (sh - size[1]) // 2))
        if 1.0 < t < 5.0:
            hint = hint_font.render("Esc: skip", True, (200, 200, 200))
            hint.set_alpha(int(255 * min(1.0, (5.0 - t))))
            screen.blit(hint, (sw - hint.get_width() - 16, sh - hint.get_height() - 12))
        pygame.display.flip()
    cap.release()
    if sound:
        pygame.mixer.music.stop()
    return "quit" if result == "quit" else None


def _card(screen, clock, text):
    """No film: a plain title card for a few seconds."""
    font = pygame.font.SysFont("georgia,times new roman,serif", 54, bold=True)
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < 4000:
        clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return "quit"
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return None
        screen.fill((0, 0, 0))
        t = font.render(text, True, (220, 30, 30))
        a = min(1.0, (pygame.time.get_ticks() - start) / 800)
        t.set_alpha(int(255 * a))
        sw, sh = screen.get_size()
        screen.blit(t, ((sw - t.get_width()) // 2, (sh - t.get_height()) // 2))
        pygame.display.flip()
    return None
