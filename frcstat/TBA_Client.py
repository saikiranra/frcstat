import numpy as np
import os
import json
import urllib.parse
import urllib.request
import requests
from collections import defaultdict
import datetime

from .API_Keys import API_Keys
from .Event import Event
from .Season import Season
from .Team import Team

class TBA_Client:
    def __init__(self , tbakey = None):
        self.saveDir = os.path.dirname(os.path.abspath(__file__))
        self.localDataDir = os.path.join(self.saveDir , "localData")
        self.teamDir   = os.path.join(self.localDataDir , "teams")
        self.eventDir  = os.path.join(self.localDataDir , "events")
        self.seasonDir = os.path.join(self.localDataDir , "seasons")
        
        self.keys = API_Keys(tbakey)
        self.apiURL = r"https://www.thebluealliance.com/api/v3/"
        self.setup()

    def setup(self):
        """
        Sets up directory paths for storing local data.
        """
        if not os.path.isdir(self.localDataDir):
            os.makedirs(self.localDataDir)
        if not os.path.isdir(self.teamDir):
            os.makedirs(self.teamDir)
        if not os.path.isdir(self.eventDir):
            os.makedirs(self.eventDir)
        if not os.path.isdir(self.seasonDir):
            os.makedirs(self.seasonDir)
            
    def dictToDefaultDict(self , obj , callable):
        out = defaultdict(callable)
        if obj == None:
            return out
        for k in obj.keys():
            out[k] = obj[k]
        return out

    def readData(self , fname):
        out = None
        if os.path.isfile(fname):
            with open(fname) as fp:
                try:
                    out = json.loads(fp.read())
                except json.decoder.JSONDecodeError:
                    if __debug__:
                        print(fname + " failed JSON decoding.")
        return out
    
    def readSeasonData(self , file):
        """
            file - File name in season/ .json will be appended
        """
        fname = os.path.join(self.seasonDir , file + ".json")
        return self.readData(fname)
        
    def writeSeasonData(self , file , data):
        """
            file - File name in season/ .json will be appended
            data - Python data structure to be written to file (Will be converted to JSON object string)
        """
        success = False
        fname = os.path.join(self.seasonDir , file + ".json")
        with open(fname , 'w') as fp:
            fp.write(json.dumps(data))
            success = True
        return success
        
    def readTeamData(self , file):
        """
            file - File name in season/ .json will be appended
        """
        fname = os.path.join(self.teamDir , file + ".json")
        return self.readData(fname)
        
    def writeTeamData(self , file , data):
        """
            file - File name in season/ .json will be appended
            data - Python data structure to be written to file (Will be converted to JSON object string)
        """
        success = False
        fname = os.path.join(self.teamDir , file + ".json")
        with open(fname , 'w') as fp:
            fp.write(json.dumps(data))
            success = True
        return success
        
    def readEventData(self , file):
        """
            file - File name in season/ .json will be appended
        """
        fname = os.path.join(self.eventDir , file + ".json")
        return self.readData(fname)
        
    def writeEventData(self , file , data):
        """
            file - File name in season/ .json will be appended
            data - Python data structure to be written to file (Will be converted to JSON object string)
        """
        success = False
        fname = os.path.join(self.eventDir , file + ".json")
        with open(fname , 'w') as fp:
            fp.write(json.dumps(data))
            success = True
        return success
        
    def makeSmartRequest(self , dataName : str , request : str , validityData : dict , requestingObject : type , cacheRefreshAggression : int , dataMutator = None):
        '''
            dataName - name of the request. Saves data in the name of this prefix
            request - request to make to tba
            validityData - dict that will be updated with the new refresh tag
            requestingObject - object that is making the request
            cacheRefreshAggression - 0 only saved , 1 check file , 2 check request
            dataMutator - mutates the return data for use, optional
        '''
        out = None
        if cacheRefreshAggression == 0 or cacheRefreshAggression == 1:
            #Read from file
            if type(requestingObject) == Event:
                out = self.readEventData(dataName)
            elif type(requestingObject) == Team:
                out = self.readTeamData(dataName)
            elif type(requestingObject) == Season:
                out = self.readSeasonData(dataName)
            #If 0, return
            if cacheRefreshAggression == 0:
                return out
            if out != None:
                return out
        
        request = self.makeRequest(request , validityData[dataName])
        rawData = None
        if request == None: #Use saved values
            if type(requestingObject) == Event:
                out = self.readEventData(dataName)
            elif type(requestingObject) == Team:
                out = self.readTeamData(dataName)
            elif type(requestingObject) == Season:
                out = self.readSeasonData(dataName)
        else: #use values from server
            if dataMutator == None:
                out = request[0]
            else:
                out = dataMutator(request[0])
            validityData[dataName] = request[1] #Write the If-Modified-Since header to validation file
            
            if type(requestingObject) == Event:
                self.writeEventData(dataName , out)
            elif type(requestingObject) == Team:
                self.writeTeamData(dataName , out)
            elif type(requestingObject) == Season:
                self.writeSeasonData(dataName , out)
        return out
            
    def makeRequest(self , requestTag : str , refreshCode : str = None):
        '''
            requestTag - request string that will be sent to the API
            refreshCode - If it exists, this is the "Last-Modified" header value recived last time the request was made
            
            out
                type(list) - [Json of the request data , new Last-Modified value to save]
                type(None) - Use cached values
        '''
        req = None
        url = self.apiURL + requestTag
        if refreshCode == None:
            req = requests.get(url , headers = {"X-TBA-Auth-Key":self.keys.getTBAKey()})
        else:
            req = requests.get(url , headers = {"X-TBA-Auth-Key":self.keys.getTBAKey() , "If-Modified-Since":refreshCode})
        #print("{} {}".format(refreshCode , req.headers["Last-Modified"]))
        if req.status_code == 200:
            return [json.loads(req.text) , req.headers["Last-Modified"]]
        if req.status_code == 304:
            return None
        if req.status_code == 401:
            raise(Exception("API Key Not Valid!"))
        else:
            raise(Exception("Not valid status code! With Request {}".format(requestTag)))

    def URLToJson(self , url: str) -> 'json':
        return(json.loads(requests.get(url).text))

    def storeData(self):
        """
        How data will be accessed

        When initializing teams, we will mostly care about historical data
        What events, what awards, what years, so on
        Need method to maybe store metrics we find useful? 
        
        """
        pass
    
    
    
