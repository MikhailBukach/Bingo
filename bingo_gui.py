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

steps = []


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

        for row in cur.fetchall():
            gui.listbox.insert(END,row[0])


        db.close()


    except MySQLdb.Error, e:
        print "MySQL ERROR:", e

def tick():
    global gui
    global start_time

    if not started:
        gui.lbl.config(text="Not Started")
    else:
        gui.lbl.config(text=str(round(time.clock() - start_time)))
        # gui.listbox.insert(END, str(round(time.clock() - start_time)))

def run_read_num():
    image_name = "camera03_1.jpg"
    res_numbr = read_win_number(image_name, "final.jpg")

def start_stop(label):
    global thresh_val
    global scheduler
    global started
    global start_time

    if not started:
        start_time = time.clock()
        started = True
        gui.btn_start_stop.config(text="Stop")
    else:
        started = False
        start_time = 0
        gui.btn_start_stop.config(text="Start")

    fetch_form_db()


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


class BingoTkApp(threading.Thread):
    def __init__(self):
        self.end_item = None
        self.root = Tk()
        self.root.wm_title("Bingo GUI")
        self.row1 = Frame(self.root)

        self.img = ImageTk.PhotoImage(Image.open("final.jpg"))
        self.img_box = Label(self.row1, image=self.img)
        self.img_box.pack(side=LEFT, fill=BOTH, expand="yes")

        self.font = tkFont.nametofont(self.img_box['font'])

        self.lbl = Label(self.row1, width=15, height=2, text='Ready', font=(self.font['family'], 30, 'bold'),
                         fg="darkgreen", bg='grey')
        self.lbl.pack(side=RIGHT, fill=BOTH, expand="yes")

        # self.scrollbar = Scrollbar(frame, orient=VERTICAL)
        # listbox = Listbox(frame, yscrollcommand=scrollbar.set)
        # scrollbar.config(command=listbox.yview)
        # scrollbar.pack(side=RIGHT, fill=Y)
        # listbox.pack(side=LEFT, fill=BOTH, expand=1)

        self.listbox = Listbox(self.row1, font=(self.font['family'], 14, 'bold'))
        self.listbox.pack()
        self.listbox.insert(END, "Ready to the game")

        self.row1.pack(side=TOP, fill=BOTH, padx=5, pady=5)

        # Read number button
        self.btn_start_stop = Button(self.root, text='Start', command=(lambda e=self.lbl: start_stop(e)))
        self.btn_start_stop.pack(side=RIGHT, padx=5, pady=5)

        self.lbl_status = Label(self.root, width=20, height=2, text='Start', font=(self.font['family'], 14, 'bold'),
                                fg="black")

        self.lbl_status.pack(side=RIGHT)

        update_status_lable(self.lbl_status)
        threading.Thread.__init__(self)

    def run(self):
        self.root.mainloop()


def update_status_lable(label):
    status = "Ready"

    if start_time != 0:
        status = "Reading image: " + str(round(time.clock() - start_time, 2)) + " sec"

    label.config(text=status)


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(tick, 'interval', seconds=1, id='job_timer_tick')
    scheduler.add_job(run_read_num,  'interval', seconds=1, id='job_run_read_num')
    scheduler.start()

    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

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
