"""
renderer_tk.py — Responsive Tkinter Canvas rendering engine with algorithm display
"""

from modules.constants import (
    GRID_W, GRID_H, TILE_SIZE, PANEL_W,
    EMPTY, BRICK, STEEL, WATER, FOREST, EAGLE,
    TYPE_BASIC, TYPE_FAST, TYPE_ARMOR, TYPE_BOSS, TYPE_PLAYER,
    BOSS_HP_MAX,
)

# Colour palette
C = {
    "bg": "#0f0f1c",
    "grid_line": "#1c1c2e",
    "brick": "#b44014",
    "brick_hi": "#e05520",
    "brick_lo": "#6a2508",
    "steel": "#6e7888",
    "steel_hi": "#a8b8c8",
    "steel_lo": "#484e58",
    "water1": "#1e50c8",
    "water2": "#3c78e0",
    "forest": "#1e6e1e",
    "forest_hi": "#2a9e2a",
    "eagle": "#dcc832",
    "eagle_hi": "#fff080",
    "player": "#ffd032",
    "basic": "#50c864",
    "fast": "#64b4ff",
    "armor": "#c864c8",
    "boss": "#ff3c3c",
    "armor_h0": "#c864c8",
    "armor_h1": "#e68c3c",
    "armor_h2": "#ff5050",
    "armor_h3": "#ffff50",
    "bullet_pl": "#ffe050",
    "bullet_en": "#ff5050",
    "panel_bg": "#090912",
    "panel_bdr": "#323250",
    "accent": "#ffc820",
    "text": "#dcdce0",
    "subtext": "#8080a0",
    "hp_ok": "#50c864",
    "hp_low": "#ff3c3c",
}

ARMOR_STAGE_COLOURS = ["#c864c8", "#e68c3c", "#ff5050", "#ffff50"]

# Algorithm icons and names
ALGO_INFO = {
    TYPE_BASIC: {"icon": "🟢", "name": "BFS", "agent": "Simple Reflex"},
    TYPE_FAST: {"icon": "🔵", "name": "Greedy BFS", "agent": "Goal-Based"},
    TYPE_ARMOR: {"icon": "🟣", "name": "A*", "agent": "Model-Based Reflex"},
    TYPE_BOSS: {"icon": "🔴", "name": "Minimax+αβ", "agent": "Adversarial"},
    TYPE_PLAYER: {"icon": "⭐", "name": "Human", "agent": "Player Control"},
}


class TkRenderer:
    """Responsive Tkinter renderer with algorithm display"""

    def __init__(self, canvas):
        self.canvas = canvas
        self._tick = 0
        self._scale = 1.0

    def _update_scale(self):
        """Update scale factor based on canvas size"""
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 0:
            target_width = GRID_W * TILE_SIZE + PANEL_W
            if target_width > 0:
                self._scale = canvas_width / target_width

    def draw(self, game_state):
        """Main draw function"""
        self._update_scale()
        self.canvas.delete("all")
        self._tick += 1

        if game_state:
            self._draw_grid(game_state.grid)
            self._draw_bullets(game_state.bullets)
            self._draw_tanks(game_state)
            self._draw_hud(game_state)

    def _draw_grid(self, grid):
        """Draw terrain grid"""
        scaled_tile = TILE_SIZE * self._scale

        for y in range(GRID_H):
            for x in range(GRID_W):
                tile = grid[y][x]
                rx = x * scaled_tile
                ry = y * scaled_tile
                self._draw_tile(tile, rx, ry, scaled_tile)

    def _draw_tile(self, tile, rx, ry, size):
        """Draw individual tile"""
        c = self.canvas

        if tile == EMPTY:
            c.create_rectangle(rx, ry, rx+size, ry+size,
                               fill=C["bg"], outline=C["grid_line"], width=1)

        elif tile == BRICK:
            c.create_rectangle(rx, ry, rx+size, ry+size,
                               fill=C["brick"], outline=C["brick_lo"], width=1)
            mid = size // 2
            c.create_line(rx, ry+mid, rx+size, ry+mid, fill=C["brick_lo"], width=1)
            c.create_line(rx+mid, ry, rx+mid, ry+mid, fill=C["brick_lo"], width=1)

        elif tile == STEEL:
            c.create_rectangle(rx, ry, rx+size, ry+size,
                               fill=C["steel"], outline=C["steel_lo"], width=1)
            c.create_line(rx+2, ry+2, rx+size-2, ry+size-2, fill=C["steel_hi"], width=1)
            c.create_line(rx+size-2, ry+2, rx+2, ry+size-2, fill=C["steel_hi"], width=1)

        elif tile == WATER:
            c.create_rectangle(rx, ry, rx+size, ry+size,
                               fill=C["water1"], outline=C["water1"], width=0)

        elif tile == FOREST:
            c.create_rectangle(rx, ry, rx+size, ry+size,
                               fill=C["forest"], outline=C["forest"], width=0)

        elif tile == EAGLE:
            pulse = C["eagle_hi"] if (self._tick // 8) % 2 == 0 else C["eagle"]
            c.create_rectangle(rx, ry, rx+size, ry+size,
                               fill=pulse, outline=C["eagle"], width=2)
            cx, cy = rx + size//2, ry + size//2
            c.create_line(cx, ry+3, cx, ry+size-3, fill="#1a1000", width=3)
            c.create_line(rx+3, cy, rx+size-3, cy, fill="#1a1000", width=3)
            c.create_oval(cx-4, cy-4, cx+4, cy+4, fill="#1a1000", outline="")

    def _draw_tanks(self, gs):
        """Draw all tanks with algorithm labels"""
        for tank in gs.enemies:
            if tank.alive:
                self._draw_tank(tank, gs)
        if gs.player.alive:
            self._draw_tank(gs.player, gs)

    def _draw_tank(self, tank, gs=None):
        """Draw individual tank (no algorithm badge)"""
        size = TILE_SIZE * self._scale
        rx = tank.x * size
        ry = tank.y * size
        cx = rx + size // 2
        cy = ry + size // 2
        c = self.canvas

        # Choose body colour
        if tank.tank_type == TYPE_ARMOR and hasattr(tank, "hit_count"):
            idx = min(tank.hit_count, 3)
            body_col = ARMOR_STAGE_COLOURS[idx]
        else:
            colours = {
                TYPE_PLAYER: C["player"],
                TYPE_BASIC: C["basic"],
                TYPE_FAST: C["fast"],
                TYPE_ARMOR: C["armor"],
                TYPE_BOSS: C["boss"],
            }
            body_col = colours.get(tank.tank_type, "#ffffff")

        pad = 3 * self._scale
        c.create_rectangle(rx + pad, ry + pad, rx + size - pad, ry + size - pad,
                           fill=body_col, outline="#4a4a5a", width=2)

        # Tracks
        dx, dy = tank.direction
        if dy == 0:
            c.create_rectangle(rx + 2, ry + 2, rx + size - 2, ry + 5, fill="#4a4a5a", outline="")
            c.create_rectangle(rx + 2, ry + size - 5, rx + size - 2, ry + size - 2, fill="#4a4a5a", outline="")
        else:
            c.create_rectangle(rx + 2, ry + 2, rx + 5, ry + size - 2, fill="#4a4a5a", outline="")
            c.create_rectangle(rx + size - 5, ry + 2, rx + size - 2, ry + size - 2, fill="#4a4a5a", outline="")

        # Turret barrel
        tx = cx + dx * (size // 2 - 4)
        ty = cy + dy * (size // 2 - 4)
        c.create_line(cx, cy, tx, ty, fill="#ffffff", width=4, capstyle='round')
        c.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#ffffff", outline="")

        # Armor tank HP indicator
        if tank.tank_type == TYPE_ARMOR and hasattr(tank, "hp"):
            hp_width = size // 4
            for i in range(tank.hp):
                hp_x = rx + 4 + i * hp_width
                hp_y = ry + size - 6
                c.create_rectangle(hp_x, hp_y, hp_x + hp_width - 2, hp_y + 4,
                                   fill=C["hp_ok"], outline="")
    def _draw_bullets(self, bullets):
        """Draw bullets"""
        size = TILE_SIZE * self._scale
        for b in bullets:
            if not b.active:
                continue
            bx = b.x * size + size // 2
            by = b.y * size + size // 2
            col = C["bullet_pl"] if b.owner_type == TYPE_PLAYER else C["bullet_en"]
            self.canvas.create_oval(bx-4, by-4, bx+4, by+4, fill=col, outline="")
            self.canvas.create_oval(bx-2, by-2, bx+2, by+2, fill="white", outline="")

    def _draw_hud(self, gs):
        """Draw HUD panel with algorithm display"""
        c = self.canvas
        panel_x = GRID_W * TILE_SIZE * self._scale
        panel_w = PANEL_W * self._scale

        c.create_rectangle(panel_x, 0, panel_x + panel_w, self.canvas.winfo_height(),
                           fill=C["panel_bg"], outline=C["panel_bdr"], width=2)

        y = 20 * self._scale
        px = panel_x + 10 * self._scale

        def draw_text(text, colour=C["text"], size=12, bold=False):
            nonlocal y
            font_size = int(size * self._scale)
            weight = "bold" if bold else "normal"
            c.create_text(px, y, text=text, fill=colour,
                          font=("Courier", font_size, weight), anchor="nw")
            y += (size + 4) * self._scale

        # Title
        draw_text("⚡ BATTLE CITY AI ⚡", colour=C["accent"], size=16, bold=True)
        draw_text(f"LEVEL {gs.level}", colour=C["subtext"], size=12)
        y += 10 * self._scale

        # Player stats
        draw_text("🎮 PLAYER", colour=C["accent"], size=13, bold=True)
        draw_text(f"Lives: {gs.player.lives}",
                 colour=C["hp_ok"] if gs.player.lives > 3 else C["hp_low"])
        draw_text(f"Score: {gs.score}", colour=C["subtext"])
        y += 10 * self._scale

        # Enemy stats
        draw_text("👾 ENEMIES", colour=C["accent"], size=13, bold=True)
        draw_text(f"Remaining: {gs.enemies_remaining}", colour=C["subtext"])
        draw_text(f"Active: {len(gs.enemies)}", colour=C["subtext"])
        y += 10 * self._scale

        # ========== ALGORITHM DISPLAY SECTION ==========
        draw_text("🤖 AI ALGORITHMS", colour=C["accent"], size=13, bold=True)

        # Display active enemy algorithms
        active_algos = {}
        for enemy in gs.enemies:
            if enemy.tank_type not in active_algos:
                active_algos[enemy.tank_type] = 0
            active_algos[enemy.tank_type] += 1

        for tank_type, count in active_algos.items():
            algo_info = ALGO_INFO.get(tank_type, {"icon": "🤖", "name": "AI", "agent": "Unknown"})
            colour = {
                TYPE_BASIC: C["basic"],
                TYPE_FAST: C["fast"],
                TYPE_ARMOR: C["armor"],
                TYPE_BOSS: C["boss"],
            }.get(tank_type, C["text"])

            algo_text = f"{algo_info['icon']} {algo_info['name']:12} x{count}"
            draw_text(algo_text, colour=colour, size=10)

        # AI Metrics
        y += 5 * self._scale
        draw_text("📊 AI METRICS", colour=C["accent"], size=12, bold=True)
        draw_text(f"BFS nodes: {gs.bfs_nodes_last}", colour=C["subtext"], size=10)
        draw_text(f"A* nodes: {gs.astar_nodes_last}", colour=C["subtext"], size=10)
        draw_text(f"Greedy steps: {gs.greedy_nodes_last}", colour=C["subtext"], size=10)

        # Minimax stats for Boss
        if gs.minimax_stats and gs.level == 3:
            y += 5 * self._scale
            draw_text("🧠 MINIMAX", colour=C["accent"], size=12, bold=True)
            ratio = gs.minimax_stats.get("speedup_ratio", "?")
            draw_text(f"α-β Speedup: {ratio}x", colour=C["hp_ok"], size=10, bold=True)

        # Boss HP Bar
        if gs.level == 3 and gs.enemies:
            boss = gs.enemies[0] if gs.enemies else None
            if boss and boss.tank_type == TYPE_BOSS:
                y += 10 * self._scale
                draw_text("💀 BOSS STATUS", colour=C["boss"], size=12, bold=True)
                draw_text(f"Phase: {boss.phase}", colour="#ff9640", size=11)

                # HP Bar
                bar_w = panel_w - 20
                bar_h = 12
                hp_frac = boss.hp / BOSS_HP_MAX
                c.create_rectangle(px, y, px + bar_w, y + bar_h,
                                   fill="#321010", outline=C["panel_bdr"])
                bar_col = C["hp_ok"] if hp_frac > 0.4 else C["hp_low"]
                c.create_rectangle(px, y, px + int(bar_w * hp_frac), y + bar_h,
                                   fill=bar_col, outline="")
                y += bar_h + 10 * self._scale

        # ========== ALGORITHM LEGEND ==========
        y = self.canvas.winfo_height() - 160 * self._scale

        draw_text("📖 ALGORITHM LEGEND", colour=C["accent"], size=11, bold=True)

        legend_items = [
            ("🟢 BFS", "Shortest path", C["basic"]),
            ("🔵 Greedy", "Rushes toward Eagle", C["fast"]),
            ("🟣 A*", "Cost-aware navigation", C["armor"]),
            ("🔴 Minimax", "Strategic decision", C["boss"]),
        ]

        for name, desc, colour in legend_items:
            draw_text(f"{name:12} {desc}", colour=colour, size=9)

        y += 5 * self._scale
        draw_text("🎯 Proximity Fire: Within 6 tiles", colour=C["subtext"], size=8)

        # Controls
        y = self.canvas.winfo_height() - 45 * self._scale
        draw_text("🎮 CONTROLS: WASD/Arrows | SPACE Fire | P Pause | ESC Menu",
                 colour=C["subtext"], size=8)