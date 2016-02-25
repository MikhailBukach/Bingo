from Tkinter import *
import tkFont
import subprocess
from PIL import ImageTk, Image
from bingo_config import *
from bingo import *
import os
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import mp709
# import urllib.request
import urllib2
from datetime import datetime

game_id = 0


# from datetime import datetime
# from datetime import timedelta

# def callback_threaded(label):
#     threading.Thread(target=read_number(label)).start()
def controls_info():
    global gui
    state = ("off","on")
    control = mp709.relaysControl()
    rels = control.enumerateRelays()
    inf_str = ""
    for ctrl in rels:
        inf = ctrl.getInfo()
        inf_str =  inf_str + " " + str(inf['id']) + ":" + str(state[int(ctrl.getPort())]) + "  "

        print inf['id'], ":", state[int(ctrl.getPort())]

    gui.update_top_center(inf_str)

def switch_dev(id, state):
    try:
        control = mp709.relaysControl()
        control.setId(id)
        control.setState(state)
        control.main()

    except:
        pass


def update_game_id():
    global gui
    game_id = get_game_id()
    gui.update_top_left("Game: " + str(game_id))


def start_new_game():
    try:
        response = urllib2.urlopen(start_new_game_url)
        # print response.info()
        # html = response.read()
        update_game_id()
    except:
        pass


def fetch_form_db():
    global gui
    try:
        db = get_connection()

        # you must create a Cursor object. It will let
        #  you execute all the queries you need
        cur = db.cursor()

        # Use all the SQL you like
        cur.execute("SELECT WinNumber FROM timer WHERE 1 = 1 ORDER BY StartTime DESC LIMIT 30")
        # db.commit()


        # print all the first cell of all the rows
        gui.listbox.delete(0, END)
        for row in cur.fetchall():
            gui.listbox.insert(END, row[0])
        gui.listbox.select_set(0)
        db.close()


    except MySQLdb.Error, e:
        print "MySQL ERROR:", e


def get_game_id():
    global gui
    global game_id

    try:
        db = get_connection()

        cur = db.cursor()

        # Use all the SQL you like
        cur.execute("SELECT timer_id FROM timer WHERE status = 0")

        for row in cur.fetchall():
            game_id = row[0]

        db.close()

        return game_id
    except MySQLdb.Error, e:
        print "MySQL ERROR:", e
        return game_id


def update_labels(action, t='0'):
    global attempt

    gui.update_status(action.upper())

    gui.update_countdown(t)

    if attempt > 1:
        gui.update_attempt(str(attempt) + '/' + str(attempts_limit), "darkred")
    else:
        gui.update_attempt("NEXT:")


def tick():
    global gui
    global start_time
    global step_id
    global attempt

    if not started:
        gui.update_status('Ready')
        gui.update_countdown('0')
        if gui.listbox.size() < 1:
            fetch_form_db()
    else:
        action, delay = steps[step_id]

        time_dif = int(time.clock() - start_time)

        update_labels(action, str(delay - time_dif))

        if delay - time_dif <= 0:
            time_dif = delay
            update_labels(action)

            if not busy:
                run_action(action)
                if step_id == len(steps) - 1:
                    step_id = 0
                else:
                    step_id += 1
                start_time = time.clock()


def run_action(action):
    busy = True
    gui.update_status(action.upper(), "red")
    print datetime.now().strftime('%H:%M:%S'), "Running action:", action

    if action == 'start_new_game':
        start_new_game()

    if action == 'readnum':
        run_read_num()

    if action == 'photo':
        run_take_photo()

    if action == 'all_dev_off':
        switch_dev(dev_shuffle, "off")
        switch_dev(dev_pickup, "off")
        switch_dev(dev_blow, "off")

    if action == 'shuffle_on':
        switch_dev(dev_shuffle, "on")

    if action == 'shuffle_off':
        switch_dev(dev_shuffle, "off")

    if action == 'pickup_on':
        switch_dev(dev_pickup, "on")

    if action == 'pickup_off':
        switch_dev(dev_pickup, "off")

    if action == 'blow_on':
        switch_dev(dev_blow, "on")

    if action == 'blow_off':
        switch_dev(dev_blow, "off")

    busy = False
    controls_info()


def run_take_photo():
    global camera_image
    global images_folder

    try:
        # args = [take_image_exec]
        # proc = subprocess.Popen(args)
        # retcode = proc.wait()

        im = cv2.imread(camera_image)
        img_height, img_width, a = im.shape

        if img_width > 1000:
            im = cv2.resize(im, (0, 0), fx=0.5, fy=0.5)
            cv2.imwrite(images_folder + "resized.jpg", im)
            gui.update_image(images_folder + "resized.jpg")
        else:
            gui.update_image(camera_image)

    except:
        pass


def run_read_num():
    global gui
    global steps
    global step_id
    global attempt
    global attempts_limit
    global camera_image
    global images_folder
    global start_time

    res_numbr = read_win_number(camera_image, images_folder + "final.jpg")
    fetch_form_db()

    if res_numbr == -1 and attempt < attempts_limit:
        steps = list(sequence_1)
        attempt += 1
        step_id = -1

    if res_numbr == -2:
        attempt = 1
        steps = list(sequence_2)
        step_id = -1

    if res_numbr >= 0:
        gui.update_image(images_folder + "final.jpg")
        put_image_to_db(images_folder + "final.jpg")
        attempt = 1
        steps = list(main_sequence)
        step_id = -1


def put_image_to_db(image_name):
    im = cv2.imread(image_name)
    cv2.imwrite(images_folder + str(game_id) + ".jpg", im)


def start_stop(label):
    global thresh_val
    global scheduler
    global started
    global start_time

    if not started:
        if len(steps) < 1:
            reset_game()
        start_time = time.clock()
        started = True
        gui.btn_start_stop.config(text="Stop")
        gui.btn_start_stop.config(fg="darkred")
    else:
        started = False
        start_time = 0
        gui.btn_start_stop.config(text="Start")
        gui.btn_start_stop.config(fg="darkgreen")


def reset_game():
    global steps
    global start_time
    global started
    global step_id

    steps = list(main_sequence)
    step_id = 0
    start_time = 0
    started = True


# class BingoTkApp(threading.Thread):
class BingoTkApp():
    def __init__(self):
        self.end_item = None
        self.root = Tk()
        self.root.wm_title("Bingo GUI")

        # self.font = tkFont.nametofont(self.img_box['font'])
        self.font = tkFont.Font(family="Helvetica", size=14, weight="bold")

        self.row0 = Frame(self.root)

        # TOP RIGHT
        self.lbl_top_rightest = Label(self.row0, width=10, height=2, text='', font=(self.font['family'], 14, 'bold'),
                                      fg="darkgreen", bg='grey')
        self.lbl_top_rightest.pack(side=RIGHT, fill=X, expand="yes")

        # TOP RIGHT
        self.lbl_top_right = Label(self.row0, width=10, height=2, text='', font=(self.font['family'], 14, 'bold'),
                                   fg="darkgreen", bg='darkgrey')
        self.lbl_top_right.pack(side=RIGHT, fill=X, expand="yes")

        # TOP CENTER
        self.lbl_top_center = Label(self.row0, width=30, height=2, text='', font=(self.font['family'], 14, 'bold'),
                                    fg="darkgreen", bg='grey')

        self.lbl_top_center.pack(side=RIGHT, fill=X, expand="yes")

        # TOP LEFT
        self.lbl_top_left = Label(self.row0, width=10, height=2, text='',
                                  font=(self.font['family'], 14, 'bold'),
                                  fg="darkgreen", bg='darkgrey')
        self.lbl_top_left.pack(side=RIGHT, fill=X, expand="yes")

        self.row0.pack(side=TOP, fill=BOTH)

        self.row1 = Frame(self.root)

        self.img = ImageTk.PhotoImage(Image.open(default_image))
        self.img_box = Label(self.row1, image=self.img, width=60, height=60, bg='grey')
        self.img_box.pack(side=LEFT, fill=BOTH, expand="yes")

        # self.scrollbar = Scrollbar(self.row1, orient=VERTICAL)
        # listbox = Listbox(frame, yscrollcommand=scrollbar.set)
        # scrollbar.config(command=listbox.yview)
        # scrollbar.pack(side=RIGHT, fill=Y)
        # listbox.pack(side=LEFT, fill=BOTH, expand=1)

        self.scrollbar = Scrollbar(self.row1, orient=VERTICAL, bg='darkgrey')
        self.listbox = Listbox(self.row1, width=3, height=6, yscrollcommand=self.scrollbar.set,
                               font=(self.font['family'], 32, 'bold'), fg="darkgreen", bg='darkgrey')
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.pack(fill=Y, expand="yes")
        # self.listbox.insert(END, "Ready to the game")

        self.row1.pack(side=TOP, fill=BOTH)

        self.row2 = Frame(self.root)

        # Read number button
        self.btn_start_stop = Button(self.row2, text='Start', width=10,
                                     font=(self.font['family'], 14, 'bold'), fg="darkgreen",
                                     command=(lambda e=self: start_stop(e)))
        self.btn_start_stop.pack(side=RIGHT, fill=BOTH)

        # Countdown Label
        self.lbl_countdown = Label(self.row2, width=10, height=2, text='', font=(self.font['family'], 14, 'bold'),
                                   fg="darkgreen", bg='darkgrey')
        self.lbl_countdown.pack(side=RIGHT, fill=X, expand="yes")

        # Action Label
        self.lbl_status = Label(self.row2, width=30, height=2, text='Ready', font=(self.font['family'], 14, 'bold'),
                                fg="darkgreen", bg='grey')

        self.lbl_status.pack(side=RIGHT, fill=X, expand="yes")

        # Attempt Label
        self.lbl_attempt = Label(self.row2, width=10, height=2, text='', font=(self.font['family'], 14, 'bold'),
                                 fg="darkgreen", bg='darkgrey')
        self.lbl_attempt.pack(side=LEFT, fill=X, expand="yes")

        self.row2.pack(side=TOP, fill=BOTH)

        # threading.Thread.__init__(self)

    def update_top_center(self, status_text, color="darkgreen"):
        self.lbl_top_center.config(text=status_text)
        self.lbl_top_center.config(fg=color)

    def update_top_left(self, status_text, color="darkgreen"):
        self.lbl_top_left.config(text=status_text)
        self.lbl_top_left.config(fg=color)

    def update_image(self, image_name):
        self.img = ImageTk.PhotoImage(Image.open(image_name))
        self.img_box.config(image=self.img)

    def update_status(self, status_text, color="darkgreen"):
        self.lbl_status.config(text=status_text)
        self.lbl_status.config(fg=color)

    def update_countdown(self, status_text, color="darkgreen"):
        self.lbl_countdown.config(text=status_text)
        self.lbl_countdown.config(fg=color)

    def update_attempt(self, status_text, color="darkgreen"):
        self.lbl_attempt.config(text=status_text)
        self.lbl_attempt.config(fg=color)

    def run(self):
        scheduler.start()
        self.root.mainloop()


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(tick, 'interval', seconds=1, id='job_timer_tick')
    # scheduler.add_job(run_read_num,  'interval', seconds=1, id='job_run_read_num')


    gui = BingoTkApp()
    gui.run()
    scheduler.shutdown()

    # try:
    #     # This is here to simulate application activity (which keeps the main thread alive).
    #     while True:
    #         if gui is None:
    #             gui = BingoTkApp()
    #             gui.run()
    #
    #         time.sleep(2)
    # except (KeyboardInterrupt, SystemExit):
    #     # Not strictly necessary if daemonic mode is enabled but should be done if possible
    #     scheduler.shutdown()
