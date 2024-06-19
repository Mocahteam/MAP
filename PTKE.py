import copy
import sys
from Episode import Episode
from Event import Call, Event, Sequence
from bisect import insort

# PTKE => Proximity Top-K Frequent Episodes
class PTKE:
    K:int
    QCSP_ALPHA:int

    def __init__(self) -> None:
        self.kEpisodes:list[Episode] = []
        self.minScore:float = 0

    def getBestEpisode(self, event_list: list[Event]) -> Episode:
        Episode.MIN_SUPPORT = 1
        Episode.MAX_SUPPORT = 1
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
            if len(positions) >= Episode.MIN_SUPPORT or len(self.kEpisodes) < PTKE.K:
                evtWithSuffisantSupport[event] = positions
                # Ajout de cet event en tant qu'épisode
                episode:Episode = Episode(event, [])
                for pos in positions:
                    episode.add((pos, pos))
                self.saveEpisode(episode)
                
        halfSize:int = int(len(event_list)/2)
        while self.needEpisodeExploration():
            newEpisodes:list[Episode] = []
            for kEpisode in self.kEpisodes:
                if not kEpisode.explored:
                    disqualifiedEvents:list[Event] = []
                    for event, positions in evtWithSuffisantSupport.items():
                        if len(positions) >= Episode.MIN_SUPPORT:
                            simulatedEpisodes:list[Episode] = self.tryToExtendEpisodeWithEvent(kEpisode, event, positions, halfSize)
                            for episode in simulatedEpisodes:
                                if episode.getSupport() > 0 and episode.getScore() > self.minScore:
                                    newEpisodes.append(episode)
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

        for kepi in self.kEpisodes:
            print (str(kepi)+f" => {kepi.getScore():.2f} (part1:{kepi.part1:.2f}; part2:{kepi.part2:.2f}) (inside:{kepi.inside:.2f}; outside:{kepi.outside:.2f})")
        # Le meilleur pattern est le dernier des kEpisodes
        return self.kEpisodes[-1]

    # Vérifie s'il reste au moins un épisode dans les k meilleurs épisodes identifiés à explorer
    def needEpisodeExploration(self) -> bool:
        for episode in self.kEpisodes:
            if not episode.explored:
                return True
        return False

	# Enregistre un épisode dans l'ensemble de top-k pattern.
	# 
	# :param episode: the episode to be saved
    def saveEpisode(self, episode: Episode) -> None:
        # insertion de l'épisode dans les meilleurs k episode et maintient de la liste triée par le score
        insort(self.kEpisodes, episode)
        self.kEpisodes = self.kEpisodes[-PTKE.K:] # ne conserver que les K meilleurs
        # we update MIN_SUPPORT and MAX_SUPPORT
        Episode.MIN_SUPPORT = sys.maxsize
        Episode.MAX_SUPPORT = 1
        for episode in self.kEpisodes:
            currentSupport:int = episode.getSupport()
            if currentSupport > Episode.MAX_SUPPORT:
                Episode.MAX_SUPPORT = currentSupport
            if currentSupport < Episode.MIN_SUPPORT:
                Episode.MIN_SUPPORT = currentSupport
        self.minScore = self.kEpisodes[0].getScore()

    # Simule un nouvel episode en étendant un episode donné avec un event
    #
    # :param episode: episode à étendre
    # :param event: évènement à tenter d'intégrer à l'épisode
    # :param eventPos: la position de event dans la séquence
    # :param maxWindowSize: taille de la fenêtre maximale a respecter pour autoriser une extension de l'épisode
    # 
    # :return: l'episode étendu
    def tryToExtendEpisodeWithEvent(self, episode:Episode, event:Event, eventPositions:list[int], maxWindowSize:int) -> list[Episode]:
        # Calcul de la fenêtre maximale autorisée => ALPHA * la longueur cumulée du kième épisodes + 1 (le nouvel evènement) => pour accepter d'éventuelles traces intercalées
        max_window_size = min((episode.event.getLength()+1)*PTKE.QCSP_ALPHA, maxWindowSize)
        # Calcul des bounds contenant la fusion des bounds de l'épisode avec les positions d'un évènement
        newBoundlist:list[tuple[int, int]] = []
        i:int = 0
        j:int = 0

        while i < len(episode.boundlist) and j < len(eventPositions):
            # ------------- Tentative de suppression de ce cas, sinon on élimine certains bounds possibles de manière arbitraire, il vaut mieux tous les garder et voir ensuite ceux qu'on élimine ---------------------------
            # éviter la superposition de bounds => sinon le support augmente mais ne reflète pas bien la future compression possible car un event ne peut être inclus que dans un et un seul bound
            # episode : [... <?,4> ...] => on fait avancer l'épisode pour tenter de trouver un bound après le dernier bound de la nouvelle bound list
            # new     : [... <6,?>]
            #if(len(newBoundlist)>0 and episode.boundlist[i][0] <= newBoundlist[-1][1]):
            #    i += 1

            # avancer sur la position de l'event tant qu'elle commence avant la position de fin du bound courant de l'épisode => ça ne sert à rien d'explorer une position de l'event qui commence avant la fin du bound courant de l'épisode
            # episode : [... <?,6> ...]
            # event   : [... <3,3> ...] => on fait avancer l'event pour tenter de trouver une position commence après le 6
            if episode.boundlist[i][1] >= eventPositions[j]:
                j += 1
            # avancer sur le bound suivant de l'épisode tant que la distance entre le début de ce bound et la position de l'event est supérieur ou égal à la taille de la fenêtre maximale autorisée
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
        # Ici les bounds peuvent se chevaucher ([... <3,5> <4,6> ...] => dans cet exemple le premier bound fini à 5 alors que le suivant commence à 4). On va donc créer autant d'éposides que nécessaire pour désenlacer les bounds
        # 1 - On commence par générer le nouveau modèle d'épisode
	    # clonage du contenu de l'épisode
        pattern:Episode = copy.deepcopy(episode)
        pattern.durty = True # Forcer à recalculer son score si besoin
        # ajout le l'évènement ajouté
        if isinstance(pattern.event, Call):
            # transformation du Call en une séquence le contenant
            seq:Sequence = Sequence()
            seq.event_list.append(pattern.event)
            # ajout de l'évènement intégré aux bounds
            seq.event_list.append(event)
            pattern.event = seq
        elif isinstance(pattern.event, Sequence):
            pattern.event.event_list.append(event)
        # 2 - On désenlace la boundlist
        # on initialise la liste des scénarios avec un premier scénarion contenant simplement le premier bound
        scenarios:list[list[tuple[int, int]]] = []
        # on parcours tous les bounds suivants
        for bound in newBoundlist:
            # placer ce bound dans les scenarios
            placed:bool = False
            # tenter de placer ce bound à la fin d'un scénario existant
            for scenario in scenarios:
                if scenario[-1][1] < bound[0]:
                    scenario.append(bound)
                    placed = True
            # Si le bound n'a pas pu être placé tenter de lui trouver une place au coeur d'un des scénarioq
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
        # 3 - Créer autant d'épisode que de scénarios construits
        newEpisodes:list[Episode] = []
        for scenario in scenarios:
            newEpisode:Episode = copy.deepcopy(pattern)
            # redéfinition de la bound list avec la nouvelle calculée
            newEpisode.boundlist = scenario
            newEpisodes.append(newEpisode)
            
        return newEpisodes
            
