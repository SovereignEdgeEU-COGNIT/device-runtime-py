# Overview
This document serves as a general guide for users to use the Minio client provided in the SR repository. It gives some basic MinIO related information, how to use the SR minio client and finally provides an API of the available methods.

# MinIO general notes
It's important to note that Minio does not differentiate between files and folders: everything inside a bucket is considered an *object*.
However, externally Minio does support a linux like estructure using slash ("/"). For example, consider these two cases:
1. Save a file to the root bucket path:
    ```python
    minio_client.upload_object(
        bucket="ikerlan",
        objectPath="testData.csv",
        data=data
    )
    ```
    **Result inside MinIO**:
    ```bash
    ikerlan(bucket)
    └── testData.csv
    ```
2. Save a file inside a folder:
    ```python
    minio_client.upload_object(
        bucket="ikerlan",
        objectPath="recordings/20250512/recording1.csv",
        data=data
    )
    ```
    **Result inside MinIO**:
    ```bash
    ikerlan(bucket)
    └── recordings
        └── 20250512
            └── recording1.csv
    ```

# Function offloading guidelines
The following must be defined in the function using minio to be offloaded, as only the code inside the offloaded function is preserved.
- `endpoint_url`
  - String defining the Minio endpoint.
  - It must have the format "`http://IP:PORT`" (Important: "http://" must be included).
  - Note: Not tested with HTTPS.
- `access_key`
  - String defining the Minio username.
- `secret_key`
  - String defining the Minio password.

Additionally, the MinioClient import must follow the Serverless Runtime code structure. Curretly, the SR Minio code structure is the following:

```bash
.
├── app
│   ├── main.py
│   ├── models
│       └── ...
│   ├── modules
│       ├── _minio_client.py
│       ├── ...
│   ...
```
Considering that the SR code runs inside the "app" folder (*app/main.py*), the root folder becomes "app" and as such the import must be done considering this.

**So for the above structure, the import should be:**
```python
from modules._minio_client import MinioClient
```

## Enabling offloaded function logs in the SR log
There is a possibility to log the internal state of the offloaded funcions inside the Serverless Runtime app log.

To do so, the user will need to include the following inside **each offloaded function** that wants to log within the SR log:
```
from modules._logger import CognitLogger
cognit_logger = CognitLogger()
```
Afterwards the user can use the log levels:
```python
cognit_logger.debug("This is a     DEBUG     level message")
cognit_logger.info("This is an     INFO      level message")
cognit_logger.warning("This is a   WARNING   level message")
cognit_logger.error("This is an    ERROR     level message")
cognit_logger.critical("This is a  CRITICAL  level message")

```

So that the SR app log running in the VM will include the following, being the lines having "`[offload_minio.py::]`" the ones coming from the DR (note that it is the same as the DR script name inside "*examples*" folder.)
```bash
[2025-05-12 13:54:16,010] [DEBUG] [faas.py::304] PyExec created successfully
[2025-05-12 13:54:16,016] [INFO] [_pyexec.py::50] Starting the task ...
[2025-05-12 13:54:16,035] [DEBUG] [_minio_client.py::28] Initializing MinIO client...
[2025-05-12 13:54:16,062] [DEBUG] [_minio_client.py::41] MinIO client initialized successfully.
[2025-05-12 13:54:16,067] [DEBUG] [_minio_client.py::67] Listing buckets...
[2025-05-12 13:54:16,082] [DEBUG] [offload_minio.py::159] Deleting all objects in bucket: ikerlan
[2025-05-12 13:54:16,096] [DEBUG] [offload_minio.py::164] Bucket is empty, deleting bucket: ikerlan
[2025-05-12 13:54:16,108] [INFO] [_minio_client.py::86] Bucket 'ikerlan' deleted successfully.
[2025-05-12 13:54:16,112] [DEBUG] [offload_minio.py::166] ######################################
```

# Available methods
- This section describes the minio related methods available in the Serverless Runtime.
- More information of each specific method can be found in the Serverless Runtime repository's "`_minio_client.py`" inline comments.

## Bucket level methods

- `create_bucket(bucket_name)`
  - Create a bucket.
  
- `list_buckets() -> List[str]`
  - List all buckets.
  
- `delete_bucket(bucket_name)`
  - Delete an empty bucket.
  
- `enable_versioning(bucket_name)`
  - Enable versioning for a bucket.
  
- `set_bucket_policy(bucket_name, policy)`
  - Set a JSON policy document on a bucket.

## Object level methods

- `list_objects(bucket_name) -> List[str]`
  - List all object keys in a bucket.
  
- `upload_object(bucket, objectPath, data, extraArgs=None) -> str`
  - Upload raw bytes (`data`) to `bucket` at key `objectPath`, with optional `extraArgs` (metadata, ACL).
  
- `download_object(bucket: str, key: str, download_path: str = None) -> Union[bytes, str, Exception]`
  - If `download_path` is provided, save the object to that **Serverless Runtime** path and return the path; otherwise return raw bytes.
  > ***WARNING***: If `download_path` is provided, the downloaded file stays in the SR, meaning that no data is transferred back to the DR.
  
- `delete_object(bucket_name, object_name)`
  - Delete a single object from a bucket.
  
- `get_object_metadata(bucket_name, object_name) -> dict`
  - Retrieve the user-defined metadata for an object.
  
- `copy_object(source_bucket, source_key, destination_bucket, destination_key)`
  - Copy an object from one bucket/key to another bucket/key.

## Serverless Runtime local disk methods

- `download_file_to_sr_disk(bucket_name, object_name, download_path)`
  - Download a single file from a bucket to the Serverless Runtime’s local disk at `download_path`.
  
- `download_objects_with_prefix_to_sr_disk(bucket_name, prefix, target_local_directory, preserve_nested_structure=False)`
  - Download all objects in `bucket_name` whose keys start with `prefix` into `target_local_directory`.
    - If `preserve_nested_structure` is `False`, files are flattened into `target_local_directory`.
    - If `True`, the full key path under `prefix` is recreated under `target_local_directory`.

- `download_object(bucket: str, key: str, download_path: str = None) -> Union[bytes, str, Exception]`
  - For the cases that `download_path` is provided, as it is explained in "*Object level methods*" section.