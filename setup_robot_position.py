import time
from hexss.control_robot.robot import Robot
from hexss.serial import get_comport

comport = get_comport('ATEN USB to Serial', 'USB-Serial Controller')
robot = Robot(comport, baudrate=38400)
robot.move_to(0)
time.sleep(2)
robot.alarm_reset()
time.sleep(2)

x = 30
y = 76
z1 = round(150 - 6 - 110 / 1.414, 2)
z2 = round(150 - 6 - 36 / 1.441, 2)
z3 = round(150 - 6 - 78 / 1.414, 2)
y1 = y
y2 = y + 52
y3 = y - 43
position = {
    0: (0, 0, 150, 8),
    1: (x + 0, y1, z1, 0),
    2: (x + 0, y2, z2, 0),
    3: (x + 86, y1, z1, 0),
    4: (x + 86, y2, z2, 0),
    5: (x + 162, y1, z1, 0),
    6: (x + 162, y2, z2, 0),
    7: (x + 237, y1, z1, 0),
    8: (x + 237, y2, z2, 0),
    9: (x + 304, y1, z1, 0),
    10: (x + 304, y2, z2, 0),
    11: (x + 230, y3, z3, 0),

}
# for k, v in position.items():
#     print(f'{k}: {v}')
#     robot.set_to(1, k, v[0], 200, 0.1, 0.1)
#     robot.set_to(2, k, v[1], 200, 0.1, 0.1)
#     robot.set_to(3, k, v[2], 100, 0.1, 0.1)
#     robot.set_to(4, k, v[3], 100, 0.1, 0.1)

for row in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]:
    print(f'move_to {row}')
    robot.move_to(row)
    time.sleep(3)
