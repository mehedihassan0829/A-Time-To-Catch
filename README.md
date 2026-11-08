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

Every time the game runs, the story starts the night before in the detective's flat: he's about to light a cigarette when the phone rings. The next morning you're on Park Street. Click (or press E, Space or Enter) to move on through cut scenes.

The compass at the top of the screen always points the way to walk to your next objective. It follows the real walking route around buildings, water, the police tape and people, and keeps to the pavement. The distance shows in metres. When the next place is on another map or behind a door, it leads you there first. Press **E** when a prompt appears (a locker, a shelf, a question).

1. **The crime scene at the harbourside.** You talk to the police officer and Daniel Shaw, and Daniel gives you his number. The officer then hands you John's audio recorder, which brings on the first **time echo**. Time echoes are flashbacks in black and white, set in the place itself: here John is standing by the water when a shadowy figure comes up behind him.
2. **The Bristol Arcade.** A hint tells you to beat John's high score on Seagull Bird. Do that and Martin comes over to talk. He lets you into John's locker in the store room, where you find a token, an old photograph and notes that cite Professor Usher.
3. **Professor Usher's office** (through the Wills Memorial Building's front door). Usher isn't in, and an echo shows John and Usher talking about the photograph.
4. **The cafés.** You ask for Emily in one café after another. At the fourth, they tell you Emily Carter comes in at 6pm, so you sit and wait. She shows you the photograph, and an echo shows her and John looking at it.
5. **The Gazette** (Daniel's newspaper office on Park Street). Daniel finds the 1999 front page: Jack Harper, 31, found dead in the river.
6. **The arcade's store room.** The 1999 staff binder is missing from the shelf. The 1998 one has P. Usher on it.
7. **Usher's office again.** It's been packed up. You find the missing 1999 record and the photograph of Jack and Usher, which brings on the last echo. Then Usher's computer shows the train times.
8. **Clifton Down station.** Run off the top of Park Street. To be continued...

Optional: buy the morning paper at Park Stores on the way to the crime scene.

Everything you pick up goes into your pocket (two rows of eight). You can read the papers, records and photographs again from there with **Enter**. All the dialogue is in `quest_script.py`, so the story can be edited without touching the game code.

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
| `minimap.py` | a mini-map (not shown in the game at the moment) |
| `daynight.py` | game clock, lighting and the watch |
| `inventory.py` | the pocket and notebook |
| `quest.py` | the story as you play it: objectives, the walking-route compass, cut scenes |
| `quest_script.py` | everything the characters say, the narration, the objectives and the newspapers' words - edit this to change the story |
| `echo.py` | the time echoes (black and white flashbacks) and the opening scene in the flat |
| `documents.py` | the things you read: newspapers, staff records, photographs, the train times |
| `art/pixilart/` | every drawing as a `.pixil` file for Pixilart |
| `art/drawings/` | the same drawings as PNGs |

Your notebook, the time of day and the arcade high scores are saved in `saves/` (not committed).

## Credits

- All art is drawn in code, in `pixel_art.py` and `people.py`.
- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available under the Open Database Licence.
