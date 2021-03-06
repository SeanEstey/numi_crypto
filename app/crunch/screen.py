# Display formatted text to stdout in table form
import curses, logging, re
from curses import init_pair, color_pair
from decimal import Decimal
log = logging.getLogger(__name__)

class c:
    BOLD = curses.A_BOLD

def get_n_lines():
    return curses.LINES
def get_n_cols():
    return curses.COLS
def midx(stdscr):
    return stdscr.getmaxyx()[1]
def midy(stdscr):
    return stdscr.getmaxyx()[0]

#----------------------------------------------------------------------
def setup(stdscr):
    """Setup curses window.
    """
    set_colors(stdscr)
    # Don't print what I type on the terminal
    curses.noecho()
    # React to every key press, not just when pressing "enter"
    curses.cbreak()
    stdscr.nodelay(True)
    stdscr.keypad(True)
    # hide cursor
    curses.curs_set(0)
    stdscr.refresh()

#----------------------------------------------------------------------
def teardown(stdscr):
    # Reverse changes made to terminal by cbreak()
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    # restore the terminal to its original state
    curses.endwin()

#----------------------------------------------------------------------
def printrow(stdscr, y, datarow, colsizes, colors,
             align=None, colsp=None, x=None, usecurspos=True):
    x = x if x is not None else 2
    justify = align if align else str.ljust
    colspace = colsp if colsp else 2

    if usecurspos:
        stdscr.move(y,x)
    for idx in range(0, len(datarow)):
        stdscr.addstr(
            y,
            stdscr.getyx()[1],
            justify(str(datarow[idx]), colsizes[idx]+colspace),
            colors[idx])

#-----------------------------------------------------------------------------
def print_table(stdscr, titles, hdr, datarows, colors,
                align=None, colsp=None, div=True):
    """Print justified datatable w/ header row.
    @hdr: list of column headers
    @datarows: list of rows, each row a list of column print values
    @colors: list of rows, each row a list of column print colors
    """
    justify = str.ljust if align is None else str.rjust
    colspace = colsp or 3  # Column spacing
    col_wdt = _colsizes(hdr, datarows) # Justified column widths
    tbl_width = sum(col_wdt) + len(col_wdt)*colspace
    tbl_sp = int((stdscr.getmaxyx()[1] - tbl_width)/2) # Tablespacing
    getyx = stdscr.getyx

    if len(titles) == 1:
        # Centered
        tbl_width = sum(col_wdt) + len(col_wdt)*colspace
        x = int(tbl_width/2 - len(titles[0])/2)
        stdscr.addstr(getyx()[0]+1, tbl_sp + x, titles[0])
    elif len(titles) == 2:
        y = getyx()[0]+1
        # Left-aligned
        stdscr.addstr(y, tbl_sp, titles[0])
        # Right-aligned
        tbl_width = sum(col_wdt) + len(col_wdt)*colspace
        x = tbl_sp + tbl_width - len(titles[1])
        stdscr.addstr(y, x, titles[1])

    if div:
        divider(stdscr, getyx()[0]+1, col_wdt, colspace, x=tbl_sp)

    # Print header row (white)
    printrow(stdscr, getyx()[0]+1,hdr, col_wdt, [c.WHITE for n in hdr],
        align=justify, colsp=colspace, x=tbl_sp)

    # Print data rows (custom colors)
    for n in range(0, len(datarows)):
        printrow(stdscr, getyx()[0]+1, datarows[n], col_wdt, colors[n],
            align=justify, colsp=colspace, x=tbl_sp)

#----------------------------------------------------------------------
def input_char(stdscr):
    # Make getch() non-blocking
    #stdscr.nodelay(True)
    ch = stdscr.getch()
    curses.flushinp()
    #stdscr.nodelay(False)
    return ch

#----------------------------------------------------------------------
def input_prompt(stdscr, y, x, prompt):
    # Block input until Enter key
    stdscr.nodelay(False)
    # Show input on screen
    curses.echo()
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()

    inp = stdscr.getstr(y+1, x, 20)
    # Unblock input
    stdscr.nodelay(True)
    curses.noecho()

    return inp

#----------------------------------------------------------------------
def pretty(number, t=None, f=None, abbr=None, d=None):
    """Convert Decimal and floats to human readable strings
    @t: "pct", "money"
    @f: "sign"
    """
    try:
        number = float(number)
    except (ValueError, TypeError) as e:
        return "--"

    head = ""
    tail = ""
    dec = d if d is not None else 2

    if abbr == True:
        if isinstance(number, Decimal):
            exp = number.adjusted()
        else:
            number = round(number, 2)
            exp = len(str(int(number))) - 1

        if exp in range(0,3):
            strval = str(number)
        elif exp in range(3,6):
            short = int(number/pow(10,3)) if dec==0 else round(number/pow(10,3),dec)
            strval = "%s%s" %(short, 'K')
        elif exp in range(6,9):
            short = int(number/pow(10,6)) if dec==0 else round(number/pow(10,6),dec)
            strval = "%s%s" %(short, 'M')
        elif exp in range(9,12):
            short = int(number/pow(10,9)) if dec==0 else round(number/pow(10,9),dec)
            strval = "%s%s" %(short, 'B')
        elif exp in range(12,15):
            short = int(number/pow(10,12)) if dec==0 else round(number/pow(10,12),dec)
            strval = "%s%s" %(short, 'T')
    # Full length number w/ comma separators
    else:
        num = int(number) if dec == 0 else round(number, dec)
        strval = "{:,}".format(num)

    if f == 'sign':
        head += "+" if number > 0 else ""

    if t == "money":
        head += "$"
    elif t == "pct":
        tail += "%"

    return "%s%s%s" %(head, strval, tail)

#----------------------------------------------------------------------
def pnlcolor(colorstr):
    return c.RED if str(colorstr)[0] == '-' else c.GREEN

#----------------------------------------------------------------------
def get_width(val):
    rmv_esc = re.compile(r'\x1b[^m]*m')
    fixed_len = rmv_esc.sub('', str(val))
    return len(fixed_len)

#----------------------------------------------------------------------
def _print_color_palette(stdscr):
    try:
        for i in range(0, 255):
            stdscr.addstr(str(i)+",", color_pair(i))
    except curses.ERR:
        pass

#----------------------------------------------------------------------
def coeff_color(value):
    colormap = {
        -10: c.RED,
        -9:  color_pair(52),
        -8:  color_pair(34),
        -7:  color_pair(28),
        -6:  color_pair(27),
        -5:  color_pair(26),
        -4:  color_pair(26),
        -3:  color_pair(26),
        -2:  color_pair(26),
        -1:  color_pair(26),
         0:  color_pair(66),
         1:  color_pair(66),
         2:  color_pair(66),
         3:  color_pair(66),
         4:  color_pair(66),
         5:  color_pair(23),
         6:  color_pair(29),
         7:  color_pair(35),
         8:  color_pair(41),
         9:  color_pair(47),
         10: c.WHITE
     }

    return colormap[int(value*10)]

#----------------------------------------------------------------------
def set_colors(stdscr):
    """ init_pair args: [pair_number, foreground, background]
    pair_number 0 = WHITE
    """
    curses.start_color()
    curses.use_default_colors()

    for i in range(0, curses.COLORS):
        init_pair(i + 1, i, -1)

    c.WHITE = color_pair(0)
    c.ORANGE = color_pair(2)
    c.BLUE = color_pair(5)
    c.GREEN = color_pair(47)
    c.RED = color_pair(197)

#-----------------------------------------------------------------------------
def _colsizes(hdr, rows):
    colspace = 3
    widths = [len(n) for n in hdr]
    for row in rows:
        widths = [max(widths[n], len(str(row[n]))) for n in range(0,len(row))]
    return widths

#----------------------------------------------------------------------
def divider(stdscr, y, colwidths, colspace, x=None):
    x = x if x is not None else 2
    stdscr.hline(y, x, '-', sum(colwidths) + (len(colwidths)-1)*colspace )
