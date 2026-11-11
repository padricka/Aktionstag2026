"""Redis-Ersatz für die Entwicklung ohne Docker (z. B. Windows ohne Docker Desktop).

Startet einen Redis-kompatiblen Server rein in Python (fakeredis, steht schon in
requirements.txt). Alle Daten liegen nur im Arbeitsspeicher und sind nach dem Beenden weg.
Wird normalerweise von `npm run game` (tools/start-game.mjs) gestartet.

    python dev_redis.py [port]
"""
import sys

from fakeredis import TcpFakeServer

HOST = "127.0.0.1"


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 6379
    server = TcpFakeServer((HOST, port), server_type="redis")
    print(f"Redis-Ersatz (fakeredis) läuft auf {HOST}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
