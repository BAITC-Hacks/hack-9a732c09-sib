"""Real Uvicorn/socket smoke; TestClient alone is not an HTTP-server check."""

import os
from pathlib import Path
import socket
import subprocess
import sys
from time import monotonic, sleep
from urllib.error import URLError
from urllib.request import urlopen

from backend.smoke import check_api

ROOT = Path(__file__).resolve().parents[2]


def test_uvicorn_real_http():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, env=dict(os.environ, PYTHONUTF8="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    try:
        base_url = f"http://127.0.0.1:{port}"
        deadline = monotonic() + 15
        while monotonic() < deadline:
            assert process.poll() is None, "Uvicorn exited before becoming ready"
            try:
                with urlopen(base_url + "/api/v1/health", timeout=.5) as response:
                    assert response.status == 200
                break
            except (URLError, TimeoutError):
                sleep(.1)
        else:
            raise AssertionError("Uvicorn startup timed out")
        assert check_api(base_url)["status"] == "completed"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
