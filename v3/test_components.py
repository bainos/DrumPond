import curses
from logging import DEBUG
from src.components.dispatcher import Dispatcher
from src.components.input import Input

def draw(stdscr: curses.window) -> None:
    curses.nonl()
    # curses.set_escdelay(25)
    stdscr.nodelay(True)
    stdscr.erase()
    stdscr.box()
    stdscr.refresh()

    i = Input(stdscr)
    i.log_level(DEBUG)

    i.start()

if __name__ == '__main__':
    d = Dispatcher()
    d.start()
    curses.wrapper(draw)
