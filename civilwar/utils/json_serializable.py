from abc import abstractmethod, ABC


class JsonSerializable(ABC):
    @abstractmethod
    def to_json(self):
        pass
