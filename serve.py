#!/usr/bin/env python3
"""Serve only the Stepwise app — not the whole repo.

ponytail: this is answer-hiding for a local teaching tool, not a security
boundary. It stops a curious learner from browsing to dev/ or tools/ and
reading reference solutions in the URL bar; it does nothing against anyone
willing to read the repo on disk, use git, or otherwise bypass HTTP. No auth,
no TLS, no protection against a hostile client on the same network.
"""
import http.server
import posixpath

PORT = 8000

# What the running app is made of. Everything the browser loads is either a
# front-end file sitting directly in the repo root, or lives in one of the
# app's own directories. Solutions live in tools/ and dev/, which are
# directories and therefore never match.
#
# This used to be a hand-listed set of filenames, and three separate features
# shipped broken because a new file was not added to it. The rule is now
# structural: adding app.js's next neighbour needs no edit here.
ALLOWED_ROOT_SUFFIXES = (".html", ".js", ".css")
ALLOWED_FILES = {
    "/",
    # The tracer, not a solution: it animates whatever function it is handed.
    "/tracer.py",
}
ALLOWED_DIRS = ("/problems/", "/views/")


class AppOnlyHandler(http.server.SimpleHTTPRequestHandler):
    def _allowed(self, path):
        path = posixpath.normpath(path)
        if path == ".":
            path = "/"
        if ".." in path:
            return False
        if path in ALLOWED_FILES:
            return True
        # A root-level front-end file: exactly one slash, known suffix.
        if path.count("/") == 1 and path.endswith(ALLOWED_ROOT_SUFFIXES):
            return True
        return any(path.startswith(d) for d in ALLOWED_DIRS)

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
