from Tkinter import *
import tkFont
from PIL import ImageTk, Image
from bingo import *
import os
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from datetime import timedelta

start_time = 0
gui = None
scheduler = None
started = False
busy = False
delay = 0
steps = []
base_sequence = [("photo", 1), ("delay", 10), ("shuffle", 5), ("delay", 3), ("pickup", 3), ("photo", 3), ("readnum", 2)]
sequence_1 = [("delay", 2), ("blow", 3), ("photo", 2), ("readnum", 2)]
sequence_2 = [("shuffle", 5), ("delay", 3), ("pickup", 3), ("photo", 2), ("readnum", 2)]
attempt = 1
attempts_limit = 3
step_id = 0


# def callback_threaded(label):
#     threading.Thread(target=read_number(label)).start()

def fetch_form_db():
    global gui
    try:
        db = MySQLdb.connect(host="localhost",  # your host, usually localhost
                             user="root",  # your username
                             passwd="",  # your password
                             db="bingo")  # name of the data base

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


def update_labels(action, t='0'):
    global attempt

    gui.update_status(action.upper() + ' IS NEXT')
    gui.update_attempt(str(attempt))
    gui.update_countdown(t)

    if attempt > 1:
        gui.update_attempt(str(attempt) + '/' + str(attempts_limit), "darkred")


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

    if action == 'readnum':
        print "Running action:", action
        run_read_num()
        print "Done"

    if action == 'photo':
        print "Running action:", action
        run_take_photo()
        print "Done"

    busy = False


def run_take_photo():
    image_name = "camera15.jpg"
    im = cv2.imread(image_name)
    im = cv2.resize(im, (0, 0), fx=0.5, fy=0.5)
    cv2.imwrite("resized_" + image_name, im)
    gui.update_image("resized_" + image_name)


def run_read_num():
    global gui
    global steps
    global step_id
    global attempt
    global attempts_limit

    image_name = "camera15.jpg"
    res_numbr = read_win_number(image_name, "final.jpg")
    fetch_form_db()
    gui.update_image("grey_ball.jpg")

    if res_numbr == -1 and attempt < attempts_limit:
        steps = list(sequence_1)
        attempt += 1
        step_id = 0
    else:
        attempt = 1
        steps = list(base_sequence)
        step_id = 0

    if res_numbr == -2:
        steps = list(sequence_2)
        step_id = 0


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



        # if not started:
        #     for job in scheduler.get_jobs():
        #         job.resume()
        #         started = True
        #         gui.btn_start_stop.config(text="Stop")
        #
        # else:
        #     for job in scheduler.get_jobs():
        #         job.pause()
        #         started = False
        #         gui.btn_start_stop.config(text="Start")


        # start_time = time.clock()
        #
        # image_name = "camera03_1.jpg"
        #
        # label.config(text="Please wait...")
        #
        # args = sys.argv[1:]
        # res_numbr = read_win_number(image_name, "final.jpg")
        #
        # lim_thresh_val = thresh_val
        # thresh_val -= reset_thresh_val
        #
        # while res_numbr < 0 and res_numbr != -2 and thresh_val <= lim_thresh_val:
        #     thresh_val += 10
        #     res_numbr = read_win_number(image_name, "final.jpg")
        #
        # str_res_number = str(res_numbr)
        # if len(str_res_number) > 10:
        #     str_res_number = '0' + str_res_number
        #
        # label.config(text=str_res_number)
        #
        # print "Complete in ", round(time.clock() - start_time, 2), "seconds"


def reset_game():
    global steps
    global start_time
    global started

    steps = list(base_sequence)
    start_time = 0
    started = True


class BingoTkApp(threading.Thread):
    def __init__(self):
        self.end_item = None
        self.root = Tk()
        self.root.wm_title("Bingo GUI")
        self.row1 = Frame(self.root)

        self.img = ImageTk.PhotoImage(Image.open("no-image.jpg"))
        self.img_box = Label(self.row1, image=self.img, width=60, height=60, bg='grey')
        self.img_box.pack(side=LEFT, fill=BOTH, expand="yes")

        self.font = tkFont.nametofont(self.img_box['font'])

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
        self.lbl_countdown = Label(self.row2, width=10, height=2, text='0', font=(self.font['family'], 14, 'bold'),
                                   fg="darkgreen", bg='darkgrey')
        self.lbl_countdown.pack(side=RIGHT, fill=X, expand="yes")

        # Action Label
        self.lbl_status = Label(self.row2, width=30, height=2, text='Ready', font=(self.font['family'], 14, 'bold'),
                                fg="darkgreen", bg='grey')

        self.lbl_status.pack(side=RIGHT, fill=X, expand="yes")

        # Attempt Label
        self.lbl_attempt = Label(self.row2, width=10, height=2, text='0', font=(self.font['family'], 14, 'bold'),
                                 fg="darkgreen", bg='darkgrey')
        self.lbl_attempt.pack(side=LEFT, fill=X, expand="yes")

        self.row2.pack(side=TOP, fill=BOTH)

        threading.Thread.__init__(self)

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
        self.root.mainloop()


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(tick, 'interval', seconds=1, id='job_timer_tick')
    # scheduler.add_job(run_read_num,  'interval', seconds=1, id='job_run_read_num')
    scheduler.start()

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
