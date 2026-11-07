"""Story characters - edit this file to write the plot.

These are the homeless characters in Park Street's alleyways. They're the ones who matter to the story,
so everything about them lives here, separate from the game code:

  id        never change this once you've written plot that refers to it
  name      what the game shows above their dialogue
  spot      where they sit: (tile x, tile y) on the Park Street map
  pose      "sit" (on cardboard), "sleep" (in a sleeping bag) or "stand"
  facing    which way they look: "down", "left", "right" or "up"
  dog       True = they have a dog with them
  look      optional colours, e.g. dict(coat="#5a4a3a", hat="#7a2a2a"); leave out for a random look
  lines     what they say, one line per press of E. Use a list of lists to give them a different
            conversation each time you talk to them (the last one repeats).

  Night time (from about half eight in the evening until half five in the morning) - all optional:
  night_pose    what they do at night instead ("stand", "sit", "sleep")
  night_facing  which way they face at night
  night_lines   what they say at night (same format as lines)

  flags     anything you like - your own notes/state for the plot (the game doesn't use it yet)
"""

STORY_NPCS = [
    dict(
        id="dez",
        name="Dez",
        spot=(58.5, 17),                 # Park Street Avenue, the steps alley on the north side
        pose="sit", facing="down", dog=False,
        look=dict(coat="#4b5a3c", hat="#7a2e2e"),
        lines=[
            ["...", "You're not from round here, are you?", "Most people walk past. You stopped. That's something."],
            ["Still here. Where else would I be?", "Keep your eyes open on this street. It's not what it looks like."],
        ],
        night_pose="stand", night_facing="down",
        night_lines=[
            ["Can't sit still at night. Not on this street.", "See the ones in the hoods? Don't let them see you watching."],
        ],
        flags={},
    ),
    dict(
        id="maggie",
        name="Maggie",
        spot=(80.5, 16),                 # the Frogmore Street steps alley
        pose="sleep", facing="right", dog=False,            # asleep all day...
        look=dict(coat="#5a3b5e"),
        lines=[
            ["Mm? ...Let a woman sleep, would you.", "Come back when the lights go off. Then we'll talk."],
        ],
        night_pose="stand", night_facing="down",            # ...up and about once it's dark
        night_lines=[
            ["You came back. Good.", "Lights are off in the offices now. That's when this street wakes up.",
             "I don't sleep at night. Somebody has to keep watch."],
            ["Still here? Write it down, love. Write everything down.", "You've got a notebook, haven't you?"],
        ],
        flags={},
    ),
    dict(
        id="fitz",
        name="Fitz",
        spot=(51, 34),                   # Charlotte Street, behind the shops on the south side
        pose="sit", facing="down", dog=True,
        night_pose="sleep", night_facing="right",           # Fitz and Biscuit bed down at night
        night_lines=[["Zzz... not now... Biscuit, quiet..."]],
        look=dict(coat="#2e3e5c", hat="#3a3a3a"),
        lines=[
            ["This is Biscuit. Don't let her eat your shoelaces.", "We've seen things down this alley. Things people want forgotten."],
            ["Biscuit likes you. She's a good judge.", "Not yet. I'll tell you when you're ready."],
        ],
        flags={},
    ),
    dict(
        id="ray",
        name="Ray",
        spot=(89.5, 34),                 # Frog Lane, beside City Hall
        pose="sit", facing="right", dog=False,
        look=dict(coat="#6a4a2a"),
        lines=[
            ["Council lot walk right past me every morning. Every single one.", "I used to work in there, you know. Third floor."],
            ["I know what's in the basement of that building.", "...Forget I said that."],
        ],
        night_lines=[
            ["See that light on, top floor? Every night. Same window.", "Nobody works that late. Nobody."],
        ],
        flags={},
    ),
]
