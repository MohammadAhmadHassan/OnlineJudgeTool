# -*- coding: utf-8 -*-
"""
Improved Competitor Interface
Enhanced UI with better layout and visual feedback
"""
import json
import os
import sys
import zipfile
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import tempfile
import shutil
import subprocess
from data_manager import create_data_manager


class ImprovedCompetitorApp:
    def __init__(self, root, data_manager):
        self.root = root
        self.data_manager = data_manager
        self.root.title("Competitor View - Python Coding Competition")
        # Start maximized to fit window
        self.root.state('zoomed')
        self.root.minsize(1000, 700)
        
        # Modern color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'success': '#27ae60',
            'error': '#e74c3c',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'text': '#2c3e50',
            'background': '#ffffff',
            'select': '#d4e6f1',
            'code_bg': '#f8f9fa',
            'border': '#dee2e6'
        }
        
        # Configure styles
        self.configure_styles()
        
        # Initialize data
        self.current_problem = 0
        self.problems = []
        self.user_name = ""
        self.results = {}
        self.auto_save_job = None
        
        # Create widgets
        self.create_widgets()
        
        # Defer loading problems until after UI is shown (improves startup time)
        self.root.after(100, self._deferred_init)
    
    def _deferred_init(self):
        """Deferred initialization to improve startup performance"""
        self.load_problems()
        
        if self.problems:
            self.show_problem(0)
    
    def configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame styles
        style.configure('TFrame', background=self.colors['background'])
        style.configure('Header.TFrame', background=self.colors['primary'])
        style.configure('Card.TFrame', background=self.colors['background'], 
                       relief='solid', borderwidth=1)
        
        # Label styles
        style.configure('TLabel', background=self.colors['background'], 
                       foreground=self.colors['text'], font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), 
                       foreground='white', background=self.colors['primary'])
        style.configure('Subtitle.TLabel', font=('Segoe UI', 12, 'bold'), 
                       foreground=self.colors['secondary'])
        style.configure('Status.TLabel', font=('Segoe UI', 9), 
                       padding=5, relief='sunken')
        
        # Button styles
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'),
                       padding=8, background=self.colors['secondary'])
        style.map('Primary.TButton',
                 background=[('active', '#2980b9'), ('disabled', '#bdc3c7')])
        
        style.configure('Success.TButton', font=('Segoe UI', 10, 'bold'),
                       padding=8, background=self.colors['success'])
        style.map('Success.TButton',
                 background=[('active', '#229954'), ('disabled', '#bdc3c7')])
        
        style.configure('Nav.TButton', font=('Segoe UI', 9), padding=5)
        
        # Entry style
        style.configure('TEntry', font=('Segoe UI', 10), padding=5)
        
        # Treeview styles
        style.configure('Treeview', font=('Segoe UI', 10), rowheight=35,
                       background=self.colors['background'],
                       fieldbackground=self.colors['background'])
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'),
                       background=self.colors['light'], foreground=self.colors['primary'])
        style.map('Treeview', background=[('selected', self.colors['select'])])
        
        # LabelFrame style
        style.configure('TLabelframe', background=self.colors['background'],
                       borderwidth=2, relief='solid')
        style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'),
                       foreground=self.colors['primary'], background=self.colors['background'])
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.create_header(main_container)
        
        # Action buttons at the top (always visible)
        self.create_action_buttons(main_container)
        
        # Center frame to hold all content
        center_outer = ttk.Frame(main_container)
        center_outer.pack(fill=tk.BOTH, expand=True)
        
        # Create a centered column for content (narrower for better visual centering)
        center_column = ttk.Frame(center_outer)
        center_column.place(relx=0.5, rely=0.5, anchor=tk.CENTER, relwidth=0.85, relheight=0.95)
        
        # Use simpler scrolling with frame instead of canvas for better performance
        scrollable_container = ttk.Frame(center_column)
        scrollable_container.pack(fill=tk.BOTH, expand=True)
        
        # Vertical scrollbar only
        scrollbar = ttk.Scrollbar(scrollable_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Use Text widget as scrollable container (much lighter than Canvas)
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
        
        # Content area with padding - increased for better centering
        content_frame = ttk.Frame(scrollable_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=60, pady=20)
        
        # Problem navigation
        self.create_navigation(content_frame)
        
        # Create PanedWindow for resizable sections
        paned = tk.PanedWindow(content_frame, orient=tk.VERTICAL, 
                              sashwidth=5, sashrelief=tk.RAISED,
                              bg=self.colors['border'])
        paned.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Top section: Problem description
        desc_container = ttk.Frame(paned)
        self.create_problem_description(desc_container)
        paned.add(desc_container, minsize=150, height=200)
        
        # Middle section: Code editor
        code_container = ttk.Frame(paned)
        self.create_code_editor(code_container)
        paned.add(code_container, minsize=200, height=250)
        
        # Bottom section: Test cases
        test_container = ttk.Frame(paned)
        self.create_test_cases(test_container)
        paned.add(test_container, minsize=150, height=200)
        
        # Status bar
        self.create_status_bar(main_container)
    
    def create_header(self, parent):
        """Create header section"""
        header = ttk.Frame(parent, style='Header.TFrame')
        header.pack(fill=tk.X)
        
        # Title
        title_label = ttk.Label(header, 
                               text="🏆 Python Coding Competition",
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # User info frame
        user_frame = ttk.Frame(header, style='Header.TFrame')
        user_frame.pack(side=tk.RIGHT, padx=20, pady=15)
        
        ttk.Label(user_frame, text="Competitor Name:", 
                 foreground='white', background=self.colors['primary'],
                 font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.name_entry = ttk.Entry(user_frame, width=25, font=('Segoe UI', 10))
        self.name_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_btn = ttk.Button(user_frame, text="▶ Start Competition",
                                    style='Success.TButton',
                                    command=self.start_competition)
        self.start_btn.pack(side=tk.LEFT)
    
    def create_navigation(self, parent):
        """Create problem navigation"""
        nav_frame = ttk.Frame(parent)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.prev_btn = ttk.Button(nav_frame, text="◀ Previous",
                                   style='Nav.TButton',
                                   command=self.prev_problem,
                                   state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.problem_title = ttk.Label(nav_frame, text="",
                                       style='Subtitle.TLabel')
        self.problem_title.pack(side=tk.LEFT, expand=True, padx=20)
        
        # Problem status indicator
        self.problem_status_label = ttk.Label(nav_frame, text="",
                                             font=('Segoe UI', 9))
        self.problem_status_label.pack(side=tk.LEFT, padx=10)
        
        self.next_btn = ttk.Button(nav_frame, text="Next ▶",
                                   style='Nav.TButton',
                                   command=self.next_problem,
                                   state=tk.DISABLED)
        self.next_btn.pack(side=tk.RIGHT, padx=5)
    
    def create_problem_description(self, parent):
        """Create problem description section"""
        frame = ttk.LabelFrame(parent, text="📋 Problem Description", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with better styling
        self.problem_desc = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, font=('Segoe UI', 11),
            padx=15, pady=15, bg=self.colors['background'],
            relief=tk.FLAT, borderwidth=0
        )
        self.problem_desc.pack(fill=tk.BOTH, expand=True)
        self.problem_desc.config(state=tk.DISABLED)
    
    def create_code_editor(self, parent):
        """Create code editor section"""
        frame = ttk.LabelFrame(parent, text="💻 Your Solution", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(toolbar, text="Write your Python code below:",
                 font=('Segoe UI', 9, 'italic'),
                 foreground='#6c757d').pack(side=tk.LEFT)
        
        # Clear button
        clear_btn = ttk.Button(toolbar, text="🗑 Clear",
                              command=self.clear_code,
                              style='Nav.TButton')
        clear_btn.pack(side=tk.RIGHT, padx=2)
        
        # Code editor with line numbers effect
        editor_frame = ttk.Frame(frame)
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        self.code_editor = scrolledtext.ScrolledText(
            editor_frame, wrap=tk.NONE, font=('Consolas', 11),
            padx=10, pady=10, bg=self.colors['code_bg'],
            insertbackground=self.colors['primary'],
            selectbackground=self.colors['select'],
            relief=tk.SOLID, borderwidth=1
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # Bind auto-save
        self.code_editor.bind('<KeyRelease>', self.schedule_auto_save)
    
    def create_test_cases(self, parent):
        """Create test cases section"""
        frame = ttk.LabelFrame(parent, text="✓ Test Cases", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Test results treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.test_tree = ttk.Treeview(
            tree_frame,
            columns=("status", "input", "output", "expected"),
            show="headings",
            selectmode='browse'
        )
        
        # Configure columns
        self.test_tree.heading("status", text="Status")
        self.test_tree.heading("input", text="Input")
        self.test_tree.heading("output", text="Your Output")
        self.test_tree.heading("expected", text="Expected Output")
        
        self.test_tree.column("status", width=100, stretch=False, anchor=tk.CENTER)
        self.test_tree.column("input", width=200, stretch=True)
        self.test_tree.column("output", width=200, stretch=True)
        self.test_tree.column("expected", width=200, stretch=True)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                                command=self.test_tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL,
                                command=self.test_tree.xview)
        self.test_tree.configure(yscrollcommand=y_scroll.set, 
                                xscrollcommand=x_scroll.set)
        
        self.test_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Bind double-click to show details
        self.test_tree.bind("<Double-1>", self.show_test_details)
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        # Container with background to make it stand out
        button_container = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        button_container.pack(fill=tk.X, padx=10, pady=5)
        
        button_frame = ttk.Frame(button_container)
        button_frame.pack(fill=tk.X, padx=15, pady=12)
        
        # Left side buttons
        left_frame = ttk.Frame(button_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.run_btn = ttk.Button(left_frame, text="▶ Run & Test Solution",
                                  style='Primary.TButton',
                                  command=self.run_tests,
                                  state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, padx=5, ipadx=25, ipady=8)
        
        ttk.Label(left_frame, text="← Compare your code with test cases",
                 font=('Segoe UI', 9, 'italic'),
                 foreground='#6c757d').pack(side=tk.LEFT, padx=(5, 20))
        
        self.submit_btn = ttk.Button(left_frame, text="✓ Submit Solution",
                                     style='Success.TButton',
                                     command=self.submit_solution,
                                     state=tk.DISABLED)
        self.submit_btn.pack(side=tk.LEFT, padx=5, ipadx=25, ipady=8)
        
        ttk.Label(left_frame, text="← Record your submission",
                 font=('Segoe UI', 9, 'italic'),
                 foreground='#6c757d').pack(side=tk.LEFT, padx=5)
        
        # Right side button
        self.export_btn = ttk.Button(button_frame, text="📦 Export All",
                                     style='Nav.TButton',
                                     command=self.export_solutions,
                                     state=tk.DISABLED)
        self.export_btn.pack(side=tk.RIGHT, padx=5, ipadx=15, ipady=8)
    
    def create_status_bar(self, parent):
        """Create status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Please enter your name and start the competition.")
        
        self.status_bar = ttk.Label(parent, textvariable=self.status_var,
                                    style='Status.TLabel', anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def load_problems(self):
        """Load all problems from JSON files"""
        self.problems = []
        
        # Handle PyInstaller bundled resources
        if getattr(sys, 'frozen', False):
            # Running as executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        problems_dir = os.path.join(base_path, "problems")
        
        if not os.path.exists(problems_dir):
            messagebox.showerror("Error", f"Problems directory not found!\nLooked in: {problems_dir}")
            return
        
        # Load regular problems
        for i in range(1, 11):
            problem_file = os.path.join(problems_dir, f"problem{i}.json")
            if os.path.exists(problem_file):
                try:
                    with open(problem_file, "r", encoding='utf-8') as f:
                        problem = json.load(f)
                        problem["id"] = i
                        self.problems.append(problem)
                except Exception as e:
                    print(f"Error loading problem {i}: {e}")
        
        if not self.problems:
            messagebox.showwarning("Warning", "No problems found!")
    
    def start_competition(self):
        """Start the competition"""
        self.user_name = self.name_entry.get().strip()
        
        if not self.user_name:
            messagebox.showerror("Error", "Please enter your name!")
            return
        
        # Check if name is already taken
        if self.data_manager.is_name_taken(self.user_name):
            response = messagebox.askyesno("Name Taken", 
                f"The name '{self.user_name}' is already in use. Do you want to continue as this user?")
            if not response:
                return
        else:
            # Register new competitor
            self.data_manager.register_competitor(self.user_name)
        
        # Update UI
        self.name_entry.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.run_btn.config(state=tk.NORMAL)
        self.submit_btn.config(state=tk.NORMAL)
        self.next_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
        
        self.status_var.set(f"✓ Competition started! Welcome, {self.user_name}")
        self.update_status_color(self.colors['success'])
    
    def show_problem(self, problem_idx):
        """Display the specified problem"""
        if not 0 <= problem_idx < len(self.problems):
            return
        
        self.save_current_code()
        self.current_problem = problem_idx
        problem = self.problems[problem_idx]
        
        # Update data manager
        if self.user_name:
            self.data_manager.update_competitor_problem(self.user_name, problem['id'])
        
        # Update title
        self.problem_title.config(text=f"Problem {problem['id']}: {problem['title']}")
        
        # Update problem description
        self.problem_desc.config(state=tk.NORMAL)
        self.problem_desc.delete(1.0, tk.END)
        self.problem_desc.insert(tk.END, problem['description'])
        self.problem_desc.config(state=tk.DISABLED)
        
        # Clear and update test cases
        for item in self.test_tree.get_children():
            self.test_tree.delete(item)
        
        for test_case in problem['test_cases']:
            self.test_tree.insert("", tk.END, 
                                 values=("⏳ Not Run", 
                                        self.truncate_text(test_case['input']),
                                        "", 
                                        self.truncate_text(test_case['output'])))
        
        # Update navigation buttons
        self.prev_btn.config(state=tk.NORMAL if problem_idx > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if problem_idx < len(self.problems) - 1 else tk.DISABLED)
        
        # Load saved code
        self.code_editor.delete(1.0, tk.END)
        if problem['id'] in self.results:
            self.code_editor.insert(tk.END, self.results[problem['id']]['code'])
        
        # Update problem status
        self.update_problem_status()
    
    def update_problem_status(self):
        """Update the problem status indicator"""
        problem_id = self.problems[self.current_problem]['id']
        
        if problem_id in self.results and self.results[problem_id].get('passed'):
            self.problem_status_label.config(text="✓ Solved", 
                                            foreground=self.colors['success'])
        elif problem_id in self.results:
            self.problem_status_label.config(text="◐ Attempted",
                                            foreground=self.colors['warning'])
        else:
            self.problem_status_label.config(text="○ Not Attempted",
                                            foreground='#6c757d')
    
    def truncate_text(self, text, max_length=50):
        """Truncate text for display"""
        text = str(text).strip()
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    def clear_code(self):
        """Clear the code editor"""
        if messagebox.askyesno("Confirm", "Clear all code in the editor?"):
            self.code_editor.delete(1.0, tk.END)
    
    def schedule_auto_save(self, event=None):
        """Schedule auto-save of current code"""
        if self.auto_save_job:
            self.root.after_cancel(self.auto_save_job)
        self.auto_save_job = self.root.after(1000, self.save_current_code)
    
    def save_current_code(self):
        """Save current code to results"""
        if not self.problems:
            return
        
        problem_id = self.problems[self.current_problem]['id']
        code = self.code_editor.get(1.0, tk.END).strip()
        
        if problem_id not in self.results:
            self.results[problem_id] = {"code": code, "passed": False}
        else:
            self.results[problem_id]["code"] = code
    
    def prev_problem(self):
        """Navigate to previous problem"""
        self.show_problem(self.current_problem - 1)
    
    def next_problem(self):
        """Navigate to next problem"""
        self.show_problem(self.current_problem + 1)
    
    def run_tests(self):
        """Run all test cases"""
        self.save_current_code()
        
        problem = self.problems[self.current_problem]
        problem_id = problem['id']
        student_code = self.code_editor.get(1.0, tk.END).strip()
        
        if not student_code:
            messagebox.showwarning("Warning", "Please write some code first!")
            return
        
        if not self.user_name:
            messagebox.showerror("Error", "Please start the competition first!")
            return
        
        self.status_var.set("⏳ Running tests...")
        self.run_btn.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.DISABLED)
        self.root.update()
        
        # Run tests in a separate thread to keep UI responsive
        import threading
        thread = threading.Thread(target=self._run_tests_thread, 
                                 args=(problem, problem_id, student_code), 
                                 daemon=True)
        thread.start()
    
    def _run_tests_thread(self, problem, problem_id, student_code):
        """Run tests in background thread"""
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        test_results = []
        all_passed = True
        
        try:
            for i, test_case in enumerate(problem['test_cases']):
                # Update status for this test
                self.root.after(0, lambda idx=i: self.status_var.set(f"⏳ Running test {idx+1}/{len(problem['test_cases'])}..."))
                temp_file = os.path.join(temp_dir, f"test_{problem_id}_{i}.py")
                
                # Create test program
                with open(temp_file, "w", encoding='utf-8') as f:
                    input_path = os.path.join(temp_dir, 'input.txt').replace('\\', '\\\\')
                    f.write("# Auto-generated test file\n")
                    f.write("import sys\n")
                    f.write(f"sys.stdin = open(r'{input_path}', 'r', encoding='utf-8')\n\n")
                    f.write("# Student code below:\n")
                    f.write(student_code)
                    if not student_code.endswith('\n'):
                        f.write("\n")
                
                # Create input file
                with open(os.path.join(temp_dir, 'input.txt'), 'w', encoding='utf-8') as f:
                    f.write(test_case['input'])
                
                # Execute code
                try:
                    # Set environment to force UTF-8 encoding
                    env = os.environ.copy()
                    env['PYTHONIOENCODING'] = 'utf-8'
                    
                    # Find the correct Python interpreter
                    # When frozen (executable), use system Python or bundled Python
                    if getattr(sys, 'frozen', False):
                        # Use system Python when running as executable
                        python_cmd = 'python'
                    else:
                        # Use the current Python interpreter when running as script
                        python_cmd = sys.executable
                    
                    # Run with subprocess
                    process = subprocess.Popen(
                        [python_cmd, temp_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        cwd=temp_dir,
                        env=env
                    )
                    stdout, stderr = process.communicate(timeout=30)
                    
                    # Check for errors
                    if stderr:
                        # Filter out warnings, only raise on actual errors
                        error_lines = [line for line in stderr.split('\n') 
                                      if line.strip() and not line.startswith('  File')]
                        if error_lines:
                            raise Exception(stderr)
                    
                    # Normalize output
                    student_output = stdout.strip()
                    expected_output = test_case['output'].strip()
                    passed = student_output == expected_output
                    
                    # Update tree (schedule on main thread) - capture values in closure
                    status = "✓ Passed" if passed else "✗ Failed"
                    status_color = self.colors['success'] if passed else self.colors['error']
                    
                    # Use default arguments to capture current values (avoid closure issues)
                    def update_tree(idx=i, st=status, tc_in=test_case['input'], 
                                  s_out=student_output, e_out=expected_output, color=status_color):
                        item = self.test_tree.get_children()[idx]
                        self.test_tree.item(item, values=(
                            st,
                            self.truncate_text(tc_in),
                            self.truncate_text(s_out),
                            self.truncate_text(e_out)
                        ))
                        self.test_tree.tag_configure(f"row{idx}", foreground=color)
                        self.test_tree.item(item, tags=(f"row{idx}",))
                    
                    self.root.after(0, update_tree)
                    
                    test_results.append({
                        "test_id": i + 1,
                        "passed": passed,
                        "input": test_case['input'],
                        "expected": expected_output,
                        "actual": student_output
                    })
                    
                    if not passed:
                        all_passed = False
                
                except subprocess.TimeoutExpired:
                    # Capture values to avoid closure issues
                    def update_timeout(idx=i, tc_in=test_case['input'], tc_out=test_case['output']):
                        item = self.test_tree.get_children()[idx]
                        self.test_tree.item(item, values=(
                            "⏱ Timeout",
                            self.truncate_text(tc_in),
                            "Execution timeout",
                            self.truncate_text(tc_out)
                        ))
                        self.test_tree.tag_configure(f"row{idx}", foreground=self.colors['warning'])
                        self.test_tree.item(item, tags=(f"row{idx}",))
                    
                    self.root.after(0, update_timeout)
                    
                    test_results.append({
                        "test_id": i + 1,
                        "passed": False,
                        "error": "Timeout"
                    })
                    all_passed = False
                
                except Exception as e:
                    error_msg = str(e)
                    # Capture values to avoid closure issues
                    def update_error(idx=i, tc_in=test_case['input'], err=error_msg, tc_out=test_case['output']):
                        item = self.test_tree.get_children()[idx]
                        self.test_tree.item(item, values=(
                            "✗ Error",
                            self.truncate_text(tc_in),
                            self.truncate_text(err, 100),
                            self.truncate_text(tc_out)
                        ))
                        self.test_tree.tag_configure(f"row{idx}", foreground=self.colors['error'])
                        self.test_tree.item(item, tags=(f"row{idx}",))
                    
                    self.root.after(0, update_error)
                    
                    test_results.append({
                        "test_id": i + 1,
                        "passed": False,
                        "error": str(e)
                    })
                    all_passed = False
            
            # Update results
            self.results[problem_id]["passed"] = all_passed
            self.results[problem_id]["test_results"] = test_results
            
            # Update status (on main thread)
            def update_final_status():
                if all_passed:
                    self.status_var.set(f"✓ All tests passed! Great job!")
                    self.update_status_color(self.colors['success'])
                else:
                    passed_count = sum(1 for t in test_results if t.get("passed", False))
                    self.status_var.set(f"⚠ {passed_count}/{len(test_results)} tests passed")
                    self.update_status_color(self.colors['warning'])
                
                self.update_problem_status()
                self.run_btn.config(state=tk.NORMAL)
                self.submit_btn.config(state=tk.NORMAL)
            
            self.root.after(0, update_final_status)
        
        except Exception as e:
            error_msg = str(e)
            def show_error():
                messagebox.showerror("Error", f"Failed to run tests:\n{error_msg}")
                self.status_var.set("✗ Error running tests")
                self.update_status_color(self.colors['error'])
                self.run_btn.config(state=tk.NORMAL)
                self.submit_btn.config(state=tk.NORMAL)
            
            self.root.after(0, show_error)
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def submit_solution(self):
        """Submit the current solution"""
        self.save_current_code()
        
        problem = self.problems[self.current_problem]
        problem_id = problem['id']
        
        if problem_id not in self.results or not self.results[problem_id].get('code'):
            messagebox.showwarning("Warning", "Please write some code first!")
            return
        
        if 'test_results' not in self.results[problem_id]:
            response = messagebox.askyesno("Not Tested",
                "You haven't run the tests yet. Do you want to submit anyway?")
            if not response:
                return
            test_results = []
            all_passed = False
        else:
            test_results = self.results[problem_id].get('test_results', [])
            all_passed = self.results[problem_id].get('passed', False)
        
        # Submit to data manager
        self.data_manager.submit_solution(
            self.user_name,
            problem_id,
            self.results[problem_id]['code'],
            test_results,
            all_passed
        )
        
        if all_passed:
            messagebox.showinfo("Success", 
                f"✓ Solution submitted successfully!\nAll test cases passed!")
            self.status_var.set(f"✓ Solution submitted for Problem {problem_id}")
            self.update_status_color(self.colors['success'])
        else:
            messagebox.showinfo("Submitted", 
                f"Solution submitted. Some tests need attention.")
            self.status_var.set(f"⚠ Solution submitted for Problem {problem_id} (incomplete)")
            self.update_status_color(self.colors['warning'])
    
    def show_test_details(self, event):
        """Show full test case details in a popup"""
        region = self.test_tree.identify("region", event.x, event.y)
        if region == "heading":
            return
        
        column = self.test_tree.identify_column(event.x)
        item = self.test_tree.identify_row(event.y)
        
        if item and column:
            col_index = int(column[1:]) - 1
            columns = ["status", "input", "output", "expected"]
            col_name = columns[col_index]
            cell_value = self.test_tree.item(item, "values")[col_index]
            
            # Create popup
            popup = tk.Toplevel(self.root)
            popup.title(f"{col_name.upper()}")
            popup.geometry("600x400")
            popup.transient(self.root)
            
            text_area = scrolledtext.ScrolledText(popup, wrap=tk.WORD,
                                                 font=('Consolas', 10),
                                                 padx=15, pady=15)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert(tk.END, cell_value)
            text_area.config(state=tk.DISABLED)
            
            close_btn = ttk.Button(popup, text="Close",
                                  command=popup.destroy)
            close_btn.pack(pady=10)
    
    def export_solutions(self):
        """Export all solutions to a ZIP file"""
        if not self.user_name:
            messagebox.showerror("Error", "Please start the competition first!")
            return
        
        temp_dir = tempfile.mkdtemp()
        export_dir = os.path.join(temp_dir, f"solutions_{self.user_name}")
        os.makedirs(export_dir)
        
        try:
            # Create solution files
            summary_lines = [
                f"Competitor: {self.user_name}",
                f"Export Date: {subprocess.check_output(['date', '/t'], text=True).strip() if os.name == 'nt' else ''}",
                "\n" + "="*50,
                "\nProblem Results:",
                "="*50 + "\n"
            ]
            
            for problem in self.problems:
                problem_id = problem['id']
                filename = os.path.join(export_dir, f"problem_{problem_id}.py")
                
                with open(filename, "w", encoding='utf-8') as f:
                    if problem_id in self.results and self.results[problem_id]['code']:
                        f.write(f"# Problem {problem_id}: {problem['title']}\n")
                        f.write(f"# {'-' * 50}\n\n")
                        f.write(self.results[problem_id]["code"])
                    else:
                        f.write(f"# Problem {problem_id}: {problem['title']}\n")
                        f.write("# No solution submitted\n")
                
                # Add to summary
                status = "✓ PASSED" if (problem_id in self.results and 
                                       self.results[problem_id].get("passed")) else "✗ NOT SOLVED"
                summary_lines.append(f"Problem {problem_id}: {status}")
            
            # Write summary
            with open(os.path.join(export_dir, "SUMMARY.txt"), "w", encoding='utf-8') as f:
                f.write("\n".join(summary_lines))
            
            # Ask for save location
            zip_filename = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip")],
                initialfile=f"solutions_{self.user_name}.zip"
            )
            
            if zip_filename:
                with zipfile.ZipFile(zip_filename, 'w') as zipf:
                    for root, dirs, files in os.walk(export_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, export_dir)
                            zipf.write(file_path, arcname)
                
                messagebox.showinfo("Success", 
                    f"✓ Solutions exported to:\n{zip_filename}")
                self.status_var.set("✓ Solutions exported successfully")
                self.update_status_color(self.colors['success'])
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{str(e)}")
        
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def update_status_color(self, color):
        """Update status bar background color"""
        self.status_bar.configure(background=color, foreground='white')
        self.root.after(3000, lambda: self.status_bar.configure(
            background=self.colors['background'], 
            foreground=self.colors['text']))


def main():
    root = tk.Tk()
    data_manager = create_data_manager()
    app = ImprovedCompetitorApp(root, data_manager)
    root.mainloop()


if __name__ == "__main__":
    main()
