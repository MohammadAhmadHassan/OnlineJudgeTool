# -*- coding: utf-8 -*-
"""
Competition System Launcher
Main entry point for the competition system - allows users to choose their role
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from data_manager import create_data_manager


class CompetitionLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Coding Competition - Role Selection")
        # Start maximized to fit window
        self.root.state('zoomed')
        self.root.resizable(True, True)
        
        # Colors
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'success': '#27ae60',
            'competitor': '#3498db',
            'judge': '#e74c3c',
            'spectator': '#9b59b6',
            'light': '#ecf0f1',
            'background': '#ffffff'
        }
        
        # Configure styles
        self.configure_styles()
        
        # Create widgets
        self.create_widgets()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame styles
        style.configure('TFrame', background=self.colors['background'])
        style.configure('Header.TFrame', background=self.colors['primary'])
        style.configure('Card.TFrame', background=self.colors['light'],
                       relief='raised', borderwidth=2)
        
        # Label styles
        style.configure('Header.TLabel', font=('Segoe UI', 24, 'bold'),
                       foreground='white', background=self.colors['primary'])
        style.configure('SubHeader.TLabel', font=('Segoe UI', 11),
                       foreground='white', background=self.colors['primary'])
        style.configure('CardTitle.TLabel', font=('Segoe UI', 16, 'bold'),
                       background=self.colors['light'])
        style.configure('CardDesc.TLabel', font=('Segoe UI', 10),
                       background=self.colors['light'], foreground='#6c757d')
        
        # Button styles for each role
        for role, color in [('Competitor', self.colors['competitor']),
                           ('Judge', self.colors['judge']),
                           ('Spectator', self.colors['spectator'])]:
            style.configure(f'{role}.TButton', 
                          font=('Segoe UI', 12, 'bold'),
                          padding=15,
                          background=color)
            style.map(f'{role}.TButton',
                     background=[('active', color), ('pressed', color)])
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Check database connection
        self.check_database_connection()
        
        # Main container with center alignment
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Center frame to hold all content
        center_frame = ttk.Frame(main_container)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Header
        self.create_header(center_frame)
        
        # Content
        content = ttk.Frame(center_frame)
        content.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Role selection cards
        self.create_role_cards(content)
        
        # Footer
        self.create_footer(center_frame)
    
    def check_database_connection(self):
        """Check and display database connection status"""
        try:
            dm = create_data_manager()
            backend_type = dm.get_backend_type()
            
            if backend_type == "firebase":
                print("[OK] Using Firebase Firestore for multi-device synchronization")
            else:
                print("[INFO] Using local JSON storage (single device)")
                print("  To enable multi-device support, configure Firebase credentials")
        except Exception as e:
            print(f"[WARNING] Database initialization warning: {e}")
    
    def create_header(self, parent):
        """Create header section"""
        header = ttk.Frame(parent, style='Header.TFrame')
        header.pack(fill=tk.X)
        
        header_content = ttk.Frame(header, style='Header.TFrame')
        header_content.pack(pady=30)
        
        ttk.Label(header_content, text="🏆 Python Coding Competition",
                 style='Header.TLabel').pack()
        
        ttk.Label(header_content, text="Select your role to continue",
                 style='SubHeader.TLabel').pack(pady=(10, 0))
    
    def create_role_cards(self, parent):
        """Create role selection cards"""
        roles = [
            {
                'title': '💻 Competitor',
                'icon': '💻',
                'description': 'Participate in the competition\nSolve problems and submit solutions',
                'button_text': 'Join as Competitor',
                'button_style': 'Competitor.TButton',
                'command': self.launch_competitor,
                'color': self.colors['competitor']
            },
            {
                'title': '👨‍⚖️ Judge',
                'icon': '👨‍⚖️',
                'description': 'Monitor the competition\nTrack competitors and submissions',
                'button_text': 'Open Judge Dashboard',
                'button_style': 'Judge.TButton',
                'command': self.launch_judge,
                'color': self.colors['judge']
            },
            {
                'title': '👥 Spectator',
                'icon': '👥',
                'description': 'Watch the competition live\nView leaderboard and statistics',
                'button_text': 'Open Spectator View',
                'button_style': 'Spectator.TButton',
                'command': self.launch_spectator,
                'color': self.colors['spectator']
            }
        ]
        
        for i, role in enumerate(roles):
            card = self.create_role_card(parent, role)
            card.pack(fill=tk.X, pady=10)
    
    def create_role_card(self, parent, role_info):
        """Create a single role selection card"""
        card = ttk.Frame(parent, style='Card.TFrame')
        
        content = ttk.Frame(card, style='Card.TFrame')
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left side: Icon and text
        left_frame = ttk.Frame(content, style='Card.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Icon and title
        title_frame = ttk.Frame(left_frame, style='Card.TFrame')
        title_frame.pack(anchor=tk.W)
        
        icon_label = ttk.Label(title_frame, text=role_info['icon'],
                              font=('Segoe UI', 20),
                              background=self.colors['light'])
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = ttk.Label(title_frame, text=role_info['title'],
                               style='CardTitle.TLabel',
                               foreground=role_info['color'])
        title_label.pack(side=tk.LEFT)
        
        # Description
        desc_label = ttk.Label(left_frame, text=role_info['description'],
                              style='CardDesc.TLabel', justify=tk.LEFT)
        desc_label.pack(anchor=tk.W, pady=(10, 0))
        
        # Right side: Button
        button = ttk.Button(content, text=role_info['button_text'],
                           style=role_info['button_style'],
                           command=role_info['command'])
        button.pack(side=tk.RIGHT, padx=(20, 0))
        
        return card
    
    def create_footer(self, parent):
        """Create footer"""
        footer = ttk.Frame(parent)
        footer.pack(fill=tk.X, pady=15)
        
        ttk.Label(footer, text="© 2025 The Geek Academy",
                 font=('Segoe UI', 9), foreground='#6c757d').pack()
        
        ttk.Label(footer, text="Multiple windows can be opened simultaneously",
                 font=('Segoe UI', 8, 'italic'), foreground='#95a5a6').pack()
    
    def launch_competitor(self):
        """Launch competitor interface"""
        try:
            # Check if file exists
            if not os.path.exists('competitor_interface.py'):
                messagebox.showerror("Error", 
                    "competitor_interface.py not found!\n\n"
                    "Please ensure all files are in the same directory.")
                return
            
            # Launch in new process
            if sys.platform == 'win32':
                subprocess.Popen([sys.executable, 'competitor_interface.py'],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, 'competitor_interface.py'])
            
            messagebox.showinfo("Launched", 
                "✓ Competitor interface launched!\n\n"
                "The competitor window should open shortly.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch competitor interface:\n{str(e)}")
    
    def launch_judge(self):
        """Launch judge dashboard"""
        try:
            # Check if file exists
            if not os.path.exists('judge_dashboard.py'):
                messagebox.showerror("Error", 
                    "judge_dashboard.py not found!\n\n"
                    "Please ensure all files are in the same directory.")
                return
            
            # Launch in new process
            if sys.platform == 'win32':
                subprocess.Popen([sys.executable, 'judge_dashboard.py'],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, 'judge_dashboard.py'])
            
            messagebox.showinfo("Launched", 
                "✓ Judge dashboard launched!\n\n"
                "The judge window should open shortly.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch judge dashboard:\n{str(e)}")
    
    def launch_spectator(self):
        """Launch spectator view"""
        try:
            # Check if file exists
            if not os.path.exists('spectator_dashboard.py'):
                messagebox.showerror("Error", 
                    "spectator_dashboard.py not found!\n\n"
                    "Please ensure all files are in the same directory.")
                return
            
            # Launch in new process
            if sys.platform == 'win32':
                subprocess.Popen([sys.executable, 'spectator_dashboard.py'],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, 'spectator_dashboard.py'])
            
            messagebox.showinfo("Launched", 
                "✓ Spectator view launched!\n\n"
                "The spectator window should open shortly.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch spectator view:\n{str(e)}")


def main():
    root = tk.Tk()
    app = CompetitionLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
