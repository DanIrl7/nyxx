# Nyxx shell integration for Bash/Zsh.
#
# Copy the nyxx() function below into your ~/.bashrc or ~/.zshrc, then
# update SCRIPT_DIR and PYTHON_BIN so they point at your actual install.
#
# Python can't change its parent shell's working directory or run a
# command in it directly, so instead of doing that itself, Nyxx writes
# what it wants done to ~/.nyxx/action as "CD:<path>" or "EXEC:<cmd>".
# This wrapper runs Nyxx, then reads that file and acts on it here, in
# the actual interactive shell.
nyxx() {
    local SCRIPT_DIR="$HOME/path/to/nyxx"
    local PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"

    # NYXX_CWD tells Python which directory the user is currently in.
    NYXX_CWD="$(pwd)" PYTHONPATH="$SCRIPT_DIR" "$PYTHON_BIN" -m src.nyxx.main "$@"

    local action_file="$HOME/.nyxx/action"
    if [[ -f "$action_file" ]]; then
        local action
        action=$(cat "$action_file")
        rm -f "$action_file"
        case "$action" in
            CD:*)   cd "${action#CD:}" || echo "nyxx: cd failed: ${action#CD:}" ;;
            EXEC:*) eval "${action#EXEC:}" ;;
            *)      echo "nyxx: unexpected action: $action" ;;
        esac
    fi
}
