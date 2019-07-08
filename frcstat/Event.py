import re
import frcstat.Team as Team
import numpy as np
import scipy.linalg as lin
from copy import copy
from scipy.special import erfinv
from collections import defaultdict
from .ObjectShare import ObjectShare

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
        self.cacheRefreshAggression = localDataOnly
        self.matchData = None
        self.teamList = None
        self.rawTeamList = None
        self.eventData = None
        self.rankings = None
        self.teamList = None
        self.districtPoints = None
        self.awards = None
        self.alliances = None
        self.oprs = None
        self.coprs = None

        self.fetchedOprs = False
        self.fetchedCoprs = False
        self.fetchedAlliances = False
        self.fetchedRankings = False
        self.fetchedMatches = False

        self.lookup = None

        self.qualMatchAmount = None

        self.validityFile = code + "-valid"
        self._old_validity_data = None

    def getMatchData(self):
        if not self.fetchedMatches:
            self.loadMatchData()
            self.fetchedMatches = True
        return self.matchData

    def getRankings(self):
        if not self.fetchedRankings:
            self.loadRankingsData()
            self.fetchedRankings = True
        return self.rankings

    def getDistrictPoints(self):
        if not self.districtPoints:
            self.loadDistrictPoints()
        return self.districtPoints

    def getAwardsObj(self):
        if not self.awards:
            self.loadAwards()
        return self.awards

    def getAlliances(self):
        if not self.fetchedAlliances:
            self.loadAlliances()
            self.fetchedAlliances = True
        return self.alliances

    def getTeamList(self):
        """
           Returns team list.

           Currently, this is the same thing as getPlayingTeamList(). This is calculated on the loading of this object.
        """
        if not self.teamList:
            self.loadTeamList()
        return self.teamList

    def getRawTeamList(self):
        """
           Returns the teamlist that is returned from the API rather than a team list created from matches and rankings
        """
        if not self.rawTeamList:
            self.loadTeamList()
        return self.rawTeamList

    def getEventData(self):
        if not self.eventData:
            self.loadEventData()
        return self.eventData

    def getLookup(self):
        if not self.lookup:
            self.lookup = self._getLookupDict()
        return self.lookup

    def getOprs(self):
        if not self.fetchedOprs:
            self.loadOprs()
            self.fetchedOprs = True
        return self.oprs

    def getCoprs(self):
        if not self.fetchedCoprs:
            self.loadCoprs()
            self.fetchedCoprs = True
        return self.coprs

    def getTeamAmount(self):
        if self.getTeamList():
            return len(self.teamList)
        return len(self.rawTeamList)

    def getQualMatchAmount(self):
        if not self.qualMatchAmount:
            self.qualMatchAmount = 0
            matchData = self.getMatchData()
            for mkey in matchData:
                m = matchData[mkey]
                if m["comp_level"] == "qm":
                    self.qualMatchAmount += 1
        return self.qualMatchAmount

    def getYear(self):
        eventData = self.getEventData()
        return eventData['year']

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
        matchData = self.getMatchData()
        return matchData[matchKey]
        
    def elimMatchGen(self):
        matchData = self.getMatchData()
        for m in matchData:
            if matchData[m]["comp_level"] != "qm":
                yield matchData[m]

    def qualsMatchGen(self):
        matchData = self.getMatchData()
        for m in matchData:
            if matchData[m]["comp_level"] == "qm":
                yield matchData[m]
        
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
        
        matchData = self.getMatchData()
        for m in matchData:
            if matchData[m]["comp_level"] == "qm":
                match = matchData[m]
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
            #print("LEAST SQUARES SOLUTION USED.")
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
        matchData = self.getMatchData()
        for m in matchData:
            if matchData[m]["comp_level"] == "qm":
                match = matchData[m]
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
        
        #factoredA = lin.cho_factor(A , True , True , False)
        for key in validKeys:
            try:
                out[key] = lin.solve(np.copy(A), BDict[key])
            except:
                #print("LEAST SQUARES SOLUTION USED.")
                #print(A)
                #print(B)
                #print(lin.lstsq(A , B))
                out[key] =  lin.lstsq(np.copy(A) , BDict[key])[0]
            #out[key] = lin.cho_solve(np.copy(factoredA) , BDict[key] , False)
        return out
        
    def getTeamMatches(self , team):
        if type(team) == int:
            team = "frc" + str(team)
        out = {}
        matchData = self.getMatchData()
        for key in matchData.keys():
            if team in matchData[key]["alliances"]["red"]["team_keys"]:
                out[key] = matchData[key]
            elif team in matchData[key]["alliances"]["blue"]["team_keys"]:
                out[key] = matchData[key]
        return out
        
    def _allianceLookup(self, teams , lookup):
        for i in range(len(lookup)):
            for team in teams:
                if team in lookup[i]:
                    return i
        raise Exception("Event _allianceLookup failed")
        
    def _getAlliancesFromMatches(self):
        """
            Most years
                Code - R v B
                qf1  - 1 v 8
                qf2  - 4 v 5
                qf3  - 2 v 7
                qf4  - 3 v 6
        """
        alliances = [{"status" : {"level" : "qf" , "status" : "eliminated"} , "picks" : None} for i in range(8)]
        if self.getYear() == 2015:
            pass
        else:
            matchData = self.getMatchData()
            alliances[0]["picks"] = matchData["qf1m1"]["alliances"]["red"]["team_keys"]
            alliances[7]["picks"] = matchData["qf1m1"]["alliances"]["blue"]["team_keys"]
            alliances[3]["picks"] = matchData["qf2m1"]["alliances"]["red"]["team_keys"]
            alliances[4]["picks"] = matchData["qf2m1"]["alliances"]["blue"]["team_keys"]
            alliances[1]["picks"] = matchData["qf3m1"]["alliances"]["red"]["team_keys"]
            alliances[6]["picks"] = matchData["qf3m1"]["alliances"]["blue"]["team_keys"]
            alliances[2]["picks"] = matchData["qf4m1"]["alliances"]["red"]["team_keys"]
            alliances[5]["picks"] = matchData["qf4m1"]["alliances"]["blue"]["team_keys"]
            
            lookup = []
            for i in range(len(alliances)):
                lookup.append(alliances[i]["picks"])
            
            #finals
            for codes in [("f" , "f1") , ("sf" , "sf1") , ("sf" , "sf2")]:
                fdat = matchData[codes[1] + "m2"] if codes[1] + "m3" not in matchData else matchData[codes[1] + "m3"]
                wCol = fdat["winning_alliance"]
                lCol = "red" if fdat["winning_alliance"] == "blue" else "blue"
                wAlliance = self._allianceLookup(fdat["alliances"][wCol]["team_keys"] , lookup)
                lAlliance = self._allianceLookup(fdat["alliances"][lCol]["team_keys"] , lookup)
                
                if alliances[wAlliance]["status"]["level"] == "qf":
                    alliances[wAlliance]["status"]["status"] = "won"
                    alliances[wAlliance]["status"]["level"] = codes[0]
                if alliances[lAlliance]["status"]["level"] == "qf":
                    alliances[lAlliance]["status"]["status"] = "eliminated"
                    alliances[lAlliance]["status"]["level"] = codes[0]
                    
        return alliances

    def getTeamDistrictPoints(self , teamNumber , rookieYear = None, includePlayoffs = True):
        code = teamNumber
        if type(teamNumber) == int:
            code = "frc"+str(teamNumber)

        districtPoints = self.getDistrictPoints()
        if (districtPoints is not None and code in districtPoints['points']) and self.getYear() >= 2015: #years from 2015 to now we can trust TBA data
            return districtPoints["points"][code]
        if self.getYear() == 2015:
            print("WARNING: undefined behavior for 2015 elims points")
            #raise Exception("Event getDistrictPoints calculator doesn't currently support 2015")
        else:
            #formula
            rookiePoints = 0
            awardsPoints = 0
            playoffPoints = 0
            alliancePoints = 0
            rankingPoints = 0
            
            #rookie points
            """
            if rookieYear == None:
                team = Team.Team(teamNumber)
                rookieYear = team.teamData["rookie_year"]
            yearDiff = self.eventData["year"] - rookieYear
            if yearDiff < 2:
                rookiePoints = 10 - (5 * yearDiff)
            """

            #awards points
            awards = self.getAwardsObj()
            for award in awards:
                isRecipient = False
                for recipient in award["recipient_list"]:
                    if recipient["team_key"] == code:
                        isRecipient = True
                        break
                if isRecipient:
                    if award["award_type"] == 0: #chairmans
                        awardsPoints += 10
                    elif award["award_type"] == 9: #ei
                        awardsPoints += 8
                    elif award["award_type"] == 10: #rookie all star
                        awardsPoints += 8
                    elif award["award_type"] == 68:  #wildcard
                        pass
                    elif award["award_type"] == 14:  #highest rookie seed
                        pass
                    elif award["award_type"] > 10:
                        awardsPoints += 5
                        
            #alliance selection results
            allianceObj = self.getAlliances() #to facilitate the generation of them
            if not allianceObj:
                allianceObj = self._getAlliancesFromMatches()
            for allianceNumber in range(len(allianceObj)):
                alliance = allianceObj[allianceNumber]
                if code in alliance["picks"]:
                    if code == alliance["picks"][0]:
                        alliancePoints = 16 - allianceNumber
                    elif code == alliance["picks"][1]:
                        alliancePoints = 16 - allianceNumber
                    else:
                        alliancePoints = 1 + allianceNumber
                    break
                    
            #playoff performance
            if includePlayoffs:
                matchData = self.getMatchData()
                for matchKeys in matchData:
                    if "qm" not in matchKeys:
                        winningAllianceKey = matchData[matchKeys]["winning_alliance"]
                        if winningAllianceKey == "":
                            winningAllianceKey = "red"
                            if matchData[matchKeys]["alliances"]["red"]["score"] < matchData[matchKeys]["alliances"]["blue"]["score"]:
                                winningAllianceKey = "blue"
                        if code in matchData[matchKeys]["alliances"][winningAllianceKey]["team_keys"]:
                            lastMatchInSeries = matchKeys[:-1]+"2" if matchKeys[:-1]+"3" not in matchData else matchKeys[:-1]+"3"
                            if winningAllianceKey == matchData[lastMatchInSeries]["winning_alliance"]:
                                playoffPoints += 5


            #qualification round performance
            rankings = self.getRankings()
            r = -1
            n = len(rankings['rankings'])
            a = 1.07
            for rankData in rankings["rankings"]:
                if code == rankData["team_key"]:
                    r = rankData["rank"]

            rankingPoints = min(np.ceil((erfinv((n - (2 * r) + 2) / (a * n)) * (10 / (erfinv(1/a)))) + 12) , 22)

            out = {}
            out["alliance_points"] = int(alliancePoints)
            out["award_points"] = int(awardsPoints)
            out["elim_points"] = int(playoffPoints)
            out["qual_points"] = int(rankingPoints)
            out["total"] = rookiePoints + alliancePoints + awardsPoints + playoffPoints + rankingPoints

            return out
 
    def getTeamElimWins(self, teamNumber):
        if not self.teamElimWins:
            self.teamElimWins = {}
        eventData = self.getEventData()
        year = eventData["year"]
        argTeamCode = 'frc{}'.format(teamNumber)
        if argTeamCode in self.teamElimWins:
            return self.teamElimWins[argTeamCode]
        for teamCode in self.teamList:
            teamMatches = self.getTeamMatches(teamCode)
            wins = 0
            for matchKey in teamMatches.keys():
                if teamMatches[matchKey]["comp_level"] != "qm":
                    if year != 2015:
                        color = "blue"
                        if teamCode in teamMatches[matchKey]["alliances"]["red"]["team_keys"]:
                            color = "red"
                        if color == teamMatches[matchKey]["winning_alliance"]:
                            wins += 1
                    else:
                        if (teamCode in teamMatches[matchKey]["alliances"]["red"]["team_keys"] \
                            and teamMatches[matchKey]["alliances"]["red"]["score"] > teamMatches[matchKey]["alliances"]["blue"]["score"]) \
                            or (teamCode in teamMatches[matchKey]["alliances"]["blue"]["team_keys"] \
                            and teamMatches[matchKey]["alliances"]["blue"]["score"] > teamMatches[matchKey]["alliances"]["red"]["score"]):
                            wins += 1
                            
            self.teamElimWins[teamCode] = wins if year != 2015 else min(wins, 6)
        return self.teamElimWins[argTeamCode]

        
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
        sortedMatches = [self.matchData[m] for m in self.getMatchData()]
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
        if len(metricArray) != self.getTeamAmount():
            raise("metricArray not same size as teamList!")
        out = {}
        for i in range(self.getTeamAmount()):
            out[self.teamList[i]] = metricArray[i]
        return out

    def _getLookupDict(self):
        """
            Returns a dictionary where team codes are linked to an array index
        """
        out = {}
        teamList = self.getTeamList()
        if teamList == None:
            teamList = self.rawTeamList
        for i in range(self.getTeamAmount()):
            out[teamList[i]] = i
        return out

    def readValidityData(self):
        self._old_validity_data =  _Singleton_TBA_Client.dictToDefaultDict(_Singleton_TBA_Client.readEventData(self.validityFile) , lambda:None)
        return copy(self._old_validity_data)

    def writeValidityData(self, validityData):
        if self._old_validity_data == validityData:
            return True
        return _Singleton_TBA_Client.writeEventData(self.validityFile , validityData)

    def loadData(self):
        '''
            cacheRefreshAggression - [0,1,2]. 
                0 only uses saved data
                1 checks if saved data file exists, if not make a requests (checks cache validity through request)
                2 only makes new requests (checks cache validity through request)
            
            
        '''

        self.loadEventData()
        self.loadMatchData()
        self.loadRankingsData()
        self.loadTeamList()
        self.loadDistrictPoints()
        self.loadAwards()
        self.loadAlliances()

        ###Derived Calculations###

        self.loadOprs()
        self.loadCoprs()


    def loadEventData(self):
        validityData = self.readValidityData()
        dataObjName = "{}-data".format(self.eventCode)
        dataRequest = "event/{}".format(self.eventCode)
        self.eventData = _Singleton_TBA_Client.makeSmartRequest(dataObjName, dataRequest, validityData, self,
                                                                self.cacheRefreshAggression)
        self.writeValidityData(validityData)

    def loadMatchData(self):
        validityData = self.readValidityData()
        def matchDataMutator(md):
            out = {}
            for m in md:
                out[m["key"].replace(self.eventCode + "_", "")] = m
            return out

        matchObjName = "{}-matches".format(self.eventCode)
        matchRequest = "event/{}/matches".format(self.eventCode)
        self.matchData = _Singleton_TBA_Client.makeSmartRequest(matchObjName, matchRequest, validityData, self,
                                                                self.cacheRefreshAggression, matchDataMutator)
        self.writeValidityData(validityData)

    def loadRankingsData(self):
        validityData = self.readValidityData()
        rankingsObjName = "{}-rankings".format(self.eventCode)
        rankingsRequest = "event/{}/rankings".format(self.eventCode)
        self.rankings = _Singleton_TBA_Client.makeSmartRequest(rankingsObjName, rankingsRequest, validityData, self,
                                                               self.cacheRefreshAggression)
        self.writeValidityData(validityData)

    def loadTeamList(self):
        validityData = self.readValidityData()
        teamListObjName = "{}-teamlist".format(self.eventCode)
        teamListRequest = "event/{}/teams/keys".format(self.eventCode)
        self.rawTeamList = _Singleton_TBA_Client.makeSmartRequest(teamListObjName, teamListRequest, validityData, self,
                                                                  self.cacheRefreshAggression)
        try:
            self.teamList = self.getPlayingTeamList(True)
        except:
            self.teamList = None
        self.writeValidityData(validityData)

    def loadDistrictPoints(self):
        validityData = self.readValidityData()
        # Containts both tie breaker and point data
        districtPointsObjName = "{}-districtpoints".format(self.eventCode)
        districtPointsRequest = "event/{}/district_points".format(self.eventCode)
        self.districtPoints = _Singleton_TBA_Client.makeSmartRequest(districtPointsObjName, districtPointsRequest,
                                                                     validityData, self, self.cacheRefreshAggression)
        self.writeValidityData(validityData)

    def loadAwards(self):
        validityData = self.readValidityData()
        awardsObjName = "{}-awards".format(self.eventCode)
        awardsRequest = "event/{}/awards".format(self.eventCode)
        self.awards = _Singleton_TBA_Client.makeSmartRequest(awardsObjName, awardsRequest, validityData, self,
                                                             self.cacheRefreshAggression)
        self.writeValidityData(validityData)

    def loadAlliances(self):
        validityData = self.readValidityData()
        allianceObjName = "{}-alliances".format(self.eventCode)
        allianceRequest = "event/{}/alliances".format(self.eventCode)
        self.alliances = _Singleton_TBA_Client.makeSmartRequest(allianceObjName, allianceRequest, validityData, self,
                                                                self.cacheRefreshAggression)
        self.writeValidityData(validityData)

    def loadOprs(self):
        self.oprs = np.array(_Singleton_TBA_Client.readEventData("{}-oprs".format(self.eventCode)))
        if self.oprs.size <= 1:
            self.oprs = self.getArrayOPRS()
            _Singleton_TBA_Client.writeEventData("{}-oprs".format(self.eventCode), self.oprs.tolist())

    def loadCoprs(self):
        # We can't get COPRS for old games
        try:
            self.coprs = np.array(_Singleton_TBA_Client.readEventData("{}-coprs".format(self.eventCode)))
            if self.coprs.size <= 1:
                self.coprs = self.getComponentOPRS()
                _Singleton_TBA_Client.writeEventData("{}-coprs".format(self.eventCode), self.coprs.tolist())
        except:
            pass


    def getPlayingTeamList(self , getKey = False):
        """
            Returns a team list based on rankings or match data
            
            getKey determines if the list is filled with numbers or team keys
            getKey = False : [3476 , 254, 1114, 118]
            getKey = True  : ["frc3476" , "frc254" , "frc1114" , "frc118"]
        """
        modFunc = int
        if getKey:
            modFunc = self.getTeamKey

        rankings = self.getRankings()
        if rankings:
            if len(rankings['rankings']) > 0:
                return [modFunc(team['team_key'][3:]) for team in rankings['rankings']]
        matchData = self.getMatchData()
        if matchData:
            out = set()
            for matchKey in matchData:
                for color in matchData[matchKey]["alliances"]:
                    if matchData[matchKey]["alliances"][color]["score"] > -1:
                        out = out.union(matchData[matchKey]["alliances"][color]["team_keys"])
            return [modFunc(x) for x in out]
        return [modFunc(x) for x in self.rawTeamList]
        
    def getTeamKey(self, team):
        """
            Helper function to return a teamkey in the form "frc####"
        """
        out = str(team)
        if len(team) < 4:
            return "frc" + team
        if team[:2] == "frc":
            return team
        return "frc" + team

    def getAwards(self):
        """
            Returns a dictionary mapping from teamKey to a set of awards won at that event, i.e. for 2018nyut, 
            awards['frc2791'] = set([1, 16]), for winner and industrial design
        """
        awardsDict = {teamKey: set([]) for teamKey in self.getRawTeamList()}
        awards = self.getAwardsObj()
        if awards is None:
            return {}
        for award in awards:
            awardType = award["award_type"]
            for recipient in award["recipient_list"]:
                teamKey = recipient["team_key"]
                if teamKey is not None and teamKey in awardsDict:
                    awardsDict[teamKey].add(awardType)
        return awardsDict

        
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


_eventShare = ObjectShare(Event)


def getEvent(eventKey, cacheRefreshAggression = 1):
    return _eventShare.get(eventKey, cacheRefreshAggression)

        
def _Event_Set_TBA_Client(client):
    global _Singleton_TBA_Client
    _Singleton_TBA_Client = client
