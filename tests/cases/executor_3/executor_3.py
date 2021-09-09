from typing import Tuple, Dict
import jina
from jina import DocumentArray


class Executor3(jina.Executor):
    """
    Executor 3
    """
    def __init__(
            self,
            arg1: int = 1,
            arg2: Tuple[str, str] = ('123  123', 'test\ntest'),
            **kwargs):
        super().__init__(**kwargs)

    @jina.requests(on='/foo')
    def foo(
            self,
            docs: DocumentArray,
            parameters: Dict = {}
    ):
        """foo docstring"""
        pass

    @jina.requests
    def bar(
            self,
            docs: DocumentArray,
            parameters: Dict = {}
    ):
        """bar docstring"""
        pass

    def not_an_endpoint(self, ):
        """bar docstring
        """
        pass
