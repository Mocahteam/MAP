from __future__ import annotations
from abc import abstractmethod
from typing import Optional
import copy

class Event:
    def __init__(self) -> None:
        self.opt:bool = False

    @abstractmethod
    def getLength(self) -> int:
        pass
    
    @abstractmethod
    def linearize(self) -> list[LinearEvent]:
        pass

class Call(Event):
    def __init__(self, call:str) -> None:
        super().__init__()
        self.call:str = call
    
    def __str__(self) -> str:
        return self.call + ('*' if self.opt else '')
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Call) and self.call == other.call
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        return hash(self.call)

    def getLength(self) -> int:
        return 1
    
    def linearize(self) -> list[LinearEvent]:
        return [LinearCall(self)]

class Sequence(Event):
    def __init__(self) -> None:
        super().__init__()
        self.event_list:list[Event] = []
        self.isRoot:bool = False

    def __str__(self) -> str:
        export:str = '' if self.isRoot else '['
        if len(self.event_list) > 0:
            for e in self.event_list:
                export += str(e)
        export += '' if self.isRoot else (']' + ('*' if self.opt else ''))
        return export
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sequence) and self.event_list == other.event_list
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        return hash(str(self))

    def getLength(self) -> int:
        return len(self.event_list)
    
    # Getter pour récupérer une sous partie de la séquence comprise entre l'indice "start" (inclus) et l'indice "end" (exclus).
	# Return la sous partie clonée de la séquence.
    def getSubSequence(self, start:int, end:int) -> Sequence:
        start = start if start >= 0 else 0
        end = end if end > start and end <= self.getLength() else self.getLength()
        subSequence:Sequence = Sequence()
        if end-start == 1 and isinstance(self.event_list[start], Sequence):
            cast:Event = self.event_list[start]
            if isinstance(cast, Sequence):
                subSequence = copy.deepcopy(cast)
            else:
                subSequence.event_list = [copy.deepcopy(self.event_list[start])]
        else:
            subSequence.event_list = copy.deepcopy(self.event_list[start:end])
        return subSequence
    

    # Linéarisation de l'ensemble des traces. 
    # Exemple, la séquence suivante (C modélisent un Call et S une séquence) :
    #       C
    #      \ /
    #   C C S
    #   \_ _/
    # C C S C
    #
    # Est linéarisée de la manière suivante où Sb modélise un début de séquence et Se modélise une fin de séquence :
    # C C Sb C C Sb C Se Se C
    #
    # :param start: indice de départ de linéarisation de la séquence (valeur par défaut : 0)
    # :param end indice de fin de linéarisation de la séquence (valeur par défaut : -1 => fin de la trace)
    #
    # :return: un vecteur d'évènement linéarisé représentant une version linéarisée des traces
    def linearize(self) -> list[LinearEvent]:
        linearSequence:list[LinearEvent] = [LinearBegin()]
        for e in self.event_list:
            linearSequence += e.linearize()
        linearSequence.append(LinearEnd())
        return linearSequence
    
    # Tansforme une liste de LinearEvent en un liste d'Event et l'ajoute à la fin de le séquence
    def appendLinearSequence (self, linearSequence:list[LinearEvent]) -> None:
        i:int = 0
        while i < len(linearSequence): # Ne pas passer par un for ... in ... car on veut contrôler dans la boucle le compteur (cf cas du begin)
            # on ajoute la trace courante
            linearEvent:LinearEvent = linearSequence[i]
            # si on est sur un call
            if isinstance(linearEvent, LinearCall):
                self.event_list.append(linearEvent.call)
                self.event_list[-1].opt = linearEvent.opt
            elif isinstance(linearEvent, LinearBegin):
                # Création d'une nouvelle Sequence
                newSeq:Sequence = Sequence()
                newSeq.opt = linearEvent.opt
                # On récupère les bornes de la sous-séquence
                start:int = i
                end:int = getEndPosOfLinearSequence(linearSequence, i, 1)
                # On récupère le contenue de la sous-séquence linéarisée
                subLinearSequence:list[LinearEvent] = linearSequence[start+1:end]
                # appel récursif sur la sous-séquence pour y intégrer la sous-partie linéarisée
                newSeq.appendLinearSequence(subLinearSequence)
                # On saute à la fin de la sous-séquence linéarisée puisqu'elle vient d'être traité dans l'appel récursif
                i = end-1 # on enlève 1 parce qu'il est rajouté dans le cas général, ainsi i sera bien positionné sur "end"
                # Ajout de cette nouvelle séquende
                self.event_list.append(newSeq)
            i += 1


class LinearEvent:
    def __init__(self) -> None:
        self.opt:bool = False
        self.orientation:str = "" # Orientation indique si la sélection de cet évènement provient de la ligne noté "l" (source s1), de la colonne noté "c" (source s2), ou de la diagonale noté "d" (sources s1 et s2 alignées) lors de la remonté de la matrice de transformation fournie par computeTransformationMatrix

class LinearCall(LinearEvent):
    def __init__(self, call:Call) -> None:
        super().__init__()
        self.call:Call = call
    
    def __str__(self) -> str:
        return str(self.call)
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, LinearCall) and self.call == other.call

class LinearBorder(LinearEvent):
    def __init__(self) -> None:
        super().__init__()

class LinearBegin(LinearBorder):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "["
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, LinearBegin)
    
class LinearEnd(LinearBorder):
    def __init__(self) -> None:
        super().__init__()
        self.overlapped:bool = False

    def __str__(self) -> str:
        return "]"
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, LinearEnd)



# Vérifie si l'évènement à la position "pos" dans "eventList" est optionnel ainsi que l'ensemble des Séquences dans lesquelles cet évènement est inclus
# Exemple des évènements vérifiés
#         +---------------+----+
#         |               |    |
#         |             \ | /\ | /  
#         |              \_/  \_/
# Sb C Sb C C Sb C C Se C Se C Se C Sb C Se
def isHierachyOptional(eventList:list[LinearEvent], pos:int) -> bool:
    pos = 0 if pos < 0 else pos
    # si la position est au delà de la longueur de la trace, renvoyer faux
    if pos > len(eventList):
        return False
    # si l'évènement à la position interrogée est optionnel, ce n'est pas utile de chercher plus loin
    if eventList[pos].opt:
        return True
    startCount:int = 0
    # On remonte la liste des évènements pour vérifier si les End qui englobent cet évènement sont optionnels ou pas
    for i in range(pos+1, len(eventList)):
        # A chaque fois qu'on rencontre un Begin on le note pour ignorer le End correspondant
        if isinstance(eventList[i], LinearBegin):
            startCount += 1
        elif isinstance(eventList[i], LinearEnd):
            if startCount == 0 and eventList[i].opt:
                return True
            elif startCount > 0:
                startCount -= 1 # Décompter un Begin
    return False

# Calcule la distance entre deux séquences linéarisée. Calcule une distance de Levenshtein entre deux séquences en considérant les coûts suivants :
# Coût vertical, passage d'une ligne à l'autre l[i-1]c[j] -> l[i]c[j]
#  - Si key(l[i]) est optionnelle ou une fin de séquence => 0
#  - Sinon => 1
# Coût horizontal, Passage d'une colonne à l'autre l[i]c[j-1] -> l[i]c[j]
#  - Si key(c[j]) est optionnelle ou une fin de séquence => 0
#  - Sinon => 1
# Coût diagonale, Passage de l[i-1]c[j-1] -> l[i]c[j]
#  - Si key(l[i]) != key(c[j]) => 0
#  - Sinon => 1
# 
# Si l1 = ABC et l2 = AC, la matrice résultat sera
#     - A C
# - [[0 1 2],
# A  [1 0 1],
# B  [2 1 1],
# C  [3 2 1]]
# 
# :param s1: la première séquence linéarisée
# :param s2: la seconde séquence linéarisée
# 
# :return: la matrice d'alignement indiquant comment les deux listes de traces ont été alignées. La valeur située en bas à droite de la matrice représente la distance entre s1 et s2
def computeTransformationMatrix(s1:list[LinearEvent], s2:list[LinearEvent]) -> list[list[int]]:
    # matrix est une matrice de s1+1 lignes et s2+1 colonnes remplie de 0
    matrix:list[list[int]] = [[0 for _ in range(len(s2)+1)] for _ in range(len(s1)+1)]

    # Important pour la compréhension de la suite : dans notre adaptation de la distance de Levenshtein on considère que le coût vertical et horizontal est nul pour une option et pour une fin de séquence.

    matrix[0][0] = 0
    # initialisation de la première colonne
    for l in range(1, len(s1)+1):
        matrix[l][0] = matrix[l-1][0] if isHierachyOptional(s1, l-1) or isinstance(s1[l-1], LinearEnd) else matrix[l-1][0]+1 # on ajoute 1 si la trace n'est pas optionnelle (ou fille d'une trace optionnelle) et que ce n'est pas une fin de séquence
    # initialisation de la première ligne
    for c in range(1, len(s2)+1):
        matrix[0][c] = matrix[0][c-1] if isHierachyOptional(s2, c-1) or isinstance(s2[c-1], LinearEnd) else matrix[0][c-1]+1; # on ajoute 1 si la trace n'est pas optionnelle (ou fille d'une trace optionnelle) et que ce n'est pas une fin de séquence

    # calcul de la distance
    substitutionCost:int
    for l in range(1, len(s1)+1):
        for c in range(1, len(s2)+1):
            substitutionCost = 0 if s1[l-1] == s2[c-1] else 1
            matrix[l][c] = min(min(
                matrix[l-1][c]+(0 if isHierachyOptional(s1, l-1) or isinstance(s1[l-1], LinearEnd) else 1), # Attention l dans matrix <=> l-1 dans s1. Donc si s1[l-1] est optionnel ou est une fin de séquence, le coût pour passer de matrix[l-1][X] à matrix[l][X] est 0 et 1 sinon
                matrix[l][c-1]+(0 if isHierachyOptional(s2, c-1) or isinstance(s2[c-1], LinearEnd) else 1)), # Attention c dans matrix <=> c-1 dans s2. Donc si s2[c-1] est optionnel ou est une fin de séquence, le coût pour passer de matrix[X][c-1] à matrix[X][c] est 0 et 1 sinon
                matrix[l-1][c-1] + substitutionCost)
    return matrix

# recherche le point terminal d'une séquence dans une trace linéarisée à partir d'une position de départ et d'un sens de lecture. Si la position de départ est une fin de séquence alors le point de départ est immédiatement retourné. Si le point de départ n'est pas une fin de séquence alors l'algorithme cherchera en aval (ou en amont en fonction du sens de lecture) la fin de la séquence dans laquelle la position courrante est incluse.
# Exemple:
#  +---+---------------------+
#  |   |                     |
#  |   |         +---+       |
#  |   |         | \ | /   \ | / 
#  |   |         |  \_/     \_/ 
# Sb C C Sb C C Sb C Se Se C Se
# 
# :param linearSquence: une trace linéarisée
# :param start: indice de départ dans la trace linéarisée passée en paramètre
# :param step: un nombre entier pour définir l'incrément, permet d'adapter le parcours en fonction de l'ordre dans lesquels les évènements de la trace linéarisée sont placés (cas de la trace inversée lors de la fusion)
#
# :return: l'indice de fin dans "linearSequence" de la séquence dans laquelle l'évènemenr à l'indice "start" est inclus. -1 est retourné si l'algorithme a atteind le bout de la trace sans identifié la fin de la séquence associé à l'évènement de l'indice "start".
def getEndPosOfLinearSequence(linearSequence:list[LinearEvent], start:int, step:int) -> int:
    seqCounter:int = 0
    i:int = 0 if start < 0 else start

    # si le point de départ est une fin de séquence, il faut retourner immediatement
    if isinstance(linearSequence[start], LinearEnd):
        return start
    
    # si le point de départ est un début de séquence, il faut commencer à l'évènement suivant
    if isinstance(linearSequence[start], LinearBegin):
        start += 1 if step > 0 else -1

    # Parcours de la séquence linéarisée dans le bon sens en fonction de step
    for i in range(start, len(linearSequence) if step > 0 else -1, step):
        if isinstance(linearSequence[i], LinearEnd):
            if seqCounter <= 0:
                return i
            else:
                seqCounter -= 1
        elif isinstance(linearSequence[i], LinearBegin):
            seqCounter += 1
    return -1

# Reconfigure mergedSequence en cas de détection de chevauchement, on assume que le dernier élément de la séquence fusionnée est un LinearBegin
def manageOverlapping(mergedSequence:list[LinearEvent]) -> None:
    if not isinstance(mergedSequence[-1], LinearBegin):
        raise Exception	("Prerequisite not satisfied, mergedSequence has to end with a LinearBegin event")
    
    begin:LinearBegin = mergedSequence[-1]

    # Recherche du premier End dans la séquence fusionnée en partant de la fin
    endPos:int = getEndPosOfLinearSequence(mergedSequence, len(mergedSequence)-1, -1) # On parcours en sens inverse car la fusion est inversée, l'indice 0 est la fin de la trace
    castEvent:LinearEvent = mergedSequence[endPos]
    if endPos == -1 or not isinstance(castEvent, LinearEnd):
        raise Exception	("Incompatible type")
    end:LinearEnd = castEvent
    
    # l'orientation du begin est le même que son end, c'est parfait on n'a rien à faire
    if begin.orientation == end.orientation:
        return
    
    # le end associé est une diagonale et notre begin n'est pas une diagonale, on transforme le end associé en l'opposé de l'orientation du begin et on monte toutes les traces intercallées d'un niveau
	# exemple : B[C] vs [BC] => avec "B[C]" sur les lignes de la matrice et "[BC]" sur les colonnes. Sur la remontée on sera sur "C]". Le "]" a été ajouté avec un "d" et on cherche à ajouter le "[" du "B[C]". Donc on transforme le "C]" en "C]]" et on change le end associé à "c" pour noter que l'imbrication des lignes a été traité mais qu'il reste un "c" à gérer.
    elif end.orientation == "d":
        # duplication du end associé dans le vecteur de fusion
        newEnd:LinearEnd = copy.deepcopy(end)
        mergedSequence.insert(endPos+1, newEnd)
        # définition des orientations en conséquence
        newEnd.orientation = begin.orientation # la copie prend l'orientation du begin passé en paramètre puisqu'on considère qu'il est dépilé
        end.orientation = "l" if begin.orientation == "c" else "c" # le end associé est traitée en partie donc il faut lui affecter le complément de l'orientation du begin
    
    # le begin est une diagonale et le end associé est soit "l" soit "c". On va décomposer le "d" pour traiter le end associé. On ajoute donc une fermeture pour cette première composante du "d" et on fait un appel récursif pour traiter le complément du "d" non traité.
	# exemple : [B]C vs [BC] => avec "[B]C" sur les lignes de la matrice et "[BC]" sur les colonnes. Sur la remontée on sera sur "B]C]". Les deux "]" ont été ajoutés une première fois en colonne puis en ligne et on cherche à ajouter "[" en diagonale donc à la fois sur "l" et "c". Donc on ajoute un "[" supplémentaire et on fait un appel récursif pour gérer le complément non traité du "d".
    elif begin.orientation == "d":
        # on transforme le begin pour noter que l'on traite une partie de son "d" en le mettant en correspondance avec l'orientation de son end
        begin.orientation = end.orientation
        # on ajoute un nouveau begin pour intégrer le complément
        newBegin:LinearBegin = LinearBegin()
        newBegin.orientation =  "l" if end.orientation == "c" else "c"
        mergedSequence.append(newBegin)
        # On fait un appel récursif pour gérer les chevauchement éventuel de ce nouveau begin
        manageOverlapping(mergedSequence)
	
    # le begin est soit "l" soit "c" et le end associé est l'opposée (cas de séquences qui se chevochent)
	# exemple : A[BC] vs [AB]C => avec "A[BC]" sur les lignes de la matrice et "[AB]C" sur les colonnes. Sur la remontée on sera sur "B]C]". Les deux "]" ont été ajoutés une première fois en ligne puis en colonne (dernier ajout en "c") et on cherche à ajouter "[" en ligne ce qui est pour l'instant pas possible puisque l'orientation du begin n'est pas cohérent avec l'orientation de son end associé. On va donc passer les traces non incluses dans le chevauchement en optionnelle pour obtenir [*A[B]*C] qui est bien un moyen de fusionner les deux traces en exemple.
	# Soit "x" l'orientation du begin (l'orientation du end associé est le complément de "x") :
	# 1- Chercher dans les ends précédents le premier "x" (ou "d") disponible correspondant à l'orientation du begin, noté "t" pour target.
	# 2- Mettre toutes les traces comprises entre "t" (s'il est trouve) et le end associé comme optionnelle (si on tombe sur une séquence on la marque comme optionnelle et on saute directement à son End pour éviter de traiter tout ses enfants).
	# 3- Noter "t" en chevauchement de manière à ce que toute nouvelle trace soit notée comme optionnelle tant que ce end n'a pas été fermé.
    elif (begin.orientation == "l" and end.orientation == "c") or (begin.orientation == "c" and end.orientation == "l"):
		# 1- Chercher dans les ends précédents le premier "x" (ou "d") disponible correspondant à l'orientation du begin, noté "t" pour target.
        tPos:int = endPos-1
        tEndFound = False
        while not tEndFound and tPos >= 0:
            tPos = getEndPosOfLinearSequence(mergedSequence, tPos-1, -1) # On parcours en sens inverse car la fusion est inversée, l'indice 0 est la fin de la trace
            if tPos >= 0 and mergedSequence[tPos].orientation == begin.orientation or mergedSequence[tPos].orientation == "d":
                tEndFound = True
        if tPos >= 0:
            # 2- Mettre toutes les traces comprises entre "t" (s'il est trouve) et le end associé comme optionnelle (si on tombe sur une séquence on la marque comme optionnelle et on saute directement à son End pour éviter de traiter tout ses enfants).
            level:int = 0
            for i in range(tPos+1, endPos):
                if level == 0:
                    mergedSequence[i].opt = True
                if isinstance(mergedSequence[i], LinearEnd):
                    level += 1
                if isinstance(mergedSequence[i], LinearBegin):
                    level -= 1
		    # 3- Noter le end associé en chevauchement de manière à ce que toute nouvelle trace soit notée comme optionnelle tant que ce end n'a pas été fermé.
            castEvent:LinearEvent = mergedSequence[tPos]
            if isinstance(castEvent, LinearEnd):
                castEvent.overlapped = True


# Gère les ajouts de Begin et End. On assume pour cette fonction que le dernier évènement de de la séquence linéarisée est le dernier Begin ou End ajouté sur lequel on va travailler
#
# :param mergedSequence: la séquence fusionnée à adapter en fonction des enchainements de Begin et End et de leur orientation (Cette liste est inversé, le premier élément de la liste doit être le plus ancien).
def manageBorder(mergedSequence:list[LinearEvent]) -> None:
    # Récupérer la dernière extrémitée ajoutée
    border = mergedSequence[-1]
    if isinstance(border, LinearEnd):
        # on se sert de l'attribut "optionnel" d'une séquence End pour coder le fait que cette séquence est potentiellement optionnelle jusqu'à preuve du contraire (si elle ne contient aucune trace alignée). Cette astuce sera aussi utilisée pour déterminer si un Call doit être mis en option sur un changement de ligne ou de colonne (pas la diagonale) en effet si le End de la séquence mère est tagué Optionnel alors il n'est pas nécessaire de noter les Call enfants comme optionnels.
        # # Donc, par défaut, on tague toutes les Séquences End comme optionnelle. Si ensuite en construisant la fusion on trouve des traces alignées, on annulera cette mise en option.
        border.opt = True
	# ici on est sur un Begin, il faut vérifier si on peut dépiler simplement ou s'il faut faire des opérations spécifiques
    elif isinstance(border, LinearBegin):
        manageOverlapping(mergedSequence)
    else:
        raise Exception ("Warning! the last event of mergedSequence as to be a LinearBorder")
	

# Procède à la fusion de s1 et s2 à l'aide de la matrice de transformation transformationMatrix.
#
# :param s1: la première séquence linéarisée passée en entrée de la fusion.
# :param s2: la seconde séquence linéarisée passée en entrée de la fusion.
# :param transformationMatrix: la matrice de transformation permettant de savoir comment aligner les traces de s1 et s2 (voir computeTransformationMatrix pour la génération de cette matrice de transformation)
# :return: résultat de la fusion entre s1 et s2 (Attention la liste retournée est inversée à savoir que le premier évènement est la fusion des derniers évènements de s1 et s2). 
def computeMergedSequence(s1:list[LinearEvent], s2:list[LinearEvent], transformationMatrix:list[list[int]]) -> list[LinearEvent]:
    # Séquence fusionnée
    mergedSequence:list[LinearEvent] = []
    mergedEvent:Optional[LinearEvent] = None
    # partir du coin inférieur droit de la matrice et remonter soit à gauche, soit en haut, soit en diagonale (sémantique des orientations : gauche c-1 <- c => ajouter colonne c (si Call, taguer optionnel) ; haut l-1 <- l => ajouter ligne l (si Call, taguer optionnel) ; diagonale [l-1][c-1] <- [l][c] => ajouter la fusion de la ligne l et la colonne c)
    l:int = len(transformationMatrix)-1
    c:int = len(transformationMatrix[0])-1
    # On s'arrête si Si l == 0 et c == 0
    while l > 0 or c > 0:
        # si on est sur la première ligne (ou la première colonne) prendre la trace de la ligne (respectivement colonne)
        if l == 0 or c == 0:
            mergedEvent = copy.deepcopy(s2[c-1] if l == 0 else s1[l-1]) # transformationMatrix contient une ligne et une colonne de plus que s1 et s2, d'où le -1
            mergedEvent.orientation = "c" if l == 0 else "l"
            mergedSequence.append(mergedEvent) 
            if l == 0:
                c -= 1
            else:
                l -= 1
        # les deux traces sont des Call
        elif isinstance(s1[l-1], LinearCall) and isinstance(s2[c-1], LinearCall):
            # Si la diagonale est le coût minimal et colonne c == ligne l privilégier la diagonale sinon privilégier le min entre haut et gauche, si égalité réduire en priorité la trace la plus longue, sinon à défaut prendre à gauche.

            # si les deux Call sont égaux et le coût minimal est la diagonale, prendre la diagonale
            if s1[l-1] == s2[c-1] and transformationMatrix[l-1][c-1] <= min(transformationMatrix[l-1][c], transformationMatrix[l][c-1]):
                # on ajoute un des deux (ils sont égaux)
                mergedEvent = copy.deepcopy(s1[l-1])
                mergedEvent.orientation = "d"
                # on fusionne le caractère optionnel des deux Calls
                mergedEvent.opt = s1[l-1].opt or s2[c-1].opt
                mergedSequence.append(mergedEvent)
                # noter que le end associé ne peut plus être optionnel (voir commentaire dans manageBorder)
                endPos:int = getEndPosOfLinearSequence(mergedSequence, len(mergedSequence)-1, -1) # On parcours en sens inverse car la fusion est inversée, l'indice 0 est la fin de la trace
                mergedSequence[endPos].opt = False
                l -= 1
                c -= 1
            # sinon si coût minimum sur la ligne d'en dessus ou coût égal mais le nombre de ligne est plus grand que le nombre de colonne, prendre la ligne du dessus
            elif transformationMatrix[l-1][c] < transformationMatrix[l][c-1] or (transformationMatrix[l-1][c] == transformationMatrix[l][c-1] and len(s1) > len(s2)):
                mergedEvent = copy.deepcopy(s1[l-1])
                mergedEvent.orientation = "l"
                mergedSequence.append(mergedEvent)
                l -= 1
			# sinon on prend la colonne de gauche
            else:
                mergedEvent = copy.deepcopy(s2[c-1])
                mergedEvent.orientation = "c"
                mergedSequence.append(mergedEvent)
                c -= 1
        # une des traces est un Call et l'autre est une séquence
        elif (isinstance(s1[l-1], LinearCall) and isinstance(s2[c-1], LinearBorder)) or (isinstance(s1[l-1], LinearBorder) and  isinstance(s2[c-1], LinearCall)):
			# privilégier l'orientation vers le haut ou la gauche avec le poid minimal (interdire la diagonale). Si égalité privilégier l'orientation du Seq
            mergedEvent = None
			# si le coût de la ligne du haut est plus petit que la colonne de gauche ou qu'ils sont égaux et que la séquence se trouve sur la ligne du haut, prendre la ligne
            if transformationMatrix[l-1][c] < transformationMatrix[l][c-1] or (transformationMatrix[l-1][c] == transformationMatrix[l][c-1] and isinstance(s1[l-1], LinearBorder)):
                mergedEvent = copy.deepcopy(s1[l-1])
                mergedEvent.orientation = "l"
                mergedSequence.append(mergedEvent)
                l -= 1
            # si le coût de la colonne de gauche est plus petit que la ligne du haut ou qu'ils sont égaux et que la séquence se trouve sur la colonne de gauche, prendre la colonne
            elif transformationMatrix[l][c-1] < transformationMatrix[l-1][c] or (transformationMatrix[l-1][c] == transformationMatrix[l][c-1] and isinstance(s2[c-1], LinearBorder)):
                mergedEvent = copy.deepcopy(s2[c-1])
                mergedEvent.orientation = "c"
                mergedSequence.append(mergedEvent)
                c -= 1
            # Gestion de l'ajoute d'un bord
            if mergedEvent != None and isinstance(mergedEvent, LinearBorder):
                manageBorder(mergedSequence)
        # Ici les deux traces sont des séquences
        else:
            # Si la diagonale est le coût minimal et colonne c == ligne l privilégier la diagonale, sinon privilégier le min entre haut et gauche, si égalité et colonne c != ligne l privilégier le Begin sinon si égalité et colonne c == ligne l réduire en priorité la trace la plus longue, sinon à défaut prendre à gauche.

            mergedEvent = None
            # si les deux Séquences sont du même type et le coût minimal est la diagonale, prendre la diagonale
            if type(s1[l-1]) == type(s2[c-1]) and transformationMatrix[l-1][c-1] <= min(transformationMatrix[l-1][c], transformationMatrix[l][c-1]):
                mergedEvent = copy.deepcopy(s1[l-1])
                mergedEvent.orientation = "d"
                # on fusionne le caractère optionnel des deux Séquences
                mergedEvent.opt = s1[l-1].opt or s2[c-1].opt
                mergedSequence.append(mergedEvent)
                l -= 1
                c -= 1
            # sinon si coût minimum sur la ligne d'en dessus ou coût égal et (les deux séquences sont différentes et celle de la ligne d'au dessus est un Begin OU les deux séquence sont de même nature et le nombre de ligne est plus grand que le nombre de colonne), prendre la ligne du dessus
            elif transformationMatrix[l-1][c] < transformationMatrix[l][c-1] or (transformationMatrix[l-1][c] == transformationMatrix[l][c-1] and ((type(s1[l-1]) != type(s2[c-1]) and isinstance(s1[l-1], LinearBegin)) or (len(s1) > len(s2)))):
                mergedEvent = copy.deepcopy(s1[l-1])
                mergedEvent.orientation = "l"
                mergedSequence.append(mergedEvent)
                l -= 1
            # sinon on prend la colonne de gauche
            else:
                mergedEvent = copy.deepcopy(s2[c-1])
                mergedEvent.orientation = "c"
                mergedSequence.append(mergedEvent)
                c -= 1
            # Gestion de la pile
            if isinstance(mergedEvent, LinearBorder):
                manageBorder(mergedSequence)
    return mergedSequence

# Déterminer les options en fonction des orientations prises et des chevauchements détectés
#
# :param mergedSequence: la séquence fusionnée à adapter en fonction des enchainements de Begin et End et de leur orientation (Cette liste est inversé, le premier élément de la liste doit être le plus ancien).
def updateOptions(mergedSequence:list[LinearEvent]) -> None:
    for eventPos in range(len(mergedSequence)):
        event:LinearEvent = mergedSequence[eventPos]
        # On ne touche pas à l'option dans le cas où on est sur un End
        if not isinstance(event, LinearEnd):
            # récupération de la fin de séquence associée à cet évènment
            endPos:int = getEndPosOfLinearSequence(mergedSequence, eventPos, -1)
            end:Optional[LinearEnd] = None
            if endPos >= 0:
                castEvent:LinearEvent = mergedSequence[endPos]
                if isinstance(castEvent, LinearEnd):
                    end = castEvent
            # On définit cette trace optionnelle
            #   s'il n'y a pas eu d'alignement ET
            #       c'est un Call ET
            #           il n'est pas inclus dans une séquence
            #           OU
            #           il est inclus dans une séquence non optionnelle
            #       OU
            #       c'est un Begin dont sa fin est restée taguée optionnelle
            #       OU
            #       que son end associé nous indique un chevauchement de séquence
            #   OU
            #   s'il y a eu un alignment et que son end associé nous indique un chevauchement de séquence
            if (event.orientation != "d" and ((isinstance(event, LinearCall) and (end == None or not end.opt)) or (isinstance(event, LinearBegin) and end != None and end.opt) or (end != None and end.overlapped))) or (event.orientation == "d" and end != None and end.overlapped):
                event.opt = True

# Fusionne deux séquences linéarisées
#
# Cette fonction permet de construire une nouvelle séquence linéarisée la plus générale possible à partir de deux séquences s1 et s2.
#
# Exemple de cas singuliers :
#  1 - [AB[C]] et [[A]BC] => [[A]B[C]]
#  2 - A[C] et AB => A[*C]B
#  3 - A[BC] et [AB]C => [*A[B]*C]
#  4 - A[B] et [AB] => [A[B]]
#  5 - [A]B et [AB] => [[A]B]
#  
# :param s1: la première séquence linéarisée passée en entrée de la fusion.
# :param s2: la seconde séquence linéarisée passée en entrée de la fusion.
#
# :return: la nouvelle séquence créée résultante de la fusion de s1 et s2
def mergeLinearSequences(s1:list[LinearEvent], s2:list[LinearEvent]) -> list[LinearEvent]:
    mergedSequence:list[LinearEvent] = [] # La séquence contenant le résultat de la fusion

    transformationMatrix:list[list[int]] = computeTransformationMatrix(s1, s2)

    # Construction de la fusion entre s1 et s2 en prenant en compte les chevauchements de Séquence
    mergedSequence:list[LinearEvent] = computeMergedSequence(s1, s2, transformationMatrix)

    # Déterminer les options en fonction des orientations prises et des chevauchements détectés
    updateOptions(mergedSequence)

    # On met le vecteur de fusion dans le bon sens
    mergedSequence.reverse()
    return mergedSequence