import sys
import os

# Make sure the src directory is on the path so the package is findable
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
# Now import and run the package normally — the CLI lives in one place,
# nyxx.main.run_cli, shared with the `python -m src.nyxx.main` wrappers.
from nyxx.main import run_cli

if __name__ == '__main__':
    run_cli()
