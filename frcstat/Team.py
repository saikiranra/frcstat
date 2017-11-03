_Singleton_TBA_Client = None

class Team:
    def __init__(self , number , localDataOnly = False):
        """
            number - Team Number
            localDataOnly - Set True if offline and know you have all the data cached
        """
        self.number = number
        self.teamCode = "frc{}".format(str(number))
        self.validityFile = str(number) + "-valid"
        self.loadData(localDataOnly)

    def loadData(self , localDataOnly):
        """
            self.teamData
            self.teamAwards
            self.teamEvents
        """
        if localDataOnly:
            teamDataName = "{}-data".format(self.teamCode)
            self.teamData = _Singleton_TBA_Client.readTeamData(teamDataName)
            
            teamEventName = "{}-events".format(self.teamCode)
            self.eventData = _Singleton_TBA_Client.readTeamData(teamEventName)
            
            teamAwardName = "{}-events".format(self.teamCode)
            self.awardData = _Singleton_TBA_Client.readTeamData(teamAwardName)
            return 
            
        #First get modified data to check if update needed
        validityData = _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readTeamData(self.validityFile) , lambda:None)
        
        #Team Data Requests
        teamDataName = "{}-data".format(self.teamCode) #common name
        teamDataRequest = _Singleton_TBA_Client.makeRequest("team/{}".format(self.teamCode) , validityData[teamDataName])
        self.teamData = None
        if teamDataRequest == None: #Use saved values
            self.teamData = _Singleton_TBA_Client.readTeamData(teamDataName)
        else: #Use values from server
            self.teamData = teamDataRequest[0] #Assign data to member object
            validityData[teamDataName] = teamDataRequest[1] #Write the If-Modified-Since header to our validity data
            _Singleton_TBA_Client.writeTeamData(teamDataName , self.teamData) #Write member object data to file
            
            
        #Team Events Requests
        teamEventName = "{}-events".format(self.teamCode) #common name
        teamEventRequest = _Singleton_TBA_Client.makeRequest("team/{}/events".format(self.teamCode) , validityData[teamEventName])
        self.eventData = None
        if teamEventRequest == None: #Use saved values
            self.eventData = _Singleton_TBA_Client.readTeamData(teamEventName)
        else: #Use values from server
            self.eventData = teamEventRequest[0] #Assign data to member object
            validityData[teamEventName] = teamEventRequest[1] #Write the If-Modified-Since header to our validity data
            _Singleton_TBA_Client.writeTeamData(teamEventName , self.eventData) #Write member object data to file
            
            
        #Team Awads Requests
        teamAwardName = "{}-events".format(self.teamCode) #common name
        teamAwardRequest = _Singleton_TBA_Client.makeRequest("team/{}/awards".format(self.teamCode) , validityData[teamAwardName])
        self.awardData = None
        if teamAwardRequest == None: #Use saved values
            self.awardData = _Singleton_TBA_Client.readTeamData(teamAwardName)
        else: #Use values from server
            self.awardData = teamAwardRequest[0] #Assign data to member object
            validityData[teamAwardName] = teamAwardRequest[1] #Write the If-Modified-Since header to our validity data
            _Singleton_TBA_Client.writeTeamData(teamAwardName , self.awardData) #Write member object data to file
        
            
        _Singleton_TBA_Client.writeTeamData(self.validityFile , validityData) #Write validity object to file   

def _Team_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client