#!/bin/bash
# nyxx_run.sh
python3 -m nyxx.main --project-root "$(dirname "$(readlink -f "$0")")"