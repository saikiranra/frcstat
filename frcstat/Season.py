from collections import defaultdict
from copy import copy
from .ObjectShare import ObjectShare

_Singleton_TBA_Client = None


class Season:
    def __init__(self , year , cacheRefreshAggression = 1):
        '''
            Data Loaded from TBA
                self.events
        '''
        self.year = year
        self.validityFile = str(year) + "-valid"
        self._old_validity_data = None
        self.loadData(cacheRefreshAggression)
        


    def getAllEvents(self):
        return self.events
    
    def offSeasonEvents(self):
        '''
        Generator
        '''
        for event in self.events:
            if event["event_type"] == 99:
                yield event
        
    def getOffseasonEvents(self):
        return [x for x in self.offSeasonEvents()]
        
    def officialEvents(self):
        for event in self.events:
            if event["event_type"] in [0 , 1  , 2 , 3 , 4 , 5 , 6]:
                yield event
    
    def getOfficialEvents(self):
        return [x for x in self.officialEvents()]
        
    def oprableEvents(self):
        for event in self.events:
            if event["event_type"] in [0 , 1 , 2 , 3 , 5]:
                yield event
        
    def getLowLevelEvents(self):
        """
            Low Level Events defined as regional and district events
        """
        out = []
        for event in self.events:
            if event["event_type"] == 0 or event["event_type"] == 1:
                out.append(event)
        return out
        
    def getPreseasonEvents(self):
        out = []
        for event in self.events:
            if event["event_type"] == 100:
                out.append(event)
        return out
        
    def getDistrictChampionshipEvents(self):
        out = []
        for event in self.events:
            if event["event_type"] == 2:
                out.append(event)
        return out
    
    def getChampionshipEvents(self):
        out = []
        for event in self.events:
            if event["event_type"] in [3,4,6]:
                out.append(event)
        return out

    def getDivisionEvents(self):
        out = []
        for event in self.events:
            if event["event_type"] == 3:
                out.append(event)
        return out

    def getComponentOPRLabels(self):
        pass
        
    def loadData(self , cacheRefreshAggression):
        validityData = _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readSeasonData(self.validityFile) , lambda:None)
        self._old_validity_data = copy(validityData)
        
        eventObjName = "{}-data".format(str(self.year))
        eventRequest = "events/{}".format(str(self.year))
        self.events = _Singleton_TBA_Client.makeSmartRequest(eventObjName , eventRequest , validityData , self , cacheRefreshAggression)
            
        if self._old_validity_data != validityData:
            _Singleton_TBA_Client.writeSeasonData(self.validityFile , validityData) #Write validity object to file


_seasonShare = ObjectShare(Season)


def getSeason(year, cacheRefreshAggression = 1):
    return _seasonShare.get(year, cacheRefreshAggression)

def _Season_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client


    
    
        
