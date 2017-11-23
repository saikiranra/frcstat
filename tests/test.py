import frcstat as frc
import time
from scipy import stats

cc = frc.Event("2017new" , 1)
coprs = cc.coprs
lookup = cc.lookup

i118 = lookup["frc118"]
i1678 = lookup["frc1678"]

zoprs = stats.zscore(cc.oprs)
z = cc._assocArrayToDict(zoprs)

with open("zscores.csv" , 'w') as fp:
    for t in cc.getTeamList():
        fp.write("{},{},{}\n".format(t , str(cc.oprs[lookup[t]]) , str(z[t])))
        
