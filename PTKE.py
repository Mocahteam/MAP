import copy
from Episode import Episode, NonOverlappedEpisode
from Event import Call, Event, Sequence
from bisect import insort

# PTKE => Proximity Top-K Frequent Episodes
class PTKE:
    K:int
    QCSP_ALPHA:int

    def __init__(self) -> None:
        self.kEpisodes:list[Episode] = []
        self.minScore:float = 0

    # Calcule les meilleurs épisodes sans chevauchement des bounds à partir d'une liste d'évènements
    #
    # :param event_list: Liste des évènements desquels extraire les meilleurs épisodes
    # :return: La liste des épisodes sans chevauchement des bounds ayant le meilleur score
    def getBestEpisodes(self, event_list: list[Event]) -> list[NonOverlappedEpisode]:
        self.minScore = 1
        # Map enregistrant pour chaque event ses positions d'apparition
        mapEventToLocations:dict[Event, list[int]] = {}
        # parcourir toutes les traces de la séquence et enregistrer les positions d'apparition de chaque item
        for i in range(len(event_list)):
            event:Event = event_list[i]
            if event in mapEventToLocations:
                # trace déjà connue => ajout de la nouvelle position
                mapEventToLocations[event].append(i)
            else:
                # Nouvelle trace détectée => on crée une nouvelle entrée pour enregistrer sa possition
                mapEventToLocations[event] = [i]
        
        evtWithSuffisantSupport:dict[Event, list[int]] = {}
        # on ne conserve que les events ayant un support supérieur ou égal au support minimal
        for event, positions in mapEventToLocations.items():
            if len(positions) >= self.getMinSup() or len(self.kEpisodes) < PTKE.K:
                evtWithSuffisantSupport[event] = positions
                # Ajout de cet event en tant qu'épisode
                episode:Episode = Episode(event, [])
                for pos in positions:
                    episode.add((pos, pos))
                self.saveEpisode(episode)
                
        halfSize:int = int(len(event_list)/2)
        needExploration:bool = True
        while needExploration:
            newEpisodes:list[Episode] = []
            for kEpisode in self.kEpisodes:
                if not kEpisode.explored:
                    disqualifiedEvents:list[Event] = []
                    for event, positions in evtWithSuffisantSupport.items():
                        if len(positions) >= self.getMinSup():
                            newEpisode:Episode = self.extendEpisodeWithEvent(kEpisode, event, positions, halfSize)
                            if newEpisode.getSupport() > self.getMinSup():
                                newEpisodes.append(newEpisode)
                        else:
                            # le support de cet event n'est plus assez fort, on le supprimera
                            disqualifiedEvents.append(event)
                    # Suppression de tous les évènements disqualifiés
                    for e in disqualifiedEvents:
                        del evtWithSuffisantSupport[e]
                    kEpisode.explored = True
            # ajouter les nouveaux épisodes aux top-k
            for newE in newEpisodes:
                self.saveEpisode(newE)
            needExploration = len(newEpisodes) > 0
         
        # Ici les bounds des kEpisodes peuvent se chevaucher ([... <3,5> <4,6> ...] => dans cet exemple le premier bound fini à 5 alors que le suivant commence à 4). Pour la suite de l'algo on ne peut avoir de chevauchements entre les bounds. On va donc créer autant d'éposides que nécessaire pour désenlacer les bounds de chacun des kEpisodes
        maxSup:int = 0
        nonOverlappedEpisodes:list[NonOverlappedEpisode] = []
        for episode in self.kEpisodes:
            # 1 - On désenlace la boundlist
            scenarios:list[list[tuple[int, int]]] = []
            # on parcours tous les bounds suivants
            for bound in episode.boundlist:
                # placer ce bound dans les scenarios
                placed:bool = False
                # tenter de placer ce bound à la fin des scénarios
                for scenario in scenarios:
                    if scenario[-1][1] < bound[0]:
                        scenario.append(bound)
                        placed = True
                # Si le bound n'a pas pu être placé tenter de lui trouver une place au coeur d'un des scénarios
                if not placed:
                    newScenarios:list[list[tuple[int, int]]] = []
                    for scenario in scenarios:
                        # Remonter ce scénario jusqu'à trouver un emplacement valide
                        i:int = len(scenario)-1
                        while i >= 0 and scenario[i][1] >= bound[0]:
                            i -= 1
                        # Si on a trouvé une place au coeur du scénario, on dupplique son début et on l'ajoute à la suite
                        if i >= 0:
                            copiedScenario:list[tuple[int, int]] = scenario[0:i+1]
                            copiedScenario.append(bound)
                            newScenarios.append(copiedScenario)
                            placed = True
                    # on ajoute tout ces nouveaux scéanrios dans la liste des scénarios
                    scenarios = scenarios + newScenarios
                # Si le bound n'a pas été placé dans un scénario existant, on crée un nouveau scénario commençant par ce bound
                if not placed:
                    scenarios.append([bound])
            # 2 - Créer autant d'épisode désenlacé que de scénarios construits
            maxSup = max(maxSup, max(len(boundList) for boundList in scenarios))
            newEpisodes:list[Episode] = []
            for scenario in scenarios:
                newEpisode:Episode = copy.deepcopy(episode)
                # redéfinition de la bound list avec la nouvelle calculée
                newEpisode.boundlist = scenario
                nonOverlappedEpisodes.append(NonOverlappedEpisode(newEpisode))
        # Les épisodes sont maintenant désenlacés, on calcul leur score et on sélectionne les meilleurs
        bestNonOverlappedEpisodes:list[NonOverlappedEpisode] = []
        for nonOverlappedEpisode in nonOverlappedEpisodes:
            nonOverlappedEpisode.computeScore(maxSup)
            if len(bestNonOverlappedEpisodes) == 0 or nonOverlappedEpisode.score == bestNonOverlappedEpisodes[0].score:
                bestNonOverlappedEpisodes.append(nonOverlappedEpisode)
            elif nonOverlappedEpisode.score > bestNonOverlappedEpisodes[0].score:
                bestNonOverlappedEpisodes = [nonOverlappedEpisode]

        return bestNonOverlappedEpisodes

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
    def saveEpisode(self, episode: Episode) -> None:
        # insertion de l'épisode dans les meilleurs k episode et maintient de la liste triée par le score
        insort(self.kEpisodes, episode)
        self.kEpisodes = self.kEpisodes[-PTKE.K:] # ne conserver que les K meilleurs

    # Etend un episode donné avec un event
    #
    # :param episode: episode à étendre
    # :param event: évènement à tenter d'intégrer à l'épisode
    # :param eventPos: la position de event dans la séquence
    # :param maxWindowSize: taille de la fenêtre maximale a respecter pour autoriser une extension de l'épisode
    # 
    # :return: l'episode étendu
    def extendEpisodeWithEvent(self, episode:Episode, event:Event, eventPositions:list[int], maxWindowSize:int) -> Episode:
        # Calcul de la fenêtre maximale autorisée => ALPHA * la longueur cumulée du kième épisodes + 1 (le nouvel evènement) => pour accepter d'éventuelles traces intercalées
        max_window_size = min((episode.event.getLength()+1)*PTKE.QCSP_ALPHA, maxWindowSize)
        # Calcul des bounds contenant la fusion des bounds de l'épisode avec les positions d'un évènement
        newBoundlist:list[tuple[int, int]] = []
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
        newEpisode:Episode = copy.deepcopy(episode)
        # ajout le l'évènement ajouté
        if isinstance(newEpisode.event, Call):
            # transformation du Call en une séquence le contenant
            seq:Sequence = Sequence()
            seq.event_list.append(newEpisode.event)
            # ajout de l'évènement intégré aux bounds
            seq.event_list.append(event)
            newEpisode.event = seq
        elif isinstance(newEpisode.event, Sequence):
            newEpisode.event.event_list.append(event)
        # redéfinition de la bound list avec la nouvelle calculée
        newEpisode.boundlist = newBoundlist

        return newEpisode
            
