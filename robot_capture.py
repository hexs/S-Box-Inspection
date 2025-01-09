import os.path
import time
import logging
from pprint import pprint

import cv2
import numpy as np
from hexss import json_load
from hexss.image import get_image_from_url, overlay, crop_img
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main(data, robot):
    time.sleep(1)

    image_url = data['config']['image_url']
    projects_dir = data['projects_directory']

    while data['play']:
        time.sleep(0.1)
        if data['model_name'] == '-':
            continue

        model_name_dir = os.path.join(projects_dir, f"auto_inspection_data__{data['model_name']}")
        robot_data = json_load(os.path.join(model_name_dir, 'robot pos.json'))
        w, h = robot_data['img wh']

        if data['robot capture'] == 'capture':
            print('robot capture = capture')
            images = np.zeros([h, w, 3], dtype=np.uint8)

            for k, v in robot_data['robot'].items():
                print(int(k), v)
                slaves = [1, 2, 3, 4]
                # robot.move_to(slaves=slaves, row=int(k))
                for slave, position in zip(slaves, v['position']):
                    robot.move(slave=slave, value=int(position * 100))
                robot.wait_for_target(slaves=slaves)
                # time.sleep(0.5)
                while True:
                    image = get_image_from_url(image_url)
                    if image is not None:
                        break
                    else:
                        print('get_image_from_url image is not None')
                    time.sleep(1)

                v['image_data']['img'] = image
                img = crop_img(v['image_data']['img'], v['image_data']['img xywhn'])
                overlay_xy = v['image_data']['overlay_xy']
                overlay(images, img, overlay_xy)

            data['images'] = images
            data['robot capture'] = 'capture ok'  # *'', 'capture', 'capture ok', 'error'
            print('robot capture = capture ok')
            robot.move_to(slaves=[1, 2, 3, 4], row=0)


if __name__ == '__main__':
    robot_url = 'http://box01:2005'
    image_url = 'http://box01:2002/image?source=video_capture&id=0'
