# -*- coding: utf-8 -*-
"""
Python Coding Competition App with Fixed UI Issues
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
from PIL import Image, ImageTk

class CodingCompetitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("The Geek Academy - Python Coding Competition")
        self.root.geometry("1100x800")
        self.root.minsize(900, 650)
        # Configure grid weights for the root window
              # Modern color scheme
        self.colors = {
            'primary': '#2c3e50',     # Dark blue
            'secondary': '#3498db',   # Light blue
            'success': '#27ae60',     # Green
            'error': '#e74c3c',       # Red
            'warning': '#f39c12',     # Yellow
            'light': '#ecf0f1',       # Light gray
            'text': '#2c3e50',        # Dark text
            'background': '#ffffff',  # White background
            'select': '#d4e6f1'       # Selection color
        }
        
        # Configure styles
        self.configure_styles()
        
        # Create widgets
        self.create_widgets()
        
        # Initialize data
        self.current_problem = 0
        self.problems = []
        self.user_name = ""
        self.results = {}
        self.load_problems()
        
        if self.problems:
            self.show_problem(0)

   

    def create_widgets(self):
        """Create all GUI widgets in a single window layout"""
        # Header frame
        self.header_frame = ttk.Frame(self.root, padding=10)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        # Title
        self.title_label = ttk.Label(
            self.header_frame, 
            text="The Geek Academy - Python Coding Competition",
            style='Title.TLabel'
        )
        self.title_label.pack(side=tk.LEFT)

        # User entry
        self.user_frame = ttk.Frame(self.header_frame)
        self.user_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(self.user_frame, text="Your Name:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(self.user_frame, width=20)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        self.start_btn = ttk.Button(
            self.user_frame, 
            text="Start Competition", 
            command=self.start_competition
        )
        self.start_btn.pack(side=tk.LEFT)
        
        # Main content area
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(3, weight=1)  # Test cases (reduced space)

        # Problem navigation
        self.nav_frame = ttk.Frame(self.content_frame)
        self.nav_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.prev_btn = ttk.Button(
            self.nav_frame, 
            text="◀ Previous", 
            style='Nav.TButton',
            command=self.prev_problem, 
            state=tk.DISABLED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.problem_title = ttk.Label(
            self.nav_frame, 
            text="", 
            style='Subtitle.TLabel'
        )
        self.problem_title.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = ttk.Button(
            self.nav_frame, 
            text="Next ▶", 
            style='Nav.TButton',
            command=self.next_problem, 
            state=tk.DISABLED
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        
        # Problem Description Frame (auto-sized)
        self.desc_frame = ttk.LabelFrame(self.content_frame, text="Problem Description", padding=10)
        self.desc_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        self.desc_frame.columnconfigure(0, weight=1)
        self.desc_frame.rowconfigure(0, weight=1)

        self.problem_desc = scrolledtext.ScrolledText(
            self.desc_frame, 
            wrap=tk.WORD, 
            font=('Arial', 11),
            padx=10,
            pady=10,
            state=tk.NORMAL  # Start in normal state

        )
        self.problem_desc.grid(row=0, column=0, sticky="nsew")
        
        # Code Editor Frame
        self.code_frame = ttk.LabelFrame(self.content_frame, text="Your Solution", padding=10)
        self.code_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        self.code_frame.columnconfigure(0, weight=1)
        self.code_frame.rowconfigure(0, weight=1)
        
        self.code_editor = scrolledtext.ScrolledText(
            self.code_frame, 
            wrap=tk.WORD, 
            font=('Consolas', 11),
            padx=10,
            pady=10,
            height=8  # Fixed height for code editor
        )
        self.code_editor.grid(row=0, column=0, sticky="nsew")
        
        # Test Cases Frame
        self.test_frame = ttk.LabelFrame(self.content_frame, text="Test Cases", padding=10)
        self.test_frame.grid(row=3, column=0, sticky="nsew", pady=5)
        self.test_frame.columnconfigure(0, weight=1)
        self.test_frame.rowconfigure(0, weight=1)
        self.desc_frame.grid_propagate(False)  # Keep fixed height
        self.test_frame.grid_propagate(False)  # Keep fixed height

        self.desc_frame.config(height=20)  # Adjust this value as needed
        self.test_frame.config(height=10)  # Adjust this value as needed

        # Configure grid weights for content frame
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)  # Description expands
        self.content_frame.grid_rowconfigure(2, weight=1)  # Code editor fixed
        self.content_frame.grid_rowconfigure(3, weight=3)  # Test cases fixed height

        # Test case treeview
        self.test_tree = ttk.Treeview(
            self.test_frame,
            columns=("status", "input", "output", "expected"),
            show="headings",
            selectmode='browse',
        )
        
        # Configure columns
        self.test_tree.heading("status", text="Status", anchor=tk.CENTER)
        self.test_tree.heading("input", text="Input", anchor=tk.W)
        self.test_tree.heading("output", text="Your Output", anchor=tk.W)
        self.test_tree.heading("expected", text="Expected Output", anchor=tk.W)
        
        # Set column widths
        self.test_tree.column("status", width=100, stretch=False, anchor=tk.CENTER)
        self.test_tree.column("input", width=200, minwidth=150, stretch=True)
        self.test_tree.column("output", width=200, minwidth=150, stretch=True)
        self.test_tree.column("expected", width=200, minwidth=150, stretch=True)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(self.test_frame, orient=tk.VERTICAL, command=self.test_tree.yview)
        x_scroll = ttk.Scrollbar(self.test_frame, orient=tk.HORIZONTAL, command=self.test_tree.xview)
        self.test_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Grid layout
        self.test_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        
        # Action buttons
        self.action_frame = ttk.Frame(self.root, padding=10)
        self.action_frame.grid(row=2, column=0, sticky="ew")
        
        self.run_btn = ttk.Button(
            self.action_frame, 
            text="Run Tests", 
            command=self.run_tests,
            state=tk.DISABLED
        )
        self.run_btn.pack(side=tk.LEFT, padx=10, ipadx=20)
        
        self.export_btn = ttk.Button(
            self.action_frame, 
            text="Export Solutions", 
            command=self.export_solutions,
            state=tk.DISABLED
        )
        self.export_btn.pack(side=tk.RIGHT, padx=10, ipadx=20)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=5
        )
        self.status_bar.grid(row=3, column=0, sticky="ew")
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Bind events
        self.test_tree.bind("<Double-1>", self.show_cell_content)
        self.test_tree.bind("<<TreeviewSelect>>", self.on_test_select)
    def load_problems(self):
        """Load all problems from JSON files"""
        self.problems = []
        
        try:
            for i in range(1, 6):
                with open(f"problems/problem{i}.json", "r") as f:
                    problem = json.load(f)
                    problem["id"] = i
                    self.problems.append(problem)   
        except FileNotFoundError:
            print(f"Problem {i} not found")

    def show_cell_content(self, event):
        """Show full content of a cell in a popup window when double-clicked"""
        region = self.test_tree.identify("region", event.x, event.y)
        if region == "heading":
            return  # Don't show popup for column headings
            
        column = self.test_tree.identify_column(event.x)
        item = self.test_tree.identify_row(event.y)
        
        if item and column:
            # Get the cell value
            col_index = int(column[1:]) - 1
            columns = ["status", "input", "output", "expected"]
            col_name = columns[col_index]
            cell_value = self.test_tree.item(item, "values")[col_index]
            
            # Create popup window
            popup = tk.Toplevel(self.root)
            popup.title(f"{col_name.capitalize()} Content")
            popup.geometry("500x300")
            popup.resizable(True, True)
            
            # Add scrolled text widget
            text_area = scrolledtext.ScrolledText(
                popup,
                wrap=tk.WORD,
                font=('Consolas', 10),
                padx=10,
                pady=10
            )
            text_area.pack(fill=tk.BOTH, expand=True)
            text_area.insert(tk.END, cell_value)
            text_area.config(state=tk.DISABLED)
            
            # Close button
            close_btn = ttk.Button(
                popup,
                text="Close",
                command=popup.destroy
            )
            close_btn.pack(pady=5)

    # Add this method to your class
    def on_test_select(self, event):
        selected = self.test_tree.selection()
        if not selected:
            return
            
        # Make sure the selected item is visible
        self.test_tree.see(selected[0])
        
        # Clear previous selections
        for item in self.test_tree.get_children():
            self.test_tree.item(item, tags=())
        
        # Apply selection highlight to entire row
        #self.test_tree.item(selected[0], tags=('selected',))

    # Update your __init__ method to include this style configuration
    def configure_styles(self):
        """Configure ttk styles for the application"""
        style = ttk.Style()
        
        # Main styles
        style.configure('.', background=self.colors['background'])
        style.configure('TFrame', background=self.colors['background'])
        style.configure('TLabel', background=self.colors['background'], foreground=self.colors['text'])
        style.configure('TButton', font=('Arial', 10), foreground=self.colors['text'])
        style.configure('TEntry', font=('Arial', 10))
        
        # Treeview styles
        style.configure('Treeview', 
                      font=('Arial', 10),
                      rowheight=30,
                      background=self.colors['background'],
                      fieldbackground=self.colors['background'],
                      foreground=self.colors['text'])
        
        style.configure('Treeview.Heading', 
                      font=('Arial', 10, 'bold'),
                      background=self.colors['light'],
                      foreground=self.colors['primary'])
        
        style.map('Treeview',
                background=[('selected', self.colors['select'])],
                foreground=[('selected', self.colors['text'])])
        
        # Custom styles
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), foreground=self.colors['primary'])
        style.configure('Subtitle.TLabel', font=('Arial', 11, 'bold'), foreground=self.colors['secondary'])
        style.configure('Accent.TButton', 
                      font=('Arial', 10, 'bold'),
                      padding=6)
        
        style.map('Accent.TButton',
                background=[('active', self.colors['primary']), 
                          ('disabled', '#cccccc')],
                foreground=[('active', 'white'),
                          ('disabled', '#888888')])
        
        style.configure('Nav.TButton', 
                      font=('Arial', 10),
                      padding=4)
      
    def start_competition(self):
        """Start the competition with the entered name"""
        self.user_name = self.name_entry.get().strip()
        if not self.user_name:
            messagebox.showerror("Error", "Please enter your name")
            return
        
        self.name_entry.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.run_btn.config(state=tk.NORMAL)
        self.next_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
        
        self.status_var.set(f"Competition started for {self.user_name}")

    def show_problem(self, problem_idx):
        """Display the specified problem"""
        if not 0 <= problem_idx < len(self.problems):
            return
            
        self.current_problem = problem_idx
        problem = self.problems[problem_idx]
        
        # Update problem display
        self.problem_title.config(text=f"Problem {problem['id']}: {problem['title']}")
        
        # Update problem description
        self.problem_desc.config(state=tk.NORMAL)  # Enable editing
        self.problem_desc.delete(1.0, tk.END)
        self.problem_desc.insert(tk.END, problem['description'])
            
        # Clear and update test cases
        for item in self.test_tree.get_children():
            self.test_tree.delete(item)
            
        for test_case in problem['test_cases']:
            self.test_tree.insert("", tk.END, values=("Not run", test_case['input'], "", test_case['output']))
        
        # Auto-size columns
        self.auto_size_columns()
        
        # Update navigation buttons
        self.prev_btn.config(state=tk.NORMAL if problem_idx > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if problem_idx < len(self.problems) - 1 else tk.DISABLED)
        
        # Load saved code if exists
        self.code_editor.delete(1.0, tk.END)
        if problem['id'] in self.results:
            self.code_editor.insert(tk.END, self.results[problem['id']]['code'])

    def auto_size_columns(self):
        """Auto-size columns and rows based on content"""
        # Calculate the required row height based on content
        max_lines = 1
        
        for child in self.test_tree.get_children():
            # Get all cell values for this row
            values = self.test_tree.item(child, 'values')
            
            # Calculate maximum number of lines in any cell
            for value in values:
                lines = str(value).count('\n') + 1
                if lines > max_lines:
                    max_lines = lines
        
        # Set row height based on content (minimum 30 pixels, +20 for each additional line)
        row_height = 30 + (max_lines - 1) * 20
        style = ttk.Style()
        style.configure('Treeview', rowheight=row_height)
        
        # Auto-size columns
        for col in ["input", "output", "expected"]:
            max_len = max([len(str(self.test_tree.set(child, col))) 
                         for child in self.test_tree.get_children()] or [0])
            # Set column width with some padding
            self.test_tree.column(col, width=min(400, max_len * 8 + 20))

    def prev_problem(self):
        """Navigate to previous problem"""
        self.save_current_code()
        self.show_problem(self.current_problem - 1)

    def next_problem(self):
        """Navigate to next problem"""
        self.save_current_code()
        self.show_problem(self.current_problem + 1)

    def save_current_code(self):
        """Save the current code to results"""
        problem_id = self.problems[self.current_problem]['id']
        code = self.code_editor.get(1.0, tk.END).strip()
        
        if problem_id not in self.results:
            self.results[problem_id] = {"code": code, "passed": False}
        else:
            self.results[problem_id]["code"] = code

    def run_tests(self):
        """Run all test cases for the current problem"""
        self.save_current_code()
        
        problem = self.problems[self.current_problem]
        problem_id = problem['id']
        student_code = self.code_editor.get(1.0, tk.END).strip()
        
        if not student_code:
            messagebox.showwarning("Warning", "Please write some code first")
            return
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            all_passed = True
            
            for i, test_case in enumerate(problem['test_cases']):
                temp_file = os.path.join(temp_dir, f"test_{problem_id}_{i}.py")
                
                # Create the test program
                with open(temp_file, "w") as f:
                    input_path = os.path.join(temp_dir, 'input.txt').replace('\\', '\\\\')
                    f.write(f"import sys\n")
                    f.write(f"sys.stdin = open(r'{input_path}', 'r')\n")
                    f.write(student_code + "\n")
                
                # Create input file
                with open(os.path.join(temp_dir, 'input.txt'), 'w') as f:
                    f.write(test_case['input'])
                
                # Execute the code
                try:
                    process = subprocess.Popen(
                        ['python', temp_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(timeout=5)
                    
                    if stderr:
                        raise Exception(stderr)
                    
                    # Normalize output for comparison
                    student_output = stdout.strip()
                    expected_output = test_case['output'].strip()
                    passed = student_output == expected_output
                    
                    # Update test case row
                    status = "✓ Passed" if passed else "✗ Failed"
                    fg_color = self.colors['success'] if passed else self.colors['error']
                    
                    self.test_tree.item(self.test_tree.get_children()[i], 
                                      values=(status, test_case['input'], student_output, expected_output))
                    self.test_tree.tag_configure(f"row{i}", foreground=fg_color)
                    self.test_tree.item(self.test_tree.get_children()[i], tags=(f"row{i}",))
                    
                    if not passed:
                        all_passed = False
                    
                except subprocess.TimeoutExpired:
                    self.test_tree.item(self.test_tree.get_children()[i], 
                                      values=("Timeout", test_case['input'], "", test_case['output']))
                    self.test_tree.tag_configure(f"row{i}", foreground=self.colors['warning'])
                    self.test_tree.item(self.test_tree.get_children()[i], tags=(f"row{i}",))
                    all_passed = False
                    process.kill()
                    
                except Exception as e:
                    self.test_tree.item(self.test_tree.get_children()[i], 
                                      values=("Error", test_case['input'], str(e), test_case['output']))
                    self.test_tree.tag_configure(f"row{i}", foreground=self.colors['error'])
                    self.test_tree.item(self.test_tree.get_children()[i], tags=(f"row{i}",))
                    all_passed = False
            
            # Auto-size columns after updating content
            self.auto_size_columns()
            
            # Update problem status
            self.results[problem_id]["passed"] = all_passed
            if all_passed:
                self.status_var.set(f"All test cases passed for Problem {problem_id}!")
                self.status_bar.configure(background=self.colors['success'], foreground='white')
            else:
                self.status_var.set(f"Some test cases failed for Problem {problem_id}")
                self.status_bar.configure(background=self.colors['error'], foreground='white')
            
            # Switch to test cases tab
            #self.notebook.select(2)
            
            # Reset status bar after 5 seconds
            self.root.after(5000, lambda: self.status_bar.configure(
                background=self.colors['background'], foreground=self.colors['text']))
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run tests:\n{str(e)}")
            self.status_bar.configure(background=self.colors['error'], foreground='white')
            self.root.after(5000, lambda: self.status_bar.configure(
                background=self.colors['background'], foreground=self.colors['text']))
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)

    def export_solutions(self):
        """Export all solutions to a zip file"""
        if not self.user_name:
            messagebox.showerror("Error", "Please enter your name first")
            return
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        export_dir = os.path.join(temp_dir, f"solutions_{self.user_name}")
        os.makedirs(export_dir)
        
        try:
            # Create solution files and results summary
            summary = []
            summary.append(f"Student Name: {self.user_name}")
            summary.append("\nProblem Results:")
            
            for problem in self.problems:
                problem_id = problem['id']
                filename = os.path.join(export_dir, f"problem_{problem_id}.py")
                
                # Write solution code
                with open(filename, "w") as f:
                    if problem_id in self.results:
                        f.write(self.results[problem_id]["code"])
                    else:
                        f.write("# No solution submitted for this problem\n")
                
                # Add to summary
                status = "PASSED" if problem_id in self.results and self.results[problem_id]["passed"] else "FAILED/MISSING"
                summary.append(f"Problem {problem_id}: {status}")
            
            # Write summary file
            with open(os.path.join(export_dir, "SUMMARY.txt"), "w") as f:
                f.write("\n".join(summary))
            
            # Ask for save location
            zip_filename = filedialog.asksaveasfilename(
                defaultextension=".zip",
                filetypes=[("ZIP files", "*.zip")],
                initialfile=f"solutions_{self.user_name}.zip"
            )
            
            if zip_filename:
                # Create zip file
                with zipfile.ZipFile(zip_filename, 'w') as zipf:
                    for root, dirs, files in os.walk(export_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), 
                                      os.path.relpath(os.path.join(root, file), export_dir))
                
                messagebox.showinfo("Success", f"Solutions exported to {zip_filename}")
                self.status_var.set(f"Solutions exported successfully!")
                self.status_bar.configure(background=self.colors['success'], foreground='white')
                self.root.after(3000, lambda: self.status_bar.configure(
                    background=self.colors['background'], foreground=self.colors['text']))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export solutions:\n{str(e)}")
            self.status_bar.configure(background=self.colors['error'], foreground='white')
            self.root.after(3000, lambda: self.status_bar.configure(
                background=self.colors['background'], foreground=self.colors['text']))
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = CodingCompetitionApp(root)
    root.mainloop()