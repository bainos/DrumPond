import asyncio

import socket
import struct

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 7581
MULTICAST_TTL = 1

r_sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM,
    # socket.IPPROTO_UDP
)
r_sock.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

r_sock.bind((MCAST_GRP, MCAST_PORT))
mreq = struct.pack(
    '4sl',
    socket.inet_aton(MCAST_GRP),
    socket.INADDR_ANY
)

# r_sock.setsockopt(
#     socket.IPPROTO_IP,
#     socket.IP_MULTICAST_TTL,
#     mreq
# )


async def sreader(name: str):
    print(f'{name} listening..')
    listen = True
    while listen:
        msg = r_sock.recv(10240)
        print(f'{name}: {msg}')
        if msg == 'EXIT':
            listen = False


w_sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM,
    socket.IPPROTO_UDP
)
w_sock.setsockopt(
    socket.IPPROTO_IP,
    socket.IP_MULTICAST_TTL,
    MULTICAST_TTL
)


async def swriter(message: str):
    for i in range(10):
        print('send')
        w_sock.sendto(
            message.encode(),
            (MCAST_GRP, MCAST_PORT)
        )
        await asyncio.sleep(3)

    w_sock.sendto(
        b'EXIT',
        (MCAST_GRP, MCAST_PORT)
    )


def main():
    for x in range(3):
        sreader(f'r{x}')

    asyncio.sleep(1)

    swriter('Yo!')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(swriter('Yo!')),
        loop.create_task(sreader('r0')),
        loop.create_task(sreader('r1')),
        loop.create_task(sreader('r2')),
    ]
    loop.run_until_complete(asyncio.wait(tasks))
