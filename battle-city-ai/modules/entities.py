"""
entities.py — Tank & Bullet classes with proximity fire for enemies
"""
import random
from modules.constants import (
    GRID_W, GRID_H, EMPTY, BRICK, STEEL, WATER, FOREST, EAGLE, EAGLE_POS,
    DIRS, UP, DOWN, LEFT, RIGHT,
    SPEED_SLOW, SPEED_MEDIUM, SPEED_FAST,
    FIRE_BASIC, FIRE_ARMOR, FIRE_FAST, FIRE_BOSS,
    ATTACK_RANGE, ENEMY_ATTACK_COOLDOWN,
    ARMOR_RETREAT_WAIT, BFS_REPLAN_INTERVAL,
    TYPE_BASIC, TYPE_FAST, TYPE_ARMOR, TYPE_BOSS, TYPE_PLAYER,
    TANK_COLOURS, ARMOR_HIT_COLOURS, BOSS_HP_MAX,
    MINIMAX_DEPTH, BOSS_PHASE2_HP, BOSS_PHASE3_HP,
)
from modules.search import bfs, greedy_best_first_step, astar
from modules.minimax import boss_decide, _get_phase

class Bullet:
    def __init__(self, x, y, direction, owner_type):
        self.x = x
        self.y = y
        self.direction = direction
        self.owner_type = owner_type
        self.active = True

        def destroy(self, all_tanks):
            self.active = False

            # Remove bullet reference from owner tank
            for tank in all_tanks:
                if tank.bullet is self:
                    tank.bullet = None

    def update(self, grid, all_tanks, bullets, on_brick_destroyed=None):
        from modules.constants import BULLET_SPEED
        for _ in range(BULLET_SPEED):
            if not self.active:
                return
            nx = self.x + self.direction[0]
            ny = self.y + self.direction[1]
            if not (0 <= nx < GRID_W and 0 <= ny < GRID_H):
                self.active = False
                return
            tile = grid[ny][nx]
            if tile == BRICK:
                grid[ny][nx] = EMPTY
                if on_brick_destroyed:
                    on_brick_destroyed(nx, ny)
                self.active = False
                return
            if tile in (STEEL, WATER, EAGLE):
                if tile == EAGLE:
                    for t in all_tanks:
                        if hasattr(t, "_eagle_hit"):
                            t._eagle_hit = True
                self.active = False
                return
            self.x, self.y = nx, ny
            for tank in all_tanks:
                if not tank.alive: continue
                if tank.x == self.x and tank.y == self.y:
                    if (self.owner_type == TYPE_PLAYER and tank.tank_type == TYPE_PLAYER) or \
                       (self.owner_type != TYPE_PLAYER and tank.tank_type != TYPE_PLAYER):
                        continue
                    tank.take_hit()
                    self.active = False
                    return
            for other in bullets:
                if other is self or not other.active: continue
                if other.x == self.x and other.y == self.y:
                    self.active = False
                    other.active = False
                    return

class Tank:
    def __init__(self, x, y, tank_type):
        self.x = x
        self.y = y
        self.tank_type = tank_type
        self.direction = DOWN
        self.alive = True
        self.bullet = None
        self._move_timer = 0
        self._fire_timer = 0
        self._attack_cooldown = 0

    def _can_move_to(self, nx, ny, grid, other_tanks):
        if not (0 <= nx < GRID_W and 0 <= ny < GRID_H):
            return False
        if grid[ny][nx] in (BRICK, STEEL, WATER):
            return False
        for t in other_tanks:
            if t is self or not t.alive: continue
            if t.x == nx and t.y == ny:
                return False
        return True

    def _move(self, direction, grid, other_tanks):
        nx = self.x + direction[0]
        ny = self.y + direction[1]
        self.direction = direction
        if self._can_move_to(nx, ny, grid, other_tanks):
            self.x, self.y = nx, ny
            return True
        return False

    def _distance_to_player(self, player):
        if player is None: return float('inf')
        return abs(self.x - player.x) + abs(self.y - player.y)

    def _has_line_of_sight(self, player, grid):
        if player is None: return False
        px, py, tx, ty = player.x, player.y, self.x, self.y
        if tx == px:
            step = 1 if py > ty else -1
            for y in range(ty + step, py, step):
                if grid[y][tx] in (STEEL, WATER, BRICK): return False
            return True
        if ty == py:
            step = 1 if px > tx else -1
            for x in range(tx + step, px, step):
                if grid[ty][x] in (STEEL, WATER, BRICK): return False
            return True
        return False

    def _try_proximity_fire(self, player, grid, bullets, all_tanks, on_brick_destroyed):
        if player is None or not player.alive: return False
        dist = self._distance_to_player(player)
        if dist <= ATTACK_RANGE:
            dx = player.x - self.x
            dy = player.y - self.y
            self.direction = (RIGHT if dx > 0 else LEFT) if abs(dx) > abs(dy) else (DOWN if dy > 0 else UP)
            if self._attack_cooldown <= 0 and self._fire_timer <= 0:
                if self._fire(bullets, grid, all_tanks, on_brick_destroyed):
                    self._attack_cooldown = ENEMY_ATTACK_COOLDOWN
                    return True
            return True
        return False

    def _fire(self, bullets, grid=None, all_tanks=None, on_brick_destroyed=None):
        if self._fire_timer > 0: return False
        if self.bullet and self.bullet.active: return False
        dx, dy = self.direction
        adjx, adjy = self.x + dx, self.y + dy
        if grid is not None and 0 <= adjx < GRID_W and 0 <= adjy < GRID_H:
            tile = grid[adjy][adjx]
            if tile == BRICK:
                grid[adjy][adjx] = EMPTY
                if on_brick_destroyed: on_brick_destroyed(adjx, adjy)
                return True
            if tile in (STEEL, WATER, EAGLE):
                if tile == EAGLE:
                    for t in (all_tanks or []):
                        if hasattr(t, "_eagle_hit"): t._eagle_hit = True
                return True
            if all_tanks is not None:
                for t in all_tanks:
                    if not t.alive: continue
                    if t.x == adjx and t.y == adjy:
                        if (self.tank_type == TYPE_PLAYER and t.tank_type == TYPE_PLAYER) or \
                           (self.tank_type != TYPE_PLAYER and t.tank_type != TYPE_PLAYER):
                            continue
                        t.take_hit()
                        return True
        self.bullet = Bullet(self.x, self.y, self.direction, self.tank_type)
        bullets.append(self.bullet)
        return True

    def take_hit(self):
        self.alive = False

    def update(self, grid, all_tanks, bullets, player=None, on_brick_destroyed=None):
        if self._move_timer > 0: self._move_timer -= 1
        if self._fire_timer > 0: self._fire_timer -= 1
        if self._attack_cooldown > 0: self._attack_cooldown -= 1

class PlayerTank(Tank):
    def __init__(self, x, y):
        super().__init__(x, y, TYPE_PLAYER)
        self.lives = 10
        self.move_speed = SPEED_FAST
        self._eagle_hit = False
        self._pending_dir = None
        self._pending_shoot = False
        self.respawn_pos = (x, y)  # 🆕 ADDED: Dynamic respawn tracking

    @property
    def colour(self):
        return TANK_COLOURS[TYPE_PLAYER]

    def set_input(self, direction, shoot):
        self._pending_dir = direction
        self._pending_shoot = shoot

    def take_hit(self):
        self.lives -= 1
        if self.lives <= 0:
            self.alive = False
        else:
            self.x, self.y = self.respawn_pos  # 🆕 UPDATED: Uses dynamic position

    def update(self, grid, all_tanks, bullets, player=None, on_brick_destroyed=None):
        super().update(grid, all_tanks, bullets, player, on_brick_destroyed)
        if self._move_timer == 0 and self._pending_dir:
            self._move(self._pending_dir, grid, all_tanks)
            self._move_timer = self.move_speed
        if self._pending_shoot:
            self._fire(bullets, grid, all_tanks, on_brick_destroyed)
            self._fire_timer = FIRE_BASIC
            self._pending_shoot = False
        self._pending_dir = None
        self._pending_shoot = False

class BasicTank(Tank):
    def __init__(self, x, y):
        super().__init__(x, y, TYPE_BASIC)
        self._bfs_path_dir = None
        self._replan_timer = 0
        self._bfs_nodes = 0
        self.speed_mult = 1.0
    @property
    def colour(self): return TANK_COLOURS[TYPE_BASIC]
    @property
    def speed(self): return max(1, int(SPEED_SLOW / self.speed_mult))
    def take_hit(self): self.alive = False
    def _replan_bfs(self, grid):
        result = bfs(grid, (self.x, self.y))
        self._bfs_path_dir = result.direction
        self._bfs_nodes = result.nodes_visited
        self._replan_timer = BFS_REPLAN_INTERVAL
    def update(self, grid, all_tanks, bullets, player=None, on_brick_destroyed=None):
        super().update(grid, all_tanks, bullets, player, on_brick_destroyed)
        # Prefer to engage the player if they're reasonably close, otherwise
        # follow BFS towards the Eagle (default behaviour).
        if player and player.alive:
            if self._try_proximity_fire(player, grid, bullets, all_tanks, on_brick_destroyed):
                return
        # Choose goal: player when nearby, else default (Eagle handled by bfs())
        goal = None
        if player and player.alive and self._distance_to_player(player) <= (ATTACK_RANGE * 2):
            goal = (player.x, player.y)

        self._replan_timer -= 1
        if self._replan_timer <= 0 or self._bfs_path_dir is None:
            # Pass goal through to BFS when provided
            result = bfs(grid, (self.x, self.y), goal) if goal is not None else bfs(grid, (self.x, self.y))
            self._bfs_path_dir = result.direction
            self._bfs_nodes = result.nodes_visited
            self._replan_timer = BFS_REPLAN_INTERVAL
        if player and self._has_line_of_sight(player, grid):
            if player.x < self.x: self.direction = LEFT
            elif player.x > self.x: self.direction = RIGHT
            elif player.y < self.y: self.direction = UP
            else: self.direction = DOWN
            if self._fire(bullets, grid, all_tanks, on_brick_destroyed):
                self._fire_timer = FIRE_BASIC
                return
        if self._move_timer == 0 and self._bfs_path_dir:
            dx, dy = self._bfs_path_dir
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and grid[ny][nx] == BRICK:
                self.direction = self._bfs_path_dir
                self._fire(bullets, grid, all_tanks, on_brick_destroyed)
                self._fire_timer = FIRE_BASIC
            else:
                moved = self._move(self._bfs_path_dir, grid, all_tanks)
                if not moved:
                    free = [d for d in DIRS if self._can_move_to(self.x + d[0], self.y + d[1], grid, all_tanks)]
                    if free: self._move(random.choice(free), grid, all_tanks)
                self._bfs_path_dir = None
            self._move_timer = self.speed

class FastTank(Tank):
    def __init__(self, x, y):
        super().__init__(x, y, TYPE_FAST)
        self._greedy_nodes = 0
        self.speed_mult = 1.0
    @property
    def colour(self): return TANK_COLOURS[TYPE_FAST]
    @property
    def speed(self): return max(1, int(SPEED_FAST / self.speed_mult))
    def take_hit(self): self.alive = False
    def update(self, grid, all_tanks, bullets, player=None, on_brick_destroyed=None):
        super().update(grid, all_tanks, bullets, player, on_brick_destroyed)
        if self._try_proximity_fire(player, grid, bullets, all_tanks, on_brick_destroyed):
            return
        # If player is nearby, bias the greedy step towards the player
        goal = None
        if player and player.alive and abs(self.x - player.x) + abs(self.y - player.y) <= (ATTACK_RANGE * 2):
            goal = (player.x, player.y)
        result = greedy_best_first_step(grid, (self.x, self.y), goal)
        self._greedy_nodes = result.nodes_visited
        if self._move_timer == 0 and result.direction:
            dx, dy = result.direction
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and grid[ny][nx] == BRICK:
                self.direction = result.direction
                self._fire(bullets, grid, all_tanks, on_brick_destroyed)
                self._fire_timer = FIRE_FAST
            else:
                self._move(result.direction, grid, all_tanks)
                self._move_timer = self.speed
        elif self._move_timer == 0:
            free = [d for d in DIRS if self._can_move_to(self.x + d[0], self.y + d[1], grid, all_tanks)]
            if free:
                self._move(random.choice(free), grid, all_tanks)
                self._move_timer = self.speed

class ArmorTank(Tank):
    def __init__(self, x, y):
        super().__init__(x, y, TYPE_ARMOR)
        self.hp = 4
        self.hit_count = 0
        self._astar_dir = None
        self._replan_timer = 0
        self._retreating = False
        self._retreat_wait = 0
        self._retreat_target = None
        self._astar_nodes = 0
        self.speed_mult = 1.0
    @property
    def colour(self): return ARMOR_HIT_COLOURS[min(self.hit_count, len(ARMOR_HIT_COLOURS) - 1)]
    @property
    def speed(self): return max(1, int(SPEED_MEDIUM / self.speed_mult))
    def take_hit(self):
        self.hp -= 1
        self.hit_count += 1
        if self.hp <= 0: self.alive = False; return
        if self.hit_count == 3:
            self._retreating = True
            self._astar_dir = None
            self._retreat_target = None
    def _find_nearest_steel(self, grid):
        from collections import deque
        q = deque([(self.x, self.y, 0)])
        visited = {(self.x, self.y)}
        while q:
            x, y, dist = q.popleft()
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < GRID_W and 0 <= ny < GRID_H): continue
                if grid[ny][nx] == STEEL: return (x, y)
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if (nx, ny) in visited or not (0 <= nx < GRID_W and 0 <= ny < GRID_H): continue
                if grid[ny][nx] in (EMPTY, FOREST):
                    visited.add((nx, ny))
                    q.append((nx, ny, dist + 1))
        return None
    def _replan_astar(self, grid):
        result = astar(grid, (self.x, self.y))
        self._astar_dir = result.direction
        self._astar_nodes = result.nodes_visited
        self._replan_timer = BFS_REPLAN_INTERVAL
    def update(self, grid, all_tanks, bullets, player=None, on_brick_destroyed=None):
        super().update(grid, all_tanks, bullets, player, on_brick_destroyed)
        if not self._retreating:
            if self._try_proximity_fire(player, grid, bullets, all_tanks, on_brick_destroyed):
                return
        self._replan_timer -= 1
        if self._retreating:
            if self._retreat_wait > 0:
                self._retreat_wait -= 1
                if self._retreat_wait == 0:
                    self._retreating = False
                    self._replan_astar(grid)
                return
            if self._retreat_target is None:
                self._retreat_target = self._find_nearest_steel(grid)
            if self._retreat_target:
                tx, ty = self._retreat_target
                if (self.x, self.y) == (tx, ty):
                    self._retreat_wait = ARMOR_RETREAT_WAIT
                    return
                result = bfs(grid, (self.x, self.y), self._retreat_target)
                if self._move_timer == 0 and result.direction:
                    self._move(result.direction, grid, all_tanks)
                    self._move_timer = self.speed
            return
        if self._replan_timer <= 0 or self._astar_dir is None:
            # Prefer to path directly at the player if they're nearby, otherwise
            # default to moving toward the Eagle.
            if player and player.alive and abs(self.x - player.x) + abs(self.y - player.y) <= (ATTACK_RANGE * 2):
                result = astar(grid, (self.x, self.y), (player.x, player.y))
                self._astar_dir = result.direction
                self._astar_nodes = result.nodes_visited
                self._replan_timer = BFS_REPLAN_INTERVAL
            else:
                self._replan_astar(grid)
        if player and self._has_line_of_sight(player, grid):
            if player.x < self.x: self.direction = LEFT
            elif player.x > self.x: self.direction = RIGHT
            elif player.y < self.y: self.direction = UP
            else: self.direction = DOWN
            if self._fire(bullets, grid, all_tanks, on_brick_destroyed):
                self._fire_timer = FIRE_ARMOR
        if self._move_timer == 0 and self._astar_dir:
            dx, dy = self._astar_dir
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and grid[ny][nx] == BRICK:
                self.direction = self._astar_dir
                self._fire(bullets, grid, all_tanks, on_brick_destroyed)
                self._fire_timer = FIRE_ARMOR
            else:
                moved = self._move(self._astar_dir, grid, all_tanks)
                if not moved: self._astar_dir = None
            self._move_timer = self.speed

class BossTank(Tank):
    def __init__(self, x, y):
        super().__init__(x, y, TYPE_BOSS)
        self.hp = BOSS_HP_MAX
        self._minimax_stats = {}
        self.speed_mult = 1.0
    @property
    def colour(self): return TANK_COLOURS[TYPE_BOSS]
    @property
    def phase(self): return _get_phase(self.hp)
    @property
    def speed(self):
        base_speed = {1: SPEED_SLOW, 2: SPEED_MEDIUM, 3: SPEED_FAST}[self.phase]
        return max(1, int(base_speed / self.speed_mult))
    @property
    def fire_rate(self): return {1: 60, 2: 45, 3: 24}[self.phase]
    def take_hit(self):
        self.hp = max(0, self.hp - 1)
        if self.hp <= 0: self.alive = False
    def update(self, grid, all_tanks, bullets, player=None, on_brick_destroyed=None):
        super().update(grid, all_tanks, bullets, player, on_brick_destroyed)
        if player is None or not player.alive:
            return
        if self._move_timer > 0:
            return
        self._move_timer = self.speed

        if self._try_proximity_fire(player, grid, bullets, all_tanks, on_brick_destroyed):
            self._fire_timer = self.fire_rate
            return

        action, stats = boss_decide(self, player, grid)
        self._minimax_stats = stats

        if action == "shoot":
            # Ensure boss faces the player or the Eagle before firing so shots
            # are aimed correctly (minimax may pick `shoot` without changing
            # the direction). Do not change game rules — only orient.
            if player and player.alive:
                dx = player.x - self.x
                dy = player.y - self.y
                if abs(dx) > abs(dy):
                    self.direction = (RIGHT if dx > 0 else LEFT)
                else:
                    self.direction = (DOWN if dy > 0 else UP)
            else:
                ex, ey = EAGLE_POS
                dx = ex - self.x
                dy = ey - self.y
                if abs(dx) > abs(dy):
                    self.direction = (RIGHT if dx > 0 else LEFT)
                else:
                    self.direction = (DOWN if dy > 0 else UP)
            if self._fire(bullets, grid, all_tanks, on_brick_destroyed):
                self._fire_timer = self.fire_rate
        elif action in DIRS:
            nx = self.x + action[0]
            ny = self.y + action[1]
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H and grid[ny][nx] == BRICK:
                self.direction = action
                if self._fire(bullets, grid, all_tanks, on_brick_destroyed):
                    self._fire_timer = self.fire_rate
            else:
                moved = self._move(action, grid, all_tanks)
                # 🆕 UPDATED: Fallback to prevent getting stuck on steel/other tanks
                if not moved:
                    free = [d for d in DIRS if self._can_move_to(self.x + d[0], self.y + d[1], grid, all_tanks)]
                    if free:
                        self._move(random.choice(free), grid, all_tanks)

def make_tank(tank_type, x, y):
    types = {
        TYPE_BASIC: BasicTank,
        TYPE_FAST: FastTank,
        TYPE_ARMOR: ArmorTank,
        TYPE_BOSS: BossTank,
    }
    if tank_type in types:
        return types[tank_type](x, y)
    raise ValueError(f"Unknown tank type: {tank_type}")