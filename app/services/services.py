from abc import ABC, abstractmethod

class BaseService(ABC):
    """
    Interface gốc cho mọi service của hệ thống.
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def detect(self):
        pass