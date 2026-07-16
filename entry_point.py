import sys
import os

# Make sure the src directory is on the path so the package is findable
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
# Now import and run the package normally
from nyxx.main import run_tui
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Nyxx terminal navigator")
    parser.add_argument(
        "subcommand",
        nargs="?",
        default="home",
        choices=["home", "cd", "jump", "memo", "theme"]
    )
    parser.add_argument("name", nargs="?", default=None)
    args = parser.parse_args()

    # Handle direct CLI lookups
    if args.name and args.name != "add":
        if args.subcommand == "jump":
            from nyxx.jumpstore import find_jump
            import os
            entry = find_jump(args.name)
            if entry:
                print("CD:" + os.path.expanduser(entry["path"]), flush=True)
            else:
                print(f"nyxx: no jump named '{args.name}'", file=sys.stderr)
                sys.exit(1)
        elif args.subcommand == "memo":
            from nyxx.memostore import find_memo
            entry = find_memo(args.name)
            if entry:
                print("EXEC:" + entry["cmd"], flush=True)
            else:
                print(f"nyxx: no memo named '{args.name}'", file=sys.stderr)
                sys.exit(1)
        sys.exit(0)

    # Handle add subcommand
    if args.name == "add":
        if args.subcommand == "jump":
            from nyxx.jumpstore import add_jump
            name = input("Jump name: ").strip()
            desc = input("Description: ").strip()
            path = input("Path (leave blank for current dir): ").strip()
            if not path:
                path = os.getcwd()
            success, err = add_jump(name, desc, path)
            print(f"Jump '{name}' saved." if success else f"Error: {err}")
        elif args.subcommand == "memo":
            from nyxx.memostore import add_memo
            name = input("Memo name: ").strip()
            desc = input("Description: ").strip()
            cmd  = input("Command: ").strip()
            success, err = add_memo(name, desc, cmd)
            print(f"Memo '{name}' saved." if success else f"Error: {err}")
        sys.exit(0)

    state_map = {
        "home": "home", "cd": "nav",
        "jump": "jump", "memo": "memo", "theme": "theme"
    }
    run_tui(state_map[args.subcommand])