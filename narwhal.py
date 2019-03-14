#!/usr/local/bin/python3
import argparse
import errno
import logging
import os
import select
import signal
import socket
import sys
from typing import List


class HTTPServer:
    def __init__(
            self,
            worker_count: int = 1,
            port: int = 8080,
            debug: bool = False,
    ) -> None:
        """
        Create the main socket and listen for new clients.
        """
        self._desired_worker_count = worker_count
        self._port = port

        logging.basicConfig(
            stream=sys.stdout,
            level=logging.DEBUG if debug else logging.INFO
        )
        self.logger = logging.getLogger('HTTPServer')

        self._workers: List[int] = []
        self._listener: socket.socket = HTTPServer._create_socket(port=self._port)

    def run(self) -> None:
        """
        Start the parent process loop, watching for dying workers and forking
        new ones as appropriate.

        The parent is responsible for killing workers after a shutdown event.
        """
        try:
            while True:
                while len(self._workers) < self._desired_worker_count:
                    self._start_worker_loop()
        except KeyboardInterrupt:
            self._kill_workers()
        except SystemExit:
            self._kill_workers()

    def _kill_workers(self) -> None:
        for pid in self._workers:
            os.kill(pid, signal.SIGTERM)

    def _start_worker_loop(self) -> None:
        """
        Create a new worker process by forking the parent.

        The parent returns, while the child worker is then put into the main
        select/accept loop to handle connections.
        """
        # Child gets 0 return, parent gets child's pid
        pid = os.fork()
        if pid != 0:
            self.logger.info(f' Started worker: {pid}')
            self._workers.append(pid)
        elif pid == 0:
            while True:
                while True:
                    # Wait for incoming messages before attempting to accept()
                    socks = select.select([self._listener], [], [], 1.0)
                    if socks[0]:
                        break

                try:
                    conn, address = self._listener.accept()
                    self._handle_request(conn, address)
                except socket.error as e:
                    # Use errno.errorcode[<int>] to lookup any exceptions here
                    # that aren't handled.
                    if e.errno != errno.EAGAIN:
                        raise e

    def _handle_request(self, conn: socket.socket, address: str) -> None:
        """
        Read data from an accepted connection and return response data.
        """
        # Nonblocking sockets hang and cause connection resets due to failed
        # reads, or something else? But ensuring it is switched to blocking
        # resolves this.
        conn.setblocking(1)

        data = conn.recv(512)
        self.logger.debug(f'{data}')

        response_text = '<html><body>Hello!</body></html>'
        response = (
            'HTTP/1.1 200 OK\r\n'
            f'Content-Length: {len(response_text)}\r\n'
            'Content-Type: text/html\r\n'
            'Connection: close\r\n'
            '\r\n'
            f'{response_text}'
        ).encode()
        conn.sendall(response)
        conn.close()
        self.logger.debug(f'{response}')

    @staticmethod
    def _create_socket(
            host: str = 'localhost',
            port: int = 8080,
            backlog: int = 512,
    ) -> socket.socket:
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
        s.setblocking(0)
        # Use no-delay, aka Nagle's algorithm
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # Reuse a local socket in TIME_WAIT state, without waiting for timeout
        # to expire
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Host is either a domain e.g. 'daring.cwi.nl' or an IPv4 address e.g.
        # '100.50.200.5'
        s.bind((host, port))
        # There will be multiple workers handling connections so we don't want
        # to refuse any connections that aren't immediately accepted.
        s.listen(backlog)

        return s


def parse_cmd_line():
    parser = argparse.ArgumentParser(
        description='Run a pre-fork worker HTTP server',
    )

    parser.add_argument(
        '-w',
        '--worker_count',
        action='store',
        default=1,
        type=int,
        metavar='WORKER_COUNT',
        help='The number of workers processes to run',
    )

    parser.add_argument(
        '-p',
        '--port',
        action='store',
        default=8080,
        type=int,
        metavar='PORT',
        help='The port to listen for requests on',
    )

    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='If set enables debug level logs',
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_cmd_line()

    server = HTTPServer(
        worker_count=args.worker_count,
        port=args.port,
        debug=args.debug,
    )
    server.run()
