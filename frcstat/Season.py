from collections import defaultdict

_Singleton_TBA_Client = None



class Season:
    def __init__(self , year , localDataOnly = False):
        """
            year - Season year
            localDataOnly - Set True if offline and know you have all the data cached
        """
        self.year = year
        self.validityFile = str(year) + "-valid"
        self.loadData(localDataOnly)
        


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
        
    def loadData(self , localDataOnly):
        if localDataOnly:
            eventObjName = "{}-events".format(str(self.year))
            self.events = _Singleton_TBA_Client.readSeasonData(eventObjName)
            return
            
        #First get modified data to check if update needed
        validityData = _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readSeasonData(self.validityFile) , lambda:None)
        
        #Events in a year requests
        eventObjName = "{}-events".format(str(self.year)) #common name
        eventRequest = _Singleton_TBA_Client.makeRequest("events/{}".format(str(self.year)) , validityData[eventObjName])
        self.events = None
        if eventRequest == None: #Use saved values
            self.events = _Singleton_TBA_Client.readSeasonData(eventObjName)
        else: #Use values from server
            self.events = eventRequest[0] #Assign data to member object
            validityData[eventObjName] = eventRequest[1] #Write the If-Modified-Since header to our validity data
            _Singleton_TBA_Client.writeSeasonData(eventObjName , self.events) #Write member object data to file
        
            
        _Singleton_TBA_Client.writeSeasonData(self.validityFile , validityData) #Write validity object to file
        
def _Season_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client


    
    
        
