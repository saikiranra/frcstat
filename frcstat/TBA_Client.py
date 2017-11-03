import numpy as np
import os
import json
import urllib.parse
import urllib.request
import requests
from collections import defaultdict
import datetime

from .API_Keys import API_Keys


class TBA_Client:
    def __init__(self , tbakey = None):
        self.saveDir = os.path.dirname(os.path.abspath(__file__))
        self.localDataDir = self.saveDir +r"/localData/"
        self.teamDir = self.localDataDir + r"teams/"
        self.eventDir = self.localDataDir + r"events/"
        self.seasonDir = self.localDataDir + "seasons/"
        
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

    def readSeasonData(self , file):
        """
            file - File name in season/ .json will be appended
        """
        out = None
        fname = self.seasonDir + file + ".json"
        if os.path.isfile(fname):
            with open(fname) as fp:
                out = json.loads(fp.read())
        return out
        
    def writeSeasonData(self , file , data):
        """
            file - File name in season/ .json will be appended
            data - Python data structure to be written to file (Will be converted to JSON object string)
        """
        success = False
        fname = self.seasonDir + file + ".json"
        with open(fname , 'w') as fp:
            fp.write(json.dumps(data))
            success = True
        return success
        
    def readTeamData(self , file):
        """
            file - File name in season/ .json will be appended
        """
        out = None
        fname = self.teamDir + file + ".json"
        if os.path.isfile(fname):
            with open(fname) as fp:
                out = json.loads(fp.read())
        return out
        
    def writeTeamData(self , file , data):
        """
            file - File name in season/ .json will be appended
            data - Python data structure to be written to file (Will be converted to JSON object string)
        """
        success = False
        fname = self.teamDir + file + ".json"
        with open(fname , 'w') as fp:
            fp.write(json.dumps(data))
            success = True
        return success
        
    def readEventData(self , file):
        """
            file - File name in season/ .json will be appended
        """
        out = None
        fname = self.eventDir + file + ".json"
        if os.path.isfile(fname):
            with open(fname) as fp:
                out = json.loads(fp.read())
        return out
        
    def writeEventData(self , file , data):
        """
            file - File name in season/ .json will be appended
            data - Python data structure to be written to file (Will be converted to JSON object string)
        """
        success = False
        fname = self.eventDir + file + ".json"
        with open(fname , 'w') as fp:
            fp.write(json.dumps(data))
            success = True
        return success
    
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
            raise("API Key Not Valid!")
        else:
            raise("Not valid status code!")

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
    
    
    
