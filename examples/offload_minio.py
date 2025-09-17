import sys
sys.path.append(".")

from cognit import device_runtime

import json # optional

# Execution requirements, dependencies and policies
REQS_INIT = {
      "FLAVOUR": "SmartCity",
      "MIN_ENERGY_RENEWABLE_USAGE": 70,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

def minio_list_buckets():
    try:
        MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
        # MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL TESTS
        
        from modules._logger import CognitLogger
        cognit_logger = CognitLogger()
        cognit_logger.debug(f" [DR] Listing buckets in {MINIO_ENDPOINT}")
        
        from modules._minio_client import MinioClient
        minio_client = MinioClient(
            endpoint_url=MINIO_ENDPOINT,
            access_key="minio_user",
            secret_key="minio_psw"
        )
        response = minio_client.list_buckets()
        return response
    except Exception as e:
        return [f"Error listing buckets: {str(e)}"]
    

def create_bucket(bucket_name):
        """
        Create a bucket.

        :param bucket_name: Name of the bucket to create.
        """
        try:
            MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
            # MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL TESTS
            
            from modules._logger import CognitLogger
            cognit_logger = CognitLogger()
            cognit_logger.debug(f" [DR] Creating bucket {MINIO_ENDPOINT}/{bucket_name}")
            
            from modules._minio_client import MinioClient
            minio_client = MinioClient(
                endpoint_url=MINIO_ENDPOINT,
                access_key="minio_user",
                secret_key="minio_psw"
            )
            
            minio_client.create_bucket(bucket_name)
            if bucket_name in minio_client.list_buckets():
                return f"Bucket {bucket_name} created successfully"
            else:
                return f"No exceptions, but bucket {bucket_name} was not created"
        except Exception as e:
            return f"Failed to create bucket: {str(e)}"

  
def upload_data(bucket_name, minio_path, data, extraArgs=None):
    """
    Upload an object to MinIO.
    :param bucket_name: Name of the bucket.
    :param minio_path: Path to the object in MinIO.
    :param data: Data to upload (as bytes).
    :param extraArgs: Extra arguments for the upload, such as metadata (optional).
    """
    try:
        MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
        # MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL TESTS
        
        
        
        from modules._logger import CognitLogger
        cognit_logger = CognitLogger()
        cognit_logger.debug(f" [DR] Uploading data to {MINIO_ENDPOINT}/{bucket_name}/{minio_path}")
        
        from modules._minio_client import MinioClient
        minio_client = MinioClient(
            endpoint_url=MINIO_ENDPOINT,
            access_key="minio_user",
            secret_key="minio_psw"
        )

        minio_client.upload_object(
            bucket=bucket_name,
            objectPath=minio_path,
            data=data,
            extraArgs=extraArgs
        )
        return f"Uploaded JSON file to {bucket_name}/{minio_path}"
    except Exception as e:
        return f"Failed to upload JSON file: {str(e)}"
      

def download_data_to_memory(bucket_name, minio_path):
    MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
    # MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL TESTS
    
    from modules._logger import CognitLogger
    cognit_logger = CognitLogger()
    cognit_logger.debug(f" [DR] Downloading data to memory from {MINIO_ENDPOINT}/{bucket_name}/{minio_path}")
    
    from modules._minio_client import MinioClient
    minio_client = MinioClient(
        endpoint_url=MINIO_ENDPOINT,
        access_key="minio_user",
        secret_key="minio_psw"
    )
    data = minio_client.download_object(
        bucket=bucket_name,
        key=minio_path,
        download_path=None # if None, it will return the object as a byte array
    )
    return data


def download_data_to_disk(bucket_name, minio_path, save_disk_path):
    MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
    # MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL TESTS
    
    from modules._logger import CognitLogger
    cognit_logger = CognitLogger()
    cognit_logger.debug(f" [DR] Downloading data to disk from {MINIO_ENDPOINT}/{bucket_name}/{minio_path}")
    
    from modules._minio_client import MinioClient
    minio_client = MinioClient(
        endpoint_url=MINIO_ENDPOINT,
        access_key="minio_user",
        secret_key="minio_psw"
    )
    data = minio_client.download_object(
        bucket=bucket_name,
        key=minio_path,
        download_path=save_disk_path
    )
    return data

def recursive_cleanup():
    """
    Recursivelly deletes all the objects and buckets in MinIO.
    The bucket must be empty before deleting it, so first all the objects are deleted.
    """
    MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
    # MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL TESTS
    
    from modules._minio_client import MinioClient
    minio_client = MinioClient(
        endpoint_url=MINIO_ENDPOINT,
        access_key="minio_user",
        secret_key="minio_psw"
    )
    
    ## Use this to enable logging mechanism for the offloaded function in the SR:
    from modules._logger import CognitLogger
    cognit_logger = CognitLogger()
    ##
    
    bucket_list = minio_client.list_buckets()
    for bucket in bucket_list:
        cognit_logger.debug("######################################\n")
        cognit_logger.debug("Deleting all objects in bucket: " + str(bucket))
        objects = minio_client.list_objects(bucket)
        for obj in objects:
            cognit_logger.debug("Deleting object: " + str(obj))
            minio_client.delete_object(bucket, obj)
        cognit_logger.debug("Bucket is empty, deleting bucket: " + str(bucket))
        minio_client.delete_bucket(bucket)
        cognit_logger.debug("######################################\n")
        
    return len(minio_client.list_buckets()) == 0 # Returns True if all buckets have been deleted


def run_rest_large_files(my_device_runtime, bucket_name):
    # 1. Upload to MinIO
    minio_path = "test/test_large_file.json.gz"
    with open("examples/2015-01-01-15.json.gz", "rb") as f:
        json_data = f.read()
    result = my_device_runtime.call(upload_data, bucket_name, minio_path, json_data)
    print("Upload result: " + str(result.ret_code))
    print("######################################\n")
    # 2. Download from MinIO
    result = my_device_runtime.call(download_data_to_memory, bucket_name, "test/test_large_file.json.gz")
    print("Download result: " + str(result.ret_code))
    print("######################################\n")


def run_minio_example():
    try:
        # Instantiate a device Device Runtime
        my_device_runtime = device_runtime.DeviceRuntime("./examples/cognit-template.yml")
        my_device_runtime.init(REQS_INIT)
        bucket_name = "ikerlan"
        minio_path = "test/test.json" # minio will automatically create a folder named "test" in the bucket and create the file "test.json" inside
             
        # List buckets
        # return_code, result = my_device_runtime.call(minio_list_buckets)
        result = my_device_runtime.call(minio_list_buckets)
        # print("Status code: " + str(return_code))
        print("Available buckets: " + str(result.res))
        print("######################################\n")
        if (len(result.res) > 0) and ("ERROR" in result.res[0]): # error happened
            print("Error listing buckets, exiting...")
            return -1
        
        # If necessary, create the bucket:
        if bucket_name not in result.res:
            result = my_device_runtime.call(create_bucket, bucket_name)
            print("Bucket creation result: " + str(result.res))
            print("######################################\n")
        
        ## Upload data
        simple_dict = {"a": 100, "b": 200, "testID":133}
        # Convert dict to JSON and then to bytes
        json_data = json.dumps(simple_dict).encode("utf-8")
        result = my_device_runtime.call(upload_data, bucket_name, minio_path, json_data, {'ContentType': 'application/json'})
        print("Upload result: " + str(result.res))
        print("######################################\n")
        
        result = my_device_runtime.call(download_data_to_memory, bucket_name, minio_path)
        data = result.res
        #data = None
        if data is not None:
            print("Data retrieved: " + str(data))
            # text = data.decode('utf-8')        # for text files
            obj  = json.loads(data)            # for JSON
            print(obj)
            # img  = Image.open(BytesIO(data))   # for images
            print("######################################\n")
        
        
        
        ### Test with large file (3.7MB).
        ### Previously downloaded to device running the DR using: `github-device-runtime-py/examples$ wget https://data.gharchive.org/2015-01-01-15.json.gz``
        if True:
            try:
                run_rest_large_files(my_device_runtime, bucket_name)
                # If it gives:
                # "HTTPError: 413 Client Error: Request Entity Too Large for url..."
                # then it means that the file size is larger thant the one
                # allowed in the NGINX configuration of the edge cluster frontend.
            except Exception as e:
                print("An exception has occured: " + str(e))
                print("######################################\n")
        
        ### Example of download to SR disk (data remains in SR, not in DR)
        if False: # Tested, but unusued currently
            result = my_device_runtime.call(download_data_to_disk, bucket_name, minio_path, "/tmp/test.json")
            data = result.res
            if data is not None:
                print(f"Download path is {str(data)}, verify in the SR ") 
                print("######################################\n")
        
        ## Cleanup -> Delete all buckets and objects
        print("Cleaning all buckets and objects...")
        result = my_device_runtime.call(recursive_cleanup)
        print("Cleanup result: " + str(result.res))

        return 0

    except Exception as e:
        print("An exception has occured: " + str(e))

        return -1


def run_cleanup():
    my_device_runtime = device_runtime.DeviceRuntime("./examples/cognit-template.yml")
    my_device_runtime.init(REQS_INIT)
    result = my_device_runtime.call(recursive_cleanup)
    # print("Status code: " + str(return_code))
    print("Cleanup result: " + str(result.res))

if __name__ == "__main__":
    run_minio_example()
    # run_cleanup() -> Called as last step inside 'run_minio_example' 
    print("Exit OK")
