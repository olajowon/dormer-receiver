# Created by zhouwang on 2020/9/10.
import socket
import select
import logging
logger = logging.getLogger('base')


def receive_process(queue, addr, port):
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    skt_fd = skt.fileno()
    skt.bind((addr, port))
    fd_skt_mp = {skt_fd: skt}

    epoll = select.epoll()
    epoll.register(skt_fd, select.EPOLLIN)
    skt.listen(100)
    fd_leftover_mp = {}

    while True:
        events = epoll.poll(1)
        for fd, event in events:
            if fd == skt_fd:
                client, address = skt.accept()
                client.setblocking(0)
                epoll.register(client.fileno(), select.EPOLLIN)
                fd_skt_mp[client.fileno()] = client
                fd_leftover_mp[client.fileno()] = b''
            else:
                if event & select.EPOLLIN:
                    content = b''
                    try:
                        content = fd_skt_mp[fd].recv(1024)
                    except Exception as e:
                        if e.errno in (11, 4):
                            continue
                        elif e.errno not in (104,):
                            logger.error('receive socket recv error, %s' % str(e))

                    if content:
                        content = fd_leftover_mp[fd] + content
                        endindex = content.rfind(b'\n') + 1
                        content, leftover = content[:endindex], content[endindex:]
                        fd_leftover_mp[fd] = leftover
                        queue.put(content)
                    else:
                        epoll.unregister(fd)
                        fd_skt_mp[fd].close()
                        del fd_skt_mp[fd]
                        del fd_leftover_mp[fd]
                elif event & select.EPOLLHUP:
                    epoll.unregister(fd)
                    fd_skt_mp[fd].close()
                    del fd_skt_mp[fd]
                    del fd_leftover_mp[fd]

    epoll.unregister(skt_fd)
    epoll.close()
    skt.close()
    logger.info('receive exit')
