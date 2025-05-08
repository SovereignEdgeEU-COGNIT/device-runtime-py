import sys
sys.path.append(".")

from cognit import device_runtime

import json # optional

# Execution requirements, dependencies and policies
REQS_INIT = {
      "FLAVOUR": "EnergyV2",
      "MIN_ENERGY_RENEWABLE_USAGE": 70,
      "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
}

def minio_list_buckets():
    try:
        # MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
        MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL
        MINIO_USERNAME = "minio_user"
        MINIO_PASSWORD = "minio_psw"
        
        from modules._minio_client import MinioClient # gets stuck in execution
        minio_client = MinioClient(
            endpoint_url=MINIO_ENDPOINT,
            access_key=MINIO_USERNAME,
            secret_key=MINIO_PASSWORD
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
            # MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
            MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL
            MINIO_USERNAME = "minio_user"
            MINIO_PASSWORD = "minio_psw"
            
            from modules._minio_client import MinioClient # gets stuck in execution
            minio_client = MinioClient(
                endpoint_url=MINIO_ENDPOINT,
                access_key=MINIO_USERNAME,
                secret_key=MINIO_PASSWORD
            )
            
            minio_client.create_bucket(bucket_name)
            return f"Bucket '{bucket_name}' created successfully."
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
        # MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
        MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL
        MINIO_USERNAME = "minio_user"
        MINIO_PASSWORD = "minio_psw"
        
        from modules._minio_client import MinioClient
        minio_client = MinioClient(
            endpoint_url=MINIO_ENDPOINT,
            access_key=MINIO_USERNAME,
            secret_key=MINIO_PASSWORD
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
    # MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
    MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL
    MINIO_USERNAME = "minio_user"
    MINIO_PASSWORD = "minio_psw"
    
    from modules._minio_client import MinioClient
    minio_client = MinioClient(
        endpoint_url=MINIO_ENDPOINT,
        access_key=MINIO_USERNAME,
        secret_key=MINIO_PASSWORD
    )
    print("Downloading object from MinIO...")
    data = minio_client.download_object(
        bucket=bucket_name,
        key=minio_path,
        download_path=None # if None, it will return the object as a byte array
    )
    return data

def download_data_to_disk(bucket_name, minio_path, save_disk_path):
    # MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
    MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL
    MINIO_USERNAME = "minio_user"
    MINIO_PASSWORD = "minio_psw"
    
    from modules._minio_client import MinioClient
    minio_client = MinioClient(
        endpoint_url=MINIO_ENDPOINT,
        access_key=MINIO_USERNAME,
        secret_key=MINIO_PASSWORD
    )
    data = minio_client.download_object(
        bucket=bucket_name,
        key=minio_path,
        download_path=save_disk_path
    )
    return data



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
    
    # If necessary, create the bucket:
    if bucket_name not in result.res:
        result = my_device_runtime.call(create_bucket, bucket_name)
        print("Bucket creation result: " + str(result.res))
        print("######################################\n")
    # Upload data
    
    simple_dict = {"a": 100, "b": 200, "testID":133}
    # Convert dict to JSON and then to bytes
    json_data = json.dumps(simple_dict).encode("utf-8")
    result = my_device_runtime.call(upload_data, bucket_name, minio_path, json_data, {'ContentType': 'application/json'})
    print("Upload result: " + str(result.res))
    print("######################################\n")
    
    result = my_device_runtime.call(download_data_to_memory, bucket_name, minio_path)
    data = result.res
    if data is not None:
        print("Data retrieved: " + str(data))
        # text = data.decode('utf-8')        # for text files
        obj  = json.loads(data)            # for JSON
        print(obj)
        # img  = Image.open(BytesIO(data))   # for images
        print("######################################\n")
    
    # Example of download to disk
    result = my_device_runtime.call(download_data_to_disk, bucket_name, minio_path, "/tmp/test.json")
    data = result.res
    if data is not None:
        print("Download path: " + str(data))
        print("######################################\n")
    print("######################################\n")


except Exception as e:
    print("An exception has occured: " + str(e))
    exit(-1)
