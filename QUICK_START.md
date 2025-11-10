# 🚀 Quick Start Guide

## Getting Started in 3 Steps

### Step 1: Launch the System
```bash
python launcher.py
```

A window will appear with three role options.

### Step 2: Choose Your Role

#### Option A: I'm a Competitor
1. Click **"Join as Competitor"**
2. Enter your name
3. Click **"Start Competition"**
4. Start solving problems!

#### Option B: I'm a Judge
1. Click **"Open Judge Dashboard"**
2. Monitor all competitors in real-time
3. View detailed submissions and code
4. Track competition progress

#### Option C: I'm a Spectator
1. Click **"Open Spectator View"**
2. Watch the live leaderboard
3. See who's leading
4. View problem statistics

### Step 3: Use the Interface

## 💻 Competitor Workflow

1. **Read the problem** - Scroll through the description
2. **Write your code** - Use the code editor (auto-saves)
3. **Run tests** - Click "▶ Run Tests" to check your solution
4. **Submit** - Click "✓ Submit Solution" to record your attempt
5. **Navigate** - Use Previous/Next buttons to move between problems
6. **Export** - Click "📦 Export All Solutions" when done

### Tips for Competitors:
- ✅ Code auto-saves as you type
- ✅ Double-click test results for full details
- ✅ Green = Passed, Red = Failed
- ✅ You can revisit and resubmit problems
- ✅ Best submission is automatically tracked

## 👨‍⚖️ Judge Dashboard Guide

### Main View:
- **Top Statistics Cards** - Overview of competition
- **Competitors List** (left) - All participants
- **Details Panel** (right) - Selected competitor info

### Monitoring:
1. **Click a competitor** to see their details
2. **Problem Status Tab** - See which problems they've attempted
3. **Submission History Tab** - View all submissions chronologically
4. **Code View Tab** - Read their code for any problem

### Actions:
- 🔄 **Refresh Now** - Manual data update
- ✅ **Auto-refresh** - Toggle automatic updates (every 5s)
- 📊 **Export Report** - Generate competition report (coming soon)
- 🔄 **Reset Competition** - Clear all data (use carefully!)

### Status Indicators:
- 🟢 **Active** - Working now (last 5 minutes)
- 🟡 **Idle** - Inactive 5-30 minutes
- ⚪ **Inactive** - No activity >30 minutes

## 👥 Spectator View Guide

### What You'll See:
1. **Top 3 Podium** - Leading competitors with stats
2. **Full Leaderboard** - All participants ranked
3. **Problem Statistics** - Solve rates and attempts

### Understanding the Display:
- 🥇 🥈 🥉 - Top 3 positions
- **Solved** - Number of problems completed
- **Tests Passed** - Total test cases passed
- **Submissions** - Total attempts made
- **Current Problem** - What they're working on now

### Refresh:
- Updates automatically every 5 seconds
- Shows last update time in header

## 🎯 Common Scenarios

### Scenario 1: Running a Class Competition
1. Teacher opens **Judge Dashboard** on their computer
2. Teacher projects **Spectator View** on classroom screen
3. Students open **Competitor Interface** on their computers
4. Students enter their names and start
5. Teacher monitors via Judge Dashboard
6. Class watches progress on Spectator View

### Scenario 2: Testing Before Event
1. Open **Competitor Interface**
2. Enter test name (e.g., "Test User")
3. Try solving a problem
4. Open **Judge Dashboard** to verify tracking
5. Open **Spectator View** to check display
6. Verify data appears in all views

### Scenario 3: Multiple Competitors
1. Launch multiple **Competitor Interface** windows
2. Use different names for each
3. All data syncs automatically
4. Watch them appear in Judge/Spectator views

## ⚠️ Important Notes

### Do's:
✅ Keep all files in the same folder  
✅ Use unique competitor names  
✅ Let auto-refresh run in Judge/Spectator views  
✅ Export solutions before closing  

### Don'ts:
❌ Don't edit `competition_data.json` manually  
❌ Don't use the same name twice (unless continuing)  
❌ Don't delete files while system is running  
❌ Don't spam submit (it tracks everything!)  

## 🔧 Keyboard Shortcuts

### Competitor Interface:
- `Ctrl+S` - Auto-saves (happens automatically)
- `F5` - Run tests (use button instead)
- Double-click test result - View full details

### All Interfaces:
- `Alt+F4` - Close window
- Mouse wheel - Scroll content

## 📊 Understanding Test Results

### Status Icons:
- ✓ **Passed** - Correct output
- ✗ **Failed** - Wrong output  
- ⏱ **Timeout** - Too slow (>5 seconds)
- ✗ **Error** - Code crashed
- ⏳ **Not Run** - Not tested yet

### Test Details:
- **Input** - What was given to your code
- **Your Output** - What your code produced
- **Expected Output** - What was expected

## 🎨 Problem Difficulty

Problems are numbered 1-10:
- **1-3**: Easy (basic I/O, simple logic)
- **4-7**: Medium (loops, conditions, data structures)
- **8-10**: Hard (algorithms, optimization)

## 💡 Pro Tips

### For Competitors:
1. **Read carefully** - Understand the problem first
2. **Test with examples** - Use sample inputs
3. **Check edge cases** - What if input is 0? Negative?
4. **Submit often** - Best submission is tracked
5. **Move on** - Don't get stuck on one problem

### For Judges:
1. **Monitor activity** - Check Active/Idle status
2. **Review code** - Look at submitted solutions
3. **Track progress** - See who's stuck
4. **Encourage** - Competition is for learning!

### For Spectators:
1. **Watch the podium** - Top 3 changes live
2. **Check problem stats** - See what's hard
3. **Follow favorites** - Track specific competitors
4. **Enjoy the show** - It updates automatically!

## 🆘 Quick Fixes

### Window not opening?
→ Check terminal for errors  
→ Run: `python -m pip install Pillow`  
→ Try running file directly

### Data not showing?
→ Submit a solution first  
→ Wait for auto-refresh (5 seconds)  
→ Click "Refresh Now" in Judge view

### Can't submit?
→ Click "Start Competition" first  
→ Enter your name  
→ Write some code  
→ Run tests before submitting

### Tests failing?
→ Check output format (exact match required)  
→ Remove extra spaces/newlines  
→ Double-click test to see details

## 📞 Need Help?

1. Check the **README.md** for detailed info
2. Look at error messages in terminal
3. Review code comments in source files
4. Test with a simple problem first

---

**Ready to compete? Launch `launcher.py` and get started! 🚀**
