import copy
from multiprocessing import Pool
#import time
from Episode import BoundGraph, BoundList, Episode, NonOverlappedEpisode, Scorable
from Event import Event, Sequence
from bisect import insort

# Enregistre un item dans l'ensemble des top-k.
# 
# :param item: the item to be saved
# :param topk: the list containing the topk items
def saveInTopK(item: Scorable, topk:list[Scorable]) -> None:
    """
    Save an item in the top-k set while maintaining the sorted order.
    
    Args:
        item (Scorable): The item to be saved
        topk (list[Scorable]): The list containing the top-k items
        
    Note:
        The list is maintained sorted by score in descending order.
        If the list exceeds K items after insertion, the lowest scoring item is removed.
    """
    if item not in topk:
        # insertion de l'épisode dans les meilleurs k episodes et maintient de la liste triée par le score (du meilleur en premier au moins bon en dernier)
        if len(topk) < PTKE.K or item.getScore() > topk[-1].getScore():
            insort(topk, item)
        if len(topk) > PTKE.K:
            topk.pop() # ne conserver que les K meilleurs

            

# Désenlace un épisode et retourne les K meilleurs candidats
def unoverlapEpisode(params:tuple[Episode, int, float, float]) -> list[NonOverlappedEpisode]:
    """
    Unravel an episode into non-overlapping episodes and return the K best candidates.
    
    This function takes an episode with potentially overlapping bounds and creates
    multiple non-overlapping episodes by:
    1. Creating a tree structure of bounds
    2. Finding valid paths through the tree
    3. Converting each valid path into a non-overlapping episode
    
    Args:
        params (tuple[Episode, int, float, float]): Tuple containing:
            - Episode: The episode to unravel
            - int: Maximum support value
            - float: Proximity balancing factor
            - float: Weight support factor
            
    Returns:
        list[NonOverlappedEpisode]: List of best non-overlapping episodes
    """
    episode:Episode = params[0]
    NonOverlappedEpisode.MAX_SUP = params[1]
    NonOverlappedEpisode.PROXIMITY_BALANCING = params[2]
    NonOverlappedEpisode.WEIGHT_SUPPORT = params[3]
    #start_time:float = time.time()
    tmp:int = 0

    # création de la liste des feuilles à explorer
    topkLeafs:list[BoundGraph] = []
    # 1 - On désenlace la boundlist
    # on parcours tous les bounds
    for bound in episode.boundlist:
        # placer ce bound dans les scenarios
        # tenter de placer ce bound à la suite de chaque feuille
        newLeafs:list[BoundGraph] = []
        for leaf in topkLeafs:
            if leaf.bound[1] < bound[0]:
                newLeafs.append(BoundGraph(episode.event, bound, leaf))
        # Si le bound n'a pas pu être placé tenter de lui trouver une place au coeur d'un des scénarios
        if len(newLeafs) == 0:
            # parcourir chaque feuille
            for node in topkLeafs:
                # Remonter ce scénario dont leaf est la feuille terminale jusqu'à trouver un emplacement valide
                while node.parent != None and node.bound[1] >= bound[0]:
                    node = node.parent
                # Si on a trouvé un emplacement, on ajoute à ce noeud une nouvelle feuille si elle ne la contient pas déjà
                if node.bound[1] < bound[0] and not node.hasChild(bound):
                    newLeafs.append(BoundGraph(episode.event, bound, node))
        # Si le bound n'a pas été placé dans un scénario existant, on crée un nouveau arbre commençant par ce bound
        if len(newLeafs) == 0:
            newLeafs.append(BoundGraph(episode.event, bound))
        # Ajout des nouvelles feuilles à liste des topk
        for leaf in newLeafs:
            saveInTopK(leaf, topkLeafs) # type: ignore
        tmp += 1

    # Construire les épisodes sans recouvrement à partir des feuilles retenues
    nonOverlappedEpisodes:list[NonOverlappedEpisode] = []
    for node in topkLeafs:
        # on remonte l'arbre pour récupérer les bounds désenlacés (du dernier au premier)
        bounds:list[tuple[int, int]] = [node.bound]
        while node.parent != None:
            node = node.parent
            bounds.append(node.bound)
        # on inverse la liste des bounds et on les enregistre
        nonOverlappedEpisodes.append(NonOverlappedEpisode(copy.deepcopy(episode.event)))
        reversedBoundList = nonOverlappedEpisodes[-1].boundlist
        for bound in reversed(bounds):
            reversedBoundList.append(bound)

    #print (str(time.time()-start_time))
    return nonOverlappedEpisodes

# PTKE => Proximity Top-K Frequent Episodes
class PTKE:
    """
    Proximity Top-K Frequent Episodes (PTKE) algorithm implementation.
    
    This class implements the PTKE algorithm which finds the K most frequent episodes
    in a sequence while considering proximity between events. Episodes are built
    incrementally and scored based on support and proximity metrics.
    
    Class Attributes:
        K (int): Number of top episodes to maintain
        GAP_RATIO (float): Controls allowed gap size between episodes relative to episode length
        
    Attributes:
        kEpisodes (list[NonOverlappedEpisode]): Current top-K episodes
        minScore (float): Minimum score among top-K episodes
    """
    K:int
    # GAP_RATIO controls the size of gaps between episodes in relation to the length of the episode. GAP_RATIO is a multiplier used by to jump events proportionaly to episode size (will produce optional events). 0 means episodes will be merge if no gap exists between them.
    GAP_RATIO:float

    def __init__(self) -> None:
        """
        Initialize a new PTKE instance with empty episode list and minimum score.
        """
        self.kEpisodes:list[NonOverlappedEpisode] = []
        self.minScore:float = 0

    # Calcule les meilleurs épisodes sans chevauchement des bounds à partir d'une liste d'évènements
    #
    # :param event_list: Liste des évènements desquels extraire les meilleurs épisodes
    # :return: La liste des épisodes sans chevauchement des bounds ayant le meilleur score
    def getBestEpisodes(self, event_list: list[Event]) -> list[NonOverlappedEpisode]:
        """
        Find the best non-overlapping episodes from a list of events.
        
        This method implements the main PTKE algorithm:
        1. Maps events to their locations
        2. Creates initial single-event episodes
        3. Iteratively extends episodes with new events
        4. Unravels overlapping episodes into non-overlapping ones
        5. Maintains the K best episodes based on score
        
        Args:
            event_list (list[Event]): List of events to analyze
            
        Returns:
            list[NonOverlappedEpisode]: List of best non-overlapping episodes
        """
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
            saveInTopK(noe, self.kEpisodes) # type: ignore
                
        needExploration:bool = True
#        statLoop:float = time.time()
        while needExploration:
            newEpisodes:list[Episode] = []
            lengthSum:int = 0
            # Etendre chacun des meilleurs épisodes avec un évènement supplémentaire
            for kEpisode in self.kEpisodes:
                if not kEpisode.explored:
                    for event, positions in mapEventToLocations.items():
                        newEpisode:Episode = self.extendEpisodeWithEvent(kEpisode, event, positions)
                        if len(newEpisode.boundlist) > 0:
                            lengthSum += len(newEpisode.boundlist)
                            newEpisodes.append(newEpisode)
                    kEpisode.explored = True

            # Ici les bounds des kEpisodes peuvent se chevaucher ([... <3,5> <4,6> ...] => dans cet exemple le premier bound fini à 5 alors que le suivant commence à 4). Pour la suite de l'algo on ne peut avoir de chevauchements entre les bounds. On va donc créer autant d'éposides que nécessaire pour désenlacer les bounds de chacun des kEpisodes
            
            # Si la longueur moyenne des bounds à désenlacer pour ces nouveaux épisodes est supérieur à un seuil, les traiter en parallèle
            if len(newEpisodes) > 0 and lengthSum/len(newEpisodes) > 100:
                print ("MT")
                # Désenlacement des épisodes en parallèle
                # Création d'un pool avec X processus
                results:list[list[NonOverlappedEpisode]]
                with Pool(processes=5) as pool:
                    results = pool.map(unoverlapEpisode, [(newEpi, NonOverlappedEpisode.MAX_SUP, NonOverlappedEpisode.PROXIMITY_BALANCING, NonOverlappedEpisode.WEIGHT_SUPPORT) for newEpi in newEpisodes])
                # ajouter les nouveaux épisodes aux top-k
                for result in results:
                    for noe in result:
                        saveInTopK(noe, self.kEpisodes) # type: ignore
            else:
                # Désenlacement des épisodes en série
                for newE in newEpisodes:
                    noes:list[NonOverlappedEpisode] = unoverlapEpisode((newE, NonOverlappedEpisode.MAX_SUP, NonOverlappedEpisode.PROXIMITY_BALANCING, NonOverlappedEpisode.WEIGHT_SUPPORT))
                    # ajouter les nouveaux épisodes aux top-k
                    for noe in noes:
                        saveInTopK(noe, self.kEpisodes) # type: ignore
            
            needExploration = len(newEpisodes) > 0
        # Les épisodes sont maintenant désenlacés, on sélectionne tous les épisodes avec un score égal au meilleur
        bestNonOverlappedEpisodes:list[NonOverlappedEpisode] = []
        for nonOverlappedEpisode in self.kEpisodes:
            if len(bestNonOverlappedEpisodes) == 0 or nonOverlappedEpisode.getScore() == bestNonOverlappedEpisodes[0].getScore():
                bestNonOverlappedEpisodes.append(nonOverlappedEpisode)
            else:
                break
        
        # Ramener les épisodes qui ont une forme [[...]] à [...]
        for epi in bestNonOverlappedEpisodes:
            # Si l'épisode est une séquence (normalement c'est forcément le cas) et qu'il ne contient qu'un seul enfant
            if isinstance(epi.event, Sequence) and epi.event.getLength() == 1:
                seq:Sequence = epi.event
                # Si son unique enfant est lui même une séquence, on est dans le cas à simplifier
                if isinstance(seq.event_list[0], Sequence):
                    seqChild:Sequence = seq.event_list[0]
                    epi.event = seqChild

#        print (time.time()-statLoop)
#        for epi in bestNonOverlappedEpisodes:
#            print (epi.event)

        return bestNonOverlappedEpisodes

    # Obtention du support minimal
    def getMinSup(self) -> int:
        """
        Get the minimum support threshold for episodes.
        
        Returns:
            int: 0 if fewer than K episodes exist, otherwise the support of the
                lowest scoring episode in the top-K list
        """
        # Tantqu'on n'a pas encore identifié K épisodes, considérer le support minimal à 0 pour autoriser de nouvelles explorations
        if len(self.kEpisodes) < PTKE.K:
            return 0
        else:
            return self.kEpisodes[-1].getSupport()



    # Etend un episode donné avec un event
    #
    # :param episode: episode à étendre
    # :param event: évènement à tenter d'intégrer à l'épisode
    # :param eventPositions: liste des positions de event dans la séquence
    # 
    # :return: l'episode étendu
    def extendEpisodeWithEvent(self, episode:Episode, event:Event, eventPositions:list[int]) -> Episode:
        """
        Extend an episode by adding a new event.
        
        This method attempts to extend an existing episode with a new event by:
        1. Calculating the maximum allowed window size based on GAP_RATIO
        2. Finding valid combinations of existing bounds with new event positions
        3. Creating a new episode with the extended event sequence
        
        Args:
            episode (Episode): Episode to extend
            event (Event): Event to add
            eventPositions (list[int]): Positions where the event occurs
            
        Returns:
            Episode: New episode containing the original episode extended with the event
            
        Raises:
            TypeError: If the episode's event is not a Sequence
        """
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
            
