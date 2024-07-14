import copy
import time
from Episode import NonOverlappedEpisode
from Event import Call, Event, LinearEnd, Sequence, LinearEvent, LinearBegin, mergeLinearSequences
from PTKE import PTKE


# init constant values
PTKE.K = 10
PTKE.QCSP_ALPHA = 2
TIME_LIMIT:int = 300
GAP_RATIO:float = 0.5

class StabableRoot:
    def __init__(self, root:Sequence) -> None:
        self.root = root
        self.stable = False

def oneRootsNotStable(roots:list[StabableRoot]) -> bool:
    for root in reversed(roots):
        if not root.stable:
            return True
    return False

# MAP => Mining Algorithm Patterns
def MAP (event_list:list[Event], gr:float, ws:float, pb:float) -> list[str]:
    GAP_RATIO = gr
    NonOverlappedEpisode.WEIGHT_SUPPORT = ws
    NonOverlappedEpisode.PROXIMITY_BALANCING = pb

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
                if time.time()-start_time > 20:
                    return ["OverTime"]

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
                    rootSize:int = len(root.linearize())

                    # Transformation de cet épisode en une séquence linéarisée
                    bestPattern:list[LinearEvent] = bestEpisode.event.linearize()

                    # par sécurité, ce cas ne devrait jamais arriver
                    if isinstance(bestEpisode.event, Call): # Si le meilleur épisode est un simple Call il faut l'encapsuler dans une séquence
                        bestPattern = [LinearBegin()]+bestPattern+[LinearEnd()]

                    #print (str(bestEpisode)+f" => {bestEpisode.score:.2f} (part1:{bestEpisode.part1:.2f}; part2:{bestEpisode.part2:.2f}) (inside:{bestEpisode.inside:.2f}; outside:{bestEpisode.outside:.2f})")

                    # On commence la compression depuis la fin
                    mergedBound:tuple[int, int] = bestEpisode.boundlist[-1]
                    mergedLinearSequence:list[LinearEvent] = mergeLinearSequences(root.getSubSequence(mergedBound[0], mergedBound[1]+1).linearize(), bestPattern)

                    mergeCount:int = 1
                    # Parcourir tous les bounds (de l'avant dernier au premier)
                    for k in range(len(bestEpisode.boundlist)-2, -1, -1):
                        currentBound:tuple[int, int] = bestEpisode.boundlist[k]
                        # vérifier si l'écart entre ce bound et le précédent est inférieur au seuil
                        if (mergedBound[0] - currentBound[1] - 1)/rootSize <= GAP_RATIO:
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
    compressions:list[str] = []
    for stabableRoot in stabableRoots:
        compressions.append(str(stabableRoot.root))
    return compressions