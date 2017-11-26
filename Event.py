import re
import numpy as np
import scipy.linalg as lin
from collections import defaultdict

_Singleton_TBA_Client = None

class Event:
    def __init__(self , code , localDataOnly = 1):
        '''
            Data Loaded from TBA
                self.matchData
                self.teamList
                self.eventData
                
            Derived Data 
                self.lookup - dict where team key "frc330" maps to index used in other calculations
                self.oprs - array of oprs, where self.lookup gives us the index of a team to look at
                self.coprs - dict of arrays, where the key in the dict tells us what component opr we are looking at 
        '''
        self.eventCode = code
        
        self.validityFile = code + "-valid"
        self.loadData(localDataOnly)
        
        
    def getCalculationPatterns(self):
        patterns = {}
        patterns["OPR"] = "B11 + B21 + B31 = BS;R11 + R21 + R31 = RS"
        patterns["EPR"] = "R11 + R21 + R31 + (-1)*B11 + (-1)*B21 + (-1)*B31 = RS - BS;B11 + B21 + B31 = BS.R11 + R21 + R31 = RS"
        patterns["GPR"] = "R11 + R21 + R31 + (-1)*B11 + (-1)*B21 + (-1)*B31 = RS - BS"
        patterns["DPR"] = "B11 + B21 + B31 + (-1)*R12 + (-1)*R22 + (-1)*R32 = BS;R11 + R21 + R31 + (-1)*B12 + (-1)*B22 + (-1)*B32 = RS"
        return(patterns)
        
    def getMatchInformation(self , matchKey):
        """
            Examples for matchKey  
                qm53
                qm2
                f1m1
                qf2m3
        """
        return self.matchData[matchKey]
        
    def elimMatchGen(self):
        for m in self.matchData:
            if self.matchData[m]["comp_level"] != "qm":
                yield self.matchData[m]
    def qualsMatchGen(self):
        for m in self.matchData:
            if self.matchData[m]["comp_level"] == "qm":
                yield self.matchData[m]
        
    def flattenDictionary(self , inDict):
        """
            Returns a dictionary where inner dictionaries are flattened to be on the base level of the current dict
        """
        out = {}
        for k in inDict:
            if type(inDict[k]) == dict:
                inner = self.flattenDictionary(inDict[k])
                for ik in inner:
                    out[k+"_"+ik] = inner[ik]
            else:
                out[k] = inDict[k]
        return out
        
        
    def getValidPatternData(self):
        """
            Returns a list of valid keys that can be used in the scoreMetricFromPattern pattern for calculation.
        """
        keyToCheck = "qm1"
        match = self.getMatchInformation(keyToCheck)
        fmatch = self.flattenDictionary(match)
        return fmatch.keys()
        
    def getArrayOPRS(self):
        '''
            Fast solving for component OPRS using cholesky decomposition
            Minimal looping, hard coded incrementation 
            
            Returns array where teams are looked up by index
        '''
        lookupDict = self._getLookupDict()
        totalMatches = self.getQualMatchAmount()
        A = np.zeros((len(self.getTeamList()) , len(self.getTeamList())))
        B = np.zeros(len(self.getTeamList()))
        
        
        for m in self.matchData:
            if self.matchData[m]["comp_level"] == "qm":
                match = self.matchData[m]
                RS = match["alliances"]["red"]["score"]
                BS = match["alliances"]["blue"]["score"]
                if RS != -1 and BS != -1: #is valid match
                    R1I = lookupDict[match["alliances"]["red"]["team_keys"][0]]
                    R2I = lookupDict[match["alliances"]["red"]["team_keys"][1]]
                    R3I = lookupDict[match["alliances"]["red"]["team_keys"][2]]
                    B1I = lookupDict[match["alliances"]["blue"]["team_keys"][0]]
                    B2I = lookupDict[match["alliances"]["blue"]["team_keys"][1]]
                    B3I = lookupDict[match["alliances"]["blue"]["team_keys"][2]]
                   
                    A[R1I][R1I] += 1
                    A[R1I][R2I] += 1
                    A[R1I][R3I] += 1
                    A[R2I][R1I] += 1
                    A[R2I][R2I] += 1
                    A[R2I][R3I] += 1
                    A[R3I][R1I] += 1
                    A[R3I][R2I] += 1
                    A[R3I][R3I] += 1
                    
                    A[B1I][B1I] += 1
                    A[B1I][B2I] += 1
                    A[B1I][B3I] += 1
                    A[B2I][B1I] += 1
                    A[B2I][B2I] += 1
                    A[B2I][B3I] += 1
                    A[B3I][B1I] += 1
                    A[B3I][B2I] += 1
                    A[B3I][B3I] += 1

                    B[R1I] += RS
                    B[R2I] += RS
                    B[R3I] += RS
                    
                    B[B1I] += BS
                    B[B2I] += BS
                    B[B3I] += BS
        #return lin.cho_solve(lin.cho_factor(A) , B) #lin.cho_solve(lin.cho_factor(A , True , True , False) , B , False)
        try:
            return lin.solve(A , B)
        except:
            print("LEAST SQUARES SOLUTION USED.")
            #print(A)
            #print(B)
            #print(lin.lstsq(A , B))
            return lin.lstsq(A , B)[0]
        
    def getDictOPRS(self):
        lookupDict = self._getLookupDict()
        oprs = self.getArrayOPRS()
        out = {}
        for key in lookupDict:
            out[key] = oprs[lookupDict[key]]
            
        return out
        
    def _assocArrayToDict(self , arr):
        lookupDict = self._getLookupDict()
        out = {}
        for key in lookupDict:
            out[key] = arr[lookupDict[key]]
            
        return out
         
    def getComponentOPRS(self):
        lookupDict = self._getLookupDict()
        totalMatches = self.getQualMatchAmount()
        A = np.zeros((len(self.getTeamList()) , len(self.getTeamList())))
        BDict = defaultdict(lambda : np.zeros(len(self.getTeamList())))
        
        validKeys = []
        colors = ["red" , "blue"]
        
        for m in self.matchData:
            if self.matchData[m]["comp_level"] == "qm":
                match = self.matchData[m]
                RS = match["alliances"]["red"]["score"]
                BS = match["alliances"]["blue"]["score"]
                if RS != -1 and BS != -1: #is valid match
                    R1I = lookupDict[match["alliances"]["red"]["team_keys"][0]]
                    R2I = lookupDict[match["alliances"]["red"]["team_keys"][1]]
                    R3I = lookupDict[match["alliances"]["red"]["team_keys"][2]]
                    B1I = lookupDict[match["alliances"]["blue"]["team_keys"][0]]
                    B2I = lookupDict[match["alliances"]["blue"]["team_keys"][1]]
                    B3I = lookupDict[match["alliances"]["blue"]["team_keys"][2]]
                    
                    #Check what keys have associated numeric values
                    if len(validKeys) == 0:
                        for key in match["score_breakdown"]["red"]:
                            try:
                                value = float(match["score_breakdown"]["red"][key])
                                validKeys.append(key)
                            except ValueError:
                                pass
                                
                    for key in validKeys:
                        colorIs = [[R1I , R2I , R3I] , [B1I , B2I , B3I]]
                        for c in range(2): 
                            for i in colorIs[c]:
                                BDict[key][i] += match["score_breakdown"][colors[c]][key]
                   
                    A[R1I][R1I] += 1
                    A[R1I][R2I] += 1
                    A[R1I][R3I] += 1
                    A[R2I][R1I] += 1
                    A[R2I][R2I] += 1
                    A[R2I][R3I] += 1
                    A[R3I][R1I] += 1
                    A[R3I][R2I] += 1
                    A[R3I][R3I] += 1
                    
                    A[B1I][B1I] += 1
                    A[B1I][B2I] += 1
                    A[B1I][B3I] += 1
                    A[B2I][B1I] += 1
                    A[B2I][B2I] += 1
                    A[B2I][B3I] += 1
                    A[B3I][B1I] += 1
                    A[B3I][B2I] += 1
                    A[B3I][B3I] += 1

        out = {}
        factoredA = lin.cho_factor(A , True , True , False)
        for key in validKeys:
            out[key] = lin.cho_solve(np.copy(factoredA) , BDict[key] , False)
        return out
        
    def getQualMatchAmount(self):
        return self.qualMatchAmount
        
    def scoreMetricFromPattern(self , pattern = "B11 + B21 + B31 = BS;R11 + R21 + R31 = RS" , toMatch = 9999):
        """
            This allows us to plug in linear equations we might find interesting to play with. 
            These equations are made up of variables we can solve for and constants from each match's data
            
            Some examples of metrics can be found in getCalculationPatterns()
            
            Pattern are linear equations and have to be in the form of
                <linear combination we are solving for>=<system that evaluates to a constant>;<next linear combination>=<evaluation constant>
                
            We create x values we want to solve for as team variables with certain suffixes. 
                B1 , B2 , B3 , R1 , R2 , R3 are the base variable creation strings to be used
                This means that we can append any string suffix to the end to create a variable we will be returned out
                B11 , B12 , B1_OPR , R1_WOWZERS are all valid variables that can be used
                
            Linear Combination Example
                B1_OPR + B2_OPR + B3_OPR - R1_DPR - R2_DPR - R3_DPR
           
            Evaluatable Constant Example
                B1 - score_breakdown_blue_foulPoints 
                BS and RS can be used as the Blue Score value and Red Score Value respectively
                
            The way to see what variables are available to use for a certain event, run the function getValidPatternData().
                A list of valid constant variables are returned that can be used in calculations
        """
        varsPerTeam = 0
        splitPattern = pattern.split(";")
        suffixList = self._getPatternSuffixList(pattern)
        lookupDict = self._getLookupDict() #associates a team to an index for fast lookup
        suffixAmount = len(suffixList)
        splitPatternAmount = len(splitPattern)
        
        #Construct Numpy Arrays Ax = B
        #A is a len(suffixList) * len(teamList) by len(splitPattern) * len(matches) array - What we populate with _Pattern_Variable information
        #x is a vector of len(suffixList) * len(teamList) - What we are solving for 
        #B is a vector of len(splitPattern) * len(matches) - What we populate with score information and the whatnot 
        totalMatches = self.getQualMatchAmount()
        if totalMatches > toMatch:
            totalMatches = toMatch
        A = np.zeros((len(splitPattern) * totalMatches , suffixAmount * len(self.getTeamList())))
        B = np.zeros((len(splitPattern) * totalMatches))
        
        matchNum = 0
        sortedMatches = [self.matchData[m] for m in self.matchData]
        sortedMatches.sort(key = lambda x: float(x["match_number"]))
        
        for match in sortedMatches:
            if match["comp_level"] == "qm" and match["match_number"] < toMatch: #Only run on qm matches and matches under toMatch
                RS = match["alliances"]["red"]["score"]
                BS = match["alliances"]["blue"]["score"]
                if RS != -1 and BS != -1: #Is a valid match
                    matchTeams = {"B1" : match["alliances"]["blue"]["team_keys"][0] , "B2" : match["alliances"]["blue"]["team_keys"][1] , "B3" : match["alliances"]["blue"]["team_keys"][2], \
                    "R1" : match["alliances"]["red"]["team_keys"][0] , "R2" : match["alliances"]["red"]["team_keys"][1] , "R3" : match["alliances"]["red"]["team_keys"][2]}
                    #Create flattened dictionary to use for computations
                    matchFlat = self.flattenDictionary(match)
                    matchFlat["RS"] = RS
                    matchFlat["BS"] = BS
                    for col in ["B1" , "B2" , "B3" , "R1" , "R2" , "R3"]:
                        i = 0
                        for suff in suffixList:
                            matchFlat[col + suff] = _Pattern_Variable(col + suff , (lookupDict[matchTeams[col]] * suffixAmount) + i)
                            i += 1
                    #Run Patterns
                    i = 0
                    for indPat in splitPattern:
                        B[(matchNum * splitPatternAmount) + i] = self._decomposePattern(indPat , matchFlat)
                        for col in ["B1" , "B2" , "B3" , "R1" , "R2" , "R3"]:
                            for suff in suffixList:
                                A[(matchNum * splitPatternAmount) + i][matchFlat[col + suff].getIndex()] = matchFlat[col + suff].getFactor()
                                matchFlat[col + suff].resetFactor()
                        i += 1
                    #Modify Matricies    
                matchNum += 1
        AMP = np.linalg.pinv(A)
        X = (AMP.dot(B)).tolist()
        out = {}
        for t in lookupDict:
            for i in range(suffixAmount):
                out[str(t)+suffixList[i]] = X[(lookupDict[t] * suffixAmount) + i]
        return out
        
    def _decomposePattern(self , pattern , flattenedMatch):
        #print(pattern)
        splitPattern = pattern.split("=")
        eval(splitPattern[0] , flattenedMatch)
        #self.ld = (flattenedMatch["B11"].getFactor() , flattenedMatch["B21"].getFactor() ,  flattenedMatch["R11"].getFactor() ,  flattenedMatch["R21"].getFactor())
        return eval(splitPattern[1] , flattenedMatch)
        
    
    def _getPatternSuffixList(self , pattern):
        """
            Returns how many variables are needed to be stored per team.
        """
        colorKeys = "B1", "B2" , "B3" , "R1" , "R2" , "R3"
        suffixSet = set()
        for colorKey in colorKeys:
            expr = "{}(\w*)".format(colorKey)
            allSuff = re.findall(expr , pattern)
            for suff in allSuff:
                suffixSet.add(suff)
                
        return list(suffixSet)
                
        
    def _metricArrayToDict(self , metricArray):
        """
            Converts an array of values into a dictionary
            Where every index in the metricArray becomes associated with a team with the same index in teamList
        """
        if len(metricArray) != self.teamAmount:
            raise("metricArray not same size as teamList!")
        out = {}
        for i in range(self.teamAmount):
            out[self.teamList[i]] = metricArray[i]
        return out

    def _getLookupDict(self):
        """
            Returns a dictionary where team codes are linked to an array index
        """
        out = {}
        for i in range(self.teamAmount):
            out[self.teamList[i]] = i
        return out
        
        
    def loadData(self , cacheRefreshAggression):
        '''
            cacheRefreshAggression - [0,1,2]. 
                0 only uses saved data
                1 checks if saved data file exists, if not make a requests (checks cache validity through request)
                2 only makes new requests (checks cache validity through request)
            
            
        '''
        validityData = _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readEventData(self.validityFile) , lambda:None)
        
        dataObjName = "{}-data".format(self.eventCode)
        dataRequest = "event/{}".format(self.eventCode)
        self.eventData = _Singleton_TBA_Client.makeSmartRequest(dataObjName , dataRequest , validityData , self , cacheRefreshAggression)
        
        def matchDataMutator(md):
            out = {}
            for m in md:
                out[m["key"].replace(self.eventCode+"_" ,"")] = m
            return out
        
        matchObjName = "{}-matches".format(self.eventCode)
        matchRequest = "event/{}/matches".format(self.eventCode)
        self.matchData = _Singleton_TBA_Client.makeSmartRequest(matchObjName , matchRequest , validityData , self , cacheRefreshAggression , matchDataMutator)
        
        teamListObjName = "{}-teamlist".format(self.eventCode)
        teamListRequest = "event/{}/teams/keys".format(self.eventCode)
        self.teamList = _Singleton_TBA_Client.makeSmartRequest(teamListObjName , teamListRequest , validityData , self , cacheRefreshAggression)
        
        _Singleton_TBA_Client.writeEventData(self.validityFile , validityData)
        
        ###Derived Calculations###
        self.teamAmount = len(self.teamList)
        self.lookup = self._getLookupDict()
        self.qualMatchAmount = 0
        for mkey in self.matchData:
            m = self.matchData[mkey]
            if m["comp_level"] == "qm":
                self.qualMatchAmount += 1
                
        self.oprs = np.array(_Singleton_TBA_Client.readEventData("{}-oprs".format(self.eventCode)))
        if self.oprs.size <= 1:
            self.oprs = self.getArrayOPRS()
            _Singleton_TBA_Client.writeEventData("{}-oprs".format(self.eventCode) , self.oprs.tolist())
        #We can't get COPRS for old games
        try:
            self.coprs = np.array(_Singleton_TBA_Client.readEventData("{}-coprs".format(self.eventCode)))
            if  self.coprs.size <= 1:
                self.coprs = self.getComponentOPRS()
                _Singleton_TBA_Client.writeEventData("{}-coprs".format(self.eventCode) , self.coprs.tolist())
        except:
            pass
      
    def getTeamList(self):
        return self.teamList
        
class _Pattern_Variable:
    def __init__(self , name , arrayIndex):
        self.name  = name
        self.factor = 0
        self.index = arrayIndex
        
    def _initFactor(self):
        if self.factor == 0:
            self.factor = 1
        
    def __rmul__(self , other):
        self._initFactor()
        if type(other) == _Pattern_Variable:
            raise Exception("Pattern Variable not allowed to be multiplied with another Pattern Variable!")
        self.factor *= other
        return self
        
    def __mul__(self , other):
        self._initFactor()
        if type(other) == _Pattern_Variable:
            raise Exception("Pattern Variable not allowed to be multiplied with another Pattern Variable!")
        self.factor *= other
        return self

    def __div__(self , other):
        self._initFactor()
        if type(other) == _Pattern_Variable:
            raise Exception("Pattern Variable not allowed to be divided with another Pattern Variable!")
        self.factor /= other
        return self

    def __rdiv__(self , other):
        self._initFactor()
        if type(other) == _Pattern_Variable:
            raise Exception("Pattern Variable not allowed to be divided with another Pattern Variable!")
        #self.factor /= other
        return self

    def __add__(self , other):
        self._initFactor()
        if type(other) == _Pattern_Variable:
            other._initFactor()
        return self

    def __radd__(self , other):
        self._initFactor()
        if type(other) == _Pattern_Variable:
            other._initFactor()
        return self

    def __sub__(self , other):
        self._initFactor()
        if type(other) == _Pattern_Variable:
            other._initFactor()
        if type(other) == _Pattern_Variable:
            other *= -1
        return self

    def __rsub__(self , other):
        self._initFactor()
        if type(other) == _Pattern_Variable:
            other._initFactor()
        if type(other) == _Pattern_Variable:
            self.factor *= -1
        return self

    #def __int__(self):
    #    self._initFactor()
    #    return self.factor
    
    def getFactor(self):
        return self.factor
        
    def getIndex(self):
        return self.index
    
    def resetFactor(self):
        self.factor = 0
    
        
def _Event_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client
