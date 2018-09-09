import frcstat as frc


EVENTS_TO_TEST = ["2018cair" , "2018onwin" , "2013txho"]
DEBUG = True

def tester(event_code):
    event = frc.Event(event_code)
    realPoints = {}
    calculatedPoints = {}
    keys = set()
    print("Testing event {}".format(event_code))
    if event.districtPoints == None:
        errorMessage = "districtPointGeneration test cannot be run on event {} because the TBA API doesn't provide district points to test against".format(event_code)
        raise Exception(errorMessage)

    if DEBUG:
        print("Getting real district points")

    first = True
    for team in event.getTeamList():
        realPoints[team] = event.districtPoints["points"][team]
        if first:
            first = False
            keys = set(realPoints[team].keys())

    event.districtPoints = None

    if DEBUG:
        print("Getting calculated district points")
    first = True
    for team in event.getTeamList():
        calculatedPoints[team] = event.getDistrictPoints(team)
        if first:
            first = False
            keys = keys.union(set(calculatedPoints[team].keys()))

    if DEBUG:
        print("Generating point differences")
    for team in event.getTeamList():
        if realPoints[team] != calculatedPoints[team]:
            print("{} calculation not consistent.".format(team))
            if DEBUG:
                print("   {:20}   Real  Calc".format("Key"))
                for key in keys:
                    rv = -1
                    cv = -1
                    if key in calculatedPoints[team]:
                        cv = calculatedPoints[team][key]
                    if key in realPoints[team]:
                        rv = realPoints[team][key]
                    print("   {:20}    {:02d}    {:02d}".format(key , int(rv) , int(cv)))

    print("Done with event {}".format(event_code))       

if __name__ == "__main__":
    for event_code in EVENTS_TO_TEST:
        tester(event_code)
