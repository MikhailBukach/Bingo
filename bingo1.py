import cv2
import numpy as np
from os import listdir
from os.path import isfile, join
import sys, getopt
import time
import math
from pytesser import *
from PIL import Image

max_contour_area = 1000

min_contour_w = 4
min_contour_h = 4
images_folder = "images/"
contour_distance = 16


def read_image(image_name='croped.jpg'):
    img = Image.open(image_name)
    txt = image_to_string(img)
    txt = txt.strip('\n')
    txt = txt.strip()
    txt = txt.lstrip()

    cv_im = cv2.imread(image_name)
    height, width, channels = cv_im.shape
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(cv_im, txt, (int(0), int(20)), font, 0.8, (0, 0, 255), 2)

    # cv2.imshow('rotated', cv_im)
    # key = cv2.waitKey(0)
    cv2.imwrite(image_name, cv_im)
    return txt


def rotate_about_center(src, angle, scale=1.):
    w = src.shape[1]
    h = src.shape[0]
    rangle = np.deg2rad(angle)  # angle in radians
    # now calculate new image width and height
    nw = (abs(np.sin(rangle) * h) + abs(np.cos(rangle) * w)) * scale
    nh = (abs(np.cos(rangle) * h) + abs(np.sin(rangle) * w)) * scale
    # ask OpenCV for the rotation matrix
    rot_mat = cv2.getRotationMatrix2D((nw * 0.5, nh * 0.5), angle, scale)
    # calculate the move from the old center to the new center combined
    # with the rotation
    rot_move = np.dot(rot_mat, np.array([(nw - w) * 0.5, (nh - h) * 0.5, 0]))
    # the move only affects the translation, so update the translation
    # part of the transform
    rot_mat[0, 2] += rot_move[0]
    rot_mat[1, 2] += rot_move[1]

    rotated = cv2.warpAffine(src, rot_mat, (int(math.ceil(nw)), int(math.ceil(nh))), flags=cv2.INTER_LANCZOS4,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255, 100))
    '''
    d = 10

    height, width = rotated.shape
    rotated[:] = (255, 255, 255)

    blank_image = create_blank(width + d, height + d, (0, 0, 0))
    print rotated.shape,blank_image.shape
    gray = cv2.cvtColor(blank_image, cv2.COLOR_BGR2GRAY)

    d = 5
    blank_image[d:height + d, d:width + d] = rotated
    return blank_image
    '''
    return rotated


def find_if_close(cnt1, cnt2):
    row1, row2 = cnt1.shape[0], cnt2.shape[0]
    for i in xrange(row1):
        for j in xrange(row2):
            dist = np.linalg.norm(cnt1[i] - cnt2[j])
            if abs(dist) < contour_distance:
                return True
            elif i == row1 - 1 and j == row2 - 1:
                return False


def searching_progress(end_val, bar_length=20):
    for i in xrange(0, end_val):
        percent = float(i) / end_val
        hashes = '#' * int(round(percent * bar_length))
        spaces = ' ' * (bar_length - len(hashes))
        sys.stdout.write("\rSearch: [{0}] {1}%".format(hashes + spaces, int(round(percent * 100))))
        sys.stdout.flush()


def find_hulls(img, contours):
    start_time = time.clock()
    LENGTH = len(contours)

    status = np.zeros((LENGTH, 1))

    for i, cnt1 in enumerate(contours):
        x = i
        if i != LENGTH - 1:
            for j, cnt2 in enumerate(contours[i + 1:]):
                x = x + 1
                dist = find_if_close(cnt1, cnt2)
                searching_progress(x, len(contours) - 2)
                if dist == True:
                    val = min(status[i], status[x])
                    status[x] = status[i] = val
                else:
                    if status[x] == status[i]:
                        status[x] = i + 1

    print " Done."
    unified = []

    maximum = int(status.max()) + 1

    # print status

    for i in xrange(maximum):
        pos = np.where(status == i)[0]
        if pos.size != 0:
            cont = np.vstack(contours[i] for i in pos)
            hull = cv2.convexHull(cont)
            unified.append(hull)

    # Draw hull of contours
    cv2.drawContours(img, unified, -1, (0, 0, 255), 2)
    print "Complete in ", round(time.clock() - start_time, 2), "seconds"

    return img, unified


def is_in_area(cnt):
    rect = cv2.minAreaRect(cnt)
    ((x, y), (w, h), angle) = rect

    if w > min_contour_w and h > min_contour_h:
        if w * h >= min_contour_w * min_contour_h and w * h <= max_contour_area:
            # print x, y, w, h, angle
            return 1
        else:
            return 0
    else:
        return 0


def is_int(n):
    try:
        n = int(n)
        return True
    except:
        return False


def num_in_range(num, min, max):
    if min <= num <= max:
        return True
    else:
        return False


def create_blank(width, height, rgb_color=(0, 0, 0)):
    """Create new image(numpy array) filled with certain color in RGB"""
    # Create black blank image
    image = np.zeros((height, width, 3), np.uint8)

    # Since OpenCV uses BGR, convert the color first
    color = tuple(reversed(rgb_color))
    # Fill image with color
    image[:] = color

    return image


def filter_contours(contours):
    cnts = [c for c in contours if is_in_area(c) > 0]

    return (cnts)


def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)

    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)

    # return the edged image
    return edged


def find_ball(source_img):
    gray = cv2.cvtColor(source_img.copy(), cv2.COLOR_GRAY2BGR)

    height, width, channels = gray.shape

    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # canny = cv2.Canny(blur, 200, 300)
    canny = auto_canny(blur)

    thresh = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    cv2.imshow('detected circles', canny)
    cv2.waitKey(0)

    _, contours, hierarchy = cv2.findContours(canny.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print hierarchy[0]
    contours = filter_contours(contours)
    blank_image = create_blank(width, height, (255, 255, 255))

    i = 0
    for comp in zip(contours, hierarchy[0]):
        cnt, hier = comp

        rect = cv2.minAreaRect(cnt)
        ((x, y), (w, h), angle) = rect

        hull = cv2.convexHull(cnt)
        epsilon = 0.0001 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if 100 > w > 5 and 100 > h > 5:
            # cv2.drawContours(blank_image, [hull], 0, (0, 255, 0), 1)

            cv2.drawContours(blank_image, [approx], 0, (0, 0, 0), 1)

    gray = cv2.cvtColor(blank_image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    cv2.imshow('gray circles', thresh)
    cv2.waitKey(0)
    _, contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = filter_contours(contours)
    blur, hulls = find_hulls(blur, contours)
    # cv2.drawContours(blur, [approx], 0, (0, 0, 0), -1)
    # cv2.imshow('gray circles', blur)
    # cv2.waitKey(0)

    # font = cv2.FONT_HERSHEY_SIMPLEX
    # cv2.putText(blank_image, str(i + 1), (int(x), int(y)), font, 0.5, (0, 0, 0), 1)
    # print hier
    # cv2.imshow('detected circles', blank_image)
    # cv2.waitKey(0)




    # i += 1
    # blank, hulls = find_hulls(blank_image, contours)
    # cv2.imshow('detected circles', blank)
    # cv2.waitKey(0)
    r_text = []
    f_list = []
    i = 0
    for hull in hulls:
        # min Area Rect of joined contours
        rect = cv2.minAreaRect(hull)
        ((x, y), (w, h), angle) = rect
        if  w >= 30 and h >= 30:
            # box = cv2.boxPoints(rect)
            # box = np.int0(box)
            # cv2.drawContours(blank, [box], 0, (0, 255, 0), 1)

            # Bounding Rect of joined contours
            [x, y, w, h] = cv2.boundingRect(hull)
            # cv2.rectangle(blank, (x, y), (x + w, y + h), (0, 0, 255), 2)

            croped_hull = thresh[y:y + h, x:x + w]

            croped_hull_rotated = rotate_about_center(croped_hull, angle)


            i += 1

            croped_hull_rotated = rotate_about_center(croped_hull_rotated, angle)
            cv2.imshow('detected circles', croped_hull_rotated)
            cv2.waitKey(0)

            im_rotated_name = images_folder + "deg_norm_" + str(i) + ".jpg"

            cv2.imwrite(im_rotated_name, croped_hull_rotated)

            # Text recognition
            txt = read_image(im_rotated_name)
            if len(txt) == 2 and is_int(txt):
                if num_in_range(int(txt), 0, 36):
                    r_text.append(txt)
                    f_list.append(im_rotated_name)

            degrees = [90, 180, 270]

            for index in range(len(degrees)):
                new_im_name = images_folder + "deg_" + str(degrees[index]) + "_" + str(i) + ".jpg"

                im_rotated_to_angle = rotate_about_center(croped_hull_rotated, degrees[index])
                cv2.imwrite(new_im_name, im_rotated_to_angle)

                # Text recognition
                txt = read_image(new_im_name)
                if len(txt) == 2 and is_int(txt):
                    if num_in_range(int(txt), 0, 36):
                        r_text.append(txt)
                        f_list.append(new_im_name)
    #
    # i += 1

    print r_text, f_list
    # cv2.drawContours(blank_image, contours, -1, (255, 0, 0), -1)

    cv2.imshow('detected circles', blank_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


onlyfiles = [f for f in listdir("camera/") if isfile(join("camera/", f))]
for fname in onlyfiles:
    img = cv2.imread('camera/' + fname, 0)
    img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
    find_ball(img)
