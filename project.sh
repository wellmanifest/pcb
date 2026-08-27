#!/usr/bin/env bash
# Entry point for wellmanifest/pcb domain pack validation & testing contracts.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cmd="${1:-check}"

case "$cmd" in
  check|validate)
    echo "[wellmanifest/pcb] Checking rule vocabulary, schema and example profiles..."
    "$repo_root/scripts/validate.sh"
    ;;
  digests)
    echo "[wellmanifest/pcb] Refreshing artifact digests in dsl-manifest.json..."
    python3 "$repo_root/scripts/validate.py" --refresh-digests
    ;;
  test)
    echo "[wellmanifest/pcb] Running the adopter contract suite..."
    if [ -n "${ADOPTER_DIR:-}" ] && [ -d "$ADOPTER_DIR" ]; then
      (cd "$ADOPTER_DIR" && python3 -m pytest -q tests/test_style.py)
    else
      echo "… ADOPTER_DIR nie ustawiony — pomijam testy adoptera"
    fi
    ;;
  *)
    echo "Usage: $0 [check|digests|test]"
    exit 1
    ;;
esac
