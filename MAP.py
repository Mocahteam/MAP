import copy
import time
from Episode import NonOverlappedEpisode
from Event import Event, LinearEventWithStats, Root, Sequence, LinearEvent, mergeLinearSequences
from PTKE import PTKE


# init constant values
PTKE.K = 10
TIME_LIMIT:int = 5

class CompressionStats:
    """
    Statistics about a compression operation.
    
    This class stores information about a compression operation including the
    compression string, score, and various counters for operations performed.
    
    Attributes:
        compression (Sequence): The compressed representation
        countOpt (int): Count of optional elements
        countAlign (int): Count of alignment operations
        countMerge (int): Count of merge operations
    """
    def __init__(self, compression:Sequence, countOpt:int, countAlign:int, countMerge:int) -> None:
        """
        Initialize a new CompressionStats instance.
        
        Args:
            compression (Sequence): The compressed representation
            countOpt (int): Count of optional elements
            countAlign (int): Count of alignment operations
            countMerge (int): Count of merge operations
        """
        self.compression:Sequence = compression
        self.countOpt:int = countOpt
        self.countAlign:int = countAlign
        self.countMerge:int = countMerge
    
    def __eq__(self, other:object) -> bool:
        """
        Check if two CompressionStats are equal.
        
        Args:
            other (object): The object to compare with
            
        Returns:
            bool: True if the compressions and counters are equal
        """
        return isinstance(other, CompressionStats) and self.compression == other.compression and self.countOpt == other.countOpt and self.countAlign == other.countAlign and self.countMerge == other.countMerge
    
    def __hash__(self) -> int:
        """
        Generate a hash value for the CompressionStats.
        
        Returns:
            int: Hash value based on compression and counters
        """
        return hash((self.compression, self.countOpt, self.countAlign, self.countMerge))
    
    def __str__(self) -> str:
        """
        Get a string representation of the CompressionStats.
        
        Returns:
            str: Space-separated string of compression and counters
        """
        return str(self.compression)+" "+str(self.countOpt)+" "+str(self.countAlign)+" "+str(self.countMerge)
    
    def to_dict(self) -> dict[str, str]:
        """
        Convert the CompressionStats to a dictionary.
        
        Returns:
            dict[str, str]: Dictionary containing all stats as string values
        """
        return {
            "Compression": str(self.compression),
            "OptCount": str(self.countOpt),
            "AlignCount": str(self.countAlign),
            "MergeCount": str(self.countMerge)
        }


class CompressionSet:
    """
    A set of compression statistics.
    
    This class maintains a collection of CompressionStats objects and provides
    methods to compare and manipulate compression sets. Two CompressionSets are
    considered equal if they share at least one compression or if both are empty.
    """
    def __init__(self) -> None:
        """
        Initialize a new empty CompressionSet.
        """
        self.set:set[CompressionStats] = set()
		
    # On considère que des CompressionSet sont égaux s'ils contiennent au moins une compression identique ou que les deux sont vides
    def __eq__(self, other:object) -> bool:
        """
        Check if two CompressionSets are equal.
        
        Two sets are equal if they share at least one compression or if both are empty.
        
        Args:
            other (object): The object to compare with
            
        Returns:
            bool: True if the sets are equal according to the rules
        """
        if not isinstance(other, CompressionSet):
            return NotImplemented
        return (not self.__ne__(other)) or (len(self.set) == 0 and len(other.set) == 0)
	
    def __ne__(self, other:object) -> bool:
        """
        Check if two CompressionSets are not equal.
        
        Args:
            other (object): The object to compare with
            
        Returns:
            bool: True if the sets have no compressions in common
        """
        if not isinstance(other, CompressionSet):
            return NotImplemented
        return self.set.isdisjoint(other.set)
	
    def __hash__(self) -> int:
        """
        Generate a hash value for the CompressionSet.
        
        Returns:
            int: Hash value based on the frozen set of compressions
        """
        return hash(frozenset(self.set))
	
    def __repr__(self) -> str:
        """
        Get a string representation of the CompressionSet.
        
        Returns:
            str: String representation showing the set contents
        """
        return f'CompressionSet({self.set})'
        
    def to_dict(self) ->list[CompressionStats]:
        """
        Convert the CompressionSet to a list for serialization.
        
        Returns:
            list[CompressionStats]: List containing all compression stats
        """
        return list(self.set)
     
    @classmethod
    def from_dict(cls, list_:list[CompressionStats]) -> 'CompressionSet':
        """
        Create a CompressionSet from a list of CompressionStats.
        
        Args:
            list_ (list[CompressionStats]): List of compression stats
            
        Returns:
            CompressionSet: New compression set containing the stats
        """
        # Convertir la liste en ensemble pour la désérialisation
        return cls(set=set(list_)) # type: ignore
	
	# \brief Vérifie si au moins une des "compressions" est égale à la solution "solution". Retourne 1 si au moins une des compressions est égale à la solution ou -1 si la compression n'est pas allée au bout ("OverTime") ou 2 sinon
	#
	# @solution : représente la solution de référence sous la forme d'une liste
    def getCode(self, solution:str) -> int:
        """
        Check if any compression matches the solution.
        
        Args:
            solution (str): The reference solution to compare against
            
        Returns:
            int: 1 if a match is found, -1 if overtime occurred, 2 otherwise
        """
        if any(solution == str(s.compression) for s in self.set):
            return 1
        if any(s.countOpt == 0 and s.countAlign == 0 and s.countMerge == 0 for s in self.set):
            return -1
        return 2


# Recherche dans la liste "l", l'évènement e à partir de l'indice "start" (inclus), jusqu'à l'indice "end" (exclus) avec comme pas de parcours "step"
def getIndex(l:list[Event], e:Event, start:int, end:int, step:int)-> int:
    """
    Search for an event in a list with specified direction and range.
    
    Args:
        l (list[Event]): The list to search in
        e (Event): The event to search for
        start (int): Starting index (inclusive)
        end (int): Ending index (exclusive)
        step (int): Step size and direction (positive or negative)
        
    Returns:
        int: Index of the found event or -1 if not found
        
    Raises:
        ValueError: If step is 0 or direction is inconsistent with start/end
    """
    # Vérification de la validité des paramètres
    if step == 0 or (step < 0 and start < end) or (step > 0 and start > end):
        raise ValueError("MAP.py => getIndex: Parameters not correct")
    while start != end:
        if l[start].isEquiv(e):
            return start
        start += step
    return -1

# Aggrège dans newRoot les Events fusionnés en gérant les Event intercalés entre les bounds englobant les Events fusionnés.
# newRoot: la nouvelle séquence dans laquelle le résultat de la fusion doit être inséré
# mergedLinearSequence: le contenu du root fusionné dans l'intervalle mergedBound
# mergedBound: les indices de début et de fin dans root des Event fusionnés dans mergedLinearSequence. Autrement dit mergedBound est l'union des bounds ayant été intégrés à la fusion
# intercaletedEvents: les Events du root intercalés entre les bounds fusionnés, A noter que tous les Events de intercaletedEvents doivent être tagué en optionnel
# nextBoundStart: la position du début du prochain bound dans root. Si mergedBound est la fusion de tous les bounds, nextBoundStart doit être initialisé à la longueur du root
# root: la séquence dans laquelle on a calculer le meilleur épisode
def aggregateMerge (newRoot:Root, mergedLinearSequence:LinearEventWithStats, mergedBound:tuple[int, int], intercaletedEvents:LinearEventWithStats, nextBoundStart:int, root:Root) -> None:
    """
    Aggregate merged events into a new root while handling interspersed events.
    
    This complex function handles the merging of events while properly managing
    events that occur between merged bounds. It:
    1. Handles upstream events that match interspersed events
    2. Injects interspersed events at both start and end of merged sequences
    3. Skips downstream events that are already included in interspersed events
    
    Args:
        newRoot (Root): The new sequence where merge results will be inserted
        mergedLinearSequence (LinearEventWithStats): Content of merged root in mergedBound interval
        mergedBound (tuple[int, int]): Start and end indices of merged events in root
        intercaletedEvents (LinearEventWithStats): Optional events between merged Bounds
        nextBoundStart (int): Position of next bound start in root
        root (Root): Original sequence where best episode was found
        
    Note:
        All events in intercaletedEvents must be marked as optional.
        If mergedBound is the fusion of all bounds, nextBoundStart should be root length.
    """
    newEndBound:int = mergedBound[1]
    # NOTE : Le code ci-dessous est gardé pour mémoire car s'il avait été ajouté c'était sûrement pour résoudre un cas particulier qui n'a pas été noté mais en l'état ce code pose problème pour construire des boucles imbriquées du type BCDCDCDBCDCDBCDBCDCD qui avec comme pattern CD sera réduit à B[CD]B[CD]BCDB[CD]. Le troisième paquet de CD qui n'est constitué que d'une seule occurence va être laissé sous la forme CD et non [CD], du coup à la prochaine passe le pattern [B[CD]] va poser problème
    # injection de la dernière fusion dans le root
    #if mergedLinearSequence.countMerge == 1 and not isinstance(root.content.event_list[mergedBound[0]], Sequence):
    #    # S'il n'y a eu qu'une seule fusion et qu'elle ne portait pas sur une Sequence on réinjecte les évènements directement sans les encapsuler dans une séquence de pattern donc on retire le Begin et le End du pattern
    #    newRoot.content.appendLinearSequence(mergedLinearSequence[1:-1])
    #    # test de contrôle qui théoriquement ne doit jamais arriver car si on a un seul merge on ne peut avoir des évènements intercalés d'où le fait que dans la ligne ci-dessus on ne s'est pas embêté à réinjecter les traces intercalées
    #    if len(intercaletedEvents) > 0: 
    #         print("Error, this test would not appen!!! something wrong...")
    #else:
    
    # Transformation des évènements intercalés linéarisés en séquence (non linéarisée)
    intercaletedSeq:Sequence = Sequence()
    intercaletedSeq.appendLinearSequence(intercaletedEvents.linearEvent)
    newRootContent:Sequence = newRoot.content
    # Remonter les traces en amont du mergedBound (donc la fin du newRoot) pour chercher des traces correspondant aux évènements intercalés
    # l'indice à tester en amont du bound (le dernier élément du newRoot)
    upstreamCheck:int = len(newRootContent.event_list)-1
    # On démarre par la fin des évènements intercalés
    index:int = len(intercaletedSeq.event_list)-1
    # Tant qu'on trouve dans les traces intercalées des évènements en amont, on continue à remonter la fin du newRoot
    lastValidPos:int = -1
    while upstreamCheck >= 0 and (index := getIndex(intercaletedSeq.event_list, newRootContent.event_list[upstreamCheck], index, -1, -1)) != -1:
        lastValidPos = upstreamCheck
        upstreamCheck -= 1
    # Si on a au moins trouvé un Event en amont du mergedBound (donc dans la fin du newRoot) qui est présent dans les traces intercalées, les supprimer de l'amont. On est dans le cas :
    # newRoot => ...AB]CDE
    # intercaletedEvents => F*E*G*D*
    # mergedLinearSequence => [HI]
    # On a détecté que DE de la fin du newRoot était inclus intercaleted donc on les supprime de newRoot pour obtenir ...AB]C
    if lastValidPos != -1:
        for _ in range(len(newRootContent.event_list)-lastValidPos):
            newRootContent.event_list.pop()
            
    # Maintenant qu'on a nettoyé l'amont on ajoute dans le nouveau root la fusion à laquelle on injecte les traces intercalées
    # Le choix est fait ici d'injecter les traces intercallées au début ET à la fin de la fusion car on n'a pas de moyen objectif pour savoir si elles constituent la fin d'une itération d'un pattern ou le début du suivant donc pour rester le plus générique possible, on recopie les traces intercallées au début et à la fin
    # On a nettoyé newRoot de ...AB]CDE à ...AB]C et on va l'augmenter avec les traces intercallée pour obtenir :
    # ...AB]C[F*E*G*D*HIF*E*G*D*]
    newRoot.content.appendLinearSequence([mergedLinearSequence.linearEvent[0]]+intercaletedEvents.linearEvent+mergedLinearSequence.linearEvent[1:-1]+intercaletedEvents.linearEvent+[mergedLinearSequence.linearEvent[-1]])
    
    # Pour gérer ce qui suit mergedBound on va sauter les Event du root qui serait contenus dans les traces intercallées. L'idée est que comme on a intégré FEDG à la fin de la fusion, si la suite du root contiendrait des Events des traces intercallées, il faut les sauter. Imaginons qu'à la suite de mergedBound le root contienne les traces suivantes EGJK... comme EG est inclus dans les Events intercalés (F*E*G*D*), on va les ignorer de manière à ne poursuivre dans root qu'à partir de JK...
    # Descendre les traces en aval du bound pour chercher des traces correspondant aux évènements intercalés
    # l'indice à tester en aval du bound (l'Event suivant la fin de mergedBound)
    downstreamCheck:int = mergedBound[1]+1
    # On démarre par le début des évènements intercalés
    index:int = 0
    # Tant qu'on trouve dans les traces intercalées des évènements en aval du mergedBound, on continue à avancer
    lastValidPos = -1
    while downstreamCheck < nextBoundStart and (index := getIndex(intercaletedSeq.event_list, root.content.event_list[downstreamCheck], index, len(intercaletedSeq.event_list), 1)) != -1:
        lastValidPos = downstreamCheck
        downstreamCheck += 1
    # Si on a au moins trouvé une trace en aval du mergedBound dans les traces intercalées, adapter la fin du bound pour sauter dans le root les Events trouvés
    if lastValidPos != -1:
        newEndBound = lastValidPos

    # on termine en ajoutant les évènements intercalés jusqu'au début du prochain bound
    # Au final dans notre exemple on se retrouve avec un newRoot de la forme ...AB]C[F*E*G*D*HIF*E*G*D*]JK...
    newRoot.content.event_list += root.content.event_list[newEndBound+1:nextBoundStart]
    # mise à jour des stats du nouveau root
    newRoot.countOpt += mergedLinearSequence.countOpt+intercaletedEvents.countOpt
    newRoot.countAlign += mergedLinearSequence.countAlign+intercaletedEvents.countAlign
    newRoot.countMerge += mergedLinearSequence.countMerge+intercaletedEvents.countMerge

# MAP => Mining Algorithm Patterns
def MAP (event_list:list[Event], gr:float, ws:float, pb:float) -> CompressionSet:
    """
    Mining Algorithm Patterns (MAP) implementation.
    
    This function implements the MAP algorithm which:
    1. Takes a sequence of events and tries to find recurring patterns
    2. Uses PTKE to find frequent episodes
    3. Compresses the sequence by replacing patterns with shorter representations
    4. Maintains multiple compression candidates in parallel
    
    Args:
        event_list (list[Event]): List of events to analyze
        gr (float): Gap ratio for PTKE
        ws (float): Weight support factor for scoring
        pb (float): Proximity balancing factor
        
    Returns:
        CompressionSet: Set of different possible compressions with their stats
        
    Note:
        The algorithm stops after TIME_LIMIT seconds, adding an "OverTime"
        compression stat if the limit is reached.
    """
    #gr = 8
    #ws = 0.5
    #pb = 0.5
    PTKE.GAP_RATIO = gr
    NonOverlappedEpisode.WEIGHT_SUPPORT = ws
    NonOverlappedEpisode.PROXIMITY_BALANCING = pb

    compressions:CompressionSet = CompressionSet()

    start_time:float = time.time()

    # Ajout d'un root stabilisable et association de la liste d'évènement à ce root
    roots:list[Root] = [Root(Sequence())]
    roots[0].content.isRoot = True
    roots[0].content.event_list = event_list

    originalRootLength = len(event_list)

    # tant qu'il y a au moins un root à explorer
    root_i:int = 0
    while root_i < len(roots):
        root:Root = roots[root_i]
        # Couper si ça prend trop de temps
        if time.time()-start_time > TIME_LIMIT:
            compressions.set.add(CompressionStats(Sequence(), 0, 0, 0))
            #for r in roots:
            #      print (r.content)
            break

        ptke:PTKE = PTKE()
        bestEpisodes:list[NonOverlappedEpisode] = ptke.getBestEpisodes(root.content.event_list)
        # Pour chaque épisode donné par tke, simuler la compression
        best_i:int = 0
        while best_i<len(bestEpisodes):
            bestEpisode:NonOverlappedEpisode = bestEpisodes[best_i]
            # On ne traite cet épisode que si son support est strictement supérieur à 1
            if bestEpisode.getSupport() > 1:
                newRoot:Root = Root(Sequence())
                newRoot.content.isRoot = True
                # Transformation de cet épisode en une séquence linéarisée
                bestPattern:list[LinearEvent] = bestEpisode.event.linearize()

                #print (str(bestEpisode)+f" => {bestEpisode.score:.2f} (part1:{bestEpisode.part1:.2f}; part2:{bestEpisode.part2:.2f}) (inside:{bestEpisode.inside:.2f}; outside:{bestEpisode.outside:.2f})")

                # On commence la compression avec le premier bound
                mergedBound:tuple[int, int] = bestEpisode.boundlist[0]
                # On injecte dans le nouveau root les traces précédant le premier bound
                if mergedBound[0] > 0:
                    newRoot.content.event_list = root.content.event_list[:mergedBound[0]]
                # On fusionne le premier bound avec le meilleur pattern
                mergedLinearSequence:LinearEventWithStats = mergeLinearSequences(root.content.getSubSequence(mergedBound[0], mergedBound[1]+1).linearize(), bestPattern)
                mergedLinearSequence.countOpt += root.countOpt
                mergedLinearSequence.countAlign += root.countAlign

                # Une sequence linéarisée pour stocker les traces intercallées entre le bounds
                intercaletedEvents:LinearEventWithStats = LinearEventWithStats()
                # Parcourir tous les bounds
                for k in range(1, len(bestEpisode.boundlist)):
                    currentBound:tuple[int, int] = bestEpisode.boundlist[k]
                    # vérifier si l'écart entre la fin du précédent et la fin de ce bound est inférieur au seuil
                    #if currentBound[1] - mergedBound[1] <= (currentBound[1]-currentBound[0] + 1)*(1 + PTKE.GAP_RATIO):
                    if currentBound[1] - mergedBound[1] <= (currentBound[1]-currentBound[0] + 1)*(1 + PTKE.GAP_RATIO)*NonOverlappedEpisode.PROXIMITY_BALANCING:
                        # extraction de la séquence linéarisée entre les deux bounds (on inclus toutes les traces intercallées entre la fin des épisodes précédement fusionnés et le debut du bound courrant)
                        if mergedBound[1]+1 < currentBound[0]:
                            # On crée une séquence temporaire
                            subSequence:Sequence = Sequence()
                            # On clone le contenu intercallé
                            subSequence.event_list = copy.deepcopy(root.content.event_list[mergedBound[1]+1:currentBound[0]])
                            # Appel récursif de MAP pour compresser les traces intercalées
                            result:CompressionSet = MAP(subSequence.event_list, gr, ws, pb)
                            linearSequenceInsertedEvents:list[LinearEvent]
                            if len(result.set) > 0 :
                                # transformation de la première compression trouvée en une séquence linéarisée et on fait sauter le Begin et le End
                                linearSequenceInsertedEvents = result.set.pop().compression.linearize()[1:-1]
                            else:
                                # Si pas de compression générée, on linéarise simplement la séquence entercalée et on fait sauter le Begin et le End
                                linearSequenceInsertedEvents = subSequence.linearize()[1:-1]
                            # On merge cette partie avec les évènements intercalés, à noter que lors des premiers Event intercallés on va chercher à fusionner [] avec une liste d'Events non vide, ils seront donc tous mis en optionnel et c'est justement ce que l'on cherche.
                            result1:LinearEventWithStats = mergeLinearSequences(linearSequenceInsertedEvents, intercaletedEvents.linearEvent)
                            # Prise en compte du résultat et comptabilisation des stats d'option et d'alignement
                            intercaletedEvents.update(result1.linearEvent, result1.countOpt, result1.countAlign)

                        # linearisation du bound courrant
                        linearSequenceCurrentBound:list[LinearEvent] = root.content.getSubSequence(currentBound[0], currentBound[1]+1).linearize()
                        # calcule la fusion entre le dernier état de fusion et cette nouvelle séquence linéarisée
                        result2:LinearEventWithStats = mergeLinearSequences(linearSequenceCurrentBound, mergedLinearSequence.linearEvent)
                        mergedLinearSequence.update(result2.linearEvent, result2.countOpt, result2.countAlign)

                        # on étend la plage de la fusion pour englober ce nouvel épisode
                        mergedBound = (mergedBound[0], currentBound[1])
                    else:
                        # l'écart entre la fusion précédente et le bound courant est trop importante donc on injecte la fusion précédente dans le newRoot
                        aggregateMerge(newRoot, mergedLinearSequence, mergedBound, intercaletedEvents, currentBound[0], root)

                        # on réinitialise la fusion à la fusion du bound courant et du pattern fournit par TKE
                        mergedLinearSequence = mergeLinearSequences(root.content.getSubSequence(currentBound[0], currentBound[1]+1).linearize(), bestPattern)

                        # on réinitialise les traces intercallées
                        intercaletedEvents = LinearEventWithStats()
                        # Et on repositionne le bound de fusion sur le bound courrant
                        mergedBound = currentBound
                
                aggregateMerge(newRoot, mergedLinearSequence, mergedBound, intercaletedEvents, len(root.content.event_list), root)

                # on ne stocke le nouveau root que s'il n'est pas plus long d'un quart de la longueur initiale (le -2 est pour ne pas compter le premier Begin et le dernier End de la linéarisation) et qu'il contient moins de Call que le root original et qu'on ne l'a pas déjà exploré
                if len(newRoot.content.linearize())-2 <= originalRootLength*1.25 and newRoot.content.countCalls() <= originalRootLength and not any(newRoot == r for r in roots):
                    roots.append(newRoot)
                
            best_i += 1
        root_i += 1

    #print ("Analyse terminée, temps de calcul : "+str(time.time()-start_time))
    #print("Meilleure compression trouvée :")
    #print(str(root))
    #print("Fin")
    # Enregistrement des compressions
    for modelRoot in roots[1:]: # On saute le premier root (le root original)
        compressions.set.add(CompressionStats(modelRoot.content, modelRoot.countOpt, modelRoot.countAlign, modelRoot.countMerge))
    return compressions