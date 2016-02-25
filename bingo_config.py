import MySQLdb

# Settings for Bingo.py
start_time = 0

hough_circles_dp = 1.4
hough_circles_min_dist = 300

thresh_val = 170
reset_thresh_val = 60
contour_distance = 10
ignor_hierarchy = 1
min_contour_area = 200
max_contour_area = 2000
images_folder = 'images/'

min_hull_area = 1300
max_hull_area = 4000

debug_mode = 0

rotate_image = 1
rotate_image_clockwize = 1

# Settings for bingo_gui.py

start_new_game_url = 'http://localhost/bingo'
start_time = 0
gui = None
scheduler = None
started = False
busy = False
delay = 0
steps = []

main_sequence = [("main sequence", 1), ("pickup_off", 1), ("shuffle_off", 1), ("blow_off", 1),
                 ("start_new_game", 5), ("shuffle_on", 1),
                 ("shuffle_off", 5), ("pickup_on", 3),
                 ("photo", 1), ("readnum", 1)]

sequence_1 = [("sequence -1", 2), ("blow_on", 1), ("blow_off", 2), ("photo", 3), ("readnum", 2)]

sequence_2 = [("sequence -2", 2), ("pickup_off", 1), ("shuffle_off", 1), ("blow_off", 1), ("shuffle_on", 2),
              ("shuffle_off", 5),
              ("pickup", 3), ("photo", 3), ("readnum", 2)]
attempt = 1
attempts_limit = 3
step_id = 0
default_image = "images/no-image.png"
camera_image = "camera/camera.jpg"
take_image_exec = "get_picture.bat"

dev_shuffle = 3906
dev_pickup = 3937
dev_blow = 3779


def get_connection():
    try:
        db = MySQLdb.connect(host="localhost",  # your host, usually localhost
                             user="root",  # your username
                             passwd="",  # your password
                             db="bingo")  # name of the data base

        return db

    except MySQLdb.Error, e:
        print "MySQL ERROR:", e
