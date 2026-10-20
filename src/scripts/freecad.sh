#!/usr/bin/env bash
# Run FreeCAD in console mode with the repository accessible.
#
#   src/scripts/freecad.sh src/scripts/cad/generate_cad.py
#
# Prefers a native `FreeCADCmd` binary and falls back to the user level
# Flatpak installation used by this project.  The flatpak sandbox needs
# explicit access to the repository volume:
#
#   flatpak override --user --filesystem=/media --filesystem=/run/media org.freecad.FreeCAD
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if command -v FreeCADCmd >/dev/null 2>&1; then
    exec FreeCADCmd "$@"
fi

if command -v freecadcmd >/dev/null 2>&1; then
    exec freecadcmd "$@"
fi

if flatpak list --user --app 2>/dev/null | grep -q "org.freecad.FreeCAD"; then
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
        --command=FreeCADCmd org.freecad.FreeCAD "${ARGS[@]}"
fi

echo "error: no FreeCAD installation found." >&2
echo "  install with: flatpak install -y --user flathub org.freecad.FreeCAD" >&2
exit 1
