from jina import Executor, requests

from .helper import print_something


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        print_something()
