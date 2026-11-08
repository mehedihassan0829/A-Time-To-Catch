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
| Click / E / Space | next line in a cut scene, put the newspaper away |
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

## Playing the story

You start on Park Street every time the game runs. The compass at the top of the screen points to where you need to go next. It follows the real walking route around buildings, water and the police tape, and the distance shows as metres to walk.

1. **The crime scene.** The compass leads you down to the harbourside. When you get close to the police officer, a cut scene plays between the detective, the officer and Daniel Shaw. Click to move on to the next line. Daniel gives you his number, which goes into your pocket and your notebook.
2. **The Bristol Arcade.** Next, the compass points to the arcade where John worked.

On the way you can call in at **Park Stores**. Press **E** at the counter to buy the morning paper (*The Harbour Gazette*). It stays in your pocket, so you can read it again (I, then Enter).

## The harbourside and the arcade

Walk off the right-hand end of College Green to reach the harbourside: Anchor Road, the market (two rows of stalls, busiest around lunchtime), the plaza with its ground fountains, Za Za Bazaar, the ferry platform, the harbourside decks and pontoons with their boats, and the Bristol Arcade (where the aquarium was). The arcade is open 10:00 till 2:00.

You can walk into Za Za Bazaar (open 12:00 till 23:00). It's laid out like the map they give you at the door: the bar along the back, six food stations with their chefs (desserts, salads, far east, tex mex, european, indian), the drinks station, the toilets, and a dining hall of booths and tables under string lights. It's packed at lunch and dinner and quiet in between.

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
| `minimap.py` | the mini-map in the bottom-left corner |
| `daynight.py` | game clock, lighting and the watch |
| `inventory.py` | the pocket and notebook |
| `quest.py` | objectives, the compass, cut scenes and the newspaper |
| `art/pixilart/` | every drawing as a `.pixil` file for Pixilart |
| `art/drawings/` | the same drawings as PNGs |

Your notebook, the time of day and the arcade high scores are saved in `saves/` (not committed).

## Credits

- All art is drawn in code, in `pixel_art.py` and `people.py`.
- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available under the Open Database Licence.
