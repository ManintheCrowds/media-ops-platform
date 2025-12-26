# Simple wrapper script to run breach check
# Can be called directly or from Task Scheduler

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CheckScript = Join-Path $ScriptDir "check_breaches.py"

# Change to project directory
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir

# Run the check
python $CheckScript

# Exit with the same code
exit $LASTEXITCODE

