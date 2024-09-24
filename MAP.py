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
            return compressions

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
                mergedLinearSequence:list[LinearEvent] = mergeLinearSequences(root.content.getSubSequence(mergedBound[0], mergedBound[1]+1).linearize(), bestPattern)
                # On injecte dans le nouveau root les traces précédant le premier bound
                if mergedBound[0] > 0:
                    newRoot.content.event_list = root.content.event_list[:mergedBound[0]]

                mergeCount:int = 1
                # Parcourir tous les bounds
                for k in range(1, len(bestEpisode.boundlist)):
                    currentBound:tuple[int, int] = bestEpisode.boundlist[k]
                    # vérifier si l'écart entre la fin du précédent et la fin de ce bound est inférieur au seuil
                    if currentBound[1] - mergedBound[1] <= (currentBound[1]-currentBound[0] + 1)*(1 + PTKE.GAP_RATIO):
                        # extraction de la séquence linéarisée entre les deux bounds (on inclus toutes les traces intercallées entre la fin des épisodes précédement fusionnés et le debut du bound courrant)
                        if mergedBound[1]+1 < currentBound[0]:
                            # On crée une séquence temproraire
                            subSequence:Sequence = Sequence()
                            # On clone le contenu intercallé
                            subSequence.event_list = copy.deepcopy(root.content.event_list[mergedBound[1]+1:currentBound[0]])
                            # On linéarise cette séquence et on fait sauter le Begin et le End
                            linearSequenceInsertedEvents:list[LinearEvent] = subSequence.linearize()[1:-1]
                            # On insère cette partie à l'avant dernière position de la fusion précédente
                            mergedLinearSequence[-1:-1] = linearSequenceInsertedEvents

                        # linearisation du bound courrant
                        linearSequenceCurrentBound:list[LinearEvent] = root.content.getSubSequence(currentBound[0], currentBound[1]+1).linearize()


                        # calcule la fusion entre le dernier état de fusion et cette nouvelle séquence linéarisée
                        mergedLinearSequence = mergeLinearSequences(linearSequenceCurrentBound, mergedLinearSequence)

                        # on étend la plage de la fusion pour englober ce nouvel épisode
                        mergedBound = (mergedBound[0], currentBound[1])
                    else:
                        # l'écart entre la fusion précédente et le bound courant est trop importante donc on injecte la fusion précédente dans le root
                        newRoot.content.appendLinearSequence(mergedLinearSequence)
                        # on termine en ajoutant les évènements intercalés avec le début du bound courant
                        newRoot.content.event_list += root.content.event_list[mergedBound[1]+1:currentBound[0]]

                        # on réinitialise la fusion à la fusion du bound courant et du pattern fournit par TKE
                        mergedLinearSequence = mergeLinearSequences(root.content.getSubSequence(currentBound[0], currentBound[1]+1).linearize(), bestPattern)

                        # Et on repositionne le bound de fusion sur le bound courrant
                        mergedBound = currentBound
                        # on comptabilise une integration supplémentaire
                        mergeCount += 1
                # injection de la dernière fusion dans le root
                newRoot.content.appendLinearSequence(mergedLinearSequence)
                # on termine en ajoutant la fin inchangée
                newRoot.content.event_list += root.content.event_list[bestEpisode.boundlist[-1][1]+1:]

                # on ne stocke le nouveau root que s'il n'est pas plus long d'un quart de la longueur initiale (le -2 et pour ne pas compter le premier Begin et le dernier End de la linéarisation) et qu'il contient moins de Call que le root original et qu'on ne l'a pas déjà exploré
                if len(newRoot.content.linearize())-2 <= originalRootLength*1.25 and newRoot.content.countCalls() <= originalRootLength and newRoot not in roots:
                    roots.append(newRoot)
                
            best_i += 1
        root_i += 1

    #print ("Analyse terminée, temps de calcul : "+str(time.time()-start_time))
    #print("Meilleure compression trouvée :")
    #print(str(root))
    #print("Fin")
    for modelRoot in roots[1:]: # On saute le premier root (le root original)
        compressions.set.add(str(modelRoot.content))
    return compressions