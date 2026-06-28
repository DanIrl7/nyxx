#!/bin/bash

# Navii Installation Script

# Determine the project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [ -d "$SCRIPT_DIR/.venv/Scripts" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/Scripts/python"
else
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
fi

# --- Step 1: Check Python and Virtual Environment ---
echo "Checking Python environment..."
PYTHON_COMMAND=""
if command -v python3 &> /dev/null; then
    PYTHON_COMMAND="python3"
elif command -v python &> /dev/null; then
    PYTHON_COMMAND="python"
else
    echo "Error: Python 3 is not installed or not in PATH. Please install Python 3."
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON_COMMAND -m venv "$SCRIPT_DIR/.venv" # Use the determined command
fi

echo "Activating virtual environment and installing dependencies..."
source "$SCRIPT_DIR/.venv/Scripts/activate" || { echo "Failed to activate venv. Ensure Python and venv are properly set up."; exit 1; }
pip install -r "$SCRIPT_DIR/requirements.txt" || { echo "Failed to install Python dependencies."; exit 1; }
echo "Python dependencies installed."

echo "Setting up Navii config directory..."
mkdir -p "$HOME/.navi"

if [ ! -f "$HOME/.navi/jumps.json" ]; then
    echo "[]" > "$HOME/.navi/jumps.json"
    echo "Created ~/.navi/jumps.json"
fi

if [ ! -f "$HOME/.navi/memos.json" ]; then
    echo "[]" > "$HOME/.navi/memos.json"
    echo "Created ~/.navi/memos.json"
fi


SHELL_NAME=$(basename "$SHELL")
CONFIG_FILE=""
NAV_SOURCE_LINE=""
NAV_FUNCTION_NAME="navi" 

case "$SHELL_NAME" in
    "bash")
        CONFIG_FILE="$HOME/.bashrc"
        NAV_SOURCE_LINE=""
        ;;
    "zsh")
        CONFIG_FILE="$HOME/.zshrc"
        NAV_SOURCE_LINE=""
        ;;
    "pwsh" | "powershell")

        echo "PowerShell detected. Please manually add the following to your \$PROFILE file (type 'notepad \$PROFILE' in PowerShell):"
        echo "  . '$(cygpath -w "$SCRIPT_DIR/shell_integrations/navi.ps1")'"
        echo "Then restart PowerShell or run '. \$PROFILE'"
        exit 0
        ;;
    *)
        echo "Unsupported shell: $SHELL_NAME. Please manually configure Navii."
        exit 1
        ;;
esac


if [ -n "$CONFIG_FILE" ]; then
    echo "Adding Navii function to $CONFIG_FILE..."
    CONFIG_BASENAME="$(basename "$CONFIG_FILE")"
    (
        cd "$HOME" || { echo "Error: Could not change to HOME directory for Bash/Zsh config."; exit 1; }
        if ! grep -qF "navi() {" "$CONFIG_BASENAME" 2>/dev/null; then
            echo -e "\n# Navii Integration" >> "$CONFIG_BASENAME"
            cat << EOF_NAVI_FUNCTION >> "$CONFIG_BASENAME"
navi() {
  # Interactive CLI subcommands (navi jump add / navi memo add) need the
  # terminal for input() prompts, so run them directly without capturing.
  if [[ "\$1" == "jump" && "\$2" == "add" ]] || [[ "\$1" == "memo" && "\$2" == "add" ]]; then
    PYTHONPATH="${SCRIPT_DIR}" "${PYTHON_BIN}" -m src.navii.main "\$@"
    return
  fi

  # TUI + lookup commands: capture only the final output line, then act on
  # its prefix. CD:/path -> cd ; EXEC:command -> eval ; bare path -> cd.
  local output
  output=\$(PYTHONPATH="${SCRIPT_DIR}" "${PYTHON_BIN}" -m src.navii.main "\$@" 2>/dev/null)
  if [[ -n "\$output" ]]; then
    case "\$output" in
      CD:*)   cd "\${output#CD:}" ;;
      EXEC:*) eval "\${output#EXEC:}" ;;
      *)      cd "\$output" ;;
    esac
  fi
}
EOF_NAVI_FUNCTION
            echo "Navii function added to $CONFIG_FILE."
            echo "Please restart your shell or run 'source $CONFIG_FILE' to enable Navii."
        else
            echo "Navii function already exists in $CONFIG_FILE. Skipping."
        fi
    )
fi

echo "Navii installation complete!"