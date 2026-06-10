# Purge verified Adzuna secrets from git history
#
# APPROVAL_NEEDED: Rotate Adzuna API keys at the provider BEFORE running.
# APPROVAL_NEEDED: Force-push rewrites main — coordinate with collaborators.
#
# Prerequisites: pip install git-filter-repo
#
# Usage (from repo root, with a clean working tree):
#   1. Copy config/filter-repo-adzuna-replacements.txt to a local-only file with real literals.
#   2. git filter-repo --force --replace-text path/to/your-replacements.txt
#   3. git push --force-with-lease origin main
#   4. Re-run scheduled TruffleHog; confirm zero verified Adzuna hits.
#
# Paths historically flagged: job-automation-service/.env.backup (untracked on main; still in history).

Write-Host "Read config/filter-repo-adzuna-replacements.txt and docs/portfolio/GH-PF-03-security-scan.md"
Write-Host "Do not run filter-repo until Adzuna keys are rotated."
