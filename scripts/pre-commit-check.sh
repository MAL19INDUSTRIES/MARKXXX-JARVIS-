#!/bin/bash
# Pre-commit hook: scan staged files for API keys or secrets.
#
# Install:  ln -s ../../scripts/pre-commit-check.sh .git/hooks/pre-commit
# Or copy:  cp scripts/pre-commit-check.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

set -euo pipefail

RED='\033[0;31m'
YEL='\033[1;33m'
NC='\033[0m' # No Color

# Patterns that look like a Gemini / generic Google API key
GEMINI_PATTERN='AIza[0-9A-Za-z\-_]{35}'
# Generic-looking key= patterns that might be secrets
SECRET_PATTERNS=(
    'GEMINI_API_KEY\s*=\s*[A-Za-z0-9_\-]{20,}'
    'api_key\s*=\s*["'"'"'][A-Za-z0-9_\-]{20,}["'"'"']'
)

# Files that should NEVER be committed
BLOCKED_FILES=(
    ".env"
    "config/api_keys.json"
    "memory/long_term.json"
)

found=0

echo "🔍 Scanning staged changes for secrets..."

# Check for blocked files. Deletions are allowed so previously committed
# local-secret files can be removed from the repository.
for blocked in "${BLOCKED_FILES[@]}"; do
    if git diff --cached --name-status | grep -qE "^[AMCRTU][[:space:]]+$blocked$"; then
        echo -e "${RED}❌ BLOCKED: $blocked is in the commit. This file contains secrets and must not be committed.${NC}"
        echo "   Run: git reset HEAD $blocked"
        found=1
    fi
done

# Check staged diff for key patterns
if git diff --cached -U0 | grep -qE "$GEMINI_PATTERN"; then
    echo -e "${RED}❌ DETECTED: Gemini/Google API key pattern (AIza...) found in staged diff.${NC}"
    found=1
fi

for pattern in "${SECRET_PATTERNS[@]}"; do
    if git diff --cached -U0 | grep -qE "$pattern"; then
        echo -e "${RED}❌ DETECTED: Potential secret pattern: $pattern${NC}"
        found=1
    fi
done

if [ "$found" -eq 1 ]; then
    echo ""
    echo -e "${RED}═══════════════════════════════════════════${NC}"
    echo -e "${RED}  COMMIT BLOCKED — secrets detected above  ${NC}"
    echo -e "${RED}═══════════════════════════════════════════${NC}"
    exit 1
fi

echo "✅ No secrets found — commit allowed."
exit 0
