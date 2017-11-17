import frcstat as frc
import time

cc = frc.Event("2017new" , 1)
oprs = cc.scoreMetricFromPattern()
eq = "B1_P + B2_P + B3_P = BS - (score_breakdown_blue_foulPoints + score_breakdown_blue_kPaBonusPoints + score_breakdown_blue_teleopTakeoffPoints + score_breakdown_blue_autoMobilityPoints);"
eq += "R1_P + R2_P + R3_P = RS - (score_breakdown_red_foulPoints + score_breakdown_red_kPaBonusPoints + score_breakdown_red_teleopTakeoffPoints + score_breakdown_red_autoMobilityPoints)"

powerRating = cc.scoreMetricFromPattern(eq)

with open("power.csv" , 'w') as fp:
    for t in cc.getTeamList():
        fp.write("{},{},{}\n".format(t , str(oprs["{}1".format(t)]) , str(powerRating["{}_P".format(t)])))
        
