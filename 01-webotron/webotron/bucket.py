# -*- coding: utf-8 -*-

"""Bucket Manager for all the functions needed."""

from pathlib import Path
import mimetypes


class BucketManager:
    """Manage an S3 Bucket."""

    def __init__(self, session):
        """Create a BucketManager object."""
        self.s3 = session.resource('s3')

    def all_buckets(self):
        """Get an iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Get an iterator for all objects in bucket."""
        return self.s3.Bucket(bucket_name).objects.all()

    def init_bucket(self, bucket_name):
        """Create new bucket, or return existing one by name."""
        s3_bucket = self.s3.create_bucket(Bucket=bucket_name)
        return s3_bucket

    def set_policy(self, bucket):
        """Set bucket policy to be readable by everyone."""
        policy = """
        {
          "Version":"2012-10-17",
          "Statement":[{
            "Sid":"PublicReadGetObject",
              "Effect":"Allow",
              "Principal": "*",
              "Action":["s3:GetObject"],
              "Resource":["arn:aws:s3:::%s/*"
              ]
            }
          ]
        }
        """ % bucket.name
        policy = policy.strip()
        pol = bucket.Policy()
        pol.put(Policy=policy)

    def configure_website(self, bucket):
        """Configure website."""
        bucket.Website().put(WebsiteConfiguration={
            'ErrorDocument':
                {
                    'Key': 'error.html'
                },
            'IndexDocument': {
                'Suffix': 'index.html'
                }
            })

    @staticmethod
    def upload_file(bucket, path, key):
        """Upload a file to S3."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'
        key = str(key).replace("\\", "/")
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            }
        )

    def sync(self, pathname, bucket_name):
        """Upload entire directory."""
        bucket = self.s3.Bucket(bucket_name)
        root = Path(pathname).expanduser().resolve()

        def handle_directory(target):
            """Trims path."""
            for p in target.iterdir():
                if p.is_dir():
                    handle_directory(p)
                if p.is_file():
                    self.upload_file(bucket, str(p), str(p.relative_to(root)))

        handle_directory(root)
