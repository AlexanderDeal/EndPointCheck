"""Small concurrent HTTP demonstration server; no production-service guarantees."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import sleep


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        try:
            if self.path == "/slow":
                sleep(0.6)
            status = 500 if self.path == "/error" else 200
            if self.path not in {"/ready", "/healthy", "/slow", "/error", "/timeout"}:
                status = 404
            body = b"demo response\n"
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.flush()
            if self.path == "/timeout":
                sleep(1)
            self.wfile.write(body)
            self.wfile.flush()
        except BrokenPipeError, ConnectionResetError, ConnectionAbortedError:
            # A timed-out inspector can disconnect before the delayed body arrives.
            pass

    def log_message(self, format: str, *args: object) -> None:
        """Keep expected demonstration traffic quiet."""


def main() -> None:
    with ThreadingHTTPServer(("0.0.0.0", 8000), DemoHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
