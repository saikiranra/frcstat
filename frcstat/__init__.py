from .TBA_Client import TBA_Client
from .Season import Season, getSeason, _Season_Set_TBA_Client
from .Event import Event, getEvent, _Event_Set_TBA_Client
from .Team import Team, getTeam, _Team_Set_TBA_Client

LOCAL_ONLY    = 0 #Local only mode, if local file doesn't exist, error
CHECK_LOCAL   = 1 #If a local file exists, uses that instead of making request. If not, request is made
CHECK_REQUEST = 2 #Request is always made using the cache header



def resetClient(client):
    _Singleton_TBA_Client = client
    _Season_Set_TBA_Client(_Singleton_TBA_Client)
    _Event_Set_TBA_Client(_Singleton_TBA_Client)
    _Team_Set_TBA_Client(_Singleton_TBA_Client)
 
resetClient(TBA_Client())