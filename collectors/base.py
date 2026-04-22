from abc import ABC, abstractmethod
from typing import List

from models.event import Event


class BaseCollector(ABC):
    def __init__(self, source_config: dict):
        self.source_config = source_config
        self.name = source_config.get("name", self.__class__.__name__)

    @abstractmethod
    def collect(self) -> List[Event]:
        raise NotImplementedError