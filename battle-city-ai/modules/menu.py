"""
menu.py — Interactive Main Menu System for Battle City
Features: Responsive layout, fullscreen support, hover effects, level selection
"""
import tkinter as tk
from modules.constants import (
    STATE_MENU, STATE_RULES, STATE_SETTINGS, STATE_PLAYING,
    STATE_GAME_OVER, STATE_PAUSED, STATE_LEVEL_CLEAR
)

# Custom state for level selection testing
STATE_LEVEL_SELECT = "level_select"

class MenuSystem:
    """Handles all menu UI and game state transitions with enhanced visuals"""
    def __init__(self, root, canvas, game_start_callback, level_change_callback):
        self.root = root
        self.canvas = canvas
        self.game_start_callback = game_start_callback
        self.level_change_callback = level_change_callback
        self.current_state = STATE_MENU
        self.sound_enabled = True
        self.fullscreen = False
        self.current_level = 1
        self.animation_id = None
        self.bg_offset = 0

        self.create_overlays()
        self.start_background_animation()
        self.bind_keys()
        self.show_state(STATE_MENU)

    def start_background_animation(self):
        """Start animated background movement"""
        def animate():
            self.bg_offset = (self.bg_offset + 1) % 100
            if self.current_state == STATE_MENU:
                self.update_main_menu_background()
            self.animation_id = self.root.after(50, animate)
        animate()

    def update_main_menu_background(self):
        """Update animated background for main menu"""
        if hasattr(self, 'main_menu') and self.main_menu.winfo_ismapped():
            self.canvas.delete("menu_bg")
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w <= 0 or h <= 0: return

            # Dark gradient background
            for i in range(20):
                y = i * (h // 20)
                color = f"#{10 + i:02x}{10 + i:02x}{20 + i:02x}"
                self.canvas.create_rectangle(0, y, w, y + h//20, fill=color, outline="", tags="menu_bg")

            # Animated grid lines
            spacing = 40
            offset = self.bg_offset % spacing
            for x in range(offset, w, spacing):
                self.canvas.create_line(x, 0, x, h, fill="#2a2a4a", width=1, tags="menu_bg", stipple="gray50")
            for y in range(offset, h, spacing):
                self.canvas.create_line(0, y, w, y, fill="#2a2a4a", width=1, tags="menu_bg", stipple="gray50")

            # Floating particles
            import random
            for _ in range(30):
                x = (self.bg_offset * 3 + _ * 37) % w
                y = (self.bg_offset * 2 + _ * 53) % h
                size = random.randint(2, 5)
                self.canvas.create_oval(x, y, x+size, y+size, fill="#ffc820", outline="", tags="menu_bg", stipple="gray75")

    def create_overlays(self):
        """Create all UI overlay frames with responsive, centered containers"""

        # ========== MAIN MENU ==========
        self.main_menu = tk.Frame(self.canvas, bg='#090912')
        self.main_menu.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.main_container = tk.Frame(self.main_menu, bg='#090912')
        self.main_container.place(relx=0.5, rely=0.5, anchor='center')

        # Title with enhanced styling
        title_frame = tk.Frame(self.main_container, bg='#090912')
        title_frame.pack(pady=50)
        
        # Shadow title effect
        tk.Label(title_frame, text="BATTLE CITY 1990", font=('Courier', 40, 'bold'), fg='#0a0a14', bg='#090912').pack()
        tk.Label(title_frame, text="BATTLE CITY 1990", font=('Courier', 40, 'bold'), fg='#ffc820', bg='#090912', relief='raised', bd=1).pack()
        
        # Subtitle with pulsing effect
        self.subtitle = tk.Label(self.main_container, text="⚡ AI Tank Combat ⚡", font=('Courier', 16, 'bold'), fg='#50c864', bg='#090912')
        self.subtitle.pack(pady=8)
        self.animate_subtitle()

        # Decorative separator
        sep_frame = tk.Frame(self.main_container, bg='#090912', height=3)
        sep_frame.pack(fill='x', pady=20, padx=40)
        tk.Label(sep_frame, text="─" * 50, font=('Courier', 10), fg='#ffc820', bg='#090912').pack()

        # Tank preview with enhanced styling
        preview_frame = tk.Frame(self.main_container, bg='#1a1a2e', highlightbackground='#ffc820', highlightthickness=3, relief='raised', bd=2)
        preview_frame.pack(pady=20, padx=30, fill='x', expand=False)
        
        # Header for tank preview
        preview_header = tk.Label(preview_frame, text="🤖 ENEMY AI TYPES 🤖", font=('Courier', 12, 'bold'), fg='#ffc820', bg='#1a1a2e')
        preview_header.pack(pady=10)
        
        tanks = [
            ("🟢", "Basic", "#50c864", "BFS"),
            ("🔵", "Fast", "#64b4ff", "Greedy"),
            ("🟣", "Armor", "#c864c8", "A*"),
            ("🔴", "Boss", "#ff3c3c", "Minimax"),
        ]
        
        tank_container = tk.Frame(preview_frame, bg='#1a1a2e')
        tank_container.pack(fill='x', expand=True)
        
        for i, (icon, name, color, desc) in enumerate(tanks):
            t_frame = tk.Frame(tank_container, bg='#0f0f1c', highlightbackground=color, highlightthickness=1, relief='solid', bd=1)
            t_frame.pack(side='left', expand=True, padx=5, pady=8, fill='both')
            tk.Label(t_frame, text=icon, font=('Arial', 28), bg='#0f0f1c').pack(pady=3)
            tk.Label(t_frame, text=name, font=('Courier', 11, 'bold'), fg=color, bg='#0f0f1c').pack()
            tk.Label(t_frame, text=desc, font=('Courier', 9), fg='#a0a0b0', bg='#0f0f1c').pack(pady=2)

        # Buttons with enhanced styling
        buttons_frame = tk.Frame(self.main_container, bg='#090912')
        buttons_frame.pack(pady=25, padx=20, fill='x')

        # Main play button (prominent)
        self.play_btn = self.create_styled_button(
            buttons_frame, "▶  PLAY GAME  ▶", 
            "#ffffff", "#ffff00", "#2a6a3a", 
            command=self.start_game, size=20, width=25,
            hover_bg="#4a9a5a"
        )
        self.play_btn.pack(pady=12, padx=20, fill='x', ipady=8)

        # Other buttons in a grid-like layout
        menu_buttons_frame = tk.Frame(self.main_container, bg='#090912')
        menu_buttons_frame.pack(pady=5, fill='x', padx=30)

        self.level_select_btn = self.create_styled_button(
            menu_buttons_frame, "🔬  LEVEL SELECT", 
            "#dcdce0", "#ffffff", "#3a5a7a",
            command=self.show_level_select, size=13, width=20,
            hover_bg="#5a7aaa"
        )
        self.level_select_btn.pack(pady=8, padx=15, side='left', fill='x', expand=True)

        self.rules_btn = self.create_styled_button(
            menu_buttons_frame, "📖  RULES",
            "#dcdce0", "#ffffff", "#3a5a7a",
            command=self.show_rules, size=13, width=18,
            hover_bg="#5a7aaa"
        )
        self.rules_btn.pack(pady=8, padx=15, side='left', fill='x', expand=True)

        more_buttons = tk.Frame(self.main_container, bg='#090912')
        more_buttons.pack(pady=5, fill='x', padx=30)

        self.settings_btn = self.create_styled_button(
            more_buttons, "⚙  SETTINGS",
            "#dcdce0", "#ffffff", "#5a3a7a",
            command=self.show_settings, size=13, width=20,
            hover_bg="#8a5aaa"
        )
        self.settings_btn.pack(pady=8, padx=15, side='left', fill='x', expand=True)

        self.quit_btn = self.create_styled_button(
            more_buttons, "🚪  QUIT",
            "#dcdce0", "#ffffff", "#7a3a3a",
            command=self.quit_game, size=13, width=18,
            hover_bg="#aa5a5a"
        )
        self.quit_btn.pack(pady=8, padx=15, side='left', fill='x', expand=True)

        # Footer
        footer_frame = tk.Frame(self.main_container, bg='#090912')
        footer_frame.pack(side='bottom', pady=15, padx=20, fill='x')
        tk.Label(footer_frame, text="Spring 2026 | AI Lab Project | v2.1", font=('Courier', 9), fg='#505070', bg='#090912').pack()
        tk.Label(footer_frame, text="Press WASD + SPACE to play | ESC to pause", font=('Courier', 8), fg='#606080', bg='#090912').pack()

        # ========== RULES MENU ==========
        self.rules_menu = tk.Frame(self.canvas, bg='#090912')
        self.rules_menu.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.rules_container = tk.Frame(self.rules_menu, bg='#090912')
        self.rules_container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(self.rules_container, text="📖  GAME RULES  📖", font=('Courier', 30, 'bold'), fg='#ffc820', bg='#090912').pack(pady=25)

        rules_frame = tk.Frame(self.rules_container, bg='#1a1a2e', highlightbackground='#ffc820', highlightthickness=3, relief='raised', bd=2)
        rules_frame.pack(fill='both', expand=True, padx=20, pady=15)

        rules_text = tk.Text(
            rules_frame, font=('Courier', 11), bg='#1a1a2e', fg='#dcdce0', 
            wrap='word', bd=0, relief='flat', highlightthickness=0, height=18, width=65
        )
        rules_text.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(rules_frame, command=rules_text.yview, bg='#0f0f1c', troughcolor='#1a1a2e')
        scrollbar.pack(side='right', fill='y', padx=5)
        rules_text.config(yscrollcommand=scrollbar.set)

        rules_content = """
╔══════════════════════════════════════════════════════════════╗
║                      🎮 CONTROLS                            ║
╠══════════════════════════════════════════════════════════════╣
║  WASD or Arrow Keys      →  Move Tank                       ║
║  SPACE or Mouse Click    →  Fire Cannon                     ║
║  P                       →  Pause Game                      ║
║  ESC                     →  Main Menu                       ║
╚══════════════════════════════════════════════════════════════╝
╔══════════════════════════════════════════════════════════════╗
║                   🤖 ENEMY AI TYPES                         ║
╠══════════════════════════════════════════════════════════════╣
║  🟢 BASIC TANK                                              ║
║     • BFS Pathfinding (Shortest hops)                       ║
║     • Simple Reflex Agent (IF-THEN rules)                   ║
║     • Shoots when player in line-of-sight                   ║
║                                                             ║
║  🔵 FAST TANK                                               ║
║     • Greedy Best-First Search                              ║
║     • Goal-Based Agent (rushes Eagle)                       ║
║     • Twice as fast as Basic tank                           ║
║                                                             ║
║  🟣 ARMOR TANK                                              ║
║     • A* Search with cost-aware navigation                  ║
║     • Model-Based Reflex Agent (tracks hits)                ║
║     • Retreats to cover when damaged (4 hits to destroy)    ║
║                                                             ║
║  🔴 BOSS TANK (Tank Commander)                              ║
║     • Minimax + Alpha-Beta Pruning                          ║
║     • Adversarial Agent (simulates player responses)        ║
║     • 3 phases with increasing difficulty                   ║
╚══════════════════════════════════════════════════════════════╝
╔══════════════════════════════════════════════════════════════╗
║                      🎯 OBJECTIVE                           ║
╠══════════════════════════════════════════════════════════════╣
║  • Protect your Eagle base (bottom center of map)           ║
║  • Destroy ALL enemy tanks to advance levels                ║
║  • Brick walls are DESTRUCTIBLE                             ║
║  • Steel walls are INDESTRUCTIBLE                           ║
║  • 10 Lives to complete all 3 levels                        ║
║  • 3 LEVELS: Brick Maze → Steel Fortress → Boss Arena      ║
╚══════════════════════════════════════════════════════════════╝
"""
        rules_text.insert('1.0', rules_content)
        rules_text.config(state='disabled')

        back_btn_frame = tk.Frame(self.rules_container, bg='#090912')
        back_btn_frame.pack(pady=15, fill='x', padx=20)
        self.create_styled_button(back_btn_frame, "←  BACK TO MENU", "#dcdce0", "#ffffff", "#5a5a7a", command=self.show_main_menu, size=14, width=20, hover_bg="#8a8aaa").pack()

        # ========== SETTINGS MENU ==========
        self.settings_menu = tk.Frame(self.canvas, bg='#090912')
        self.settings_menu.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.settings_container = tk.Frame(self.settings_menu, bg='#090912')
        self.settings_container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(self.settings_container, text="⚙  SETTINGS  ⚙", font=('Courier', 30, 'bold'), fg='#ffc820', bg='#090912').pack(pady=30)

        settings_box = tk.Frame(
            self.settings_container, bg='#1a1a2e', 
            highlightbackground='#ffc820', highlightthickness=3, 
            relief='raised', bd=2
        )
        settings_box.pack(fill='both', expand=True, padx=40, pady=25)

        # Settings items with better layout
        for label, btn_txt, cmd, icon in [
            ("🔊  SOUND EFFECTS", "ON", self.toggle_sound, "🔊"),
            ("🖥  FULLSCREEN MODE", "OFF", self.toggle_fullscreen, "🖥")
        ]:
            f = tk.Frame(settings_box, bg='#1a1a2e', relief='solid', bd=1, highlightbackground='#505070', highlightthickness=1)
            f.pack(fill='x', padx=20, pady=15, ipady=10)
            
            label_frame = tk.Frame(f, bg='#1a1a2e')
            label_frame.pack(side='left', fill='both', expand=True, padx=15)
            tk.Label(label_frame, text=label, font=('Courier', 14, 'bold'), fg='#dcdce0', bg='#1a1a2e').pack(anchor='w')
            
            btn = tk.Button(
                f, text=btn_txt, width=10, font=('Courier', 12, 'bold'), 
                bg='#505070' if btn_txt=="OFF" else '#50c864', fg='#ffffff', 
                activebackground='#9090b0' if btn_txt=="OFF" else '#80ff80',
                activeforeground='#ffffff',
                relief='raised', bd=2, padx=15, pady=8, cursor='hand2'
            )
            btn.config(command=cmd)
            btn.pack(side='right', padx=15)
            
            if "SOUND" in label:
                self.sound_toggle = btn
            if "FULL" in label:
                self.fs_toggle = btn

        tk.Frame(settings_box, bg='#1a1a2e', height=1).pack(fill='x', padx=20, pady=10)
        
        # Information text
        info_frame = tk.Frame(self.settings_container, bg='#090912')
        info_frame.pack(pady=20, fill='x', padx=40)
        tk.Label(
            info_frame, 
            text="💡 TIP: Fullscreen can improve visual quality on some systems.",
            font=('Courier', 10), fg='#8080a0', bg='#090912'
        ).pack()
        
        back_btn_frame = tk.Frame(self.settings_container, bg='#090912')
        back_btn_frame.pack(pady=15, fill='x', padx=20)
        self.create_styled_button(back_btn_frame, "←  BACK TO MENU", "#dcdce0", "#ffffff", "#5a5a7a", command=self.show_main_menu, size=14, width=20, hover_bg="#8a8aaa").pack()

        # ========== LEVEL SELECT MENU ==========
        self.level_select_menu = tk.Frame(self.canvas, bg='#090912')
        self.level_select_menu.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.level_select_container = tk.Frame(self.level_select_menu, bg='#090912')
        self.level_select_container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(
            self.level_select_container, 
            text="🔬  LEVEL SELECT (TEST MODE)  🔬", 
            font=('Courier', 26, 'bold'), fg='#ffc820', bg='#090912'
        ).pack(pady=30)
        
        tk.Label(
            self.level_select_container, 
            text="Select a level to test immediately.\nPlay Game always starts at Level 1.",
            font=('Courier', 11), fg='#8080a0', bg='#090912', justify='center'
        ).pack(pady=10)

        tk.Frame(self.level_select_container, height=2, bg='#ffc820').pack(fill='x', pady=15, padx=40)

        levels_frame = tk.Frame(self.level_select_container, bg='#090912')
        levels_frame.pack(pady=20, padx=30, fill='both', expand=True)

        level_info = [
            (1, "BRICK MAZE", "Start here! Basic enemies with BFS pathfinding.", "#50c864"),
            (2, "STEEL FORTRESS", "Harder! Armor tanks with A* and Fast tanks.", "#64b4ff"),
            (3, "BOSS ARENA", "Ultimate challenge! Face the Tank Commander!", "#ff3c3c"),
        ]

        for lvl, name, desc, color in level_info:
            lvl_card = tk.Frame(levels_frame, bg='#1a1a2e', highlightbackground=color, highlightthickness=2, relief='raised', bd=1)
            lvl_card.pack(fill='x', pady=10, padx=10, ipady=10)
            
            header_frame = tk.Frame(lvl_card, bg='#1a1a2e')
            header_frame.pack(fill='x', padx=15, pady=(10, 5))
            tk.Label(header_frame, text=f"LEVEL {lvl}: {name}", font=('Courier', 13, 'bold'), fg=color, bg='#1a1a2e').pack(anchor='w')
            
            tk.Label(lvl_card, text=desc, font=('Courier', 10), fg='#a0a0b0', bg='#1a1a2e').pack(anchor='w', padx=15, pady=(0, 10))
            
            btn_frame = tk.Frame(lvl_card, bg='#1a1a2e')
            btn_frame.pack(fill='x', padx=15, pady=10)
            self.create_styled_button(
                btn_frame, f"▶  START LEVEL {lvl}",
                "#ffffff", "#ffff00", color,
                command=lambda l=lvl: self.start_test_level(l), 
                size=12, width=25,
                hover_bg=self.lighten_color(color)
            ).pack(fill='x')

        back_btn_frame = tk.Frame(self.level_select_container, bg='#090912')
        back_btn_frame.pack(pady=15, fill='x', padx=20)
        self.create_styled_button(back_btn_frame, "←  BACK TO MENU", "#dcdce0", "#ffffff", "#5a5a7a", command=self.show_main_menu, size=14, width=20, hover_bg="#8a8aaa").pack()

        # ========== GAME OVER MENU ==========
        self.game_over_menu = tk.Frame(self.canvas, bg='#090912')
        self.game_over_menu.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.go_container = tk.Frame(self.game_over_menu, bg='#090912')
        self.go_container.place(relx=0.5, rely=0.5, anchor='center')

        self.go_title = tk.Label(
            self.go_container, text="GAME OVER", 
            font=('Courier', 36, 'bold'), fg='#ff3c3c', bg='#090912'
        )
        self.go_title.pack(pady=30)
        
        self.go_message = tk.Label(
            self.go_container, text="", 
            font=('Courier', 13), fg='#dcdce0', bg='#090912', 
            wraplength=400, justify='center'
        )
        self.go_message.pack(pady=20)
        
        go_buttons = tk.Frame(self.go_container, bg='#090912')
        go_buttons.pack(pady=15, fill='x', padx=30)
        
        self.retry_btn = self.create_styled_button(
            go_buttons, "🔄  RETRY LEVEL",
            "#ffffff", "#ffff00", "#2a6a3a",
            command=self.retry_level, size=14, width=20,
            hover_bg="#4a9a5a"
        )
        self.retry_btn.pack(pady=8, padx=15, fill='x')
        
        self.menu_btn_go = self.create_styled_button(
            go_buttons, "🏠  MAIN MENU",
            "#dcdce0", "#ffffff", "#5a5a7a",
            command=self.quit_to_menu, size=14, width=20,
            hover_bg="#8a8aaa"
        )
        self.menu_btn_go.pack(pady=8, padx=15, fill='x')

        # ========== PAUSE MENU ==========
        self.pause_menu = tk.Frame(self.canvas, bg='#090912')
        self.pause_menu.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.pause_container = tk.Frame(self.pause_menu, bg='#090912')
        self.pause_container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(
            self.pause_container, text="⏸  PAUSED  ⏸",
            font=('Courier', 32, 'bold'), fg='#ffc820', bg='#090912'
        ).pack(pady=40)
        
        tk.Label(
            self.pause_container, text="Press RESUME to continue your adventure",
            font=('Courier', 11), fg='#8080a0', bg='#090912'
        ).pack(pady=10)
        
        pause_buttons = tk.Frame(self.pause_container, bg='#090912')
        pause_buttons.pack(pady=15, padx=20, fill='x')
        
        self.create_styled_button(
            pause_buttons, "▶  RESUME",
            "#ffffff", "#ffff00", "#2a6a3a",
            command=self.resume_game, size=15, width=20,
            hover_bg="#4a9a5a"
        ).pack(pady=10, padx=15, fill='x')
        
        self.create_styled_button(
            pause_buttons, "🏠  MAIN MENU",
            "#dcdce0", "#ffffff", "#5a5a7a",
            command=self.quit_to_menu, size=14, width=20,
            hover_bg="#8a8aaa"
        ).pack(pady=10, padx=15, fill='x')

        # ========== LEVEL CLEAR MENU ==========
        self.level_clear_frame = tk.Frame(self.canvas, bg='#090912')
        self.level_clear_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.lc_container = tk.Frame(self.level_clear_frame, bg='#090912')
        self.lc_container.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(
            self.lc_container, text="✨  LEVEL CLEAR!  ✨",
            font=('Courier', 32, 'bold'), fg='#ffc820', bg='#090912'
        ).pack(pady=40)
        
        self.lc_message = tk.Label(
            self.lc_container, text="Loading next level...",
            font=('Courier', 14), fg='#50c864', bg='#090912'
        )
        self.lc_message.pack(pady=15)
        
        # Enhanced progress bar
        progress_frame = tk.Frame(self.lc_container, bg='#090912')
        progress_frame.pack(pady=20)
        
        tk.Label(progress_frame, text="Advancing to next level", font=('Courier', 10), fg='#8080a0', bg='#090912').pack()
        
        self.progress_bar = tk.Canvas(
            progress_frame, width=320, height=15, 
            bg='#1a1a2e', highlightthickness=2, 
            highlightbackground='#ffc820', relief='solid'
        )
        self.progress_bar.pack(pady=10)

        self.hide_all_overlays()
        self.show_state(STATE_MENU)

    def create_styled_button(self, parent, text, fg, fg_hover, bg, command, size=14, width=15, hover_bg=None):
        """Create a beautifully styled button with enhanced hover effects"""
        if hover_bg is None:
            hover_bg = self.lighten_color(bg)
        
        btn = tk.Button(
            parent, text=text, font=('Courier', size, 'bold'), 
            fg=fg, bg=bg, activeforeground=fg_hover, activebackground=hover_bg, 
            bd=0, padx=20, pady=10, cursor='hand2', command=command, width=width,
            relief='flat', overrelief='raised'
        )
        
        def on_enter(e):
            btn.config(fg=fg_hover, bg=hover_bg, relief='sunken')
        
        def on_leave(e):
            btn.config(fg=fg, bg=bg, relief='flat')
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def lighten_color(self, color):
        if color.startswith('#'):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            return f"#{min(255, r+30):02x}{min(255, g+30):02x}{min(255, b+30):02x}"
        return color

    def animate_subtitle(self):
        colors = ['#50c864', '#64b4ff', '#c864c8', '#ffc820']
        if hasattr(self, 'subtitle') and self.subtitle.winfo_exists():
            current = self.subtitle.cget('fg')
            idx = (colors.index(current) + 1) % len(colors) if current in colors else 0
            self.subtitle.config(fg=colors[idx])
            self.root.after(500, self.animate_subtitle)

    def hide_all_overlays(self):
        self.main_menu.place_forget()
        self.rules_menu.place_forget()
        self.settings_menu.place_forget()
        self.game_over_menu.place_forget()
        self.pause_menu.place_forget()
        self.level_clear_frame.place_forget()
        self.level_select_menu.place_forget()

    def show_state(self, state):
        self.current_state = state
        self.hide_all_overlays()
        if state == STATE_MENU: self.main_menu.place(relx=0, rely=0, relwidth=1, relheight=1)
        elif state == STATE_RULES: self.rules_menu.place(relx=0, rely=0, relwidth=1, relheight=1)
        elif state == STATE_SETTINGS: self.settings_menu.place(relx=0, rely=0, relwidth=1, relheight=1)
        elif state == STATE_GAME_OVER: self.game_over_menu.place(relx=0, rely=0, relwidth=1, relheight=1)
        elif state == STATE_PAUSED: self.pause_menu.place(relx=0, rely=0, relwidth=1, relheight=1)
        elif state == STATE_LEVEL_CLEAR:
            self.level_clear_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.animate_progress_bar()
        elif state == STATE_LEVEL_SELECT: self.level_select_menu.place(relx=0, rely=0, relwidth=1, relheight=1)

    def animate_progress_bar(self):
        """Animate the level clear progress bar with smooth fill"""
        if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
            self.progress_bar.delete("all")
            # Background border
            self.progress_bar.create_rectangle(0, 0, 320, 15, fill='#1a1a2e', outline='#ffc820', width=2, tags="bg")
            
            # Animated fill
            max_width = 316
            for i in range(0, 321, 5):
                def update(w=i):
                    if hasattr(self, 'progress_bar') and self.progress_bar.winfo_exists():
                        self.progress_bar.delete("progress")
                        fill_color = '#50c864'
                        self.progress_bar.create_rectangle(2, 2, 2 + min(w * (max_width / 320), max_width), 13, fill=fill_color, tags="progress")
                        self.progress_bar.update()
                self.root.after(i * 5, update)

    def show_main_menu(self): self.show_state(STATE_MENU)
    def show_rules(self): self.show_state(STATE_RULES)
    def show_settings(self): self.show_state(STATE_SETTINGS)
    def show_level_select(self): self.show_state(STATE_LEVEL_SELECT)

    def start_game(self):
        """Play button always starts Level 1"""
        self.current_level = 1
        self.show_state(STATE_PLAYING)
        if self.game_start_callback: self.game_start_callback(1)

    def start_test_level(self, level):
        """Test mode starts selected level"""
        self.current_level = level
        self.show_state(STATE_PLAYING)
        if self.game_start_callback: self.game_start_callback(level)

    def retry_level(self):
        self.show_state(STATE_PLAYING)
        if self.level_change_callback: self.level_change_callback(self.current_level)

    def resume_game(self): self.show_state(STATE_PLAYING)

    def quit_to_menu(self):
        self.current_level = 1
        self.show_state(STATE_MENU)
        if self.level_change_callback: self.level_change_callback(None)

    def quit_game(self):
        self.root.quit()
        self.root.destroy()

    def show_game_over(self, won=False, message=""):
        if won:
            self.go_title.config(text="VICTORY!", fg='#50c864')
            self.go_message.config(text=f"Congratulations!\n{message}\n\nYou are a true commander!")
        else:
            self.go_title.config(text="GAME OVER", fg='#ff3c3c')
            self.go_message.config(text=f"{message}\n\nBetter luck next time, Commander!")
        self.show_state(STATE_GAME_OVER)

    def show_level_clear(self, next_level):
        self.current_level = next_level
        self.lc_message.config(text=f"Loading Level {next_level}...\nGet ready for more action!")
        self.show_state(STATE_LEVEL_CLEAR)
        self.root.after(2000, lambda: self.advance_to_next_level(next_level))

    def advance_to_next_level(self, next_level):
        if next_level <= 3:
            self.show_state(STATE_PLAYING)
            if self.level_change_callback: self.level_change_callback(next_level)
        else:
            self.show_game_over(won=True, message="You have completed all 3 levels!")

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.sound_toggle.config(text="ON" if self.sound_enabled else "OFF", bg='#50c864' if self.sound_enabled else '#505070')

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            # Use 'zoomed' for Windows, set geometry for cross-platform
            try:
                self.root.state('zoomed')
            except:
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                self.root.geometry(f'{screen_w}x{screen_h}+0+0')
            self.root.attributes('-fullscreen', True)
        else:
            self.root.attributes('-fullscreen', False)
            self.root.state('normal')
        self.fs_toggle.config(text="ON" if self.fullscreen else "OFF", bg='#50c864' if self.fullscreen else '#505070')

    def bind_keys(self):
        self.root.bind('<Escape>', lambda e: self.handle_escape())

    def handle_escape(self):
        if self.current_state == STATE_PLAYING:
            self.show_state(STATE_PAUSED)
        elif self.current_state == STATE_PAUSED:
            self.show_state(STATE_PLAYING)
        elif self.current_state not in [STATE_MENU, STATE_RULES, STATE_SETTINGS, STATE_LEVEL_SELECT]:
            self.show_main_menu()

# Helper dict for level names in the UI
LEVEL_NAMES = {1: "BRICK MAZE", 2: "STEEL FORTRESS", 3: "BOSS ARENA"}