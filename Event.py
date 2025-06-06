from __future__ import annotations
from abc import abstractmethod
from typing import Optional
import copy

class Event:
    """
    Abstract base class representing an event in a sequence.
    
    This class serves as the foundation for all event types in the sequence system.
    It provides basic functionality and interface that all events must implement.
    
    Attributes:
        opt (bool): Flag indicating if the event is optional
    """
    def __init__(self) -> None:
        self.opt:bool = False

    @abstractmethod
    def isEquiv(self, other: object) -> bool:
        """
        Checks if two events are equivalent, ignoring the 'opt' property.
        
        Args:
            other (object): The event to compare with
            
        Returns:
            bool: True if the events are equivalent, False otherwise
        """
        pass

    @abstractmethod
    def getLength(self) -> int:
        """
        Gets the length of the event.
        
        Returns:
            int: The length of the event
        """
        pass
    
    @abstractmethod
    def linearize(self) -> list[LinearEvent]:
        """
        Converts the event into a linear sequence of events.
        
        Returns:
            list[LinearEvent]: A list of linearized events
        """
        pass
    
    @abstractmethod
    def countCalls(self) -> int:
        """
        Counts the number of calls in this event.
        
        Returns:
            int: The total number of calls
        """
        pass

class Call(Event):
    """
    Represents a call event in a sequence.
    
    A Call is a basic event that represents a single function call or operation.
    
    Attributes:
        call (str): The name or identifier of the call
        opt (bool): Inherited from Event, indicates if the call is optional
    """
    def __init__(self, call:str) -> None:
        """
        Initializes a new Call event.
        
        Args:
            call (str): The name or identifier of the call
        """
        super().__init__()
        self.call:str = call
    
    def __str__(self) -> str:
        """
        Returns a string representation of the call.
        
        Returns:
            str: The call string, with '*' appended if the call is optional
        """
        return self.call + ('*' if self.opt else '')
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two calls are equal.
        
        Args:
            other (object): The call to compare with
            
        Returns:
            bool: True if the calls are equal (same call string and opt value), False otherwise
        """
        return isinstance(other, Call) and self.call == other.call and self.opt == other.opt
    
    def __ne__(self, other: object) -> bool:
        """
        Checks if two calls are not equal.
        
        Args:
            other (object): The call to compare with
            
        Returns:
            bool: True if the calls are not equal, False otherwise
        """
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        """
        Computes the hash value for the call.
        
        Returns:
            int: Hash value based on the call string
        """
        return hash(self.call)
    
    def isEquiv(self, other: object) -> bool:
        """
        Checks if two calls are equivalent (same call string, ignoring opt value).
        
        Args:
            other (object): The call to compare with
            
        Returns:
            bool: True if the calls are equivalent, False otherwise
        """
        return isinstance(other, Call) and self.call == other.call

    def getLength(self) -> int:
        """
        Gets the length of the call (always 1).
        
        Returns:
            int: Always returns 1 as a call is an atomic event
        """
        return 1
    
    def linearize(self) -> list[LinearEvent]:
        """
        Converts the call into a linear sequence (single LinearCall).
        
        Returns:
            list[LinearEvent]: A list containing a single LinearCall
        """
        return [LinearCall(self)]
    
    def countCalls(self) -> int:
        """
        Counts the number of calls (always 1).
        
        Returns:
            int: Always returns 1 as this represents a single call
        """
        return 1

class Sequence(Event):
    """
    Represents a sequence of events.
    
    A Sequence is a container that holds multiple events in order. It can be marked as
    a root sequence or as an optional sequence.
    
    Attributes:
        event_list (list[Event]): List of events in the sequence
        isRoot (bool): Flag indicating if this is a root sequence
        opt (bool): Inherited from Event, indicates if the sequence is optional
    """
    def __init__(self) -> None:
        """
        Initializes a new empty sequence.
        """
        super().__init__()
        self.event_list:list[Event] = []
        self.isRoot:bool = False

    def __str__(self) -> str:
        """
        Returns a string representation of the sequence.
        
        The sequence is represented with square brackets unless it's a root sequence.
        Optional sequences are marked with '*'.
        
        Returns:
            str: String representation of the sequence
        """
        export:str = '' if self.isRoot else '['
        if len(self.event_list) > 0:
            for e in self.event_list:
                export += str(e)
        export += '' if self.isRoot else (']' + ('*' if self.opt else ''))
        return export
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two sequences are equal.
        
        Args:
            other (object): The sequence to compare with
            
        Returns:
            bool: True if the sequences have the same events in the same order and same opt value
        """
        return isinstance(other, Sequence) and self.opt == other.opt and len(self.event_list) == len(other.event_list) and self.event_list == other.event_list
    
    def __ne__(self, other: object) -> bool:
        """
        Checks if two sequences are not equal.
        
        Args:
            other (object): The sequence to compare with
            
        Returns:
            bool: True if the sequences are not equal
        """
        return not self.__eq__(other)
    
    def __hash__(self) -> int:
        """
        Computes the hash value for the sequence.
        
        Returns:
            int: Hash value based on the tuple of events in the sequence
        """
        return hash(tuple(self.event_list))
    
    def isEquiv(self, other: object) -> bool:
        """
        Checks if two sequences are equivalent (same events, ignoring opt value).
        
        Args:
            other (object): The sequence to compare with
            
        Returns:
            bool: True if the sequences are equivalent
        """
        return isinstance(other, Sequence) and len(self.event_list) == len(other.event_list) and self.event_list == other.event_list

    def getLength(self) -> int:
        """
        Gets the length of the sequence (number of events).
        
        Returns:
            int: The number of events in the sequence
        """
        return len(self.event_list)
    
    def countCalls(self) -> int:
        """
        Counts the total number of calls in the sequence.
        
        Returns:
            int: The total number of calls across all events in the sequence
        """
        counter:int = 0
        for e in self.event_list:
            counter += e.countCalls()
        return counter
    
    def getSubSequence(self, start:int, end:int) -> Sequence:
        """
        Extracts a subsequence from the current sequence.
        
        Creates a new sequence containing events from start (inclusive) to end (exclusive).
        Special handling is done for single-event sequences to preserve their structure.
        
        Args:
            start (int): Starting index (inclusive)
            end (int): Ending index (exclusive)
            
        Returns:
            Sequence: A new sequence containing the specified subsequence
        """
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
        """
        Linearizes the sequence into a flat list of events.

        Transforms a hierarchical sequence structure into a linear sequence where nested
        sequences are represented by Begin/End markers.

        Example:
        Given this hierarchical sequence (where C=Call, S=Sequence):
        ```
              C
             \\ /
          C C S
          \\_ _/
        C C S C
        ```

        The linearized output will be (where Sb=SequenceBegin, Se=SequenceEnd):
        ```
        C C Sb C C Sb C Se Se C
        ```

        Returns:
            list[LinearEvent]: A list of linear events representing the flattened sequence
        """
        linearSequence:list[LinearEvent] = [LinearBegin()]
        for e in self.event_list:
            linearSequence += e.linearize()
        linearSequence.append(LinearEnd())
        return linearSequence
    
    # Tansforme une liste de LinearEvent en une liste d'Event et l'ajoute à la fin de la séquence
    def appendLinearSequence (self, linearSequence:list[LinearEvent]) -> None:
        """
        Transforms a list of LinearEvents into Events and appends them to the sequence.

        This method recursively processes a linearized sequence and reconstructs the
        hierarchical structure by:
        1. Converting LinearCalls back to Calls
        2. Creating new Sequences when encountering LinearBegin markers
        3. Processing nested sequences recursively
        4. Preserving optional flags from the linear events

        Args:
            linearSequence (list[LinearEvent]): The linearized sequence to convert and append
        """
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
                # Ajout de cette nouvelle séquence
                self.event_list.append(newSeq)
            i += 1

class LinearEvent:
    """
    Base class for linear events used in sequence linearization.
    
    A linear event is a basic building block used to represent sequences in a linear form.
    It can be marked as optional and has an orientation indicating its source in the merge process.
    
    Attributes:
        opt (bool): Flag indicating if the event is optional
        orientation (str): Source orientation ('l' for line/s1, 'c' for column/s2, 'd' for diagonal/both)
    """
    def __init__(self) -> None:
        self.opt:bool = False
        # Orientation indique si la sélection de cet évènement provient de la ligne noté "l" (source s1), de la colonne noté "c" (source s2), ou de la diagonale noté "d" (sources s1 et s2 alignées) lors de la remonté de la matrice de transformation fournie par computeTransformationMatrix
        self.orientation:str = "" 

class LinearCall(LinearEvent):
    """
    Represents a linearized call event.
    
    A LinearCall wraps a Call event in the linearized sequence representation.
    
    Attributes:
        call (Call): The original Call event being wrapped
        opt (bool): Inherited from LinearEvent
        orientation (str): Inherited from LinearEvent
    """
    def __init__(self, call:Call) -> None:
        """
        Initializes a new LinearCall.
        
        Args:
            call (Call): The Call event to wrap
        """
        super().__init__()
        self.call:Call = call
    
    def __str__(self) -> str:
        """
        Returns a string representation of the linear call.
        
        Returns:
            str: String representation of the wrapped call
        """
        return str(self.call)
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two linear calls are equal.
        
        Args:
            other (object): The linear call to compare with
            
        Returns:
            bool: True if both wrap the same call
        """
        return isinstance(other, LinearCall) and self.call == other.call

class LinearBorder(LinearEvent):
    """
    Abstract base class for sequence border events (Begin/End).
    
    Border events mark the boundaries of sequences in the linearized representation.
    """
    def __init__(self) -> None:
        super().__init__()

class LinearBegin(LinearBorder):
    """
    Represents the beginning of a sequence in linear form.
    
    Marked with '[' in string representation.
    """
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        """
        Returns the string representation of sequence beginning.
        
        Returns:
            str: Always returns '['
        """
        return "["
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two sequence beginnings are equal.
        
        Args:
            other (object): The border to compare with
            
        Returns:
            bool: True if other is also a LinearBegin
        """
        return isinstance(other, LinearBegin)
    
class LinearEnd(LinearBorder):
    """
    Represents the end of a sequence in linear form.
    
    Marked with ']' in string representation.
    Can be marked as overlapped to handle special merge cases.
    
    Attributes:
        overlapped (bool): Flag indicating if this end is part of an overlapping sequence
    """
    def __init__(self) -> None:
        super().__init__()
        self.overlapped:bool = False

    def __str__(self) -> str:
        """
        Returns the string representation of sequence end.
        
        Returns:
            str: Always returns ']'
        """
        return "]"
    
    def __eq__(self, other: object) -> bool:
        """
        Checks if two sequence ends are equal.
        
        Args:
            other (object): The border to compare with
            
        Returns:
            bool: True if other is also a LinearEnd
        """
        return isinstance(other, LinearEnd)

class LinearEventWithStats:
    """
    Container for a linear event sequence with associated statistics.
    
    Tracks the number of optional events, alignments, and merges performed
    during sequence construction.
    
    Attributes:
        linearEvent (list[LinearEvent]): The sequence of linear events
        countOpt (int): Count of optional events
        countAlign (int): Count of aligned events
        countMerge (int): Count of merge operations
    """
    def __init__(self) -> None:
        self.linearEvent:list[LinearEvent] = []
        self.countOpt:int = 0
        self.countAlign:int = 0
        self.countMerge:int = 0
    
    def update(self, linearEvent:list[LinearEvent], countOpt:int, countAlign:int) -> None:
        """
        Updates the statistics for this sequence.
        
        Args:
            linearEvent (list[LinearEvent]): New sequence of events
            countOpt (int): Number of optional events to add
            countAlign (int): Number of alignments to add
        """
        self.linearEvent = linearEvent
        self.countOpt += countOpt
        self.countAlign += countAlign
        self.countMerge += 1

class Root:
    """
    Root container for a sequence with associated statistics.
    
    Holds a sequence and tracks merge statistics.
    
    Attributes:
        content (Sequence): The contained sequence
        countOpt (int): Count of optional events
        countAlign (int): Count of alignments
        countMerge (int): Count of merge operations
    """
    def __init__(self, root:Sequence) -> None:
        self.content:Sequence = root
        self.countOpt:int = 0
        self.countAlign:int = 0
        self.countMerge:int = 0

    def __eq__(self, other:object) -> bool:
        """
        Checks if two roots are equal.
        
        Args:
            other (object): The root to compare with
            
        Returns:
            bool: True if both contain the same sequence
        """
        return isinstance(other, Root) and self.content == other.content

# Vérifie si l'évènement à la position "pos" dans "eventList" est optionnel ainsi que l'ensemble des Séquences dans lesquelles cet évènement est inclus
# Exemple des évènements vérifiés
#         +---------------+----+
#         |               |    |
#         |             \ | /\ | /  
#         |              \_/  \_/
# Sb C Sb C C Sb C C Se C Se C Se C Sb C Se
def isHierachyOptional(eventList:list[LinearEvent], pos:int) -> bool:
    """
    Checks if an event at a given position is optional in its hierarchical context.
    
    Verifies if the event itself is optional or if it's contained within an optional sequence.
    The function traverses the sequence structure to check all containing sequences.
    
    Example structure checked:
    ```
            +---------------+----+
            |               |    |
            |             \\ | /\\ | /  
            |              \\_/  \\_/
    Sb C Sb C C Sb C C Se C Se C Se
    ```
    
    Args:
        eventList (list[LinearEvent]): The list of linear events to check
        pos (int): Position of the event to check
        
    Returns:
        bool: True if the event is optional in its context, False otherwise
    """
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
    """
    Computes a transformation matrix between two linearized sequences.
    
    Calculates a Levenshtein-like distance matrix with the following costs:
    - Vertical cost (l[i-1]c[j] -> l[i]c[j]):
        * 0 if l[i] is optional or a sequence end
        * 1 otherwise
    - Horizontal cost (l[i]c[j-1] -> l[i]c[j]):
        * 0 if c[j] is optional or a sequence end
        * 1 otherwise
    - Diagonal cost (l[i-1]c[j-1] -> l[i]c[j]):
        * 0 if l[i] != c[j]
        * 1 if l[i] == c[j]
    
    Example:
    For s1 = ABC and s2 = AC, the result matrix is:
    ```
        - A C
    - [[0 1 2],
    A  [1 0 1],
    B  [2 1 1],
    C  [3 2 1]]
    ```
    
    Args:
        s1 (list[LinearEvent]): First linearized sequence
        s2 (list[LinearEvent]): Second linearized sequence
        
    Returns:
        list[list[int]]: Transformation matrix showing how to align the sequences
    """
    # matrix est une matrice de s1+1 lignes et s2+1 colonnes remplie de 0
    matrix:list[list[int]] = [[0 for _ in range(len(s2)+1)] for _ in range(len(s1)+1)]

    # Important pour la compréhension de la suite : dans notre adaptation de la distance de Levenshtein on considère que le coût vertical et horizontal est nul pour une option et pour une fin de séquence.

    matrix[0][0] = 0
    # initialisation de la première colonne
    for l in range(1, len(s1)+1):
        # on ajoute 1 si la trace n'est pas optionnelle (ou fille d'une trace optionnelle) et que ce n'est pas une fin de séquence
        matrix[l][0] = matrix[l-1][0] if isHierachyOptional(s1, l-1) or isinstance(s1[l-1], LinearEnd) else matrix[l-1][0]+1 
    # initialisation de la première ligne
    for c in range(1, len(s2)+1):
        # on ajoute 1 si la trace n'est pas optionnelle (ou fille d'une trace optionnelle) et que ce n'est pas une fin de séquence
        matrix[0][c] = matrix[0][c-1] if isHierachyOptional(s2, c-1) or isinstance(s2[c-1], LinearEnd) else matrix[0][c-1]+1

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
    """
    Finds the end position of a sequence from a given starting point.
    
    If the starting position is a sequence end, returns immediately.
    Otherwise, searches forward or backward (based on step) to find the corresponding
    sequence end.
    
    Example structure:
    ```
     +---+---------------------+
     |   |                     |
     |   |         +---+       |
     |   |         | \\ | /   \\ | / 
     |   |         |  \\_/     \\_/ 
    Sb C C Sb C C Sb C Se Se C Se
    ```
    
    Args:
        linearSequence (list[LinearEvent]): The linearized sequence to search in
        start (int): Starting position in the sequence
        step (int): Direction to search (positive for forward, negative for backward)
        
    Returns:
        int: Position of the sequence end, or -1 if not found
    """
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
    """
    Handles overlapping sequences during merge.
    
    Reconfigures the merged sequence when overlapping is detected. Assumes the last
    element of the merged sequence is a LinearBegin.
    
    The function handles three main cases:
    1. Begin and End have same orientation - no action needed
    2. End is diagonal but Begin isn't - transforms End to match Begin's orientation
    3. Begin is diagonal but End isn't - splits Begin to handle both orientations
    4. Begin and End have opposite orientations - handles sequence overlap
    
    Args:
        mergedSequence (list[LinearEvent]): The sequence being merged (modified in-place)
        
    Raises:
        Exception: If prerequisites are not met or incompatible types are found
    """
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
        tPos:int = endPos
        tEndFound = False
        while not tEndFound and tPos > 0:
            # On cherche à partir de tPos-1 mais attention si l'évènement à tPos-1 est un begin il faut sauter jusqu'à son end pour chercher le premier end englobant ensuite
            prevEvent:LinearEvent = mergedSequence[tPos-1]
            tPos = getEndPosOfLinearSequence(mergedSequence, tPos-1, -1) # On parcours en sens inverse car la fusion est inversée, l'indice 0 est la fin de la trace
            if isinstance(prevEvent, LinearBegin):
                continue # Si l'event précédent est un Begin on ne fait rien de plus, tPos référence son End, on va donc poursuivre la recherche à partir de l'event précédant ce End
            elif tPos >= 0 and mergedSequence[tPos].orientation == begin.orientation or mergedSequence[tPos].orientation == "d":
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


# Gère les ajouts de Begin et End. On assume pour cette fonction que le dernier évènement de la séquence linéarisée est le dernier Begin ou End ajouté sur lequel on va travailler
#
# :param mergedSequence: la séquence fusionnée à adapter en fonction des enchainements de Begin et End et de leur orientation (Cette liste est inversé, le premier élément de la liste doit être le plus ancien).
def manageBorder(mergedSequence:list[LinearEvent]) -> None:
    """
    Manages sequence borders during merge.
    
    Handles the addition of Begin and End events in the merged sequence.
    Assumes the last event in the sequence is the most recently added Begin or End.
    
    The function:
    1. For End events: Marks them as potentially optional
    2. For Begin events: Handles potential overlapping
    
    Args:
        mergedSequence (list[LinearEvent]): The sequence being merged (modified in-place)
        
    Raises:
        Exception: If the last event is not a LinearBorder
    """
    # Récupérer la dernière extrémitée ajoutée
    border = mergedSequence[-1]
    if isinstance(border, LinearEnd):
        # on se sert de l'attribut "optionnel" d'une séquence End pour coder le fait que cette séquence est potentiellement optionnelle jusqu'à preuve du contraire (si elle ne contient aucune trace alignée). Cette astuce sera aussi utilisée pour déterminer si un Call doit être mis en option sur un changement de ligne ou de colonne (pas la diagonale) en effet si le End de la séquence mère est tagué Optionnel alors il n'est pas nécessaire de noter les Call enfants comme optionnels.
        # Donc, par défaut, on tague toutes les Séquences End comme optionnelle. Si ensuite en construisant la fusion on trouve des traces alignées, on annulera cette mise en option.
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
    """
    Merges two linearized sequences using a transformation matrix.

    This function performs a bottom-up traversal of the transformation matrix to merge
    sequences s1 and s2. The merge process follows these rules:
    1. For first row/column: Take events from the remaining sequence
    2. For Call vs Call:
       - If equal and diagonal cost is minimal: Take diagonal (marked as 'd')
       - If vertical cost is minimal or equal with longer s1: Take from s1 (marked as 'l')
       - Otherwise: Take from s2 (marked as 'c')
    3. For Call vs Border or Border vs Call:
       - Take the minimal cost path, preferring the Border's direction if costs are equal
    4. For Border vs Border:
       - If same type and diagonal cost is minimal: Take diagonal
       - If vertical cost is minimal or equal with specific conditions: Take from s1
       - Otherwise: Take from s2

    Args:
        s1 (list[LinearEvent]): First linearized sequence to merge
        s2 (list[LinearEvent]): Second linearized sequence to merge
        transformationMatrix (list[list[int]]): Alignment matrix from computeTransformationMatrix

    Returns:
        list[LinearEvent]: Merged sequence (in reverse order, first event is the merge of
        the last events from s1 and s2)
    """
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
            # transformationMatrix contient une ligne et une colonne de plus que s1 et s2, d'où le -1
            mergedEvent = copy.deepcopy(s2[c-1] if l == 0 else s1[l-1]) 
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
                if endPos != -1:
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
        # Gestion de l'ajoute d'un bord
        if mergedEvent != None and isinstance(mergedEvent, LinearBorder):
            manageBorder(mergedSequence)
    return mergedSequence

# Déterminer les options en fonction des orientations prises et des chevauchements détectés
#
# :param mergedSequence: la séquence fusionnée à adapter en fonction des enchainements de Begin et End et de leur orientation (Cette liste est inversé, le premier élément de la liste doit être le plus ancien).
# :return: un couple contenant en premier le nombre d'option définit lors de ce merge et en second le nombre d'alignement (nbOpt, nbAlign)
def updateOptions(mergedSequence:list[LinearEvent]) -> tuple[int, int]:
    """
    Updates event options based on orientations and overlaps.
    
    Determines which events should be marked as optional based on:
    1. Event orientation
    2. Sequence containment
    3. Sequence overlapping
    
    Args:
        mergedSequence (list[LinearEvent]): The sequence to update
        
    Returns:
        tuple[int, int]: (number of options set, number of alignments)
    """
    nbOpt:int = 0
    nbAlign:int = 0
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
                # Ne comptabiliser la trace comme optionnelle que qi elle ne l'était pas déjà
                if not event.opt:
                    event.opt = True
                    nbOpt += 1
            elif (event.orientation == "d"):
                nbAlign += 1
    return (nbOpt, nbAlign)

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
# :return: la nouvelle un tuple contenant en premier la séquence créée résultante de la fusion de s1 et s2, en second le nombre d'option définit lors de cette fusion et en troisème le nombre d'alignements
def mergeLinearSequences(s1:list[LinearEvent], s2:list[LinearEvent]) -> LinearEventWithStats:
    """
    Merges two linearized sequences into a new generalized sequence.
    
    Creates a new sequence that represents the most general form combining both
    input sequences. Handles special cases like:
    1. [AB[C]] and [[A]BC] => [[A]B[C]]
    2. A[C] and AB => A[*C]B
    3. A[BC] and [AB]C => [*A[B]*C]
    4. A[B] and [AB] => [A[B]]
    5. [A]B and [AB] => [[A]B]
    
    Args:
        s1 (list[LinearEvent]): First sequence to merge
        s2 (list[LinearEvent]): Second sequence to merge
        
    Returns:
        LinearEventWithStats: Merged sequence with statistics about options and alignments
    """
    mergedSequence:list[LinearEvent] = []

    transformationMatrix:list[list[int]] = computeTransformationMatrix(s1, s2)

    # Construction de la fusion entre s1 et s2 en prenant en compte les chevauchements de Séquence
    mergedSequence:list[LinearEvent] = computeMergedSequence(s1, s2, transformationMatrix)

    # Déterminer les options en fonction des orientations prises et des chevauchements détectés
    statsMerge:tuple[int, int] = updateOptions(mergedSequence)

    # On met le vecteur de fusion dans le bon sens
    mergedSequence.reverse()

    result:LinearEventWithStats = LinearEventWithStats()
    result.update(mergedSequence, statsMerge[0], statsMerge[1]-1) # -1 sur le compteur d'alignement pour ne pas comptabiliser le merge du premier Begin qui sera toujours présent
    return result