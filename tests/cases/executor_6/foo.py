from jina import Executor, requests

class Executor6(Executor):
    @requests
    def foo(self):
        pass

