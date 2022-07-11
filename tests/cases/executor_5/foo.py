from jina import Executor, requests

class Executor5(Executor):
    @requests
    def foo(self):
        pass

