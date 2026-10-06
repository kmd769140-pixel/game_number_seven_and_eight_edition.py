# ────────────────────────────────────────────────
# SPAWNERS  (replace the whole spawn_asteroid + spawn_powerup)
# ────────────────────────────────────────────────
def spawn_asteroid():
    size = random.randint(18, 48)
    x = random.randint(size + 14, WIDTH - size - 14)
    y = -size - 14
    speed = random.uniform(3.2 + level * 0.34, 5.9 + level * 0.52) * time_scale

    # Size-based HP (exactly as you requested)
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

def spawn_powerup(x, y, forced_kind=None):
    if forced_kind:
        kind = forced_kind
    else:
        kind = random.choices(
            ["life", "rapid", "shield", "warp", "multi"],
            weights=[18, 24, 24, 20, 14]          # slightly higher chance for life
        )[0]

    colors = {
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