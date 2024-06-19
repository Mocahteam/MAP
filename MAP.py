import time
from Episode import Episode
from Event import Call, Event
from PTKE import PTKE

# MAP => Mining Algorithm Patterns
def MAP (event_list:list[Event]):
    current_time:float = time.time()
    while (True):
        ptke:PTKE = PTKE()
        bestEpisode:Episode = ptke.getBestEpisode(event_list)
        print(str(bestEpisode))
        break
    print ("Temps de calcul : "+str(time.time()-current_time))

# init constant values
Episode.PROXIMITY_BALANCING = 0.5
Episode.WEIGHT_SUPPORT = 0.5
PTKE.K = 10
PTKE.QCSP_ALPHA = 2

test:str = "AAABAAABBAAA"
# Transformation du string en une liste d'évènement
eventList:list[Event] = []
for char in test:
    eventList.append(Call(char))
MAP(eventList)