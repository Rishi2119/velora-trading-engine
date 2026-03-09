class AgentError(Exception):
    """Base exception for the autonomous agent."""
    pass

class SafetyViolationError(AgentError):
    """Raised when an action violates safety constraints."""
    pass

class ReasoningError(AgentError):
    """Raised when the reasoning engine fails or returns malformed output."""
    pass

class ExecutionError(AgentError):
    """Raised when a task execution fails."""
    pass

class MemoryOverflowError(AgentError):
    """Raised when context size exceeds limits."""
    pass
