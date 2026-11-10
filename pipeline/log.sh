#!/bin/sh
# Append one build log row stamped from the real clock (UTC equals Europe/London in November).
# Usage: sh pipeline/log.sh "Type" "Entry text"
cd "$(dirname "$0")/.." && printf '| %s | %s | %s |\n' "$(date -u +%H:%M)" "$1" "$2" >> BUILD_LOG.md
