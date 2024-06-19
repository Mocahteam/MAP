class Event:
    def __init__(self) -> None:
        pass

    def getLength(self) -> int:
        return 0

class Call(Event):
    def __init__(self, call:str) -> None:
        self.call:str = call
    
    def __str__(self) -> str:
        return self.call
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Call):
            return self.call == other.call
        return False
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        return hash(self.call)

    def getLength(self) -> int:
        return 1

class Sequence(Event):
    def __init__(self) -> None:
        self.event_list:list[Event] = []

    def __str__(self) -> str:
        if len(self.event_list) == 0:
            return "[]"
        export = '['+str(self.event_list[0])
        for e in self.event_list[1:]:
            export += ','+str(e)
        export += ']'
        return export
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Sequence):
            return self.event_list == other.event_list
        return False
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        return hash(self.event_list)

    def getLength(self) -> int:
        return len(self.event_list)