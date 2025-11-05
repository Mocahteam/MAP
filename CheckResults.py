import json

files = ["m1", "m2", "m3", "m4", "m5", "m6", "m7", "m81", "m82", "m11"]#, "m9"]
#files = ["m2"]
#files = ["m81"]
mainDir = "./dataset1"

for fileName in files:
    # Ouvrir et charger le fichier JSON
    with open(mainDir+"/solutionsExplored/dichotomous_"+fileName+".txt", 'r', encoding='utf-8') as fichier:
        donnees = json.load(fichier)
    maxScore:float = 0
    betterComp:str = ""
    for key, set in donnees.items():
        for comp in set:
            if comp[1] > maxScore:
                maxScore = comp[1]
                betterComp = comp[0]
            if comp[1] == maxScore and comp[0] not in betterComp:
                betterComp = betterComp + "##" + comp[0]
                
    # Afficher les données chargées
    print(fileName+": "+str(betterComp)+" "+str(maxScore))