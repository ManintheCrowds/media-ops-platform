# Windows Setup Guide

## Scheduled Checks with Task Scheduler

### Quick Setup

1. **Open PowerShell as Administrator**
   - Right-click PowerShell
   - Select "Run as Administrator"

2. **Navigate to project directory**
   ```powershell
   cd D:\software\home-cyber-risk
   ```

3. **Run the setup script**
   ```powershell
   .\scripts\setup_windows_scheduler.ps1 -Schedule Weekly -Time 09:00 -DayOfWeek Monday
   ```

### Schedule Options

**Weekly (default):**
```powershell
.\scripts\setup_windows_scheduler.ps1 -Schedule Weekly -Time 09:00 -DayOfWeek Monday
```

**Daily:**
```powershell
.\scripts\setup_windows_scheduler.ps1 -Schedule Daily -Time 09:00
```

**Custom:**
For custom schedules, use the Task Scheduler GUI:
1. Open `taskschd.msc`
2. Find task: `HomeCyberRisk-BreachCheck`
3. Edit trigger settings

### Managing the Scheduled Task

**View task:**
```powershell
Get-ScheduledTask -TaskName "HomeCyberRisk-BreachCheck"
```

**Run task immediately:**
```powershell
Start-ScheduledTask -TaskName "HomeCyberRisk-BreachCheck"
```

**Remove task:**
```powershell
Unregister-ScheduledTask -TaskName "HomeCyberRisk-BreachCheck" -Confirm:$false
```

**View task history:**
1. Open Task Scheduler (`taskschd.msc`)
2. Find `HomeCyberRisk-BreachCheck`
3. Click "History" tab

### Manual Check

Run checks manually anytime:
```powershell
cd D:\software\home-cyber-risk
python scripts/check_breaches.py
```

Or use the wrapper script:
```powershell
.\scripts\run_breach_check.ps1
```

## Observability Stack

### Starting Services

```powershell
cd D:\software\home-cyber-risk\infra
docker-compose up -d grafana loki
```

### Accessing Grafana

1. Open browser: http://localhost:3000
2. Login:
   - Username: `admin`
   - Password: `admin` (change on first login)
3. Configure Loki data source:
   - Go to Configuration → Data Sources
   - Add Loki data source
   - URL: `http://loki:3100`
   - Click "Save & Test"

### Viewing Logs

1. In Grafana, go to Explore
2. Select Loki data source
3. Query: `{job="breach-monitor"}`
4. View breach check logs in real-time

### Stopping Services

```powershell
cd D:\software\home-cyber-risk\infra
docker-compose down
```

## Troubleshooting

### Task Scheduler Issues

**Task not running:**
- Check if Python is in PATH: `python --version`
- Verify script path is correct
- Check Task Scheduler history for errors
- Ensure task is enabled (not disabled)

**Permission errors:**
- Run PowerShell as Administrator
- Check file permissions on `scripts/check_breaches.py`

### Docker Issues

**Services not starting:**
```powershell
docker-compose logs grafana loki
```

**Port conflicts:**
- Grafana uses port 3000
- Loki uses port 3100
- Change ports in `docker-compose.yml` if needed

**Container not found:**
```powershell
docker-compose ps
docker-compose up -d grafana loki
```

## Next Steps

1. Add HIBP API key to `.env` for full email/username checking
2. Configure alert channels (email/Telegram) in `.env`
3. Set up Grafana dashboard (import `config/grafana-dashboard.json`)
4. Review logs regularly in Grafana

