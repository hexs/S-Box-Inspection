import os.path
import time
import numpy as np
from hexss import json_load
from hexss.image import get_image_from_url, overlay, crop_img
from hexss.modbus.serial.robot import Robot


def main(data, robot: Robot):
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

        if data['robot step'] == 'stop':
            data['robot step'] = 'capture error'

        if data['robot step'] == 'capture':
            images = np.zeros([h, w, 3], dtype=np.uint8)
            errors = []
            for k, v in robot_data['robot'].items():
                for slave, position in zip(robot.slaves, v['position']):
                    slave.move(int(position * 100))
                error = robot.wait(error_emergency=True, error_servo_off=True, error_paused=True)
                errors.append(error)

                if error == 'servo off':
                    data['robot step'] = 'capture error'
                    break

                if v['image_data'].get('no_capture'):
                    continue

                time.sleep(0.6)
                while True:
                    image = get_image_from_url(image_url)
                    if image is not None:
                        break
                    time.sleep(1)

                v['image_data']['img'] = image
                img = crop_img(v['image_data']['img'], v['image_data']['img xywhn'])
                overlay_xy = v['image_data']['overlay_xy']
                overlay(images, img, overlay_xy)

            e = robot.is_any_emergency()
            s = robot.is_any_servo_off()
            p = robot.is_any_paused()
            print(errors, '|', e, s, p)
            if e or s or p:
                data['robot step'] = 'capture error'

            elif any(status in errors for status in ['paused', 'servo off', 'emergency']):
                data['robot step'] = 'capture error'
            else:
                data['images'] = images
                data['robot step'] = 'capture ok'
                robot.move_to(0)
            print(f'capture {data["robot step"]}')
