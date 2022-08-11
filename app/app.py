import json
import os


def handler(event, context):
    os.system(f"blender -b -P script.py -- {event.get('blend_in', '/tmp/test.stl')} {event.get('highres_out', '/tmp/test.highres.glb')} {event.get('lowres_out', '/tmp/test.lowres.glb')} {event.get('scale', 1)} {event.get('shouldSmooth', 0)}")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": 'ok'})
    }
