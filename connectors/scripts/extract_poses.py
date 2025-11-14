import sys
import json
import numpy as np

input_json = sys.stdin.read()
data = json.loads(input_json)

input_data = data.get('input')
if isinstance(input_data, dict) and 'poses' in input_data:
    poses = input_data['poses']
    output = poses
else:
    output = input_data

result = {'result': output}
print(json.dumps(result))
