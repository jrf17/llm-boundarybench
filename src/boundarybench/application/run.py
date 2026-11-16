"""Run the synthetic application API on loopback.

Usage:
    python -m boundarybench.application.run --mode vulnerable --port 8000
    python -m boundarybench.application.run --mode hardened --port 8001

The server binds to 127.0.0.1 only.
"""

from __future__ import annotations

import argparse


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="Run the synthetic BoundaryBench app")
    parser.add_argument("--mode", choices=["vulnerable", "hardened"], default="vulnerable")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    from boundarybench.application.api import create_app

    app = create_app(mode=args.mode)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
