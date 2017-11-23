_Singleton_TBA_Client = None

class Team:
    def __init__(self , number , cacheRefreshAggression = 1):
        '''
            Data Loaded from TBA
                self.teamData
                self.eventData
                self.awardData
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
        return out

        
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
            
        _Singleton_TBA_Client.writeTeamData(self.validityFile , validityData) #Write validity object to file   

def _Team_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client