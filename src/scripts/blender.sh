#!/usr/bin/env bash
# Run Blender in background mode with the repository accessible.
#
#   src/scripts/blender.sh --background --python src/scripts/generate_temple.py -- --variant exterior
#
# The wrapper prefers a native `blender` binary and falls back to the
# user-level Flatpak installation used by this project.  The flatpak
# sandbox needs explicit access to the repository volume, which is granted
# once with:
#
#   flatpak override --user --filesystem=/media --filesystem=/run/media org.blender.Blender
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if command -v blender >/dev/null 2>&1; then
    exec blender "$@"
fi

if flatpak list --user --app 2>/dev/null | grep -q "org.blender.Blender"; then
    # The flatpak sandbox starts in /app/blender, so every path argument is
    # resolved against the directory the user invoked the script from.
    CALLER_DIR="$PWD"
    ARGS=()
    for arg in "$@"; do
        case "$arg" in
            -*) ARGS+=("$arg") ;;
            /*)  ARGS+=("$arg") ;;
            */*)  ARGS+=("${arg/#/${CALLER_DIR}/}") ;;
            *)    ARGS+=("$arg") ;;
        esac
    done
    exec flatpak run \
        --filesystem="/run/media" \
        --filesystem="/media" \
        --env=LC_ALL=C.UTF-8 \
        --command=blender org.blender.Blender "${ARGS[@]}"
fi

echo "error: no Blender installation found." >&2
echo "  install with: flatpak install -y --user flathub org.blender.Blender" >&2
echo "  then grant access: flatpak override --user --filesystem=/media --filesystem=/run/media org.blender.Blender" >&2
exit 1
