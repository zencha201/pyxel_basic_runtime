"""HTTP from the BASIC screen (COMMANDS.md 5), against a local server."""

import http.server
import threading
import time

import pytest
from helpers import make_screen

from pyxel_basic_runtime import ENDED, STOPPED


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/slow":
            time.sleep(1)
        data = b'{"greeting":"HELLO","n":[1,2,3]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture(scope="module")
def base():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d" % server.server_address[1]
    server.shutdown()


def run_until_done(screen, limit=300):
    for _ in range(limit):
        screen.step()
        screen.draw()                       # the screen keeps drawing while it waits
        if screen.phase != "run":
            return
        time.sleep(0.01)


def test_http_in_the_basic_screen(base):
    screen = make_screen('DICT R$\nHTTP "GET", "%s/", "", R$\n'
                         'PRINT HTTPSTATUS();R$("greeting");R$("n.#")' % base)
    run_until_done(screen)
    assert screen.terminal.text().startswith("200HELLO3")
    assert screen._pending_result.kind == ENDED
    screen.close()


def test_stop_while_waiting_for_a_reply(base):
    screen = make_screen('DICT R$\nHTTP "GET", "%s/slow", "", R$\nPRINT "NO"' % base)
    screen.step()
    screen.stop()
    assert screen.result.kind == STOPPED
    screen.close()
