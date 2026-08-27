#!/usr/bin/env bash
# Sprawdza, że słownik reguł, schemat i profile mówią to samo.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$root/scripts/validate.py" "$@"
