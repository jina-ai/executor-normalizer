from jina import Executor, DocumentArray, requests


class executor_7(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        pass
