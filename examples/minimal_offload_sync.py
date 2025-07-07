# This is needed to run the example from the cognit source code
# If you installed cognit with pip, you can remove this
import sys
import time
sys.path.append(".")

from cognit import device_runtime

# Functions used to be uploaded
def suma(a: int, b: int):
    return a + b

def mult(a: int, b: int):
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
<<<<<<< Updated upstream
    "FLAVOUR": "SmartCity_ice_V2",
    "GEOLOCATION": {
        "latitude": 43.05,
        "longitude": -2.53
    }
}

REQS_NEW = {
    "FLAVOUR": "SmartCity_ice_V2",
    "MAX_FUNCTION_EXECUTION_TIME": 15.0,
    "MAX_LATENCY": 45,
    "MIN_ENERGY_RENEWABLE_USAGE": 75,
    "GEOLOCATION": {
        "latitude": 43.05,
        "longitude": -2.53
    }
}

REQS_ML = {
    "FLAVOUR": "NatureV2",
    "MAX_FUNCTION_EXECUTION_TIME": 15.0,
    "MAX_LATENCY": 45,
    "MIN_ENERGY_RENEWABLE_USAGE": 75,
    "GEOLOCATION": {
            "latitude": 43.05,
            "longitude": -2.53
        }
=======
      "FLAVOUR": "Nature",
      "GEOLOCATION": "43,2"
}

REQS_NEW = {
      "FLAVOUR": "Nature",
      "MAX_FUNCTION_EXECUTION_TIME": 15.0,
      "MAX_LATENCY": 45,
      "MIN_ENERGY_RENEWABLE_USAGE": 75,
      "GEOLOCATION": "43,2" 
}

REQS_ML = {
      "FLAVOUR": "Nature",
      "MAX_FUNCTION_EXECUTION_TIME": 15.0,
      "MAX_LATENCY": 45,
      "MIN_ENERGY_RENEWABLE_USAGE": 75,
      "GEOLOCATION": "43,1"
>>>>>>> Stashed changes
}


def get_result(result):
    print("*************************************************")
    print("Sync result: " + str(result))
    print("*************************************************")
    return result

try:

    # Instantiate a device Device Runtime
    my_device_runtime = device_runtime.DeviceRuntime("./examples/cognit-template.yml")
    my_device_runtime.init(REQS_INIT)

    # Synchronous offload and execution of a function
    result = my_device_runtime.call(suma, 17, 5)

    print("-----------------------------------------------")
    print("Sum sync result: " + str(result))
    print("-----------------------------------------------")

    # Update the requirements
    are_updated = my_device_runtime.update_requirements(REQS_NEW)

    if (are_updated):
        print("Requirements: "+ str(REQS_NEW) + " UPDATED!")
    else:   
        print("Requirements: "+ str(REQS_NEW) + "NOT UPDATED!")

    # Offload asyncronously a function
    my_device_runtime.call_async(suma, get_result, 100, 10)

    # Offload and execute a function
    result = my_device_runtime.call(mult, 2, 3)

    print("-----------------------------------------------")
    print("Multiply sync result: " + str(result))
    print("-----------------------------------------------")

    # Lets offload a function with wrong parameters
    result = my_device_runtime.call(mult, "wrong_parameter", "3")

    print("-----------------------------------------------")
    print("Wrong result: " + str(result))
    print("-----------------------------------------------")

    # Update the requirements
    are_updated = my_device_runtime.update_requirements(REQS_ML)

    if (are_updated):
        print("Requirements: "+ str(REQS_ML) + " UPDATED!")
    else:   
        print("Requirements: "+ str(REQS_ML) + "NOT UPDATED!")

    # More complex function
    # Offload and execute ml_workload function
    #start_time = time.perf_counter()
    #result = my_device_runtime.call(ml_workload, 10, 5)
    #end_time = time.perf_counter()

    #print("--------------------------------------------------------")
    #print("Predicted Y: " + str(result))
    #print(f"Execution time: {(end_time-start_time):.6f} seconds")
    #print("--------------------------------------------------------")

    time.sleep(5)

    # Offload and execute a function
    result = my_device_runtime.call(mult, 9, 12)

    print("-----------------------------------------------")
    print("Multiply sync result: " + str(result))
    print("----------------------------------------------------")

except Exception as e:
    print("An exception has occured: " + str(e))
    exit(-1)
