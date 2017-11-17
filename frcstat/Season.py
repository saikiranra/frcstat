from collections import defaultdict

_Singleton_TBA_Client = None



class Season:
    def __init__(self , year , cacheRefreshAggression = 1):
        '''
            Data Loaded from TBA
                self.events
        '''
        self.year = year
        self.validityFile = str(year) + "-valid"
        self.loadData(cacheRefreshAggression)
        


    def getAllEvents(self):
        return self.events

    def getOffseasonEvents(self):
        out = []
        for event in self.events:
            if event["event_type_string"] == "Offseason":
                out.append(event)
        return out
        
    def getOfficialEvents(self):
        out = []
        for event in self.events:
            if event["event_type_string"] != "Offseason":
                out.append(event)
        return out
        
    def getLowLevelEvents(self):
        """
            Low Level Events defined as regional and district events
        """
        out = []
        for event in self.events:
            if event["event_type_string"] == "Regional" or event["event_type_string"] == "District":
                out.append(event)
        return out
        
    def getPreseasonEvents(self):
        out = []
        for event in self.events:
            if event["event_type_string"] == "Preseason":
                out.append(event)
        return out
        
    def getDistrictChampionshipEvents(self):
        out = []
        for event in self.events:
            if event["event_type_string"] == "District Championship":
                out.append(event)
        return out
    
    def getChampionshipEvents(self):
        out = []
        for event in self.events:
            if event["event_type_string"] == "Championship" or event["event_type_string"] == "Championship Finals":
                out.append(event)
        return out

    def getComponentOPRLabels(self):
        pass
        
    def loadData(self , cacheRefreshAggression):
        validityData = _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readSeasonData(self.validityFile) , lambda:None)
        
        eventObjName = "{}-data".format(self.eventCode)
        eventRequest = "event/{}".format(self.eventCode)
        self.events = _Singleton_TBA_Client.makeSmartRequest(eventObjName , eventRequest , validityData , self , cacheRefreshAggression)
            
        _Singleton_TBA_Client.writeSeasonData(self.validityFile , validityData) #Write validity object to file
        
def _Season_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client


    
    
        
