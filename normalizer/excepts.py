"""This modules defines all kinds of exceptions raised in Normalizer."""


class ExecutorNotFoundError(Exception):
    """Raised when the executor doesn’t exist. """


class ExecutorExistsError(Exception):
    """Raised when more than one executors exist."""


class IllegalExecutorError(Exception):
    """Raised when the executor is defined with for illegal argument types."""


class DependencyError(Exception):
    """Raised when cyclic or missing dependancy detected"""
