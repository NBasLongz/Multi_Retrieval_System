import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from backend import config
from utils.video_metadata import load_video_metadata

url = "http://192.168.20.156:5601/api/v2/login"

data = {
    "username": "team006",
    "password": "123456"
}

response = requests.post(url, json=data, verify=False)

# Lấy session ID và evaluation ID từ config
session_id = config.SESSION_ID
evaluation_id = config.EVALUATION_ID

params = {
    "session": session_id
}

url = f"{config.EVAL_SERVER_URL}/api/v2/submit/{evaluation_id}"

VIDEO_METADATA = load_video_metadata(config.VIDEOS_DIR)
video = "L03_V030"
start = 15927
end = start
fps = VIDEO_METADATA.get(video, 25.0)

data = {
    "answerSets": [
        {
            "answers": [
                {
                    "mediaItemName": video,
                    "start": f"{int(float(start/fps) * 1000)}",
                    "end": f"{int(float(end/fps) * 1000)}"
                }
            ]
        }
    ]
}

response = requests.post(url, json=data, params=params)

print(response.status_code)
print(response.json())