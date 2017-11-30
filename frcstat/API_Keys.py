import os

class API_Keys:
    def __init__(self , tbakey = None):
        if tbakey == None:
            try:
                self.tba = os.environ["TBA_KEY"]
            except:
                print("TBA_KEY not found in environmental variables. Please add to env vars, or initilize obj with key")
                self.tba = None
        else:
            self.tba = tbakey

    def getTBAKey(self):
        return self.tba
