# A Time To Catch

A top-down pixel-art game set on Park Street, Frogmore Street and the harbourside in Bristol. Walk the street by day and night, talk to the people who live in its alleyways, and keep notes on what you find.

## Story

In 2026, a detective with the ability to witness fragments of the past is called to investigate the latest murder attributed to the Bristol Pusher, a killer who has remained dormant for eleven years. Investigating the final days of victim John, the detective interviews three people from his life: his arcade coworker, a close friend and a local journalist, before speaking to his university professor, Dr Peter Usher. Through objects left behind by John, the detective reconstructs his movements and uncovers a hidden investigation into the Bristol Pusher. An old arcade token reveals that John's father was Jack, the killer's first victim in 1999. As the detective uncovers the original arcade records, he finally discovers the murderer's identity. But when he reaches the train station, two trains are about to depart, and he must make a decision that could determine whether the Bristol Pusher escapes forever.

## Play

**Windows:** double-click `play.bat`

**Mac / Linux:** `./play.sh`

**Any computer:**

```
python -m pip install -r requirements.txt
python main.py
```

Needs Python 3.9 or newer. The libraries are `pygame-ce` and `pygame-widgets` (used by MVB Kombat), which `main.py` installs on first run if they're missing.

## Controls

| Key | |
|---|---|
| WASD / arrows | move |
| Shift | run |
| E | talk / play an arcade machine |
| I | pocket (inventory) |
| N | notebook |
| F | lighter |
| T (hold) | make time pass faster |
| Tab | switch character |
| M | switch map |
| F1 | show hitboxes |
| F3 | show FPS |
| F5 / F6 / F7 | *(testing)* jump to the Frogmore steps / Park Street stairwell / the arcade |
| Esc | close / quit |

## The harbourside and the arcade

Walk off the right-hand end of College Green to reach the harbourside: Anchor Road, the Centre and the ferry landing, the Watershed, the pontoons and boats, and the Harbour Arcade (where the aquarium was). The arcade is open 10:00 till 2:00.

Walk up to a machine and press E to play it. The game fills the screen inside the machine's frame; Esc or Backspace steps away. High scores are saved in `saves/highscores.json`.

| Machine | |
|---|---|
| MVB Kombat | the MVB Kombat fighting game (in `mvb_kombat/`) |
| Seagull Bird | flap a gull past Cabot Tower and the harbour cranes |
| Hoop Shot | basketball with real ball physics: baskets in a row score more and more |
| Invaders | Space Invaders |

## Files

| | |
|---|---|
| `main.py` | the game: world, drawing, camera, player, shops, stairs and levels |
| `pixel_art.py` | all the pixel art, drawn in code |
| `park_street_map.py`, `frogmore_map.py` | the two street maps (generated from OpenStreetMap) |
| `harbourside_map.py` | the harbourside, off the end of College Green |
| `arcade.py` | the arcade machines and their games (Seagull Bird, Hoop Shot, Invaders), and running MVB Kombat inside a machine |
| `mvb_kombat/` | the MVB Kombat game, its art and sound |
| `queens_road_map.py` | an earlier Queens Road map |
| `people.py` | NPCs: looks, jobs, routines, opening hours |
| `story.py` | the story characters and what they say - edit this to write the plot |
| `traffic.py` | cars, the bus and the traffic lights |
| `daynight.py` | game clock, lighting and the watch |
| `inventory.py` | the pocket and notebook |
| `art/pixilart/` | every drawing as a `.pixil` file for Pixilart |
| `art/drawings/` | the same drawings as PNGs |

Your notebook, the time of day and the arcade high scores are saved in `saves/` (not committed).

## Credits

- All art is drawn in code, in `pixel_art.py` and `people.py`.
- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available under the Open Database Licence.
