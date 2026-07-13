import sys
import os

# Ensure Python knows where the package is
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from nyxx.main import run_cli

if __name__ == '__main__':
    run_cli()