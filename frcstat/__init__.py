from .TBA_Client import TBA_Client
from .Season import Season , _Season_Set_TBA_Client
from .Event import Event , _Event_Set_TBA_Client
from .Team import Team , _Team_Set_TBA_Client

def resetClient(client):
    _Singleton_TBA_Client = client
    _Season_Set_TBA_Client(_Singleton_TBA_Client)
    _Event_Set_TBA_Client(_Singleton_TBA_Client)
    _Team_Set_TBA_Client(_Singleton_TBA_Client)
 
resetClient(TBA_Client())