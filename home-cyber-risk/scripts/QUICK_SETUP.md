# Quick Setup Guide - Windows Task Scheduler

## Method 1: PowerShell Script (Recommended)

### Step 1: Open PowerShell as Administrator

1. Press **Windows Key**
2. Type: `PowerShell`
3. **Right-click** on "Windows PowerShell"
4. Select **"Run as Administrator"**
5. Click "Yes" when prompted

### Step 2: Navigate and Run

```powershell
cd D:\software\home-cyber-risk
.\scripts\setup_windows_scheduler.ps1 -Schedule Weekly -Time 09:00 -DayOfWeek Monday
```

That's it! The task will be created automatically.

## Method 2: Task Scheduler GUI (No Admin Required)

### Step 1: Open Task Scheduler

Press **Windows Key**, type `taskschd.msc`, press Enter

### Step 2: Create Basic Task

1. Click **"Create Basic Task..."** in the right panel
2. **Name:** `HomeCyberRisk-BreachCheck`
3. **Description:** `Automated breach check for Home Cyber Risk Awareness Server`
4. Click **Next**

### Step 3: Set Trigger

1. **Trigger:** Weekly
2. Click **Next**
3. **Start:** Today's date
4. **Time:** 9:00 AM
5. **Recur every:** 1 weeks
6. **On:** Monday
7. Click **Next**

### Step 4: Set Action

1. **Action:** Start a program
2. Click **Next**
3. **Program/script:** `python`
   - (Or full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX\python.exe`)
4. **Add arguments:** `scripts\check_breaches.py`
5. **Start in:** `D:\software\home-cyber-risk`
6. Click **Next**

### Step 5: Finish

1. Check **"Open the Properties dialog..."**
2. Click **Finish**

### Step 6: Configure Properties

1. In the Properties window:
   - Check **"Run whether user is logged on or not"**
   - Check **"Run with highest privileges"** (optional)
   - Click **OK**
   - Enter your Windows password if prompted

## Verify Task is Created

```powershell
Get-ScheduledTask -TaskName "HomeCyberRisk-BreachCheck"
```

## Test the Task

```powershell
Start-ScheduledTask -TaskName "HomeCyberRisk-BreachCheck"
```

## Troubleshooting

**"Python not found" error:**
- Make sure Python is in your PATH
- Or use full path to Python in Task Scheduler

**Task doesn't run:**
- Check Task Scheduler History tab
- Verify Python path is correct
- Check "Start in" directory is correct

