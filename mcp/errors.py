"""Errors which are safe to expose through the MCP boundary."""


class MCPDomainError(Exception):
    """A bounded, user-actionable tool error."""

    def __init__(self, message: str, *, code: str = "invalid_request") -> None:
        super().__init__(message)
        self.code = code


class ConfigurationError(MCPDomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="configuration_error")


class BoundaryViolation(MCPDomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="boundary_violation")
