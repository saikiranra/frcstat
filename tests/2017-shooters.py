import frcstat as frc
import time
from scipy import stats
from collections import defaultdict
from tqdm import tqdm


teamDict = defaultdict(lambda : [0 , 0])

season = frc.Season(2017)

for ev in tqdm(season.getOfficialEvents()):
    event = frc.Event(ev["key"])
    try:
        for t in event.teamList:
            if event.coprs == None:
                event.coprs = event.getComponentOPRS()
            if event.coprs["autoFuelPoints"][event.lookup[t]] > teamDict[t][0]:
                teamDict[t][0] = event.coprs["autoFuelPoints"][event.lookup[t]]
            if event.coprs["teleopFuelPoints"][event.lookup[t]] > teamDict[t][1]:
                teamDict[t][1] = event.coprs["teleopFuelPoints"][event.lookup[t]]
    except:
        print(ev["key"])
        

with open("2017shooters.csv" , 'w') as fp:
    for t in teamDict:
        fp.write("{},{},{}\n".format(t , str(teamDict[t][0]) , str(teamDict[t][1])))
        
