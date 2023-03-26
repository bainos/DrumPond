from multiprocessing import shared_memory
from pickle import dumps, loads

shm = shared_memory.SharedMemory(
        create=True, size=1024, name='dpshm')

buffer = shm.buf
registry = dict()

def _save() -> None:
    cache = bytearray(dumps(registry))
    buffer[:len(cache)] = cache   # type: ignore

def _load() -> None:
    global registry
    barr = bytearray()
    for i in range(len(buffer)):  # type: ignore
        barr.append(buffer[i])    # type: ignore
    registry = loads(bytes(barr))

def init() -> None:
    _save()

def kset(k: str, v: str|int) -> None:
    _load()
    registry[k] = v
    _save()

def dset(d: dict[str,str|int]) -> None:
    _load()
    for k in d.keys():
        registry[k] = d[k]
    _save()

def release() -> None:
    shm.unlink()

if __name__ == '__name__':
    init()
    print(registry)
    kset('mese', 'Aprile')
    print(registry)
    kset('giorno', 31)
    print(registry)
    print(registry['mese'])
    print(registry['giorno'])
    shm.unlink()
