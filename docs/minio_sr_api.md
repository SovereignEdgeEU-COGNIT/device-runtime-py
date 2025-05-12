# Overview
This document describes the minio related methods available in the Serverless Runtime.
Additional information can be found in the Serverless Runtime repository's "_minio_client.py" inline comments.

# Function offloading guidelines
The following must be defined in the function using minio to be offloaded:
- `endpoint_url`
  - String defining the Minio endpoint.
  - It must have the format "http://IP:PORT" (Important: "http://" must be included).
  - Not tested with HTTPS.
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

So for the above structure, the import should be:
- `from modules._minio_client import MinioClient`

# Available methods

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