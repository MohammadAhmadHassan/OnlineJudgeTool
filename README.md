# 🏆 Python Coding Competition System

A comprehensive competition management system with separate interfaces for competitors, judges, and spectators.

## 📋 Features

### 🎯 Three Distinct Interfaces

#### 💻 Competitor Interface
- **Clean, modern UI** with resizable panels
- **Problem navigation** with status indicators
- **Integrated code editor** with auto-save
- **Real-time test execution** with detailed feedback
- **Solution submission** tracking
- **Export functionality** for all solutions

#### 👨‍⚖️ Judge Dashboard
- **Real-time monitoring** of all competitors
- **Live statistics** (total competitors, active users, submissions)
- **Detailed competitor view** with:
  - Problem-by-problem status
  - Submission history
  - Code viewer
- **Auto-refresh** every 5 seconds
- **Search and filter** capabilities
- **Competition reset** functionality

#### 👥 Spectator Dashboard
- **Live leaderboard** with rankings
- **Podium display** for top 3 competitors
- **Problem statistics** (solve rates, attempts)
- **Auto-refresh** for real-time updates
- **Public-facing view** with no editing capabilities

## 🚀 Quick Start

### 1. Launch the System

Run the main launcher:
```bash
python launcher.py
```

### 2. Select Your Role

Choose from:
- **Competitor** - Participate and solve problems
- **Judge** - Monitor and manage the competition
- **Spectator** - Watch the competition live

### 3. Multiple Windows

You can open multiple windows simultaneously:
- Multiple competitor windows (different participants)
- Multiple judge dashboards
- Multiple spectator views

All windows share the same data in real-time!

## 📁 File Structure

```
problemSolvingTool/
│
├── launcher.py                    # Main entry point - role selection
├── competitor_interface.py        # Competitor view
├── judge_dashboard.py            # Judge monitoring dashboard
├── spectator_dashboard.py        # Public spectator view
├── competition_data_manager.py   # Shared data management
├── VirtualCompetitionTool.py     # Original tool (legacy)
│
├── problems/                     # Problem definitions
│   ├── problem1.json
│   ├── problem2.json
│   └── ...
│
└── competition_data.json         # Live competition data (auto-created)
```

## 📊 Data Management

### Shared Data Store
- **JSON-based storage** (`competition_data.json`)
- **Thread-safe operations**
- **Real-time synchronization** across all interfaces
- **Automatic persistence**

### Tracked Information
- Competitor names and join times
- Current problem being viewed
- All submissions with timestamps
- Test results for each submission
- Best submission for each problem
- Activity timestamps

## 🎨 UI Improvements

### Fixed Issues
✅ Removed janky tab-based navigation  
✅ Added resizable panels with sash controls  
✅ Improved color scheme and visual hierarchy  
✅ Better spacing and padding  
✅ Responsive layout that adapts to window size  
✅ Status indicators with color coding  
✅ Auto-save functionality  
✅ Smooth scrolling in all views  

### Visual Enhancements
- Modern color palette
- Icon-based navigation
- Status badges (✓ ✗ ⏳ ○ ◐)
- Rank medals (🥇 🥈 🥉)
- Real-time activity indicators
- Podium display for top 3

## 🔧 Technical Details

### Requirements
- Python 3.7+
- tkinter (included with Python)
- Pillow (automatically installed)

### Architecture
```
┌─────────────┐
│  Launcher   │
└──────┬──────┘
       │
       ├──────────────┬──────────────┬
       │              │              │
┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
│ Competitor  │ │  Judge   │ │ Spectator  │
│ Interface   │ │Dashboard │ │ Dashboard  │
└──────┬──────┘ └────┬─────┘ └─────┬──────┘
       │              │              │
       └──────────────┴──────────────┘
                      │
              ┌───────▼───────┐
              │  Data Manager │
              │ (JSON Store)  │
              └───────────────┘
```

### Data Flow
1. Competitors submit solutions
2. Data Manager saves to JSON
3. Judge/Spectator dashboards auto-refresh
4. All views stay synchronized

## 📝 Problem Format

Problems are stored as JSON files:

```json
{
  "title": "Problem Title",
  "description": "Problem description...",
  "test_cases": [
    {
      "input": "test input",
      "output": "expected output"
    }
  ]
}
```

## 🎯 Usage Scenarios

### 1. Classroom Competition
- Teacher opens **Judge Dashboard**
- Projects **Spectator View** on screen
- Students open **Competitor Interface**
- Live monitoring and leaderboard display

### 2. Coding Event
- Event organizer manages via **Judge Dashboard**
- Public **Spectator View** on display screens
- Participants compete via **Competitor Interface**

### 3. Practice Mode
- Individual opens **Competitor Interface**
- Self-monitor via **Judge Dashboard**
- Track progress over time

## 🔒 Security Notes

- No authentication (designed for trusted environments)
- Data stored locally in JSON
- Competitor names should be unique
- No network functionality (all local)

## 🐛 Troubleshooting

### "competitor_interface.py not found"
- Ensure all files are in the same directory
- Run from the correct folder

### "Import PIL could not be resolved"
- Pillow should auto-install
- Manual install: `pip install Pillow`

### Windows not opening
- Check console for error messages
- Ensure Python is properly installed
- Try running individual files directly

### Data not syncing
- Check `competition_data.json` exists
- Verify file permissions
- Close and restart all windows

## 🎨 Customization

### Colors
Edit the `colors` dictionary in each file:
```python
self.colors = {
    'primary': '#2c3e50',
    'secondary': '#3498db',
    'success': '#27ae60',
    # ... more colors
}
```

### Refresh Rate
Change auto-refresh interval (milliseconds):
```python
# In judge_dashboard.py or spectator_dashboard.py
self.root.after(5000, self.refresh_data)  # 5000ms = 5 seconds
```

### Problem Count
Adjust the problem loading range:
```python
# In competitor_interface.py
for i in range(1, 11):  # Loads problems 1-10
```

## 📈 Future Enhancements

Potential additions:
- [ ] Export detailed reports
- [ ] Time tracking per problem
- [ ] Difficulty ratings
- [ ] Hints system
- [ ] Chat/messaging
- [ ] Authentication
- [ ] Network mode
- [ ] Database backend
- [ ] Code plagiarism detection
- [ ] Automated judging

## 📄 License

This project is created for educational purposes.

## 🤝 Contributing

Feel free to enhance and customize for your needs!

## 📧 Support

For issues or questions, refer to the code comments or documentation.

---

**Made with ❤️ for The Geek Academy**
