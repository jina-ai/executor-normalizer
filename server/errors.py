from enum import Enum, unique


@unique
class ErrorCode(Enum):
    ExecutorNotFound = 4000
    ExecutorExists = 4001
    IllegalExecutor = 4002
    BrokenDependency = 4003

    Others = 5000
