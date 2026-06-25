navi() {
    # Run navii, capturing stdout. Curses draws to /dev/tty directly,
    # so only the final CD: or EXEC: line gets captured here.
    local output
    output=$(PYTHONPATH="." python -m src.navii.main "$@" 2>/dev/null)

    if [ -z "$output" ]; then
        return 0   # User quit without selecting anything
    fi

    if [[ "$output" == CD:* ]]; then
        local path="${output#CD:}"
        cd "$path" || echo "navi: could not cd to '$path'"

    elif [[ "$output" == EXEC:* ]]; then
        local cmd="${output#EXEC:}"
        eval "$cmd"

    else
        # Plain path output (legacy cd module behaviour)
        cd "$output" || echo "navi: could not cd to '$output'"
    fi
}