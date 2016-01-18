import sys
import numpy as np
import cv2
import math

from pytesser import *
from PIL import Image

thresh_val = 45
contour_distance = 50
ignor_hierarchy = 0
contour_area = 2500

rotate_image = 1
rotate_image_clockwize = 1

img_name = 'IMG_20151225_152224.jpg'
img_name = 'IMG_20151225_152236.jpg'
#img_name = 'IMG_20151225_152213.jpg'
#img_name = '3480087_7943.jpg'
#img_name = 'Captcha.png'

def is_numeric(s):
    # Returns True for all non-unicode numbers
    try:
        s = s.decode('utf-8')
    except:
        return False

    try:
        float(s)
        return True
    except:
        return False

def read_image(image_name = 'croped.jpg'):
    img = Image.open(image_name)
    txt = image_to_string(img)
    txt = txt.strip('\n')
    txt = txt.strip()
    txt = txt.lstrip()
    return txt

def find_if_close(cnt1, cnt2):
    row1, row2 = cnt1.shape[0], cnt2.shape[0]
    for i in xrange(row1):
        for j in xrange(row2):
            dist = np.linalg.norm(cnt1[i] - cnt2[j])
            if abs(dist) < contour_distance :
                return True
            elif i == row1 - 1 and j == row2 - 1:
                return False

def is_in_area_and_level(cnt, area, lvl):
    ct = cnt[0]
    hy = cnt[1]

    if hy[3] == 0:
        if cv2.contourArea(ct) > area:
            #print cv2.contourArea(ct) 
            return 1
    else:
        return 0
def is_in_area(cnt, area):
    ct = cnt[0]
    
    if cv2.contourArea(ct) > area:
        #print cv2.contourArea(ct) 
        return 1
    else:
        return 0
    
def filter_contours(contours, hierarchy, s = 3000, lvl = 0):
    
    if ignor_hierarchy:
        cnts = [c[0] for c in zip(contours, hierarchy) if  is_in_area(c, s) > 0]
    else:
        cnts = [c[0] for c in zip(contours, hierarchy) if  is_in_area_and_level(c, s, lvl) > 0]
    
    #print len(cnts)
    return(cnts)

def sort_contours(cnts, method = "left-to-right"):
    # initialize the reverse flag and sort index
    reverse = False
    i = 0
 
    # handle if we need to sort in reverse
    if method == "right-to-left" or method == "bottom-to-top":
        reverse = True
 
    # handle if we are sorting against the y-coordinate rather than
    # the x-coordinate of the bounding box
    if method == "top-to-bottom" or method == "bottom-to-top":
        i = 1
 
    # construct the list of bounding boxes and sort them from top to
    # bottom
    boundingBoxes = [cv2.boundingRect(c) for c in cnts]
    (cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes), key=lambda b:b[1][i], reverse=reverse))
 
    # return the list of sorted contours and bounding boxes
    return (cnts, boundingBoxes)
'''
def angle_wrt_x(A,B):
    """Return the angle between B-A and the positive x-axis.
    Values go from 0 to pi in the upper half-plane, and from 
    0 to -pi in the lower half-plane.
    """
    ax, ay = A
    bx, by = B
    return math.atan2(by-ay, bx-ax)

def dist(A,B):
    ax, ay = A
    bx, by = B
    return math.hypot(bx-ax, by-ay)
'''
def rotate_about_center(src, angle, scale=1.):
    w = src.shape[1]
    h = src.shape[0]
    rangle = np.deg2rad(angle)  # angle in radians
    # now calculate new image width and height
    nw = (abs(np.sin(rangle)*h) + abs(np.cos(rangle)*w))*scale
    nh = (abs(np.cos(rangle)*h) + abs(np.sin(rangle)*w))*scale
    # ask OpenCV for the rotation matrix
    rot_mat = cv2.getRotationMatrix2D((nw*0.5, nh*0.5), angle, scale)
    # calculate the move from the old center to the new center combined
    # with the rotation
    rot_move = np.dot(rot_mat, np.array([(nw-w)*0.5, (nh-h)*0.5,0]))
    # the move only affects the translation, so update the translation
    # part of the transform
    rot_mat[0,2] += rot_move[0]
    rot_mat[1,2] += rot_move[1]
    return cv2.warpAffine(src, rot_mat, (int(math.ceil(nw)), int(math.ceil(nh))), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255, 0))

def read_text_by_image():
    im = cv2.imread(img_name)

    im3 = im.copy()

    gray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray,(5, 5), 0)
    cv2.imwrite("blur.jpg", blur) 

    #cv2.imshow('blur',blur)
    #key = cv2.waitKey(0)
    
    #thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    _,thresh=cv2.threshold(blur, thresh_val, 255, cv2.THRESH_BINARY)
    
    cv2.imshow('thresh',thresh)
    key = cv2.waitKey(0)

    im_thresh = thresh.copy()
    #cv2.imshow('norm1',im4)


    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #print hierarchy
    hierarchy = hierarchy[0]
    #print hierarchy


    cnts = filter_contours(contours, hierarchy)
    contours = filter_contours(contours, hierarchy, contour_area)

    LENGTH = len(contours)
    status = np.zeros((LENGTH,1))

    for i, cnt1 in enumerate(contours):
        x = i    
        if i != LENGTH-1:
            for j, cnt2 in enumerate(contours[i+1:]):
                x = x + 1
                dist = find_if_close(cnt1, cnt2)
                if dist == True:
                    val = min(status[i],status[x])
                    status[x] = status[i] = val
                else:
                    if status[x] == status[i]:
                        status[x] = i + 1

    unified = []
    r_text = []
    maximum = int(status.max())+1

    #print status



    for i in xrange(maximum):
        pos = np.where(status == i)[0]
        if pos.size != 0:
            cont = np.vstack(contours[i] for i in pos)
            hull = cv2.convexHull(cont)
            unified.append(hull)

            # Angle of one of the contours
            # todo - need to calc avg angle of all joined contours
            rect = cv2.minAreaRect(contours[i])
            ((x1,y1),(w1,h1),angle) = rect
            #print rect
        
            box = cv2.cv.BoxPoints(rect)
            box = np.int0(box)
            #cv2.drawContours(im,[box],0,(0,255,0),2)

            # Bounding Rect of joined contours
            [x,y,w,h] = cv2.boundingRect(hull)
            cv2.rectangle(im,(x,y),(x+w,y+h),(0,0,255),2)

            # Print angle to the source image
            #font = cv2.FONT_HERSHEY_SIMPLEX
            #cv2.putText(im, str(int(angle)) ,(int((x+w)/2), int((y+h)/2)), font, 1,(0,0,255),2)

            # Crop joined contours image
            im_crop = im_thresh[y:y+h, x:x+w]

            # Rotate cropped image to angle
            if rotate_image < 1:
                angle = 0
            im_crop_rotated = rotate_about_center(im_crop, angle)
            cv2.imwrite("croped.jpg", im_crop_rotated)
        
            # Text recognition
            txt = read_image()
            r_text.append(txt)
        
            cv2.imshow('croped', im_crop_rotated)
            key = cv2.waitKey(0)

            degrees = [90, 180,  270]

            if rotate_image_clockwize:
                for index in range(len(degrees)):
                    #print 'angle :', degrees[index]

                    im_crop_rotated_to_angle = rotate_about_center(im_crop_rotated, degrees[index])
                    cv2.imwrite("croped.jpg", im_crop_rotated_to_angle)
            
                    #Text recognition
                    txt = read_image()
                    r_text.append(txt)

                    #cv2.imshow('rotated', im_crop_rotated_to_angle)
                    #key = cv2.waitKey(0)

        
    # Draw hull of contours
    cv2.drawContours(im, unified, -1, (0, 255, 0),2)

    #cv2.drawContours(thresh,unified,-1,255,-1)

    print r_text

    for str_val in r_text:
    
        if is_numeric(str_val):
            print 'Detected number: ', str_val

        
    print "complete"

    cv2.imshow('final', im)
    key = cv2.waitKey(0)

read_text_by_image()

