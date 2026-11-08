"""Everything the characters say, the narration and the stage directions - edit this to change the story's words.

Each scene is a list of lines: (who's speaking, what they say) or (who, what, {stage directions}).
who = "" is narration (no name tag). Click / E / Space moves on to the next line.

Stage directions (all optional):
  face="crime_officer"     the detective and that person turn to face each other
  walk="approach"          the detective walks over to the CRIME_SCENE "approach" spot
  give="token"             put an item in the detective's pocket (see ITEMS)
  leave="crime_daniel"     that person walks off and is gone
  walk_to_player="martin"  that person walks over to the detective
  scene="harbour_john"     start a scene (a TIME ECHO in black and white, or the opening in colour - see echo.py)
  cut="harbour_push"       cut straight to another scene
  end_scene=True           back to the present (the game)
  move=("shadow", (x, y))  someone in the scene walks to (x, y) (tiles)
  push=True                (the last echo) the push into the water
  glitch=1.2               the echo breaks up for this many seconds, then goes on by itself
  black=True               a black screen behind this line
  auto=2.0                 goes on by itself after this many seconds
  view="paper1999"         show a document full screen (see documents.py); view=None puts it away
  ring=True / False        (the opening) the phone ringing
  flame=True / False       (the opening) the lighter
"""

DANIEL_NUMBER = "07700 900 417"
JOHN_SCORE = 5                      # John's high score on Seagull Bird (beat it to get Martin's attention)
JOHN_MACHINE = "seagull"

SPEAKERS = {   # name -> label colour
    "Detective": (240, 196, 90),
    "Police Officer": (120, 170, 255),
    "Daniel": (130, 210, 140),
    "Martin": (250, 140, 90),
    "John": (200, 200, 200),
    "Usher": (230, 120, 120),
    "Emily": (220, 160, 230),
    "Jack": (190, 190, 150),
    "Barista": (230, 150, 120),
    "Shopkeeper": (230, 150, 120),
}

# ------------------------------------------------------------------ the objectives, in order
OBJECTIVES = [
    dict(id="crime_scene", label="Get to the crime scene at the harbourside"),
    dict(id="arcade", label="Go to the Bristol Arcade, where John worked"),
    dict(id="high_score", label="Beat John's high score on Seagull Bird"),
    dict(id="locker", label="Look through John's locker in the store room"),
    dict(id="usher", label="Visit Professor Usher's office in the Wills Memorial Building"),
    dict(id="find_emily", label="Find Emily: ask in the cafés"),
    dict(id="wait_emily", label="Wait for Emily Carter"),
    dict(id="daniel", label="Ask Daniel about 1999 at The Gazette"),
    dict(id="records", label="Find the 1999 staff record in the arcade's store room"),
    dict(id="usher2", label="Go back to Professor Usher's office"),
    dict(id="search", label="Search Professor Usher's office"),
    dict(id="station", label="Catch the bus to Clifton Down (College Green stop) - stop Usher"),
]

# ------------------------------------------------------------------ the pocket items the story gives you
ITEMS = {   # id -> (name, description, icon function name in pixel_art.py)
    "daniel_number": ("Daniel's number", f"Daniel Shaw, journalist. {DANIEL_NUMBER}. He knew John Harper.", "card_icon"),
    "newspaper": ("Newspaper", "The Harbour Gazette: THE BRISTOL PUSHER IS BACK. Enter to read it.", "newspaper_icon"),
    "recorder": ("Audio recorder", "John's. Found on him at the harbour - the water has got into it.", "recorder_icon"),
    "token": ("Arcade token", "An old Bristol Arcade token, from John's locker. They stopped making these in the 90s.", "token_icon"),
    "old_photo": ("Old photograph", "From John's locker. The arcade, years ago.", "photo_icon"),
    "notes": ("John's notes", "Pages of research into old Bristol. Every source is Professor Peter Usher, University of Bristol.",
              "notes_icon"),
    "emily_photo": ("Emily's photograph", "1999. The arcade, with a group of staff in the background. Enter to look at it.",
                    "photo_icon"),
    "cutting": ("1999 newspaper", "JACK HARPER, 31, FOUND DEAD IN THE RIVER. Enter to read it.", "cutting_icon"),
    "record1998": ("Staff record 1998", "The arcade's staff list for 1998. P. Usher is on it. Jack Harper isn't. Enter to read it.",
                   "folder_icon"),
    "record1999": ("Staff record 1999", "The missing binder, from Usher's office. P. Usher - and J. Harper. Enter to read it.",
                   "folder_icon"),
    "ju_photo": ("Photograph of Jack and Usher", "Two young men in arcade uniforms. On the back: \"I know what you did Peter, "
                 "come clear this up with me - Jack\". Enter to look at it.", "photo_icon"),
}

# ------------------------------------------------------------------ the opening: the detective's flat, the night before
OPENING = [
    ("", "Bristol. Late at night.", dict(scene="home", flame=False)),
    ("", "In his flat, a private detective is about to light up a cigarette...", dict(flame=True)),
    ("", "...when the phone rings.", dict(ring=True, flame=False, move=("detective", (6.5, 4.6)))),
    ("Detective", "Hello?", dict(ring=False)),
    ("", "..."),
    ("Detective", "I'll be there."),
    ("", "The next morning, the detective sets off for the harbourside.", dict(black=True)),
    ("", "Follow the compass at the top of the screen. Park Stores sells the morning papers, if you want one on the way.",
     dict(end_scene=True)),
]

# ------------------------------------------------------------------ the crime scene
CRIME_SCENE = [
    ("", "The detective arrives at the crime scene. There are police officers, forensic investigators and a small "
         "cordoned-off area beside the water. John's body has already been removed, but the scene is still being investigated."),
    ("Detective", "What happened?", dict(face="crime_officer")),
    ("Police Officer", "John Harper died from drowning after being pushed into the harbourside river."),
    ("Detective", "Well, who's that over by the cordon strip?", dict(face="crime_daniel")),
    ("Police Officer", "Daniel Shaw. Journalist. He's been asking questions about the Bristol Pusher for a while. "
                       "Apparently, he knew the victim."),
    ("", "The detective approaches him.", dict(walk="approach", face="crime_daniel")),
    ("Detective", "Daniel Shaw?"),
    ("Daniel", "That's me. You're the detective investigating John?"),
    ("Detective", "You knew him?"),
    ("Daniel", "We spoke a few times. He contacted me about some research he was doing into Bristol's history. "
               "Old buildings, businesses, things that have disappeared over the years."),
    ("Detective", "What did that have to do with the Pusher?"),
    ("Daniel", "That's what I wondered. He started asking about the older cases, particularly the first one. "
               "He seemed convinced there was something people had overlooked."),
    ("Detective", "Did he tell you what he'd found?"),
    ("Daniel", "No. But he mentioned the arcade where he worked more than once. Might be worth looking into."),
    ("", "Daniel hands the detective his number.", dict(give="daniel_number")),
    ("Daniel", "Here's my number. Let me know if you find anything."),
    ("Detective", "I will."),
    ("", "Daniel walks away.", dict(leave="crime_daniel")),
]

# ...cut back to the game for a moment, then the officer has John's audio recorder: the first TIME ECHO
RECORDER = [
    ("", "The police officer comes over.", dict(walk_to_player="crime_officer")),
    ("Police Officer", "Detective - one more thing. We found this on him. An audio recorder. The water's got into it."),
    ("", "The officer passes it over.", dict(give="recorder")),
    ("", "As the detective's fingers close around it, the noise of the harbour fades away...", dict(glitch=1.0)),
    ("", "TIME ECHO. When the detective holds something that belonged to someone, he sees a moment it was there for - "
         "in black and white, like an old photograph.", dict(scene="harbour_john")),
    ("", "John Harper is standing by the water. Just standing, looking out."),
    ("", "Footsteps. Someone is coming up behind him.", dict(move=("shadow", (47.6, 51.6)))),
    ("", "A figure, all in shadow, reaches out -", dict(glitch=1.4)),
    ("", "BACK TO THE PRESENT.", dict(black=True)),
    ("Detective", "Daniel said John kept mentioning the arcade where he worked. That's where I'll start.", dict(end_scene=True)),
]

# ------------------------------------------------------------------ the arcade
ARCADE_ENTER = [
    ("", "The Bristol Arcade. Flashing screens, the rattle of the machines, the smell of old carpet."),
    ("Detective", "John worked here. Someone here must have known him."),
    ("", "On the Seagull Bird machine, the high score is still J.HARPER's."),
]
ARCADE_HINT = "HINT: beat the high score on SEAGULL BIRD - someone might come over"

MARTIN = [
    ("", "Someone from behind the counter comes over.", dict(walk_to_player="martin")),
    ("Martin", "Not bad! That was John's high score you just beat. Nobody's been able to beat it in months."),
    ("Detective", "You heard about the murder? It's unfortunate, isn't it?"),
    ("Martin", "Yeah, I was the last one working with him."),
    ("Detective", "How was he acting before?"),
    ("Martin", "He'd been acting strangely for weeks. Kept asking about the arcade's history and spending time in the "
               "old storage room."),
    ("Detective", "What was he looking for?"),
    ("Martin", "Couldn't tell you. But I remember him mentioning someone called Jack. Seemed pretty important to him."),
    ("Detective", "Jack? Who's that?"),
    ("Martin", "Never asked. You could try looking through his locker. He kept a few personal things in there."),
    ("", "Martin gives the detective access to John's locker, in the store room at the back."),
]

LOCKER = [
    ("", "The detective opens John's locker.", dict(view="locker")),
    ("", "Inside: an old arcade token, an old photograph, and some notes.", dict(give=("token", "old_photo", "notes"))),
    ("", "The notes are a mess, but one of the research notes catches your eye with a reference in the bottom: Professor Peter Usher, University of Bristol."),
    ("Detective", "Professor Usher. His office is in the Wills Memorial Building, at the top of Park Street.",
     dict(view=None)),
]

# ------------------------------------------------------------------ Professor Usher's office: the second echo
USHER_OFFICE = [
    ("", "Professor Usher's office, in the Wills Memorial Building. The professor isn't in."),
    ("", "The detective takes out John's notes. Usher's name is on every page. The room begins to fade..."),
    ("John", "I think I've finally noticed something in this photograph.", dict(scene="usher_office")),
    ("Usher", "What is it?"),
    ("John", "Look at the background. There's something there that doesn't seem to fit."),
    ("Usher", "Have you worked out what it is?"),
    ("John", "Not yet. I want to take another look at it."),
    ("Usher", "Perhaps a fresh pair of eyes would help."),
    ("John", "Actually, I'll show it to Emily over coffee. She usually spots things I miss."),
    ("", "The Echo ends.", dict(end_scene=True)),
    ("Detective", "Emily... over coffee. If she's a regular somewhere, someone in one of these cafés will know her."),
]

# ------------------------------------------------------------------ looking for Emily in the cafés (in the order you ask)
CAFE_ASKS = [
    [("Detective", "I'm looking for someone called Emily. Does she come in here?"),
     ("Barista", "Emily? Sorry, doesn't ring a bell.")],
    [("Detective", "Do you know an Emily? She'd have come in with a young man called John."),
     ("Barista", "No Emily here, I'm afraid. Try further up the road.")],
    [("Detective", "I'm looking for an Emily. A regular, maybe?"),
     ("Barista", "Emily? Yeah, we get an Emily in."),
     ("Detective", "Carter?"),
     ("Barista", "Carter? No - ours is Emily Price. Sorry.")],
    [("Detective", "I'm looking for Emily Carter."),
     ("Barista", "Emily Carter? Oh, yeah. She comes in here every day at six. Regular as clockwork."),
     ("Detective", "Then I'll wait.")],
]
CAFE_ASKED_AGAIN = [("Barista", "Like I said - sorry, can't help.")]

EMILY = [
    ("", "Six o'clock. The door opens, and a young woman walks in.", dict(walk_to_player="emily")),
    ("Detective", "Emily Carter?"),
    ("Emily", "...Yes? Who's asking?"),
    ("Detective", "I'm the detective looking into John Harper's death. I'm sorry."),
    ("Emily", "John was going to show me something. We'd been looking through my dad's old photographs."),
    ("Emily", "I've got the one he was so interested in. I still don't know what he saw in it."),
    ("", "The detective picks up the photograph.", dict(give="emily_photo")),
    ("Emily", "I found this in my dad's things. It must be from the late nineties.", dict(scene="cafe_emily")),
    ("John", "Do you know when?"),
    ("Emily", "I think 1999. Why?"),
    ("John", "Look at the arcade in the background.")   ,
    ("", "Emily looks closer."),
    ("Emily", "What about it?"),
    ("John", "That's where I work."),
    ("Emily", "You think there's something there?"),
    ("John", "I know there is. I just need to find out what."),
    ("", "John takes a closer look at the photograph.", dict(view="photo1999")),
    ("", "In the background, a small group of arcade employees can just about be seen."),
    ("", "The Echo ends.", dict(view=None, end_scene=True)),
    ("Detective", "1999. Daniel's paper must have an archive - he'll know what happened that year."),
]

# ------------------------------------------------------------------ Daniel, at The Gazette
DANIEL = [
    ("Daniel", "Detective. Found anything?", dict(face="daniel")),
    ("Detective", "Maybe. What made the news in Bristol in 1999?"),
    ("Daniel", "1999... give me a minute."),
    ("", "Daniel comes back with a bound volume of old papers and opens it on the desk.", dict(view="paper1999")),
    ("", "Jack Harper, 31, found dead in the river. The first victim of the man they would come to call the Bristol Pusher."),
    ("", "The detective turns John's token over in his fingers.", dict(view=None)),
    ("Daniel", "Is that from the 90s?"),
    ("Detective", "Yes. I found this in John's locker.", dict(give="cutting")),
    ("Detective", "The arcade will have kept its staff records. I want to see 1999."),
]

# ------------------------------------------------------------------ the store room: the missing year
RECORDS = [
    ("", "A shelf of old staff records. One binder for every year, the year written big down the spine.", dict(view="shelf")),
    ("", "1996... 1997... 1998... 2000. The 1999 binder is missing."),
    ("Detective", "Someone's taken it."),
    ("", "The detective pulls out 1998 instead.", dict(view="record1998", give="record1998")),
    ("", "The staff list for 1998. P. Usher - floor attendant. No Jack Harper."),
    ("Detective", "Usher worked here. Long before he was a professor.", dict(view=None)),
    ("Detective", "I need to talk to Professor Usher."),
]

# ------------------------------------------------------------------ Usher's office, emptied: the truth
USHER_GONE = [   # walking in the last time - then it's up to you to search the place
    ("", "The office is empty. Books gone from the shelves, drawers pulled out, boxes half packed. "
         "It looks like he was packing to leave."),
    ("Detective", "Where are you going, Professor?"),
    ("", "Search the office. Walk up to things and press E to look at them."),
]

# things to look at in the packed-up office: E at each. (The three that matter: the desk, its drawers, the computer.)
SEARCH_RECORD = [
    ("", "On the desk, under a pile of papers: a binder marked 1999.", dict(view="record1999", give="record1999")),
    ("", "The staff list for 1999. P. Usher... and J. Harper."),
    ("Detective", "Jack Harper. Harper... John was Jack's son.", dict(view=None)),
    ("Detective", "John wasn't researching Bristol's history. He was looking for the man who killed his father."),
    ("", "And Peter Usher found out John was getting too close. He knew when John finished his shift, and that he "
         "took the harbour route home. That is where he attacked him."),
]
SEARCH_DRAWER = [
    ("", "The detective pulls open the desk drawers. Empty... except the bottom one: a photograph, face down. "
         "Two young men in arcade uniforms.", dict(view="ju_photo")),
    ("", "Jack Harper and Peter Usher."),
    ("", "On the back, in faded pen:", dict(view="ju_back")),
    ("", "\"I know what you did Peter, come clear this up with me - Jack\""),
    ("", "The detective touches the photograph.", dict(view=None, give="ju_photo", glitch=0.8)),
    ("Jack", "I know what you've been doing, Peter.", dict(scene="arcade_1999")),
    ("Usher", "You don't know anything."),
    ("Jack", "I've seen the records. I'm not covering for you."),
    ("Usher", "You need to think very carefully about what you're saying."),
    ("Jack", "I'm going to the police."),
    ("Usher", "Then I suppose there's nothing left to discuss."),
    ("", "The scene cuts to the harbourside.", dict(cut="harbour_push")),
    ("", "Jack is standing at the edge of the water. Usher comes up behind him...", dict(move=("usher", (48.7, 43.6)))),
    ("", "...and pushes him in.", dict(push=True)),
    ("", "The echo ends.", dict(end_scene=True)),
    ("", "Peter Usher killed Jack Harper in 1999 - the Bristol Pusher's first victim. After that first time, he "
         "couldn't stop. Every killing since was his."),
]
SEARCH_DESK_EMPTY = [("", "Nothing else in the desk. He's cleared it out.")]
SEARCH_TICKET = [
    ("", "A train ticket, bought this morning. One way, from Clifton Down - leaving today.", dict(view="ticket")),
    ("Detective", "He's running.", dict(view=None)),
]
SEARCH_LOOKS = {   # the other things in the room (a look each - some of it might help, some won't)
    "bookcase": [("", "Half the shelves are bare. Gaps where books have been pulled out and packed - all on old Bristol.")],
    "cabinet": [("", "Department paperwork, exam scripts from years back. One drawer's been emptied completely.")],
    "box1": [("", "Lecture notes, bundled with string. 'Lost businesses of the harbourside, 1980-2000.'")],
    "box2": [("", "A kettle, two mugs and a framed degree certificate: Peter Usher, BA, University of Bristol, 2001.")],
    "box3": [("", "Clothes, thrown in. Packed in a hurry.")],
    "armchair": [("", "A coat's been left over the armchair. In the pocket, a bus timetable - folded open at the "
                      "page for Clifton Down.")],
    "chair": [("", "His desk chair, pushed back. The seat's still warm.")],
}
SEARCH_DONE = [
    ("Detective", "The record, the photograph, the ticket... It was him. All of it."),
    ("Detective", "Clifton Down. The quickest way's the bus from the College Green stop - now."),
]

# ------------------------------------------------------------------ the end (for now)
BUS_RIDE = [
    ("", "The detective jumps on the bus. \"Clifton Down - quick as you can.\""),
    ("", "The bus pulls away up the hill, past the Wills Memorial Building, towards Whiteladies Road."),
]

ENDING = [
    ("", "The bus pulls up outside Clifton Down station. The detective runs for the platforms.", dict(black=True)),
    ("", "Somewhere ahead, Professor Peter Usher is waiting for a train.", dict(black=True)),
]   # ...then the film (art/videos/final.mp4) plays, and it's back to the main menu

# ------------------------------------------------------------------ the morning paper (optional, from Park Stores)
NEWSPAPER_BUY = [
    ("Shopkeeper", "Morning. Paper? They're flying off the shelf today - have you seen the front page?"),
    ("Detective", "I'll take one.", dict(give="newspaper")),
]

PAPER = dict(
    masthead="THE HARBOUR GAZETTE",
    dateline="SATURDAY 7 NOVEMBER 2026", price="90p",
    kicker="BODY FOUND IN THE FLOATING HARBOUR",
    headline="THE BRISTOL PUSHER IS BACK",
    standfirst="...and he will be gone as quick as he came",
    byline="By Daniel Shaw, crime reporter",
    body=[
        "A man found in the water beside the harbourside decks in the early hours of yesterday morning has been "
        "named locally as John Harper, 29, of Bristol.",
        "Police say Mr Harper drowned, and that they believe he was pushed. Officers have cordoned off part of the "
        "waterfront off Anchor Road while forensic teams examine the scene.",
        "It is the first death linked to the so-called Bristol Pusher in eleven years. The killer, who has never "
        "been caught, is thought to have claimed a first victim in the same harbour in 1999.",
        "Mr Harper worked at an arcade on the harbourside and is believed to have been walking home along the "
        "water after his shift. A colleague described him as \"a quiet lad, always reading up on old Bristol.\"",
        "Detectives are appealing for anyone who was near Anchor Road or the harbourside decks late on Thursday "
        "night to come forward.",
    ],
    caption="Police at the scene on the harbourside decks",
    inside=["Harbourside market back this weekend - p4", "Clifton Down: trains delayed again - p7",
            "Weather: drizzle, 11C"],
)

PAPER_1999 = dict(
    masthead="THE HARBOUR GAZETTE",
    dateline="TUESDAY 14 SEPTEMBER 1999", price="35p",
    kicker="HARBOURSIDE TRAGEDY",
    headline="JACK HARPER, 31, FOUND DEAD IN THE RIVER",
    standfirst="Police: \"We are not treating this as an accident\"",
    byline="By our news staff",
    body=[
        "The body of a Bristol man was recovered from the Floating Harbour yesterday morning, close to the "
        "waterfront off Anchor Road.",
        "He has been named as Jack Harper, 31, who worked at an amusement arcade on the harbourside. He leaves a "
        "wife and a two-year-old son.",
        "Mr Harper is thought to have gone into the water late on Sunday night. Police say they are not treating "
        "his death as an accident, and are appealing for witnesses.",
        "Colleagues described him as \"honest to a fault\" and said he had seemed worried in the weeks before he died.",
    ],
    caption="The harbourside, where Mr Harper was found",
    inside=["Eclipse fever: last month's big day in pictures - p6", "New millennium plans for the waterfront - p9",
            "Weather: showers, 16C"],
)

STAFF_1998 = ["Max Doyle - manager", "Peter Usher - floor attendant", "Smith Grant - cashier", "Terrence Okafor - technician",
              "Ray Hale - floor attendant", "Lucifer Morgan - cashier (Saturdays)"]
STAFF_1999 = ["Max Doyle - manager", "Peter Usher - floor attendant", "Jack Harper - floor attendant", "Smith Grant - cashier",
              "Terrence Okafor - technician", "Lucifer Morgan - cashier (Saturdays)"]

TRAINS = [   # Usher's computer, open on the train times
    ("Clifton Down", "Severn Beach", "Platform 1"),
    ("Clifton Down", "Bristol Temple Meads", "Platform 2"),
]
