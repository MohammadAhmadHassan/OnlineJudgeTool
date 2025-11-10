# -*- coding: utf-8 -*-
"""
Spectator Dashboard
Public-facing leaderboard and competition status display
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from data_manager import create_data_manager


class SpectatorDashboard:
    def __init__(self, root, data_manager):
        self.root = root
        self.data_manager = data_manager
        self.root.title("Spectator View - Live Competition")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        
        # Colors
        self.colors = {
            'primary': '#1e3a5f',
            'secondary': '#3498db',
            'success': '#27ae60',
            'gold': '#f39c12',
            'silver': '#95a5a6',
            'bronze': '#cd7f32',
            'light': '#ecf0f1',
            'dark': '#2c3e50',
            'background': '#ffffff',
            'card_bg': '#f8f9fa'
        }
        
        self.auto_refresh = True
        self.refresh_job = None
        
        # Configure styles
        self.configure_styles()
        
        # Create widgets
        self.create_widgets()
        
        # Start auto-refresh
        self.refresh_data()
    
    def configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame styles
        style.configure('TFrame', background=self.colors['background'])
        style.configure('Header.TFrame', background=self.colors['primary'])
        style.configure('Card.TFrame', background=self.colors['card_bg'],
                       relief='solid', borderwidth=1)
        
        # Label styles
        style.configure('TLabel', background=self.colors['background'],
                       foreground=self.colors['dark'], font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 20, 'bold'),
                       foreground='white', background=self.colors['primary'])
        style.configure('SubHeader.TLabel', font=('Segoe UI', 12),
                       foreground='white', background=self.colors['primary'])
        style.configure('Rank.TLabel', font=('Segoe UI', 16, 'bold'),
                       background=self.colors['card_bg'])
        style.configure('Name.TLabel', font=('Segoe UI', 14, 'bold'),
                       background=self.colors['card_bg'],
                       foreground=self.colors['dark'])
        style.configure('Stat.TLabel', font=('Segoe UI', 11),
                       background=self.colors['card_bg'])
        
        # Treeview styles
        style.configure('Treeview', font=('Segoe UI', 11), rowheight=40)
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'))
        style.map('Treeview', background=[('selected', self.colors['secondary'])])
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_container)
        
        # Use simpler frame layout instead of canvas for better performance
        scrollable_container = ttk.Frame(main_container)
        scrollable_container.pack(fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(scrollable_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Use Text widget as scrollable container (lighter than Canvas)
        self.scroll_container = tk.Text(scrollable_container, 
                                        wrap=tk.NONE,
                                        yscrollcommand=scrollbar.set,
                                        highlightthickness=0,
                                        borderwidth=0,
                                        state=tk.DISABLED)
        self.scroll_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.scroll_container.yview)
        
        # Create scrollable frame
        scrollable_frame = ttk.Frame(self.scroll_container)
        
        # Embed frame in text widget
        self.scroll_container.configure(state=tk.NORMAL)
        self.scroll_container.window_create("1.0", window=scrollable_frame)
        self.scroll_container.configure(state=tk.DISABLED)
        
        # Bind mousewheel
        def _on_mousewheel(event):
            self.scroll_container.yview_scroll(int(-1*(event.delta/120)), "units")
        self.scroll_container.bind("<MouseWheel>", _on_mousewheel)
        
        # Content area
        content = ttk.Frame(scrollable_frame)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Top 3 podium
        self.create_podium(content)
        
        # Leaderboard
        self.create_leaderboard(content)
        
        # Problem statistics
        self.create_problem_stats(content)
        
        # Footer
        self.create_footer(main_container)
    
    def create_header(self, parent):
        """Create header section"""
        header = ttk.Frame(parent, style='Header.TFrame')
        header.pack(fill=tk.X)
        
        header_content = ttk.Frame(header, style='Header.TFrame')
        header_content.pack(fill=tk.X, padx=30, pady=20)
        
        # Title
        title_frame = ttk.Frame(header_content, style='Header.TFrame')
        title_frame.pack(fill=tk.X)
        
        ttk.Label(title_frame, text="🏆 Live Competition Leaderboard",
                 style='Header.TLabel').pack()
        
        self.subtitle_var = tk.StringVar(value="Watch the competition unfold in real-time")
        ttk.Label(title_frame, textvariable=self.subtitle_var,
                 style='SubHeader.TLabel').pack(pady=(5, 0))
        
        # Auto-refresh indicator
        refresh_frame = ttk.Frame(header_content, style='Header.TFrame')
        refresh_frame.pack(side=tk.RIGHT, pady=(10, 0))
        
        self.refresh_indicator = ttk.Label(refresh_frame, text="🔄",
                                          foreground='white',
                                          background=self.colors['primary'],
                                          font=('Segoe UI', 10))
        self.refresh_indicator.pack(side=tk.LEFT, padx=5)
        
        self.last_update_var = tk.StringVar(value="Updating...")
        ttk.Label(refresh_frame, textvariable=self.last_update_var,
                 foreground='white', background=self.colors['primary'],
                 font=('Segoe UI', 9)).pack(side=tk.LEFT)
    
    def create_podium(self, parent):
        """Create top 3 podium display"""
        podium_frame = ttk.Frame(parent, style='Card.TFrame')
        podium_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(podium_frame, text="🏅 Top 3 Competitors",
                               font=('Segoe UI', 13, 'bold'),
                               foreground=self.colors['primary'],
                               background=self.colors['card_bg'])
        title_label.pack(pady=(15, 10))
        
        # Podium container
        podium_container = ttk.Frame(podium_frame, style='Card.TFrame')
        podium_container.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # Create 3 podium positions (2nd, 1st, 3rd layout)
        self.podium_cards = {}
        positions = [(1, '1st', self.colors['gold'], '130%', 1),
                    (0, '2nd', self.colors['silver'], '110%', 2),
                    (2, '3rd', self.colors['bronze'], '100%', 3)]
        
        for col, rank_text, color, height, rank_num in positions:
            card_frame, card_vars = self.create_podium_card(podium_container, rank_text, color, height)
            card_frame.grid(row=0, column=col, padx=10, sticky="nsew")
            self.podium_cards[rank_num] = card_vars
            podium_container.columnconfigure(col, weight=1)
    
    def create_podium_card(self, parent, rank_text, color, height):
        """Create a single podium card"""
        card = ttk.Frame(parent, style='Card.TFrame', relief='raised', borderwidth=2)
        
        # Rank
        rank_label = ttk.Label(card, text=rank_text, style='Rank.TLabel',
                              foreground=color)
        rank_label.pack(pady=(15, 5))
        
        # Name
        name_var = tk.StringVar(value="--")
        name_label = ttk.Label(card, textvariable=name_var, style='Name.TLabel')
        name_label.pack(pady=5)
        
        # Stats frame
        stats_frame = ttk.Frame(card, style='Card.TFrame')
        stats_frame.pack(pady=10)
        
        # Problems solved
        solved_frame = ttk.Frame(stats_frame, style='Card.TFrame')
        solved_frame.pack(pady=2)
        ttk.Label(solved_frame, text="✓ Solved: ", style='Stat.TLabel',
                 foreground='#6c757d').pack(side=tk.LEFT)
        solved_var = tk.StringVar(value="0")
        ttk.Label(solved_frame, textvariable=solved_var, style='Stat.TLabel',
                 foreground=self.colors['success'], font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)
        
        # Submissions
        sub_frame = ttk.Frame(stats_frame, style='Card.TFrame')
        sub_frame.pack(pady=2)
        ttk.Label(sub_frame, text="📝 Submissions: ", style='Stat.TLabel',
                 foreground='#6c757d').pack(side=tk.LEFT)
        sub_var = tk.StringVar(value="0")
        ttk.Label(sub_frame, textvariable=sub_var, style='Stat.TLabel',
                 foreground=self.colors['secondary']).pack(side=tk.LEFT)
        
        # Current problem
        current_frame = ttk.Frame(stats_frame, style='Card.TFrame')
        current_frame.pack(pady=2)
        ttk.Label(current_frame, text="📋 Working on: ", style='Stat.TLabel',
                 foreground='#6c757d').pack(side=tk.LEFT)
        current_var = tk.StringVar(value="--")
        ttk.Label(current_frame, textvariable=current_var, style='Stat.TLabel').pack(side=tk.LEFT)
        
        # Store variables for updating
        card_vars = {
            'name_var': name_var,
            'solved_var': solved_var,
            'sub_var': sub_var,
            'current_var': current_var
        }
        
        # Return both the frame and the variables dictionary
        return card, card_vars
    
    def create_leaderboard(self, parent):
        """Create full leaderboard table"""
        board_frame = ttk.Frame(parent, style='Card.TFrame')
        board_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Title
        title_label = ttk.Label(board_frame, text="📊 Full Leaderboard",
                               font=('Segoe UI', 13, 'bold'),
                               foreground=self.colors['primary'],
                               background=self.colors['card_bg'])
        title_label.pack(pady=(15, 10), padx=15, anchor=tk.W)
        
        # Treeview
        tree_frame = ttk.Frame(board_frame, style='Card.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        columns = ("rank", "name", "solved", "tests", "submissions", "current")
        self.leaderboard_tree = ttk.Treeview(tree_frame, columns=columns,
                                            show="headings", selectmode='none')
        
        # Configure columns
        self.leaderboard_tree.heading("rank", text="Rank")
        self.leaderboard_tree.heading("name", text="Competitor")
        self.leaderboard_tree.heading("solved", text="Solved")
        self.leaderboard_tree.heading("tests", text="Tests Passed")
        self.leaderboard_tree.heading("submissions", text="Submissions")
        self.leaderboard_tree.heading("current", text="Current Problem")
        
        self.leaderboard_tree.column("rank", width=70, stretch=False, anchor=tk.CENTER)
        self.leaderboard_tree.column("name", width=200, stretch=True)
        self.leaderboard_tree.column("solved", width=100, stretch=False, anchor=tk.CENTER)
        self.leaderboard_tree.column("tests", width=120, stretch=False, anchor=tk.CENTER)
        self.leaderboard_tree.column("submissions", width=120, stretch=False, anchor=tk.CENTER)
        self.leaderboard_tree.column("current", width=150, stretch=False, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                 command=self.leaderboard_tree.yview)
        self.leaderboard_tree.configure(yscrollcommand=scrollbar.set)
        
        self.leaderboard_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_problem_stats(self, parent):
        """Create problem statistics panel"""
        stats_frame = ttk.Frame(parent, style='Card.TFrame')
        stats_frame.pack(fill=tk.X)
        
        # Title
        title_label = ttk.Label(stats_frame, text="📈 Problem Statistics",
                               font=('Segoe UI', 13, 'bold'),
                               foreground=self.colors['primary'],
                               background=self.colors['card_bg'])
        title_label.pack(pady=(15, 10), padx=15, anchor=tk.W)
        
        # Stats grid
        self.stats_grid = ttk.Frame(stats_frame, style='Card.TFrame')
        self.stats_grid.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.problem_stat_labels = {}
    
    def create_footer(self, parent):
        """Create footer"""
        footer = ttk.Frame(parent)
        footer.pack(fill=tk.X, pady=5)
        
        self.competitor_count_var = tk.StringVar(value="0 competitors")
        ttk.Label(footer, textvariable=self.competitor_count_var,
                 font=('Segoe UI', 9), foreground='#6c757d').pack(side=tk.LEFT, padx=20)
        
        ttk.Label(footer, text="Auto-refreshes every 5 seconds",
                 font=('Segoe UI', 9, 'italic'), foreground='#6c757d').pack(side=tk.RIGHT, padx=20)
    
    def refresh_data(self):
        """Refresh all data"""
        try:
            leaderboard = self.data_manager.get_leaderboard()
            
            # Update podium (top 3)
            self.update_podium(leaderboard)
            
            # Update full leaderboard
            self.update_leaderboard(leaderboard)
            
            # Update problem statistics
            self.update_problem_statistics()
            
            # Update footer
            self.competitor_count_var.set(f"{len(leaderboard)} competitor{'s' if len(leaderboard) != 1 else ''}")
            
            # Update refresh time
            now = datetime.now().strftime('%H:%M:%S')
            self.last_update_var.set(f"Updated: {now}")
            
            # Animate refresh indicator
            self.animate_refresh_indicator()
            
        except Exception as e:
            self.last_update_var.set(f"Error: {str(e)}")
        
        # Schedule next refresh (increased from 5s to 10s for better performance)
        if self.auto_refresh:
            self.refresh_job = self.root.after(10000, self.refresh_data)
    
    def update_podium(self, leaderboard):
        """Update podium display with top 3"""
        # Clear all podium cards first
        for rank in [1, 2, 3]:
            if rank in self.podium_cards:
                self.podium_cards[rank]['name_var'].set("--")
                self.podium_cards[rank]['solved_var'].set("0")
                self.podium_cards[rank]['sub_var'].set("0")
                self.podium_cards[rank]['current_var'].set("--")
        
        # Update with current leaders
        for i, entry in enumerate(leaderboard[:3], 1):
            if i in self.podium_cards:
                card = self.podium_cards[i]
                card['name_var'].set(entry['name'])
                card['solved_var'].set(str(entry['problems_solved']))
                card['sub_var'].set(str(entry['total_submissions']))
                card['current_var'].set(f"Problem {entry['current_problem']}")
    
    def update_leaderboard(self, leaderboard):
        """Update full leaderboard"""
        # Cache existing items to avoid full recreation
        existing_items = {}
        for item in self.leaderboard_tree.get_children():
            values = self.leaderboard_tree.item(item)['values']
            if values and len(values) > 1:
                existing_items[values[1]] = (item, values)
        
        # Track which items to keep
        items_to_keep = set()
        
        # Add or update all competitors
        for i, entry in enumerate(leaderboard, 1):
            # Rank display
            if i == 1:
                rank = "🥇"
            elif i == 2:
                rank = "🥈"
            elif i == 3:
                rank = "🥉"
            else:
                rank = str(i)
            
            new_values = (
                rank,
                entry['name'],
                entry['problems_solved'],
                entry['total_tests_passed'],
                entry['total_submissions'],
                f"Problem {entry['current_problem']}"
            )
            
            # Update existing item or create new
            if entry['name'] in existing_items:
                item_id, old_values = existing_items[entry['name']]
                if old_values != new_values:
                    self.leaderboard_tree.item(item_id, values=new_values, tags=(f"rank{i}",))
                else:
                    # Still update tags in case ranking changed
                    self.leaderboard_tree.item(item_id, tags=(f"rank{i}",))
                items_to_keep.add(item_id)
            else:
                item_id = self.leaderboard_tree.insert("", tk.END, values=new_values, tags=(f"rank{i}",))
                items_to_keep.add(item_id)
        
        # Remove items no longer in the list
        for item in self.leaderboard_tree.get_children():
            if item not in items_to_keep:
                self.leaderboard_tree.delete(item)
        
        # Highlight top 3
        self.leaderboard_tree.tag_configure("rank1", background='#fff9e6')
        self.leaderboard_tree.tag_configure("rank2", background='#f0f0f0')
        self.leaderboard_tree.tag_configure("rank3", background='#ffe4cc')
    
    def update_problem_statistics(self):
        """Update problem statistics"""
        stats = self.data_manager.get_problem_statistics()
        
        # Cache existing stat items to avoid full recreation (performance optimization)
        if not hasattr(self, '_stat_items_cache'):
            self._stat_items_cache = {}
        
        if not stats:
            # Clear cache and show message
            for widget in self.stats_grid.winfo_children():
                widget.destroy()
            self._stat_items_cache = {}
            ttk.Label(self.stats_grid, text="No problem data available yet",
                     style='Stat.TLabel', foreground='#6c757d').pack(pady=10)
            return
        
        # Update existing items or create new ones
        current_problems = set(stats.keys())
        cached_problems = set(self._stat_items_cache.keys())
        
        # Remove old problems
        for problem_id in (cached_problems - current_problems):
            if problem_id in self._stat_items_cache:
                self._stat_items_cache[problem_id]['frame'].destroy()
                del self._stat_items_cache[problem_id]
        
        # Update or create stat items
        for i, (problem_id, problem_stats) in enumerate(sorted(stats.items())):
            solvers = problem_stats.get('total_solvers', 0)
            attempts = problem_stats.get('total_attempts', 0)
            solve_rate = (solvers / attempts * 100) if attempts > 0 else 0
            stats_text = f"✓ {solvers} solved | 📝 {attempts} attempts ({solve_rate:.0f}%)"
            
            if problem_id in self._stat_items_cache:
                # Update existing
                cached = self._stat_items_cache[problem_id]
                cached['stats_label'].configure(text=stats_text)
                # Update grid position if changed
                cached['frame'].grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="ew")
            else:
                # Create new
                stat_item = ttk.Frame(self.stats_grid, style='Card.TFrame')
                stat_item.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="ew")
                
                # Problem title
                title_label = ttk.Label(stat_item, text=f"Problem {problem_id}",
                         font=('Segoe UI', 10, 'bold'),
                         background=self.colors['card_bg'])
                title_label.pack(anchor=tk.W)
                
                # Stats
                stats_label = ttk.Label(stat_item, text=stats_text,
                         font=('Segoe UI', 9),
                         foreground='#6c757d',
                         background=self.colors['card_bg'])
                stats_label.pack(anchor=tk.W)
                
                self._stat_items_cache[problem_id] = {
                    'frame': stat_item,
                    'title_label': title_label,
                    'stats_label': stats_label
                }
            
            self.stats_grid.columnconfigure(i % 3, weight=1)
    
    def animate_refresh_indicator(self):
        """Animate the refresh indicator"""
        current = self.refresh_indicator.cget("text")
        indicators = ["🔄", "🔃", "🔄", "🔃"]
        next_idx = (indicators.index(current) + 1) % len(indicators)
        self.refresh_indicator.configure(text=indicators[next_idx])


def main():
    root = tk.Tk()
    data_manager = create_data_manager()
    app = SpectatorDashboard(root, data_manager)
    root.mainloop()


if __name__ == "__main__":
    main()
