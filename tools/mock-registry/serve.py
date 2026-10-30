#!/usr/bin/env python3
"""Local mock registry: serves ../miniapps (index.json + .miniapp packages) on :8080.

Usage: python serve.py — then in the emulator point the host at http://10.0.2.2:8080/
(debug build reads MINIAPP_REGISTRY_MOCK; otherwise set up a hosts/proxy override).
"""
import functools
import http.server
import os

registry_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "miniapps")
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=registry_dir)
http.server.ThreadingHTTPServer(("", 8080), handler).serve_forever()
