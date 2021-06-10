import jina
from jina import Executor, requests

class DummyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @requests
    def foo(self):
        print(f"jina version: {jina.__version__}")

class Dummy2Executor(jina.Executor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @requests
    def foo(self):
        print(f"jina version: {jina.__version__}")


class Dummy3Executor(Executor):
    def __init__(self, bar = 'hello', **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
    
    @requests
    def foo(self):
        print(f"jina version: {jina.__version__}")


class FailedExecutor(Executor):
    def __init__(self, bar, **kwargs):
        super().__init__(**kwargs)
        self.bar = bar
    
    @requests
    def foo(self):
        print(f"jina version: {jina.__version__}")