# This is the main programme that uses the Camera, DC Motor, LCD Screen, Keypad, Buzzer and RFID
# It also sends Temperature and Humidity to ThingSpeak 
# Lastly, it uses the Telegram bot to start and receiving notifications

import RPi.GPIO as GPIO  #Import RPi.GPIO module
import dht11
import datetime
import I2C_LCD_driver  #Import library
import requests
import json
import logging
import sys
import time
import telepot
from time import sleep  #To create delays
from mfrc522 import SimpleMFRC522
from picamera import PiCamera
from urllib import request
from telepot.loop import MessageLoop
from subprocess import call

GPIO.setmode(GPIO.BCM)  #Choose BCM mode
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)  #Buzzer
GPIO.setup(23, GPIO.OUT)  #DC motor
instance = dht11.DHT11(pin=21)  #Temp & Humid
reader = SimpleMFRC522()

auth=[] # rfid

#Keypad
MATRIX = [[1, 2, 3],
         [4, 5, 6],
         [7, 8, 9],
         ['*', 0, '#']]  #Layout of keys on keypad
ROW = [6, 20, 19, 13]  #Row pins
COL = [12, 5, 16]  #Column pins

key = ""
select = ""
pressedcorrect = ""

set1 = 0
set2 = 0
set3 = 0
set4 = 0
set5 = 0
set6 = 0

my_camera=PiCamera()
my_camera.resolution=(1920,1000)
my_camera.vflip=True
my_camera.hflip=True

temperature = 0
humidity = 0

TOKEN = "5502610916:AAE-AQtT7dVCUCf_UVhPZ8bWVu918ozVQoA" # for Telegram

def handle(msg): #for Telegram
    global chat_id
    global telegramText

    chat_id = msg['chat']['id']
    telegramText = msg['text']

    if telegramText == '/start':
        bot.sendMessage(chat_id, 'Welcome to Smart Vending Machine.')
    
    while True:
        main()

bot = telepot.Bot(TOKEN)
bot.message_loop(handle)


def main():
    global chat_id
    global temperature
    global humidity
    global key
    global select
    global pressedcorrect
    global set1
    global set2
    global set3
    global set4
    global set5
    global set6
    
    result = instance.read()
    temperature = result.temperature
    humidity = result.humidity
    if result.is_valid():  #Send Temperature and Humidity data to the first 2 fields
        resp=requests.get("https://api.thingspeak.com/update?api_key=B3DZVAZNN6OWV4BI&field1=%s&field2=%s" %(temperature,humidity))
    time.sleep(5)  #Short delay between reads

    if (temperature>25): # Check the Temperature values and call the notification function
        sendNotification1()
    
    if (humidity>80):# Check the Humidity values and call the notification function
        sendNotification2()

    LCD = I2C_LCD_driver.lcd()
    sleep(0.5)
    LCD.backlight(0)
    sleep(0.5)
    LCD.backlight(1)
    LCD.lcd_display_string("Select No.:", 1)

    pressedcorrect = 0

    for i in range(3): #for keypad
        GPIO.setup(COL[i],GPIO.OUT)
        GPIO.output(COL[i],1)

    for j in range(4):
        GPIO.setup(ROW[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)

    nullselect = 1
    while nullselect == 1: # while the user has not entered the number and has not sent over to ThingSpeak yet
        for i in range(3):
            GPIO.output(COL[i],0)
            for j in range(4):
                if GPIO.input(ROW[j])==0:
                        key = MATRIX[j][i]
                        while GPIO.input(ROW[j])==0:
                            sleep(0.1)
                            if key == 1 or key == 2 or key == 3 or key == 4 or key == 5 or key == 6: # if pressed correctly (ThingSpeak left with 6 fields)
                                LCD.lcd_display_string(str(key),2)
                                select = key # temporary value to store the key for sending to ThingSpeak and Telegram
                                pressedcorrect = key # temporary value to ensure user pressed 1 out of 6 correct keys, cannot enter wrong or missing value
                            elif key == 7 or key == 8 or key == 9 or key == 0: # no such products exits, thus cannot accept these numbers
                                LCD.lcd_display_string(str(key),2)
                                buzzer()
                            elif key == "*": # a back space button
                                LCD.lcd_display_string(str(" "),2)
                            elif key == "#" and pressedcorrect!= "0": # a enter button that will check if it is a valid number
                                if select == 1: # check which is the value entered and then sends it ThingSpeak
                                    set1 += 1
                                elif select == 2:
                                    set2 += 1
                                elif select == 3:
                                    set3 += 1
                                elif select == 4:
                                    set4 += 1
                                elif select == 5:
                                    set5 += 1
                                elif select == 6:
                                    set6 += 1
                                resp=requests.get("https://api.thingspeak.com/update?api_key=B3DZVAZNN6OWV4BI&field3=%s&field4=%s&field5=%s&field6=%s&field7=%s&field8=%s" %(set1,set2,set3,set4,set5,set6))
                                time.sleep(15)
                                nullselect = 0
            GPIO.output(COL[i],1)

    identify_cards() 

def buzzer():
    GPIO.output(18, 1)  #Output logic high/'1'
    sleep(2)  #Delay 2 second
    GPIO.output(18, 0)  # Output logic low/'0'
    sleep(1)  #Delay 1 second

def dcmotor():
    GPIO.output(23, 1)  # Output logic high/'1'
    sleep(5)  #Delay 5 second
    GPIO.output(23, 0)  #Output logic low/'0'
    sleep(1)  #Delay 1 second
    
def identify_cards():
    while True:
        LCD = I2C_LCD_driver.lcd()
        LCD.lcd_clear()
        LCD.lcd_display_string("Please tap ",1)
        LCD.lcd_display_string("your ID card! ",2)
        print("Hold card near the reader to check if it is in the database")
        id = reader.read_id()
        id = str(id)
        f = open("authlist.txt", "r+")
        if f.mode == "r+":
              auth=f.read()
        if id in auth: # if the id is in the auth list
              number = auth.split('\n')
              pos = number.index(id)
              print("Card with UID", id, "found in database entry #", pos, "; access granted")
              LCD.lcd_display_string("Pick your   ",1)
              LCD.lcd_display_string("item below!  ",2)
              sendNotification(id, select) 
              dcmotor()
              main()
        else:
            print("Card with UID", id, "not found in database; access denied")
            LCD.lcd_display_string("Try Again!   ",1)
            identify_cards()
            return 0
sleep(2)

def sendNotification(identidy, key): # sends notifications of picture, ID number and Set number
    global chat_id
    my_camera.capture('image001.jpg'.format(1))
    bot.sendPhoto(chat_id, photo = open('image001.jpg', 'rb'))
    bot.sendMessage(chat_id, "ID: " + str(identidy) + " ordered " + "Set " + str(key))

def sendNotification1(): # send notification for high temperature -> vending machine cooler not operating
    global chat_id
    bot.sendMessage(chat_id, 'Alert! Temperature is high!')
    print('Temperature = High')
    sleep(1)

def sendNotification2(): # send notification for high humidity -> vending machine cooler not operating
    global chat_id
    bot.sendMessage(chat_id, 'Alert! Humidity is high!')
    print('Humidity = High')
    sleep(1)

while 1:
    time.sleep(10)