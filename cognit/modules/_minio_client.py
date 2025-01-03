from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from cognit.modules._logger import CognitLogger
import boto3

cognit_logger = CognitLogger()

class MinioClient:
    def __init__(self, endpoint_url, access_key, secret_key):
        """
        Initialize the MinIO client.

        :param endpoint_url: URL of the MinIO server (e.g., http://localhost:9000).
        :param access_key: Access key for authentication.
        :param secret_key: Secret key for authentication.
        """
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise ValueError("Invalid credentials") from e

    def create_bucket(self, bucket_name):
        """
        Create a bucket.

        :param bucket_name: Name of the bucket to create.
        """
        try:
            self.s3_client.create_bucket(Bucket=bucket_name)
            cognit_logger.info(f"Bucket '{bucket_name}' created successfully.")
        except ClientError as e:
            cognit_logger.error(f"Failed to create bucket: {e}")

    def list_buckets(self):
        """
        List all buckets.

        :return: List of bucket names.
        """
        try:
            response = self.s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response.get('Buckets', [])]
            return buckets
        except ClientError as e:
            cognit_logger.error(f"Failed to list buckets: {e}")
            return []

    def upload_file(self, bucket_name, file_path, object_name):
        """
        Upload a file to a bucket.

        :param bucket_name: Name of the bucket.
        :param file_path: Path to the local file.
        :param object_name: Name of the object in the bucket.
        """
        try:
            self.s3_client.upload_file(file_path, bucket_name, object_name)
            cognit_logger.info(f"File '{file_path}' uploaded as '{object_name}' in bucket '{bucket_name}'.")
        except ClientError as e:
            cognit_logger.error(f"Failed to upload file: {e}")

    def download_file(self, bucket_name, object_name, download_path):
        """
        Download a file from a bucket.

        :param bucket_name: Name of the bucket.
        :param object_name: Name of the object in the bucket.
        :param download_path: Local path to save the downloaded file.
        """
        try:
            self.s3_client.download_file(bucket_name, object_name, download_path)
            cognit_logger.info(f"File '{object_name}' downloaded to '{download_path}'.")
        except ClientError as e:
            cognit_logger.error(f"Failed to download file: {e}")

    def list_objects(self, bucket_name):
        """
        List all objects in a bucket.

        :param bucket_name: Name of the bucket.
        :return: List of object names.
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            objects = [obj['Key'] for obj in response.get('Contents', [])]
            return objects
        except ClientError as e:
            cognit_logger.error(f"Failed to list objects: {e}")
            return []

    def delete_object(self, bucket_name, object_name):
        """
        Delete an object from a bucket.

        :param bucket_name: Name of the bucket.
        :param object_name: Name of the object to delete.
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
            cognit_logger.info(f"Object '{object_name}' deleted from bucket '{bucket_name}'.")
        except ClientError as e:
            cognit_logger.error(f"Failed to delete object: {e}")

    def delete_bucket(self, bucket_name):
        """
        Delete a bucket. The bucket must be empty.

        :param bucket_name: Name of the bucket to delete.
        """
        try:
            self.s3_client.delete_bucket(Bucket=bucket_name)
            cognit_logger.info(f"Bucket '{bucket_name}' deleted successfully.")
        except ClientError as e:
            cognit_logger.error(f"Failed to delete bucket: {e}")

    def enable_versioning(self, bucket_name):
        """
        Enable versioning for a bucket.

        :param bucket_name: Name of the bucket.
        """
        try:
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            cognit_logger.info(f"Versioning enabled for bucket '{bucket_name}'.")
        except ClientError as e:
            cognit_logger.error(f"Failed to enable versioning: {e}")

    def get_object_metadata(self, bucket_name, object_name):
        """
        Retrieve metadata for an object.

        :param bucket_name: Name of the bucket.
        :param object_name: Name of the object.
        :return: Metadata of the object.
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_name)
            return response['Metadata']
        except ClientError as e:
            cognit_logger.error(f"Failed to retrieve metadata: {e}")
            return None

    def copy_object(self, source_bucket, source_key, destination_bucket, destination_key):
        """
        Copy an object from one bucket to another.

        :param source_bucket: Source bucket name.
        :param source_key: Source object key.
        :param destination_bucket: Destination bucket name.
        :param destination_key: Destination object key.
        """
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=destination_bucket,
                Key=destination_key
            )
            cognit_logger.info(f"Object '{source_key}' copied from '{source_bucket}' to '{destination_bucket}/{destination_key}'.")
        except ClientError as e:
            cognit_logger.error(f"Failed to copy object: {e}")

    def set_bucket_policy(self, bucket_name, policy):
        """
        Set a policy for a bucket.

        :param bucket_name: Name of the bucket.
        :param policy: Policy document as a JSON string.
        """
        try:
            self.s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policy)
            cognit_logger.info(f"Policy set for bucket '{bucket_name}'.")
        except ClientError as e:
            cognit_logger.error(f"Failed to set bucket policy: {e}")
