from cognit.modules._minio_client import MinioClient  # Assuming the client is saved as minio_client.py
from botocore.exceptions import ClientError
import pytest

# IMPORTANT #
# Before executing these test, launch the minio container located in the local_minio directory
# Using docker-compose up

# Fixture to initialize the MinioClient
def get_minio_client():
    endpoint = "http://localhost:9000"
    access_key = "user123"
    secret_key = "CHANGEME123"
    return MinioClient(endpoint, access_key, secret_key)

@pytest.fixture
def minio_client():
    return get_minio_client()

@pytest.fixture
def test_bucket_name():
    return "test-bucket"

@pytest.fixture
def test_object_name():
    return "test-object.txt"

@pytest.fixture
def test_file_path(tmp_path):
    file_path = tmp_path / "test-file.txt"
    file_path.write_text("This is a test file.")
    return str(file_path)

def test_create_bucket(minio_client, test_bucket_name):
    try:
        minio_client.create_bucket(test_bucket_name)
        buckets = minio_client.list_buckets()
        assert test_bucket_name in buckets
    finally:
        minio_client.delete_bucket(test_bucket_name)

def test_upload_file(minio_client, test_bucket_name, test_file_path, test_object_name):
    try:
        minio_client.create_bucket(test_bucket_name)
        minio_client.upload_file(test_bucket_name, test_file_path, test_object_name)
        objects = minio_client.list_objects(test_bucket_name)
        assert test_object_name in objects
    finally:
        minio_client.delete_object(test_bucket_name, test_object_name)
        minio_client.delete_bucket(test_bucket_name)

def test_download_file(minio_client, test_bucket_name, test_file_path, test_object_name, tmp_path):
    try:
        minio_client.create_bucket(test_bucket_name)
        minio_client.upload_file(test_bucket_name, test_file_path, test_object_name)

        download_path = tmp_path / "downloaded-file.txt"
        minio_client.download_file(test_bucket_name, test_object_name, str(download_path))

        assert download_path.exists()
        assert download_path.read_text() == "This is a test file."
    finally:
        minio_client.delete_object(test_bucket_name, test_object_name)
        minio_client.delete_bucket(test_bucket_name)

def test_list_objects(minio_client, test_bucket_name, test_file_path, test_object_name):
    try:
        minio_client.create_bucket(test_bucket_name)
        minio_client.upload_file(test_bucket_name, test_file_path, test_object_name)
        objects = minio_client.list_objects(test_bucket_name)
        assert test_object_name in objects
    finally:
        minio_client.delete_object(test_bucket_name, test_object_name)
        minio_client.delete_bucket(test_bucket_name)

def test_delete_object(minio_client, test_bucket_name, test_file_path, test_object_name):
    try:
        minio_client.create_bucket(test_bucket_name)
        minio_client.upload_file(test_bucket_name, test_file_path, test_object_name)

        minio_client.delete_object(test_bucket_name, test_object_name)
        objects = minio_client.list_objects(test_bucket_name)
        assert test_object_name not in objects
    finally:
        minio_client.delete_bucket(test_bucket_name)

def test_enable_versioning(minio_client, test_bucket_name):
    try:
        minio_client.create_bucket(test_bucket_name)
        minio_client.enable_versioning(test_bucket_name)
        # There is no direct way to assert versioning enabled using boto3
        # However, no exceptions indicate success
    finally:
        minio_client.delete_bucket(test_bucket_name)

def test_get_object_metadata(minio_client, test_bucket_name, test_file_path, test_object_name):
    try:
        minio_client.create_bucket(test_bucket_name)
        minio_client.upload_file(test_bucket_name, test_file_path, test_object_name)

        metadata = minio_client.get_object_metadata(test_bucket_name, test_object_name)
        assert metadata is not None
    finally:
        minio_client.delete_object(test_bucket_name, test_object_name)
        minio_client.delete_bucket(test_bucket_name)

def test_copy_object(minio_client, test_bucket_name, test_file_path, test_object_name):
    destination_bucket_name = "destination-bucket"
    try:
        minio_client.create_bucket(test_bucket_name)
        minio_client.create_bucket(destination_bucket_name)
        minio_client.upload_file(test_bucket_name, test_file_path, test_object_name)

        minio_client.copy_object(test_bucket_name, test_object_name, destination_bucket_name, test_object_name)
        destination_objects = minio_client.list_objects(destination_bucket_name)
        assert test_object_name in destination_objects
    finally:
        minio_client.delete_object(test_bucket_name, test_object_name)
        minio_client.delete_bucket(test_bucket_name)
        minio_client.delete_object(destination_bucket_name, test_object_name)
        minio_client.delete_bucket(destination_bucket_name)

def test_set_bucket_policy(minio_client, test_bucket_name):
    try:
        minio_client.create_bucket(test_bucket_name)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            "*"
                        ]
                    },
                    "Action": [
                        "s3:GetObject"
                    ],
                    "Resource": [
                        "arn:aws:s3:::policy-bucket/*"
                    ]
                }
            ]
        }
        minio_client.set_bucket_policy(test_bucket_name, str(policy))
        # No exception indicates success
    finally:
        minio_client.delete_bucket(test_bucket_name)
