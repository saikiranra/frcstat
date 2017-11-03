import frcstat as frc
import time

s1 = time.time()
s2016 = frc.Season(2016)
e1 = time.time()

s2 = time.time()
s22016 = frc.Season(2016 , True)
e2 = time.time()

s3 = time.time()
s2017 = frc.Season(2012)
e3 = time.time()


print(e1 - s1)
print(e2 - s2)
print(e3 - s3)

