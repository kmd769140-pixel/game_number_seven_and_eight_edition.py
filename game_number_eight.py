import tkinter as tk
import random
import math
import json
from pathlib import Path

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
WIDTH, HEIGHT = 960, 700
BASE_FPS = 14
PLAYER_SPEED = 7.8
MAX_LIVES = 3
HIGH_SCORE_FILE = Path.home() / ".neon_galaxy_highscore.json"

# Premium neon palette
NEON_CYAN   = "#22d3ee"
NEON_PINK   = "#f472b6"
NEON_PURPLE = "#c084fc"
NEON_YELLOW = "#fde047"
NEON_ORANGE = "#fb923c"
NEON_GREEN  = "#4ade80"
NEON_BLUE   = "#38bdf8"
DARK_BG     = "#020617"
MID_BG      = "#0f172a"

root = tk.Tk()
root.title("NEON GALAXY  •  PREMIUM")
root.resizable(False, False)
root.configure(bg=DARK_BG)

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                   bg=DARK_BG, highlightthickness=0)
canvas.pack()

# ────────────────────────────────────────────────
# STATE
# ────────────────────────────────────────────────
screen = "menu"
score = 0
level = 1
lives = MAX_LIVES
high_score = 0
paused = False
player_x = WIDTH // 2
player_y = HEIGHT - 105
keys = set()

asteroids = []
bullets = []
enemy_bullets = []
powerups = []
particles = []
stars = []
bullet_trails = []
engine_trails = []

boss = None
boss_active = False
boss_hp = boss_max_hp = 0
boss_spawned_this_level = False

spawn_timer = 14
shoot_cooldown = 0
invincible_timer = 0
time_scale = 1.0
time_warp_timer = 0
combo = 0
combo_timer = 0
frame = 0
rapid_fire_timer = 0

try:
    high_score = int(json.loads(HIGH_SCORE_FILE.read_text()).get("high_score", 0))
except Exception:
    high_score = 0

# ────────────────────────────────────────────────
# BACKGROUND – deeper space feel
# ────────────────────────────────────────────────
for _ in range(110):
    x, y = random.randrange(WIDTH), random.randrange(HEIGHT)
    s = random.choice([1, 1, 2])
    color = random.choice(["#64748b", "#67e8f9", "#a78bfa", "#f0abfc", "#94a3b8"])
    stars.append([
        canvas.create_oval(x, y, x+s, y+s, fill=color, outline=""),
        random.uniform(0.25, 1.0), s
    ])
for _ in range(70):
    x, y = random.randrange(WIDTH), random.randrange(HEIGHT)
    s = random.choice([2, 3, 3])
    color = random.choice(["#22d3ee", "#a78bfa", "#f472b6", "#c084fc"])
    stars.append([
        canvas.create_oval(x, y, x+s, y+s, fill=color, outline=""),
        random.uniform(1.2, 2.6), s
    ])

# Soft vignette
vignette = [
    canvas.create_rectangle(0, 0, WIDTH, 55, fill="#000000", outline="", stipple="gray50"),
    canvas.create_rectangle(0, HEIGHT-60, WIDTH, HEIGHT, fill="#000000", outline="", stipple="gray50"),
]

# Subtle scanlines
scanlines = []
for y in range(0, HEIGHT, 5):
    scanlines.append(canvas.create_line(0, y, WIDTH, y, fill="#0f172a", width=1))

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
hud = canvas.create_text(24, 18, anchor="nw", fill="#e2e8f0",
                         font=("Consolas", 15, "bold"))
level_text = canvas.create_text(WIDTH-24, 18, anchor="ne", fill=NEON_CYAN,
                                font=("Consolas", 15, "bold"))
speed_text = canvas.create_text(WIDTH//2, 18, anchor="n", fill=NEON_YELLOW,
                                font=("Consolas", 13, "bold"))
combo_text = canvas.create_text(WIDTH//2, 52, anchor="n", fill=NEON_PINK,
                                font=("Consolas", 18, "bold"))

boss_bg = canvas.create_rectangle(240, 62, 720, 80,
                                  fill="#1e1b4b", outline="", state="hidden")
boss_bar = canvas.create_rectangle(240, 62, 720, 80,
                                   fill=NEON_PINK, outline="", state="hidden")
boss_label = canvas.create_text(WIDTH//2, 48, text="◆ BOSS ◆",
                                fill=NEON_PURPLE, font=("Consolas", 13, "bold"),
                                state="hidden")

title = canvas.create_text(WIDTH//2, 150, text="NEON GALAXY",
                           fill=NEON_CYAN, font=("Consolas", 52, "bold"))
subtitle = canvas.create_text(WIDTH//2, 210, text="▸ PREMIUM HARDCORE SURVIVAL ◂",
                              fill=NEON_PURPLE, font=("Consolas", 16, "bold"))
menu = canvas.create_text(WIDTH//2, 360, fill="#e2e8f0",
                          font=("Consolas", 15), justify="center")
message = canvas.create_text(WIDTH//2, HEIGHT//2, fill="white",
                             font=("Consolas", 28, "bold"), justify="center")

player_parts = []

# ────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────
def distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

def burst(x, y, color=NEON_CYAN, amount=18, speed_mult=1.0):
    for _ in range(amount):
        a = random.random() * math.tau
        sp = random.uniform(2.2, 9.0) * speed_mult * time_scale
        size = random.randint(2, 5)
        item = canvas.create_oval(x-size, y-size, x+size, y+size,
                                  fill=color, outline="")
        particles.append([item, x, y, math.cos(a)*sp, math.sin(a)*sp,
                          random.randint(14, 34)])

def update_particles():
    for p in particles[:]:
        item, x, y, vx, vy, life = p
        x += vx
        y += vy
        vx *= 0.955
        vy *= 0.955
        life -= 1
        p[1:6] = [x, y, vx, vy, life]
        s = max(1, life // 9)
        canvas.coords(item, x-s, y-s, x+s, y+s)
        if life <= 0:
            canvas.delete(item)
            particles.remove(p)

def update_trails():
    for t in bullet_trails[:]:
        item, life = t
        life -= 1
        t[1] = life
        if life <= 0:
            canvas.delete(item)
            bullet_trails.remove(t)
        else:
            coords = canvas.coords(item)
            if coords:
                cx = (coords[0] + coords[2]) / 2
                cy = (coords[1] + coords[3]) / 2
                s = max(1, life / 5.5)
                canvas.coords(item, cx-s, cy-s, cx+s, cy+s)

    for t in engine_trails[:]:
        item, life = t
        life -= 1
        t[1] = life
        if life <= 0:
            canvas.delete(item)
            engine_trails.remove(t)
        else:
            coords = canvas.coords(item)
            if coords:
                cx = (coords[0] + coords[2]) / 2
                cy = (coords[1] + coords[3]) / 2
                s = max(1, life / 4)
                canvas.coords(item, cx-s, cy-s, cx+s, cy+s)

# ────────────────────────────────────────────────
# PLAYER – Unique premium fighter design
# ────────────────────────────────────────────────
def draw_player():
    for item in player_parts:
        canvas.delete(item)
    player_parts.clear()

    pulse = 1.0
    if invincible_timer:
        pulse = 1.0 + 0.18 * math.sin(frame * 0.45)

    # Outer soft glow
    g = 48 * pulse
    glow = canvas.create_oval(player_x-g, player_y-g, player_x+g, player_y+g,
                              outline="#0e7490", width=2)
    g2 = 34 * pulse
    glow2 = canvas.create_oval(player_x-g2, player_y-g2, player_x+g2, player_y+g2,
                               outline="#22d3ee", width=1)

    # Main body – unique angular fighter silhouette
    body = canvas.create_polygon(
        player_x,       player_y - 42,
        player_x - 11,  player_y - 18,
        player_x - 28,  player_y + 8,
        player_x - 22,  player_y + 28,
        player_x - 8,   player_y + 22,
        player_x,       player_y + 38,
        player_x + 8,   player_y + 22,
        player_x + 22,  player_y + 28,
        player_x + 28,  player_y + 8,
        player_x + 11,  player_y - 18,
        fill="#0ea5e9", outline="#ecfeff", width=2
    )

    # Upper armor plate
    armor = canvas.create_polygon(
        player_x,       player_y - 36,
        player_x - 9,   player_y - 16,
        player_x - 18,  player_y + 4,
        player_x,       player_y + 12,
        player_x + 18,  player_y + 4,
        player_x + 9,   player_y - 16,
        fill="#0284c7", outline="#67e8f9", width=1
    )

    # Cockpit canopy
    cockpit = canvas.create_oval(player_x-10, player_y-20,
                                 player_x+10, player_y+2,
                                 fill="#0f172a", outline="#a5f3fc", width=2)
    cockpit_glass = canvas.create_oval(player_x-6, player_y-16,
                                       player_x+6, player_y-2,
                                       fill="#22d3ee", outline="")

    # Wing accents / energy rails
    left_rail = canvas.create_polygon(
        player_x-26, player_y+6,
        player_x-32, player_y+14,
        player_x-20, player_y+18,
        player_x-14, player_y+10,
        fill=NEON_PINK, outline=""
    )
    right_rail = canvas.create_polygon(
        player_x+26, player_y+6,
        player_x+32, player_y+14,
        player_x+20, player_y+18,
        player_x+14, player_y+10,
        fill=NEON_PINK, outline=""
    )

    # Side thruster lights
    left_light  = canvas.create_oval(player_x-24, player_y+10, player_x-16, player_y+18,
                                     fill="#f9a8d4", outline="")
    right_light = canvas.create_oval(player_x+16, player_y+10, player_x+24, player_y+18,
                                     fill="#f9a8d4", outline="")

    # Main engine glow + core flame
    flame_h = 58 + random.randint(0, 14) + int(6 * time_scale)
    outer_flame = canvas.create_polygon(
        player_x - 14, player_y + 30,
        player_x,      player_y + flame_h,
        player_x + 14, player_y + 30,
        fill=NEON_ORANGE, outline=""
    )
    core_flame = canvas.create_polygon(
        player_x - 7, player_y + 32,
        player_x,     player_y + flame_h - 12,
        player_x + 7, player_y + 32,
        fill=NEON_YELLOW, outline=""
    )
    if frame % 2 == 0:
        trail = canvas.create_oval(player_x-4, player_y+36, player_x+4, player_y+44,
                                   fill="#fef08a", outline="")
        engine_trails.append([trail, 8])

    player_parts.extend([
        glow, glow2, body, armor, cockpit, cockpit_glass,
        left_rail, right_rail, left_light, right_light,
        outer_flame, core_flame
    ])

# ────────────────────────────────────────────────
# SPAWNERS
# ────────────────────────────────────────────────
def spawn_asteroid():
    size = random.randint(18, 48)
    x = random.randint(size + 14, WIDTH - size - 14)
    y = -size - 14
    speed = random.uniform(3.2 + level * 0.34, 5.9 + level * 0.52) * time_scale

    # Size-based HP (small = 1, medium = 2, large = 3)
    if size < 28:
        hp = 1
    elif size < 39:
        hp = 2
    else:
        hp = 3

    # Premium palette sets for different asteroid "species"
    palettes = [
        {  # Cyan crystal
            "glow": "#0e7490",
            "outline": "#67e8f9",
            "body": "#0f172a",
            "facet": "#164e63",
            "core": "#22d3ee",
            "vein": "#a5f3fc",
            "shard": "#67e8f9",
        },
        {  # Purple void
            "glow": "#4c1d95",
            "outline": "#c084fc",
            "body": "#1e1b4b",
            "facet": "#312e81",
            "core": "#e879f9",
            "vein": "#f0abfc",
            "shard": "#d8b4fe",
        },
        {  # Pink energy
            "glow": "#9d174d",
            "outline": "#f472b6",
            "body": "#1e1b4b",
            "facet": "#831843",
            "core": "#f9a8d4",
            "vein": "#fbcfe8",
            "shard": "#f472b6",
        },
        {  # Amber rock
            "glow": "#9a3412",
            "outline": "#fb923c",
            "body": "#1c1917",
            "facet": "#431407",
            "core": "#fde047",
            "vein": "#fef08a",
            "shard": "#fdba74",
        },
        {  # Emerald
            "glow": "#065f46",
            "outline": "#4ade80",
            "body": "#022c22",
            "facet": "#064e3b",
            "core": "#6ee7b7",
            "vein": "#a7f3d0",
            "shard": "#34d399",
        },
    ]
    pal = random.choice(palettes)

    # Build highly irregular premium silhouette
    points = []
    sides = random.randint(10, 15)
    for i in range(sides):
        a = i * math.tau / sides + random.uniform(-0.12, 0.12)
        r = size * random.uniform(0.55, 1.35)
        points += [x + math.cos(a) * r, y + math.sin(a) * r]

    items = []

    # 1. Soft outer glow
    glow_r = size * 1.55
    glow = canvas.create_oval(
        x - glow_r, y - glow_r, x + glow_r, y + glow_r,
        outline=pal["glow"], width=3
    )
    items.append(glow)

    # 2. Secondary thin glow ring
    glow2_r = size * 1.28
    glow2 = canvas.create_oval(
        x - glow2_r, y - glow2_r, x + glow2_r, y + glow2_r,
        outline=pal["outline"], width=1
    )
    items.append(glow2)

    # 3. Main body – dark crystalline rock
    body = canvas.create_polygon(
        *points, fill=pal["body"], outline=pal["outline"], width=2
    )
    items.append(body)

    # 4. Faceted overlay
    facet_pts = []
    for i in range(sides):
        a = i * math.tau / sides + 0.08
        r = size * random.uniform(0.42, 0.88)
        facet_pts += [x + math.cos(a) * r, y + math.sin(a) * r]
    facet = canvas.create_polygon(
        *facet_pts, fill=pal["facet"], outline=pal["vein"], width=1
    )
    items.append(facet)

    # 5. Glowing energy core
    core_s = size * random.uniform(0.22, 0.38)
    core = canvas.create_oval(
        x - core_s, y - core_s, x + core_s, y + core_s,
        fill=pal["core"], outline=pal["vein"], width=1
    )
    items.append(core)

    # 6. Inner bright pinpoint
    pin_s = core_s * 0.45
    pin = canvas.create_oval(
        x - pin_s, y - pin_s, x + pin_s, y + pin_s,
        fill="#ffffff", outline=""
    )
    items.append(pin)

    # 7. Energy veins / cracks
    vein_count = random.randint(3, 5)
    for _ in range(vein_count):
        a = random.random() * math.tau
        r1 = core_s * 0.9
        r2 = size * random.uniform(0.7, 1.05)
        x1 = x + math.cos(a) * r1
        y1 = y + math.sin(a) * r1
        x2 = x + math.cos(a) * r2
        y2 = y + math.sin(a) * r2
        vein = canvas.create_line(
            x1, y1, x2, y2,
            fill=pal["vein"], width=random.randint(1, 2)
        )
        items.append(vein)

    # 8. Small crystalline shards
    shard_count = random.randint(2, 4)
    for _ in range(shard_count):
        a = random.random() * math.tau
        dist = size * random.uniform(0.85, 1.25)
        sx = x + math.cos(a) * dist
        sy = y + math.sin(a) * dist
        ss = random.uniform(2.5, 5.5)
        sa = random.random() * math.tau
        sp = [
            sx + math.cos(sa) * ss,
            sy + math.sin(sa) * ss,
            sx + math.cos(sa + 2.1) * ss * 0.7,
            sy + math.sin(sa + 2.1) * ss * 0.7,
            sx + math.cos(sa + 4.2) * ss * 0.7,
            sy + math.sin(sa + 4.2) * ss * 0.7,
        ]
        shard = canvas.create_polygon(*sp, fill=pal["shard"], outline="")
        items.append(shard)

    asteroids.append({
        "items": items,
        "x": x, "y": y, "size": size,
        "speed": speed, "hp": hp
    })

def shoot():
    global shoot_cooldown
    if shoot_cooldown > 0:
        return

    speed = 16.5 * time_scale
    offsets = (-15, 15)
    if rapid_fire_timer > 0:
        offsets = (-18, -6, 6, 18)

    for dx in offsets:
        item = canvas.create_rectangle(
            player_x + dx - 2.8, player_y - 46,
            player_x + dx + 2.8, player_y - 20,
            fill=NEON_YELLOW, outline="#fffbeb", width=1
        )
        bullets.append({"item": item, "x": player_x + dx, "y": player_y - 33, "speed": speed})

        trail = canvas.create_oval(player_x+dx-3.5, player_y-33, player_x+dx+3.5, player_y-26,
                                   fill="#fef08a", outline="")
        bullet_trails.append([trail, 8])

    burst(player_x, player_y - 40, NEON_YELLOW, 6, 0.55)
    base_cd = 5.6 if rapid_fire_timer > 0 else 6.4
    shoot_cooldown = max(2, int(base_cd / time_scale))

def spawn_powerup(x, y, forced_kind=None):
    if forced_kind:
        kind = forced_kind
    else:
        kind = random.choices(
            ["life", "rapid", "shield", "warp", "multi"],
            weights=[18, 24, 24, 20, 14]   # slightly higher chance for life
        )[0]

    colors  = {
        "life": NEON_PINK, "rapid": NEON_YELLOW,
        "shield": NEON_BLUE, "warp": NEON_PURPLE, "multi": NEON_GREEN
    }
    symbols = {
        "life": "♥", "rapid": "⚡", "shield": "◆",
        "warp": "⌛", "multi": "✦"
    }

    glow = canvas.create_oval(x-20, y-20, x+20, y+20,
                              outline=colors[kind], width=2)
    item = canvas.create_oval(x-14, y-14, x+14, y+14,
                              fill=colors[kind], outline="white", width=1)
    label = canvas.create_text(x, y, text=symbols[kind],
                               fill="#0f172a", font=("Arial", 13, "bold"))
    powerups.append({
        "item": item, "label": label, "glow": glow,
        "x": x, "y": y, "kind": kind
    })

# ────────────────────────────────────────────────
# COMBAT & BOSS
# ────────────────────────────────────────────────
def hit_player():
    global lives, invincible_timer, combo
    if invincible_timer > 0:
        return
    lives -= 1
    invincible_timer = 80
    combo = 0
    burst(player_x, player_y, NEON_PINK, 48, 1.5)
    hud_update()
    if lives <= 0:
        end_game()

def start_boss():
    global boss_active, boss_hp, boss_max_hp, boss, boss_spawned_this_level
    if boss_active:
        return
    boss_active = True
    boss_spawned_this_level = True

    boss_max_hp = 100 + level * 42 + (level // 3) * 28
    boss_hp = boss_max_hp

    x, y = WIDTH // 2, -100
    body = canvas.create_polygon(
        x, y-78,
        x-105, y-28,
        x-138, y+58,
        x-58, y+42,
        x, y+82,
        x+58, y+42,
        x+138, y+58,
        x+105, y-28,
        fill="#4c1d95", outline=NEON_PURPLE, width=3
    )
    core = canvas.create_oval(x-34, y-12, x+34, y+44,
                              fill=NEON_PINK, outline="#fecdd3", width=2)
    eye = canvas.create_oval(x-14, y+6, x+14, y+34,
                             fill="#0f172a", outline="")
    left_plate = canvas.create_polygon(
        x-95, y-10, x-120, y+30, x-70, y+35, x-55, y+5,
        fill="#6d28d9", outline=NEON_PURPLE, width=1
    )
    right_plate = canvas.create_polygon(
        x+95, y-10, x+120, y+30, x+70, y+35, x+55, y+5,
        fill="#6d28d9", outline=NEON_PURPLE, width=1
    )

    boss = {
        "body": body, "core": core, "eye": eye,
        "left": left_plate, "right": right_plate,
        "x": x, "y": y,
        "vx": (3.6 + level * 0.14) * time_scale
    }

    canvas.itemconfig(boss_bg, state="normal")
    canvas.itemconfig(boss_bar, state="normal")
    canvas.itemconfig(boss_label, state="normal")
    canvas.itemconfig(boss_label, text=f"◆  BOSS  •  LEVEL {level}  ◆")
    boss_shoot()

def boss_shoot():
    if not boss_active or boss is None or paused:
        return

    pattern = level % 4
    if pattern == 0:
        offsets = [-80, -40, 0, 40, 80]
    elif pattern == 1:
        offsets = [-95, -50, 50, 95]
    elif pattern == 2:
        offsets = [-70, -25, 25, 70, 0]
    else:
        offsets = [-100, -60, -20, 20, 60, 100]

    for dx in offsets:
        item = canvas.create_oval(
            boss["x"]+dx-8, boss["y"]+50,
            boss["x"]+dx+8, boss["y"]+66,
            fill=NEON_PINK, outline="#fff1f2"
        )
        enemy_bullets.append({
            "item": item,
            "x": boss["x"] + dx,
            "y": boss["y"] + 58,
            "vx": dx * 0.024 * time_scale,
            "vy": (6.0 + level * 0.24) * time_scale
        })

    delay = max(200, int((760 - level * 24) / time_scale))
    root.after(delay, boss_shoot)

def defeat_boss():
    global boss_active, boss, score, boss_spawned_this_level
    burst(boss["x"], boss["y"], NEON_PURPLE, 140, 1.8)
    score += 950 + level * 90
    for key in ("body", "core", "eye", "left", "right"):
        canvas.delete(boss[key])
    boss = None
    boss_active = False
    boss_spawned_this_level = False
    canvas.itemconfig(boss_bg, state="hidden")
    canvas.itemconfig(boss_bar, state="hidden")
    canvas.itemconfig(boss_label, state="hidden")

def activate_powerup(kind):
    global lives, invincible_timer, time_warp_timer, shoot_cooldown, rapid_fire_timer
    if kind == "life":
        lives = min(MAX_LIVES, lives + 1)
        burst(player_x, player_y, NEON_PINK, 24)
    elif kind == "rapid":
        rapid_fire_timer = 320
        shoot_cooldown = 0
        invincible_timer = max(invincible_timer, 30)
    elif kind == "shield":
        invincible_timer = 300
    elif kind == "warp":
        time_warp_timer = 280
        burst(player_x, player_y, NEON_PURPLE, 32)
    elif kind == "multi":
        rapid_fire_timer = max(rapid_fire_timer, 180)
        invincible_timer = max(invincible_timer, 50)
        burst(player_x, player_y, NEON_GREEN, 26)
    hud_update()

# ────────────────────────────────────────────────
# HUD & TIME SCALE
# ────────────────────────────────────────────────
def hud_update():
    global high_score
    high_score = max(high_score, score)
    hearts = "♥ " * lives + "♡ " * (MAX_LIVES - lives)
    canvas.itemconfig(hud, text=f"SCORE  {score:06d}   BEST  {high_score:06d}\nLIVES  {hearts}")
    canvas.itemconfig(level_text, text=f"LEVEL {level}")

    extras = []
    if time_warp_timer > 0:
        extras.append("⚡ WARP")
    if rapid_fire_timer > 0:
        extras.append("✦ RAPID")
    extra_str = "  ".join(extras)
    canvas.itemconfig(speed_text, text=f"SPEED ×{time_scale:.2f}   {extra_str}")

    if combo >= 3:
        canvas.itemconfig(combo_text, text=f"COMBO ×{combo}", fill=NEON_PINK)
    else:
        canvas.itemconfig(combo_text, text="")

def update_time_scale():
    global time_scale
    base = 1.0 + min(2.3, (level - 1) * 0.09 + score / 10500)
    time_scale = base * 1.55 if time_warp_timer > 0 else base

# ────────────────────────────────────────────────
# MAIN LOOP
# ────────────────────────────────────────────────
def game_loop():
    global player_x, score, level, spawn_timer, shoot_cooldown
    global invincible_timer, boss_hp, time_warp_timer, combo, combo_timer, frame
    global boss_spawned_this_level, rapid_fire_timer

    frame += 1

    if screen == "game" and not paused:
        update_time_scale()

        # Movement
        move = PLAYER_SPEED * time_scale
        if "left" in keys or "a" in keys:
            player_x -= move
        if "right" in keys or "d" in keys:
            player_x += move
        player_x = max(45, min(WIDTH - 45, player_x))

        if "space" in keys:
            shoot()
        if shoot_cooldown > 0:
            shoot_cooldown -= 1

        draw_player()

        # Spawning
        spawn_timer -= time_scale
        if spawn_timer <= 0 and not boss_active:
            spawn_asteroid()
            spawn_timer = max(6.5, (33 - level * 1.7) / time_scale)

        # Level progression
        new_level = score // 430 + 1
        if new_level > level:
            level = new_level
            burst(WIDTH // 2, HEIGHT // 2, NEON_CYAN, 70)

            # ★ Guaranteed Extra Life every level ★
            spawn_powerup(
                random.randint(80, WIDTH - 80),
                -30,
                forced_kind="life"
            )

            if not boss_active:
                start_boss()

        # Asteroids
        for a in asteroids[:]:
            a["y"] += a["speed"]
            for item in a["items"]:
                canvas.move(item, 0, a["speed"])
            if a["y"] - a["size"] > HEIGHT + 30:
                for item in a["items"]:
                    canvas.delete(item)
                asteroids.remove(a)
                score += 4
                continue
            if distance(a["x"], a["y"], player_x, player_y) < a["size"] + 26:
                for item in a["items"]:
                    canvas.delete(item)
                asteroids.remove(a)
                burst(a["x"], a["y"], NEON_ORANGE, 34)
                hit_player()

        # Player bullets
        for b in bullets[:]:
            b["y"] -= b["speed"]
            canvas.move(b["item"], 0, -b["speed"])
            if b["y"] < -40:
                canvas.delete(b["item"])
                bullets.remove(b)
                continue

            hit = False
            for a in asteroids[:]:
                if distance(b["x"], b["y"], a["x"], a["y"]) < a["size"] + 6:
                    a["hp"] -= 1
                    burst(b["x"], b["y"], NEON_YELLOW, 8)
                    canvas.delete(b["item"])
                    bullets.remove(b)
                    hit = True
                    combo += 1
                    combo_timer = 80
                    if a["hp"] <= 0:
                        pts = (28 + a["size"] // 2) * (1 + combo // 5)
                        score += pts
                        burst(a["x"], a["y"], "#94a3b8", 28)
                        if random.random() < 0.08:
                            spawn_powerup(a["x"], a["y"])
                        for item in a["items"]:
                            canvas.delete(item)
                        asteroids.remove(a)
                    break

            if not hit and boss_active and boss:
                if distance(b["x"], b["y"], boss["x"], boss["y"]) < 105:
                    boss_hp -= 1
                    burst(b["x"], b["y"], NEON_PURPLE, 5)
                    canvas.delete(b["item"])
                    bullets.remove(b)
                    ratio = max(0, boss_hp / boss_max_hp)
                    canvas.coords(boss_bar, 240, 62, 240 + 480 * ratio, 80)
                    if boss_hp <= 0:
                        defeat_boss()

        # Enemy bullets
        for b in enemy_bullets[:]:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            canvas.move(b["item"], b["vx"], b["vy"])
            if b["y"] > HEIGHT + 40:
                canvas.delete(b["item"])
                enemy_bullets.remove(b)
                continue
            if distance(b["x"], b["y"], player_x, player_y) < 26:
                canvas.delete(b["item"])
                enemy_bullets.remove(b)
                hit_player()

        # Boss movement
        if boss_active and boss:
            if boss["y"] < 125:
                dy = 2.5 * time_scale
                boss["y"] += dy
                for key in ("body", "core", "eye", "left", "right"):
                    canvas.move(boss[key], 0, dy)
            else:
                boss["x"] += boss["vx"]
                if boss["x"] < 140 or boss["x"] > WIDTH - 140:
                    boss["vx"] *= -1
                for key in ("body", "core", "eye", "left", "right"):
                    canvas.move(boss[key], boss["vx"], 0)

        # Power-ups
        for p in powerups[:]:
            dy = 2.7 * time_scale
            p["y"] += dy
            canvas.move(p["item"], 0, dy)
            canvas.move(p["label"], 0, dy)
            canvas.move(p["glow"], 0, dy)
            if p["y"] > HEIGHT + 35:
                canvas.delete(p["item"])
                canvas.delete(p["label"])
                canvas.delete(p["glow"])
                powerups.remove(p)
                continue
            if distance(p["x"], p["y"], player_x, player_y) < 35:
                activate_powerup(p["kind"])
                burst(p["x"], p["y"], NEON_YELLOW, 18)
                canvas.delete(p["item"])
                canvas.delete(p["label"])
                canvas.delete(p["glow"])
                powerups.remove(p)

        # Timers
        if invincible_timer > 0:
            invincible_timer -= 1
        if time_warp_timer > 0:
            time_warp_timer -= 1
        if rapid_fire_timer > 0:
            rapid_fire_timer -= 1
        if combo_timer > 0:
            combo_timer -= 1
            if combo_timer <= 0:
                combo = 0

        hud_update()

    update_particles()
    update_trails()

    delay = max(7, int(BASE_FPS / (0.78 + 0.22 * time_scale)))
    root.after(delay, game_loop)

# ────────────────────────────────────────────────
# STATE MANAGEMENT
# ────────────────────────────────────────────────
def clear_objects():
    for a in asteroids:
        for item in a["items"]:
            canvas.delete(item)
    for b in bullets:
        canvas.delete(b["item"])
    for b in enemy_bullets:
        canvas.delete(b["item"])
    for p in powerups:
        canvas.delete(p["item"])
        canvas.delete(p["label"])
        canvas.delete(p["glow"])
    for p in particles:
        canvas.delete(p[0])
    for t in bullet_trails:
        canvas.delete(t[0])
    for t in engine_trails:
        canvas.delete(t[0])
    asteroids.clear()
    bullets.clear()
    enemy_bullets.clear()
    powerups.clear()
    particles.clear()
    bullet_trails.clear()
    engine_trails.clear()

def start_game():
    global screen, score, level, lives, paused, player_x
    global spawn_timer, boss, boss_active, shoot_cooldown
    global invincible_timer, time_scale, time_warp_timer, combo
    global boss_spawned_this_level, rapid_fire_timer

    clear_objects()
    if boss:
        for key in ("body", "core", "eye", "left", "right"):
            canvas.delete(boss[key])
    boss = None
    boss_active = False
    boss_spawned_this_level = False
    canvas.itemconfig(boss_bg, state="hidden")
    canvas.itemconfig(boss_bar, state="hidden")
    canvas.itemconfig(boss_label, state="hidden")

    score = 0
    level = 1
    lives = MAX_LIVES
    paused = False
    player_x = WIDTH // 2
    spawn_timer = 12
    shoot_cooldown = 0
    invincible_timer = 0
    time_scale = 1.0
    time_warp_timer = 0
    rapid_fire_timer = 0
    combo = 0
    screen = "game"

    canvas.itemconfig(title, state="hidden")
    canvas.itemconfig(subtitle, state="hidden")
    canvas.itemconfig(menu, state="hidden")
    canvas.itemconfig(message, text="")
    draw_player()
    hud_update()

def show_menu():
    global screen, paused
    screen = "menu"
    paused = False
    canvas.itemconfig(title, state="normal")
    canvas.itemconfig(subtitle, state="normal")
    canvas.itemconfig(menu, state="normal")
    canvas.itemconfig(menu, text=
        "PREMIUM HARDCORE MODE\n\n"
        "Boss every level  •  Unique fighter  •  Faster enemies\n"
        "Large rocks need multiple hits  •  Extra life every level\n\n"
        "← →   or   A D      Move\n"
        "SPACE                 Shoot\n"
        "P                     Pause\n\n"
        "Press  ENTER  to Start\n\n"
        f"BEST SCORE  {high_score}")
    canvas.itemconfig(message, text="")

def pause_game():
    global paused
    if screen == "game":
        paused = not paused
        canvas.itemconfig(message,
            text="PAUSED\n\nPress P to continue" if paused else "")

def end_game():
    global screen, high_score
    screen = "gameover"
    if score > high_score:
        high_score = score
        try:
            HIGH_SCORE_FILE.write_text(json.dumps({"high_score": high_score}))
        except Exception:
            pass
    canvas.itemconfig(message, text=
        f"GAME OVER\n\n"
        f"SCORE   {score}\n"
        f"LEVEL   {level}\n"
        f"BEST    {high_score}\n\n"
        "ENTER  →  Play Again\n"
        "ESC    →  Menu")

def key_down(event):
    key = event.keysym.lower()
    keys.add(key)
    if key == "return" and screen in ("menu", "gameover"):
        start_game()
    elif key == "p":
        pause_game()
    elif key == "escape" and screen == "game":
        show_menu()

def key_up(event):
    keys.discard(event.keysym.lower())

def animate_stars():
    for item, speed, size in stars:
        canvas.move(item, 0, speed * max(0.75, time_scale * 0.92))
        c = canvas.coords(item)
        if c and c[1] > HEIGHT:
            x = random.randrange(WIDTH)
            canvas.coords(item, x, -size, x + size, 0)
    root.after(28, animate_stars)

# ────────────────────────────────────────────────
# START
# ────────────────────────────────────────────────
root.bind("<KeyPress>", key_down)
root.bind("<KeyRelease>", key_up)

show_menu()
animate_stars()
game_loop()
root.mainloop()