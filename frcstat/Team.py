import time
from collections import defaultdict
from copy import copy
from .ObjectShare import ObjectShare

_Singleton_TBA_Client = None

class Team:
    def __init__(self, number, cacheRefreshAggression = 1):
        '''
            Data Loaded from TBA
                self.teamData
                self.eventData
                self.awardData
                self.districtData
        '''
        if type(number) == str:
            self.number = int(float(number.replace("frc", "")))
        else:
            self.number = number
        self.teamCode = "frc{}".format(str(self.number))
        self.validityFile = str(self.number) + "-valid"
        self.cacheRefreshAggression = cacheRefreshAggression
        #self.loadData()
        self.teamData = None
        self.eventData = None
        self.awardData = None
        self.districtData = None

        self.getElimEventWins = None

        self._old_validity_data = None

    def getTeamData(self):
        if not self.teamData:
            self.loadTeamData()
        return self.teamData

    def getEventData(self):
        if not self.eventData:
            self.loadEventData()
        return self.eventData

    def getAwardData(self):
        if not self.awardData:
            self.loadAwardData()
        return self.awardData

    def getDistrictData(self):
        if not self.districtData:
            self.loadDistrictData()
        return self.districtData

    def getAwardsByYear(self , year):
        out = []
        for award in self.getAwardData():
            if year == award["year"]:
                out.append(award)
        return out
        
    def getEventsByYear(self, year):
        out = []
        for event in self.getEventData():
            if year == event["year"]:
                out.append(event)
        out.sort(key = lambda x: time.strptime(x["start_date"], "%Y-%m-%d"))
        return out
        
    def getElimEventWinsByYear(self , year):
        import frcstat.Event as Event
        if not self.getElimEventWins:
            self.getElimEventWins = {}
        if year in self.getElimEventWins:
            return self.getElimEventWins[year]
        self.getElimEventWins[year] = {}
        for event in self.getEventData():
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
        districtData = self.getDistrictData()
        if not districtData:
            return None

        start = None
        end = None
        for i in range(len(districtData)):
            if i == 0:
                start = districtData[i]["year"]
                end = districtData[i]["year"]

            else:
                start = min(start, districtData[i]["year"])
                end = max(end, districtData[i]["year"])
        return start, end

    def getDistrictAtYear(self, year):
        districtData = self.getDistrictData()
        if not districtData:
            return None

        for dm in districtData:
            if dm["year"] == year:
                return dm

        return None

    def readValidityData(self):
        self._old_validity_data = _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readTeamData(self.validityFile) , lambda:None)
        return copy(self._old_validity_data)

    def writeValidityData(self, validityData):
        if self._old_validity_data == validityData:
            return True
        return _Singleton_TBA_Client.writeTeamData(self.validityFile, validityData)  # Write validity object to file

    def loadData(self):
        """
            
        """

        self.loadTeamData()
        self.loadEventData()
        self.loadAwardData()
        self.loadDistrictData()

    def loadTeamData(self):
        validityData = self.readValidityData()

        teamDataName = "{}-data".format(self.teamCode)
        teamDataRequest = r"team/{}".format(self.teamCode)
        self.teamData = _Singleton_TBA_Client.makeSmartRequest(teamDataName, teamDataRequest, validityData, self,
                                                               self.cacheRefreshAggression)

        self.writeValidityData(validityData)

    def loadEventData(self):
        validityData = self.readValidityData()

        teamEventName = "{}-events".format(self.teamCode)  # common name
        teamEventRequest = r"team/{}/events".format(self.teamCode)
        self.eventData = _Singleton_TBA_Client.makeSmartRequest(teamEventName, teamEventRequest, validityData, self,
                                                                self.cacheRefreshAggression)

        self.writeValidityData(validityData)

    def loadAwardData(self):
        validityData = self.readValidityData()
        teamAwardName = "{}-awards".format(self.teamCode)  # common name
        teamAwardRequest = r"team/{}/awards".format(self.teamCode)
        self.awardData = _Singleton_TBA_Client.makeSmartRequest(teamAwardName, teamAwardRequest, validityData, self,
                                                                self.cacheRefreshAggression)
        self.writeValidityData(validityData)


    def loadDistrictData(self):
        validityData = self.readValidityData()
        districtDataName = "{}-districts".format(self.teamCode)  # common name
        districtDataRequest = r"team/{}/districts".format(self.teamCode)
        self.districtData = _Singleton_TBA_Client.makeSmartRequest(districtDataName, districtDataRequest, validityData,
                                                                   self, self.cacheRefreshAggression)
        self.writeValidityData(validityData)



_teamShare = ObjectShare(Team)


def getTeam(teamNumber, cacheRefreshAggression = 1):
    return _teamShare.get(teamNumber, cacheRefreshAggression)


def _Team_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client
