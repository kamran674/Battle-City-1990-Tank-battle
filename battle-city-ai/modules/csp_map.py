"""
csp_map.py — Module A: Constraint Satisfaction Problem Map Generator

Variables  : Each of the 676 tiles X_{i,j} on the 26×26 grid.
Domain     : {0=Empty, 1=Brick, 2=Steel, 3=Water, 4=Forest, 5=Eagle}
Constraints:
  C1 – Base Safety  : Eagle surrounded by ≥1 ring of Brick/Steel.
  C2 – Reachability : Valid BFS path from every spawn to Eagle must exist.
  C3 – Fairness     : No spawn within 10 tiles (Manhattan) of player start.
  C4 – Density      : ≤40 % of tiles may be wall-type tiles.
  C5 – Water        : Water may not block the only path to Eagle.

Algorithm: Probabilistic generation + backtracking + forward-checking.
"""

import random
from collections import deque
from modules.constants import (
    GRID_W, GRID_H, EMPTY, BRICK, STEEL, WATER, FOREST, EAGLE,
    EAGLE_POS, PLAYER_SPAWN, ENEMY_SPAWNS,
    SPAWN_CLEAR_RADIUS, CSP_MAX_WALL_FRACTION, LEVEL_CSP_PROFILE,
    DIRS
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _bfs_reachable(grid, start, goal):
    """Return True if there is any passable path from start to goal.
    Passable = EMPTY or FOREST (BFS ignores brick cost for reachability)."""
    sx, sy = start
    gx, gy = goal
    if not (0 <= sx < GRID_W and 0 <= sy < GRID_H):
        return False
    visited = set()
    q = deque([(sx, sy)])
    visited.add((sx, sy))
    while q:
        x, y = q.popleft()
        if (x, y) == (gx, gy):
            return True
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited:
                continue
            if not (0 <= nx < GRID_W and 0 <= ny < GRID_H):
                continue
            tile = grid[ny][nx]
            # reachability check: treat brick as passable (can be shot open)
            # only steel / water are absolute blockers for reachability
            if tile in (STEEL, WATER):
                continue
            visited.add((nx, ny))
            q.append((nx, ny))
    return False


# ── constraint checkers ───────────────────────────────────────────────────────

def _c1_base_safety(grid):
    """C1: Eagle must have at least 1 ring of Brick or Steel around it."""
    ex, ey = EAGLE_POS
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            nx, ny = ex + dx, ey + dy
            if not (0 <= nx < GRID_W and 0 <= ny < GRID_H):
                continue
            if grid[ny][nx] not in (BRICK, STEEL):
                return False
    return True


def _c2_reachability(grid):
    """C2: BFS path must exist from each spawn to Eagle."""
    for spawn in ENEMY_SPAWNS:
        if not _bfs_reachable(grid, spawn, EAGLE_POS):
            return False
    return True


def _c3_fairness(grid):
    """C3: No spawn within SPAWN_CLEAR_RADIUS Manhattan tiles of player start."""
    # This is enforced during generation (enemy spawns are fixed at top corners).
    # We verify player start is clear of enemy spawns.
    px, py = PLAYER_SPAWN
    for sx, sy in ENEMY_SPAWNS:
        if _manhattan((px, py), (sx, sy)) < SPAWN_CLEAR_RADIUS:
            return False   # by map design this should always pass
    return True


def _c4_density(grid):
    """C4: ≤40% of tiles are wall-type (Brick or Steel)."""
    wall_count = sum(
        1 for row in grid for tile in row if tile in (BRICK, STEEL)
    )
    total = GRID_W * GRID_H
    return wall_count / total <= CSP_MAX_WALL_FRACTION


def _c5_water_no_block(grid):
    """C5: Water tiles must not block the sole path to Eagle.
    We temporarily replace all water with STEEL and recheck reachability."""
    # make a temp grid with water replaced by steel
    temp = [row[:] for row in grid]
    for y in range(GRID_H):
        for x in range(GRID_W):
            if temp[y][x] == WATER:
                temp[y][x] = STEEL
    return _c2_reachability(temp)


def _all_constraints(grid):
    """Run all 5 constraints; return (ok:bool, failed:list[str])."""
    results = {
        "C1-BaseSafety":   _c1_base_safety(grid),
        "C2-Reachability": _c2_reachability(grid),
        "C3-Fairness":     _c3_fairness(grid),
        "C4-Density":      _c4_density(grid),
        "C5-WaterBlock":   _c5_water_no_block(grid),
    }
    failed = [k for k, v in results.items() if not v]
    return len(failed) == 0, failed


# ── protected zones (tiles that must keep fixed types) ────────────────────────

def _protected_positions():
    """Return set of (x,y) positions that must not be overwritten."""
    protected = set()
    protected.add(EAGLE_POS)
    # player spawn clear zone
    px, py = PLAYER_SPAWN
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            protected.add((px + dx, py + dy))
    # enemy spawn clear zone
    for sx, sy in ENEMY_SPAWNS:
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                protected.add((sx + dx, sy + dy))
    return protected


# ── map generation ─────────────────────────────────────────────────────────────

def _blank_grid():
    """Create a fully-EMPTY 26×26 grid."""
    return [[EMPTY] * GRID_W for _ in range(GRID_H)]


def _place_eagle(grid):
    ex, ey = EAGLE_POS
    grid[ey][ex] = EAGLE


def _place_eagle_ring(grid, ring_type=BRICK):
    """C1: Surround Eagle with Brick (or Steel) ring."""
    ex, ey = EAGLE_POS
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue
            nx, ny = ex + dx, ey + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                grid[ny][nx] = ring_type


def _place_eagle_double_ring(grid, ring_type=BRICK):
    """Place two protection layers around Eagle (Chebyshev radius 1 and 2)."""
    ex, ey = EAGLE_POS
    for radius in (1, 2):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                nx, ny = ex + dx, ey + dy
                if 0 <= nx < GRID_W and 0 <= ny < GRID_H and grid[ny][nx] != EAGLE:
                    grid[ny][nx] = ring_type


def _apply_terrain_noise(grid, protected, brick_p, steel_p, water_p, forest_p):
    """Probabilistically assign terrain to non-protected tiles.
    Uses forward-checking: skip if placing a wall would exceed density cap early."""
    wall_limit = int(GRID_W * GRID_H * CSP_MAX_WALL_FRACTION)
    wall_count = sum(1 for row in grid for t in row if t in (BRICK, STEEL))

    coords = [(x, y) for y in range(GRID_H) for x in range(GRID_W)
              if (x, y) not in protected and grid[y][x] == EMPTY]
    random.shuffle(coords)

    for (x, y) in coords:
        r = random.random()
        if r < brick_p:
            if wall_count < wall_limit:          # forward-check C4
                grid[y][x] = BRICK
                wall_count += 1
        elif r < brick_p + steel_p:
            if wall_count < wall_limit:
                grid[y][x] = STEEL
                wall_count += 1
        elif r < brick_p + steel_p + water_p:
            grid[y][x] = WATER
        elif r < brick_p + steel_p + water_p + forest_p:
            grid[y][x] = FOREST


def _repair_reachability(grid, protected):
    """Backtrack repair: carve a clear corridor from each spawn to Eagle.
    Converts any STEEL or WATER blocking tiles to EMPTY along the path."""
    for spawn in ENEMY_SPAWNS:
        if _bfs_reachable(grid, spawn, EAGLE_POS):
            continue
        sx, sy = spawn
        ex, ey = EAGLE_POS
        x, y = sx, sy
        # Carve vertical corridor first, then horizontal (L-shape)
        while y != ey:
            step = 1 if ey > y else -1
            y += step
            if (x, y) not in protected and grid[y][x] in (STEEL, WATER):
                grid[y][x] = EMPTY
        while x != ex:
            step = 1 if ex > x else -1
            x += step
            if (x, y) not in protected and grid[y][x] in (STEEL, WATER):
                grid[y][x] = EMPTY


# ── public API ────────────────────────────────────────────────────────────────

def generate_map(level: int, max_attempts: int = 50) -> list[list[int]]:
    """
    Generate a valid map for the given level using CSP + backtracking.

    Algorithm:
      1. Start from blank grid.
      2. Place fixed elements (Eagle, spawn zones).
      3. Enforce Eagle protection ring (C1).
      4. Probabilistically fill remaining tiles (forward-check C4 inline).
      5. If C2 or C5 fail → backtrack-repair then re-check.
      6. If any constraint still fails after max_attempts → return best valid map.

    Returns a 26×26 list[list[int]].
    """
    profile = LEVEL_CSP_PROFILE.get(level, LEVEL_CSP_PROFILE[1])
    brick_p, steel_p, water_p, forest_p = profile
    protected = _protected_positions()

    best_grid = None

    for attempt in range(max_attempts):
        grid = _blank_grid()
        _place_eagle(grid)

        # C1 — Eagle protection ring.
        if level == 1:
            _place_eagle_double_ring(grid, BRICK)
        else:
            _place_eagle_ring(grid, BRICK)  # Keep destructible to preserve reachability dynamics

        # Add ring cells to protected so noise doesn't overwrite them
        ex, ey = EAGLE_POS
        ring_protected = set(protected)
        ring_radius = 2 if level == 1 else 1
        for dy in range(-ring_radius, ring_radius + 1):
            for dx in range(-ring_radius, ring_radius + 1):
                ring_protected.add((ex + dx, ey + dy))

        # Probabilistic terrain fill with forward-checking on C4
        _apply_terrain_noise(grid, ring_protected, brick_p, steel_p, water_p, forest_p)

        # Repair step — carve corridors if C2/C5 fail
        _repair_reachability(grid, ring_protected)

        ok, failed = _all_constraints(grid)
        if ok:
            return grid

        # Keep the most recent candidate as fallback seed.
        best_grid = [row[:] for row in grid]

    # Final fallback: return a minimal safe map
    print(f"[CSP] Warning: could not fully satisfy all constraints after {max_attempts} attempts.")
    return _minimal_safe_map(level, best_grid)


def _minimal_safe_map(level: int, seed_grid=None) -> list[list[int]]:
    """Last-resort fallback: almost-empty map that satisfies all constraints."""
    for _ in range(120):
        grid = [row[:] for row in seed_grid] if seed_grid is not None else _blank_grid()
        _place_eagle(grid)
        if level == 1:
            _place_eagle_double_ring(grid, BRICK)
        else:
            _place_eagle_ring(grid, BRICK)

        # Ensure no hard barriers block all spawns.
        _repair_reachability(grid, _protected_positions())

        ok, _failed = _all_constraints(grid)
        if ok:
            return grid

        # If seeded grid was invalid, try fresh simple maps.
        seed_grid = None

    # Guaranteed playable emergency map.
    grid = _blank_grid()
    _place_eagle(grid)
    _place_eagle_ring(grid, BRICK)
    _repair_reachability(grid, _protected_positions())
    return grid


def generate_boss_arena() -> list[list[int]]:
    """
    Generate the 12×12 boss arena embedded in the centre of the 26×26 grid.
    Arena contains: some brick walls, steel pillars, one water patch.
    The rest of the outer grid is STEEL (impassable arena boundary).
    """
    grid = [[STEEL] * GRID_W for _ in range(GRID_H)]

    # Clear a 12×12 arena anchored around the fixed Eagle row.
    # This keeps the Eagle at (12,24) while ensuring all combat spawns are inside.
    arena_ox = (GRID_W - 12) // 2   # 7
    arena_oy = GRID_H - 12          # 14

    for y in range(arena_oy, arena_oy + 12):
        for x in range(arena_ox, arena_ox + 12):
            grid[y][x] = EMPTY

    # Place Eagle at the fixed project position
    ex, ey = EAGLE_POS
    grid[ey][ex] = EAGLE

    # Steel pillars (2×2 blocks in corners of arena)
    for (px, py) in [(arena_ox + 1, arena_oy + 1),
                     (arena_ox + 9, arena_oy + 1),
                     (arena_ox + 1, arena_oy + 8),
                     (arena_ox + 9, arena_oy + 8)]:
        for dy in range(2):
            for dx in range(2):
                if 0 <= px+dx < GRID_W and 0 <= py+dy < GRID_H:
                    grid[py + dy][px + dx] = STEEL

    # Brick walls — horizontal strips
    for x in range(arena_ox + 2, arena_ox + 10):
        grid[arena_oy + 4][x] = BRICK
        grid[arena_oy + 7][x] = BRICK

    # Water patch (centre-left)
    grid[arena_oy + 5][arena_ox + 4] = WATER
    grid[arena_oy + 6][arena_ox + 4] = WATER

    return grid
