"""
main.py — Battle City AI Project Entry Point

Complete implementation with menu system, level progression,
responsive design, and improved enemy AI.
"""

import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from modules.constants import (
    GAME_TICK_MS, STATE_PLAYING,
    UP, DOWN, LEFT, RIGHT
)
from modules.game_state import GameState
from modules.renderer_tk import TkRenderer
from modules.menu import MenuSystem


class BattleCityGame:
    """Main game controller"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Battle City 1990 | Tank Battle")
        self.root.configure(bg='#090912')

        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Calculate responsive canvas size
        self.calc_canvas_size()

        # Create canvas
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height,
                                bg='#0f0f1c', highlightthickness=0)
        self.canvas.pack(expand=True, fill='both')

        # Center window
        self.center_window()

        # Initialize menu system
        self.menu = MenuSystem(
            self.root, self.canvas,
            game_start_callback=self.start_game,
            level_change_callback=self.change_level
        )

        # Game state
        self.game_state = None
        self.renderer = TkRenderer(self.canvas)
        self.keys_held = set()
        self.shoot_pending = False
        self.running = True

        # Bind events
        self.bind_events()

        # Start game loop
        self.root.after(100, self.game_loop)
        self.root.mainloop()

    def calc_canvas_size(self):
        """Calculate responsive canvas size based on screen"""
        target_aspect = 1072 / 832  # ~1.29 aspect ratio
        max_width = self.screen_width * 0.85
        max_height = self.screen_height * 0.85

        if max_width / max_height > target_aspect:
            self.canvas_height = int(max_height)
            self.canvas_width = int(self.canvas_height * target_aspect)
        else:
            self.canvas_width = int(max_width)
            self.canvas_height = int(self.canvas_width / target_aspect)

        # Ensure minimum size
        self.canvas_width = max(self.canvas_width, 800)
        self.canvas_height = max(self.canvas_height, 620)

    def center_window(self):
        """Center window on screen"""
        x = (self.screen_width - self.canvas_width) // 2
        y = (self.screen_height - self.canvas_height) // 2
        self.root.geometry(f"{self.canvas_width}x{self.canvas_height}+{x}+{y}")

    def bind_events(self):
        """Bind keyboard and mouse events"""
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.canvas.bind('<Button-1>', self.on_mouse_click)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_key_press(self, event):
        """Handle key press"""
        key = event.keysym.lower()

        # Global controls
        if key == 'backspace':
            if self.menu.current_state == STATE_PLAYING and self.game_state:
                self.game_state.paused = True
                self.menu.show_state('paused')
            elif self.menu.current_state == 'paused':
                if self.game_state:
                    self.game_state.paused = False
                self.menu.show_state(STATE_PLAYING)
            else:
                self.menu.show_main_menu()
            return

        if key == 'p':
            if self.game_state and self.menu.current_state == STATE_PLAYING:
                self.game_state.paused = not self.game_state.paused
                if self.game_state.paused:
                    self.menu.show_state('paused')
                else:
                    self.menu.show_state(STATE_PLAYING)
            return

        # Game controls
        if self.game_state and self.menu.current_state == STATE_PLAYING and not self.game_state.paused:
            if key in ['w', 'up']:
                self.keys_held.add('up')
            elif key in ['s', 'down']:
                self.keys_held.add('down')
            elif key in ['a', 'left']:
                self.keys_held.add('left')
            elif key in ['d', 'right']:
                self.keys_held.add('right')
            elif key == 'space':
                self.shoot_pending = True

    def on_key_release(self, event):
        """Handle key release"""
        key = event.keysym.lower()
        self.keys_held.discard('up')
        self.keys_held.discard('down')
        self.keys_held.discard('left')
        self.keys_held.discard('right')

    def on_mouse_click(self, event):
        """Handle mouse click for shooting"""
        if self.game_state and self.menu.current_state == STATE_PLAYING and not self.game_state.paused:
            self.shoot_pending = True

    def process_input(self):
        """Process player input"""
        if not self.game_state or self.menu.current_state != STATE_PLAYING or self.game_state.paused:
            return

        direction = None
        if 'up' in self.keys_held:
            direction = UP
        elif 'down' in self.keys_held:
            direction = DOWN
        elif 'left' in self.keys_held:
            direction = LEFT
        elif 'right' in self.keys_held:
            direction = RIGHT

        self.game_state.player.set_input(direction, self.shoot_pending)
        self.shoot_pending = False

    def start_game(self, level):
        """Start new game at specified level"""
        self.game_state = GameState(level, self.menu, self.on_level_complete)
        self.menu.show_state(STATE_PLAYING)

    def change_level(self, level):
        """Change to different level"""
        if level is None:
            self.game_state = None
        else:
            self.game_state = GameState(level, self.menu, self.on_level_complete)

    def on_level_complete(self, next_level, score):
        """Handle level completion"""
        self.start_game(next_level)

    def update(self):
        """Update game logic"""
        if self.game_state and self.menu.current_state == STATE_PLAYING:
            self.game_state.tick_update()

    def render(self):
        """Render the game"""
        if self.game_state and self.menu.current_state == STATE_PLAYING:
            self.renderer.draw(self.game_state)

    def game_loop(self):
        """Main game loop"""
        if self.running:
            self.process_input()
            self.update()
            self.render()
            self.root.after(GAME_TICK_MS, self.game_loop)

    def on_close(self):
        """Handle window close"""
        self.running = False
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    game = BattleCityGame()