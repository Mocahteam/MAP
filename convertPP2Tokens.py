import os


associations = {
    "PP_Open": "A",
    "PP_Close": "Z",
    "PP_IsGameOver": "B",
    "PP_IsGamePaused": "C",
    "PP_GetMapSize": "D",
    "PP_GetStartPosition": "E",
    "PP_GetNumSpecialAreas": "F",
    "PP_GetSpecialAreaPosition": "G",
    "PP_GetResource": "H",
    "PP_GetNumUnits": "I",
    "PP_GetUnitAt": "J",
    "PP_Unit_GetCoalition": "K",
    "PP_Unit_GetType": "L",
    "PP_Unit_GetPosition": "M",
    "PP_Unit_GetHealth": "N",
    "PP_Unit_GetMaxHealth": "O",
    "PP_Unit_GetGroup": "P",
    "PP_Unit_SetGroup": "Q",
    "PP_Unit_GetPendingCommands": "R",
    "PP_Unit_ActionOnUnit": "S",
    "PP_Unit_ActionOnPosition": "T",
    "PP_Unit_UntargetedAction": "U",
    "Sequence()": "[",
    "EndSequence": "]",
}

def process_file(input_file: str, output_file: str):
    # Ouvrir le fichier source en lecture
    with open(input_file, 'r') as infile, open(output_file, 'w+') as outfile:
        # Lire chaque ligne du fichier source
        for line in infile:
            # Vérifier chaque clé dans les associations
            for key, symbol in associations.items():
                # Si la ligne contient la clé, écrire le symbole dans le fichier de destination
                if key in line:
                    outfile.write(symbol)
                    if line.startswith('*'):
                        outfile.write('*')
                    break  # On peut sortir de la boucle dès qu'on trouve une correspondance


for root, dirs, files in os.walk("../ProgAndPlay/VersionLIP6-GIT/ProgAndPlay/pp/tracesV2/example/solutions"):
    for file in files:
        if file.endswith(".log"):
            process_file(root+"/"+file, "./example/solutions/"+file)
    break
