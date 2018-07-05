import frcstat as frc

AGGRESSION = 0

def generateReport(teams):
    with open("index.html" , "w") as fp:
        for team in teams:
            teamObj = frc.Team(team , AGGRESSION)
            fp.write("<h1>{} - {} Data</h1>".format(str(team) , teamObj.teamData["nickname"]))
            fp.write("<h2>Awards</h2>")
            fp.write(getAwardTable(teamObj))
            fp.write("<br>")


def getAwardTable(teamObj):
    out = "<table><tr><th>Year</th><th>Event</th><th>Award</th></tr>"
    for event in teamObj.awardData:
        out += "<tr>"
        out += "<th>"+str(event["year"])+"</th>"
        out += "<th>"+event["event_key"]+"</th>"
        out += "<th>"+event["name"]+"</th>"
        out += "</tr>"
    out += "</table>"
    return out


def getPerformanceTable(teamObj):
        pass
