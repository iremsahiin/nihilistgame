import math
import random

WIDTH = 960
HEIGHT = 540
TITLE = "Nihilist Penguen: Anlam İsteğe Bağlıdır"

GRAVITY = 0.55
MOVE_SPEED = 4.2
JUMP_SPEED = -11.5
GROUND_Y = 470

GAME_MENU = "menu"
GAME_PLAYING = "playing"
GAME_WON = "won"
GAME_LOST = "lost"

state = GAME_MENU
sound_on = True
music_started = False
shards_collected = 0
required_shards = 5

platforms = [
    Rect((0, GROUND_Y), (WIDTH, 70)),
    Rect((125, 385), (170, 22)),
    Rect((365, 325), (180, 22)),
    Rect((625, 385), (180, 22)),
    Rect((760, 285), (130, 22)),
]

start_button = Rect((350, 215), (260, 55))
sound_button = Rect((350, 290), (260, 55))
exit_button = Rect((350, 365), (260, 55))


def play_sound(name):
    if sound_on:
        getattr(sounds, name).play()


class AnimatedCharacter:
    def __init__(self, x, y, idle_frames, move_frames, frame_speed=0.14):
        self.actor = Actor(idle_frames[0], (x, y))
        self.idle_frames = idle_frames
        self.move_frames = move_frames
        self.frame_speed = frame_speed
        self.frame_timer = 0
        self.frame_index = 0
        self.moving = False

    def animate(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_speed:
            self.frame_timer = 0
            frames = self.move_frames if self.moving else self.idle_frames
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.actor.image = frames[self.frame_index]

    def draw(self):
        self.actor.draw()


class PenguinHero(AnimatedCharacter):
    def __init__(self):
        super().__init__(
            70,
            GROUND_Y - 28,
            ["penguin_idle_0", "penguin_idle_1", "penguin_idle_2"],
            ["penguin_walk_0", "penguin_walk_1", "penguin_walk_2", "penguin_walk_3"],
            0.11,
        )
        self.velocity_y = 0
        self.on_ground = False
        self.facing = 1
        self.lives = 3
        self.invulnerable = 0

    def reset_position(self):
        self.actor.pos = (70, GROUND_Y - 28)
        self.velocity_y = 0

    def update(self, dt):
        move_x = 0
        if keyboard.left or keyboard.a:
            move_x = -MOVE_SPEED
            self.facing = -1
        if keyboard.right or keyboard.d:
            move_x = MOVE_SPEED
            self.facing = 1

        self.moving = move_x != 0
        self.actor.x += move_x
        self.actor.x = max(24, min(WIDTH - 24, self.actor.x))

        self.velocity_y += GRAVITY
        self.actor.y += self.velocity_y
        self.on_ground = False

        feet = Rect((self.actor.x - 17, self.actor.y + 20), (34, 16))
        if self.velocity_y >= 0:
            for platform in platforms:
                if feet.colliderect(platform) and feet.bottom <= platform.top + 18:
                    self.actor.y = platform.top - 28
                    self.velocity_y = 0
                    self.on_ground = True
                    break

        if self.actor.y > HEIGHT + 50:
            self.take_hit()

        if self.invulnerable > 0:
            self.invulnerable -= dt
        self.animate(dt)

    def jump(self):
        if self.on_ground:
            self.velocity_y = JUMP_SPEED
            play_sound("jump")

    def take_hit(self):
        global state
        if self.invulnerable > 0:
            return
        self.lives -= 1
        play_sound("hit")
        self.invulnerable = 1.3
        self.reset_position()
        if self.lives <= 0:
            state = GAME_LOST
            play_sound("lose")


class DoubtEnemy(AnimatedCharacter):
    def __init__(self, x, y, left_edge, right_edge, speed, variant):
        idle = [f"enemy{variant}_idle_0", f"enemy{variant}_idle_1"]
        walk = [f"enemy{variant}_walk_0", f"enemy{variant}_walk_1", f"enemy{variant}_walk_2"]
        super().__init__(x, y, idle, walk, 0.16)
        self.left_edge = left_edge
        self.right_edge = right_edge
        self.speed = speed
        self.direction = random.choice([-1, 1])
        self.pause_timer = random.uniform(0.2, 1.0)

    def update(self, dt):
        if self.pause_timer > 0:
            self.pause_timer -= dt
            self.moving = False
        else:
            self.moving = True
            self.actor.x += self.speed * self.direction
            if self.actor.x <= self.left_edge or self.actor.x >= self.right_edge:
                self.direction *= -1
                self.actor.x = max(self.left_edge, min(self.right_edge, self.actor.x))
                self.pause_timer = random.uniform(0.15, 0.55)
        self.animate(dt)


class MeaningShard:
    def __init__(self, x, y):
        self.actor = Actor("shard_0", (x, y))
        self.frames = ["shard_0", "shard_1", "shard_2", "shard_3"]
        self.timer = random.random()
        self.index = 0
        self.collected = False

    def update(self, dt):
        self.timer += dt
        if self.timer > 0.13:
            self.timer = 0
            self.index = (self.index + 1) % len(self.frames)
            self.actor.image = self.frames[self.index]

    def draw(self):
        if not self.collected:
            self.actor.draw()


hero = PenguinHero()
enemies = [
    DoubtEnemy(210, 357, 145, 275, 1.7, 1),
    DoubtEnemy(450, 297, 385, 525, 2.0, 2),
    DoubtEnemy(705, 357, 645, 785, 1.8, 1),
    DoubtEnemy(825, 257, 780, 875, 2.2, 2),
]
shards = [
    MeaningShard(205, 350),
    MeaningShard(450, 290),
    MeaningShard(700, 350),
    MeaningShard(825, 250),
    MeaningShard(910, 435),
]
exit_actor = Actor("exit", (900, GROUND_Y - 35))


def reset_game():
    global shards_collected, state
    shards_collected = 0
    hero.lives = 3
    hero.invulnerable = 0
    hero.reset_position()
    for shard in shards:
        shard.collected = False
    state = GAME_PLAYING


def update(dt):
    global shards_collected, state, music_started
    if sound_on and not music_started:
        #music.play("nihilist_theme")
        music.set_volume(0.35)
        music_started = True

    if state != GAME_PLAYING:
        return

    hero.update(dt)
    for enemy in enemies:
        enemy.update(dt)
        if hero.actor.colliderect(enemy.actor) and hero.invulnerable <= 0:
            hero.take_hit()

    for shard in shards:
        shard.update(dt)
        if not shard.collected and hero.actor.colliderect(shard.actor):
            shard.collected = True
            shards_collected += 1
            play_sound("collect")

    if shards_collected == required_shards and hero.actor.colliderect(exit_actor):
        state = GAME_WON
        play_sound("win")


def draw_background():
    screen.fill((18, 24, 38))
    screen.blit("background", (0, 0))
    for platform in platforms:
        screen.draw.filled_rect(platform, (69, 93, 112))
        screen.draw.line((platform.left, platform.top), (platform.right, platform.top), (173, 219, 231))


def draw():
    if state == GAME_MENU:
        draw_menu()
        return

    draw_background()
    exit_actor.draw()
    for shard in shards:
        shard.draw()
    for enemy in enemies:
        enemy.draw()
    hero.draw()

    screen.draw.text(f"Meaning shards: {shards_collected}/{required_shards}", (20, 18), fontsize=28, color="white")
    screen.draw.text(f"Lives: {hero.lives}", (20, 50), fontsize=25, color="white")
    screen.draw.text("A/D or arrows: move   SPACE: jump   ESC: menu", (510, 20), fontsize=18, color=(205, 220, 230))

    if shards_collected < required_shards:
        screen.draw.text("The exit rejects your incomplete philosophy.", center=(WIDTH // 2, 505), fontsize=20, color=(220, 220, 220))
    else:
        screen.draw.text("All meaning acquired. Reach the glowing exit.", center=(WIDTH // 2, 505), fontsize=20, color=(240, 240, 170))

    if state == GAME_WON:
        draw_overlay("ANLAMI BULDUN", "Şüpheli. Menüye dönmek için tıkla.")
    elif state == GAME_LOST:
        draw_overlay("HİÇBİR ŞEYİN ANLAMI YOKTU", "Tahmin edilebilirdi. Menüye dönmek için tıkla.")


def draw_menu():
    screen.blit("menu_background", (0, 0))
    screen.draw.text("NİHİLİST PENGUEN", center=(WIDTH // 2, 105), fontsize=64, color="white")
    screen.draw.text("Anlam isteğe bağlı. Hayatta kalmak değil.", center=(WIDTH // 2, 155), fontsize=25, color=(195, 210, 225))
    draw_button(start_button, "OYUNA BAŞLA")
    draw_button(sound_button, "SES: AÇIK" if sound_on else "SES: KAPALI")
    draw_button(exit_button, "ÇIKIŞ")

def draw_button(rect, label):
    screen.draw.filled_rect(rect, (45, 58, 77))
    screen.draw.rect(rect, (170, 205, 220))
    screen.draw.text(label, center=rect.center, fontsize=30, color="white")


def draw_overlay(title, subtitle):
    panel = Rect((210, 175), (540, 190))
    screen.draw.filled_rect(panel, (12, 16, 25))
    screen.draw.rect(panel, (205, 220, 230))
    screen.draw.text(title, center=(WIDTH // 2, 235), fontsize=45, color="white")
    screen.draw.text(subtitle, center=(WIDTH // 2, 300), fontsize=22, color=(205, 220, 230))


def on_key_down(key):
    global state
    if state == GAME_PLAYING:
        if key == keys.SPACE:
            hero.jump()
        elif key == keys.ESCAPE:
            state = GAME_MENU


def on_mouse_down(pos):
    global sound_on, music_started, state
    if state in (GAME_WON, GAME_LOST):
        state = GAME_MENU
        return
    if state != GAME_MENU:
        return
    if start_button.collidepoint(pos):
        reset_game()
        play_sound("click")
    elif sound_button.collidepoint(pos):
        sound_on = not sound_on
        if sound_on:
            music.play("nihilist_theme")
            music.set_volume(0.35)
            music_started = True
            play_sound("click")
        else:
            music.stop()
            music_started = False
    elif exit_button.collidepoint(pos):
        raise SystemExit
