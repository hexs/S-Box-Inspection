import numpy as np
import cv2


def perpendicular_line(xy1, xy2):
    midpoint = (xy1 + xy2) / 2
    delta_y = xy2[1] - xy1[1]
    delta_x = xy2[0] - xy1[0]

    if delta_x == 0:
        slope_perpendicular = 0
        intercept = midpoint[1]
    else:
        # m = dy/dx
        slope = delta_y / delta_x
        slope_perpendicular = -1 / slope

        # y = mx + c
        # c = y - mx
        intercept = midpoint[1] - slope_perpendicular * midpoint[0]

    return slope_perpendicular, intercept


def intersection_point(line1, line2):
    m1, c1 = line1
    m2, c2 = line2

    if m1 == m2:
        raise ValueError("The lines are parallel and do not intersect.")

    x = (c2 - c1) / (m1 - m2)
    y = m1 * x + c1

    return np.array([x, y])


def rotate(image, phi, center):
    if abs(phi) < 0.01:
        print(f"func rotate, phi={phi}, don't rotate, phi<0.01")
    else:
        print(f'func rotate, phi={phi}')
        h, w = image.shape[:2]
        rotate_matrix = cv2.getRotationMatrix2D(center=center.tolist(), angle=phi, scale=1)
        image = cv2.warpAffine(src=image, M=rotate_matrix, dsize=(w, h))
    return image


def fine_mark(image, mark, xywh):
    WH_ = np.array(image.shape[1::-1])
    wh_ = np.array(mark.shape[1::-1])
    XY = xywh[:2]
    WH = xywh[2:]
    XY1_ = ((XY - WH / 2) * WH_).astype(int)
    XY2_ = ((XY + WH / 2) * WH_).astype(int)
    max_score = 0
    xy_ = None

    result = cv2.matchTemplate(image[XY1_[1]:XY2_[1], XY1_[0]:XY2_[0]], mark, cv2.TM_CCOEFF_NORMED)
    loc = np.where(result > 0.7)
    for pt in zip(*loc):
        scrolling_xy_ = pt[::-1]
        if max_score < result[*pt]:
            max_score = result[*pt]
            xy_ = XY1_ + scrolling_xy_ + wh_ / 2

    if type(xy_) != type(None):
        xy = xy_ / WH_
        return xy


def adj_image(image, model_name, mark_dict):
    h, w, _ = image.shape

    mark1 = cv2.imread(f'data/{model_name}/m1.png')
    mark2 = cv2.imread(f'data/{model_name}/m2.png')
    xy1 = mark_dict['m1']['xy']
    xy2 = mark_dict['m2']['xy']
    m1_xy = fine_mark(image, mark1, mark_dict['m1']['xywh_around'])
    m2_xy = fine_mark(image, mark2, mark_dict['m2']['xywh_around'])
    # print('m1_xy =', m1_xy, '  m2_xy =', m2_xy)

    if m1_xy is None or m2_xy is None:
        print('no mark point_be')
        return image
    else:
        # ------ rotate and move ------
        xy1_ = (xy1 * [w, h])
        xy2_ = (xy2 * [w, h])
        m1_xy_ = (m1_xy * [w, h])
        m2_xy_ = (m2_xy * [w, h])
        center_for_rotate = (m1_xy_ + m2_xy_) // 2

        default_phi = np.degrees(np.arctan2((xy2_[1] - xy1_[1]), (xy2_[0] - xy1_[0])))
        phi = np.degrees(np.arctan2((m2_xy_[1] - m1_xy_[1]), (m2_xy_[0] - m1_xy_[0])))

        # print((m1_xy_, xy1_))
        # print(m2_xy_, xy2_)
        line1 = perpendicular_line(m1_xy_, xy1_)
        line2 = perpendicular_line(m2_xy_, xy2_)
        intersection = intersection_point(line1, line2)

        print('default_phi', default_phi)
        print('phi', phi)
        image_ro = rotate(image, (phi - default_phi), center=np.array(intersection))
        # image_ro = rotate(image, (phi - default_phi), center=np.array(center_for_rotate))

        return image_ro

        # ------ move ------
        # m1_xy = fine_mark(image, mark1, mark_dict['m1']['xywh_around'])
        # m2_xy = fine_mark(image, mark2, mark_dict['m2']['xywh_around'])
        # if point_m1_af is None or point_m2_af is None:
        #     print('no mark point_af <<<<<')
        #     return
        #
        # x = (frame.marks['m1'].xpx(h, w) - point_m1_af[0] + frame.marks['m2'].xpx(h, w) - point_m2_af[0]) // 2
        # y = (frame.marks['m1'].ypx(h, w) - point_m1_af[1] + frame.marks['m2'].ypx(h, w) - point_m2_af[1]) // 2
        # image = overlay(image, image_ro, (x, y))
        # return image


if __name__ == '__main__':
    ...
