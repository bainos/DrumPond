import curses
from logging import DEBUG
from src.core import dp_shm as shm
from src.components.dispatcher import Dispatcher
from src.components.input import Input
from src.components.cursor import Cursor

def draw(stdscr: curses.window) -> None:
    curses.nonl()
    curses.set_escdelay(25)
    stdscr.erase()
    stdscr.box()
    stdscr.refresh()

    maxy, maxx = stdscr.getmaxyx()
    shm.dset({
        'winh': maxy,   'winw': maxx,
        'maxy': maxy-2, 'maxx': maxx-2,
        'miny': 3,      'minx': 2
        })

    c = Cursor(stdscr)
    c.log_level(DEBUG)
    c.start(in_thread=True)

    i = Input(stdscr)
    i.log_level(DEBUG)
    i.start()

if __name__ == '__main__':
    shm.init()
    d = Dispatcher()
    d.start()
    curses.wrapper(draw)
    shm.release()
