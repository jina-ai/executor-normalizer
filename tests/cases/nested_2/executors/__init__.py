from typing import Tuple, Dict
from jina import DocumentArray, requests


class NestedExecutor(Executor):
    """
    Nested Executor
    """
    def __init__(
            self,
            arg1: int = 1,
            **kwargs):
        super().__init__(**kwargs)

    @requests(on='/foo')
    def foo(
            self,
            docs: DocumentArray,
            parameters: Dict = {}
    ):
        """foo docstring"""
        pass
