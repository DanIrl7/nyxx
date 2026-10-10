# The `nyxx` command for Git Bash / MSYS2 (bash or zsh), as installed to
# {app}\shell by setup_script.iss, which adds a line to ~/.bashrc and
# ~/.zshrc that sources this file. Keeping the function here rather than
# in those files means reinstalling Nyxx updates it.
#
# Python can't change its parent shell's working directory or run a
# command in it directly, so instead of doing that itself, Nyxx writes
# what it wants done to ~/.nyxx/action as "CD:<path>" or "EXEC:<cmd>".
# This function runs Nyxx, then reads that file and acts on it here, in
# the actual interactive shell.

# Nyxx.exe sits one folder up from this file. ($0 is the sourced file's
# path under zsh, which has no BASH_SOURCE.)
_nyxx_exe="$(dirname "${BASH_SOURCE[0]:-$0}")/../Nyxx.exe"

nyxx() {
    local action_file="$HOME/.nyxx/action"
    # Clear anything an earlier run left behind (e.g. Nyxx.exe started from
    # the Start menu) so only this run's action gets acted on below.
    rm -f "$action_file"

    "$_nyxx_exe" "$@"

    if [ -f "$action_file" ]; then
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
