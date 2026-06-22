#!/bin/bash
# navii_run.sh
python3 -m navii.main --project-root "$(dirname "$(readlink -f "$0")")"