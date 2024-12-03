from typing import Iterator, Optional
from Event import Event
from abc import abstractmethod

class BoundList:
    def __init__(self, initial_list:list[tuple[int, int]]) -> None:
        # Initialiser la liste
        self._list:list[tuple[int, int]] = []

        # Accumulation du nombre d'évènements de chaque bounds
        self.__nbEventsInsideBounds:int = 0
        # Accumulation du nombre d'évènement entre les différents bounds
        self.__nbEventBetweenBounds:int = 0

        # Copie de la liste
        for bound in initial_list:
            self.append(bound)
        
        self.durty:bool = True

    @property
    def nbEventsInsideBounds(self) -> int:
        return self.__nbEventsInsideBounds
    
    @property
    def nbEventsBetweenBounds(self) -> int:
        return self.__nbEventBetweenBounds

    def __getitem__(self, index:int) -> tuple[int, int]:
        return self._list[index]
        
    def __iter__(self) -> Iterator[tuple[int, int]]:
        return iter(self._list)  # Renvoie un itérateur de la liste

    def __len__(self) -> int:
        return len(self._list)
        
    def __eq__ (self, other:object) -> bool:
        return isinstance(other, BoundList) and len(self._list) == len(other._list) and self._list == other._list
    
    def slice(self, start:int, stop:int, step:int=1) -> "BoundList":
        return BoundList(self._list[start:stop:step])

    def append(self, newBound:tuple[int, int]) -> None:
        # ajout du nouveau bound à la liste
        self._list.append(newBound)
        # mise à jour des données utiles au calcul des proximités
        self.__nbEventsInsideBounds += newBound[1] - newBound[0] + 1
        if len(self._list) > 1:
            self.__nbEventBetweenBounds += self._list[-1][0] - self._list[-2][1] - 1 # comptabiliser le nombre d'évènement entre le dernier bound (celui que l'on vient d'ajouter) et l'avant dernier
        self.durty = True
    
    def reverse(self) -> None:
        self._list.reverse()

    def __repr__(self) -> str:
        # Représentation pour l'impression
        return repr(self._list)

    def __str__(self) -> str:
        # Représentation pour l'impression
        return str(self._list)

class Episode:
    def __init__ (self, event: Event, positions: BoundList) -> None:
        self.event:Event = event
        self.boundlist:BoundList = positions
    
    def __str__(self) -> str:
        return str(self.event)+": "+str(self.boundlist)
        
    def __eq__ (self, other:object) -> bool:
        return isinstance(other, Episode) and self.event == other.event and self.boundlist == other.boundlist

class Scorable:
    def __init__ (self) -> None:
        self._score:float = -1
        
    @abstractmethod
    def getSupport(self) -> int:
        pass
        
    @abstractmethod
    def isDurty(self) -> bool:
        pass

    @abstractmethod
    def setDurty(self, state:bool) -> None:
        pass

    @abstractmethod
    def getNbEventsInsideBounds(self) -> int:
        pass

    @abstractmethod
    def getNbEventsBetweenBounds(self) -> int:
        pass

    @abstractmethod
    def getEventLength(self) -> int:
        pass

    @abstractmethod
    def getEpisodeLength(self) -> int:
        pass

    # Détermine si un Scorable est plus petit qu'un autre Scorable en fonction de son score. Comme on veut en premier le Scorable avec le score le plus fort (voir insort de PTKE::saveInTopK) on considère qu'un Scorable avec un score plus fort est considéré plus petit qu'un scorable avec un code plus faible. En inversant ainsi la logique on maintient la liste des topk triée du meilleur score au moins bon score
    def __lt__(self, other: "Scorable") -> bool:
        if self.getScore() > other.getScore() or (self.getScore() == other.getScore() and self.getSupport() > other.getSupport()):
            return True
        else:
            return False
    
    def getScore(self) -> float:
        # Indépendamenet de WEIGHT_SUPPORT (même s'il est défini à 0 <=> ignorer le support) on discalifie les épisodes qui n'ont pas un support au moins égal à 2, en effet on cherche les épisodes qui se répètent au moins une fois (support >= 2)
        if self.getSupport() >= 2 and self.isDurty():
            # Proximité interne de cet épisode comprise entre [0, 1] (0 très positif) : proportion d'évènements intercallés à l'intérieur de chaque bound de l'épisode
            insideProx:float = 1
            # Proximité externe de cet épisode comprise entre [0, 1] (0 très positif) : proportion d'évènements intercallés entre chaque bounds de 
            outsideProx:float = 1

            # Le score se décompose en 2 partie
            # La partie 1 : la performance de l'épisode de point de vu de son support
            part1:float = 0
            # La partie 2 : la performance de l'épisode de point de vu de ses proximités (interne et externe)
            part2:float = 0

            part1 = self.getSupport()/NonOverlappedEpisode.MAX_SUP
            # la partie 2 du score concerne la proximité. On cherche à réduire au maximum les proximités interne et externe.
            # Calcul du score de proximité interne
            nbEventsInsideBounds:int = self.getNbEventsInsideBounds()
            insideProx = (nbEventsInsideBounds-(self.getEventLength()*self.getSupport()))/nbEventsInsideBounds if nbEventsInsideBounds > 0 else 0
            # Calcul du score de proximité externe
            outsideProx = self.getNbEventsBetweenBounds()/self.getEpisodeLength()

            #  Le calcul des proximités internes et externes donnent des valeurs comprises dans l'intervalle [0,1] avec 0 très positif, donc on prend l'opposé et on balance les deux proximités en fonction du PROXIMITY_BALANCING
            part2 = (1-NonOverlappedEpisode.PROXIMITY_BALANCING) * (1-insideProx) + NonOverlappedEpisode.PROXIMITY_BALANCING * (1-outsideProx)
            # Si WEIGHT_SUPPORT == 1 prise en compte uniquement du support, si == 0 prise en compte uniquement de la longueur du pattern du support

            if insideProx < 0 or outsideProx < 0:
                print ("BUUUG")

            self._score = NonOverlappedEpisode.WEIGHT_SUPPORT*part1 + (1-NonOverlappedEpisode.WEIGHT_SUPPORT)*part2

            self.setDurty(False)
        
        return self._score        

class NonOverlappedEpisode(Episode, Scorable):
    # weight of the support in relation to proximity parameter. Must be included between [0, 1]. 0 means the support is ignored (only proximity). 1 means the proximity is ignored (only support)
    WEIGHT_SUPPORT:float
    # control balancing between inside and outside proximity of episodes. Must be included between [0, 1]. 0 means take only inside proximity in consideration (no outside proximity). 1 means take only outside proximity in consideration (no inside proximity). If WEIGH_SUPPORT is set to 1, PROXIMITY_BALANCING is useless.
    PROXIMITY_BALANCING:float

    # Support maximum
    MAX_SUP:int

    def __init__ (self, model: Event) -> None:
        Episode.__init__(self, model, BoundList([]))
        Scorable.__init__(self)
        self.explored:bool = False

    # Retourne le support de cet épisode
    def getSupport(self) -> int:
        return len(self.boundlist)
    
    def isDurty(self) -> bool:
        return self.boundlist.durty
    
    def setDurty(self, state:bool) -> None:
        self.boundlist.durty = state

    def getNbEventsInsideBounds(self) -> int:
        return self.boundlist.nbEventsInsideBounds

    def getNbEventsBetweenBounds(self) -> int:
        return self.boundlist.nbEventsBetweenBounds

    def getEventLength(self) -> int:
        return self.event.getLength()

    def getEpisodeLength(self) -> int:
        return self.boundlist[-1][1] - self.boundlist[0][0]
    
class BoundGraph (Scorable):
    def __init__(self, event:Event, bound:tuple[int, int], parent:Optional["BoundGraph"] = None) -> None:
        super().__init__()
        self.event = event
        self.bound:tuple[int, int] = bound
        self.parent:Optional[BoundGraph] = parent
        self.childs:list[BoundGraph] = []
        self.support:int = parent.support+1 if parent != None else 1
        self.nbEventsInsideBounds:int = (parent.nbEventsInsideBounds if parent != None else 0) + (bound[1]-bound[0]+1)
        self.nbEventsBetweenBounds:int = (parent.nbEventsBetweenBounds if parent != None else 0) + ((bound[0] - parent.bound[1] - 1) if parent != None else 0)
        if parent != None:
            parent.childs.append(self)
        self.root:BoundGraph = parent.root if parent != None else self
    
    def getSupport(self) -> int:
        return self.support
        
    def __eq__ (self, other:object) -> bool:
        return isinstance(other, BoundGraph) and self.bound == other.bound and self.parent is other.parent

    def hasChild(self, bound:tuple[int, int]) -> bool:
        for child in self.childs:
            if child.bound == bound:
                return True
        return False
    
    def isDurty(self) -> bool:
        return self._score == -1
    
    def setDurty(self, state:bool) -> None:
        pass

    def getNbEventsInsideBounds(self) -> int:
        return self.nbEventsInsideBounds

    def getNbEventsBetweenBounds(self) -> int:
        return self.nbEventsBetweenBounds

    def getEventLength(self) -> int:
        return self.event.getLength()

    def getEpisodeLength(self) -> int:
        return self.bound[1] - self.root.bound[0]
    
    # Pour la construction du scénario sous le forme d'un arbre on privilégie en premier lieu le support pour favoriser la construction d'Episode sans chevauchement avec le plus de bound possible. Lorsque les support sont égaux (ce qui arrive souvent lors de la construction de l'arbre), on y ajoute le calcul du score de super pour modérer le support en fonction des paramètres influant le calcul du score
    def getScore(self) -> float:
        return self.getSupport()+super().getScore()