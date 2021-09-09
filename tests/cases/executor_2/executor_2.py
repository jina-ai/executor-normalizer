from typing import Optional, List, Tuple, Dict

import jina
from jina import Executor, requests, DocumentArray


class Executor2(Executor):
    """
    My executor docstring
    :param: arg1
    :param: arg2
    """
    def __init__(
            self,
            arg1: Optional[
                Tuple[
                    int,
                    str,
                    List[int]
                ]
            ],
            arg2: Optional[
                Tuple[
                    int,
                    str,
                    List[int]
                ]
            ] = (123, 'test', [123]),
            *args, **kwargs):
        """
        init docstring
        """
        super().__init__(**kwargs)

    @requests(on=['/index', '/foo'])
    def foo(
            self,
            arg1: Tuple[
                int,
                str
            ],
            arg2: Optional[int] = None,
    ):
        """foo docstring"""
        pass

    @requests(on='/bar')
    def bar(self, docs: Optional[DocumentArray], parameters: Dict = {}):
        """bar docstring
        :param docs:
        :param parameters:
        """
        pass
