import sys
from Event import Call
from MAP import MAP
from PTKE import PTKE
from Episode import NonOverlappedEpisode

# La garde __main__ est OBLIGATOIRE : PTKE utilise multiprocessing.Pool,
# ce qui plante sous Windows et macOS sans elle.
if __name__ == "__main__":
    trace = sys.argv[1]                                   # ex : "PYPYPYPYPUY"
    PTKE.GAP_RATIO = float(sys.argv[2])                   # gr ∈ [0 ; 8]
    NonOverlappedEpisode.WEIGHT_SUPPORT = float(sys.argv[3])       # ws ∈ [0 ; 1]
    NonOverlappedEpisode.PROXIMITY_BALANCING = float(sys.argv[4])  # pb ∈ [0 ; 1]

    # Une lettre = un évènement
    compressions = MAP([Call(c) for c in trace])
    print()

    # Affiche chaque compression candidate : <compression> <OptCount> <AlignCount> <MergeCount>
    for c in compressions.set:
        print(c)

    # Optionnel : comparer avec une solution attendue
    if len(sys.argv) > 5:
        code = compressions.getCode(sys.argv[5])
        print({1: "Solution trouvée", 2: "Solution non trouvée", -1: "Temps dépassé"}[code])
