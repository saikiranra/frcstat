import frcstat as frc
from collections import defaultdict
from tqdm import tqdm

'''
For an event, this program will make a CSV of all the awards the teams
and their highest OPRS from all the events that season
'''

a = frc.Event("2016new")
teamAwards = {}
teamBestOPR = defaultdict(lambda : -1000000)
savedOPRS = {}

for t in tqdm(a.getTeamList()):
    fteam = frc.Team(t)
    teamAwards[t] = len(fteam.getAwardsByYear(2016))
    fevents = fteam.getEventsByYear(2016)
    for event in fevents:
        if event["week"] != None:
            if event["key"] not in savedOPRS:
                fevent = frc.Event(event["key"])
                savedOPRS[event["key"]] = fevent.scoreMetricFromPattern()
            if savedOPRS[event["key"]]["{}1".format(t)] > teamBestOPR[t]:
                teamBestOPR[t] = savedOPRS[event["key"]]["{}1".format(t)]

with open("awardAndOPR.csv" , "w") as fp:
    fp.write("Team,Awards,OPR\n")
    for t in a.getTeamList():
        fp.write("{},{},{}\n".format(t , str(teamAwards[t]) , str(teamBestOPR[t])))
            
                        
