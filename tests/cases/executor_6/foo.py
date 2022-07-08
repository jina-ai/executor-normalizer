from jina import Executor, requests

class Executor4(Executor):
    @requests
    def foo(self):
        pass

