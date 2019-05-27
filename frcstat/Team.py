import time
from .ObjectShare import ObjectShare

_Singleton_TBA_Client = None

class Team:
    def __init__(self , number , cacheRefreshAggression = 1):
        '''
            Data Loaded from TBA
                self.teamData
                self.eventData
                self.awardData
                self.districtData
        '''
        if type(number) == str:
            self.number = int(float(number.replace("frc" , "")))
        else:
            self.number = number
        self.teamCode = "frc{}".format(str(self.number))
        self.validityFile = str(self.number) + "-valid"
        self.loadData(cacheRefreshAggression)
        
    def getAwardsByYear(self , year):
        out = []
        for award in self.awardData:
            if year == award["year"]:
                out.append(award)
        return out
        
    def getEventsByYear(self , year):
        out = []
        for event in self.eventData:
            if year == event["year"]:
                out.append(event)
        out.sort(key = lambda x: time.strptime(x["start_date"] , "%Y-%m-%d"))
        return out
        
    def getElimEventWinsByYear(self , year):
        import frcstat.Event as Event
        if not hasattr(self , "getElimEventWins"):
            self.getElimEventWins = {}
        if year in self.getElimEventWins:
            return self.getElimEventWins[year]
        self.getElimEventWins[year] = {}
        for event in self.eventData:
            if year == event["year"]:
                ev = Event(event["key"])
                teamMatches = ev.getTeamMatches(self.teamCode)
                wins = 0
                for matchKey in teamMatches.keys():
                    if teamMatches[matchKey]["comp_level"] != "qm":
                        color = "blue"
                        if self.teamCode in teamMatches[matchKey]["alliances"]["red"]["team_keys"]:
                            color = "red"
                        if color == teamMatches[matchKey]["winning_alliance"]:
                            wins += 1
                self.getElimEventWins[year][event["key"]] = wins
        return self.getElimEventWins[year]

    def getDistrictYears(self):
        """
        Returns tuple of start year and end year, unless no districts, which then None
        """
        if not self.districtData:
            return None

        start = None
        end = None
        for i in range(len(self.districtData)):
            if i == 0:
                start = self.districtData[i]["year"]
                end = self.districtData[i]["year"]

            else:
                start = min(start , self.districtData[i]["year"])
                end = max(end , self.districtData[i]["year"])
        return (start , end)

    def getDistrictAtYear(self , year):
        if not self.districtData:
            return None

        for dm in self.districtData:
            if dm["year"] == year:
                return dm

        return None

        
    def loadData(self , cacheRefreshAggression):
        """
            
        """
        
        #First get modified data to check if update needed
        validityData = _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readTeamData(self.validityFile) , lambda:None)
        
        teamDataName = "{}-data".format(self.teamCode)
        teamDataRequest = "team/{}".format(self.teamCode)
        self.teamData = _Singleton_TBA_Client.makeSmartRequest(teamDataName , teamDataRequest , validityData , self , cacheRefreshAggression)
        
        teamEventName = "{}-events".format(self.teamCode) #common name
        teamEventRequest = "team/{}/events".format(self.teamCode)
        self.eventData = _Singleton_TBA_Client.makeSmartRequest(teamEventName , teamEventRequest , validityData , self , cacheRefreshAggression)
        
        teamAwardName = "{}-awards".format(self.teamCode) #common name
        teamAwardRequest = "team/{}/awards".format(self.teamCode)
        self.awardData = _Singleton_TBA_Client.makeSmartRequest(teamAwardName , teamAwardRequest , validityData , self , cacheRefreshAggression)

        districtDataName = "{}-districts".format(self.teamCode) #common name
        districtDataRequest = "team/{}/districts".format(self.teamCode)
        self.districtData = _Singleton_TBA_Client.makeSmartRequest(districtDataName , districtDataRequest , validityData , self , cacheRefreshAggression)   
            
        _Singleton_TBA_Client.writeTeamData(self.validityFile , validityData) #Write validity object to file   


_teamShare = ObjectShare(Team)


def getTeam(teamNumber, cacheRefreshAggression = 1):
    return _teamShare.get(teamNumber, cacheRefreshAggression)


def _Team_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client
