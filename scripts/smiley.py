import curses


def draw_smiley(stdscr):
    # Clear the screen
    stdscr.clear()

    def draw(y, start_x, pair_list, char="▄"):
        for step, pair_id in enumerate(pair_list):

            current_x = start_x + step

            color_attr = curses.color_pair(pair_id)

            stdscr.addstr(start_y + y, current_x, char, color_attr)
    
    # Hide the cursor
    curses.curs_set(0)

    # Set up colors
    curses.start_color()
    BASE_PAIR = 0
    curses.init_pair(BASE_PAIR + 3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(BASE_PAIR + 4, curses.COLOR_BLACK, curses.COLOR_YELLOW)

    C_BLK = 16; C_BD2 = 17; C_BD1 = 18; C_B = 19;   C_BL1 = 20; C_BL2 = 21
    C_MD2 = 22; C_MD1 = 23; C_M = 24;   C_ML1 = 25; C_ML2 = 26; C_SUN = 27

    # Inject your scaled 0-1000 RGB values into those unique IDs
    curses.init_color(C_BLK, 0,   0,   47)
    curses.init_color(C_BD2, 94,  141, 188)
    curses.init_color(C_BD1, 141, 188, 282)
    curses.init_color(C_B,   188, 329, 376)
    curses.init_color(C_BL1, 282, 424, 518)
    curses.init_color(C_BL2, 329, 518, 612)
    
    curses.init_color(C_MD2, 188, 94,  141)
    curses.init_color(C_MD1, 329, 188, 282)
    curses.init_color(C_M,   518, 141, 282)
    curses.init_color(C_ML1, 612, 141, 376)
    curses.init_color(C_ML2, 800, 376, 612)
    
    curses.init_color(C_SUN, 941, 847, 659)

    # 2. DEFINE COLOR PAIR ID NUMBERS (Starting at 60)
    BLK = 60; BD2 = 61; BD1 = 62; B = 63; BL1 = 64; BL2 = 65
    MD2 = 66; MD1 = 67; M = 68;  ML1 = 69; ML2 = 70; SUN = 71

    # Custom Hybrid Combinations
    MD1BL1    = 72; IMD1BL1   = 73; BL1BLK    = 74; IBL1BLK   = 75
    MBLK      = 76; IMBLK     = 77; MD2BLK    = 78; IMD2BLK   = 79
    ML2SUN    = 80; IML2SUN   = 81; SUNBLK    = 82; ISUNBLK   = 83
    ML1ML2    = 84; IML1ML2   = 85; MD1MD2    = 86; IMD1MD2   = 87
    BL1BL2    = 88; IBL1BL2   = 89; BD1BL2    = 90; IBD1BD2   = 91

    # 3. REGISTER PAIRS (Linking pair numbers to our C_ color variables)
    curses.init_pair(BLK, C_BLK, C_BLK)
    curses.init_pair(BD2, C_BD2, C_BD2)
    curses.init_pair(BD1, C_BD1, C_BD1)
    curses.init_pair(B,   C_B,   C_B)
    curses.init_pair(BL1, C_BL1, C_BL1)
    curses.init_pair(BL2, C_BL2, C_BL2)
    curses.init_pair(MD2, C_MD2, C_MD2)
    curses.init_pair(MD1, C_MD1, C_MD1)
    curses.init_pair(M,   C_M,   C_M)
    curses.init_pair(ML1, C_ML1, C_ML1)
    curses.init_pair(ML2, C_ML2, C_ML2)
    curses.init_pair(SUN, C_SUN, C_SUN)

    # Hybrid Pairs
    curses.init_pair(MD1BL1,  C_MD1, C_BL1); curses.init_pair(IMD1BL1, C_BL1, C_MD1)
    curses.init_pair(BL1BLK,  C_BL1, C_BLK); curses.init_pair(IBL1BLK, C_BLK, C_BL1)
    curses.init_pair(MBLK,    C_M,   C_BLK); curses.init_pair(IMBLK,   C_BLK, C_M)
    curses.init_pair(MD2BLK,  C_MD2, C_BLK); curses.init_pair(IMD2BLK, C_BLK, C_MD2)
    curses.init_pair(ML2SUN,  C_ML2, C_SUN); curses.init_pair(IML2SUN, C_SUN, C_ML2)
    curses.init_pair(SUNBLK,  C_SUN, C_BLK); curses.init_pair(ISUNBLK, C_BLK, C_SUN)
    curses.init_pair(ML1ML2,  C_ML1, C_ML2); curses.init_pair(IML1ML2, C_ML2, C_ML1)
    curses.init_pair(MD1MD2,  C_MD1, C_MD2); curses.init_pair(IMD1MD2, C_MD2, C_MD1)
    curses.init_pair(BL1BL2,  C_BL1, C_BL2); curses.init_pair(IBL1BL2, C_BL2, C_BL1)
    curses.init_pair(BD1BL2,  C_BD1, C_BL2); curses.init_pair(IBD1BD2, C_BD2, C_BD1)
    row1 = [
    BD1, BD1, BD1,  # Dark Blue water
    M, M,             # Neon Magenta reflection
    BD1, BD1, BD1, MBLK, MD1BL1  # Dark Blue water
]
    
    # Starting coordinates for our smiley
    start_y = 0
    start_x = 0
    

    

    draw(0,0, row1)
    
   
    # 5. Add a caption below
    stdscr.addstr(start_y + 9, start_x, "Smiley drawn purely with curses!")
  
    # Refresh the screen to push the drawings to the terminal
    stdscr.refresh()
    
    # Wait until the user presses 'q' to exit
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break

if __name__ == "__main__":
    # curses.wrapper safely sets up the terminal and restores it when done
    curses.wrapper(draw_smiley)


import curses


# def draw_dimensions(stdscr):
#     """Print the terminal window dimensions (height and width) at the top-left corner."""
#     # Get current size
#     height, width = stdscr.getmaxyx()
#     # Clear the first line to avoid leftover characters if window shrinks
#     stdscr.move(0, 0)
#     stdscr.clrtoeol()
#     # Display dimensions
#     stdscr.addstr(0, 0, f"Lines (Height): {height} | Columns (Width): {width}")
#     stdscr.refresh()
#     # Wait for user to press any key before exiting
#     stdscr.getch()
