"""Make the pinned BitBake client response wait configurable on Mac virtiofs.

The AGL checkout is mounted read-only into the fixed Podman container. The
pinned BitBake release hard-codes two 30-second polls in
``bb.server.process.ServerCommunicator.runCommand``. Parsing the mounted
checkout can exceed that boundary, so the Mac harness injects this opt-in
shim through ``PYTHONPATH`` instead of modifying the Yocto source.
"""

import os

from multiprocessing.connection import Connection


_original_poll = Connection.poll


def _fluorite_poll(self, timeout=0.0):
    if timeout == 30 or timeout == 30.0:
        configured = os.environ.get("FLUORITE_BITBAKE_CLIENT_RESPONSE_TIMEOUT")
        if configured:
            timeout = float(configured)
    return _original_poll(self, timeout)


Connection.poll = _fluorite_poll
