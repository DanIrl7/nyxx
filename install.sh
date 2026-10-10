#!/bin/bash

# Nyxx Installation Script

# ── Project root ───────────────────────────────────────────────────────────
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# ── Detect Python binary ───────────────────────────────────────────────────
# Needs 3.10+ (Pillow 12 requires it). Plain `python3` can be older — e.g.
# the one macOS ships is 3.9 — so also look for a newer versioned binary.
echo "Checking Python environment..."
PYTHON_COMMAND=""
for candidate in python3 python3.14 python3.13 python3.12 python3.11 python3.10 python; do
    if command -v "$candidate" &> /dev/null &&
       "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 10))' &> /dev/null; then
        PYTHON_COMMAND="$candidate"
        break
    fi
done
if [ -z "$PYTHON_COMMAND" ]; then
    echo "Error: Nyxx needs Python 3.10 or newer, and none was found in PATH."
    echo "       (macOS's built-in python3 is 3.9; install a newer one, e.g. 'brew install python'.)"
    exit 1
fi

# ── Create venv if missing ─────────────────────────────────────────────────
# Checks for the activate script rather than the folder: a venv whose
# creation failed partway (e.g. no python3-venv on Debian/Ubuntu) leaves
# a .venv folder without one, which would otherwise block every rerun.
if [ ! -f "$SCRIPT_DIR/.venv/bin/activate" ] && [ ! -f "$SCRIPT_DIR/.venv/Scripts/activate" ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON_COMMAND" -m venv --clear "$SCRIPT_DIR/.venv" || {
        echo "Error: Failed to create the virtual environment."
        echo "       On Debian/Ubuntu, install the venv module first: sudo apt install python3-venv"
        exit 1
    }
fi

# ── Resolve venv paths (Windows vs Unix) ──────────────────────────────────
if [ -f "$SCRIPT_DIR/.venv/Scripts/activate" ]; then
    # Windows (Git Bash / MSYS2)
    ACTIVATE="$SCRIPT_DIR/.venv/Scripts/activate"
    PYTHON_BIN="$SCRIPT_DIR/.venv/Scripts/python"
else
    # Linux / macOS
    ACTIVATE="$SCRIPT_DIR/.venv/bin/activate"
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
fi

# ── Activate and install dependencies ─────────────────────────────────────
echo "Activating virtual environment and installing dependencies..."
# shellcheck source=/dev/null
source "$ACTIVATE" || {
    echo "Error: Failed to activate virtual environment."
    echo "       Expected activation script at: $ACTIVATE"
    exit 1
}

pip install -r "$SCRIPT_DIR/requirements.txt" || {
    echo "Error: Failed to install Python dependencies."
    exit 1
}
echo "✓ Python dependencies installed."

# ── Seed ~/.nyxx config directory ─────────────────────────────────────────
echo "Setting up Nyxx config directory..."
mkdir -p "$HOME/.nyxx"

if [ ! -f "$HOME/.nyxx/jumps.json" ]; then
    echo "[]" > "$HOME/.nyxx/jumps.json"
    echo "✓ Created ~/.nyxx/jumps.json"
fi

if [ ! -f "$HOME/.nyxx/memos.json" ]; then
    echo "[]" > "$HOME/.nyxx/memos.json"
    echo "✓ Created ~/.nyxx/memos.json"
fi

if [ ! -f "$HOME/.nyxx/config.json" ]; then
    cat > "$HOME/.nyxx/config.json" << 'EOF_CONFIG'
{
  "sky_theme": "starry night",
  "ground_theme": "city",
  "sky_enabled": true,
  "ground_enabled": true
}
EOF_CONFIG
    echo "✓ Created ~/.nyxx/config.json"
fi

# ── Shell detection and wrapper injection ──────────────────────────────────
SHELL_NAME=$(basename "$SHELL")

case "$SHELL_NAME" in
    bash)
        CONFIG_FILE="$HOME/.bashrc"
        ;;
    zsh)
        CONFIG_FILE="$HOME/.zshrc"
        ;;
    pwsh|powershell)
        echo ""
        echo "PowerShell detected."

        # Resolve the PowerShell profile path
        PS_PROFILE=$(powershell -NoProfile -Command 'echo $PROFILE' 2>/dev/null)

        if [ -z "$PS_PROFILE" ]; then
            echo "Could not detect PowerShell profile path."
            echo "Please manually add the nyxx() function to your \$PROFILE."
            exit 1
        fi

        # Convert project root and python bin to Windows paths
        WIN_SCRIPT_DIR=$(cygpath -w "$SCRIPT_DIR" 2>/dev/null || echo "$SCRIPT_DIR")
        WIN_PYTHON_BIN=$(cygpath -w "$PYTHON_BIN" 2>/dev/null || echo "$PYTHON_BIN")

        if grep -qF "function nyxx" "$PS_PROFILE" 2>/dev/null; then
            echo "✓ Nyxx wrapper already exists in PowerShell profile — skipping."
        else
            mkdir -p "$(dirname "$PS_PROFILE")"
            cat >> "$PS_PROFILE" << EOF_PS

# Nyxx Integration
function nyxx {
    \$projectRoot      = "$WIN_SCRIPT_DIR"
    \$pythonExecutable = "$WIN_PYTHON_BIN"

    if (-not (Test-Path -LiteralPath \$pythonExecutable)) {
        Write-Host "nyxx: python not found at \$pythonExecutable"
        return
    }

    # Clear anything an earlier run left behind so only this run's action
    # gets acted on below.
    \$actionFile = Join-Path \$env:USERPROFILE ".nyxx\action"
    Remove-Item -LiteralPath \$actionFile -ErrorAction SilentlyContinue

    \$oldPath        = \$env:PYTHONPATH
    \$oldCwd         = \$env:NYXX_CWD
    \$env:PYTHONPATH = \$projectRoot
    \$env:NYXX_CWD   = (Get-Location).Path

    & \$pythonExecutable -m src.nyxx.main @args

    \$env:PYTHONPATH = \$oldPath
    \$env:NYXX_CWD   = \$oldCwd

    if (Test-Path -LiteralPath \$actionFile) {
        # UTF8: Nyxx writes UTF-8 without a BOM, which PowerShell 5.1 would
        # otherwise read as ANSI. -LiteralPath: [ ] in folder names.
        \$action = (Get-Content -LiteralPath \$actionFile -Raw -Encoding UTF8).Trim()
        Remove-Item -LiteralPath \$actionFile
        if (\$action -match "^CD:(.*)") {
            Set-Location -LiteralPath \$Matches[1].Trim()
        } elseif (\$action -match "^EXEC:(.*)") {
            Invoke-Expression \$Matches[1].Trim()
        } else {
            Write-Host "nyxx: unexpected action: \$action"
        }
    }
}
EOF_PS
            echo "✓ Nyxx function added to PowerShell profile."
        fi

        echo ""
        echo "  To activate in your current PowerShell session, run:"
        echo "    . \$PROFILE"
        echo ""
        echo "  Then try:"
        echo "    nyxx          — open home screen"
        echo "    nyxx cd       — open directory navigator"
        echo "    nyxx jump     — open saved locations"
        echo "    nyxx memo     — open saved commands"
        echo "    nyxx theme    — change theme"
        exit 0
        ;;
    *)
        echo ""
        echo "Unsupported shell: $SHELL_NAME"
        echo "Please manually add the nyxx() function to your shell config."
        echo "You can find the function template in: shell_integrations/nyxx.sh"
        exit 1
        ;;
esac

# ── Inject bash/zsh wrapper function ──────────────────────────────────────
if grep -qF "nyxx() {" "$CONFIG_FILE" 2>/dev/null; then
    echo "✓ Nyxx wrapper already exists in $CONFIG_FILE — skipping."
else
    echo "Adding Nyxx function to $CONFIG_FILE..."
    cat >> "$CONFIG_FILE" << EOF_NYXX_FUNCTION

# Nyxx Integration
nyxx() {
  local action_file="\$HOME/.nyxx/action"
  # Clear anything an earlier run left behind so only this run's action
  # gets acted on below.
  rm -f "\$action_file"

  # NYXX_CWD tells Python which directory the user is currently in.
  # Run directly (no output capture) so jump add / memo add prompts work
  # the same as everything else; the result comes back via the action
  # file, not stdout.
  NYXX_CWD="\$(pwd)" PYTHONPATH="${SCRIPT_DIR}" "${PYTHON_BIN}" -m src.nyxx.main "\$@"

  if [[ -f "\$action_file" ]]; then
    local action
    action=\$(cat "\$action_file")
    rm -f "\$action_file"
    case "\$action" in
      CD:*)   cd "\${action#CD:}" || echo "nyxx: cd failed: \${action#CD:}" ;;
      EXEC:*) eval "\${action#EXEC:}" ;;
      *)      echo "nyxx: unexpected action: \$action" ;;
    esac
  fi
}
EOF_NYXX_FUNCTION
    echo "✓ Nyxx function added to $CONFIG_FILE."
fi

# ── Done ───────────────────────────────────────────────────────────────────
echo ""
echo "✓ Nyxx installation complete!"
echo ""
echo "  To activate in your current session, run:"
echo "    source $CONFIG_FILE"
echo ""
echo "  Then try:"
echo "    nyxx          — open home screen"
echo "    nyxx cd       — open directory navigator"
echo "    nyxx jump     — open saved locations"
echo "    nyxx memo     — open saved commands"
echo "    nyxx theme    — change theme"
echo ""