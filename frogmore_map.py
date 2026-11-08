"""Frogmore Street - down the steps at the end of Park Street, under the bridge. OMG is here.

The bridge (Park Street) crosses overhead; Frogmore Street runs up and down underneath it.
"""

NAME = "Frogmore Street"
ATTRIBUTION = ""
LAMP_STYLE = "modern"

ROWS = [
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHHL=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====---&HHHHHHHHHHH',
    'HHHHH))))L=====---&HHHHHHHHHHH',
    'HHHHH))))-=====----HHHHHHHHHHH',
    'HHHHH////-=====---&HHHHHHHHHHH',
    'HHHHH////-=====-L-&HHHHHHHHHHH',
    'HHHHH-----=====--&-HHHHHHHHHHH',
    'HHHHH-----=====--HHHHHHHHHHHHH',
    '----------=====---------------',
    '----------=====---------------',
    '--------H-=====--H------------',
    '--------H-=====--H------------',
    '--------H-=====--H------------',
    '--------H-=====--H------------',
    '----------=====---------------',
    '----------=====---------------',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHHL=====-LHHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHHL=====-LHHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
    'HHHHHHHHH-=====--HHHHHHHHHHHHH',
]

BUILDING_IDS = [
    '000000000000000000~~~~~~~~~~~~~~~~03030303030303030303030303',
    '000000000000000000~~~~~~~~~~~~~~~~03030303030303030303030303',
    '000000000000000000~~~~~~~~~~~~~~~~03030303030303030303030303',
    '000000000000000000~~~~~~~~~~~~~~~~03030303030303030303030303',
    '010101010101010101~~~~~~~~~~~~~~~~03030303030303030303030303',
    '010101010101010101~~~~~~~~~~~~~~~~03030303030303030303030303',
    '010101010101010101~~~~~~~~~~~~~~~~~~~~0404040404040404040404',
    '0202020202~~~~~~~~~~~~~~~~~~~~~~~~~~~~0404040404040404040404',
    '0202020202~~~~~~~~~~~~~~~~~~~~~~~~~~~~0404040404040404040404',
    '0202020202~~~~~~~~~~~~~~~~~~~~~~~~~~~~0404040404040404040404',
    '0202020202~~~~~~~~~~~~~~~~~~~~~~~~~~~~0404040404040404040404',
    '0202020202~~~~~~~~~~~~~~~~~~~~~~~~~~~~0404040404040404040404',
    '0202020202~~~~~~~~~~~~~~~~~~~~~~~~04040404040404040404040404',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~05~~~~~~~~~~~~~~~~06~~~~~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~05~~~~~~~~~~~~~~~~06~~~~~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~05~~~~~~~~~~~~~~~~06~~~~~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~05~~~~~~~~~~~~~~~~06~~~~~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
    '070707070707070707~~~~~~~~~~~~~~~~08080808080808080808080808',
]

TOWER_TILES = []

# Park Street overhead: rows y0-y1 are under the bridge; lift = how high the deck is drawn (px)
BRIDGE = dict(y0=13, y1=20, lift=104, grey=True, rail_x=(10, 14))
BRIDGE_TRAFFIC = dict(lanes=[(15.9, 1), (17.9, -1)], lift=104, sort=21 * 64 + 60)
# cars on Frogmore Street (keep left: going down the screen on the right-hand lane)
LOWER_ROAD = dict(lanes=[(13.7, 1), (11.3, -1)], y0=0, y1=34, solid=True)
STAIRS = dict(y_light=9, y_dark=10, k_dark=0.7, rect=(5.0, 7.0, 9.0, 11.0), path=[(5.0, 9.0, 7.0, 11.0, "bottom"), (5.0, 7.0, 9.0, 9.0, "left"), (7.0, 9.0, 9.0, 11.0, "top")], mode="rise", open_top=True, depth=44)
PORTALS = [dict(rect=(5.0, 10.6, 7.0, 11.0), dir='down', to='Park Street', spawn=(69.0, 19.6), facing='down')]
NEON = [(16.6, 1.8, 200, (255, 80, 210), 0.95), (16.4, 3.6, 130, (255, 190, 230), 0.7), (9.4, 5.3, 150, (255, 200, 140), 0.8)]
# the fronts of the buildings that face across the road (doors, awnings, signs)
SIDE_STRIPS = [{'kind': 'brick', 'x': 9, 'y0': 0, 'rows': 4, 'facing': 'east', 'doors': [1, 3]}, {'kind': 'restaurant', 'x': 9, 'y0': 4, 'rows': 3, 'facing': 'east', 'doors': [5], 'sign': 'VERDE'}, {'kind': 'omg', 'x': 17, 'y0': 0, 'rows': 6, 'facing': 'west', 'doors': [3]}, {'kind': 'graffiti', 'x': 19, 'y0': 6, 'rows': 6, 'facing': 'west'}, {'kind': 'graffiti', 'x': 17, 'y0': 12, 'rows': 1, 'facing': 'west'}]
# you can't go under the bridge or beyond it (it's the edge of Frogmore Street)
BLOCKERS = [(0, 13.0, 30, 13.4), (8.92, 7.0, 9.08, 10.0), (5.0, 11.0, 9.0, 13.0)]   # + the railing between the steps and the pavement
# the top of the steps (up by the restaurant) and the bridge are the upper level: you can see them, greyed out
GREY_AREAS = []
RAILS_V = [(9, 7, 9)]
STAIR_SPLITS = [7]
STAIR_OPEN = [(8, 10, 1)]   # gap in the wall at the bottom right: off the steps onto the pavement
PAVEMENT_XS = [9.5, 15.6]
WALK_RANGE = (0.6, 12.6)
# people who stand about: (x, y, facing, role, (from, to) hours)
EXTRA_PEOPLE = [(16.55, 3.95, 'down', 'bouncer', (21.5, 28.5)), (16.5, 4.9, 'up', 'clubber', (22, 26.5)), (16.4, 5.7, 'up', 'clubber', (22.2, 27)), (16.55, 6.5, 'up', 'drunk', (22.5, 26.8)), (16.4, 7.3, 'up', 'clubber', (23, 26.5)), (16.5, 8.1, 'up', 'clubber', (23.2, 26)), (17.5, 7.4, 'right', 'nightowl', (22, 28)), (17.6, 9.2, 'up', 'dancer', (22.5, 27.5)), (9.4, 8.4, 'right', 'shady', (21, 29)), (17.5, 10.6, 'up', 'shady', (22, 29)), (9.3, 3.6, 'down', 'public', (11, 22))]

GROUND_SHAPES = []

SHOPS = [
    {'building': 1, 'kind': 'cafe', 'door': (8, 5), 'side': 'east', 'brand': 'TRATTORIA VERDE', 'centre': 8.0},
    {'building': 3, 'kind': 'club', 'door': (17, 3), 'side': 'west', 'brand': 'OMG', 'centre': 17.0},
]

BUILDINGS = [
    {'style': 'H', 'stone': (150, 70, 52), 'roof': (120, 120, 118), 'variant': 0, 'seed': 11841, 'floors': 3, 'shop': False, 'kind': None, 'awning': None},
    {'style': 'H', 'stone': (34, 92, 60), 'roof': (120, 120, 118), 'variant': 0, 'seed': 25722, 'floors': 3, 'shop': True, 'kind': 'cafe', 'awning': (34, 92, 60)},
    {'style': 'P', 'stone': (96, 92, 88), 'roof': (120, 120, 118), 'variant': 0, 'seed': 19657, 'floors': 2, 'shop': False, 'kind': None, 'awning': None, 'pennant': True},
    {'style': 'O', 'stone': (52, 46, 58), 'roof': (120, 120, 118), 'variant': 2, 'seed': 96910, 'floors': 3, 'shop': True, 'kind': 'club', 'awning': None, 'brand': None},
    {'style': 'X', 'stone': (204, 196, 176), 'roof': (120, 120, 118), 'variant': 0, 'seed': 39673, 'floors': 3, 'shop': False, 'kind': None, 'awning': None, 'graffiti': True},
    {'style': 'P', 'stone': (172, 170, 164), 'roof': (120, 120, 118), 'variant': 0, 'seed': 10441, 'floors': 2, 'shop': False, 'kind': None, 'awning': None},
    {'style': 'P', 'stone': (172, 170, 164), 'roof': (120, 120, 118), 'variant': 0, 'seed': 97928, 'floors': 2, 'shop': False, 'kind': None, 'awning': None},
    {'style': 'X', 'stone': (172, 170, 164), 'roof': (120, 120, 118), 'variant': 0, 'seed': 24087, 'floors': 2, 'shop': False, 'kind': None, 'awning': None, 'graffiti': True},
    {'style': 'X', 'stone': (172, 170, 164), 'roof': (120, 120, 118), 'variant': 0, 'seed': 39575, 'floors': 2, 'shop': False, 'kind': None, 'awning': None, 'graffiti': True},
]
