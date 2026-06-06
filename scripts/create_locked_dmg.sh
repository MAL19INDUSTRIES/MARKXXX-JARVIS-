#!/usr/bin/env bash
# Creates an encrypted disk image for macOS users to store a single unlock.key file.
# Usage:
#   ./scripts/create_locked_dmg.sh ~/Jarvis_locked.dmg JARVIS_LOCKED
# The script will prompt you for a password to protect the disk image, then
# create an unlock.key file inside the mounted volume and print the secret.

set -euo pipefail
OUT=${1:-$HOME/Jarvis_locked.sparsebundle}
VOL_NAME=${2:-JARVIS_LOCKED}
SIZE=${3:-10m}

echo "This will create an encrypted disk image: $OUT"
read -p "Proceed? [y/N] " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

echo "Creating encrypted sparsebundle (you'll be prompted for a password)"
# create the encrypted image; will prompt for a password interactively
hdiutil create -encryption AES-256 -size "$SIZE" -volname "$VOL_NAME" -type SPARSEBUNDLE -fs HFS+ "$OUT"

echo "Mounting the image now..."
ATTACH_PATH="$OUT"
if [[ ! -e "$ATTACH_PATH" && -e "${OUT}.sparsebundle" ]]; then
  ATTACH_PATH="${OUT}.sparsebundle"
fi
hdiutil attach "$ATTACH_PATH"

SECRET=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)

echo "$SECRET" > "/Volumes/$VOL_NAME/unlock.key"
chmod 600 "/Volumes/$VOL_NAME/unlock.key"

echo "Created unlock key for volume /Volumes/$VOL_NAME/unlock.key"
echo
cat <<EOF
IMPORTANT:
  Set this secret in your shell before running JARVIS:
    export JARVIS_LOCKED_KEY_SECRET="$SECRET"
  Then run JARVIS with the locked volume name and your Gemini key:
    JARVIS_LOCKED_VOLUME="$VOL_NAME" \ 
      JARVIS_LOCKED_KEY_SECRET="$SECRET" \ 
      GEMINI_API_KEY="YOUR_KEY" python3 main.py
EOF

echo
printf "When ready, unmount with: hdiutil detach /Volumes/%s\n" "$VOL_NAME"

exit 0
