# .env Files Setup Guide

## ✅ What's Been Done

1. **Created .env files** from .env.example templates
2. **Generated secure keys** automatically:
   - Main Platform: `SECRET_KEY` and `JWT_SECRET_KEY` 
   - Job Automation Service: `SECRET_KEY`

## 📝 Credentials You Need to Provide

### Main Platform (`D:\software\.env`)

**Already Set:**
- ✅ `SECRET_KEY` - Generated secure key
- ✅ `JWT_SECRET_KEY` - Generated secure key

**Need to Set (if applicable):**
- ⚠️ `ARLO_USERNAME` - Your Arlo camera account email (if using camera service)
- ⚠️ `ARLO_PASSWORD` - Your Arlo camera account password (if using camera service)
- ⚠️ `NOTIFICATION_EMAIL` - Email for notifications (default: utility@example.com)
- ⚠️ `DATABASE_URL` - PostgreSQL connection string (if different from default)
- ⚠️ `GRAFANA_PASSWORD` - Grafana admin password (if using monitoring)

### Job Automation Service (`D:\software\job-automation-service\.env`)

**Already Set:**
- ✅ `SECRET_KEY` - Generated secure key
- ✅ `OLLAMA_URL` - Default: http://localhost:11434
- ✅ `OLLAMA_MODEL` - Default: llama2
- ✅ `DEFAULT_LOCATION` - Default: Minneapolis, MN

**Need to Set:**
- ⚠️ `ADZUNA_API_ID` - Get from https://developer.adzuna.com/
- ⚠️ `ADZUNA_API_KEY` - Get from https://developer.adzuna.com/
- ⚠️ `JSEARCH_API_KEY` - Get from https://jsearch.app/
- ⚠️ `DATABASE_URL` - PostgreSQL connection string

## 🔧 How to Input Credentials

### Option 1: Interactive Script (Recommended)

Run the interactive setup script:

```powershell
cd D:\software
.\scripts\setup_env_credentials.ps1
```

This script will:
- Prompt you for each credential securely
- Hide passwords as you type
- Update the .env files automatically

### Option 2: Manual Edit

1. **Open the .env file:**
   ```powershell
   notepad D:\software\.env
   # or
   notepad D:\software\job-automation-service\.env
   ```

2. **Replace placeholder values:**
   - Find lines with `your-*-here` or `change-me-*`
   - Replace with your actual credentials
   - Save the file

### Option 3: PowerShell Direct Edit

```powershell
# Example: Set Adzuna API ID
$content = Get-Content D:\software\job-automation-service\.env -Raw
$content = $content -replace 'ADZUNA_API_ID=.*', 'ADZUNA_API_ID=your-actual-id'
Set-Content D:\software\job-automation-service\.env -Value $content -NoNewline
```

## 🔐 Security Notes

1. **Never commit .env files** - They're already in .gitignore
2. **Use secure passwords** - At least 32 characters for secret keys
3. **Rotate credentials regularly** - Especially if exposed
4. **Use different credentials** for dev/staging/production

## ✅ Verification

After setting up credentials, verify they're loaded:

```powershell
# Check main platform
cd D:\software
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('SECRET_KEY:', 'SET' if os.getenv('SECRET_KEY') else 'NOT SET')"

# Check job automation service
cd D:\software\job-automation-service
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('ADZUNA_API_KEY:', 'SET' if os.getenv('ADZUNA_API_KEY') else 'NOT SET')"
```

## 📚 Additional Resources

- See `CREDENTIAL_MANAGEMENT.md` for detailed best practices
- See service-specific README files for service configuration




