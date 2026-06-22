#!/usr/bin/env python3
"""Listings de Amazon (drafts internos) — portal web. Puerto 8089."""
import sys
from pathlib import Path

from flask import Flask, abort, send_from_directory

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8089
BASE = Path(__file__).parent
app = Flask(__name__)


@app.route("/")
def index():
    listings = sorted(p.name for p in BASE.glob("*.html"))
    items = "\n".join(f'<li><a href="/{name}">{name}</a></li>' for name in listings)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Amazon Listings</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; max-width: 700px; margin: 60px auto; color: #232f3e; }}
  h1 {{ border-bottom: 3px solid #ff9900; padding-bottom: 8px; }}
  li {{ margin-bottom: 8px; }}
  a {{ color: #007185; }}
</style>
</head>
<body>
<h1>Amazon Listings</h1>
<ul>{items}</ul>
</body>
</html>"""


@app.route("/<name>")
def listing(name):
    if not name.endswith(".html") or "/" in name:
        abort(404)
    path = BASE / name
    if not path.is_file():
        abort(404)
    return send_from_directory(BASE, name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
