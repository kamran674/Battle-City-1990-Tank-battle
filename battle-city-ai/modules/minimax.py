"""
minimax.py — Module C: Adversarial Search (Boss Tank)
Implements Minimax with Alpha-Beta Pruning for the Boss Tank (Tank Commander).
"""
from modules.constants import (
    GRID_W, GRID_H, DIRS, EMPTY, BRICK, FOREST, STEEL, WATER, EAGLE,
    EAGLE_POS, MINIMAX_DEPTH, BOSS_PHASE2_HP, BOSS_PHASE3_HP, INF,
    UP, DOWN, LEFT, RIGHT
)

# ── State representation ───────────────────────────────────────────────────────
class GameState:
    """Immutable snapshot used during minimax tree exploration."""
    __slots__ = (
        "boss_pos", "boss_dir", "boss_hp", "boss_phase",
        "player_pos", "player_hp",
        "grid_snapshot",
    )

    def __init__(self, boss_pos, boss_dir, boss_hp, boss_phase,
                 player_pos, player_hp, grid):
        self.boss_pos      = boss_pos     # (x, y)
        self.boss_dir      = boss_dir     # (dx, dy)
        self.boss_hp       = boss_hp
        self.boss_phase    = boss_phase
        self.player_pos    = player_pos   # (x, y)
        self.player_hp     = player_hp
        self.grid_snapshot = tuple(tuple(row) for row in grid)

    def tile(self, x, y):
        return self.grid_snapshot[y][x]

    def is_passable(self, x, y):
        if not (0 <= x < GRID_W and 0 <= y < GRID_H):
            return False
        # 🆕 UPDATED: Allow BRICK so minimax plans paths through destructible walls
        return self.tile(x, y) in (EMPTY, FOREST, BRICK)

    def _move_tank(self, pos, direction):
        nx = pos[0] + direction[0]
        ny = pos[1] + direction[1]
        if self.is_passable(nx, ny):
            return (nx, ny)
        return pos

    def apply_boss_action(self, action):
        if action == "shoot":
            return GameState(
                self.boss_pos, self.boss_dir, self.boss_hp, self.boss_phase,
                self.player_pos, self.player_hp, self.grid_snapshot
            )
        new_pos = self._move_tank(self.boss_pos, action)
        return GameState(
            new_pos, action, self.boss_hp, self.boss_phase,
            self.player_pos, self.player_hp, self.grid_snapshot
        )

    def apply_player_action(self, action):
        if action == "shoot":
            new_hp    = max(0, self.boss_hp - 1)
            new_phase = _get_phase(new_hp)
            return GameState(
                self.boss_pos, self.boss_dir, new_hp, new_phase,
                self.player_pos, self.player_hp, self.grid_snapshot
            )
        new_player_pos = self._move_tank(self.player_pos, action)
        return GameState(
            self.boss_pos, self.boss_dir, self.boss_hp, self.boss_phase,
            new_player_pos, self.player_hp, self.grid_snapshot
        )

    def boss_actions(self):
        actions = ["shoot"]
        for d in DIRS:
            nx = self.boss_pos[0] + d[0]
            ny = self.boss_pos[1] + d[1]
            if self.is_passable(nx, ny):
                actions.append(d)
        return actions

    def player_actions(self):
        actions = ["shoot"]
        for d in DIRS:
            nx = self.player_pos[0] + d[0]
            ny = self.player_pos[1] + d[1]
            if self.is_passable(nx, ny):
                actions.append(d)
        return actions

# ── Phase helper ──────────────────────────────────────────────────────────────
def _get_phase(hp):
    if hp <= BOSS_PHASE3_HP:
        return 3
    if hp <= BOSS_PHASE2_HP:
        return 2
    return 1

# ── Evaluation heuristic ──────────────────────────────────────────────────────
def _evaluate(state):
    """
    Boss Tank evaluation heuristic (MAX player wants high score).
    """
    score = 0
    bx, by = state.boss_pos
    px, py = state.player_pos

    dist = abs(bx - px) + abs(by - py)

    # Proximity bonus
    if dist <= 3:
        score += 60

    # Line-of-sight check
    if bx == px:
        step = 1 if py > by else -1
        blocked = any(
            state.tile(bx, y) in (BRICK, STEEL, WATER)
            for y in range(by + step, py, step)
        )
        if not blocked:
            score += 50
    elif by == py:
        step = 1 if px > bx else -1
        blocked = any(
            state.tile(x, by) in (BRICK, STEEL, WATER)
            for x in range(bx + step, px, step)
        )
        if not blocked:
            score += 50

    # Cover bonus
    for dx, dy in DIRS:
        nx, ny = bx + dx, by + dy
        if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
            if state.tile(nx, ny) == STEEL:
                score += 30
                break

    # HP penalties/bonuses
    score -= (10 - state.boss_hp) * 40
    score += (10 - state.player_hp) * 20

    # Forest vision penalty
    if state.tile(px, py) == FOREST:
        score -= 20

    # 🆕 UPDATED: Penalize distance to force the boss to close in instead of camping
    score -= dist * 3

    # Encourage the boss to approach the Eagle as an alternate objective
    ex, ey = EAGLE_POS
    edist = abs(bx - ex) + abs(by - ey)
    score -= edist * 2

    return score

# ── Minimax with Alpha-Beta Pruning ───────────────────────────────────────────
class MinimaxEngine:
    def __init__(self):
        self.nodes_no_pruning = 0
        self.nodes_with_pruning = 0

    def best_action(self, state, depth):
        self.nodes_with_pruning = 0
        best_val = -INF
        best_act = None
        alpha, beta = -INF, INF

        for action in state.boss_actions():
            child = state.apply_boss_action(action)
            val = self._min_value(child, depth - 1, alpha, beta)
            if val > best_val:
                best_val = val
                best_act = action
            alpha = max(alpha, best_val)

        b = 5
        self.nodes_no_pruning = sum(b ** d for d in range(depth + 1))

        stats = {
            "nodes_no_pruning":   self.nodes_no_pruning,
            "nodes_with_pruning": self.nodes_with_pruning,
            "speedup_ratio": round(
                self.nodes_no_pruning / max(self.nodes_with_pruning, 1), 2
            ),
        }
        return best_act, stats

    def _max_value(self, state, depth, alpha, beta):
        self.nodes_with_pruning += 1
        if depth == 0 or state.boss_hp <= 0 or state.player_hp <= 0:
            return _evaluate(state)

        v = -INF
        for action in state.boss_actions():
            child = state.apply_boss_action(action)
            v = max(v, self._min_value(child, depth - 1, alpha, beta))
            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    def _min_value(self, state, depth, alpha, beta):
        self.nodes_with_pruning += 1
        if depth == 0 or state.boss_hp <= 0 or state.player_hp <= 0:
            return _evaluate(state)

        v = INF
        for action in state.player_actions():
            child = state.apply_player_action(action)
            v = min(v, self._max_value(child, depth - 1, alpha, beta))
            if v <= alpha:
                return v
            beta = min(beta, v)
        return v

# ── Convenience function ─────────────────────────────────────────────────────
def boss_decide(boss_tank, player_tank, grid):
    bx, by = boss_tank.x, boss_tank.y
    phase  = _get_phase(boss_tank.hp)
    depth  = MINIMAX_DEPTH[phase]

    state = GameState(
        boss_pos   = (bx, by),
        boss_dir   = boss_tank.direction,
        boss_hp    = boss_tank.hp,
        boss_phase = phase,
        player_pos = (player_tank.x, player_tank.y),
        player_hp  = player_tank.lives,
        grid       = grid,
    )

    engine = MinimaxEngine()
    action, stats = engine.best_action(state, depth)
    return action, stats