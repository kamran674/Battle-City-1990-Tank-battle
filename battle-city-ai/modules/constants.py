"""
constants.py — Central configuration for Battle City AI Project
"""

# ── Grid ──────────────────────────────────────────────────────────────────────
GRID_W = 26
GRID_H = 26
TILE_SIZE = 32          # Base pixels per tile
PANEL_W = 240           # right-hand info panel width

# ── Display ───────────────────────────────────────────────────────────────────
SCREEN_W = GRID_W * TILE_SIZE + PANEL_W   # 832 + 240 = 1072
SCREEN_H = GRID_H * TILE_SIZE             # 832
FPS = 30
GAME_TICK_MS = 1000 // FPS

# ── Game states ───────────────────────────────────────────────────────────────
STATE_MENU = "menu"
STATE_RULES = "rules"
STATE_SETTINGS = "settings"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"
STATE_LEVEL_CLEAR = "level_clear"

# ── Terrain codes ─────────────────────────────────────────────────────────────
EMPTY = 0
BRICK = 1
STEEL = 2
WATER = 3
FOREST = 4
EAGLE = 5

# A* traversal costs
INF = float('inf')
TILE_COST = {
    EMPTY: 1,
    BRICK: 3,
    STEEL: INF,
    WATER: INF,
    FOREST: 1,
    EAGLE: INF,
}

# ── Terrain colours ───────────────────────────────────────────────────────────
COLOURS = {
    EMPTY: (20, 20, 20),
    BRICK: (180, 80, 20),
    STEEL: (140, 140, 160),
    WATER: (30, 80, 200),
    FOREST: (34, 110, 34),
    EAGLE: (220, 200, 0),
}

# ── Fixed map positions ───────────────────────────────────────────────────────
EAGLE_POS = (12, 24)
PLAYER_SPAWN = (4, 24)
ENEMY_SPAWNS = [(0, 0), (12, 0), (24, 0)]
BOSS_PLAYER_SPAWN = (12, 22)
BOSS_SPAWN = (12, 14)

# ── Game rules ────────────────────────────────────────────────────────────────
MAX_ACTIVE_ENEMIES = 3
ENEMY_POOL_SIZE = 20
PLAYER_LIVES = 10
SPAWN_CLEAR_RADIUS = 10
ATTACK_RANGE = 6
ENEMY_ATTACK_COOLDOWN = 45

# ── Level configuration ───────────────────────────────────────────────────────
LEVEL_CONFIG = {
    1: {
        "active_enemies": 3,
        "enemy_speed_mult": 1.0,
        "enemy_count": 12,
        "spawn_delay": 90,
        "name": "Brick Maze"
    },
    2: {
        "active_enemies": 3,
        "enemy_speed_mult": 1.3,
        "enemy_count": 15,
        "spawn_delay": 75,
        "name": "Steel Fortress"
    },
    3: {
        "active_enemies": 1,
        "enemy_speed_mult": 1.0,
        "enemy_count": 1,
        "spawn_delay": 0,
        "name": "Boss Arena"
    }
}

# ── Tick rates (ticks between moves) ──────────────────────────────────────────
SPEED_SLOW = 4
SPEED_MEDIUM = 3
SPEED_FAST = 2

# ── Fire rates (ticks between shots) ──────────────────────────────────────────
FIRE_BASIC = 90
FIRE_ARMOR = 60
FIRE_FAST = 45
FIRE_BOSS = 30

# Bullet speed
BULLET_SPEED = 2

# Replan intervals
BFS_REPLAN_INTERVAL = 5 * FPS
ARMOR_RETREAT_WAIT = 2 * FPS

# ── Boss phase thresholds ─────────────────────────────────────────────────────
BOSS_HP_MAX = 10
BOSS_PHASE2_HP = 6
BOSS_PHASE3_HP = 2
MINIMAX_DEPTH = {1: 2, 2: 3, 3: 4}

# ── Directions ────────────────────────────────────────────────────────────────
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRS = [UP, DOWN, LEFT, RIGHT]

DIR_NAMES = {UP: "UP", DOWN: "DOWN", LEFT: "LEFT", RIGHT: "RIGHT"}

# ── Tank types ────────────────────────────────────────────────────────────────
TYPE_BASIC = "basic"
TYPE_FAST = "fast"
TYPE_ARMOR = "armor"
TYPE_BOSS = "boss"
TYPE_PLAYER = "player"

TANK_NAMES = {
    TYPE_BASIC: "Basic Tank",
    TYPE_FAST: "Fast Tank",
    TYPE_ARMOR: "Armor Tank",
    TYPE_BOSS: "Boss Tank",
    TYPE_PLAYER: "Player"
}

# ── Tank colours ──────────────────────────────────────────────────────────────
TANK_COLOURS = {
    TYPE_PLAYER: (255, 220, 50),
    TYPE_BASIC: (80, 200, 100),
    TYPE_FAST: (100, 180, 255),
    TYPE_ARMOR: (200, 100, 200),
    TYPE_BOSS: (255, 60, 60),
}

ARMOR_HIT_COLOURS = [
    (200, 100, 200),
    (230, 140, 60),
    (255, 80, 80),
    (255, 255, 80),
]

# ── CSP limits ────────────────────────────────────────────────────────────────
CSP_MAX_WALL_FRACTION = 0.40

LEVEL_CSP_PROFILE = {
    1: (0.35, 0.05, 0.03, 0.08),
    2: (0.20, 0.18, 0.04, 0.06),
    3: (0.15, 0.20, 0.06, 0.05),
}

# ── Level enemy pools ─────────────────────────────────────────────────────────
LEVEL_POOL = {
    1: [(TYPE_BASIC, 8), (TYPE_FAST, 4)],
    2: [(TYPE_FAST, 5), (TYPE_ARMOR, 5), (TYPE_BASIC, 5)],
}