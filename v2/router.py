import threading
import asyncio
import socket
# import struct
import os
# import signal

DPSOCK = os.environ['HOME'] + '/drumpond.sock'

async def server(name: str):
    r_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    r_sock.bind(DPSOCK)
    r_sock.listen(1)
    print(f'{name} listening..')
    connection, client_address = r_sock.accept()
    try:
        while True:
            data = connection.recv(128)
            datad = data.decode('ascii')
            print(f'{client_address}: {datad}')
            # r_sock.sendall(data)
            if datad == 'EXIT':
                break
    finally:
        await asyncio.sleep(1)
        connection.close()
        print(f'{name} connection clossed.')

async def client(message: str):
    await asyncio.sleep(1)
    w_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        w_sock.connect(DPSOCK)
    except socket.error as e:
        print(f'Connection error: {e}')

    for _ in range(3):
        w_sock.sendall(bytes(message, 'ascii'))
        # data = w_sock.recv(128)
        # print(f'data: {data}')
        await asyncio.sleep(1)

    w_sock.send(b'EXIT')
    w_sock.close()

def server_worker():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(server('Server Yo!'))
    # loop.create_task(server('Server Yo!'))
    # loop.run_forever()
    loop.close()


def client_worker():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(client('c0'))
    # loop.create_task(client('c0'))
    # loop.run_forever()
    loop.close()

if __name__ == '__main__':
    try:
        os.unlink(DPSOCK)
    except OSError:
        if os.path.exists(DPSOCK):
            raise


    # for signame in {'SIGINT', 'SIGTERM'}:
        # loop.add_signal_handler(getattr(signal, signame), loop.stop)

    threading.Thread(target=server_worker).start()
    threading.Thread(target=client_worker).start()
