"""
search.py — Module B: Search Algorithms

Implements three distinct pathfinding algorithms, each mapped to a tank type:

  BFS          → Basic Tank   (shortest hops, no cost awareness)
  Greedy BFS   → Fast Tank    (single-step heuristic, can get stuck)
  A*           → Armor Tank   (optimal cost-aware; shoots through thin walls)

All algorithms operate on the 26×26 tile grid and return the NEXT STEP
the tank should take (a direction tuple), or None if no move is found.

Performance instrumentation is built-in: each call records node counts
so the report can compare BFS vs. A* vs. Greedy.
"""

from collections import deque
import heapq
from modules.constants import (
    GRID_W, GRID_H, EMPTY, BRICK, STEEL, WATER, FOREST, EAGLE,
    DIRS, TILE_COST, INF, EAGLE_POS
)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _in_bounds(x, y):
    return 0 <= x < GRID_W and 0 <= y < GRID_H


def _passable_bfs(grid, x, y):
    """BFS passability: only Empty and Forest are 'free'.
    Brick counts as passable for reachability (tank can shoot it open)."""
    tile = grid[y][x]
    return tile in (EMPTY, FOREST, BRICK, EAGLE)


def _passable_move(grid, x, y):
    """Actual movement passability (for simulation): Empty + Forest + Eagle."""
    tile = grid[y][x]
    return tile in (EMPTY, FOREST, EAGLE)


def _passable_astar(grid, x, y):
    """A* passability: same as BFS + Eagle is the goal."""
    tile = grid[y][x]
    return tile not in (STEEL, WATER)  # brick has a cost but IS traversable


def _manhattan(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def _reconstruct(came_from, start, goal):
    """Walk back from goal to start and return the first step direction."""
    path = []
    node = goal
    while node != start:
        path.append(node)
        node = came_from[node]
    path.reverse()
    if not path:
        return None
    fx, fy = start
    nx, ny = path[0]
    return (nx - fx, ny - fy)   # direction tuple


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHM 1 — BFS  (Basic Tank)
# ─────────────────────────────────────────────────────────────────────────────

class BFSResult:
    """Holds the result of a BFS call plus instrumentation data."""
    __slots__ = ("direction", "nodes_visited", "path_length")

    def __init__(self, direction, nodes_visited, path_length):
        self.direction    = direction       # (dx, dy) or None
        self.nodes_visited = nodes_visited  # int — for report
        self.path_length  = path_length     # int


def bfs(grid, start, goal=None):
    """
    Breadth-First Search from start toward goal (default: Eagle).

    Properties:
      - Finds the shortest-HOP path (not cost-optimal).
      - Treats Brick as passable (tank will shoot through it).
      - Treats Steel + Water as impassable.

    Returns: BFSResult
    """
    if goal is None:
        goal = EAGLE_POS

    sx, sy = start
    gx, gy = goal

    if (sx, sy) == (gx, gy):
        return BFSResult(None, 0, 0)

    visited = {(sx, sy)}
    came_from = {}
    queue = deque([(sx, sy)])
    nodes = 0

    while queue:
        x, y = queue.popleft()
        nodes += 1

        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited or not _in_bounds(nx, ny):
                continue
            if not _passable_bfs(grid, nx, ny):
                continue
            visited.add((nx, ny))
            came_from[(nx, ny)] = (x, y)
            if (nx, ny) == (gx, gy):
                direction = _reconstruct(came_from, (sx, sy), (gx, gy))
                path_len  = len([n for n in came_from if n != (sx, sy)])
                return BFSResult(direction, nodes, path_len)
            queue.append((nx, ny))

    return BFSResult(None, nodes, 0)   # unreachable


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHM 2 — Greedy Best-First Search  (Fast Tank)
# ─────────────────────────────────────────────────────────────────────────────

class GreedyResult:
    __slots__ = ("direction", "nodes_visited")

    def __init__(self, direction, nodes_visited):
        self.direction     = direction
        self.nodes_visited = nodes_visited


def greedy_best_first_step(grid, start, goal=None):
    """
    Greedy Best-First: single-step decision — pick the neighbour with the
    lowest Manhattan distance to goal.  No path caching needed.

    Key intentional flaw: can get stuck in local minima (surrounded by walls
    with the only opening behind it).  This demonstrates why greedy ≠ optimal.

    Returns: GreedyResult
    """
    if goal is None:
        goal = EAGLE_POS

    sx, sy = start
    gx, gy = goal

    best_dir    = None
    best_h      = INF
    nodes       = 0

    for dx, dy in DIRS:
        nx, ny = sx + dx, sy + dy
        nodes += 1
        if not _in_bounds(nx, ny):
            continue
        # Fast tank charges through brick (shoots it) but not steel/water
        if grid[ny][nx] in (STEEL, WATER):
            continue
        h = _manhattan(nx, ny, gx, gy)
        if h < best_h:
            best_h   = h
            best_dir = (dx, dy)

    return GreedyResult(best_dir, nodes)


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHM 3 — A* Search  (Armor Tank)
# ─────────────────────────────────────────────────────────────────────────────

class AStarResult:
    __slots__ = ("direction", "nodes_visited", "path_cost", "path_length")

    def __init__(self, direction, nodes_visited, path_cost, path_length):
        self.direction     = direction
        self.nodes_visited = nodes_visited
        self.path_cost     = path_cost
        self.path_length   = path_length


def astar(grid, start, goal=None):
    """
    A* Search with admissible Manhattan-distance heuristic.

    Cost function  g(n):
      Empty  = 1  |  Forest = 1  |  Brick = 3  |  Steel = ∞  |  Water = ∞

    Key insight: A* finds it cheaper to shoot through 1 brick wall (cost 3)
    than walk 6+ empty tiles around it (cost ≥6).  This creates strategically
    superior behaviour vs. BFS.

    Returns: AStarResult
    """
    if goal is None:
        goal = EAGLE_POS

    sx, sy = start
    gx, gy = goal

    if (sx, sy) == (gx, gy):
        return AStarResult(None, 0, 0, 0)

    # (f, g, x, y)
    open_heap = [(0 + _manhattan(sx, sy, gx, gy), 0, sx, sy)]
    g_score   = {(sx, sy): 0}
    came_from = {}
    nodes     = 0

    while open_heap:
        f, g, x, y = heapq.heappop(open_heap)
        nodes += 1

        if (x, y) == (gx, gy):
            direction = _reconstruct(came_from, (sx, sy), (gx, gy))
            return AStarResult(direction, nodes, g, len(came_from))

        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not _in_bounds(nx, ny):
                continue

            tile = grid[ny][nx]
            if (nx, ny) == (gx, gy):
                step_cost = 1
            else:
                step_cost = TILE_COST.get(tile, INF)
            if step_cost == INF:
                continue   # impassable

            ng = g + step_cost
            if ng < g_score.get((nx, ny), INF):
                g_score[(nx, ny)]   = ng
                came_from[(nx, ny)] = (x, y)
                h = _manhattan(nx, ny, gx, gy)
                heapq.heappush(open_heap, (ng + h, ng, nx, ny))

    return AStarResult(None, nodes, 0, 0)  # unreachable


# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHM COMPARISON DEMO  (used by Module B key-demonstration test)
# ─────────────────────────────────────────────────────────────────────────────

def compare_algorithms(grid, start, goal=None):
    """
    Run BFS, Greedy, and A* on the same grid+start+goal.
    Returns a dict with per-algorithm results for reporting.

    PDF requirement:
      'Place a thin brick wall (1 tile wide) across the direct path and a long
       detour (6+ empty tiles) around it. BFS takes detour. A* shoots through
       the wall. Greedy may get confused.'
    """
    if goal is None:
        goal = EAGLE_POS
    bfs_r    = bfs(grid, start, goal)
    greedy_r = greedy_best_first_step(grid, start, goal)
    astar_r  = astar(grid, start, goal)

    return {
        "BFS":    {"direction": bfs_r.direction,    "nodes": bfs_r.nodes_visited},
        "Greedy": {"direction": greedy_r.direction,  "nodes": greedy_r.nodes_visited},
        "A*":     {"direction": astar_r.direction,   "nodes": astar_r.nodes_visited,
                   "cost": astar_r.path_cost},
    }
