import pygame
import random
from sys import exit
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.toggle import Toggle

#region GAME PROPERTIES AND DEBUG

# SCREEN DIMENSIONS AND DEBUG

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
FPS = 60 # game fps
DISPLAY_HITBOXES = False

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

current_game = None
current_menu = None
callbacks = []
bgm_loaded = False
current_bgm = None
hicontrast = False
in_cutscene = False
ai_game = False

PAUSE_MENU = None
paused_game = None

# SETTINGS

bgm_volume = 1
sfx_volume = 1

#endregion

# SPRITES AND ANIMATION

ANIMATION_LATENCY = 10 # every ANIMATION_LATENCY frames, change animation frame
X_OFFSET_RTL = 30
X_OFFSET_LTR = 25

# DIRECTIONS

RIGHT = 1
LEFT = -1

# COLOUR DEFS

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (250, 164, 5)
GREEN = (5, 250, 9)
GRAY = (120, 120, 120)

# ANIMATION STATES

class AnimatedSprite(object):
    def __init__(self, name, spritesheet, length):
        self.name = name
        self.spritesheet = spritesheet
        self.length = length

DEFAULT_IDLE = AnimatedSprite("IDLE", "assets/spritesheet_idle.png", 4)
DEFAULT_RUNNING = AnimatedSprite("RUNNING", "assets/spritesheet_run.png", 4)
DEFAULT_PUNCHING = AnimatedSprite("PUNCHING", "assets/spritesheet_punch.png", 4)
DEFAULT_KICKING = AnimatedSprite("KICKING", "assets/spritesheet_kick.png", 4)
DEFAULT_JUMPING = AnimatedSprite("JUMPING", "assets/spritesheet_jump.png", 1)
DEFAULT_FLINCHING = AnimatedSprite("FLINCHING", "assets/spritesheet_flinch.png", 3)
DEFAULT_COLLAPSING = AnimatedSprite("COLLAPSING", "assets/spritesheet_collapse.png", 3)
DEFAULT_DEAD = AnimatedSprite("DEAD", "assets/spritesheet_dead.png", 1)

MUSK_IDLE = AnimatedSprite("IDLE", "assets/musk_idle.png", 4)
MUSK_RUNNING = AnimatedSprite("RUNNING", "assets/musk_run.png", 4)
MUSK_PUNCHING = AnimatedSprite("PUNCHING", "assets/musk_punch.png", 4)
MUSK_KICKING = AnimatedSprite("KICKING", "assets/musk_kick.png", 4)
MUSK_JUMPING = AnimatedSprite("JUMPING", "assets/musk_jump.png", 1)
MUSK_FLINCHING = AnimatedSprite("FLINCHING", "assets/musk_flinch.png", 3)
MUSK_COLLAPSING = AnimatedSprite("COLLAPSING", "assets/musk_collapse.png", 3)
MUSK_DEAD = AnimatedSprite("DEAD", "assets/musk_dead.png", 1)

TIM_IDLE = AnimatedSprite("IDLE", "assets/tim_idle.png", 4)
TIM_RUNNING = AnimatedSprite("RUNNING", "assets/tim_run.png", 4)
TIM_PUNCHING = AnimatedSprite("PUNCHING", "assets/tim_punch.png", 4)
TIM_KICKING = AnimatedSprite("KICKING", "assets/tim_kick.png", 4)
TIM_JUMPING = AnimatedSprite("JUMPING", "assets/tim_jump.png", 1)
TIM_FLINCHING = AnimatedSprite("FLINCHING", "assets/tim_flinch.png", 3)
TIM_COLLAPSING = AnimatedSprite("COLLAPSING", "assets/tim_collapse.png", 3)
TIM_DEAD = AnimatedSprite("DEAD", "assets/tim_dead.png", 1)

BILL_IDLE = AnimatedSprite("IDLE", "assets/bill_idle.png", 4)
BILL_RUNNING = AnimatedSprite("RUNNING", "assets/bill_run.png", 4)
BILL_PUNCHING = AnimatedSprite("PUNCHING", "assets/bill_punch.png", 4)
BILL_KICKING = AnimatedSprite("KICKING", "assets/bill_kick.png", 4)
BILL_JUMPING = AnimatedSprite("JUMPING", "assets/bill_jump.png", 1)
BILL_FLINCHING = AnimatedSprite("FLINCHING", "assets/bill_flinch.png", 3)
BILL_COLLAPSING = AnimatedSprite("COLLAPSING", "assets/bill_collapse.png", 3)
BILL_DEAD = AnimatedSprite("DEAD", "assets/bill_dead.png", 1)

MARK_IDLE = AnimatedSprite("IDLE", "assets/mark_idle.png", 4)
MARK_RUNNING = AnimatedSprite("RUNNING", "assets/mark_run.png", 4)
MARK_PUNCHING = AnimatedSprite("PUNCHING", "assets/mark_punch.png", 4)
MARK_KICKING = AnimatedSprite("KICKING", "assets/mark_kick.png", 4)
MARK_JUMPING = AnimatedSprite("JUMPING", "assets/mark_jump.png", 1)
MARK_FLINCHING = AnimatedSprite("FLINCHING", "assets/mark_flinch.png", 3)
MARK_COLLAPSING = AnimatedSprite("COLLAPSING", "assets/mark_collapse.png", 3)
MARK_DEAD = AnimatedSprite("DEAD", "assets/mark_dead.png", 1)

DUMMY_IDLE = AnimatedSprite("IDLE", "assets/mannequin_idle.png", 1)
DUMMY_FLINCHING = AnimatedSprite("FLINCHING", "assets/mannequin_flinch.png", 3)

DEFAULT_CHARACTER = [DEFAULT_IDLE, DEFAULT_RUNNING, DEFAULT_PUNCHING, DEFAULT_KICKING, DEFAULT_JUMPING, DEFAULT_FLINCHING, DEFAULT_COLLAPSING, DEFAULT_DEAD]

MUSK_CHARACTER = [MUSK_IDLE, MUSK_RUNNING, MUSK_PUNCHING, MUSK_KICKING, MUSK_JUMPING, MUSK_FLINCHING, MUSK_COLLAPSING, MUSK_DEAD]

TIM_CHARACTER = [TIM_IDLE, TIM_RUNNING, TIM_PUNCHING, TIM_KICKING, TIM_JUMPING, TIM_FLINCHING, TIM_COLLAPSING, TIM_DEAD]

BILL_CHARACTER = [BILL_IDLE, BILL_RUNNING, BILL_PUNCHING, BILL_KICKING, BILL_JUMPING, BILL_FLINCHING, BILL_COLLAPSING, BILL_DEAD]

MARK_CHARACTER = [MARK_IDLE, MARK_RUNNING, MARK_PUNCHING, MARK_KICKING, MARK_JUMPING, MARK_FLINCHING, MARK_COLLAPSING, MARK_DEAD]

DUMMY_CHARACTER = [DUMMY_IDLE, DUMMY_FLINCHING]

p1_character = DEFAULT_CHARACTER
p2_character = DEFAULT_CHARACTER

# FONT AND TEXT

fontsize = 28
FONTFACE = "assets/fontface.ttf"

font = pygame.font.Font(FONTFACE, fontsize)

TITLE_FONT = pygame.font.Font(FONTFACE, 40)
SUBTITLE_FONT = pygame.font.Font(FONTFACE, 36)
SMALLER_FONT = pygame.font.Font(FONTFACE, 20)

screen.fill(WHITE) # change bg color to white
pygame.display.set_caption("MVB KOMBAT") # changes title of game

GRAVITY = 1

# PLAYER MODIFIABLE ATTRIBUTES

PLAYER_SPEED = 7
PLAYER_JUMPSPEED = -16
PLAYER_SPRITE_HEIGHT = 128
PLAYER_SPRITE_WIDTH = 128
PLAYER_HEALTH = 100

PLAYER_HITBOX_WIDTH = 50
PLAYER_HITBOX_HEIGHT = 60

ground_y = (SCREEN_HEIGHT + PLAYER_SPRITE_HEIGHT) / 2

PLAYER1_SPAWN_POSITION = ((SCREEN_WIDTH + PLAYER_SPRITE_WIDTH) / 5, ground_y)
PLAYER1_KEYLEFT = pygame.K_a
PLAYER1_KEYRIGHT = pygame.K_d
PLAYER1_KEYJUMP = pygame.K_w
PLAYER1_KEYDUCK = pygame.K_s
PLAYER1_KEYPUNCH = pygame.K_j
PLAYER1_KEYKICK = pygame.K_k
PLAYER1_KEYDODGE = pygame.K_l

PLAYER2_SPAWN_POSITION = (2 * (SCREEN_WIDTH + PLAYER_SPRITE_WIDTH) / 3, ground_y)
PLAYER2_KEYLEFT = pygame.K_LEFT
PLAYER2_KEYRIGHT = pygame.K_RIGHT
PLAYER2_KEYJUMP = pygame.K_UP
PLAYER2_KEYDUCK = pygame.K_DOWN
PLAYER2_KEYPUNCH = pygame.K_PERIOD
PLAYER2_KEYKICK = pygame.K_SLASH
PLAYER2_KEYDODGE = pygame.K_COMMA

NO_KEY = pygame.K_UNKNOWN

class Hitbox(object):
    def __init__(self, surface, player):
        self.player_ref = player
        self.surface_ref = surface
        self.image = pygame.Surface((PLAYER_HITBOX_WIDTH, PLAYER_HITBOX_HEIGHT))
        if (DISPLAY_HITBOXES): self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = self.player_ref.rect.center

    def update(self):
        # sort out these magic constants
        self.rect.x = self.player_ref.rect.x + 10
        self.rect.y = self.player_ref.rect.y + 45
        if (self.player_ref.direction_facing == LEFT):
            self.rect.x += 60

    def draw(self):
        self.surface_ref.blit(self.image, self.rect) # draw to screen

DODGE_COOLDOWN_FRAMES = 30 # 30 frames
DODGE_GRACE_PERIOD_FRAMES = 15 # 15 frames grace period
DODGE_MOVE_DISTANCE = 40

class Player(pygame.sprite.Sprite):
    def __init__(self, surface, key_left, key_right, key_jump, key_duck, key_punch, key_kick, key_dodge, spawn_position, direction, healthbar_offset, sprites, game, health, display_healthbar, tutorial):
        super().__init__()
        
        # other attributes
        self.surface_ref = surface
        self.opponent_ref = None
        self.opponent_hitbox_ref = None
        self.game_ref = game
        self.tutorial_ref = tutorial

        # gameplay
        self.frozen = False
        self.health = health
        self.dead = False
        self.display_healthbar = display_healthbar
        self.direction_facing = direction
        self.is_jumping = False
        self.is_ducking = False
        self.speed = PLAYER_SPEED
        self.vertical_velocity = 0

        self.punched = False
        self.kicked = False
        self.dodging = False
        self.dodge_on_cooldown = False

        self.key_left = key_left
        self.key_right = key_right
        self.key_jump = key_jump
        self.key_duck = key_duck
        self.key_punch = key_punch
        self.key_kick = key_kick
        self.key_dodge = key_dodge

        self.spawn_position = spawn_position

        # animations
        self.sprite_handler = SpriteHandler(self, ANIMATION_LATENCY, self.game_ref)
        self.load_sprites(sprites)
        
        self.image = pygame.Surface((PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.center = self.spawn_position
        self.rect.y = ground_y - PLAYER_HITBOX_HEIGHT # ground player

        self.go_idle()

        if (not self.display_healthbar): healthbar_offset = (-100, -100)
        self.healthbar = HealthBar(self.health, self.surface_ref, healthbar_offset)

        self.ignoring_platforms = False

        # combo tracking 
        self.input_buffer = []
        self.input_frame = 0
        self.COMBO_WINDOW_FRAMES = 100
    
    def reset(self):
        self.opponent_ref = None
        self.opponent_hitbox_ref = None
        self.frozen = False
        self.health = PLAYER_HEALTH
        self.dead = False
        self.is_jumping = False
        self.is_ducking = False
        self.speed = PLAYER_SPEED
        self.vertical_velocity = 0
        self.punched = False
        self.kicked = False
        self.dodging = False
        self.dodge_on_cooldown = False
        self.rect.center = self.spawn_position
        self.rect.y = ground_y - PLAYER_HITBOX_HEIGHT # ground player
        self.go_idle()
        self.ignoring_platforms = False
        self.input_buffer = []
        self.input_frame = 0
        self.COMBO_WINDOW_FRAMES = 100

    def reset_sprite(self, new_sprites):
        self.sprite_handler.clear_anims()
        self.load_sprites(new_sprites)

    def reset_position(self):
        self.rect.center = self.spawn_position
        self.rect.y = ground_y - PLAYER_HITBOX_HEIGHT # ground player

    def unignore_platforms(self):
        self.ignoring_platforms = False

    def load_sprites(self, sprites):
        for sprite in sprites:
            spritesheet = Spritesheet(sprite.spritesheet)
            self.sprite_handler.add_anim(sprite.name, spritesheet.load_image_strip((0, 0, 64, 64), sprite.length))

    def record_input(self, action):
        self.input_buffer.append((action, self.input_frame))
        cutoff = self.input_frame - self.COMBO_WINDOW_FRAMES

        # keep only recent inputs
        self.input_buffer = [(a,f) for (a,f) in self.input_buffer if f >= cutoff]
        self.check_combos()

    def check_combos(self):
        seq = [a for (a, f) in self.input_buffer]
        if len(seq) < 3: return

        last3 = seq[-3:]
        if last3 == ['KICK', 'PUNCH', 'PUNCH'] or last3 == ['KICK', 'KICK', 'DODGE']:
            # consume combo entries so it doesn't repeatedly fire
            self.input_buffer = []
            self.trigger_large_attack()

    def dead_animation(self):
        self.current_animation = "DEAD"
        if (self.current_animation in self.sprite_handler.anims):
            self.sprite_handler.update_sprite(self.current_animation)
        return

    def update(self):
        if (self.dead): return

        if (self.health <= 0):
            if (self.game_ref.game_timer): self.game_ref.game_timer.kill()
            SWIPESPRITE.change_sprite(GAME_OVER_SPRITE)
            SWIPESPRITE.do_swipesprite_effect()
            self.dead = True
            for player in self.game_ref.players:
                player.period_freeze(80)
            Callback(game_end_sequence, 80)
            self.current_animation = "COLLAPSING"
            if (self.current_animation in self.sprite_handler.anims):
                self.sprite_handler.update_sprite(self.current_animation)
            Callback(self.dead_animation, ANIMATION_LATENCY * 3)
            return

        global current_game
        if (not current_game): return

        self.healthbar.update(f"{self.health}", self.health) # update healthbar
        
        self.input_frame += 1

        keystate = pygame.key.get_pressed()

        # JUMPING AND FALLING
        grounded = self.check_grounded()

        # if not jumping and not grounded, start falling
        if (not self.is_jumping) and (not self.is_ducking) and (not grounded):
            self.vertical_velocity = 0
            self.is_jumping = True
            # falling animation
            self.current_animation = "JUMPING"
            if not (self.current_animation in self.sprite_handler.anims): return
            self.sprite_handler.update_sprite(self.current_animation)

        if (self.is_jumping or self.vertical_velocity != 0):
            self.vertical_velocity += GRAVITY
            self.rect.y += self.vertical_velocity

            if (self.vertical_velocity >= 0) and not self.ignoring_platforms:
                for obj in self.game_ref.interactable_game_objects:
                    if (self.rect.colliderect(obj.rect)):
                        if (self.rect.bottom - self.vertical_velocity <= obj.rect.top): # dont fall into object
                            self.rect.bottom = obj.rect.top
                            self.is_jumping = False
                            self.vertical_velocity = 0
                            self.go_idle()
                            return

            if (self.rect.y >= (ground_y - PLAYER_HITBOX_HEIGHT) and (self.vertical_velocity >= 0)):
                self.rect.y = (ground_y - PLAYER_HITBOX_HEIGHT)
                self.is_jumping = False
                self.vertical_velocity = 0
                self.go_idle()

        # OTHER PLAYER ACTIONS

        if self.frozen: return # do nothing if frozen

        # move based on key input
        if keystate[self.key_left]:
            move_x = -self.get_move_left()
            self.direction_facing = LEFT
            
            if (self.direction_facing == RIGHT):
                self.image = pygame.transform.flip(self.image, 1, 0)
                self.rect.move_ip(-X_OFFSET_RTL, 0)
            
            if grounded:
                step_height = 15
                predicted_rect = self.rect.copy()
                predicted_rect.move_ip(move_x, 0)
                
                stepped_up = False
                for obj in self.game_ref.interactable_game_objects:
                    if predicted_rect.colliderect(obj.rect):
                        predicted_rect_up = predicted_rect.copy()
                        predicted_rect_up.move_ip(0, -step_height)
                        
                        if (self.rect.bottom <= obj.rect.top + step_height) and \
                           (predicted_rect_up.bottom >= obj.rect.top) and \
                           (predicted_rect_up.left < obj.rect.right) and \
                           (predicted_rect_up.right > obj.rect.left):
                            
                            self.rect.move_ip(move_x, -(self.rect.bottom - obj.rect.top))
                            self.rect.bottom = obj.rect.top
                            stepped_up = True
                            break
                
                if not stepped_up:
                    self.rect.move_ip(move_x, 0)
            
            else:
                self.rect.move_ip(move_x, 0)

            if (self.tutorial_ref): 
                self.tutorial_ref.do_tutorial()
                self.tutorial_ref.has_moved = True

        is_moving = keystate[self.key_left] or keystate[self.key_right]

        if grounded and not self.is_jumping and not self.is_ducking:
            if is_moving:
                if self.current_animation != "RUNNING":
                    self.current_animation = "RUNNING"
                    self.sprite_handler.update_sprite("RUNNING")
            else:
                if (self.current_animation != "IDLE") and (self.current_animation != "PUNCHING") and (self.current_animation != "KICKING"):
                    self.go_idle()

        if keystate[self.key_right]:
            if (self.direction_facing == LEFT):
                # we have switched directions
                self.image = pygame.transform.flip(self.image, 1, 0)
                self.rect.move_ip(X_OFFSET_LTR, 0)
            self.rect.move_ip(self.get_move_right(), 0)
            if (self.tutorial_ref): 
                self.tutorial_ref.do_tutorial()
                self.tutorial_ref.has_moved = True

        # can only duck or jump if on ground
        # fall through platform if both pressed at same time
        if keystate[self.key_jump] and (not self.is_ducking) and (not self.is_jumping):
            self.jump()
            if (self.tutorial_ref): 
                self.tutorial_ref.do_tutorial()
                self.tutorial_ref.has_jumped = True
        elif keystate[self.key_duck] and (not self.is_ducking) and (not self.is_jumping):
            self.fall_through()

        # attacks
        if keystate[self.key_punch] and (not self.is_ducking) and (not self.punched) and (not self.kicked):
            self.punch_attack()
            if (self.tutorial_ref): 
                self.tutorial_ref.do_tutorial()
                self.tutorial_ref.has_punched = True
        if keystate[self.key_kick] and (not self.is_ducking) and (not self.kicked) and (not self.punched):
            self.kick_attack()
            if (self.tutorial_ref): 
                self.tutorial_ref.do_tutorial()
                self.tutorial_ref.has_kicked = True

        if keystate[self.key_dodge] and (not self.dodging) and (not self.dodge_on_cooldown) and (not self.is_ducking) and (not self.is_jumping) and grounded:
            self.dodge_attack()

            if (self.tutorial_ref): 
                self.tutorial_ref.do_tutorial()
                self.tutorial_ref.has_dodged = True

        if (self.rect.x < 0): self.rect.x = 0
        if ((SCREEN_WIDTH - PLAYER_SPRITE_WIDTH) < self.rect.x): self.rect.x = (SCREEN_WIDTH - PLAYER_SPRITE_WIDTH)

        if (self.current_animation == "IDLE") and (random.randint(1, 1000) <= 5): # gradually regen health
            if (self.health >= 98 and self.health < 100): self.health += (100 - self.health)
            elif (self.health < 97): self.health += random.randint(1,2)

    def check_grounded(self):
        if (self.rect.y >= (ground_y - PLAYER_HITBOX_HEIGHT)): # if standind on the main ground 
            return True
        
        self.rect.y += 1
        grounded = False
        for obj in self.game_ref.interactable_game_objects:
            if (self.rect.colliderect(obj.rect) and (obj.rect.top >= self.rect.bottom - 1)): # if colliding with any platforms, is grounded
                grounded = True
                break

        self.rect.y -= 1
        return grounded

    def get_move_left(self):
        self.direction_facing = LEFT
        if (self.rect.x < self.speed): return self.rect.x
        else: return self.speed 

    def get_move_right(self):
        self.direction_facing = RIGHT
        if ((SCREEN_WIDTH - PLAYER_SPRITE_WIDTH) - self.rect.x < self.speed): return (SCREEN_WIDTH - PLAYER_SPRITE_WIDTH) - self.rect.x
        else: return self.speed

    def go_idle(self):
        self.current_animation = "IDLE"
        self.sprite_handler.update_sprite(self.current_animation)

    def attach_opponent(self, opponent, opponent_hitbox):
        self.opponent_ref = opponent
        self.opponent_hitbox_ref = opponent_hitbox

    def unpunch(self):
        self.punched = False

    def punch_attack(self):
        # freeze for 1/2 second
        self.punched = True
        Callback(self.unpunch, DEFAULT_PUNCHING.length * ANIMATION_LATENCY + 5)

        self.record_input("PUNCH") # for combos

        # do punch attack
        attack = PunchAttack(self, self.opponent_hitbox_ref, self.direction_facing, self.surface_ref, self.game_ref, damage=random.randint(10, 15))
        self.game_ref.attacks.append(attack)

        repeat = Repeat(attack.follow_player, 1)
        Callback(repeat.kill, DEFAULT_PUNCHING.length * ANIMATION_LATENCY)

        self.do_animation_and_reset("PUNCHING")

    def unkick(self):
        self.kicked = False

    def kick_attack(self):
        # freeze for 1/2 second
        self.kicked = True
        Callback(self.unkick, DEFAULT_KICKING.length * ANIMATION_LATENCY + 5)

        self.record_input("KICK") # for combos

        attack = KickAttack(self, self.opponent_hitbox_ref, self.direction_facing, self.surface_ref, self.game_ref, damage=random.randint(10, 15))
        self.game_ref.attacks.append(attack)

        repeat = Repeat(attack.follow_player, 1)
        Callback(repeat.kill, DEFAULT_KICKING.length * ANIMATION_LATENCY)

        self.do_animation_and_reset("KICKING")

    def trigger_large_attack(self):
        # print("large attack")
        # stop other attacks
        self.punched = True
        # go back to normal after large attack done
        Callback(self.unpunch, DEFAULT_PUNCHING.length * ANIMATION_LATENCY + 5)
        
        heavy_damage = random.randint(40, 50)
        heavy_stun = 80
        heavy_attack = PunchAttack(self, self.opponent_hitbox_ref, self.direction_facing, self.surface_ref, self.game_ref, damage=heavy_damage, stun_time=heavy_stun)
        
        self.game_ref.attacks.append(heavy_attack)
        
        repeat = Repeat(heavy_attack.follow_player, 1)
        Callback(repeat.kill, DEFAULT_PUNCHING.length * ANIMATION_LATENCY)

        # play punch animation
        self.do_animation_and_reset("PUNCHING")

    def do_animation_and_reset(self, anim):
        self.current_animation = anim
        if not (self.current_animation in self.sprite_handler.anims): return # we have not defined this animation
        self.sprite_handler.update_sprite(self.current_animation)
        Callback(self.go_idle, len(self.sprite_handler.anims[self.current_animation]) * ANIMATION_LATENCY)

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.vertical_velocity = PLAYER_JUMPSPEED 
            self.current_animation = "JUMPING"
            if not (self.current_animation in self.sprite_handler.anims): return
            self.sprite_handler.update_sprite(self.current_animation)

    def fall_through(self):
        is_on_platform = False
        if (self.rect.y < (ground_y - PLAYER_HITBOX_HEIGHT)): 
            self.rect.y += 1 
            for obj in self.game_ref.interactable_game_objects:
                if self.rect.colliderect(obj.rect):
                    is_on_platform = True
                    break
            self.rect.y -= 1 
            
        if is_on_platform and not self.ignoring_platforms:
            self.ignoring_platforms = True
            Callback(self.unignore_platforms, 5)
            
            self.is_jumping = True
            self.vertical_velocity = GRAVITY * 2
            
            self.current_animation = "JUMPING"
            if not (self.current_animation in self.sprite_handler.anims): 
                self.sprite_handler.update_sprite(self.current_animation)

    def undodge(self):
        self.dodging = False
        self.unfreeze()

    def reset_dodge_cooldown(self):
        self.dodge_on_cooldown = False

    def get_dash_left(self):
        self.direction_facing = LEFT
        if (self.rect.x < DODGE_MOVE_DISTANCE): return self.rect.x
        else: return DODGE_MOVE_DISTANCE 

    def get_dash_right(self):
        self.direction_facing = RIGHT
        if ((SCREEN_WIDTH - PLAYER_SPRITE_WIDTH) - self.rect.x < DODGE_MOVE_DISTANCE): return (SCREEN_WIDTH - PLAYER_SPRITE_WIDTH) - self.rect.x
        else: return DODGE_MOVE_DISTANCE

    def dodge_attack(self):
        if (self.is_jumping) or (self.is_ducking) or (self.frozen) or (self.dodge_on_cooldown): return

        self.dodging = True
        self.dodge_on_cooldown = True

        self.record_input("DODGE") # for combos

        sfx = WHOOSH
        sfx.play()
        
        Callback(self.undodge, DODGE_GRACE_PERIOD_FRAMES)
        Callback(self.reset_dodge_cooldown, DODGE_COOLDOWN_FRAMES)
        
        move_amount = 0

        if (self.direction_facing == LEFT): move_amount = self.get_dash_left()
        else: move_amount = self.get_dash_right()

        move_amount = DODGE_MOVE_DISTANCE * self.direction_facing
        self.rect.move_ip(move_amount, 0)
        self.period_freeze(DODGE_GRACE_PERIOD_FRAMES)
        self.do_animation_and_reset("DODGING")

    def damage(self, amount, stun_time, source_direction=None):
        if (self.dodging): return

        self.health -= amount
        # print(f"player damaged {amount} hp and now has {self.health} hp left")

        hurt_sound = HURT
        hurt_sound.play()

        special = False
        if (amount > 30): special = True
        HitNotif(amount, self, self.surface_ref, special)

        health_ratio = max(self.health, 0) / PLAYER_HEALTH
        # print(health_ratio)

        if source_direction is None:
            if self.opponent_ref:
                source_direction = self.opponent_ref.direction_facing
            else:
                source_direction = -self.direction_facing

        KNOCKBACK_H_MULT = 14
        KNOCKBACK_V_MULT = -9

        knock_x = int(KNOCKBACK_H_MULT / max(health_ratio, 0.6)) * source_direction
        knock_y = int(KNOCKBACK_V_MULT / max(health_ratio, 0.6))

        self.rect.move_ip(knock_x, 0)
        self.is_jumping = True
        self.vertical_velocity = knock_y

        # freeze for stun period
        self.frozen = True
        Callback(self.unfreeze, stun_time)

        # print("yes")
        self.do_animation_and_reset("FLINCHING")

    def period_freeze(self, time):
        self.frozen = True
        Callback(self.unfreeze, time)

    def freeze(self):
        self.frozen = True

    def unfreeze(self):
        self.frozen = False
        
    def draw(self):
        self.surface_ref.blit(self.image, self.rect) # draw to screen

class AI_Player(Player):
    def __init__(self, surface, key_left, key_right, key_jump, key_duck, key_punch, key_kick, key_dodge, spawn_position, direction, healthbar_offset, sprites, game, health, display_healthbar, tutorial):
        super().__init__(surface, key_left, key_right, key_jump, key_duck, key_punch, key_kick, key_dodge, spawn_position, direction, healthbar_offset, sprites, game, health, display_healthbar, tutorial)
        
        self.decision_timer = 0
        self.decision_interval = 15  # frames to wait before next action
        
    def update(self):
        if (self.dead): return
        
        super().update()
        
        # could become dead after update
        if (self.frozen or self.dead): return
            
        self.decision_timer += 1
        
        # if we waited long enough to make a decision
        if (self.decision_timer >= self.decision_interval):
            self.decision_timer = 0
            self.make_move_decision()
    
    def make_move_decision(self):
        if (not self.opponent_ref) or (not self.opponent_hitbox_ref): return
            
        opponent_dist = abs(self.rect.centerx - self.opponent_ref.rect.centerx)
        range = PUNCH_ATTACK_WIDTH + PLAYER_HITBOX_WIDTH

        # maybe we can reach player using a jump
        x_diff = self.opponent_ref.rect.x - self.rect.x
        y_diff = self.opponent_ref.rect.y - self.rect.y

        HORIZONTAL_LIMIT = 150
        VERTICAL_LIMIT = -20 

        if (y_diff < VERTICAL_LIMIT) and (abs(x_diff) <= HORIZONTAL_LIMIT) and (self.check_grounded()):
            if x_diff < 0: # player is left of ai
                self.direction_facing = LEFT
                move = self.get_move_left()
                self.rect.x -= min(move, abs(x_diff))
            else:
                self.direction_facing = RIGHT
                move = self.get_move_right()
                self.rect.x += min(move, abs(x_diff))

            self.jump()
            return
        
        # if our attack would land
        if opponent_dist <= range * 1.2:  # Slightly extended range
            # 50% chance to attack when in range
            if (random.randint(1,4) == 1):
                # 50% punch or kick
                if (random.randint(1,2) == 1):
                    if (not self.punched) and (not self.kicked):
                        self.punch_attack()
                else:
                    if (not self.punched) and (not self.kicked):
                        self.kick_attack()
        
        # we calculate health to determine how the ai should react to player attacks
        health_score = self.health / PLAYER_HEALTH
        fun = None
        
        if (health_score >= 0.75 and (random.randint(1, 3) == 1)):
            fun = self.approach_opponent
        elif (health_score >= 0.25 and (random.randint(1, 3) == 1)):
            if (random.randint(1, 10) <= 8):
                fun = self.approach_opponent
            else:
                fun = self.retreat
        elif (random.randint(1, 5) == 1):
            fun = self.retreat

        if (fun):
            repeat = Repeat(fun, 1)
            Callback(repeat.kill, 15)
    
    def approach_opponent(self):
        if (self.opponent_ref.rect.x < self.rect.x): # to the left
            self.rect.x -= self.speed
            self.direction_facing = LEFT
        else:
            self.rect.x += self.speed
            self.direction_facing = RIGHT
            
        if (self.current_animation != "PUNCHING" and self.current_animation != "KICKING" and self.current_animation != "RUNNING"):
            self.current_animation = "RUNNING"
            self.sprite_handler.update_sprite("RUNNING")
    
    def retreat(self):       
        if (self.opponent_ref.rect.x < self.rect.x): # to the left
            self.rect.x += self.speed
            self.direction_facing = RIGHT
        else:
            self.rect.x -= self.speed
            self.direction_facing = LEFT
            
        if (self.current_animation != "PUNCHING" and self.current_animation != "KICKING" and self.current_animation != "RUNNING"):
            self.current_animation = "RUNNING"
            self.sprite_handler.update_sprite("RUNNING")
    
    def damage(self, amount, stun_time, source_direction=None):
        super().damage(amount, stun_time, source_direction)

PUNCH_ATTACK_WIDTH = 40
PUNCH_ATTACK_HEIGHT = 20
PUNCH_ATTACK_OFFSET_X = -40
PUNCH_ATTACK_OFFSET_Y = 210

class HitNotif(pygame.sprite.Sprite):
    def __init__(self, damage, player, surface, special=False):
        super().__init__()
        self.damage = damage
        self.surface_ref = surface
        self.player_ref = player
        self.pos_x = player.rect.x
        self.pos_y = player.rect.y
        self.special = special

        self.repeat = Repeat(self.draw, 1)
        Callback(self.kill, 60)

    def move_random(self):
        if (self.player_ref.direction_facing == RIGHT):
            self.pos_x += random.randint(-1, 3)
        else:
            self.pos_x -= random.randint(-1, 3)
        self.pos_y -= random.randint(1, 2)

    def draw(self):
        self.move_random()
        text = None
        if (self.special): text = TITLE_FONT.render(f"{int(self.damage)}", True, GREEN)
        else: text = font.render(f"{int(self.damage)}", True, RED)
        self.surface_ref.blit(text, (self.pos_x, self.pos_y))

    def kill(self):
        if (self.repeat): self.repeat.kill()
        self.repeat = None
        super().kill()

class PunchAttack(pygame.sprite.Sprite):
    def __init__(self, player, opponent_hitbox, direction, surface, game, damage=50, stun_time=50):
        super().__init__()
        self.image = pygame.Surface((PUNCH_ATTACK_WIDTH, PUNCH_ATTACK_HEIGHT))
        self.image.fill(ORANGE)
        self.player_ref = player
        self.game_ref = game
        self.rect = self.image.get_rect()
        self.surface_ref = surface
        self.opponent_hitbox_ref = opponent_hitbox
        self.flag = True

        self.damage = damage
        self.stun_time = stun_time

        if (direction == RIGHT):
            self.rect.center = (self.player_ref.rect.x + PLAYER_SPRITE_WIDTH + PUNCH_ATTACK_OFFSET_X, self.player_ref.rect.y - PLAYER_SPRITE_HEIGHT + PUNCH_ATTACK_OFFSET_Y)
        else:
            self.rect.center = (self.player_ref.rect.x - PUNCH_ATTACK_OFFSET_X, self.player_ref.rect.y - PLAYER_SPRITE_HEIGHT + PUNCH_ATTACK_OFFSET_Y)
        
        Callback(self.delete, 30) # delete attack in 1/2 second
    
    def update(self):
        if (self.rect.colliderect(self.opponent_hitbox_ref.rect) and (self.flag)):
            self.flag = False
            self.opponent_hitbox_ref.player_ref.damage(self.damage, self.stun_time, self.player_ref.direction_facing)
            self.kill()

        if (DISPLAY_HITBOXES): self.surface_ref.blit(self.image, self.rect) # draw to screen

    def follow_player(self):
        if (self.player_ref.direction_facing == RIGHT):
            self.rect.center = (self.player_ref.rect.x + PLAYER_SPRITE_WIDTH + PUNCH_ATTACK_OFFSET_X, self.player_ref.rect.y - PLAYER_SPRITE_HEIGHT + PUNCH_ATTACK_OFFSET_Y)
        else:
            self.rect.center = (self.player_ref.rect.x - PUNCH_ATTACK_OFFSET_X, self.player_ref.rect.y - PLAYER_SPRITE_HEIGHT + PUNCH_ATTACK_OFFSET_Y)

    def delete(self):
        self.game_ref.attacks.remove(self)
        self.kill()

KICK_ATTACK_WIDTH = 40
KICK_ATTACK_HEIGHT = 20
KICK_ATTACK_OFFSET_X = -40
KICK_ATTACK_OFFSET_Y = 220

class KickAttack(pygame.sprite.Sprite):
    def __init__(self, player, opponent_hitbox, direction, surface, game, damage=50, stun_time=50):
        super().__init__()
        self.image = pygame.Surface((KICK_ATTACK_WIDTH, KICK_ATTACK_HEIGHT))
        self.image.fill(GREEN)
        self.player_ref = player
        self.game_ref = game
        self.rect = self.image.get_rect()
        self.surface_ref = surface
        self.opponent_hitbox_ref = opponent_hitbox
        self.flag = True

        self.damage = damage
        self.stun_time = stun_time

        if (direction == RIGHT):
            self.rect.center = (self.player_ref.rect.x + PLAYER_SPRITE_WIDTH + KICK_ATTACK_OFFSET_X, self.player_ref.rect.y - PLAYER_SPRITE_HEIGHT + KICK_ATTACK_OFFSET_Y)
        else:
            self.rect.center = (self.player_ref.rect.x - KICK_ATTACK_OFFSET_X, self.player_ref.rect.y - PLAYER_SPRITE_HEIGHT + KICK_ATTACK_OFFSET_Y)
        
        Callback(self.delete, 30) # delete attack in 1/2 second
    
    def update(self):
        if (self.rect.colliderect(self.opponent_hitbox_ref.rect) and (self.flag)):
            self.flag = False
            self.opponent_hitbox_ref.player_ref.damage(self.damage, self.stun_time, self.player_ref.direction_facing)
            self.kill()

        if (DISPLAY_HITBOXES): self.surface_ref.blit(self.image, self.rect) # draw to screen

    def follow_player(self):
        if (self.player_ref.direction_facing == RIGHT):
            self.rect.center = (self.player_ref.rect.x + PLAYER_SPRITE_WIDTH + KICK_ATTACK_OFFSET_X, self.player_ref.rect.y - PLAYER_SPRITE_HEIGHT + KICK_ATTACK_OFFSET_Y)
        else:
            self.rect.center = (self.player_ref.rect.x - KICK_ATTACK_OFFSET_X, self.player_ref.rect.y - PLAYER_SPRITE_HEIGHT + KICK_ATTACK_OFFSET_Y)

    def delete(self):
        self.game_ref.attacks.remove(self)
        self.kill()

#region CALLBACKS

class Callback():
    def __init__(self, function, time_in_frames):
        self.fun_ref = function
        self.time_in_frames = time_in_frames
        global callbacks
        callbacks.append(self)
    
    def process(self):
        self.time_in_frames -= 1
        if (self.time_in_frames <= 0): self.invoke()

    def invoke(self):
        self.fun_ref()
        global callbacks
        callbacks.remove(self)

    def kill(self):
        global callbacks
        if (self in callbacks): callbacks.remove(self)

class Repeat():
    def __init__(self, function, timedelay):
        self.function = function
        self.timedelay = timedelay
        self.timeref = timedelay
        global callbacks
        callbacks.append(self)
    
    def process(self):
        self.timedelay -= 1
        if (self.timedelay <= 0): self.invoke()

    def invoke(self):
        self.function()
        self.timedelay = self.timeref

    def kill(self):
        global callbacks
        if (self in callbacks): callbacks.remove(self)

class Timer():
    def __init__(self, callback_fun, time_in_seconds):
        self.callback_fun = callback_fun
        self.time_in_seconds = time_in_seconds
        self.repeat = None
        self.callback = None

    def tick(self):
        self.time_in_seconds -= 1

    def start_ticking(self):
        self.callback = Callback(self.end_action, FPS * self.time_in_seconds)
        self.repeat = Repeat(self.tick, FPS)

    def end_action(self):
        self.callback_fun() # perform action
        if (self.repeat): self.repeat.kill()
        self.time_in_seconds = 0

    def get_time(self):
        return self.time_in_seconds
    
    def kill(self):
        if (self.callback): self.callback.kill()
        if (self.repeat): self.repeat.kill()

TOAST_WIDTH = SCREEN_WIDTH / 2
TOAST_HEIGHT = 32 

class Toast(pygame.sprite.Sprite):
    def __init__(self, surface, text, display_time, on_kill_callback):
        super().__init__()
        self.image = pygame.Surface((TOAST_WIDTH, TOAST_HEIGHT))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH / 2, 30)
        self.text = text
        self.surface_ref = surface
        self.display_time = display_time
        self.on_kill_callback = on_kill_callback

        Callback(self.kill, display_time)

    def draw(self):
        self.surface_ref.blit(self.image, self.rect)
        text = font.render(self.text, True, WHITE)
        self.surface_ref.blit(text, (SCREEN_WIDTH / 2 - 250, 45 - fontsize))

    def kill(self):
        if (self.on_kill_callback): self.on_kill_callback()
        super().kill()

class Button(pygame.sprite.Sprite):
    def __init__(self, surface, on_click, static_sprite, offset, z_layer):
        super().__init__()
        self.image = pygame.image.load(static_sprite.spritesheet).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = offset
        self.surface_ref = surface
        self.on_click = on_click
        self.z = z_layer

        self.is_active = True

    def update(self):
        self.surface_ref.blit(self.image, self.rect)

    def scale(self, multiplier):
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * multiplier, self.image.get_height() * multiplier))

    def change_dimensions(self, new_dimensions):
        self.image = pygame.transform.scale(self.image, new_dimensions)

    def handle_click(self, event):
        if (not self.is_active): return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.on_click()

class Menu(object):
    def __init__(self):
        self.interactive_elements = []

    def add_button(self, button):
        self.interactive_elements.append(button)
    
    def redraw_frame(self):
        for obj in sorted(self.interactive_elements, key=(lambda x: x.z), reverse=False):
            obj.update()

TIMER_WIDTH = 64
TIMER_HEIGHT = 32
TIMER_X = SCREEN_WIDTH / 2
TIMER_Y = 60

class GameTimer(object):
    def __init__(self, surface, overtime, game):
        self.timer = None
        self.show = False
        self.surface_ref = surface
        self.image = pygame.Surface((TIMER_WIDTH, TIMER_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.center = (TIMER_X, TIMER_Y)
        self.image.fill(BLACK)
        self.overtime = overtime
        self.game_ref = game

    def show_timer(self):
        self.show = True

    def hide_timer(self):
        self.show = False

    def start_timer(self, time_in_seconds):
        self.timer = Timer(self.timer_end, time_in_seconds)
        self.timer.start_ticking()
        self.show_timer()

    def timer_end(self):
        try:
            if (not self.overtime):
                self.hide_timer()
                SWIPESPRITE.do_swipesprite_effect()
                for player in self.game_ref.players:
                    player.period_freeze(300) 
                Callback(lambda: self.start_timer(OVERTIME_LENGTH), 80)
                self.overtime = True
            else:
                SWIPESPRITE.change_sprite(GAME_OVER_SPRITE)
                SWIPESPRITE.do_swipesprite_effect()
                for player in self.game_ref.players:
                    player.period_freeze(300)
                Callback(game_end_sequence, 80)
        except:
            game_end_sequence()

    def update(self):
        if (self.show):
            if (self.timer.get_time() <= 60): self.image.fill(RED)
            text = font.render(f"{self.timer.get_time()}s", True, WHITE)
            self.surface_ref.blit(self.image, self.rect)
            self.surface_ref.blit(text, (TIMER_X - 16, TIMER_Y - 16))

    def kill(self):
        self.hide_timer()
        self.timer.kill()

#endregion

# HEALTHBAR MODIFIABLE ATTRIBUTES

FIRST_HEALTHBAR_OFFSET = (100, 30)
SECOND_HEALTHBAR_OFFSET = (SCREEN_WIDTH - FIRST_HEALTHBAR_OFFSET[0], FIRST_HEALTHBAR_OFFSET[1])
HEALTHBAR_WIDTH = 200
HEALTHBAR_HEIGHT = 20

class HealthBar(pygame.sprite.Sprite):
    def __init__(self, health, surface, offset):
        self.image = pygame.Surface((HEALTHBAR_WIDTH, HEALTHBAR_HEIGHT))
        self.backimage = pygame.Surface((HEALTHBAR_WIDTH, HEALTHBAR_HEIGHT))
        self.image.fill(RED)
        self.backimage.fill(GRAY)

        self.rect = self.image.get_rect()
        self.rect.center = (offset[0], offset[1] + fontsize * 2)
        
        # attributes
        self.maxhealth = health
        self.surface_ref = surface
        self.offset = offset

    def update(self, label, health):
        text = TITLE_FONT.render(label, True, RED)
        self.surface_ref.blit(text, self.offset)
        
        new_barwidth = int((health / self.maxhealth) * HEALTHBAR_WIDTH)
        if (new_barwidth < 0): new_barwidth = 0

        self.image = pygame.Surface((new_barwidth, HEALTHBAR_HEIGHT)) # finish
        self.image.fill(RED)

        self.surface_ref.blit(self.backimage, self.rect)
        self.surface_ref.blit(self.image, self.rect)

class Spritesheet(object):
    def __init__(self, path):
        try:
            self.sheet = pygame.image.load(path).convert_alpha()
        except:
            print(f"Could not locate spritesheet resource: {path} ")
            raise SystemExit
    
    def get_image_at(self, rect):
        crop = pygame.Rect(rect)
        image = pygame.Surface(crop.size, pygame.SRCALPHA).convert_alpha()
        image.blit(self.sheet, (0, 0), crop)
        return image
    
    def load_image_strip(self, rect, image_count):
        rects = []
        for x in range(image_count):
            rects.append((rect[0] + rect[2]*x, rect[1], rect[2], rect[3]))
        images = []
        for rect in rects:
            images.append(self.get_image_at(rect))
        return images

class SpriteHandler(object):
    def __init__(self, player, tickspeed, game):
        self.anims = {}
        self.current_anim = None
        self.current_anim_length = None
        self.current_frame = 0
        self.player_ref = player
        self.tickspeed = tickspeed
        self.game_ref = game
        self.repeat = None
    
    def clear_anims(self):
        self.anims.clear()

    def add_anim(self, name, frames):
        self.anims[name] = frames

    def change_anim(self, new_anim):
        if (self.anims.get(new_anim) == None): return False # if we have not defined this animation, break
        self.current_anim = self.anims[new_anim]
        self.current_frame = 0
        self.current_anim_length = len(self.current_anim)
        return True

    def get_next_frame(self):
        if (self.current_anim != None):
            frame = self.current_anim[self.current_frame % self.current_anim_length]
            self.current_frame += 1
            return frame

    def update_sprite(self, anim):
        if (not self.change_anim(anim)): return # if animation does not exist do nothing
        if (self.repeat): self.repeat.kill()
        self.increment_sprite()
        self.repeat = Repeat(self.increment_sprite, ANIMATION_LATENCY)
    
    def increment_sprite(self):
        new_frame = pygame.transform.scale(self.get_next_frame(), (PLAYER_SPRITE_WIDTH, PLAYER_SPRITE_HEIGHT))
        if (self.player_ref.direction_facing == LEFT): new_frame = pygame.transform.flip(new_frame, 1, 0)
        self.player_ref.image = new_frame

# GAME OBJECTS

class Platform(pygame.sprite.Sprite):
    def __init__(self, dimensions, location, surface):
        self.image = pygame.Surface(dimensions)
        self.image.fill(ORANGE)
        self.game_ref = None
        self.rect = self.image.get_rect()
        self.surface_ref = surface
        self.rect.center = location
    
    def attach_to_game(self):
        if (not self.game_ref): return # if undefined game do nothing
        self.game_ref.interactable_game_objects.add_internal(self)

    def update(self):
        if (DISPLAY_HITBOXES): self.surface_ref.blit(self.image, self.rect) # draw to screen

    def delete(self):
        if (self.game_ref): self.game_ref.interactable_game_objects.remove_internal(self)
        self.kill()

class StaticSprite(object):
    def __init__(self, name, spritesheet):
        self.name = name
        self.spritesheet = spritesheet

FOREGROUND_OBJECT = 1
BACKGROUND_OBJECT = 2

class SpritedGameObject(pygame.sprite.Sprite):
    def __init__(self, static_sprite, location, surface, z_layer, type):
        super().__init__()
        self.sprite = static_sprite
        self.z = z_layer
        self.type = type

        try:
            self.image = pygame.image.load(self.sprite.spritesheet).convert_alpha()
        except:
            print(f"Could not locate sprite resource: {self.sprite.spritesheet}")
            raise SystemExit

        self.rect = self.image.get_rect()
        self.surface_ref = surface
        self.rect.center = location
        self.game_ref = None
    
    def update(self):
        self.surface_ref.blit(self.image, self.rect) # draw to screen

    def attach_to_game(self):
        if (not self.game_ref): return # if undefined game do nothing
        self.game_ref.static_game_objects.add_internal(self)

    def scale(self, multiplier):
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * multiplier, self.image.get_height() * multiplier))

    def change_dimensions(self, new_dimensions):
        self.image = pygame.transform.scale(self.image, new_dimensions)

    def delete(self):
        self.game_ref.static_game_objects.remove_internal(self)
        self.kill()

class SpritedMenuObject(pygame.sprite.Sprite):
    def __init__(self, static_sprite, location, surface, z_layer, type, menu):
        super().__init__()
        self.sprite = static_sprite
        self.z = z_layer
        self.type = type

        try:
            self.image = pygame.image.load(self.sprite.spritesheet).convert_alpha()
        except:
            print(f"Could not locate sprite resource: {self.sprite.spritesheet}")
            raise SystemExit

        self.rect = self.image.get_rect()
        self.surface_ref = surface
        self.rect.center = location
        self.menu_ref = menu

        self.attach_to_menu()
    
    def update(self):
        self.surface_ref.blit(self.image, self.rect) # draw to screen

    def attach_to_menu(self):
        if (not self.menu_ref): return # if undefined game do nothing
        self.menu_ref.interactive_elements.append(self)

    def scale(self, multiplier):
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * multiplier, self.image.get_height() * multiplier))

    def change_dimensions(self, new_dimensions):
        self.image = pygame.transform.scale(self.image, new_dimensions)

    def delete(self):
        self.menu_ref.interactive_elements.remove(self)
        self.kill()

class MenuText(object):
    def __init__(self, text, offset, z_layer, surface, text_font, color):
        self.text = text
        self.offset = offset
        self.z = z_layer
        self.surface_ref = surface
        self.font = text_font
        self.color = color
        self.image = self.font.render(self.text, True, self.color)
        self.rect = self.image.get_rect(center=self.offset)

    def update(self):
        self.surface_ref.blit(self.image, self.rect)

# GAME

class Map(object):
    def __init__(self, name, interactable_game_objects, static_game_objects, ground_y):
        self.name = name
        self.game_ref = None 
        self.interactable_game_objects = interactable_game_objects
        self.static_game_objects = static_game_objects
        self.ground_y = ground_y

class Game(object):
    def __init__(self, tutorial):
        # FRAME UPDATE REFERENCES
        self.attacks = []
        self.interactable_game_objects = pygame.sprite.Group()
        self.static_game_objects = pygame.sprite.Group()
        self.map_ref = None
        self.tutorial = tutorial
        self.active_toast = None
        self.game_timer = None

        # PLAYERS
        self.players = []
        self.player_hitboxes = []
    
    def add_players(self, players, player_hitboxes):
        self.players.extend(players)
        self.player_hitboxes.extend(player_hitboxes)
        for player in self.players:
            player.reset_position()

    def add_timer(self, game_timer):
        self.game_timer = game_timer

    def load_map(self, map):
        self.map_ref = map
        map.game_ref = self

        for igo in map.interactable_game_objects:
            igo.game_ref = self
            igo.attach_to_game()
            
        for sgo in map.static_game_objects:
            sgo.game_ref = self
            sgo.attach_to_game()
        
    def redraw_frame(self):
        foreground = []
        background = []

        for obj in self.static_game_objects:
            if (obj.type == FOREGROUND_OBJECT):
                foreground.append(obj)
            else:
                background.append(obj)
        
        # draw in order of z layer

        for obj in sorted(background, key=(lambda x: x.z), reverse=False):
            obj.update()

        for hitbox in self.player_hitboxes:
            hitbox.update()
            if (DISPLAY_HITBOXES): hitbox.draw()

        for player in self.players:
            player.update()
            player.draw()

        for obj in self.interactable_game_objects:
            obj.update()
        
        for attack in self.attacks:
            attack.update()
        
        for obj in sorted(foreground, key=(lambda x: x.z), reverse=False):
            obj.update()

        if (self.tutorial): TUTORIAL.do_tutorial()

        if (self.active_toast):
            self.active_toast.draw()
        
        if (self.game_timer):
            self.game_timer.update()

class Tutorial(object):
    def __init__(self, surface, game):
        self.has_moved = False
        self.has_jumped = False
        self.has_punched = False
        self.has_kicked = False
        self.has_dodged = False

        self.surface_ref = surface
        self.game_ref = game
        self.is_toast_active = False

    def toast_finished(self):
        self.is_toast_active = False

    def do_tutorial(self):
        if (self.is_toast_active): return

        toast_text = None
        if (not self.has_moved):
            toast_text = "Use the keys ASD to move around!"
        elif (not self.has_jumped):
            toast_text = "Use the keys W to jump!"
        elif (not self.has_punched):
            toast_text = "Use the J key to punch!"
        elif (not self.has_kicked):
            toast_text = "Use the K key to kick!"
        elif (not self.has_dodged):
            toast_text = "Use the L key to dodge!"
        else:
            toast_text = "Congrats! You've completed the tutorial!"

        if toast_text:
            self.is_toast_active = True
            self.game_ref.active_toast = Toast(self.surface_ref, toast_text, 120, self.toast_finished)

SWIPE_SPEED = 120

class Screenswipe(pygame.sprite.Sprite):
    def __init__(self, static_sprite, surface):
        super().__init__()
        self.image = pygame.image.load(static_sprite.spritesheet).convert_alpha()
        self.image = pygame.transform.scale(self.image, (SCREEN_WIDTH * 2, SCREEN_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH / 2 + 1600, SCREEN_HEIGHT / 2)
        self.repeat = None
        self.surface_ref = surface

    def update(self):
        self.rect.move_ip(-SWIPE_SPEED, 0)

    def draw(self):
        self.surface_ref.blit(self.image, self.rect)

    def do_effect(self):
        global current_game
        Callback(self.reset, 30)
        self.repeat = Repeat(self.update, 1)

    def reset(self):
        if (self.repeat): self.repeat.kill()
        self.repeat = None
        self.rect.center = (SCREEN_WIDTH / 2 + 1600, SCREEN_HEIGHT / 2)

COUNTDOWN_MAX_SPEED = 60
COUNTDOWN_START_X = SCREEN_WIDTH + 100
COUNTDOWN_CENTRE_Y = SCREEN_HEIGHT / 2
COUNTDOWN_DECEL_FRAMES = 20
COUNTDOWN_PAUSE_FRAMES = 20
COUNTDOWN_ACCELERATION_FRAMES = 20

TRANSLUCENT_OVERLAY = "assets/overlay.png"
COUNTDOWN_IMAGES = ["assets/three.png", "assets/two.png", "assets/one.png"]

class SoundFile(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path

COUNTDOWN_VO = SoundFile("COUNTDOWN_VO", "audio/game_start.ogg")

class Countdown(pygame.sprite.Sprite):
    def __init__(self, surface):
        super().__init__()
        self.current_count = 0
        self.image2 = pygame.image.load(TRANSLUCENT_OVERLAY).convert_alpha()
        self.image2 = pygame.transform.scale(self.image2, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.image = pygame.image.load(COUNTDOWN_IMAGES[self.current_count]).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect2 = self.image2.get_rect()
        self.rect.center = (COUNTDOWN_START_X, COUNTDOWN_CENTRE_Y)
        self.rect2.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.repeat = None
        self.surface_ref = surface
        self.vo = None
        
        self.state = "IDLE"
        self.frame_count = 0
        self.current_speed = 0

        self.overlay_active = False

    def update(self):
        if self.state == "DECELERATE":
            progress = self.frame_count / COUNTDOWN_DECEL_FRAMES
            self.current_speed = COUNTDOWN_MAX_SPEED * (1 - progress)

            self.rect.move_ip(-self.current_speed, 0)
            self.frame_count += 1

            if self.frame_count >= COUNTDOWN_DECEL_FRAMES:
                self.state = "PAUSE"
                self.frame_count = 0

        elif self.state == "ACCELERATE":
            progress = self.frame_count / COUNTDOWN_ACCELERATION_FRAMES
            self.current_speed = COUNTDOWN_MAX_SPEED * progress # inversely proportional

            self.rect.move_ip(-self.current_speed, 0)
            self.frame_count += 1

            if self.frame_count >= COUNTDOWN_ACCELERATION_FRAMES:
                self.state = "IDLE"
                self.frame_count = 0

        elif self.state == "IDLE":
            pass

    def draw(self):
        if (self.overlay_active): self.surface_ref.blit(self.image2, self.rect2)
        self.surface_ref.blit(self.image, self.rect)

    def do_countdown(self):
        self.vo = SoundEffect(COUNTDOWN_VO)
        global in_cutscene
        in_cutscene = True
        self.vo.play()
        self.do_effect()
        Callback(self.do_effect, 61)
        Callback(self.do_effect, 122)
        Callback(self.disable_countdown, 200)

    def disable_countdown(self):
        global in_cutscene
        in_cutscene = False

    def start_accelerate(self):
        self.state = "ACCELERATE"
        self.frame_count = 0

    def do_effect(self):
        if self.current_count < len(COUNTDOWN_IMAGES):
            self.image = pygame.image.load(COUNTDOWN_IMAGES[self.current_count]).convert_alpha()
        
        self.rect.center = (COUNTDOWN_START_X, COUNTDOWN_CENTRE_Y)
        self.frame_count = 0
        self.state = "DECELERATE"
        
        if (self.repeat): self.repeat.kill()
        self.repeat = Repeat(self.update, 1)

        Callback(self.start_accelerate, COUNTDOWN_DECEL_FRAMES + COUNTDOWN_PAUSE_FRAMES)
        Callback(self.reset, 60) 

    def reset(self):
        if (self.repeat): self.repeat.kill()
        self.repeat = None
        self.rect.center = (COUNTDOWN_START_X, COUNTDOWN_CENTRE_Y)
        self.state = "IDLE"
        self.current_count += 1

OVERTIME_MAX_SPEED = 60
OVERTIME_START_X = SCREEN_WIDTH + 130
OVERTIME_CENTRE_Y = SCREEN_HEIGHT / 2
OVERTIME_DECEL_FRAMES = 20
OVERTIME_PAUSE_FRAMES = 40
OVERTIME_ACCELERATION_FRAMES = 20

OVERTIME_SPRITE = "assets/overtime.png"
GAME_OVER_SPRITE = "assets/game_over.png"

class SwipeSprite(pygame.sprite.Sprite):
    def __init__(self, surface, sprite_path):
        super().__init__()
        self.current_count = 0
        self.image2 = pygame.image.load(TRANSLUCENT_OVERLAY).convert_alpha()
        self.image2 = pygame.transform.scale(self.image2, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.image = pygame.image.load(sprite_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect2 = self.image2.get_rect()
        self.rect.center = (OVERTIME_START_X, OVERTIME_CENTRE_Y)
        self.rect2.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.repeat = None
        self.surface_ref = surface
        
        self.state = "IDLE"
        self.frame_count = 0
        self.current_speed = 0

        self.overlay_active = False

    def change_sprite(self, new_sprite_path):
        self.image = pygame.image.load(new_sprite_path).convert_alpha()

    def update(self):
        if self.state == "DECELERATE":
            progress = self.frame_count / OVERTIME_DECEL_FRAMES
            self.current_speed = OVERTIME_MAX_SPEED * (1 - progress)

            self.rect.move_ip(-self.current_speed, 0)
            self.frame_count += 1

            if self.frame_count >= OVERTIME_DECEL_FRAMES:
                self.state = "PAUSE"
                self.frame_count = 0

        elif self.state == "ACCELERATE":
            progress = self.frame_count / OVERTIME_ACCELERATION_FRAMES
            self.current_speed = OVERTIME_MAX_SPEED * progress # inversely proportional

            self.rect.move_ip(-self.current_speed, 0)
            self.frame_count += 1

            if self.frame_count >= OVERTIME_ACCELERATION_FRAMES:
                self.state = "IDLE"
                self.frame_count = 0

        elif self.state == "IDLE":
            pass

    def draw(self):
        if (self.overlay_active): self.surface_ref.blit(self.image2, self.rect2)
        self.surface_ref.blit(self.image, self.rect)

    def do_swipesprite_effect(self):
        self.overlay_active = True
        self.do_effect()
        global in_cutscene
        in_cutscene = True
        Callback(self.disable_overlay, 80)
        Callback(self.swipesprite_end, 85)

    def swipesprite_end(self):
        global in_cutscene
        in_cutscene = False

    def start_accelerate(self):
        self.state = "ACCELERATE"
        self.frame_count = 0

    def do_effect(self):
        self.rect.center = (OVERTIME_START_X, OVERTIME_CENTRE_Y)
        self.frame_count = 0
        self.state = "DECELERATE"
        
        if (self.repeat): self.repeat.kill()
        self.repeat = Repeat(self.update, 1)

        Callback(self.start_accelerate, OVERTIME_DECEL_FRAMES + OVERTIME_PAUSE_FRAMES)
        Callback(self.reset, 80) 

    def reset(self):
        if (self.repeat): self.repeat.kill()
        self.repeat = None
        self.rect.center = (OVERTIME_START_X, OVERTIME_CENTRE_Y)
        self.state = "IDLE"
        self.current_count += 1

    def disable_overlay(self):
        self.overlay_active = False

SCREENSWIPE = Screenswipe(StaticSprite("SCREENSWIPE", "assets/screen_swipe.png"), screen)
COUNTDOWN = Countdown(screen)
SWIPESPRITE = SwipeSprite(screen, OVERTIME_SPRITE)

class BackgroundMusic(object):
    def __init__(self, music_file):
        global bgm_loaded
        self.music_file = music_file
        self.running = False
        try:
            if (bgm_loaded): 
                return
            pygame.mixer.music.load(music_file.path)
            bgm_loaded = True
        except:
            print(f"Could not locate audio resource: {music_file.path}")

    def load_and_play(self):
        if (self.running): return
        try:
            pygame.mixer.music.load(self.music_file.path)
        except:
            print(f"Could not locate audio resource: {self.music_file.path}")
        self.play()

    def play(self):
        pygame.mixer.music.play(-1) # play infinitely
        self.running = True

    def set_volume(self, vol):
        pygame.mixer.music.set_volume(vol)
    
    def pause(self):
        if (self.running): pygame.mixer.music.pause()
        self.running = False

    def unpause(self):
        if (not self.running): pygame.mixer.music.unpause()
        self.running = True

    def stop(self):
        if (self.running): pygame.mixer.music.stop()
        self.running = False

    def kill(self):
        pygame.mixer.music.unload()
        self.running = False
        global bgm_loaded
        bgm_loaded = False

class SoundEffect(object):
    def __init__(self, sound_file):
        self.sound = None
        try:
            self.sound = pygame.mixer.Sound(sound_file.path)
        except:
            print(f"Could not locate audio resource: {sound_file.path}")
        self.set_volume(sfx_volume)

    def play(self):
        if (self.sound): self.sound.play()
    
    def set_volume(self, vol):
        if (self.sound):
            self.sound.set_volume(vol)

    def stop(self):
        if (self.sound): self.sound.stop()

    def kill(self):
        if (self.sound): self.sound.stop()
        self.sound = None

#region SFX

HURT = SoundEffect(SoundFile("HURT", "audio/hurt.ogg"))
WHOOSH = SoundEffect(SoundFile("WHOOSH", "audio/whoosh.mp3"))

#endregion

#region GLOBAL FUNCTIONS

GAME_LENGTH = 120
OVERTIME_LENGTH = 60

# SETTINGS SLIDERS

MUSIC_SLIDER = Slider(screen, 400, 205, 200, 10, min=0, max=10, step=1, initial=5)
SOUND_SLIDER = Slider(screen, 400, 275, 200, 10, min=0, max=10, step=1, initial=5)
TEXT_SLIDER = Slider(screen, 530, 415, 200, 10, min=0, max=10, step=1, initial=5)
HICONTRAST_BUTTON = Toggle(screen, 410, 345, 20, 10)

SETTINGS_WIDGETS = [MUSIC_SLIDER, SOUND_SLIDER, TEXT_SLIDER, HICONTRAST_BUTTON]
for w in SETTINGS_WIDGETS: w.hide()

def change_bgm(new_bgm):
    global current_bgm
    if (current_bgm and current_bgm.running == False): current_bgm.unpause()
    if (current_bgm): current_bgm.kill()
    current_bgm = new_bgm
    current_bgm.load_and_play()

def change_to_main_menu():
    global current_menu 
    current_menu = MAIN_MENU
    global current_game 
    current_game = None
    if (not current_bgm) or (current_bgm != MAIN_MENU_AUDIO):
        change_bgm(MAIN_MENU_AUDIO)

    Repeat(random_move_mainclouds, 30)
    
    for w in SETTINGS_WIDGETS: w.hide()

def load_char_menu():
    SCREENSWIPE.do_effect()
    Callback(change_to_char_menu, 15)

def change_to_char_menu():
    global current_menu 
    current_menu = CHARACTER_MENU
    global current_game 
    current_game = None
    # change_bgm(MAIN_MENU_AUDIO)

def load_settings_menu():
    SCREENSWIPE.do_effect()
    Callback(change_to_settings_menu, 15)

def change_to_settings_menu():
    global current_menu 
    current_menu = SETTINGS_MENU
    global current_game 
    current_game = None
    # change_bgm(MAIN_MENU_AUDIO)
    Callback(show_settings_widgets, 10)

def show_settings_widgets():
    for w in SETTINGS_WIDGETS: w.show()

def load_map_select_menu_withai():
    load_map_select_menu(True)

def load_map_select_menu(ai=False):
    global ai_game
    ai_game = ai
    SCREENSWIPE.do_effect()
    Callback(change_to_map_menu, 15)

def change_to_map_menu():
    global current_menu 
    current_menu = MAP_SELECT_MENU
    global current_game 
    current_game = None

    WILLS_PLAYER1.reset_sprite(p1_character)
    MVB_PLAYER1.reset_sprite(p1_character)
    CLIFTON_PLAYER1.reset_sprite(p1_character)
    
    WILLS_PLAYER2.reset_sprite(p2_character)
    MVB_PLAYER2.reset_sprite(p2_character)
    CLIFTON_PLAYER2.reset_sprite(p2_character)

    WILLS_AIPLAYER2.reset_sprite(p2_character)
    MVB_AIPLAYER2.reset_sprite(p2_character)
    CLIFTON_AIPLAYER2.reset_sprite(p2_character)

def load_game_over_menu():
    SCREENSWIPE.do_effect()
    Callback(change_to_gameover_menu, 15)

def change_to_gameover_menu():
    global current_menu 
    current_menu = GAME_OVER_MENU
    global current_game 
    current_game = None
    # change_bgm(MAIN_MENU_AUDIO)

def load_tutorial():
    SCREENSWIPE.do_effect()
    Callback(change_game_to_tutorial, 15)

    global ground_y
    ground_y = TUTORIAL_GROUND_Y

    TUTORIAL_PLAYER.reset_position()
    TUTORIAL_PLAYER.dead = False
    TUTORIAL_PLAYER.go_idle()

def change_game_to_tutorial():
    global current_menu 
    current_menu = None
    global current_game 
    current_game = TUTORIAL_GAME
    change_bgm(TUTORIAL_AUDIO)

def random_move_hotairballoon():
    mult = 1
    if (HOT_AIR_BALLOON.rect.x > SCREEN_WIDTH - 100): mult = -1
    if (HOT_AIR_BALLOON.rect.x < 100): mult = 1
    HOT_AIR_BALLOON.rect.move_ip(random.randint(1, 2) * mult, random.randint(-1, 1))

def load_wills():
    SCREENSWIPE.do_effect()
    Callback(change_game_to_wills, 15)
    Callback(countdown_sequence, 60)
    Callback(disable_countdown_overlay, 243) 

    Repeat(random_move_hotairballoon, 30)

    global ground_y
    ground_y = WILLS_GROUND_Y

    WILLS_GAME.players = []
    WILLS_GAME.player_hitboxes = []

    WILLS_PLAYER1.reset()
    WILLS_PLAYER2.reset()
    WILLS_AIPLAYER2.reset()
    
    if (ai_game): 
        WILLS_AIPLAYER2.reset_sprite(p2_character)

        WILLS_PLAYER1.attach_opponent(WILLS_AIPLAYER2, HITBOX_WILLS_AIPLAYER2)
        WILLS_AIPLAYER2.attach_opponent(WILLS_PLAYER1, HITBOX_WILLS_PLAYER1)

        WILLS_GAME.add_players([WILLS_AIPLAYER2], [HITBOX_WILLS_AIPLAYER2])
        WILLS_AIPLAYER2.jump()
    else:
        WILLS_PLAYER2.reset_sprite(p2_character)

        WILLS_PLAYER1.attach_opponent(WILLS_PLAYER2, HITBOX_WILLS_PLAYER2)
        WILLS_PLAYER2.attach_opponent(WILLS_PLAYER1, HITBOX_WILLS_PLAYER1)

        WILLS_GAME.add_players([WILLS_PLAYER2], [HITBOX_WILLS_PLAYER2])
        WILLS_PLAYER2.jump()

    WILLS_GAME.add_players([WILLS_PLAYER1], [HITBOX_WILLS_PLAYER1])
    WILLS_PLAYER1.reset_sprite(p1_character)
    WILLS_PLAYER1.jump()

def load_mvb():
    SCREENSWIPE.do_effect()
    Callback(change_game_to_mvb, 15)
    Callback(countdown_sequence, 60)
    Callback(disable_countdown_overlay, 243)

    global ground_y
    ground_y = MVB_GROUND_Y

    MVB_GAME.players = []
    MVB_GAME.player_hitboxes = []

    MVB_PLAYER1.reset()
    MVB_PLAYER2.reset()
    MVB_AIPLAYER2.reset()

    if (ai_game): 
        # print("ai")
        MVB_AIPLAYER2.reset_sprite(p2_character)

        MVB_PLAYER1.attach_opponent(MVB_AIPLAYER2, HITBOX_MVB_AIPLAYER2)
        MVB_AIPLAYER2.attach_opponent(MVB_PLAYER1, HITBOX_MVB_PLAYER1)

        MVB_GAME.add_players([MVB_AIPLAYER2], [HITBOX_MVB_AIPLAYER2])
    else:
        MVB_PLAYER2.reset_sprite(p2_character)

        MVB_PLAYER1.attach_opponent(MVB_PLAYER2, HITBOX_MVB_PLAYER2)
        MVB_PLAYER2.attach_opponent(MVB_PLAYER1, HITBOX_MVB_PLAYER1)

        MVB_GAME.add_players([MVB_PLAYER2], [HITBOX_MVB_PLAYER2])

    MVB_GAME.add_players([MVB_PLAYER1], [HITBOX_MVB_PLAYER1])
    MVB_PLAYER1.reset_sprite(p1_character)

def load_clifton():
    SCREENSWIPE.do_effect()
    Callback(change_game_to_clifton, 15)
    Callback(countdown_sequence, 60)
    Callback(disable_countdown_overlay, 243)

    Repeat(random_move_cliftonclouds, 30)

    global ground_y
    ground_y = CLIFTON_GROUND_Y

    CLIFTON_GAME.players = []
    CLIFTON_GAME.player_hitboxes = []

    CLIFTON_PLAYER1.reset()
    CLIFTON_PLAYER2.reset()
    CLIFTON_AIPLAYER2.reset()

    if (ai_game): 
        # print("ai")
        CLIFTON_AIPLAYER2.reset_sprite(p2_character)

        CLIFTON_PLAYER1.attach_opponent(CLIFTON_AIPLAYER2, HITBOX_CLIFTON_AIPLAYER2)
        CLIFTON_AIPLAYER2.attach_opponent(CLIFTON_PLAYER1, HITBOX_CLIFTON_PLAYER1)

        CLIFTON_GAME.add_players([CLIFTON_AIPLAYER2], [HITBOX_CLIFTON_AIPLAYER2])
    else:
        CLIFTON_PLAYER2.reset_sprite(p2_character)
        
        CLIFTON_PLAYER1.attach_opponent(CLIFTON_PLAYER2, HITBOX_CLIFTON_PLAYER2)
        CLIFTON_PLAYER2.attach_opponent(CLIFTON_PLAYER1, HITBOX_CLIFTON_PLAYER1)

        CLIFTON_GAME.add_players([CLIFTON_PLAYER2], [HITBOX_CLIFTON_PLAYER2])

    CLIFTON_GAME.add_players([CLIFTON_PLAYER1], [HITBOX_CLIFTON_PLAYER1])
    CLIFTON_PLAYER1.reset_sprite(p1_character)

def countdown_sequence():
    COUNTDOWN.current_count = 0
    COUNTDOWN.do_countdown()

def disable_countdown_overlay():
    COUNTDOWN.overlay_active = False

GAME_START_DELAY = 260

def change_game_to_mvb():
    global current_menu 
    current_menu = None
    global current_game 
    current_game = MVB_GAME
    COUNTDOWN.overlay_active = True
    if (current_bgm): current_bgm.kill()

    for player in current_game.players:
        player.period_freeze(GAME_START_DELAY)

    current_game.add_timer(GameTimer(screen, False, current_game))
    Callback(start_mvb, GAME_START_DELAY)

def start_mvb():
    change_bgm(MVB_GAME_AUDIO)
    current_game.game_timer.start_timer(GAME_LENGTH)

def change_game_to_wills():
    global current_menu 
    current_menu = None
    global current_game 
    current_game = WILLS_GAME
    COUNTDOWN.overlay_active = True
    if (current_bgm): current_bgm.kill()

    for player in current_game.players:
        player.period_freeze(GAME_START_DELAY)

    current_game.add_timer(GameTimer(screen, False, current_game))
    Callback(start_wills, GAME_START_DELAY)

def start_wills():
    change_bgm(WILLS_GAME_AUDIO)
    current_game.game_timer.start_timer(GAME_LENGTH)

def change_game_to_clifton():
    global current_menu 
    current_menu = None
    global current_game 
    current_game = CLIFTON_GAME
    COUNTDOWN.overlay_active = True
    if (current_bgm): current_bgm.kill()

    for player in current_game.players:
        player.period_freeze(GAME_START_DELAY)

    current_game.add_timer(GameTimer(screen, False, current_game))
    Callback(start_clifton, GAME_START_DELAY)

def start_clifton():
    change_bgm(CLIFTON_GAME_AUDIO)
    current_game.game_timer.start_timer(GAME_LENGTH)

def game_end_sequence():
    if (PLAYER1_WON in GAME_OVER_MENU.interactive_elements): GAME_OVER_MENU.interactive_elements.remove(PLAYER1_WON)
    if (PLAYER2_WON in GAME_OVER_MENU.interactive_elements): GAME_OVER_MENU.interactive_elements.remove(PLAYER2_WON)

    if (current_game == MVB_GAME):
        if (ai_game): comphealth = MVB_AIPLAYER2.health
        else: comphealth = MVB_PLAYER2.health 

        if (MVB_PLAYER1.health > comphealth):
            GAME_OVER_MENU.interactive_elements.append(PLAYER1_WON)
        else:
            GAME_OVER_MENU.interactive_elements.append(PLAYER2_WON)
    elif (current_game == WILLS_GAME):
        if (ai_game): comphealth = WILLS_AIPLAYER2.health
        else: comphealth = WILLS_PLAYER2.health 

        if (WILLS_PLAYER1.health > WILLS_PLAYER2.health):
            GAME_OVER_MENU.interactive_elements.append(PLAYER1_WON)
        else:
            GAME_OVER_MENU.interactive_elements.append(PLAYER2_WON)
    elif (current_game == CLIFTON_GAME):
        if (ai_game): comphealth = CLIFTON_AIPLAYER2.health
        else: comphealth = CLIFTON_PLAYER2.health 

        if (CLIFTON_PLAYER1.health > CLIFTON_PLAYER2.health):
            GAME_OVER_MENU.interactive_elements.append(PLAYER1_WON)
        else:
            GAME_OVER_MENU.interactive_elements.append(PLAYER2_WON)

    load_game_over_menu()

def random_move_cliftonclouds():
    mult = 1
    if (CLIFTON_CLOUDS.rect.x > 20): mult = -1
    if (CLIFTON_CLOUDS.rect.x < -20): mult = 1
    CLIFTON_CLOUDS.rect.move_ip(random.randint(-2, 2) * mult, random.randint(-1, 1))

def random_move_mainclouds():
    mult = 1
    if (MAIN_MENU_CLOUDS.rect.x > 20): mult = -1
    if (MAIN_MENU_CLOUDS.rect.x < -20): mult = 1
    MAIN_MENU_CLOUDS.rect.move_ip(random.randint(-2, 2) * mult, random.randint(-1, 1))

#endregion

#region MAIN MENU
MAIN_MENU = Menu()
MAIN_MENU_AUDIO = BackgroundMusic(SoundFile("MAIN_MENU_BGM", "audio/main_menu_loop.ogg"))

MAIN_MENU_BACKGROUND = SpritedMenuObject(StaticSprite("MAIN_MENU_BACKGROUND", "assets/main_menu_background.png"), (320, 180), screen, -100, BACKGROUND_OBJECT, MAIN_MENU)
MAIN_MENU_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

SENATE_HOUSE = SpritedMenuObject(StaticSprite("SENATE_HOUSE", "assets/senate_house.png"), (320, 180), screen, -90, BACKGROUND_OBJECT, MAIN_MENU)
SENATE_HOUSE.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

MAIN_MENU_LOGO = SpritedMenuObject(StaticSprite("LOGO", "assets/logo.png"), (100, 175), screen, -70, BACKGROUND_OBJECT, MAIN_MENU)
MAIN_MENU_LOGO.scale(3)

MAIN_MENU_CLOUDS = SpritedMenuObject(StaticSprite("MAIN_MENU_CLOUDS", "assets/clifton_clouds.png"), (320, 180), screen, -95, BACKGROUND_OBJECT, MAIN_MENU)
MAIN_MENU_CLOUDS.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

MAIN_MENU_TUTORIAL_BUTTON = Button(screen, load_tutorial, StaticSprite("TUTORIAL_BUTTON", "assets/tutorial_button.png"), (SCREEN_WIDTH - 150, 180), 10)
MAIN_MENU_SINGLEPLAYER_BUTTON = Button(screen, load_map_select_menu_withai, StaticSprite("SINGLEPLAYER_BUTTON", "assets/singleplayer_button.png"), (SCREEN_WIDTH - 150, 250), 10)
MAIN_MENU_MULTIPLAYER_BUTTON = Button(screen, load_map_select_menu, StaticSprite("MULTIPLAYER_BUTTON", "assets/multiplayer_button.png"), (SCREEN_WIDTH - 150, 320), 10)
MAIN_MENU_CHARACTER_BUTTON = Button(screen, load_char_menu, StaticSprite("CHARACTER_BUTTON", "assets/character_menu_button.png"), (SCREEN_WIDTH - 150, 390), 10)
MAIN_MENU_SETTINGS_BUTTON = Button(screen, load_settings_menu, StaticSprite("SETTINGS_BUTTON", "assets/settings_button.png"), (SCREEN_WIDTH - 150, 460), 10)

MAIN_MENU.add_button(MAIN_MENU_TUTORIAL_BUTTON)
MAIN_MENU.add_button(MAIN_MENU_SINGLEPLAYER_BUTTON)
MAIN_MENU.add_button(MAIN_MENU_MULTIPLAYER_BUTTON)
MAIN_MENU.add_button(MAIN_MENU_CHARACTER_BUTTON)
MAIN_MENU.add_button(MAIN_MENU_SETTINGS_BUTTON)
#endregion

#region CHARACTER MENU
CHARACTER_MENU = Menu()

CHAR_MENU_BACKGROUND = SpritedMenuObject(StaticSprite("CHARACTER_MENU_BACKGROUND", "assets/settings_background.png"), (320, 180), screen, -100, BACKGROUND_OBJECT, CHARACTER_MENU)
CHAR_MENU_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

CHAR_MENU_TITLE = MenuText("CHARACTER MENU", (SCREEN_WIDTH / 2, 50), 10, screen, TITLE_FONT, BLACK)
CHARACTER_MENU.interactive_elements.append(CHAR_MENU_TITLE)

# Define button layout from prototype
BUTTON_COORDINATES = [
    (143, 138), (729, 138),
    (143, 386), (729, 386)
]

BUTTON_SIZE = (128, 128)

CHAR_NAMES = ["'KHABIB' MUSK", "TIM 'BRUCE' LEE", "BILL 'ALI' GATES", "MARK 'MAYWEATHER' Z."]
CHAR_SELECTION = [MUSK_CHARACTER, TIM_CHARACTER, BILL_CHARACTER, MARK_CHARACTER]

def f_musk():
    global p1_character
    p1_character = MUSK_CHARACTER
    global p2_character
    p2_character = CHAR_SELECTION[random.randint(0, 3)]
    toast = Toast(screen, f"Player 1 selected: 'Khabib' Musk", 120, None)
    repeat = Repeat(toast.draw, 1)
    Callback(repeat.kill, 120)

def f_tim():
    global p1_character
    p1_character = TIM_CHARACTER
    global p2_character
    p2_character = CHAR_SELECTION[random.randint(0, 3)]
    toast = Toast(screen, f"Player 1 selected: Tim 'Bruce' Lee", 120, None)
    repeat = Repeat(toast.draw, 1)
    Callback(repeat.kill, 120)

def f_bill():
    global p1_character
    p1_character = BILL_CHARACTER
    global p2_character
    p2_character = CHAR_SELECTION[random.randint(0, 3)]
    toast = Toast(screen, f"Player 1 selected: Bill 'Ali' Gates", 120, None)
    repeat = Repeat(toast.draw, 1)
    Callback(repeat.kill, 120)

def f_mark():
    global p1_character
    p1_character = MARK_CHARACTER
    global p2_character
    p2_character = CHAR_SELECTION[random.randint(0, 3)]
    toast = Toast(screen, f"Player 1 selected: Mark 'Mayweather' Z.", 120, None)
    repeat = Repeat(toast.draw, 1)
    Callback(repeat.kill, 120)

CHAR_FUNCS = [f_musk, f_tim, f_bill, f_mark]

ASSETS = [StaticSprite("MUSK_PROFILE", "assets/musk_profile.png"), StaticSprite("TIM_PROFILE", "assets/tim_profile.png"), StaticSprite("BILL_PROFILE", "assets/bill_profile.png"), StaticSprite("MUSK_PROFILE", "assets/mark_profile.png")]

for i in range(4):
    name = CHAR_NAMES[i]
    tl = BUTTON_COORDINATES[i]
    
    center_x = tl[0] + BUTTON_SIZE[0] / 2
    center_y = tl[1] + BUTTON_SIZE[1] / 2

    char_button = Button(screen, CHAR_FUNCS[i], ASSETS[i], (center_x, center_y), 10)
    char_button.change_dimensions(BUTTON_SIZE)
    CHARACTER_MENU.add_button(char_button)
    
    name_center_x = center_x
    name_center_y = tl[1] - 15
    name_text = MenuText(name, (name_center_x, name_center_y), 10, screen, SUBTITLE_FONT, BLACK)
    CHARACTER_MENU.interactive_elements.append(name_text)

BACK_BUTTON = Button(screen, change_to_main_menu, StaticSprite("BACK_BUTTON", "assets/back_arrow.png"), (50, 50), 10)
CHARACTER_MENU.add_button(BACK_BUTTON)

#endregion

#region SETTINGS MENU
SETTINGS_MENU = Menu()

SETTINGS_MENU_BACKGROUND = SpritedMenuObject(StaticSprite("SETTINGS_MENU_BACKGROUND", "assets/settings_background.png"), (320, 180), screen, -100, BACKGROUND_OBJECT, SETTINGS_MENU)
SETTINGS_MENU_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

SETTINGS_HEADER = MenuText("SETTINGS", (SCREEN_WIDTH / 2, 100), 10, screen, TITLE_FONT, BLACK)
SETTINGS_MENU.interactive_elements.append(SETTINGS_HEADER)

MUSIC_HEADER = MenuText("MUSIC:", (250, 210), 10, screen, SUBTITLE_FONT, BLACK)
SETTINGS_MENU.interactive_elements.append(MUSIC_HEADER)

SOUND_HEADER = MenuText("SOUND:", (250, 280), 10, screen, SUBTITLE_FONT, BLACK)
SETTINGS_MENU.interactive_elements.append(SOUND_HEADER)

HICONTRAST_HEADER = MenuText("HIGH CONTRAST:", (250, 350), 10, screen, SUBTITLE_FONT, BLACK)
SETTINGS_MENU.interactive_elements.append(HICONTRAST_HEADER)

TEXT_HEADER = MenuText("TEXT SIZE:", (250, 420), 10, screen, SUBTITLE_FONT, BLACK)
TEXT_SAMPLE_1 = MenuText("SMALL", (490, 420), 10, screen, SMALLER_FONT, BLACK)
TEXT_SAMPLE_2 = MenuText("LARGE", (800, 420), 10, screen, TITLE_FONT, BLACK)
SETTINGS_MENU.interactive_elements.append(TEXT_HEADER)
SETTINGS_MENU.interactive_elements.append(TEXT_SAMPLE_1)
SETTINGS_MENU.interactive_elements.append(TEXT_SAMPLE_2)

BACK_BUTTON = Button(screen, change_to_main_menu, StaticSprite("BACK_BUTTON", "assets/back_arrow.png"), (50, 50), 10)
SETTINGS_MENU.add_button(BACK_BUTTON)

#endregion

#region MAP MENU
MAP_SELECT_MENU = Menu()

MAP_SELECT_BUTTONS = [
    Button(screen, load_mvb, StaticSprite("MVB_BUTTON", "assets/mvb_map_button.png"), (190, 338), 10),
    Button(screen, load_wills, StaticSprite("WILLS_BUTTON", "assets/wills_map_button.png"), (515, 338), 10),
    Button(screen, load_clifton, StaticSprite("CLIFTON_BUTTON", "assets/clifton_map_button.png"), (840, 338), 10)
]

MAP_MENU_BACKGROUND = SpritedMenuObject(StaticSprite("MAP_MENU_BACKGROUND", "assets/settings_background.png"), (320, 180), screen, -100, BACKGROUND_OBJECT, MAP_SELECT_MENU)
MAP_MENU_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

MAP_MENU_TITLE = MenuText("MAPS", (SCREEN_WIDTH / 2, 50), 10, screen, TITLE_FONT, BLACK)
MAP_SELECT_MENU.interactive_elements.append(MAP_MENU_TITLE)

for button in MAP_SELECT_BUTTONS:
    MAP_SELECT_MENU.add_button(button)

MAP_SELECT_MENU.add_button(BACK_BUTTON)

#endregion

#region GAME OVER MENU
GAME_OVER_MENU = Menu()

GAME_OVER_BACKGROUND = SpritedMenuObject(StaticSprite("GAME_OVER_MENU_BACKGROUND", "assets/settings_background.png"), (320, 180), screen, -100, BACKGROUND_OBJECT, GAME_OVER_MENU)
GAME_OVER_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

GAME_OVER_HEADER = MenuText("GAME OVER", (SCREEN_WIDTH / 2, 100), 10, screen, TITLE_FONT, RED)
GAME_OVER_MENU.interactive_elements.append(GAME_OVER_HEADER)

PLAYER1_WON = MenuText("PLAYER 1 WON!", (SCREEN_WIDTH / 2, 200), 10, screen, TITLE_FONT, BLACK)

PLAYER2_WON = MenuText("PLAYER 2 WON!", (SCREEN_WIDTH / 2, 200), 10, screen, TITLE_FONT, BLACK)

GAME_OVER_MENU.add_button(BACK_BUTTON)

#endregion

#region PAUSE MENU

def pause_game():
    global current_menu, paused_game, current_bgm
    
    if not current_game: return
    paused_game = current_game

    for player in paused_game.players:
        player.freeze()

    if current_bgm:
        current_bgm.pause()

    current_menu = PAUSE_MENU

def resume_game():
    global current_menu, paused_game, current_bgm

    if not paused_game:
        current_menu = None
        return

    for p in paused_game.players:
        p.unfreeze()

    if current_bgm:
        current_bgm.unpause()

    current_menu = None
    paused_game = None

def quit_to_main_from_pause():
    global paused_game

    if paused_game:
        for player in paused_game.players:
            player.unfreeze()

    paused_game = None
    change_to_main_menu()

PAUSE_MENU = Menu()
PAUSE_MENU_BACKGROUND = SpritedMenuObject(StaticSprite("PAUSE_MENU_BACKGROUND", "assets/overlay.png"), (320, 180), screen, -100, BACKGROUND_OBJECT, PAUSE_MENU)
PAUSE_MENU_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

PAUSE_TITLE = MenuText("GAME PAUSED", (SCREEN_WIDTH / 2, 120), 10, screen, TITLE_FONT, BLACK)
PAUSE_MENU.interactive_elements.append(PAUSE_TITLE)

PAUSE_RESUME = Button(screen, resume_game, StaticSprite("PAUSE_RESUME", "assets/unpause_button.png"), (SCREEN_WIDTH / 2, 180), 10)
PAUSE_QUIT = Button(screen, quit_to_main_from_pause, StaticSprite("PAUSE_QUIT", "assets/quit_button.png"), (SCREEN_WIDTH / 2, 230), 10)

PAUSE_MENU.add_button(PAUSE_RESUME)
PAUSE_MENU.add_button(PAUSE_QUIT)

#endregion

#region TUTORIAL GAME
TUTORIAL_GAME = Game(True)
TUTORIAL = Tutorial(screen, TUTORIAL_GAME)
TUTORIAL_AUDIO = BackgroundMusic(SoundFile("TUTORIAL_BGM", "audio/tutorial_loop.ogg"))

MVB_SPAWN_POSITION = PLAYER1_SPAWN_POSITION

TUTORIAL_PLAYER = Player(screen, PLAYER1_KEYLEFT, PLAYER1_KEYRIGHT, PLAYER1_KEYJUMP, PLAYER1_KEYDUCK, PLAYER1_KEYPUNCH, PLAYER1_KEYKICK, PLAYER1_KEYDODGE, MVB_SPAWN_POSITION, RIGHT, FIRST_HEALTHBAR_OFFSET, p1_character, TUTORIAL_GAME, PLAYER_HEALTH, True, TUTORIAL)
HITBOX_TUTORIAL_PLAYER = Hitbox(screen, TUTORIAL_PLAYER)

MVB_DUMMY1_SPAWN_POSITION = (2 * (SCREEN_WIDTH + PLAYER_SPRITE_WIDTH) / 3, 100)
TUTORIAL_DUMMY1 = Player(screen, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, MVB_DUMMY1_SPAWN_POSITION, RIGHT, (0, 0), DUMMY_CHARACTER, TUTORIAL_GAME, 2147483647, False, None)
HITBOX_TUTORIAL_DUMMY1 = Hitbox(screen, TUTORIAL_DUMMY1)

TUTORIAL_PLAYER.attach_opponent(TUTORIAL_DUMMY1, HITBOX_TUTORIAL_DUMMY1)
TUTORIAL_DUMMY1.attach_opponent(TUTORIAL_PLAYER, HITBOX_TUTORIAL_PLAYER)

TUTORIAL_BACKGROUND = SpritedGameObject(StaticSprite("TUTORIAL_BACKGROUND", "assets/mvb_background.png"), (320, 180), screen, -100, BACKGROUND_OBJECT)
TUTORIAL_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

TUTORIAL_PLATFORM_UPSTAIRS = Platform((SCREEN_WIDTH, 16), (SCREEN_WIDTH / 2, 290), screen)
TUTORIAL_PLATFORM_STAIRS1 = Platform((30, 16), (-35, 345), screen)
TUTORIAL_PLATFORM_STAIRS2 = Platform((30, 16), (-10, 360), screen)
TUTORIAL_PLATFORM_STAIRS3 = Platform((30, 16), (15, 375), screen)
TUTORIAL_PLATFORM_STAIRS4 = Platform((30, 16), (40, 390), screen)
TUTORIAL_PLATFORM_STAIRS5 = Platform((60, 16), (85, 405), screen)
TUTORIAL_PLATFORM_STAIRS6 = Platform((30, 16), (120, 420), screen)
TUTORIAL_PLATFORM_STAIRS7 = Platform((30, 16), (145, 435), screen)
TUTORIAL_PLATFORM_STAIRS8 = Platform((30, 16), (170, 450), screen)
TUTORIAL_PLATFORM_STAIRS9 = Platform((30, 16), (195, 465), screen)
TUTORIAL_PLATFORM_STAIRS10 = Platform((60, 16), (240, 480), screen)
TUTORIAL_PLATFORM_STAIRS11 = Platform((30, 16), (275, 495), screen)
TUTORIAL_PLATFORM_STAIRS12 = Platform((30, 16), (300, 510), screen)
TUTORIAL_PLATFORM_STAIRS13 = Platform((30, 16), (325, 525), screen)
TUTORIAL_PLATFORM_STAIRS14 = Platform((30, 16), (350, 540), screen)
TUTORIAL_PLATFORM_STAIRS15 = Platform((30, 16), (365, 555), screen)

TUTORIAL_IGO = [TUTORIAL_PLATFORM_UPSTAIRS, TUTORIAL_PLATFORM_STAIRS1, TUTORIAL_PLATFORM_STAIRS2, TUTORIAL_PLATFORM_STAIRS3, TUTORIAL_PLATFORM_STAIRS4, TUTORIAL_PLATFORM_STAIRS5, TUTORIAL_PLATFORM_STAIRS6, TUTORIAL_PLATFORM_STAIRS7, TUTORIAL_PLATFORM_STAIRS8, TUTORIAL_PLATFORM_STAIRS9, TUTORIAL_PLATFORM_STAIRS10, TUTORIAL_PLATFORM_STAIRS11, TUTORIAL_PLATFORM_STAIRS12, TUTORIAL_PLATFORM_STAIRS13, TUTORIAL_PLATFORM_STAIRS14, TUTORIAL_PLATFORM_STAIRS15]
TUTORIAL_SGO = [TUTORIAL_BACKGROUND]
TUTORIAL_GROUND_Y = 494
ground_y = TUTORIAL_GROUND_Y
TUTORIAL_MAP = Map("TUTORIAL_MAP", TUTORIAL_IGO, TUTORIAL_SGO, TUTORIAL_GROUND_Y)

TUTORIAL_GAME.add_players([TUTORIAL_PLAYER, TUTORIAL_DUMMY1], [HITBOX_TUTORIAL_PLAYER, HITBOX_TUTORIAL_DUMMY1])
TUTORIAL_GAME.load_map(TUTORIAL_MAP)

#endregion

#region MVB_GAME
MVB_GAME = Game(False)
MVB_GAME_AUDIO = BackgroundMusic(SoundFile("MVB_MAP_BGM", "audio/mvb_map_loop.mp3"))

MVB_P1_SPAWN_POSITION = ((SCREEN_WIDTH + PLAYER_SPRITE_WIDTH) / 5, ground_y)
MVB_P2_SPAWN_POSITION = MVB_DUMMY1_SPAWN_POSITION

MVB_PLAYER1 = Player(screen, PLAYER1_KEYLEFT, PLAYER1_KEYRIGHT, PLAYER1_KEYJUMP, PLAYER1_KEYDUCK, PLAYER1_KEYPUNCH, PLAYER1_KEYKICK, PLAYER1_KEYDODGE, MVB_P1_SPAWN_POSITION, RIGHT, FIRST_HEALTHBAR_OFFSET, p1_character, MVB_GAME, PLAYER_HEALTH, True, None)
HITBOX_MVB_PLAYER1 = Hitbox(screen, MVB_PLAYER1)

MVB_PLAYER2 = Player(screen, PLAYER2_KEYLEFT, PLAYER2_KEYRIGHT, PLAYER2_KEYJUMP, PLAYER2_KEYDUCK, PLAYER2_KEYPUNCH, PLAYER2_KEYKICK, PLAYER2_KEYDODGE, MVB_P2_SPAWN_POSITION, LEFT, SECOND_HEALTHBAR_OFFSET, p2_character, MVB_GAME, PLAYER_HEALTH, True, None)
HITBOX_MVB_PLAYER2 = Hitbox(screen, MVB_PLAYER2)

MVB_AIPLAYER2 = AI_Player(screen, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, MVB_P2_SPAWN_POSITION, LEFT, SECOND_HEALTHBAR_OFFSET, p2_character, MVB_GAME, PLAYER_HEALTH, True, None)
HITBOX_MVB_AIPLAYER2 = Hitbox(screen, MVB_AIPLAYER2)

#MVB_GAME.add_players([MVB_PLAYER1, MVB_PLAYER2], [HITBOX_MVB_PLAYER1, HITBOX_MVB_PLAYER2])

MVB_IGO = [TUTORIAL_PLATFORM_UPSTAIRS, TUTORIAL_PLATFORM_STAIRS1, TUTORIAL_PLATFORM_STAIRS2, TUTORIAL_PLATFORM_STAIRS3, TUTORIAL_PLATFORM_STAIRS4, TUTORIAL_PLATFORM_STAIRS5, TUTORIAL_PLATFORM_STAIRS6, TUTORIAL_PLATFORM_STAIRS7, TUTORIAL_PLATFORM_STAIRS8, TUTORIAL_PLATFORM_STAIRS9, TUTORIAL_PLATFORM_STAIRS10, TUTORIAL_PLATFORM_STAIRS11, TUTORIAL_PLATFORM_STAIRS12, TUTORIAL_PLATFORM_STAIRS13, TUTORIAL_PLATFORM_STAIRS14, TUTORIAL_PLATFORM_STAIRS15]
MVB_SGO = [TUTORIAL_BACKGROUND]
MVB_GROUND_Y = 494
ground_y = MVB_GROUND_Y
MVB_MAP = Map("MVB_MAP", MVB_IGO, MVB_SGO, MVB_GROUND_Y)

MVB_GAME.load_map(MVB_MAP)

#endregion

#region WILLS_GAME
WILLS_GAME = Game(False)
WILLS_GAME_AUDIO = BackgroundMusic(SoundFile("WILLS_MAP_BGM", "audio/wills_loop.ogg"))

WILLS_P1_SPAWN_POSITION = ((SCREEN_WIDTH + PLAYER_SPRITE_WIDTH) / 5, ground_y)
WILLS_P2_SPAWN_POSITION = (3.5 * (SCREEN_WIDTH + PLAYER_SPRITE_WIDTH) / 5, ground_y)

WILLS_PLAYER1 = Player(screen, PLAYER1_KEYLEFT, PLAYER1_KEYRIGHT, PLAYER1_KEYJUMP, PLAYER1_KEYDUCK, PLAYER1_KEYPUNCH, PLAYER1_KEYKICK, PLAYER1_KEYDODGE, WILLS_P1_SPAWN_POSITION, RIGHT, FIRST_HEALTHBAR_OFFSET, p1_character, WILLS_GAME, PLAYER_HEALTH, True, None)
HITBOX_WILLS_PLAYER1 = Hitbox(screen, WILLS_PLAYER1)

WILLS_PLAYER2 = Player(screen, PLAYER2_KEYLEFT, PLAYER2_KEYRIGHT, PLAYER2_KEYJUMP, PLAYER2_KEYDUCK, PLAYER2_KEYPUNCH, PLAYER2_KEYKICK, PLAYER2_KEYDODGE, WILLS_P2_SPAWN_POSITION, LEFT, SECOND_HEALTHBAR_OFFSET, p2_character, WILLS_GAME, PLAYER_HEALTH, True, None)
HITBOX_WILLS_PLAYER2 = Hitbox(screen, WILLS_PLAYER2)

WILLS_AIPLAYER2 = AI_Player(screen, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, WILLS_P2_SPAWN_POSITION, LEFT, SECOND_HEALTHBAR_OFFSET, p2_character, WILLS_GAME, PLAYER_HEALTH, True, None)
HITBOX_WILLS_AIPLAYER2 = Hitbox(screen, WILLS_AIPLAYER2)

WILLS_BACKGROUND = SpritedGameObject(StaticSprite("WILLS_BACKGROUND", "assets/wills_background.png"), (320, 180), screen, -100, BACKGROUND_OBJECT)
WILLS_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

HOT_AIR_BALLOON = SpritedGameObject(StaticSprite("HOT_AIR_BALLOON", "assets/hot_air_balloon.png"), (300, 100), screen, 15, FOREGROUND_OBJECT)
HOT_AIR_BALLOON.scale(2)

WILLS_ROAD_BUILDING1 = Platform((170, 16), (595, 225), screen)
WILLS_ROAD_BUILDING2 = Platform((170, 16), (765, 255), screen)
WILLS_ROAD_BUILDING3 = Platform((170, 16), (935, 305), screen)
WILLS_MEM_PLAT1 = Platform((250, 16), (300, 330), screen)
WILLS_ROAD_PLAT1 = Platform((790, 16), (100, 445), screen)
WILLS_ROAD_PLAT2 = Platform((80, 16), (530, 460), screen)
WILLS_ROAD_PLAT3 = Platform((80, 16), (610, 475), screen)
WILLS_ROAD_PLAT4 = Platform((80, 16), (690, 490), screen)
WILLS_ROAD_PLAT5 = Platform((80, 16), (770, 505), screen)
WILLS_ROAD_PLAT6 = Platform((200, 16), (900, 520), screen)

WILLS_IGO = [WILLS_ROAD_BUILDING1, WILLS_ROAD_BUILDING2, WILLS_ROAD_BUILDING3, WILLS_MEM_PLAT1, WILLS_ROAD_PLAT1, WILLS_ROAD_PLAT2, WILLS_ROAD_PLAT3, WILLS_ROAD_PLAT4, WILLS_ROAD_PLAT5, WILLS_ROAD_PLAT6]
WILLS_SGO = [WILLS_BACKGROUND, HOT_AIR_BALLOON]
WILLS_GROUND_Y = 450
ground_y = WILLS_GROUND_Y
WILLS_MAP = Map("WILLS_MAP", WILLS_IGO, WILLS_SGO, WILLS_GROUND_Y)

WILLS_GAME.load_map(WILLS_MAP)
#endregion

#region CLIFTON_GAME
CLIFTON_GAME = Game(False)
CLIFTON_GAME_AUDIO = BackgroundMusic(SoundFile("CLIFTON_MAP_BGM", "audio/clifton_loop.ogg"))

CLIFTON_P1_SPAWN_POSITION = ((SCREEN_WIDTH + PLAYER_SPRITE_WIDTH) / 6, ground_y)
CLIFTON_P2_SPAWN_POSITION = (4.3 * (SCREEN_WIDTH + PLAYER_SPRITE_WIDTH) / 6, ground_y)

CLIFTON_PLAYER1 = Player(screen, PLAYER1_KEYLEFT, PLAYER1_KEYRIGHT, PLAYER1_KEYJUMP, PLAYER1_KEYDUCK, PLAYER1_KEYPUNCH, PLAYER1_KEYKICK, PLAYER1_KEYDODGE, CLIFTON_P1_SPAWN_POSITION, RIGHT, FIRST_HEALTHBAR_OFFSET, p1_character, CLIFTON_GAME, PLAYER_HEALTH, True, None)
HITBOX_CLIFTON_PLAYER1 = Hitbox(screen, CLIFTON_PLAYER1)

CLIFTON_PLAYER2 = Player(screen, PLAYER2_KEYLEFT, PLAYER2_KEYRIGHT, PLAYER2_KEYJUMP, PLAYER2_KEYDUCK, PLAYER2_KEYPUNCH, PLAYER2_KEYKICK, PLAYER2_KEYDODGE, CLIFTON_P2_SPAWN_POSITION, LEFT, SECOND_HEALTHBAR_OFFSET, p2_character, CLIFTON_GAME, PLAYER_HEALTH, True, None)
HITBOX_CLIFTON_PLAYER2 = Hitbox(screen, CLIFTON_PLAYER2)

CLIFTON_AIPLAYER2 = AI_Player(screen, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, NO_KEY, CLIFTON_P2_SPAWN_POSITION, LEFT, SECOND_HEALTHBAR_OFFSET, p2_character, CLIFTON_GAME, PLAYER_HEALTH, True, None)
HITBOX_CLIFTON_AIPLAYER2 = Hitbox(screen, CLIFTON_AIPLAYER2)

# CLIFTON_PLAYER1.attach_opponent(CLIFTON_PLAYER2, HITBOX_CLIFTON_PLAYER2)
# CLIFTON_PLAYER2.attach_opponent(CLIFTON_PLAYER1, HITBOX_CLIFTON_PLAYER1)

CLIFTON_BACKGROUND = SpritedGameObject(StaticSprite("CLIFTON_BACKGROUND", "assets/clifton_background.png"), (320, 180), screen, -100, BACKGROUND_OBJECT)
CLIFTON_BACKGROUND.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

CLIFTON_BRIDGE = SpritedGameObject(StaticSprite("CLIFTON_BRIDGE", "assets/clifton_bridge_foreground.png"), (320, 180), screen, 15, FOREGROUND_OBJECT)
CLIFTON_BRIDGE.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

CLIFTON_CLOUDS = SpritedGameObject(StaticSprite("CLIFTON_CLOUDS", "assets/clifton_clouds.png"), (320, 180), screen, -80, BACKGROUND_OBJECT)
CLIFTON_CLOUDS.change_dimensions((SCREEN_WIDTH, SCREEN_HEIGHT))

CLIFTON_IGO = []
CLIFTON_SGO = [CLIFTON_BACKGROUND, CLIFTON_BRIDGE, CLIFTON_CLOUDS]
CLIFTON_GROUND_Y = 300
ground_y = CLIFTON_GROUND_Y
CLIFTON_MAP = Map("CLIFTON_MAP", CLIFTON_IGO, CLIFTON_SGO, CLIFTON_GROUND_Y)

# CLIFTON_GAME.add_players([CLIFTON_PLAYER1, CLIFTON_PLAYER2], [HITBOX_CLIFTON_PLAYER1, HITBOX_CLIFTON_PLAYER2])
CLIFTON_GAME.load_map(CLIFTON_MAP)

#endregion

#region FRAMELOOP

change_to_main_menu()

while True:
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            if (current_bgm): current_bgm.kill()
            pygame.quit()
            exit()

        if (current_menu):
            for element in current_menu.interactive_elements:
                if isinstance(element, Button):
                    element.handle_click(event)

        if (event.type == pygame.KEYDOWN) and (event.key == pygame.K_ESCAPE) and (not in_cutscene):
            if current_game and (current_menu is None):
                pause_game()
            elif (current_menu is PAUSE_MENU):
                resume_game()

    # game code
    screen.fill(WHITE)

    if (current_menu):
        if (current_menu is PAUSE_MENU) and current_game:
            current_game.redraw_frame()
        current_menu.redraw_frame()
        if (current_menu == SETTINGS_MENU):
            hicontrast = HICONTRAST_BUTTON.getValue()
            bgm_volume = 1 + (MUSIC_SLIDER.getValue() - 5) * 0.2
            sfx_volume = 1 + (SOUND_SLIDER.getValue() - 5) * 0.2
            fontsize = 28 + (TEXT_SLIDER.getValue() - 5) * 2
            font = pygame.font.Font(FONTFACE, fontsize)

            if (current_bgm): current_bgm.set_volume(bgm_volume)
    elif (current_game):
        current_game.redraw_frame()

    if (current_menu is not PAUSE_MENU):
        for callback in callbacks:
            callback.process()

    SCREENSWIPE.draw()
    COUNTDOWN.draw()
    SWIPESPRITE.draw()
    
    if (hicontrast):
        pixel_array = pygame.surfarray.pixels3d(screen)
        pixel_array[:,:,:] = 255 - pixel_array[:,:,:]
        del pixel_array

    pygame_widgets.update(events)
    pygame.display.update()
    clock.tick(FPS)

#endregion FRAMELOOP