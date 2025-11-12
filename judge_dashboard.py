# -*- coding: utf-8 -*-
"""
Judge Dashboard
Real-time monitoring of all competitors and their submissions
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
from datetime import datetime
from data_manager import create_data_manager


class JudgeDashboard:
    def __init__(self, root, data_manager):
        self.root = root
        self.data_manager = data_manager
        self.root.title("Judge Dashboard - Competition Monitor")
        # Start maximized to fit window
        self.root.state('zoomed')
        self.root.minsize(1200, 700)
        
        # Colors
        self.colors = {
            'primary': '#34495e',
            'secondary': '#3498db',
            'success': '#27ae60',
            'error': '#e74c3c',
            'warning': '#f39c12',
            'info': '#5dade2',
            'light': '#ecf0f1',
            'dark': '#2c3e50',
            'background': '#ffffff',
            'card_bg': '#f8f9fa'
        }
        
        self.selected_competitor = None
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
        style.configure('Header.TFrame', background=self.colors['dark'])
        style.configure('Card.TFrame', background=self.colors['card_bg'],
                       relief='solid', borderwidth=1)
        
        # Label styles
        style.configure('TLabel', background=self.colors['background'],
                       foreground=self.colors['dark'], font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'),
                       foreground='white', background=self.colors['dark'])
        style.configure('Card.TLabel', font=('Segoe UI', 11),
                       background=self.colors['card_bg'])
        style.configure('CardTitle.TLabel', font=('Segoe UI', 12, 'bold'),
                       foreground=self.colors['primary'], background=self.colors['card_bg'])
        style.configure('Stat.TLabel', font=('Segoe UI', 14, 'bold'),
                       background=self.colors['card_bg'])
        
        # Button styles
        style.configure('Refresh.TButton', font=('Segoe UI', 10),
                       padding=8)
        
        # Treeview styles
        style.configure('Treeview', font=('Segoe UI', 10), rowheight=30)
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        style.map('Treeview', background=[('selected', self.colors['info'])])
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_container)
        
        # Center frame to hold all content
        center_outer = ttk.Frame(main_container)
        center_outer.pack(fill=tk.BOTH, expand=True)
        
        # Create a centered column for content
        center_column = ttk.Frame(center_outer)
        center_column.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.90, relheight=0.95)
        
        # Use simpler frame layout instead of canvas for better performance
        scrollable_container = ttk.Frame(center_column)
        scrollable_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Vertical scrollbar
        scrollbar = ttk.Scrollbar(scrollable_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Use Text widget as scrollable container (lighter than Canvas)
        self.scroll_container = tk.Text(scrollable_container, 
                                        wrap=tk.NONE,
                                        yscrollcommand=scrollbar.set,
                                        highlightthickness=0,
                                        borderwidth=0,
                                        padx=0,
                                        pady=0,
                                        state=tk.DISABLED)
        self.scroll_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
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
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section: Statistics cards
        self.create_statistics_panel(content)
        
        # Main content: Split view
        paned = tk.PanedWindow(content, orient=tk.HORIZONTAL,
                              sashwidth=5, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left: Competitors list
        left_frame = ttk.Frame(paned)
        self.create_competitors_panel(left_frame)
        paned.add(left_frame, minsize=400)
        
        # Right: Selected competitor details
        right_frame = ttk.Frame(paned)
        self.create_details_panel(right_frame)
        paned.add(right_frame, minsize=600)
        
        # Bottom: Control panel
        self.create_control_panel(main_container)
    
    def create_header(self, parent):
        """Create header section"""
        header = ttk.Frame(parent, style='Header.TFrame')
        header.pack(fill=tk.X)
        
        header_content = ttk.Frame(header, style='Header.TFrame')
        header_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Title
        ttk.Label(header_content, text="👨‍⚖️ Judge Dashboard",
                 style='Header.TLabel').pack(side=tk.LEFT)
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        refresh_check = ttk.Checkbutton(header_content, 
                                       text="Auto-refresh",
                                       variable=self.auto_refresh_var,
                                       command=self.toggle_auto_refresh)
        refresh_check.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Manual refresh button
        refresh_btn = ttk.Button(header_content, text="🔄 Refresh Now",
                                style='Refresh.TButton',
                                command=self.refresh_data)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Last update time
        self.last_update_var = tk.StringVar(value="Last update: Never")
        ttk.Label(header_content, textvariable=self.last_update_var,
                 foreground='white', background=self.colors['dark'],
                 font=('Segoe UI', 9)).pack(side=tk.RIGHT, padx=10)
    
    def create_statistics_panel(self, parent):
        """Create statistics cards"""
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create stat cards
        self.total_competitors_var = tk.StringVar(value="0")
        self.active_competitors_var = tk.StringVar(value="0")
        self.total_submissions_var = tk.StringVar(value="0")
        self.problems_solved_var = tk.StringVar(value="0")
        
        cards = [
            ("Total Competitors", self.total_competitors_var, self.colors['info']),
            ("Active Now", self.active_competitors_var, self.colors['success']),
            ("Total Submissions", self.total_submissions_var, self.colors['secondary']),
            ("Problems Solved", self.problems_solved_var, self.colors['warning'])
        ]
        
        for i, (title, var, color) in enumerate(cards):
            card = self.create_stat_card(stats_frame, title, var, color)
            card.grid(row=0, column=i, padx=5, sticky="ew")
            stats_frame.columnconfigure(i, weight=1)
    
    def create_stat_card(self, parent, title, var, color):
        """Create a statistics card"""
        card = ttk.Frame(parent, style='Card.TFrame')
        
        content = ttk.Frame(card, style='Card.TFrame')
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(content, text=title, style='Card.TLabel').pack()
        
        value_label = ttk.Label(content, textvariable=var, style='Stat.TLabel')
        value_label.configure(foreground=color)
        value_label.pack(pady=(5, 0))
        
        return card
    
    def create_competitors_panel(self, parent):
        """Create competitors list panel"""
        parent.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="Competitors",
                 font=('Segoe UI', 12, 'bold'),
                 foreground=self.colors['primary']).pack(side=tk.LEFT)
        
        # Filter and Search box
        search_frame = ttk.Frame(title_frame)
        search_frame.pack(side=tk.RIGHT)
        
        # Global filter checkbox
        self.show_pending_only_var = tk.BooleanVar(value=False)
        pending_check = ttk.Checkbutton(search_frame, 
                                        text="Show only with pending reviews",
                                        variable=self.show_pending_only_var,
                                        command=self.filter_competitors)
        pending_check.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind('<KeyRelease>', self.filter_competitors)
        
        # Competitors treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("name", "pending", "current", "solved", "submissions", "status")
        self.competitors_tree = ttk.Treeview(tree_frame, columns=columns,
                                            show="headings", selectmode='browse')
        
        # Configure columns
        self.competitors_tree.heading("name", text="Competitor")
        self.competitors_tree.heading("pending", text="Pending Review")
        self.competitors_tree.heading("current", text="Current Problem")
        self.competitors_tree.heading("solved", text="Solved")
        self.competitors_tree.heading("submissions", text="Submissions")
        self.competitors_tree.heading("status", text="Status")
        
        self.competitors_tree.column("name", width=140, stretch=True)
        self.competitors_tree.column("pending", width=100, stretch=False, anchor=tk.CENTER)
        self.competitors_tree.column("current", width=110, stretch=False, anchor=tk.CENTER)
        self.competitors_tree.column("solved", width=70, stretch=False, anchor=tk.CENTER)
        self.competitors_tree.column("submissions", width=90, stretch=False, anchor=tk.CENTER)
        self.competitors_tree.column("status", width=90, stretch=False, anchor=tk.CENTER)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                   command=self.competitors_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL,
                                   command=self.competitors_tree.xview)
        self.competitors_tree.configure(yscrollcommand=v_scrollbar.set,
                                       xscrollcommand=h_scrollbar.set)
        
        self.competitors_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection
        self.competitors_tree.bind('<<TreeviewSelect>>', self.on_competitor_select)
    
    def create_details_panel(self, parent):
        """Create competitor details panel"""
        parent.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.detail_title_var = tk.StringVar(value="Select a competitor to view details")
        ttk.Label(title_frame, textvariable=self.detail_title_var,
                 font=('Segoe UI', 12, 'bold'),
                 foreground=self.colors['primary']).pack(side=tk.LEFT)
        
        # Notebook for different views
        self.details_notebook = ttk.Notebook(parent)
        self.details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Problem Status
        problems_tab = ttk.Frame(self.details_notebook)
        self.create_problems_view(problems_tab)
        self.details_notebook.add(problems_tab, text="Problem Status")
        
        # Tab 2: Submission History
        history_tab = ttk.Frame(self.details_notebook)
        self.create_history_view(history_tab)
        self.details_notebook.add(history_tab, text="Submission History")
        
        # Tab 3: Code View
        code_tab = ttk.Frame(self.details_notebook)
        self.create_code_view(code_tab)
        self.details_notebook.add(code_tab, text="Code View")
    
    def create_problems_view(self, parent):
        """Create problems status view"""
        # Filter toolbar
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=(5, 10), padx=10)
        
        ttk.Label(filter_frame, text="Filter:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        self.problem_filter_var = tk.StringVar(value="All")
        filters = [
            ("All Problems", "All"),
            ("Needs Review (Pending)", "Pending"),
            ("Approved Only", "Approved"),
            ("Rejected Only", "Rejected"),
            ("Solved (All Passed)", "Solved")
        ]
        
        for label, value in filters:
            rb = ttk.Radiobutton(filter_frame, text=label, variable=self.problem_filter_var,
                                value=value, command=self.apply_problem_filter)
            rb.pack(side=tk.LEFT, padx=5)
        
        # Create frame for tree and scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Problems treeview
        columns = ("problem", "status", "approval", "attempts", "tests_passed", "last_submission")
        self.problems_tree = ttk.Treeview(tree_frame, columns=columns,
                                         show="headings", selectmode='browse')
        
        self.problems_tree.heading("problem", text="Problem")
        self.problems_tree.heading("status", text="Status")
        self.problems_tree.heading("approval", text="Judge Status")
        self.problems_tree.heading("attempts", text="Attempts")
        self.problems_tree.heading("tests_passed", text="Tests Passed")
        self.problems_tree.heading("last_submission", text="Last Submission")
        
        self.problems_tree.column("problem", width=120, stretch=True)
        self.problems_tree.column("status", width=100, stretch=False, anchor=tk.CENTER)
        self.problems_tree.column("approval", width=100, stretch=False, anchor=tk.CENTER)
        self.problems_tree.column("attempts", width=70, stretch=False, anchor=tk.CENTER)
        self.problems_tree.column("tests_passed", width=100, stretch=False, anchor=tk.CENTER)
        self.problems_tree.column("last_submission", width=120, stretch=False)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                   command=self.problems_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL,
                                   command=self.problems_tree.xview)
        self.problems_tree.configure(yscrollcommand=v_scrollbar.set,
                                    xscrollcommand=h_scrollbar.set)
        
        self.problems_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection for code view
        self.problems_tree.bind('<<TreeviewSelect>>', self.on_problem_select)
    
    def create_history_view(self, parent):
        """Create submission history view"""
        # Create frame for tree and scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("time", "problem", "status", "tests")
        self.history_tree = ttk.Treeview(tree_frame, columns=columns,
                                        show="headings", selectmode='browse')
        
        self.history_tree.heading("time", text="Submission Time")
        self.history_tree.heading("problem", text="Problem")
        self.history_tree.heading("status", text="Status")
        self.history_tree.heading("tests", text="Tests Passed")
        
        self.history_tree.column("time", width=180, stretch=True)
        self.history_tree.column("problem", width=150, stretch=False)
        self.history_tree.column("status", width=120, stretch=False, anchor=tk.CENTER)
        self.history_tree.column("tests", width=120, stretch=False, anchor=tk.CENTER)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                   command=self.history_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL,
                                   command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=v_scrollbar.set,
                                   xscrollcommand=h_scrollbar.set)
        
        self.history_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
    
    def create_code_view(self, parent):
        """Create code viewer"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        self.code_problem_var = tk.StringVar(value="Select a problem to view code")
        ttk.Label(toolbar, textvariable=self.code_problem_var,
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        # Approval buttons (fixed width to prevent shifting)
        approval_frame = ttk.Frame(toolbar)
        approval_frame.pack(side=tk.RIGHT)
        
        self.approve_btn = tk.Button(approval_frame, text="Approve",
                                     font=('Segoe UI', 9),
                                     bg='#27ae60', fg='white',
                                     cursor='hand2',
                                     width=10,
                                     command=self.approve_solution)
        self.approve_btn.pack(side=tk.LEFT, padx=3)
        self.approve_btn.config(state=tk.DISABLED)
        
        self.reject_btn = tk.Button(approval_frame, text="Reject",
                                    font=('Segoe UI', 9),
                                    bg='#e74c3c', fg='white',
                                    cursor='hand2',
                                    width=10,
                                    command=self.reject_solution)
        self.reject_btn.pack(side=tk.LEFT, padx=3)
        self.reject_btn.config(state=tk.DISABLED)
        
        # Approval status indicator (fixed width)
        self.approval_status_var = tk.StringVar(value="")
        self.approval_status_label = ttk.Label(approval_frame, 
                                               textvariable=self.approval_status_var,
                                               font=('Segoe UI', 9, 'bold'),
                                               width=15)
        self.approval_status_label.pack(side=tk.LEFT, padx=10)
        
        # Code viewer
        self.code_viewer = scrolledtext.ScrolledText(parent, wrap=tk.NONE,
                                                     font=('Consolas', 10),
                                                     padx=10, pady=10,
                                                     bg='#f8f9fa')
        self.code_viewer.pack(fill=tk.BOTH, expand=True)
        self.code_viewer.config(state=tk.DISABLED)
    
    def create_control_panel(self, parent):
        """Create control panel"""
        control = ttk.Frame(parent)
        control.pack(fill=tk.X, padx=10, pady=10)
        
        # Export button
        export_btn = ttk.Button(control, text="📊 Export Report",
                               command=self.export_report)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Reset button
        reset_btn = ttk.Button(control, text="🔄 Reset Competition",
                              command=self.reset_competition)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(control, textvariable=self.status_var,
                 relief=tk.SUNKEN, padding=5).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))
    
    def refresh_data(self):
        """Refresh all data from data manager"""
        try:
            # Update statistics
            competitors = self.data_manager.get_all_competitors()
            leaderboard = self.data_manager.get_leaderboard()
            
            self.total_competitors_var.set(str(len(competitors)))
            
            # Count active competitors (activity in last 5 minutes)
            now = datetime.now()
            active_count = 0
            for comp in competitors.values():
                if comp.get('last_activity'):
                    try:
                        last_activity = datetime.fromisoformat(comp['last_activity'])
                        if (now - last_activity).seconds < 300:
                            active_count += 1
                    except:
                        pass
            self.active_competitors_var.set(str(active_count))
            
            # Total submissions and problems solved
            total_submissions = sum(entry['total_submissions'] for entry in leaderboard)
            total_solved = sum(entry['problems_solved'] for entry in leaderboard)
            self.total_submissions_var.set(str(total_submissions))
            self.problems_solved_var.set(str(total_solved))
            
            # Update competitors tree
            self.update_competitors_tree(leaderboard)
            
            # Update selected competitor if any
            if self.selected_competitor:
                self.update_competitor_details(self.selected_competitor)
            
            # Update last refresh time
            self.last_update_var.set(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
            self.status_var.set(f"✓ Refreshed - {len(competitors)} competitors tracked")
            
        except Exception as e:
            self.status_var.set(f"✗ Error: {str(e)}")
        
        # Schedule next refresh (increased from 5s to 10s for better performance)
        if self.auto_refresh_var.get():
            self.refresh_job = self.root.after(10000, self.refresh_data)
    
    def update_competitors_tree(self, leaderboard):
        """Update the competitors treeview"""
        # Get search filter
        search_text = self.search_entry.get().lower()
        
        # Cache current values to avoid unnecessary updates
        existing_items = {}
        for item in self.competitors_tree.get_children():
            values = self.competitors_tree.item(item)['values']
            if values:
                existing_items[values[0]] = (item, values)
        
        # Track which items to keep
        items_to_keep = set()
        
        # Add or update competitors
        for entry in leaderboard:
            if search_text and search_text not in entry['name'].lower():
                continue
            
            # Determine status
            try:
                last_activity = datetime.fromisoformat(entry['last_activity'])
                now = datetime.now()
                if (now - last_activity).seconds < 300:
                    status = "🟢 Active"
                    status_tag = "active"
                elif (now - last_activity).seconds < 1800:
                    status = "🟡 Idle"
                    status_tag = "idle"
                else:
                    status = "⚪ Inactive"
                    status_tag = "inactive"
            except:
                status = "⚪ Unknown"
                status_tag = "inactive"
            
            # Format pending count with highlighting
            pending_count = entry.get('pending_count', 0)
            if pending_count > 0:
                pending_display = f"⚠ {pending_count}"
                pending_tag = "has_pending"
            else:
                pending_display = "0"
                pending_tag = status_tag
            
            new_values = (
                entry['name'],
                pending_display,
                f"Problem {entry['current_problem']}",
                entry['problems_solved'],
                entry['total_submissions'],
                status
            )
            
            # Update existing item or create new
            if entry['name'] in existing_items:
                item_id, old_values = existing_items[entry['name']]
                if old_values != new_values:
                    self.competitors_tree.item(item_id, values=new_values, tags=(status_tag, pending_tag))
                items_to_keep.add(item_id)
            else:
                item_id = self.competitors_tree.insert("", tk.END, values=new_values, tags=(status_tag, pending_tag))
                items_to_keep.add(item_id)
        
        # Remove items no longer in the list
        for item in self.competitors_tree.get_children():
            if item not in items_to_keep:
                self.competitors_tree.delete(item)
        
        # Configure tags
        self.competitors_tree.tag_configure("active", foreground=self.colors['success'])
        self.competitors_tree.tag_configure("idle", foreground=self.colors['warning'])
        self.competitors_tree.tag_configure("inactive", foreground='#6c757d')
        self.competitors_tree.tag_configure("has_pending", foreground='#f39c12')
    
    def filter_competitors(self, event=None):
        """Filter competitors based on search and pending filter"""
        all_competitors = self.data_manager.get_all_competitors()
        leaderboard = []
        
        # Build leaderboard with pending count
        for name, competitor_data in all_competitors.items():
            # Count pending problems (solved but not reviewed)
            pending_count = 0
            for problem_id, problem_data in competitor_data.get('problems', {}).items():
                best_result = problem_data.get('best_result', {})
                judge_approval = problem_data.get('judge_approval')
                if best_result and best_result.get('all_passed', False) and not judge_approval:
                    pending_count += 1
            
            # Apply pending filter
            if self.show_pending_only_var.get() and pending_count == 0:
                continue
            
            # Apply search filter
            search_text = self.search_entry.get().lower()
            if search_text and search_text not in name.lower():
                continue
            
            # Count solved problems
            solved_count = sum(1 for p in competitor_data.get('problems', {}).values()
                             if p.get('best_result', {}).get('all_passed', False))
            
            # Count total submissions
            total_subs = sum(len(p.get('submissions', [])) 
                           for p in competitor_data.get('problems', {}).values())
            
            leaderboard.append({
                'name': name,
                'problems_solved': solved_count,
                'total_submissions': total_subs,
                'current_problem': competitor_data.get('current_problem', 1),
                'last_activity': competitor_data.get('last_activity', ''),
                'pending_count': pending_count
            })
        
        self.update_competitors_tree(leaderboard)
    
    def apply_problem_filter(self):
        """Apply filter to problems tree view"""
        filter_value = self.problem_filter_var.get()
        
        # Show/hide items based on filter
        for item in self.problems_tree.get_children():
            tags = self.problems_tree.item(item)['tags']
            show_item = False
            
            if filter_value == "All":
                show_item = True
            elif filter_value == "Pending":
                # Show only solved problems that are pending review
                show_item = "solved" in tags and "pending" in tags
            elif filter_value == "Approved":
                show_item = "approved" in tags
            elif filter_value == "Rejected":
                show_item = "rejected" in tags
            elif filter_value == "Solved":
                show_item = "solved" in tags
            
            # Detach or reattach item
            if show_item:
                # Make sure item is visible (reattach if needed)
                if item not in self.problems_tree.get_children():
                    values = self.problems_tree.item(item)['values']
                    tags = self.problems_tree.item(item)['tags']
                    self.problems_tree.reattach(item, '', 'end')
            else:
                # Hide item by detaching
                self.problems_tree.detach(item)
    
    def on_competitor_select(self, event):
        """Handle competitor selection"""
        selection = self.competitors_tree.selection()
        if not selection:
            return
        
        item = self.competitors_tree.item(selection[0])
        competitor_name = item['values'][0]
        
        self.selected_competitor = competitor_name
        self.update_competitor_details(competitor_name)
    
    def update_competitor_details(self, competitor_name):
        """Update the details panel for selected competitor"""
        self.detail_title_var.set(f"📊 {competitor_name}'s Details")
        
        competitor_data = self.data_manager.get_competitor_data(competitor_name)
        if not competitor_data:
            return
        
        # Update problems view
        self.update_problems_view(competitor_data)
        
        # Update history view
        self.update_history_view(competitor_data)
        
        # Automatically show code for the first problem with submissions
        self.auto_show_first_code(competitor_data)
    
    def update_problems_view(self, competitor_data):
        """Update problems status view"""
        # Clear existing
        for item in self.problems_tree.get_children():
            self.problems_tree.delete(item)
        
        # Add problems
        for problem_id, problem_data in competitor_data.get('problems', {}).items():
            best_result = problem_data.get('best_result', {})
            submissions = problem_data.get('submissions', [])
            
            # Determine status
            if best_result and best_result.get('all_passed'):
                status = "✓ Solved"
                status_tag = "solved"
            elif submissions:
                status = "◐ Attempted"
                status_tag = "attempted"
            else:
                status = "○ Not Started"
                status_tag = "not_started"
            
            # Judge approval status
            judge_approval = problem_data.get('judge_approval')
            if judge_approval == 'approved':
                approval_status = "✓ Approved"
                approval_tag = "approved"
            elif judge_approval == 'rejected':
                approval_status = "✗ Rejected"
                approval_tag = "rejected"
            else:
                approval_status = "⏳ Pending"
                approval_tag = "pending"
            
            # Tests passed
            if best_result:
                tests_passed = f"{best_result.get('passed_tests', 0)}/{best_result.get('total_tests', 0)}"
            else:
                tests_passed = "0/0"
            
            # Last submission time
            if submissions:
                last_sub = submissions[-1].get('submitted_at', '')
                try:
                    dt = datetime.fromisoformat(last_sub)
                    last_sub = dt.strftime('%H:%M:%S')
                except:
                    pass
            else:
                last_sub = "Never"
            
            self.problems_tree.insert("", tk.END, values=(
                f"Problem {problem_id}",
                status,
                approval_status,
                len(submissions),
                tests_passed,
                last_sub
            ), tags=(status_tag, approval_tag, problem_id))
        
        # Configure tags
        self.problems_tree.tag_configure("solved", foreground=self.colors['success'])
        self.problems_tree.tag_configure("attempted", foreground=self.colors['warning'])
        self.problems_tree.tag_configure("not_started", foreground='#6c757d')
        self.problems_tree.tag_configure("approved", foreground='#27ae60')
        self.problems_tree.tag_configure("rejected", foreground='#e74c3c')
        self.problems_tree.tag_configure("pending", foreground='#f39c12')
        
        # Apply current filter
        self.apply_problem_filter()
    
    def update_history_view(self, competitor_data):
        """Update submission history view"""
        # Clear existing
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Collect all submissions
        all_submissions = []
        for problem_id, problem_data in competitor_data.get('problems', {}).items():
            for submission in problem_data.get('submissions', []):
                all_submissions.append({
                    'problem_id': problem_id,
                    'submission': submission
                })
        
        # Sort by time (newest first)
        all_submissions.sort(key=lambda x: x['submission'].get('submitted_at', ''),
                            reverse=True)
        
        # Add to tree
        for entry in all_submissions:
            problem_id = entry['problem_id']
            submission = entry['submission']
            
            # Format time
            time_str = submission.get('submitted_at', '')
            try:
                dt = datetime.fromisoformat(time_str)
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
            
            # Status
            if submission.get('all_passed'):
                status = "✓ All Passed"
                status_tag = "passed"
            else:
                status = "✗ Failed"
                status_tag = "failed"
            
            tests_passed = f"{submission.get('passed_tests', 0)}/{submission.get('total_tests', 0)}"
            
            self.history_tree.insert("", tk.END, values=(
                time_str,
                f"Problem {problem_id}",
                status,
                tests_passed
            ), tags=(status_tag,))
        
        # Configure tags
        self.history_tree.tag_configure("passed", foreground=self.colors['success'])
        self.history_tree.tag_configure("failed", foreground=self.colors['error'])
    
    def auto_show_first_code(self, competitor_data):
        """Automatically show code for the first problem with submissions"""
        problems = competitor_data.get('problems', {})
        
        # Find first problem with code
        for problem_id in sorted(problems.keys(), key=lambda x: int(x) if x.isdigit() else 0):
            problem_data = problems.get(problem_id, {})
            best_result = problem_data.get('best_result', {})
            
            if best_result and best_result.get('code'):
                code = best_result['code']
                self.code_problem_var.set(f"Problem {problem_id} - Best Result")
                
                self.code_viewer.config(state=tk.NORMAL)
                self.code_viewer.delete(1.0, tk.END)
                self.code_viewer.insert(tk.END, code)
                self.code_viewer.config(state=tk.DISABLED)
                return
        
        # No code found
        self.code_problem_var.set("No code submitted yet")
        self.code_viewer.config(state=tk.NORMAL)
        self.code_viewer.delete(1.0, tk.END)
        self.code_viewer.insert(tk.END, "Select a problem from the 'Problem Status' tab to view submitted code.")
        self.code_viewer.config(state=tk.DISABLED)
    
    def on_problem_select(self, event):
        """Handle problem selection to show code"""
        selection = self.problems_tree.selection()
        if not selection or not self.selected_competitor:
            print(f"[DEBUG] on_problem_select: selection={selection}, competitor={self.selected_competitor}")
            return
        
        item = self.problems_tree.item(selection[0])
        tags = item['tags']
        print(f"[DEBUG] Problem selected - tags: {tags}, types: {[type(t).__name__ for t in tags]}")
        
        # Extract problem_id from tags
        problem_id = None
        for tag in tags:
            # Convert to string first in case it's already an int
            tag_str = str(tag)
            if tag_str.isdigit():
                problem_id = int(tag_str)
                break
        
        print(f"[DEBUG] Extracted problem_id: {problem_id}")
        
        if not problem_id:
            return
        
        # Get competitor data
        competitor_data = self.data_manager.get_competitor_data(self.selected_competitor)
        if not competitor_data:
            self.code_problem_var.set(f"Problem {problem_id} - Error loading data")
            self.code_viewer.config(state=tk.NORMAL)
            self.code_viewer.delete(1.0, tk.END)
            self.code_viewer.insert(tk.END, "Error: Could not load competitor data from database.")
            self.code_viewer.config(state=tk.DISABLED)
            return
        
        # Get code for this problem - try both string and int keys
        problems = competitor_data.get('problems', {})
        problem_data = problems.get(str(problem_id), problems.get(int(problem_id), {}))
        
        # Try to get code from best_result first, then from latest submission
        code = None
        code_source = "No submission"
        
        # Check best_result
        best_result = problem_data.get('best_result', {})
        if best_result and 'code' in best_result and best_result['code']:
            code = best_result['code']
            code_source = f"Best Result ({best_result.get('passed_tests', 0)}/{best_result.get('total_tests', 0)} tests passed)"
        
        # If no code in best_result, check latest submission
        if not code:
            submissions = problem_data.get('submissions', [])
            if submissions:
                latest = submissions[-1]
                if 'code' in latest and latest['code']:
                    code = latest['code']
                    code_source = f"Latest Submission ({latest.get('passed_tests', 0)}/{latest.get('total_tests', 0)} tests passed)"
        
        if code:
            self.code_problem_var.set(f"Problem {problem_id} - {code_source}")
            
            self.code_viewer.config(state=tk.NORMAL)
            self.code_viewer.delete(1.0, tk.END)
            self.code_viewer.insert(tk.END, code)
            self.code_viewer.config(state=tk.DISABLED)
            
            # Enable approval buttons and store current problem
            self.current_problem_id = problem_id
            self.approve_btn.config(state=tk.NORMAL)
            self.reject_btn.config(state=tk.NORMAL)
            print(f"[DEBUG] Enabled approval buttons for problem {problem_id}")
            
            # Auto-switch to Code View tab to show the buttons
            self.details_notebook.select(2)  # Index 2 = "Code View" tab
            
            # Show current approval status
            approval_status = problem_data.get('judge_approval')
            print(f"[DEBUG] Current approval status: {approval_status}")
            if approval_status == 'approved':
                self.approval_status_var.set("✓ Approved")
                self.approval_status_label.config(foreground='#27ae60')
            elif approval_status == 'rejected':
                self.approval_status_var.set("✗ Rejected")
                self.approval_status_label.config(foreground='#e74c3c')
            else:
                self.approval_status_var.set("⏳ Pending Review")
                self.approval_status_label.config(foreground='#f39c12')
        else:
            # Debug: Show what we actually found
            debug_info = f"No code submitted yet.\n\n"
            debug_info += f"Debug Info:\n"
            debug_info += f"- Problem ID: {problem_id}\n"
            debug_info += f"- Problems in data: {list(problems.keys())}\n"
            debug_info += f"- Problem data exists: {bool(problem_data)}\n"
            debug_info += f"- Best result exists: {bool(best_result)}\n"
            debug_info += f"- Submissions count: {len(problem_data.get('submissions', []))}\n"
            
            self.code_problem_var.set(f"Problem {problem_id} - No code submitted")
            self.code_viewer.config(state=tk.NORMAL)
            self.code_viewer.delete(1.0, tk.END)
            self.code_viewer.insert(tk.END, debug_info)
            self.code_viewer.config(state=tk.DISABLED)
            
            # Disable approval buttons
            self.approve_btn.config(state=tk.DISABLED)
            self.reject_btn.config(state=tk.DISABLED)
            self.approval_status_var.set("")
    
    def approve_solution(self):
        """Approve the current solution"""
        if not self.selected_competitor or not hasattr(self, 'current_problem_id'):
            print(f"[WARNING] Cannot approve: selected_competitor={self.selected_competitor}, has problem_id={hasattr(self, 'current_problem_id')}")
            return
        
        try:
            print(f"[INFO] Approving solution for {self.selected_competitor} - Problem {self.current_problem_id}")
            
            # Set approval status
            self.data_manager.set_judge_approval(
                self.selected_competitor,
                self.current_problem_id,
                'approved'
            )
            
            # Update UI
            self.approval_status_var.set("✓ Approved")
            self.approval_status_label.config(foreground='#27ae60')
            
            # Refresh to update rankings
            self.refresh_data()
            
            messagebox.showinfo("Approved", 
                f"Solution approved for {self.selected_competitor} - Problem {self.current_problem_id}")
        except Exception as e:
            print(f"[ERROR] Failed to approve: {str(e)}")
            messagebox.showerror("Error", f"Failed to approve solution:\n{str(e)}")
    
    def reject_solution(self):
        """Reject the current solution"""
        if not self.selected_competitor or not hasattr(self, 'current_problem_id'):
            print(f"[WARNING] Cannot reject: selected_competitor={self.selected_competitor}, has problem_id={hasattr(self, 'current_problem_id')}")
            return
        
        try:
            print(f"[INFO] Rejecting solution for {self.selected_competitor} - Problem {self.current_problem_id}")
            
            # Set rejection status
            self.data_manager.set_judge_approval(
                self.selected_competitor,
                self.current_problem_id,
                'rejected'
            )
            
            # Update UI
            self.approval_status_var.set("✗ Rejected")
            self.approval_status_label.config(foreground='#e74c3c')
            
            # Refresh to update rankings
            self.refresh_data()
            
            messagebox.showinfo("Rejected", 
                f"Solution rejected for {self.selected_competitor} - Problem {self.current_problem_id}")
        except Exception as e:
            print(f"[ERROR] Failed to reject: {str(e)}")
            messagebox.showerror("Error", f"Failed to reject solution:\n{str(e)}")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        if self.auto_refresh_var.get():
            self.refresh_data()
        else:
            if self.refresh_job:
                self.root.after_cancel(self.refresh_job)
    
    def export_report(self):
        """Export competition report"""
        messagebox.showinfo("Export", "Report export feature - Coming soon!")
    
    def reset_competition(self):
        """Reset all competition data"""
        response = messagebox.askyesno("Confirm Reset",
            "Are you sure you want to reset ALL competition data?\n\n"
            "This will delete all competitors, submissions, and progress.\n"
            "This action cannot be undone!")
        
        if response:
            self.data_manager.reset_competition()
            self.selected_competitor = None
            self.refresh_data()
            messagebox.showinfo("Reset Complete", "Competition data has been reset.")


def main():
    root = tk.Tk()
    data_manager = create_data_manager()
    app = JudgeDashboard(root, data_manager)
    root.mainloop()


if __name__ == "__main__":
    main()
