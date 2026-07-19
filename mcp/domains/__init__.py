"""Factories for the independently deployable bounded-context servers."""

from __future__ import annotations

from typing import Callable

from ..config import MCPConfig
from ..protocol import MCPServer

ServerFactory = Callable[[MCPConfig], MCPServer]


def factories() -> dict[str, ServerFactory]:
    # Imports stay lazy so one context cannot fail because another context has a
    # local configuration problem.
    from .agl import create_server as agl
    from .command_runner import create_server as command_runner
    from .filament import create_server as filament
    from .fluorite import create_server as fluorite
    from .flutter_runtime import create_server as flutter_runtime
    from .graphics import create_server as graphics
    from .target_validation import create_server as target_validation
    from .yocto import create_server as yocto

    return {
        "agl": agl,
        "yocto": yocto,
        "fluorite": fluorite,
        "flutter_runtime": flutter_runtime,
        "filament": filament,
        "graphics": graphics,
        "target_validation": target_validation,
        "command_runner": command_runner,
    }
