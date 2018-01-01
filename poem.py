#!/usr/bin/python

"""
On Raspberry Pi 3 you need to disable Bluetooth, otherwise you won't be able to print to the serial port
Instructions from https://openenergymonitor.org/emon/node/12311:

sudo apt-get update
sudo apt-get upgrade
sudo apt-get dist-upgrade
sudo rpi-update

Open /boot/config.txt

Add the following line at the end of the file:

dtoverlay=pi3-disable-bt

Finally, run the following command:

sudo systemctl disable hciuart

Reboot the Pi 3

+++++++++++++++++++++++++++++++++++++++++++++++++++++++

Install on-screen keyboard:

sudo apt-get install matchbox-keyboard

+++++++++++++++++++++++++++++++++++++++++++++++++++++++

You need to get the Adafruit Python Thermal Printer Library:

https://github.com/adafruit/Python-Thermal-Printer

+++++++++++++++++++++++++++++++++++++++++++++++++++++++

Any author portrait photos should be added to /home/pi/Desktop/poem/images/

"""

from __future__ import print_function
from serial import Serial

from datetime import datetime, timedelta

from time import strptime, sleep
import json
from Adafruit_Thermal import *
import requests
import textwrap
import printer
import os
import unicodedata
import textwrap
from Tkinter import *
from PIL import Image, ImageTk, ImageEnhance
from picamera import PiCamera, Color

camera = PiCamera()
camera.rotation = 180
camera.stop_preview()
camera.resolution = (200, 200)
camera.brightness = 50
camera.start_preview(fullscreen=False, window=(418, 41, 190, 191))

def getToday():
    today = datetime.today().strftime("%A, %B %-d, %Y")
    return today

def getTodayNumeric():
    today = datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
    return today

def close():
    camera.stop_preview()
    root.destroy()

def readCurrent(category):
    if category == "human":
        f = open('/home/pi/Desktop/poem/trackhuman.txt','r')
    else:
        f = open('/home/pi/Desktop/poem/trackbot.txt', 'r')
    lastLine = f.readlines()[-1]
    lastLineList = lastLine.split(" ")
    count = lastLineList[1].lstrip("0")
    f.close()
    return count

def deletePortrait():
    if os.path.isfile("/home/pi/Desktop/poem/images/portrait.png"):
        os.remove("/home/pi/Desktop/poem/images/portrait.jpg")
    
def printBot():
    deletePortrait()
    data = getBookbotData()
    printContent(data)
    count = updateCount("bot")    
    countVal = "Robot: " + count
    textCountBot.set(countVal)
    deletePortrait()

def printHuman():
    deletePortrait()
    data = getSpreadSheetData()
    printContent(data)
    count = updateCount("human")
    countVal = "Human: " + count
    textCountHuman.set(countVal)
    deletePortrait()
    
def updateCount(category):
    if category == "human":
        f = open('/home/pi/Desktop/poem/trackhuman.txt','a+')
    else:
        f = open('/home/pi/Desktop/poem/trackbot.txt', 'a+')
    lastLine = f.readlines()[-1]
    lastLineList = lastLine.split(" ")
    count = lastLineList[1].lstrip("0")
    count = int(count)
    count = count + 1
    count = str(count)
    today = getTodayNumeric()
    newLine = today + " " + str(count.zfill(6))
    f.write("\n")
    f.write(newLine)
    f.close()
    return count

def getBookbotData():
    url = "" # Link to bookBot Poet web service
    r= requests.get(url)
    data = r.json()
    return data

def getSpreadSheetData():
    url = "" # Link to Google Sheet web service for human-authored poems
    r = requests.get(url)
    data = r.json()
    return data

def takePhoto():
    camera.capture('/home/pi/Desktop/poem/images/portrait.jpg')
    image = Image.open('/home/pi/Desktop/poem/images/portrait.jpg').convert('LA')
    background = Image.new('L', (384,200), "white")
    background.paste(image, (92, 0))
    background.save('/home/pi/Desktop/poem/images/portrait.jpg')
    image = Image.open('/home/pi/Desktop/poem/images/portrait.jpg')
    contrast = ImageEnhance.Contrast(image)
    contrast.enhance(2).save("/home/pi/Desktop/poem/images/portrait.jpg")
    
def printContent(data):
    p = Adafruit_Thermal("/dev/ttyAMA0", 19200, timeout=5)
    p.begin(90) # Warmup time
    p.setTimes(65000, 5000) # Set print and feed times
    p.justify('C')
    p.setSize('M')
    p.println("My Poet, My Poem & I")
    p.feed(1)
    if os.path.isfile("/home/pi/Desktop/poem/images/portrait.png"):
        p.printImage(Image.open("/home/pi/Desktop/poem/images/portrait.png"), True)
    p.setTimes(40000, 3000) # Set print and feed times
    today = getToday()
    attribution = unicodedata.normalize("NFKD", data["Attribution"])
    attributionPrint = textwrap.fill(attribution, width=32)
    author = "A Poem by " + unicodedata.normalize("NFKD", data["Author"])
    authorPrint = textwrap.fill(author, width=32)
    title = unicodedata.normalize("NFKD", data["Title"])
    titlePrint = textwrap.fill(title, width=32)
    p.justify('L')
    p.setSize('S')
    p.println(today)
    p.setSize('M')
    p.println(titlePrint)
    p.setSize('S')
    for line in data["Poem"]:
        line = unicodedata.normalize("NFKD", line)
        linePrint = textwrap.fill(line, width=32, subsequent_indent="  ")
        p.println(linePrint)
    p.feed(1)
    p.writeBytes(27, 33, 1)
    if attribution != "":
        p.println(attributionPrint)
        p.feed(1)
    p.justify('C')
    p.println(authorPrint)
    p.feed(1)
    image = unicodedata.normalize("NFKD", data["Image"])
    imagePath = "/home/pi/Desktop/poem/images/" + image # Link to poet's portrait photo
    p.setTimes(65000, 5000) # Set print and feed times
    p.printImage(Image.open(imagePath), True)
    p.feed(1)
    p.println("Brought to you by NCSU Libraries")
    p.feed(3)

root = Tk()

countHuman = readCurrent("human")
countBot = readCurrent("bot")
textCountHumanVal = "Human: " + str(countHuman)
textCountBotVal = "Robot: " + str(countBot)
textCountHuman = StringVar(value=textCountHumanVal)
textCountBot = StringVar(value=textCountBotVal)

root.overrideredirect(True)
#root.resizable(width=False, height=False)
root.minsize(width=1024, height=600)
root.maxsize(width=1024, height=600)
root.title("Poem Dispenser")
## GUI
## Create a menu
menu = Menu(root)
root.config(menu=menu)
## File Menu
filemenu = Menu(menu)
menu.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="Exit", command=close)

buttonRow = Frame(root, height="400")
buttonRow.grid(row=0, column=0, columnspan=3, sticky=W+E)

## Setting button size. Code from: http://effbot.org/tkinterbook/button.htm
fBot = Frame(buttonRow, width=400, height=400)
fBot.grid(row=0, column=0, sticky=N+W, rowspan=2)

fEmpty = Frame(buttonRow, width=207, height=211, bg="red")
fEmpty.grid(row=0, column=1)

fSelfie = Frame(buttonRow, width=207, height=200)
fSelfie.grid(row=1, column=1)

fHuman = Frame(buttonRow, width=400, height=400)
fHuman.grid(row=0, column=2, sticky=N+E, rowspan=2)

fLabelBot = Frame(buttonRow, width=400, height=188)
fLabelBot.grid(row=2, column=0)

fLabelHuman = Frame(buttonRow, width=400, height=188)
fLabelHuman.grid(row=2, column=2)

bot = Button(fBot, text="BOT", command=printBot)
photoBot = PhotoImage(file="/home/pi/Desktop/poem/images/bot_button.gif")
bot.config(image=photoBot, width="400", height="400")

selfie = Button(fSelfie, text="Take Selfie", command=takePhoto)
photoSelfie = PhotoImage(file="/home/pi/Desktop/poem/images/wuf_take_selfie.gif")
selfie.configure(image=photoSelfie, width="207", height="189")

human = Button(fHuman, text="HUMAN", command=printHuman)
photoHuman = PhotoImage(file="/home/pi/Desktop/poem/images/human_button.gif")
human.config(image=photoHuman, width="400", height="400")

labelBot = Label(fLabelBot, textvariable=textCountBot, font=("Arial", 46))
labelBot.config(pady="50")
labelBot.pack()

labelHuman = Label(fLabelHuman, textvariable=textCountHuman, font=("Arial", 46))
labelHuman.config(pady="50")
labelHuman.pack()

bot.pack(fill=BOTH, expand=1)
human.pack(fill=BOTH, expand=1)
selfie.pack(fill=BOTH, expand=1)

mainloop()
