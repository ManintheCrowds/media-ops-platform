# PowerShell script to install the Arlo library with a workaround for Windows encoding issues

Write-Host "Installing Arlo library (Windows workaround)..." -ForegroundColor Yellow

$tempDir = Join-Path $env:TEMP "arlo-install"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Cloning repository..." -ForegroundColor Cyan
git clone https://github.com/jeffreydwalter/arlo.git $tempDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to clone Arlo repository."
    exit 1
}

Write-Host "Fixing encoding issues..." -ForegroundColor Cyan
$setupPyPath = Join-Path $tempDir "setup.py"
$readmePath = Join-Path $tempDir "README.md"

# Fix README.md encoding
if (Test-Path $readmePath) {
    try {
        $readmeContent = Get-Content $readmePath -Raw -Encoding UTF8
        $readmeContent | Set-Content $readmePath -Encoding UTF8 -NoNewline
        Write-Host "  -> README.md encoding fixed." -ForegroundColor Green
    } catch {
        # If UTF-8 read fails, try to read as bytes and convert
        $bytes = [System.IO.File]::ReadAllBytes($readmePath)
        $readmeContent = [System.Text.Encoding]::UTF8.GetString($bytes)
        [System.IO.File]::WriteAllText($readmePath, $readmeContent, [System.Text.Encoding]::UTF8)
        Write-Host "  -> README.md encoding fixed (byte conversion)." -ForegroundColor Green
    }
}

# Fix setup.py to use UTF-8 encoding
if (Test-Path $setupPyPath) {
    $content = Get-Content $setupPyPath -Raw -Encoding UTF8
    $content = $content -replace "with open\('README\.md', 'r'\) as f:", "with open('README.md', 'r', encoding='utf-8', errors='ignore') as f:"
    $content | Set-Content $setupPyPath -Encoding UTF8 -NoNewline
    Write-Host "  -> setup.py encoding fixed." -ForegroundColor Green
} else {
    Write-Warning "  -> setup.py not found in cloned repository. Skipping encoding fix."
}

Write-Host "Installing package..." -ForegroundColor Cyan
try {
    python -m pip install $tempDir
    Write-Host "[OK] Arlo library installed successfully." -ForegroundColor Green
} catch {
    Write-Error "Installation failed. Trying alternative method..."
    # Try editable install as a fallback
    try {
        python -m pip install -e $tempDir
        Write-Host "[OK] Arlo library installed in editable mode." -ForegroundColor Green
    } catch {
        Write-Error "Alternative installation also failed: $($_.Exception.Message)"
        exit 1
    }
}

# Clean up temporary directory
Remove-Item $tempDir -Recurse -Force

Write-Host "Done!" -ForegroundColor Green

