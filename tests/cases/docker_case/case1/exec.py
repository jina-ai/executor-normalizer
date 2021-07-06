from jina import Executor, requests
import tensorflow as tf
from torch import nn
import torch
import numpy as np


class MyExecutor(Executor):
    @requests
    def foo(self, **kwargs):
        print(tf.__version__)
        pass
