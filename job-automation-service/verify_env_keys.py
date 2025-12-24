"""Verify and help add API keys to .env file."""

import sys
from pathlib import Path
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

env_file = Path("C:/Users/artin/software/.env")

if not env_file.exists():
    print(f"[ERROR] .env file not found at {env_file}")
    exit(1)

print(f"[OK] Found .env file at {env_file}")
print()

# Read the file
with open(env_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Check for keys
has_adzuna_id = 'ADZUNA_API_ID' in content
has_adzuna_key = 'ADZUNA_API_KEY' in content
has_jsearch = 'JSEARCH_API_KEY' in content

print("Current .env file status:")
print(f"  ADZUNA_API_ID: {'[OK] Found' if has_adzuna_id else '[MISSING] Not found'}")
print(f"  ADZUNA_API_KEY: {'[OK] Found' if has_adzuna_key else '[MISSING] Not found'}")
print(f"  JSEARCH_API_KEY: {'[OK] Found' if has_jsearch else '[MISSING] Not found'}")
print()

if not (has_adzuna_id and has_adzuna_key and has_jsearch):
    print("To add the missing keys, add these lines to your .env file:")
    print("  (Located at: C:\\Users\\artin\\software\\.env)")
    print()
    if not has_adzuna_id:
        print("  ADZUNA_API_ID=your_adzuna_api_id_here")
    if not has_adzuna_key:
        print("  ADZUNA_API_KEY=your_adzuna_api_key_here")
    if not has_jsearch:
        print("  JSEARCH_API_KEY=your_jsearch_api_key_here")
    print()
    print("After adding the keys, run the test again.")
else:
    print("[SUCCESS] All API keys are present in .env file!")
    print()
    print("If keys are still not loading, check:")
    print("  1. No extra spaces around the = sign")
    print("  2. No quotes around the values (unless needed)")
    print("  3. Values are on the same line as the key")

