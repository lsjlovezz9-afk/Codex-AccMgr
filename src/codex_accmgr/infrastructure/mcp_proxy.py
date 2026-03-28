from __future__ import annotations

import json
import subprocess
import sys
import threading

INTERCEPT_METHODS = {
    "resources/list",
    "resources/templates",
}


def _read_message(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        if b":" in line:
            key, value = line.split(b":", 1)
            headers[key.strip().lower()] = value.strip()
    length = headers.get(b"content-length")
    if not length:
        return None
    try:
        length = int(length)
    except Exception:
        return None
    body = stream.read(length)
    if not body:
        return None
    return body


def _write_message(stream, body_bytes):
    header = f"Content-Length: {len(body_bytes)}\r\n\r\n".encode("utf-8")
    stream.write(header)
    stream.write(body_bytes)
    stream.flush()


def _server_to_client(server_stdout, client_stdout):
    while True:
        body = _read_message(server_stdout)
        if body is None:
            break
        _write_message(client_stdout, body)


def _proxy(server_cmd):
    server = subprocess.Popen(
        server_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
    )

    thread = threading.Thread(
        target=_server_to_client,
        args=(server.stdout, sys.stdout.buffer),
        daemon=True,
    )
    thread.start()

    client_in = sys.stdin.buffer
    server_in = server.stdin

    while True:
        body = _read_message(client_in)
        if body is None:
            break
        try:
            msg = json.loads(body.decode("utf-8"))
        except Exception:
            _write_message(server_in, body)
            continue

        method = msg.get("method")
        msg_id = msg.get("id")
        if method in INTERCEPT_METHODS and msg_id is not None:
            result = {"resourceTemplates": []} if method == "resources/templates" else {"resources": []}
            response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
            _write_message(sys.stdout.buffer, json.dumps(response).encode("utf-8"))
            continue

        _write_message(server_in, body)

    try:
        server.terminate()
    except Exception:
        pass


def main():
    args = sys.argv[1:]
    if args[:1] == ["--"]:
        args = args[1:]
    if not args:
        sys.stderr.write("Usage: mcp_proxy.py -- <server> [args...]\n")
        raise SystemExit(2)
    _proxy(args)


if __name__ == "__main__":
    main()
