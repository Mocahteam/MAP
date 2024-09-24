from typing import Iterator
from Event import Event

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
    def nbEventBetweenBounds(self) -> int:
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
        self.explored:bool = False
    
    def __str__(self) -> str:
        return str(self.event)+": "+str(self.boundlist)
        
    def __eq__ (self, other:object) -> bool:
        return isinstance(other, Episode) and self.event == other.event and self.boundlist == other.boundlist
    
class NonOverlappedEpisode(Episode):
    # weight of the support in relation to proximity parameter. Must be included between [0, 1]. 0 means the support is ignored (only proximity). 1 means the proximity is ignored (only support)
    WEIGHT_SUPPORT:float
    # control balancing between inside and outside proximity of episodes. Must be included between [0, 1]. 0 means take only inside proximity in consideration (no outside proximity). 1 means take only outside proximity in consideration (no inside proximity). If WEIGH_SUPPORT is set to 1, PROXIMITY_BALANCING is useless.
    PROXIMITY_BALANCING:float

    # Support maximum
    MAX_SUP:int

    def __init__ (self, model: Event) -> None:
        # Initialiser la classe parente A en utilisant les valeurs de l'instance de A
        super().__init__(model, BoundList([]))
        # Proximité interne de cet épisode comprise entre [0, 1] (0 très positif) : proportion d'évènements intercallés à l'intérieur de chaque bound de l'épisode
        self.__insideProx:float = 1
        # Proximité externe de cet épisode comprise entre [0, 1] (0 très positif) : proportion d'évènements intercallés entre chaque bounds de 
        self.__outsideProx:float = 1

        # Le score se décompose en 2 partie
        # La partie 1 la performance de l'épisode de point de vu de son support
        self.__part1:float = 0
        # La partie 1 la performance de l'épisode de point de vu de ses proximités (interne et externe)
        self.__part2:float = 0
        self.__score:float = 0

    # Détermine si un Episode est plus petit qu'un autre Episode en fonction de son score
    def __lt__(self, other: object) -> bool:
        if isinstance(other, NonOverlappedEpisode):
            if self.getScore() < other.getScore() or (self.getScore() == other.getScore() and self.getSupport() < other.getSupport()):
                return True
            else:
                return False
        else:
            return self < other

    # Retourne le support de cet épisode
    def getSupport(self) -> int:
        return len(self.boundlist)

    # Calcule et met à jour le score de cet épisode
    def getScore(self) -> float:
        # Indépendamenet de WEIGHT_SUPPORT (même s'il est défini à 0 <=> ignorer le support) on discalifie les épisodes qui n'ont pas un support au moins égal à 2, en effet on cherche les épisodes qui se répètent au moins une fois (support >= 2)
        if self.getSupport() >= 2 and self.boundlist.durty:
            self.__part1 = self.getSupport()/NonOverlappedEpisode.MAX_SUP
            # la partie 2 du score concerne la proximité. On cherche à réduire au maximum les proximités interne et externe.
            # Calcul du score de proximité interne
            self.__insideProx = (self.boundlist.nbEventsInsideBounds-(self.event.getLength()*len(self.boundlist)))/self.boundlist.nbEventsInsideBounds if self.boundlist.nbEventsInsideBounds > 0 else 0
            # Calcul du score de proximité externe
            self.__outsideProx = self.boundlist.nbEventBetweenBounds/(self.boundlist[-1][1] - self.boundlist[0][0])

            #  Le calcul des proximités internes et externes donnent des valeurs comprises dans l'intervalle [0,1] avec 0 très positif, donc on prend l'opposé et on balance les deux proximités en fonction du PROXIMITY_BALANCING
            self.__part2 = (1-NonOverlappedEpisode.PROXIMITY_BALANCING) * (1-self.__insideProx) + NonOverlappedEpisode.PROXIMITY_BALANCING * (1-self.__outsideProx)
            # Si WEIGHT_SUPPORT == 1 prise en compte uniquement du support, si == 0 prise en compte uniquement de la longueur du pattern du support

            if self.__insideProx < 0 or self.__outsideProx < 0:
                print ("BUUUG")

            self.__score = NonOverlappedEpisode.WEIGHT_SUPPORT*self.__part1 + (1-NonOverlappedEpisode.WEIGHT_SUPPORT)*self.__part2

            self.boundlist.durty = False
        
        return self.__score