"""
game_state.py — Core game loop logic with level progression
"""

import random
from modules.constants import (
    EAGLE_POS, PLAYER_SPAWN, ENEMY_SPAWNS,
    BOSS_PLAYER_SPAWN, BOSS_SPAWN,
    SPAWN_CLEAR_RADIUS,
    LEVEL_CONFIG, LEVEL_POOL,
    TYPE_BASIC, TYPE_FAST, TYPE_ARMOR, TYPE_BOSS,
    GRID_W, GRID_H
)
from modules.entities import PlayerTank, make_tank
from modules.csp_map import generate_map, generate_boss_arena


class GameState:
    """Central game state object with level progression"""

    def __init__(self, level: int, menu_system=None, on_level_complete=None):
        self.level = level
        self.menu_system = menu_system
        self.on_level_complete = on_level_complete
        self.tick = 0
        self.game_over = False
        self.won = False
        self.paused = False
        self.score = 0

        # Level configuration
        level_cfg = LEVEL_CONFIG.get(level, LEVEL_CONFIG[1])
        self.active_enemy_cap = level_cfg["active_enemies"]
        self.enemy_speed_mult = level_cfg["enemy_speed_mult"]
        self.spawn_delay = level_cfg["spawn_delay"]

        # Generate map and set spawn positions
        if level == 3:
            self.grid = generate_boss_arena()
            player_spawn = BOSS_PLAYER_SPAWN
            self.boss_spawn = BOSS_SPAWN
        else:
            self.grid = generate_map(level)
            player_spawn = PLAYER_SPAWN
            self.boss_spawn = None

        # Player with correct spawn position
        self.player = PlayerTank(player_spawn[0], player_spawn[1])
        # Store spawn position for respawn
        self.player.spawn_x = player_spawn[0]
        self.player.spawn_y = player_spawn[1]

        # Enemy management
        self._build_enemy_pool(level)
        self.enemies = []
        self._spawn_timer = 30
        self._spawn_idx = 0
        self._kills = 0
        self.bullets = []

        # Stats
        self.bfs_nodes_last = 0
        self.astar_nodes_last = 0
        self.greedy_nodes_last = 0
        self.minimax_stats = {}

    def _build_enemy_pool(self, level):
        """Build ordered list of enemy types"""
        pool = []
        if level == 3:
            pool = [TYPE_BOSS]
        else:
            level_cfg = LEVEL_CONFIG[level]
            enemy_count = level_cfg["enemy_count"]

            pool_config = LEVEL_POOL.get(level, [(TYPE_BASIC, enemy_count)])

            for tank_type, count in pool_config:
                adjusted_count = min(count, enemy_count - len(pool))
                pool.extend([tank_type] * adjusted_count)

            while len(pool) < enemy_count:
                pool.append(TYPE_BASIC)

        self._enemy_pool = pool
        self._pool_remaining = list(pool)

    @property
    def total_enemies(self):
        return len(self._enemy_pool)

    @property
    def remaining_in_pool(self):
        return len(self._pool_remaining)

    @property
    def enemies_remaining(self):
        return self.remaining_in_pool + len(self.enemies)

    def _try_spawn(self):
        """Spawn enemy if conditions allow"""
        if not self._pool_remaining:
            return
        if len(self.enemies) >= self.active_enemy_cap:
            return

        self._spawn_timer -= 1
        if self._spawn_timer > 0:
            return

        self._spawn_timer = self.spawn_delay

        if self.level == 3:
            # Boss level - spawn at fixed boss spawn position
            sx, sy = self.boss_spawn
            # Clear any existing enemies before spawning boss
            self.enemies = []
        else:
            spawn_pts = ENEMY_SPAWNS
            sp = spawn_pts[self._spawn_idx % len(spawn_pts)]
            self._spawn_idx += 1
            sx, sy = sp

        # Check distance to player (skip for boss level)
        if self.level != 3:
            px, py = self.player.x, self.player.y
            if abs(sx - px) + abs(sy - py) < SPAWN_CLEAR_RADIUS:
                self._spawn_timer = 15
                return

        # Check spawn point clear
        for t in self.enemies:
            if abs(t.x - sx) + abs(t.y - sy) < 2:
                self._spawn_timer = 15
                return

        tank_type = self._pool_remaining.pop(0)
        tank = make_tank(tank_type, sx, sy)

        if hasattr(tank, 'speed_mult'):
            tank.speed_mult = self.enemy_speed_mult

        self.enemies.append(tank)

    def tick_update(self):
        """Execute one full game-loop tick"""
        if self.game_over or self.paused:
            return

        self.tick += 1
        all_tanks = [self.player] + self.enemies

        # Update player
        if self.player.alive:
            self.player.update(self.grid, all_tanks, self.bullets,
                              self.player, self.notify_wall_destroyed)

        # Update enemies
        for enemy in list(self.enemies):
            if enemy.alive:
                enemy.update(self.grid, all_tanks, self.bullets,
                            self.player, self.notify_wall_destroyed)

        # Update bullets
        for bullet in list(self.bullets):
            if bullet.active:
                bullet.update(self.grid, all_tanks, self.bullets,
                             self.notify_wall_destroyed)

        # Remove dead objects
        self.bullets = [b for b in self.bullets if b.active]
        dead = [e for e in self.enemies if not e.alive]
        self._kills += len(dead)
        self.score += len(dead) * 100
        self.enemies = [e for e in self.enemies if e.alive]

        self._collect_stats()
        self._try_spawn()
        self._check_endgame()

    def _check_endgame(self):
        """Check win/lose conditions"""
        if not self.player.alive or self.player.lives <= 0:
            self.game_over = True
            self.won = False
            if self.menu_system:
                self.menu_system.show_game_over(won=False, message="You ran out of lives!")
            return

        ex, ey = EAGLE_POS
        if self.grid[ey][ex] != 5 or self.player._eagle_hit:
            self.game_over = True
            self.won = False
            if self.menu_system:
                self.menu_system.show_game_over(won=False, message="The Eagle was destroyed!")
            return

        if not self._pool_remaining and not self.enemies:
            self.game_over = True
            self.won = True

            if self.level < 3:
                if self.menu_system:
                    self.menu_system.show_level_clear(self.level + 1)
                if self.on_level_complete:
                    self.on_level_complete(self.level + 1, self.score)
            else:
                if self.menu_system:
                    self.menu_system.show_game_over(won=True,
                        message=f"Final Score: {self.score}")

    def _collect_stats(self):
        """Collect AI performance stats"""
        for e in self.enemies:
            if hasattr(e, "_bfs_nodes"):
                self.bfs_nodes_last = e._bfs_nodes
            if hasattr(e, "_astar_nodes"):
                self.astar_nodes_last = e._astar_nodes
            if hasattr(e, "_greedy_nodes"):
                self.greedy_nodes_last = e._greedy_nodes
            if hasattr(e, "_minimax_stats") and e._minimax_stats:
                self.minimax_stats = e._minimax_stats

    def notify_wall_destroyed(self, x, y):
        """Notify agents of map change"""
        for e in self.enemies:
            if hasattr(e, "_replan_timer"):
                e._replan_timer = 0
            if hasattr(e, "_astar_dir"):
                e._astar_dir = None

    @property
    def all_tanks(self):
        return [self.player] + self.enemies