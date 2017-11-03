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

