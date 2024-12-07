import os.path
import time
import logging
import numpy as np
from hexss import json_load
from hexss.image import get_image_from_url, overlay, crop_img
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_request(url, endpoint, method='post', **kwargs):
    try:
        response = getattr(requests, method)(f"{url}/api/{endpoint}", **kwargs)
        response.raise_for_status()
        logger.info(f"{endpoint.capitalize()} request sent successfully")
        return response.json() if method == 'get' else None
    except requests.RequestException as e:
        logger.error(f"Error sending {endpoint} request: {e}")
        return None


def move_and_capture(row, robot_url, image_url):
    send_request(robot_url, "move_to", json={"row": row})
    old_res = ["1", "2", "3", "4", "5"]
    while True:
        res = send_request(robot_url, "current_position", method="get")
        old_res.append(res)
        old_res.remove(old_res[0])
        if old_res[0] == old_res[1] == old_res[2] == old_res[3] == old_res[4]:
            break

    time.sleep(2)
    return get_image_from_url(image_url)


def get_qr_code():
    ...


def main(data):
    robot_url = data['config']['robot_url']
    image_url = data['config']['image_url']
    projects_dir = data['projects_directory']
    model_name_dir = os.path.join(projects_dir, f"auto_inspection_data__{data['model_name']}")
    robot_data = json_load(os.path.join(model_name_dir, 'robot pos.json'))
    w, h = robot_data['img wh']

    while data['play']:
        time.sleep(0.1)
        if data['robot capture'] == 'capture':
            print('robot capture = capture')
            images = np.zeros([h, w, 3], dtype=np.uint8)

            for k, v in robot_data['robot'].items():
                print(int(k), v)
                v['image_data']['img'] = move_and_capture(int(k), robot_url, image_url)
                img = crop_img(v['image_data']['img'], v['image_data']['img xywhn'])
                overlay_xy = v['image_data']['overlay_xy']
                overlay(images, img, overlay_xy)

            data['images'] = images
            data['robot capture'] = 'capture ok'  # *'', 'capture', 'capture ok', 'error'
            print('robot capture = capture ok')
            send_request(robot_url, "move_to", json={"row": 0})


if __name__ == '__main__':

    robot_url = 'http://box01:2005'
    image_url = 'http://box01:2002/image?source=video_capture&id=0'

    old_res = ["1", "2", "3", "4", "5"]
    while True:
        res = send_request(robot_url, "current_position", method="get")
        # res = requests.get(f'{robot_url}/api/current_position').text
        print(res)
        print()
        old_res.append(res)
        old_res.remove(old_res[0])
        if old_res[0] == old_res[1] == old_res[2] == old_res[3] == old_res[4]:
            break
