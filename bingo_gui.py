from Tkinter import *
import tkFont
from PIL import ImageTk, Image
from bingo import *
import os
import time
import threading

start_time = 0

def callback_threaded(label):
    threading.Thread(target=read_number(label)).start()

def read_number(label):
    global thresh_val
    start_time = time.clock()

    image_name = "camera03_1.jpg"

    label.config(text="Please wait...")

    args = sys.argv[1:]
    res_numbr = read_win_number(image_name, "final.jpg")

    lim_thresh_val = thresh_val
    thresh_val -= reset_thresh_val

    while res_numbr < 0 and res_numbr != -2 and thresh_val <= lim_thresh_val:
        thresh_val += 10
        res_numbr = read_win_number(image_name, "final.jpg")

    str_res_number = str(res_numbr)
    if len(str_res_number) > 10:
        str_res_number = '0' + str_res_number

    label.config(text=str_res_number)

    print "Complete in ", round(time.clock() - start_time, 2), "seconds"


class BingoTkApp(threading.Thread):
    def __init__(self):
        self.root = Tk()
        self.root.wm_title("Bingo GUI")
        self.row1 = Frame(self.root)

        self.img = ImageTk.PhotoImage(Image.open("final.jpg"))
        self.img_box = Label(self.row1, image=self.img)
        self.img_box.pack(side=LEFT, fill=BOTH, expand="yes")

        self.font = tkFont.nametofont(self.img_box['font'])

        self.lbl = Label(self.row1, width=15, height=2, text='Ready', font=(self.font['family'], 26, 'bold'),
                         fg="darkgreen", bg='grey')
        self.lbl.pack(side=RIGHT, fill=BOTH, expand="yes")

        self.row1.pack(side=TOP, fill=BOTH, padx=5, pady=5)

        # Read number button
        self.btn_read_num = Button(self.root, text='Read number', command=(lambda e=self.lbl: callback_threaded(e)))
        self.btn_read_num.pack(side=RIGHT, padx=5, pady=5)

        self.lbl_status = Label(self.root, width=20, height=2, text='Ready', font=(self.font['family'], 12, 'bold'),
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
    gui = BingoTkApp()
    gui.run()
    gui.lbl.config(text="Ok")
