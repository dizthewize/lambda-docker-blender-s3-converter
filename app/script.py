from datetime import datetime
import boto3
import botocore
import bpy, bmesh # type: ignore
import sys
import time

# get cli args
argv = sys.argv
argv = argv[argv.index("--") + 1:] # get all args after "--"
blend_in = argv[0]
highres_out = argv[1]
lowres_out = argv[2]
scale = argv[3]
yRotate = argv[4]
shouldSmooth = argv[4]

tokenDecRatio = 0.5 # .5  = 50% reduction in polys
tokenDecAngle = 0.04363325 # 0.0872665 is 4 degrees
correctZ = False

s3 = boto3.resource("s3")
BUCKET_NAME = "models.tabulasono.com"
BLEND_FILE_PATH = f"/tmp/test.stl" ## filename is test.stl

try:
    s3.Bucket(BUCKET_NAME).download_file("test/test.stl", BLEND_FILE_PATH)
    print("-- S3 Download Complete...")
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("-- Error downloading render file")
    else:
        raise

try:
  # delete any meshes (silly cube)
  print("\n -- Deleting Meshes")
  bpy.ops.object.select_by_type(type='MESH')
  bpy.ops.object.delete()
except:
  print("\n Error deleting meshes...")

if blend_in.endswith('.stl'):
  print("\n -- Importing STL File")
  bpy.ops.import_mesh.stl(filepath=blend_in)
if blend_in.endswith('.glb'):
  print("\n -- Importing GLB File")
  bpy.ops.import_scene.gltf(filepath=blend_in)

try:
  bpy.ops.object.mode_set(mode='OBJECT')
except:
  pass
# deselect all objects
bpy.ops.object.select_all(action='DESELECT')

try:
  # delete any cameras
  print("\n -- Deleting Cameras")
  bpy.ops.object.select_by_type(type='CAMERA')
  bpy.ops.object.delete()
except:
  print("\n Error deleting cameras...")

try:
  # delete any lights
  print("\n -- Deleting Lights")
  bpy.ops.object.select_all(action='DESELECT')
  bpy.ops.object.select_by_type(type='LIGHT')
  bpy.ops.object.delete()
except:
  print("\n Error deleting lights...")

# select all the meshes and merge them
print("\n -- Selecting meshes")
obs = []
for ob in bpy.context.scene.objects:
  if ob.type == 'MESH':
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    obs.append(ob)

ctx = bpy.context.copy()
ctx['active_object'] = obs[0]
ctx['selected_editable_objects'] = obs

# print("\n -- Merging meshes")
bpy.ops.object.join(ctx)

# TODO: - Rotate if necessary
if yRotate != "0":
  print("\n -- Rotating object by " + yRotate)

# TODO: - Scale if necessary
if scale != "1":
  print("\n -- Scaling object to " + scale)

if correctZ:
  try:
    print("\n -- Correcting Z")
    minz = 0.00
    for ob in bpy.context.scene.objects:
      if ob.type == 'MESH':
        merged = ob
        mx = ob.matrix_world
        minz = min((mx @ v.co)[2] for v in ob.data.vertices)
        mx.translation.z -= minz
  except:
    print("\n Error plopping to floor...")

# Smooth and decimate the mesh
print("\n -- Selecting meshes")
obs = []
for ob in bpy.context.scene.objects:
  if ob.type == 'MESH':
    for f in ob.data.polygons:
      if shouldSmooth == '1':
        f.use_smooth = True
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    obs.append(ob)

ctx = bpy.context.copy()
ctx['active_object'] = obs[0]
ctx['selected_editable_objects'] = obs

try:
  bpy.ops.object.mode_set(mode='EDIT')
except:
  pass

print("\n -- Exporting highres")
bpy.ops.export_scene.gltf(filepath=highres_out, export_format='GLB', export_yup=1)

print("\n -- Decimating meshes")
try:
  bpy.ops.object.modifier_add(type='DECIMATE')
  bpy.context.object.modifiers["Decimate"].decimate_type = 'DISSOLVE'
  bpy.context.object.modifiers["Decimate"].angle_limit = tokenDecAngle
  bpy.ops.object.modifier_add(type='DECIMATE')
  bpy.context.object.modifiers["Decimate.001"].ratio = tokenDecRatio
except Exception as e:
  print("\n Error setting up modifiers")
  print("\n " + str(e))

try:
  bpy.ops.object.mode_set(mode='OBJECT')
except:
  pass

try:
  bpy.ops.object.modifier_apply(modifier="Decimate")
  bpy.ops.object.modifier_apply(modifier="Decimate.001")
except Exception as e:
  print("\n Error applying modifiers")
  print("\n " + str(e))

bpy.ops.export_scene.gltf(filepath=lowres_out, export_format='GLB', export_yup=1)

# TODO: Add if statement to check for stl or glb file
# TODO: upload file as lowres or highres depending on if statement

try:
  s3.Bucket(BUCKET_NAME).upload_file(f"/tmp/test.stl", f"test/{datetime.now().strftime('%Y_%m_%d-%I:%M:%S_%p')}_test.stl")
  print("-- S3 Upload Complete...")
except botocore.exceptions.ClientError as e:
  if e.response['Error']:
      print("-- Error uploading render file")
  else:
      raise
