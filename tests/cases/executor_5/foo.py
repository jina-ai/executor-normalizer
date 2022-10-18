from jina import requests
from jina import Executor as OtherBaseName

class Executor5(OtherBaseName):
    @requests
    def foo(self):
        pass

