import os, errno
import boto3

def download_keys(prefix, bucket = 'bgse-internet-study'):
    s3 = boto3.client('s3')
    keys = [file['Key'] for file in s3.list_objects_v2(Bucket = bucket, Prefix = prefix)['Contents'] ]
    for key in keys:
        if not os.path.exists(os.path.dirname(key)):
            try:
                os.makedirs(os.path.dirname(key))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        with open(key, "w") as f:
            s3.download_fileobj(bucket, key, f)


# download_keys('MESO')
# download_keys('data')
