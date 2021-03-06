from typing import Optional, List, Tuple
from jina import Executor, requests


class Executor1(Executor):
    """
    My executor docstring
    """

    def __init__(
        self,
        arg1: str,
        arg2: Optional[List[str]],
        arg3: Tuple[int, str],
        *args,
        arg4: Optional[int] = None,
        arg5: Optional[Tuple[int, str]] = (123, '123'),
        **kwargs
    ):
        """
        init docstring
        """
        super().__init__(**kwargs)

    @requests
    def foo(self, arg1, *, kwarg1: Optional[int] = None):
        """foo docstring"""
        pass
