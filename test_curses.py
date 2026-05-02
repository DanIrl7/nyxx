import curses

stdscr = curses.initscr()

curses.noecho()
curses.cbreak()
stdscr.keypad(True)

max_y, max_x = stdscr.getmaxyx()  # Get terminal size
center_y = max_y // 2
center_x = max_x // 2
stdscr.addstr(center_y, center_x, "Welcome to NAVII")
stdscr.refresh()
stdscr.addstr(center_y - 2, 0, "Press any key to continue...")
stdscr.refresh()
stdscr.getch()

curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()