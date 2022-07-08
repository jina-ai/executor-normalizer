from jina import Executor, requests

from .helper import print_something
from .utils.data import data


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        print_something()
        data()
