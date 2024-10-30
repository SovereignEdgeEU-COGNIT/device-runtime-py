# This is needed to run the example from the cognit source code
# If you installed cognit with pip, you can remove this
import sys
sys.path.append(".")

from cognit import device_runtime

import cloudpickle as cp
import base64 as b64
import time

# Functions used to be uploaded
def sum(a: int, b: int):
    print("This is a test")
    return a + b

def multiply(a: int, b: int):
    print("This is a test")
    return a * b

# Workload from (7. Regression Analysis) of
# https://medium.com/@weidagang/essential-python-libraries-for-machine-learning-scipy-4367fabeba59

def ml_workload(x: int, y: int):
    import numpy as np
    from scipy import stats
    
    # Generate some data
    x_values = np.linspace(0, y, x)
    y_values = 2 * x_values + 3 + np.random.randn(x)
    
    # Fit a linear regression model
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
    
    # Print the results
    print("Slope:", slope)
    print("Intercept:", intercept)
    print("R-squared:", r_value**2)
    print("P-value:", p_value)
    
    # Predict y values for new x values
    new_x = np.linspace(5, 15, y)
    predicted_y = slope * new_x + intercept

    return predicted_y

# Execution requirements, dependencies and policies
REQS_INIT = {
      "FLAVOUR": "NatureV2",
      "MIN_ENERGY_RENEWABLE_USAGE": 85,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

REQS_NEW = {
      "FLAVOUR": "NatureV2",
      "MAX_FUNCTION_EXECUTION_TIME": 3.0,
      "MAX_LATENCY": 45,
      "MIN_ENERGY_RENEWABLE_USAGE": 75,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

# Requirements used for testing purposes
## TEST REQS 1: MAX_LATENCY and GEOLOCATION not defined
SIMPLE_REQS = {
    "FLAVOUR": "NatureV2",
    "MIN_ENERGY_RENEWABLE_USAGE": 85,
}

## TEST REQS 2: MAX_LATENCY defined but GEOLOCATION not defined
ERROR_REQS_NO_GEOLOCATION = {
    # With these reqs, CognitFrontendClient detects that the "GEOLOCATION" has not been defined although 
    # the "MAX_LATENCY" has been, and as a result it gives an error and does not upload 
    # the requirements to the CFE.
    "FLAVOUR": "NatureV2",
    "MIN_ENERGY_RENEWABLE_USAGE": 85,
    "MAX_LATENCY": 45
}

## TEST REQS 3: Wrong key
WRONG_KEY_REQS = {
    # In this case, as the Device Runtime internally creates a 'Scheduling' type of object
    # using the user requirements dictionary, the wrong key is omitted and the generated
    # 'Scheduling' object is filled with the default values.
      "FLAVOUR": "NatureV2",
      "WRONG_KEY": 123456,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

try:
    # Instantiate a device Device Runtime
    my_device_runtime = device_runtime.DeviceRuntime("./examples/cognit-template.yml")
    my_device_runtime.init(REQS_INIT)
    # Offload and execute a function
    return_code, result = my_device_runtime.call(sum, 100, 10)
    print("Status code: " + str(return_code))
    print("Sum result: " + str(result))
    
    # It is also possible to update the requirements 
    # when offloading a funcion or calling again the init function
    # Equivalent: my_device_runtime.call(multiply, 2, 3, new_reqs=TEST_REQS_NEW)
    my_device_runtime.init(REQS_NEW)
    return_code, result = my_device_runtime.call(multiply, 2, 3)
    print("Status code: " + str(return_code))
    print("Multiply result: " + str(result))
    # Lets offload a function with wrong parameters
    return_code, result = my_device_runtime.call(multiply, "wrong_parameter", 3)
    print("Status code: " + str(return_code))
    print("Multiply result: " + str(result))
    
    ## More complex function
    # Offload and execute ml_workload function
    start_time = time.perf_counter()
    return_code, result = my_device_runtime.call(ml_workload, 10, 5)
    end_time = time.perf_counter()
    print("Status code: " + str(return_code))
    print("Predicted Y: " + str(result))
    print(f"Execution time: {(end_time-start_time):.6f} seconds")
    
    # # Test all reqs are OK:
    # reqs_list = [REQS_INIT, REQS_NEW, ERROR_REQS_NO_GEOLOCATION, WRONG_KEY_REQS, SIMPLE_REQS]
    # print("")
    # for index, reqs in enumerate(reqs_list):
    #     print(index+1)
    #     my_device_runtime.init(reqs)
    #     print("## OK \n")

except Exception as e:
    print("An exception has occured: " + str(e))
    exit(-1)
