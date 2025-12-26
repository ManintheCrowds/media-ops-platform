#!/bin/bash
# Setup cron job for breach checking
# Run this script to install a cron job that checks for breaches periodically

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CHECK_SCRIPT="$SCRIPT_DIR/check_breaches.py"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
fi

# Default cadence: weekly (168 hours = 7 days)
CADENCE=${CHECK_CADENCE:-168}
CRON_SCHEDULE="0 0 * * 0"  # Weekly on Sunday at midnight

# Convert hours to cron schedule if needed
if [ "$CADENCE" -lt 24 ]; then
    # Daily or more frequent
    HOURS=$((CADENCE % 24))
    CRON_SCHEDULE="0 $HOURS * * *"
elif [ "$CADENCE" -lt 168 ]; then
    # Multiple times per week
    DAYS=$((CADENCE / 24))
    CRON_SCHEDULE="0 0 */$DAYS * *"
fi

# Create cron job
CRON_JOB="$CRON_SCHEDULE cd $PROJECT_DIR && python3 $CHECK_SCRIPT >> /var/log/breach-monitor.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$CHECK_SCRIPT"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$CHECK_SCRIPT" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job installed:"
echo "  Schedule: $CRON_SCHEDULE"
echo "  Script: $CHECK_SCRIPT"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"

