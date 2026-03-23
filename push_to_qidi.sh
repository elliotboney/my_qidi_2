#!/bin/bash
# Push a local file back to the Qidi printer, with local backup first.
# Usage: ./push_to_qidi.sh <local_file>
# Example: ./push_to_qidi.sh printer_data/config/printer.cfg

set -euo pipefail

REMOTE_USER="mks"
REMOTE_HOST="qidi"
BACKUP_DIR="backups"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <local_file>"
    echo "Example: $0 printer_data/config/printer.cfg"
    exit 1
fi

LOCAL_FILE="$1"

if [ ! -f "$LOCAL_FILE" ]; then
    echo "Error: '$LOCAL_FILE' not found"
    exit 1
fi

# Build backup filename: backups/path/to/file.2026-03-22_143055.cfg
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
DIR=$(dirname "$LOCAL_FILE")
BASE=$(basename "$LOCAL_FILE")
EXT="${BASE##*.}"
NAME="${BASE%.*}"

if [ "$EXT" = "$BASE" ]; then
    # No extension
    BACKUP_FILE="$BACKUP_DIR/$DIR/${NAME}.${TIMESTAMP}"
else
    BACKUP_FILE="$BACKUP_DIR/$DIR/${NAME}.${TIMESTAMP}.${EXT}"
fi

# Determine remote path (local printer_data/ maps to ~/printer_data/ on printer)
REMOTE_PATH="${REMOTE_USER}@${REMOTE_HOST}:~/${LOCAL_FILE}"

# Backup the remote version first
mkdir -p "$(dirname "$BACKUP_FILE")"
echo "Backing up remote file to $BACKUP_FILE"
scp "${REMOTE_PATH}" "$BACKUP_FILE" 2>/dev/null || {
    echo "Warning: could not fetch remote file for backup (may not exist yet)"
}

# Push local file to printer
echo "Pushing $LOCAL_FILE -> ${REMOTE_PATH}"
rsync -avz "$LOCAL_FILE" "$REMOTE_PATH"

echo "Done."
