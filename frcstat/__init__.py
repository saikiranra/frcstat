from .TBA_Client import TBA_Client
from .Season import Season, getSeason, _Season_Set_TBA_Client
from .Event import Event, getEvent, _Event_Set_TBA_Client
from .Team import Team, getTeam, _Team_Set_TBA_Client

def resetClient(client):
    _Singleton_TBA_Client = client
    _Season_Set_TBA_Client(_Singleton_TBA_Client)
    _Event_Set_TBA_Client(_Singleton_TBA_Client)
    _Team_Set_TBA_Client(_Singleton_TBA_Client)
 
resetClient(TBA_Client())