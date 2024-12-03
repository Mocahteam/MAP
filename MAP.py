import copy
import time
from Episode import NonOverlappedEpisode
from Event import Event, Sequence, LinearEvent, mergeLinearSequences
from PTKE import PTKE


# init constant values
PTKE.K = 10
TIME_LIMIT:int = 5

class Root:
    def __init__(self, root:Sequence) -> None:
        self.content = root

    def __eq__(self, other:object) -> bool:
          return isinstance(other, Root) and self.content == other.content


class CompressionSet:
	def __init__(self, ) -> None:
		self.set:set[str] = set()
		
    # On considère que des CompressionSet sont égaux s'ils contiennent au moins une compression identique ou que les deux sont vides
	def __eq__(self, other:object) -> bool:
		if not isinstance(other, CompressionSet):
			return NotImplemented
		return (not self.__ne__(other)) or (len(self.set) == 0 and len(other.set) == 0)
	
	def __ne__(self, other:object) -> bool:
		if not isinstance(other, CompressionSet):
			return NotImplemented
		return self.set.isdisjoint(other.set)
	
	def __hash__(self) -> int:
		return hash(frozenset(self.set))
	
	def __repr__(self) -> str:
		return f'CompressionSet({self.set})'
	
	# \brief Vérifie si au moins une des "compressions" est égale à la solution "solution". Retourne 1 si au moins une des compressions est égale à la solution ou -1 si la compression n'est pas allée au bout (contient "OverTime") ou 2 sinon
	#
	# @solution : représente la solution de référence sous la forme d'une liste
	def getCode(self, solution:str) -> int:
		if solution in self.set:
			return 1
		if "OverTime" in self.set:
			return -1
		return 2

# Recherche dans la liste "l", l'évènement e à partir de l'indice "start" (inclus), jusqu'à l'indice "end" (exclus) avec comme pas de parcours "step"
def getIndex(l:list[Event], e:Event, start:int, end:int, step:int)-> int:
    # Vérification de la validité des paramètres
    if step == 0 or (step < 0 and start < end) or (step > 0 and start > end):
        raise ValueError("MAP.py => getIndex: Parameters not correct")
    while start != end:
        if l[start].isEquiv(e):
            return start
        start += step
    return -1

# Ajoute au root la fusion et détermine si elle doit rester encapsulée dans une séquence ou pas
def mergeUsingPatternOrNot (mergeCount:int, root:Root, mergedBound:tuple[int, int], nextBoundStart:int, newRoot:Root, mergedLinearSequence:list[LinearEvent], intercaletedEvents:list[LinearEvent]) -> None:
    newEndBound:int = mergedBound[1]
    # NOTE : Le code ci-dessous est gardé pour mémoire car s'il avait été ajouté c'était sûrement pour résoudre un cas particulier qui n'a pas été noté mais en l'état ce code pose problème pour construire des boucles imbriquées du type BCDCDCDBCDCDBCDBCDCD qui avec comme pattern CD sera réduit à B[CD]B[CD]BCDB[CD]. Le troisième paquet de CD qui n'est constitué que d'une seule occurence va être laissé sous la forme CD et non [CD], du coup à la prochaine passe le pattern [B[CD]] va poser problème
    # injection de la dernière fusion dans le root
    #if mergeCount == 1 and not isinstance(root.content.event_list[mergedBound[0]], Sequence):
    #    # S'il n'y a eu qu'une seule fusion et qu'elle ne portait pas sur une Sequence on réinjecte les évènements directement sans les encapsuler dans une séquence de pattern donc on retire le Begin et le End du pattern
    #    newRoot.content.appendLinearSequence(mergedLinearSequence[1:-1])
    #    # test de contrôle qui théoriquement ne doit jamais arriver car si on a un seul merge on ne peut avoir des évènements intercalés d'où le fait que dans la ligne ci-dessus on ne s'est pas embêté à réinjecter les traces intercalées
    #    if len(intercaletedEvents) > 0: 
    #         print("Error, this test would not appen!!! something wrong...")
    #else:

    # Transformation des évènements intercalés linéarisés en séquence
    intercaletedSeq:Sequence = Sequence()
    intercaletedSeq.appendLinearSequence(intercaletedEvents)
    newRootContent:Sequence = newRoot.content
    # Remonter les traces en amont du bound pour chercher des traces correspondant aux évènements intercalés
    # l'indice à tester en amont du bound (le dernier élément du newRoot)
    upstreamCheck:int = len(newRootContent.event_list)-1
    # On démarre par la fin des évènements intercalés
    index:int = len(intercaletedSeq.event_list)-1
    # Tant qu'on trouve dans les traces intercalées des évènements en amont, on continue
    lastValidPos:int = -1
    while upstreamCheck >= 0 and (index := getIndex(intercaletedSeq.event_list, newRootContent.event_list[upstreamCheck], index, -1, -1)) != -1:
        lastValidPos = upstreamCheck
        upstreamCheck -= 1
    # Si on a au moins trouvé une trace en amont dans les traces intercalées, les supprimer de l'amont
    if lastValidPos != -1:
        for _ in range(len(newRootContent.event_list)-lastValidPos):
            newRootContent.event_list.pop()
            
    # Maintenant qu'on a nettoyé l'amont on ajoute dans le nouveau root la fusion à laquelle on injecte les traces intercalées
    # Le choix est fait ici d'injecter les traces intercallées au début ET à la fin de la fusion car on n'a pas de moyen objectif pour savoir si elles constituent la fin d'une itération d'un pattern ou le début du suivant donc pour rester le plus générique possible, on recopie les traces intercallées au début et à la fin
    newRoot.content.appendLinearSequence([mergedLinearSequence[0]]+intercaletedEvents+mergedLinearSequence[1:-1]+intercaletedEvents+[mergedLinearSequence[-1]])
            
    # Descendre les traces en aval du bound pour chercher des traces correspondant aux évènements intercalés
    # l'indice à tester en aval du bound
    downstreamCheck:int = mergedBound[1]+1
    # On démarre par le début des évènements intercalés
    index:int = 0
    # Tant qu'on trouve dans les traces intercalées des évènements en aval, on continue
    lastValidPos = -1
    while downstreamCheck < nextBoundStart and (index := getIndex(intercaletedSeq.event_list, root.content.event_list[downstreamCheck], index, len(intercaletedSeq.event_list), 1)) != -1:
        lastValidPos = downstreamCheck
        downstreamCheck += 1
    # Si on a au moins trouvé une trace en aval dans les traces intercalées, adapter la fin du bound
    if lastValidPos != -1:
        newEndBound = lastValidPos

    # on termine en ajoutant les évènements intercalés jusqu'au début du prochain bound
    newRoot.content.event_list += root.content.event_list[newEndBound+1:nextBoundStart]

# MAP => Mining Algorithm Patterns
def MAP (event_list:list[Event], gr:float, ws:float, pb:float) -> CompressionSet:
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
            compressions.set.add("OverTime")
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
                mergedLinearSequence:list[LinearEvent] = mergeLinearSequences(root.content.getSubSequence(mergedBound[0], mergedBound[1]+1).linearize(), bestPattern)

                # Une sequence linéarisée pour stocker les traces intercallées entre le bounds
                intercaletedEvents:list[LinearEvent] = []
                mergeCount:int = 1
                # Parcourir tous les bounds
                for k in range(1, len(bestEpisode.boundlist)):
                    currentBound:tuple[int, int] = bestEpisode.boundlist[k]
                    # vérifier si l'écart entre la fin du précédent et la fin de ce bound est inférieur au seuil
                    if currentBound[1] - mergedBound[1] <= (currentBound[1]-currentBound[0] + 1)*(1 + PTKE.GAP_RATIO):
                        # linearisation du bound courrant
                        linearSequenceCurrentBound:list[LinearEvent] = root.content.getSubSequence(currentBound[0], currentBound[1]+1).linearize()

                        # extraction de la séquence linéarisée entre les deux bounds (on inclus toutes les traces intercallées entre la fin des épisodes précédement fusionnés et le debut du bound courrant)
                        if mergedBound[1]+1 < currentBound[0]:
                            # On crée une séquence temporaire
                            subSequence:Sequence = Sequence()
                            # On clone le contenu intercallé
                            subSequence.event_list = copy.deepcopy(root.content.event_list[mergedBound[1]+1:currentBound[0]])
                            # On linéarise cette séquence et on fait sauter le Begin et le End
                            linearSequenceInsertedEvents:list[LinearEvent] = subSequence.linearize()[1:-1]
                            # On merge cette partie avec les évènements intercalés
                            intercaletedEvents = mergeLinearSequences(linearSequenceInsertedEvents, intercaletedEvents)

                        # calcule la fusion entre le dernier état de fusion et cette nouvelle séquence linéarisée
                        mergedLinearSequence = mergeLinearSequences(linearSequenceCurrentBound, mergedLinearSequence)

                        # on étend la plage de la fusion pour englober ce nouvel épisode
                        mergedBound = (mergedBound[0], currentBound[1])
                        mergeCount += 1
                    else:
                        # l'écart entre la fusion précédente et le bound courant est trop importante donc on injecte la fusion précédente dans le root
                        mergeUsingPatternOrNot(mergeCount, root, mergedBound, currentBound[0], newRoot, mergedLinearSequence, intercaletedEvents)

                        # on réinitialise la fusion à la fusion du bound courant et du pattern fournit par TKE
                        mergedLinearSequence = mergeLinearSequences(root.content.getSubSequence(currentBound[0], currentBound[1]+1).linearize(), bestPattern)
                        mergeCount = 1

                        # on réinitialise les traces intercallées
                        intercaletedEvents = []
                        # Et on repositionne le bound de fusion sur le bound courrant
                        mergedBound = currentBound
                
                mergeUsingPatternOrNot(mergeCount, root, mergedBound, len(root.content.event_list), newRoot, mergedLinearSequence, intercaletedEvents)

                # on ne stocke le nouveau root que s'il n'est pas plus long d'un quart de la longueur initiale (le -2 est pour ne pas compter le premier Begin et le dernier End de la linéarisation) et qu'il contient moins de Call que le root original et qu'on ne l'a pas déjà exploré
                if len(newRoot.content.linearize())-2 <= originalRootLength*1.25 and newRoot.content.countCalls() <= originalRootLength and newRoot not in roots:
                    roots.append(newRoot)
                
            best_i += 1
        root_i += 1

    #print ("Analyse terminée, temps de calcul : "+str(time.time()-start_time))
    #print("Meilleure compression trouvée :")
    #print(str(root))
    #print("Fin")
    # Enregistrement des compressions
    for modelRoot in roots[1:]: # On saute le premier root (le root original)
        compressions.set.add(str(modelRoot.content))
    return compressions