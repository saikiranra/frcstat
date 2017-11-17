# FRC-Statistics-Library

## Setup

For active development, all that needs to happen is a Make command in the root directory of this project. On first use, it will install required packages and set up as a library internally in Python. After each change that you want to test, Making will be very quick and allow you to use "import FRC" in any directory. 

## Use

### TBA API Key
There are two ways of registering your TBA API key with the library. 

The first would be to create an environment variable "TBA_KEY" which refers to the key. 

The second would be in code, after importing the library. 

```python
import frcstat
frcstat.resetClient(frcstat.TBA_Client("API_KEY"))
``` 


### Accessing Data

```python
import frcstat as frc

newton = frc.Event("2016new")
poofs = frc.Team(254)
stronghold = frc.Season(2016)

#Print Awards won in 2016
for award in poofs.getAwardsByYear(2016):
	print(award["name"])
	
#Get OPRS from Newton
oprs = newton.scoreMetricFromPattern() #method for accessing OPRS and component OPRS will change in the future
print(oprs["frc2541"])

#Get EPRS from Newton
eprs = newton.scoreMetricFromPattern("R1_epr + R2_epr + R3_epr + (-1)*B1_epr + (-1)*B2_epr + (-1)*B3_epr = RS - BS;B1_epr + B2_epr + B3_epr = BS.R1_epr + R2_epr + R3_epr = RS") 
print(eprs["frc254_epr"])
```

