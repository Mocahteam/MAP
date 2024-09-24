import copy
from Episode import BoundList, Episode, NonOverlappedEpisode
from Event import Event, Sequence
from bisect import insort

# PTKE => Proximity Top-K Frequent Episodes
class PTKE:
    K:int
    # GAP_RATIO controls the size of gaps between episodes in relation to the length of the episode. GAP_RATIO is a multiplier used by to jump events proportionaly to episode size (will produce optional events). 0 means episodes will be merge if no gap exists between them.
    GAP_RATIO:float

    def __init__(self) -> None:
        self.kEpisodes:list[NonOverlappedEpisode] = []
        self.minScore:float = 0

    # Calcule les meilleurs épisodes sans chevauchement des bounds à partir d'une liste d'évènements
    #
    # :param event_list: Liste des évènements desquels extraire les meilleurs épisodes
    # :return: La liste des épisodes sans chevauchement des bounds ayant le meilleur score
    def getBestEpisodes(self, event_list: list[Event]) -> list[NonOverlappedEpisode]:
        self.minScore = 1
        NonOverlappedEpisode.MAX_SUP = 1
        # Map enregistrant pour chaque event ses positions d'apparition
        mapEventToLocations:dict[Event, list[int]] = {}
        # Map enregistrant pour chaque event ses positions d'apparition
        mapEventToNOE:dict[Event, NonOverlappedEpisode] = {}
        # parcourir toutes les traces de la séquence et enregistrer les positions d'apparition de chaque item
        for i in range(len(event_list)):
            event:Event = event_list[i]
            if event in mapEventToLocations:
                # trace déjà connue => ajout de la nouvelle position
                mapEventToLocations[event].append(i)
                mapEventToNOE[event].boundlist.append((i,i))
            else:
                # Nouvelle trace détectée
                # encapsulation de cet event dans une séquence pour former le nouveau pattern
                pattern:Sequence = Sequence()
                pattern.event_list.append(event)
                # Intégration de cette séquence en tant qu'épisode
                noe:NonOverlappedEpisode = NonOverlappedEpisode(pattern)
                noe.boundlist.append((i, i))
                mapEventToNOE[event] = noe
                # on enregistre aussi simplement sa possition
                mapEventToLocations[event] = [i]
            # On met à jour le support maximal
            currentSup:int = len(mapEventToLocations[event])
            NonOverlappedEpisode.MAX_SUP = currentSup if currentSup > NonOverlappedEpisode.MAX_SUP else NonOverlappedEpisode.MAX_SUP
        
        # initialisation des k premiers épisodes 
        for event, noe in mapEventToNOE.items():
            self.saveEpisodeIn(noe, self.kEpisodes)
                
        needExploration:bool = True
        while needExploration:
            newEpisodes:list[Episode] = []
            # Etendre chacun des meilleurs épisodes avec un évènement supplémentaire
            for kEpisode in self.kEpisodes:
                if not kEpisode.explored:
                    for event, positions in mapEventToLocations.items():
                        newEpisode:Episode = self.extendEpisodeWithEvent(kEpisode, event, positions)
                        newEpisodes.append(newEpisode)
                    kEpisode.explored = True
            # ajouter les nouveaux épisodes aux top-k
            for newE in newEpisodes:
                # Ici les bounds des kEpisodes peuvent se chevaucher ([... <3,5> <4,6> ...] => dans cet exemple le premier bound fini à 5 alors que le suivant commence à 4). Pour la suite de l'algo on ne peut avoir de chevauchements entre les bounds. On va donc créer autant d'éposides que nécessaire pour désenlacer les bounds de chacun des kEpisodes
                noes:list[NonOverlappedEpisode] = self.unoverlapEpisode(newE)
                for noe in noes:
                    self.saveEpisodeIn(noe, self.kEpisodes)
            needExploration = len(newEpisodes) > 0
        
        # Les épisodes sont maintenant désenlacés, on sélectionne les meilleurs
        bestNonOverlappedEpisodes:list[NonOverlappedEpisode] = []
        for nonOverlappedEpisode in self.kEpisodes:
            if len(bestNonOverlappedEpisodes) == 0 or nonOverlappedEpisode.getScore() == bestNonOverlappedEpisodes[0].getScore():
                bestNonOverlappedEpisodes.append(nonOverlappedEpisode)
            elif nonOverlappedEpisode.getScore() > bestNonOverlappedEpisodes[0].getScore():
                bestNonOverlappedEpisodes = [nonOverlappedEpisode]

        return bestNonOverlappedEpisodes

    # Désenlace un épisode et retourne les K meilleurs candidats
    def unoverlapEpisode(self, episode:Episode) -> list[NonOverlappedEpisode]:
        nonOverlappedEpisodes:list[NonOverlappedEpisode] = []
        # Utilisation de l'épisode comme modèle pour initialiser la liste
        nonOverlappedEpisodes.append(NonOverlappedEpisode(copy.deepcopy(episode.event)))
        # 1 - On désenlace la boundlist
        # on parcours tous les bounds suivants
        for bound in episode.boundlist:
            # placer ce bound dans les scenarios
            placed:bool = False
            # tenter de placer ce bound à la fin des scénarios
            for noe in nonOverlappedEpisodes:
                if len (noe.boundlist) == 0 or noe.boundlist[-1][1] < bound[0]:
                    noe.boundlist.append(bound)
                    placed = True
            # Si le bound n'a pas pu être placé tenter de lui trouver une place au coeur d'un des scénarios
            if not placed:
                newEpisodes:list[NonOverlappedEpisode] = []
                for noe in nonOverlappedEpisodes:
                    # Remonter ce scénario jusqu'à trouver un emplacement valide
                    i:int = len(noe.boundlist)-1
                    while i >= 0 and noe.boundlist[i][1] >= bound[0]:
                        i -= 1
                    # Si on a trouvé une place au coeur du scénario, on duplique son début et on l'ajoute à la suite
                    if i >= 0:
                        newNoe:NonOverlappedEpisode = NonOverlappedEpisode(copy.deepcopy(episode.event))
                        newNoe.boundlist = noe.boundlist.slice(0, i+1)
                        newNoe.boundlist.append(bound)
                        newEpisodes.append(newNoe)
                        placed = True
                # on ajoute tout ces nouveaux scénarios dans la liste des épisodes désenlacés
                for newNoe in newEpisodes:
                    self.saveEpisodeIn(newNoe, nonOverlappedEpisodes)
            # Si le bound n'a pas été placé dans un scénario existant, on crée un nouveau scénario commençant par ce bound
            if not placed:
                newNoe:NonOverlappedEpisode = NonOverlappedEpisode(copy.deepcopy(episode.event))
                newNoe.boundlist = BoundList([bound])
                self.saveEpisodeIn(newNoe, nonOverlappedEpisodes)

        return nonOverlappedEpisodes

    # Obtention du support minimal
    def getMinSup(self) -> int:
        # Tantqu'on n'a pas encore identifié K épisodes, considérer le support minimal à 0 pour autoriser de nouvelles explorations
        if len(self.kEpisodes) < PTKE.K:
            return 0
        else:
            return self.kEpisodes[0].getSupport()

	# Enregistre un épisode dans l'ensemble de top-k pattern.
	# 
	# :param episode: the episode to be saved
    def saveEpisodeIn(self, episode: NonOverlappedEpisode, list:list[NonOverlappedEpisode]) -> None:
        if episode not in list:
            # insertion de l'épisode dans les meilleurs k episodes et maintient de la liste triée par le score
            if len(list) < PTKE.K or episode.getScore() > list[0].getScore():
                insort(list, episode)
            if len(list) > PTKE.K:
                list.pop(0) # ne conserver que les K meilleurs

    # Etend un episode donné avec un event
    #
    # :param episode: episode à étendre
    # :param event: évènement à tenter d'intégrer à l'épisode
    # :param eventPositions: liste des positions de event dans la séquence
    # 
    # :return: l'episode étendu
    def extendEpisodeWithEvent(self, episode:Episode, event:Event, eventPositions:list[int]) -> Episode:
        # Calcul de la fenêtre maximale autorisée => la longueur cumulée du kième épisodes + 1 (le nouvel evènement) * (1 + GAP_RATIO)=> pour accepter d'éventuelles traces intercalées
        max_window_size = (episode.event.getLength()+1)*(1+PTKE.GAP_RATIO)
        # Calcul des bounds contenant la fusion des bounds de l'épisode avec les positions d'un évènement
        newBoundlist:BoundList = BoundList([])
        i:int = 0
        j:int = 0

        while i < len(episode.boundlist) and j < len(eventPositions):
            # Avancer sur la position de l'event tant qu'elle commence avant la position de fin du bound courant de l'épisode => ça ne sert à rien d'explorer une position de l'event qui commence avant la fin du bound courant de l'épisode
            # episode : [... <?,6> ...]
            # event   : [... <3,3> ...] => on fait avancer l'event pour tenter de trouver une position commence après le 6
            if episode.boundlist[i][1] >= eventPositions[j]:
                j += 1
            # Avancer sur le bound suivant de l'épisode tant que la distance entre le début de ce bound et la position de l'event est supérieur ou égal à la taille de la fenêtre maximale autorisée
            # episode : [... <4,?> ...] => on fait avancer l'épisode pour tenter de trouver un bound plus proche de la position de l'évènement
            # event   : [... <9,9> ...]
            # max   : 3
            elif eventPositions[j] - episode.boundlist[i][0] >= max_window_size:
                i += 1
            # Ici les contraintes suivantes sont respectées :
            #  - le bound de fin de l'épisode se situe avant la position de l'évènement
            #  - la distance entre le bound de l'épisode et la position de l'évènement entre dans le fenêtre (< max_window_size)
            # on ajoute un boundlist et on passe au bound suivante de l'épisode
            # episode : [... <6,7> ...] => on passe au bound suivant
            # event   : [... <9,9> ...]
            # new     : [... <6,9>]     => on ajoute à new un nouveau bound qui commence au début de celui de l'épisode jusqu'à la position de l'évènement
            else:
                newBoundlist.append((episode.boundlist[i][0], eventPositions[j]))
                i += 1

	    # clonage du contenu de l'épisode
        newEpisode:Episode = Episode(copy.deepcopy(episode.event), BoundList([]))
        # ajout le l'évènement ajouté
        if isinstance(newEpisode.event, Sequence):
            newEpisode.event.event_list.append(event)
        else:
            raise TypeError
        # redéfinition de la bound list avec la nouvelle calculée
        newEpisode.boundlist = newBoundlist

        return newEpisode
            
