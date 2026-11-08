# A Time To Catch

A top-down pixel-art game set on Park Street and Frogmore Street in Bristol. Walk the street by day and night, talk to the people who live in its alleyways, and keep notes on what you find.

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

Needs Python 3.9 or newer. The only library is `pygame-ce`, which `main.py` installs on first run if it's missing.

## Controls

| Key | |
|---|---|
| WASD / arrows | move |
| Shift | run |
| E | talk / go into a shop |
| I | pocket (inventory) |
| N | notebook |
| F | lighter |
| T (hold) | make time pass faster |
| Tab | switch character |
| M | switch map |
| F1 | show hitboxes |
| F3 | show FPS |
| F5 / F6 | *(testing)* jump to the Frogmore steps / Park Street stairwell |
| Esc | close / quit |

## Files

| | |
|---|---|
| `main.py` | the game: world, drawing, camera, player, shops, stairs and levels |
| `pixel_art.py` | all the pixel art, drawn in code |
| `park_street_map.py`, `frogmore_map.py` | the two street maps (generated from OpenStreetMap) |
| `queens_road_map.py` | an earlier Queens Road map |
| `people.py` | NPCs: looks, jobs, routines, opening hours |
| `story.py` | the story characters and what they say - edit this to write the plot |
| `traffic.py` | cars, the bus and the traffic lights |
| `daynight.py` | game clock, lighting and the watch |
| `inventory.py` | the pocket and notebook |
| `art/pixilart/` | every drawing as a `.pixil` file for Pixilart |
| `art/drawings/` | the same drawings as PNGs |

Your notebook and the time of day are saved in `saves/` (not committed).

## Credits

- All art is drawn in code, in `pixel_art.py` and `people.py`.
- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available under the Open Database Licence.
