from datetime import datetime
import os
import sys

import boto3
import botocore
import bpy

BUCKET_NAME = "converter-on-lambda-bucket"
KEY = "scenes/scene.blend"
BLEND_FILE_PATH = "/tmp/scene.blend"

argv = sys.argv
argv = argv[argv.index("--") + 1:]
s3 = boto3.resource("s3")
filename = f"{datetime.now().strftime('%Y_%m_%d-%I:%M:%S_%p')}.png"

def list_s3_files_using_resource():
    """
    This functions list files from s3 bucket using s3 resource object.
    :return: None
    """
    s3_resource = boto3.resource("s3")
    s3_bucket = s3_resource.Bucket(BUCKET_NAME)
    files = s3_bucket.objects.all()
    for file in files:
        print(f"S3 bucket resource: {file}")

list_s3_files_using_resource()

try:
    s3.Bucket(BUCKET_NAME).download_file(KEY, BLEND_FILE_PATH)
    print(f"s3 file downloaded at {datetime.now().strftime('%Y_%m_%d-%I:%M:%S_%p')}")
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("The object does not exist.")
    else:
        raise

bpy.ops.wm.open_mainfile(filepath="/tmp/scene.blend", load_ui=False)
bpy.context.scene.render.filepath = f"/tmp/{filename}"
bpy.context.scene.render.resolution_x = int(argv[0])
bpy.context.scene.render.resolution_y = int(argv[1])
## Enables headless rendering ##
bpy.context.scene.render.engine = 'CYCLES'
bpy.ops.render.render(write_still = True)

try:
    s3.Bucket(BUCKET_NAME).upload_file(f"/tmp/{filename}", f"renders/{filename}")
    print(f"s3 file uploaded at {datetime.now().strftime('%Y_%m_%d-%I:%M:%S_%p')}")
except botocore.exceptions.ClientError as e:
    if e.response['Error']:
        print("Error uploading render file.")
    else:
        raise
