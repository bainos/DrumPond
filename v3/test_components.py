import curses
from logging import ERROR, DEBUG
from src.core import dp_shm as shm
from src.constants import modes as M
from src.components.dispatcher import Dispatcher
from src.components.input import Input
from src.components.cursor import Cursor
from src.components.base_component import Header
from src.components.base_component import StatusBar

def draw(stdscr: curses.window) -> None:
    curses.nonl()
    curses.set_escdelay(25)
    stdscr.erase()
    stdscr.box()
    stdscr.refresh()

    maxy, maxx = stdscr.getmaxyx()
    shm.dset({
        'k': -1,        'mode': M.NORMAL,
        'winh': maxy,   'winw': maxx,
        'maxy': maxy-2, 'maxx': maxx-2,
        'miny': 3,      'minx': 2,
        'y': 3,         'x': 2,
        })

    h = Header(stdscr)
    h.log_level(ERROR)
    h.title = 'Drumpond3'
    h.start(in_thread=True)

    s = StatusBar(stdscr)
    s.log_level(DEBUG)
    s.start(in_thread=True)

    c = Cursor(stdscr)
    c.log_level(ERROR)
    c.start(in_thread=True)

    i = Input(stdscr)
    i.log_level(ERROR)
    i.start()

if __name__ == '__main__':
    shm.init()
    try:
        d = Dispatcher()
        d.log_level(ERROR)
        d.start()
        curses.wrapper(draw)
    except Exception as e:
        print(e)
    finally:
        shm.release()
