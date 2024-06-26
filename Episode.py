from Event import Event

class Episode:
    # weight of the support in relation to proximity parameter. Must be included between [0, 1]. 0 means the support is ignored (only proximity). 1 means the proximity is ignored (only support)
    WEIGHT_SUPPORT:float
    # control balancing between inside and outside proximity of episodes. Must be included between [0, 1]. 0 means take only inside proximity in consideration (no outside proximity). 1 means take only outside proximity in consideration (no inside proximity). If WEIGH_SUPPORT is set to 1, PROXIMITY_BALANCING is useless.
    PROXIMITY_BALANCING:float

    # enregistre parmis les top-k le support minimal
    MIN_SUPPORT:int
    # enregistre parmis les top-k le support maximal
    MAX_SUPPORT:int

    def __init__ (self, event: Event, positions: list[tuple[int, int]]) -> None:
        self.event = event
        self.boundlist = positions
        self.explored = False
        self.durty = True
        self.score = -1

    # Détermine si un Episode est plus petit qu'un autre Episode à partir de leur score
    def __lt__(self, other: object) -> bool:
        if isinstance(other, Episode):
            selfScore:float = self.getScore()
            otherScore:float = other.getScore()
            if selfScore < otherScore or (selfScore == otherScore and str(self) < str(other)):
                return True
            else:
                return False
        else:
            return self < other
    
    def __str__(self) -> str:
        return str(self.event)+": "+str(self.boundlist)

    # Retourne le support de cet épisode
    def getSupport(self) -> int:
        return len(self.boundlist)
    
    def add(self, pos: tuple[int, int]) -> None:
        self.boundlist.append(pos)
        self.durty = True

    # calcul de la proximité externe de cet épisode comprise entre [0, 1] : proportion d'évènements intercallés entre chaque bounds
    def getOutsideProximity(self) -> float:
        if self.getSupport() > 1:
            nbEventBetweenBounds:int = 0
            for i in range(1, self.getSupport()):
                nbEventBetweenBounds += self.boundlist[i][0] - self.boundlist[i-1][1] - 1 # comptabilisé le nombre d'évènement entre deux bounds
            return nbEventBetweenBounds/(self.boundlist[-1][1] - self.boundlist[0][0]) # calcul de la proportion de proximité externe
        elif self.getSupport() == 1:
            return 0
        else:
            return 1
    
    # calcul de la proximité interne de cet épisode comprise entre [0, 1] : proportion d'évènements intercallés à l'intérieur de chaque bound
    def getInsideProximity(self) -> float:
        if self.event.getLength() > 0 and self.getSupport() > 0:
            nbAdditionalEventInsideBounds:int = 0
            for bound in self.boundlist:
                nbAdditionalEventInsideBounds += bound[1] - bound[0] + 1 - self.event.getLength() # comptabiliser le nombre d'évènement intercalés à l'intérieur du bound
            return nbAdditionalEventInsideBounds/(self.event.getLength()*self.getSupport()) # calcul de la proportion de proximité interne
        else:
            return 1

    # Retourne le score de cet épisode
    def getScore(self) -> float:
    
        if self.getSupport() <= 1:
            return 0 # Indépendamenet de WEIGHT_SUPPORT (même s'il est défini à 0 <=> ignorer le support) on discalifie les épisodes qui n'ont pas un support au moins égal à 2, en effet on cherche les épisodes qui se répètent au moins une fois (support >= 2)
        part1:float = self.getSupport()/Episode.MAX_SUPPORT
        # la partie 2 du score concerne la proximité. On cherche à réduire au maximum les proximités interne et externe. Le calcul des proximités internes et externes retourne une valeur comprise dans l'intervalle [0,1] avec 0 très positif, donc on prend l'opposé et on balance les deux proximités en fonction du PROXIMITY_BALANCING
        part2:float = (1-Episode.PROXIMITY_BALANCING) * (1-self.getInsideProximity()) + Episode.PROXIMITY_BALANCING * (1-self.getOutsideProximity())
        # Si WEIGHT_SUPPORT == 1 prise en compte uniquement du support, si == 0 prise en compte uniquement de la longueur du pattern du support
        newScore = Episode.WEIGHT_SUPPORT*part1 + (1-Episode.WEIGHT_SUPPORT)*part2
        if self.durty == False and self.score != newScore:
            print ("Problème avec le durty !!!!")
        else:
            self.durty = False
        self.part1 = part1
        self.part2 = part2
        self.inside = 1-self.getInsideProximity()
        self.outside = 1-self.getOutsideProximity()
        self.score = newScore
        return self.score