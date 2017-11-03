_Singleton_TBA_Client = None

class Event:
    def __init__(self , code , localDataOnly = False):
        self.eventCode = code
        
        self.validityFile = code + "-valid"
        self.loadData(localDataOnly)
        
        
    def getCalculationPatterns(self):
        patterns = {}
        patterns["OPR"] = "BS = B11 + B21 + B31.RS = R11 + R21 + R31"
        patterns["EPR"] = "RS - BS = R11 + R21 + R31 + (-1)*B11 + (-1)*B21 + (-1)*B31.BS = B11 + B21 + B31.RS = R11 + R21 + R31"
        patterns["GPR"] = "RS - BS = R11 + R21 + R31 + (-1)*B11 + (-1)*B21 + (-1)*B31"
        patterns["DPR"] = "BS = B11 + B21 + B31 + (-1)*R12 + (-1)*R22 + (-1)*R32.RS = R11 + R21 + R31 + (-1)*B12 + (-1)*B22 + (-1)*B32"
        return(patterns) 

    def loadData(self , localDataOnly):
        if localDataOnly:
            dataObjName = "{}-data".format(self.eventCode)
            self.eventData = _Singleton_TBA_Client.readEventData(dataObjName)
            
            matchObjName = "{}-matches".format(self.eventCode)
            self.matchData = _Singleton_TBA_Client.readEventData(matchObjName)
            return
            
        #First get modified data to check if update needed
        validityData = _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readEventData(self.validityFile) , lambda:None)
        
        #Event Data requests
        dataObjName = "{}-data".format(self.eventCode) #common name
        dataRequest = _Singleton_TBA_Client.makeRequest("event/{}".format(self.eventCode) , validityData[dataObjName])
        self.eventData = None
        if dataRequest == None: #Use saved values
            self.eventData = _Singleton_TBA_Client.readEventData(dataObjName)
        else: #Use values from server
            self.eventData = dataRequest[0] #Assign data to member object
            validityData[dataObjName] = dataRequest[1] #Write the If-Modified-Since header to our validity data
            _Singleton_TBA_Client.writeEventData(dataObjName , self.eventData) #Write member object data to file
            
        #Event Match requests
        matchObjName = "{}-matches".format(self.eventCode) #common name
        matchRequest = _Singleton_TBA_Client.makeRequest("event/{}/matches".format(self.eventCode) , validityData[matchObjName])
        self.matchData = None
        if matchRequest == None: #Use saved values
            self.matchData = _Singleton_TBA_Client.readEventData(matchObjName)
        else: #Use values from server
            self.matchData = matchRequest[0] #Assign data to member object
            validityData[matchObjName] = matchRequest[1] #Write the If-Modified-Since header to our validity data
            _Singleton_TBA_Client.writeEventData(matchObjName , self.matchData) #Write member object data to file
        
            
        _Singleton_TBA_Client.writeEventData(self.validityFile , validityData) #Write validity object to file
        
    def getTeamList(self):
        return self.teamList
        
def _Event_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client
