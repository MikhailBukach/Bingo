import sys, getopt
import os.path
import MySQLdb  # http://sourceforge.net/projects/mysql-python/files/latest/download?source=files
import numpy as np
import time
import cv2
import math
from pytesser import *
from PIL import Image


def filter_numbers_only(results_in_text, num_lim=1):
    results_in_numbs = []
    for str_val in results_in_text:
        try:
            if len(str_val) <= num_lim:
                results_in_numbs.append(int(str_val))

        except ValueError:
            sys_exit_code = -1

    return results_in_numbs


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
    return cv2.warpAffine(src, rot_mat, (int(math.ceil(nw)), int(math.ceil(nh))), flags=cv2.INTER_LANCZOS4,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255, 0))


def create_blank(width, height, rgb_color=(0, 0, 0)):
    """Create new image(numpy array) filled with certain color in RGB"""
    # Create black blank image
    image = np.zeros((height, width, 3), np.uint8)

    # Since OpenCV uses BGR, convert the color first
    color = tuple(reversed(rgb_color))
    # Fill image with color
    image[:] = color

    return image


def subimage(image_name, centre, theta, width, height):
    image = cv2.cv.LoadImage(image_name)

    theta = np.deg2rad(theta)  # angle in radians

    output_image = cv2.cv.CreateImage((int(width), int(height)), image.depth, image.nChannels)
    mapping = np.array([[np.cos(theta), -np.sin(theta), centre[0]],
                        [np.sin(theta), np.cos(theta), centre[1]]])

    map_matrix_cv = cv2.cv.fromarray(mapping)

    cv2.cv.GetQuadrangleSubPix(image, output_image, map_matrix_cv)
    cv2.cv.SaveImage("patched.jpg", output_image)

    cv2_im = cv2.imread("patched.jpg")

    d = 10
    blank_image = create_blank(width + d * 2, height + d * 2, (255, 255, 255))
    h, w, c = cv2_im.shape
    blank_image[d:h + d, d:w + d] = cv2_im
    # normal_clone = cv2.seamlessClone(cv2_im, blank_image, mask, center, cv2.NORMAL_CLONE)
    return blank_image


'''
im = cv2.imread('im_rotated_to_90_1.jpg')
rotated = rotate_about_center(im,(12, 21),-30)
cv2.imshow("rotate_about_center",rotated)

rotated1 = rotate_about_center1(im,-30)
cv2.imshow("rotate_about_center1",rotated1)
cv2.waitKey(0)

source_image_name = 'im_rotated_to_90_1.jpg'
im = cv2.imread(source_image_name)

h, w, c = im.shape
print im.shape

blank_image = create_blank(100, 100, (255, 255, 255))
blank_image[1:h + 1, 1:w + 1] = im
cv2.imshow("blank_image", blank_image)
cv2.waitKey(0)
'''

source_image_name = 'im_crop_rotated_1.jpg'
im = cv2.imread(source_image_name)
gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
_, thresh = cv2.threshold(blur, 170, 255, cv2.THRESH_BINARY)

cv2.imshow("thresh", thresh)
cv2.waitKey(0)

contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
hierarchy = hierarchy[0]

print len(contours)
i = 0
result_list = []

for component in zip(contours, hierarchy):
    currentContour = component[0]
    currentHierarchy = component[1]

    if currentHierarchy[3] == 0:  # cv2.contourArea(currentContour) > 50: #
        rect = cv2.minAreaRect(currentContour)
        # print rect
        ((x1, y1), (w1, h1), angle) = rect

        print "isContourConvex", cv2.isContourConvex(currentContour)

        patch = subimage(source_image_name, (x1, y1), angle, w1, h1)

        patched_name = 'patch' + str(i) + '.jpg'

        cv2.imwrite(patched_name, patch)

        if patch.shape[0] > patch.shape[1]:
            # print patch.shape
            txt = read_image(patched_name)
            result_list.append(txt)

        degrees = [90, 180, 270]

        for index in range(len(degrees)):

            new_im_name = "patch_" + str(degrees[index]) + "_" + str(i) + ".jpg"

            patch_rotated = rotate_about_center(patch, degrees[index])
            cv2.imwrite(new_im_name, patch_rotated)


            # Text recognition
            if patch_rotated.shape[0] > patch_rotated.shape[1]:
                txt = read_image(new_im_name)
                result_list.append(txt)

        box = cv2.cv.BoxPoints(rect)
        box = np.int0(box)
        # print box
        cv2.drawContours(im, [box], 0, (0, 0, 255), 2)
        i += 1

print result_list
print filter_numbers_only(result_list)
cv2.imshow("rotate_about_center1", im)
cv2.waitKey(0)
