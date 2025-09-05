from typing import Iterator, Optional
from Event import Event
from abc import abstractmethod

class BoundList:
    """
    A list-like container for managing bounds (pairs of start and end positions).
    
    This class maintains a list of bounds (tuples of integers representing start and end positions)
    and tracks statistics about the events within and between these bounds.
    
    Attributes:
        durty (bool): Flag indicating if the bound list has been modified
        _list (list[tuple[int, int]]): Internal list of bounds
        __nbEventsInsideBounds (int): Total number of events within all bounds
        __nbEventBetweenBounds (int): Total number of events between consecutive bounds
    """
    def __init__(self, initial_list:list[tuple[int, int]]) -> None:
        """
        Initialize a new BoundList.
        
        Args:
            initial_list (list[tuple[int, int]]): Initial list of bounds to copy
        """
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
        """
        Get the total number of events within all bounds.
        
        Returns:
            int: Total number of events within bounds
        """
        return self.__nbEventsInsideBounds
    
    @property
    def nbEventsBetweenBounds(self) -> int:
        """
        Get the total number of events between consecutive bounds.
        
        Returns:
            int: Total number of events between bounds
        """
        return self.__nbEventBetweenBounds

    def __getitem__(self, index:int) -> tuple[int, int]:
        """
        Get a bound at the specified index.
        
        Args:
            index (int): Index of the bound to retrieve
            
        Returns:
            tuple[int, int]: The bound at the specified index
        """
        return self._list[index]
        
    def __iter__(self) -> Iterator[tuple[int, int]]:
        """
        Get an iterator over the bounds.
        
        Returns:
            Iterator[tuple[int, int]]: Iterator over the bounds
        """
        return iter(self._list)  # Renvoie un itérateur de la liste

    def __len__(self) -> int:
        """
        Get the number of bounds in the list.
        
        Returns:
            int: Number of bounds
        """
        return len(self._list)
        
    def __eq__ (self, other:object) -> bool:
        """
        Check if two BoundLists are equal.
        
        Args:
            other (object): Object to compare with
            
        Returns:
            bool: True if the lists contain the same bounds in the same order
        """
        return isinstance(other, BoundList) and len(self._list) == len(other._list) and self._list == other._list
    
    def slice(self, start:int, stop:int, step:int=1) -> "BoundList":
        """
        Create a new BoundList containing a slice of bounds.
        
        Args:
            start (int): Start index
            stop (int): Stop index
            step (int, optional): Step size. Defaults to 1
            
        Returns:
            BoundList: New BoundList containing the specified slice
        """
        return BoundList(self._list[start:stop:step])

    def append(self, newBound:tuple[int, int]) -> None:
        """
        Add a new bound to the list and update statistics.
        
        Args:
            newBound (tuple[int, int]): New bound to append
        """
        # ajout du nouveau bound à la liste
        self._list.append(newBound)
        # mise à jour des données utiles au calcul des proximités
        self.__nbEventsInsideBounds += newBound[1] - newBound[0] + 1
        if len(self._list) > 1:
            self.__nbEventBetweenBounds += self._list[-1][0] - self._list[-2][1] - 1 # comptabiliser le nombre d'évènement entre le dernier bound (celui que l'on vient d'ajouter) et l'avant dernier
        self.durty = True
    
    def reverse(self) -> None:
        """
        Reverse the order of bounds in the list.
        """
        self._list.reverse()

    def __repr__(self) -> str:
        """
        Get a string representation for debugging.
        
        Returns:
            str: Debug representation of the BoundList
        """
        # Représentation pour l'impression
        return repr(self._list)

    def __str__(self) -> str:
        """
        Get a string representation of the BoundList.
        
        Returns:
            str: String representation of the bounds
        """
        # Représentation pour l'impression
        return str(self._list)

class Episode:
    """
    Represents an episode consisting of an event and its positions in a sequence.
    
    An episode combines an event with a list of bounds where this event occurs.
    
    Attributes:
        event (Event): The event that constitutes this episode
        boundlist (BoundList): List of positions where this event occurs
    """
    def __init__ (self, event: Event, positions: BoundList) -> None:
        """
        Initialize a new Episode.
        
        Args:
            event (Event): The event for this episode
            positions (BoundList): List of positions where this event occurs
        """
        self.event:Event = event
        self.boundlist:BoundList = positions
    
    def __str__(self) -> str:
        """
        Get a string representation of the episode.
        
        Returns:
            str: String representation showing the event and its bounds
        """
        return str(self.event)+": ("+str(len(self.boundlist))+") "+str(self.boundlist)
    
    def __repr__(self) -> str:
        """
        Get a string representation of the episode.
        
        Returns:
            str: String representation showing the event and its bounds
        """
        return str(self.event)+": ("+str(len(self.boundlist))+") "+str(self.boundlist)
        
    def __eq__ (self, other:object) -> bool:
        """
        Check if two episodes are equal.
        
        Args:
            other (object): Object to compare with
            
        Returns:
            bool: True if both episodes have the same event and bounds
        """
        return isinstance(other, Episode) and self.event == other.event and self.boundlist == other.boundlist

class Scorable:
    """
    Abstract base class for objects that can be scored.
    
    This class provides a framework for scoring episodes based on their support,
    event distribution, and other metrics. The actual scoring logic is implemented
    in the getScore method.
    
    Attributes:
        _score (float): Cached score value, -1 indicates not yet calculated
    """
    def __init__ (self) -> None:
        """
        Initialize a new Scorable object with an invalid score.
        """
        self._score:float = -1
        
    @abstractmethod
    def getSupport(self) -> int:
        """
        Get the support value for this object.
        
        Returns:
            int: Support value
        """
        pass
        
    @abstractmethod
    def isDurty(self) -> bool:
        """
        Check if the object's score needs recalculation.
        
        Returns:
            bool: True if the score needs to be recalculated
        """
        pass

    @abstractmethod
    def setDurty(self, state:bool) -> None:
        """
        Set whether the object's score needs recalculation.
        
        Args:
            state (bool): New dirty state
        """
        pass

    @abstractmethod
    def getNbEventsInsideBounds(self) -> int:
        """
        Get the number of events within bounds.
        
        Returns:
            int: Number of events within bounds
        """
        pass

    @abstractmethod
    def getNbEventsBetweenBounds(self) -> int:
        """
        Get the number of events between bounds.
        
        Returns:
            int: Number of events between bounds
        """
        pass

    @abstractmethod
    def getEventLength(self) -> int:
        """
        Get the length of the event.
        
        Returns:
            int: Event length
        """
        pass

    @abstractmethod
    def getEpisodeLength(self) -> int:
        """
        Get the total length of the episode.
        
        Returns:
            int: Episode length
        """
        pass

    def __lt__(self, other: "Scorable") -> bool:
        """
        Compare two Scorable objects based on their scores.
        
        Note: The comparison is inverted to maintain a list sorted from highest to lowest score.
        
        Args:
            other (Scorable): Object to compare with
            
        Returns:
            bool: True if this object should be considered less than the other
        """
        # Détermine si un Scorable est plus petit qu'un autre Scorable en fonction de son score. Comme on veut en premier le Scorable avec le score le plus fort (voir insort de PTKE::saveInTopK) on considère qu'un Scorable avec un score plus fort est considéré plus petit qu'un scorable avec un code plus faible. En inversant ainsi la logique on maintient la liste des topk triée du meilleur score au moins bon score
        if self.getScore() > other.getScore() or (self.getScore() == other.getScore() and self.getSupport() > other.getSupport()):
            return True
        else:
            return False
    
    def getScore(self) -> float:
        """
        Calculate and return the score for this object.
        
        The score is based on:
        1. Support (must be >= 2)
        2. Internal proximity (events within bounds)
        3. External proximity (events between bounds)
        
        The final score is a weighted combination of support and proximity scores,
        controlled by WEIGHT_SUPPORT and PROXIMITY_BALANCING parameters.
        
        Returns:
            float: Calculated score, or cached score if not dirty
        """
        # Indépendamenet de WEIGHT_SUPPORT (même s'il est défini à 0 <=> ignorer le support) on discalifie les épisodes qui n'ont pas un support au moins égal à 2, en effet on cherche les épisodes qui se répètent au moins une fois (support >= 2)
        if self.getSupport() >= 2 and self.isDurty():
            # Proximité interne de cet épisode comprise entre [0, 1] (0 très positif) : proportion d'évènements intercallés à l'intérieur de chaque bound de l'épisode
            insideProx:float = 1
            # Proximité externe de cet épisode comprise entre [0, 1] (0 très positif) : proportion d'évènements intercallés entre chaque bounds de l'épisode
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
            insideProx = (1-(self.getEventLength()*self.getSupport())/nbEventsInsideBounds) if nbEventsInsideBounds > 0 else 0
            # Calcul du score de proximité externe
            outsideProx = self.getNbEventsBetweenBounds()/self.getEpisodeLength()

            #  Le calcul des proximités internes et externes donnent des valeurs comprises dans l'intervalle [0,1] avec 0 très positif, donc on prend l'opposé et on balance les deux proximités en fonction du PROXIMITY_BALANCING
            part2 = (1-NonOverlappedEpisode.PROXIMITY_BALANCING) * (1-insideProx) + NonOverlappedEpisode.PROXIMITY_BALANCING * (1-outsideProx)

            if insideProx < 0 or outsideProx < 0:
                print ("BUUUG")

            # Si WEIGHT_SUPPORT == 1 prise en compte uniquement du support, si == 0 prise en compte uniquement de la longueur du pattern du support
            self._score = NonOverlappedEpisode.WEIGHT_SUPPORT*part1 + (1-NonOverlappedEpisode.WEIGHT_SUPPORT)*part2

            self.setDurty(False)
        
        return self._score        

class NonOverlappedEpisode(Episode, Scorable):
    """
    An episode implementation that ensures non-overlapping occurrences.
    
    This class combines the Episode and Scorable interfaces to represent episodes
    where each occurrence (bound) does not overlap with others. The scoring takes
    into account both support and proximity metrics.
    
    Class Attributes:
        WEIGHT_SUPPORT (float): Weight given to support vs proximity in scoring (0-1)
        PROXIMITY_BALANCING (float): Balance between internal and external proximity (0-1)
        MAX_SUP (int): Maximum possible support value
    
    Attributes:
        explored (bool): Whether this episode has been fully explored
    """
    # weight of the support in relation to proximity parameter. Must be included between [0, 1]. 0 means the support is ignored (only proximity). 1 means the proximity is ignored (only support)
    WEIGHT_SUPPORT:float
    # control balancing between inside and outside proximity of episodes. Must be included between [0, 1]. 0 means take only inside proximity in consideration (no outside proximity). 1 means take only outside proximity in consideration (no inside proximity). If WEIGH_SUPPORT is set to 1, PROXIMITY_BALANCING is useless.
    PROXIMITY_BALANCING:float

    # Support maximum
    MAX_SUP:int

    def __init__ (self, model: Event) -> None:
        """
        Initialize a new non-overlapped episode.
        
        Args:
            model (Event): The event model for this episode
        """
        Episode.__init__(self, model, BoundList([]))
        Scorable.__init__(self)
        self.explored:bool = False

    # Retourne le support de cet épisode
    def getSupport(self) -> int:
        """
        Get the number of non-overlapping occurrences of this episode.
        
        Returns:
            int: Number of bounds in the episode
        """
        return len(self.boundlist)
    
    def isDurty(self) -> bool:
        """
        Check if the episode's score needs recalculation.
        
        Returns:
            bool: True if the boundlist has been modified
        """
        return self.boundlist.durty
    
    def setDurty(self, state:bool) -> None:
        """
        Set whether the episode's score needs recalculation.
        
        Args:
            state (bool): New dirty state
        """
        self.boundlist.durty = state

    def getNbEventsInsideBounds(self) -> int:
        """
        Get the total number of events within all bounds.
        
        Returns:
            int: Number of events within bounds
        """
        return self.boundlist.nbEventsInsideBounds

    def getNbEventsBetweenBounds(self) -> int:
        """
        Get the total number of events between consecutive bounds.
        
        Returns:
            int: Number of events between bounds
        """
        return self.boundlist.nbEventsBetweenBounds

    def getEventLength(self) -> int:
        """
        Get the length of the episode's event.
        
        Returns:
            int: Length of the event
        """
        return self.event.getLength()

    def getEpisodeLength(self) -> int:
        """
        Get the total span of the episode from first to last bound.
        
        Returns:
            int: Distance between start of first bound and end of last bound
        """
        return self.boundlist[-1][1] - self.boundlist[0][0]
    
class BoundGraph (Scorable):
    """
    A graph structure representing bounds and their relationships.
    
    This class maintains a tree of bounds where each node represents a bound and
    edges represent valid transitions between bounds. The structure is used to
    track and score different combinations of bounds.
    
    Attributes:
        event (Event): The event associated with this bound
        bound (tuple[int, int]): The start and end positions of this bound
        parent (Optional[BoundGraph]): Parent node in the graph
        childs (list[BoundGraph]): Child nodes in the graph
        support (int): Number of bounds in the path to this node
        nbEventsInsideBounds (int): Total events within bounds in the path
        nbEventsBetweenBounds (int): Total events between bounds in the path
        root (BoundGraph): Root node of the graph
    """
    def __init__(self, event:Event, bound:tuple[int, int], parent:Optional["BoundGraph"] = None) -> None:
        """
        Initialize a new bound graph node.
        
        Args:
            event (Event): The event for this bound
            bound (tuple[int, int]): Start and end positions of the bound
            parent (Optional[BoundGraph], optional): Parent node. Defaults to None.
        """
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
        """
        Get the number of bounds in the path to this node.
        
        Returns:
            int: Support value
        """
        return self.support
        
    def __eq__ (self, other:object) -> bool:
        """
        Check if two bound graph nodes are equal.
        
        Args:
            other (object): Object to compare with
            
        Returns:
            bool: True if bounds and parents are the same
        """
        return isinstance(other, BoundGraph) and self.bound == other.bound and self.parent is other.parent

    def hasChild(self, bound:tuple[int, int]) -> bool:
        """
        Check if this node has a child with the given bound.
        
        Args:
            bound (tuple[int, int]): Bound to look for
            
        Returns:
            bool: True if a child with the given bound exists
        """
        for child in self.childs:
            if child.bound == bound:
                return True
        return False
    
    def isDurty(self) -> bool:
        """
        Check if the node's score needs recalculation.
        
        Returns:
            bool: True if score is invalid (-1)
        """
        return self._score == -1
    
    def setDurty(self, state:bool) -> None:
        """
        Set whether the node's score needs recalculation.
        This is a no-op for BoundGraph as score is always recalculated.
        
        Args:
            state (bool): New dirty state (ignored)
        """
        pass

    def getNbEventsInsideBounds(self) -> int:
        """
        Get total events within bounds in path to this node.
        
        Returns:
            int: Number of events within bounds
        """
        return self.nbEventsInsideBounds

    def getNbEventsBetweenBounds(self) -> int:
        """
        Get total events between bounds in path to this node.
        
        Returns:
            int: Number of events between bounds
        """
        return self.nbEventsBetweenBounds

    def getEventLength(self) -> int:
        """
        Get the length of the associated event.
        
        Returns:
            int: Event length
        """
        return self.event.getLength()

    def getEpisodeLength(self) -> int:
        """
        Get the total span from root to this bound.
        
        Returns:
            int: Distance from start of root bound to end of this bound
        """
        return self.bound[1] - self.root.bound[0]
    
    # Pour la construction du scénario sous le forme d'un arbre on privilégie en premier lieu le support pour favoriser la construction d'Episode sans chevauchement avec le plus de bound possible. Lorsque les support sont égaux (ce qui arrive souvent lors de la construction de l'arbre), on y ajoute le calcul du score de super pour modérer le support en fonction des paramètres influant le calcul du score
    def getScore(self) -> float:
        """
        Calculate and return the score for this node.
        
        The score combines the support count with the standard Scorable score
        to favor paths with more bounds while considering proximity metrics.
        
        Returns:
            float: Combined score value
        """
        return self.getSupport()+super().getScore()