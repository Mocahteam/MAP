import copy
import time
from Episode import NonOverlappedEpisode
from Event import Event, Sequence, LinearEvent, mergeLinearSequences
from PTKE import PTKE


# init constant values
PTKE.K = 10
TIME_LIMIT:int = 5

class StabableRoot:
    def __init__(self, root:Sequence) -> None:
        self.root = root
        self.stable = False


class CompressionSet:
	def __init__(self, ) -> None:
		self.set:set[str] = set()
		
    # On considère que des CompressionSet sont égaux s'ils contiennent au moins une compression identique
	def __eq__(self, other:object) -> bool:
		return not self.__ne__(other)
	
	def __ne__(self, other:object) -> bool:
		if not isinstance(other, CompressionSet):
			return NotImplemented
		return self.set.isdisjoint(other.set)
	
	def __hash__(self) -> int:
		return hash(frozenset(self.set))
	
	def __repr__(self) -> str:
		return f'CompressionSet({self.set})'
	
	# \brief Vérifie si au moins une des "compressions" est égale à la solution "solution". Retourne -1 si la compression n'est pas définie (OverTime par exemple). Retourne 1 si au moins une des compressions est égale à la solution ou 2 sinon
	#
	# @solution : représente la solution de référence sous la forme d'une liste
	def getCode(self, solution:str) -> int:
		if "OverTime" in self.set:
			return -1
		if solution in self.set:
			return 1
		return 2
     
def oneRootsNotStable(roots:list[StabableRoot]) -> bool:
    for root in reversed(roots):
        if not root.stable:
            return True
    return False

# MAP => Mining Algorithm Patterns
def MAP (event_list:list[Event], gr:float, ws:float, pb:float) -> CompressionSet:
    PTKE.GAP_RATIO = gr
    NonOverlappedEpisode.WEIGHT_SUPPORT = ws
    NonOverlappedEpisode.PROXIMITY_BALANCING = pb

    compressions:CompressionSet = CompressionSet()

    start_time:float = time.time()

    # Ajout d'un root stabilisable et association de la liste d'évènement à ce root
    stabableRoots:list[StabableRoot] = [StabableRoot(Sequence())]
    stabableRoots[0].root.isRoot = True
    stabableRoots[0].root.event_list = event_list

    # tant qu'il y a au moins un root à explorer
    while (oneRootsNotStable(stabableRoots)):
        # parcourir tous les roots
        stab_i:int = 0
        while stab_i < len(stabableRoots):
            stabableRoot:StabableRoot = stabableRoots[stab_i]
            # si ce root n'est pas stabilisé
            if not stabableRoot.stable:
                # Couper si ça prend trop de temps
                if time.time()-start_time > TIME_LIMIT:
                    compressions.set = {"OverTime"}
                    return compressions

                ptke:PTKE = PTKE()
                bestEpisodes:list[NonOverlappedEpisode] = ptke.getBestEpisodes(stabableRoot.root.event_list)
                # Si aucun épisode n'est renvoyé rien ne sert de poursuivre l'analyse de cet épisode, marquer donc ce root comme stable
                if len(bestEpisodes) == 0:
                    stabableRoot.stable = True
                    stab_i += 1
                    continue
                # Pour chaque épisode donné par tke, simuler la compression
                best_i:int = 0
                while best_i<len(bestEpisodes):
                    currentStabableRoot:StabableRoot = stabableRoot
                    # si on n'est pas sur le dernier meilleur épisode, dupliquer le root et poursuivre l'analyse sur cette copie
                    if best_i < len(bestEpisodes)-1:
                        currentStabableRoot = copy.deepcopy(stabableRoot)
                        stabableRoots.append(currentStabableRoot)

                    bestEpisode:NonOverlappedEpisode = bestEpisodes[best_i]

                    # Si le support de ce meilleur épisode est de 1 rien ne sert de poursuivre l'analyse de cet épisode, dans ce cas on marque ce root comme stable
                    if bestEpisode.getSupport() <= 1:
                        currentStabableRoot.stable = True
                        best_i += 1
                        continue

                    # Si on a un support suffisant on tente l'intégration
                    root:Sequence = currentStabableRoot.root

                    # Transformation de cet épisode en une séquence linéarisée
                    bestPattern:list[LinearEvent] = bestEpisode.event.linearize()

                    #print (str(bestEpisode)+f" => {bestEpisode.score:.2f} (part1:{bestEpisode.part1:.2f}; part2:{bestEpisode.part2:.2f}) (inside:{bestEpisode.inside:.2f}; outside:{bestEpisode.outside:.2f})")

                    # On commence la compression depuis la fin
                    mergedBound:tuple[int, int] = bestEpisode.boundlist[-1]
                    mergedLinearSequence:list[LinearEvent] = mergeLinearSequences(root.getSubSequence(mergedBound[0], mergedBound[1]+1).linearize(), bestPattern)

                    mergeCount:int = 1
                    # Parcourir tous les bounds (de l'avant dernier au premier)
                    for k in range(len(bestEpisode.boundlist)-2, -1, -1):
                        currentBound:tuple[int, int] = bestEpisode.boundlist[k]
                        # vérifier si l'écart entre le début de ce bound et le début du précédent est inférieur au seuil
                        if mergedBound[0] - currentBound[0] <= (currentBound[1]-currentBound[0] + 1)*(1 + PTKE.GAP_RATIO):
                            # extraction de la séquence linéarisée entre les deux bounds (on inclus toutes les traces intercallées entre le début du bound courrant et le début des épisodes précédement fusionnés)
                            linearSequence:list[LinearEvent] = root.getSubSequence(currentBound[0], mergedBound[0]).linearize()

                            # calcule la fusion entre le dernier état de fusion et cette nouvelle séquence linéarisée
                            mergedLinearSequence = mergeLinearSequences(linearSequence, mergedLinearSequence)

                            # on étend la plage de la fusion pour englober ce nouvel épisode
                            mergedBound = (currentBound[0], mergedBound[1])
                        else:
                            # l'écart entre le bound courant et la fusion précédente est trop importante donc on injecte la fusion précédente dans le root
                            # on récupère le début et la fin du root qui ne sont pas touchés
                            beginRoot:list[Event] = root.event_list[:mergedBound[0]]
                            endRoot:list[Event] = root.event_list[mergedBound[1]+1:]
                            # on écrase le root avec le début inchangé
                            root.event_list = beginRoot
                            # on ajoute au root la fusion
                            root.appendLinearSequence(mergedLinearSequence)
                            # on termine en ajoutant la fin inchangée
                            root.event_list += endRoot

                            # on réinitialise la fusion à la fusion du bound courant et du pattern fournit par TKE
                            mergedLinearSequence = mergeLinearSequences(root.getSubSequence(currentBound[0], currentBound[1]+1).linearize(), bestPattern)

                            # Et on repositionne le bound de fusion sur le bound courrant
                            mergedBound = currentBound
                            # on comptabilise une integration supplémentaire
                            mergeCount += 1
                    # injection de la dernière fusion dans le root
                    # on récupère le début et la fin du root qui ne sont pas touchés
                    beginRoot:list[Event] = root.event_list[:mergedBound[0]]
                    endRoot:list[Event] = root.event_list[mergedBound[1]+1:]
                    # on écrase le root avec le début inchangé
                    root.event_list = beginRoot
                    # on ajoute au root la fusion
                    root.appendLinearSequence(mergedLinearSequence)
                    # on termine en ajoutant la fin inchangée
                    root.event_list += endRoot

                    # si le nombre d'intégration au root est égal au nombre de bounds c'est qu'on n'a pas réussi à faire de fusion entre les bounds. Chaque épisode a été réinjecté dans le root. Donc on marque ce root comme stable.
                    if mergeCount == len(bestEpisode.boundlist):
                        currentStabableRoot.stable = True
                        
                    best_i += 1
            stab_i += 1

    #print ("Analyse terminée, temps de calcul : "+str(time.time()-start_time))
    #print("Meilleure compression trouvée :")
    #print(str(root))
    #print("Fin")
    for stabableRoot in stabableRoots:
        compressions.set.add(str(stabableRoot.root))
    return compressions