from abc import ABC, abstractmethod


class BaseUseCase(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    async def execute(self, *args, **kwargs):
        pass
    
    
    async def build_response(self, *args, **kwargs):
        pass

