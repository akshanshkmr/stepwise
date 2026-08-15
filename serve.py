#!/usr/bin/env python3
"""Serve only the CodeTeach app — not the whole repo.

ponytail: this is answer-hiding for a local teaching tool, not a security
boundary. It stops a curious learner from browsing to dev/ or tools/ and
reading reference solutions in the URL bar; it does nothing against anyone
willing to read the repo on disk, use git, or otherwise bypass HTTP. No auth,
no TLS, no protection against a hostile client on the same network.
"""
import http.server
import posixpath

PORT = 8000

# Exact files and directories that make up the running app. Anything else
# under the repo root is 404, even if it exists on disk.
ALLOWED_FILES = {
    "/", "/index.html", "/app.js", "/visualizer.js", "/runner.js", "/style.css",
}
ALLOWED_DIRS = ("/problems/", "/views/")


class AppOnlyHandler(http.server.SimpleHTTPRequestHandler):
    def _allowed(self, path):
        path = posixpath.normpath(path)
        if path == ".":
            path = "/"
        if path in ALLOWED_FILES:
            return True
        return any(path.startswith(d) for d in ALLOWED_DIRS) and ".." not in path

    def send_head(self):
        if not self._allowed(self.path.split("?", 1)[0]):
            self.send_error(404, "Not Found")
            return None
        return super().send_head()

    def end_headers(self):
        # Local dev server: never serve a stale module. Without this, editing
        # app.js or a view leaves the browser running the cached copy and you
        # debug code that is no longer on disk.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def list_directory(self, path):
        # ponytail: no directory listings, even for allowed dirs like problems/
        self.send_error(404, "Not Found")
        return None


if __name__ == "__main__":
    http.server.test(HandlerClass=AppOnlyHandler, port=PORT)
