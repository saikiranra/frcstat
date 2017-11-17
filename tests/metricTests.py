import frcstat as frc
import time

"""
scoreMetricFromPattern takes in a linear system of equations and will solve it for specified variables.
This is very useful in the exploration of new score metrics and has basic defenitons for OPR, EPR, GPR, and DPR.

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

cc = frc.Event("2017cc" , 2)
oprs = cc.scoreMetricFromPattern(cc.getCalculationPatterns()["OPR"]) 
#eq = "B1_P + B2_P + B3_P = BS - (score_breakdown_blue_foulPoints + score_breakdown_blue_kPaBonusPoints + score_breakdown_blue_teleopTakeoffPoints + score_breakdown_blue_autoMobilityPoints);"
#eq += "R1_P + R2_P + R3_P = RS - (score_breakdown_red_foulPoints + score_breakdown_red_kPaBonusPoints + score_breakdown_red_teleopTakeoffPoints + score_breakdown_red_autoMobilityPoints)"
eq = "B1_P + B2_P + B3_P = BS - (score_breakdown_blue_foulPoints);"
eq += "R1_P + R2_P + R3_P = RS - (score_breakdown_red_foulPoints)"
powerRating = cc.scoreMetricFromPattern(eq)

with open("power.csv" , 'w') as fp:
    for t in cc.getTeamList():
        fp.write("{},{},{}\n".format(t , str(oprs["{}1".format(t)]) , str(powerRating["{}_P".format(t)])))
        
