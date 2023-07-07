# This program utilises the Telegram bot to choose
# which data to read from ThingSpeak! 
import json
import logging
import sys
import time
import telepot
from urllib import request
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

#Store TOKEN for Telegram Bot
TOKEN = '5599844526:AAE76w9nV7QVVkhQRE9jNuicIqG7rWvfNQY'

#Function on_chat creates inline keyboard
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Temperature', callback_data='temp')],
                    [InlineKeyboardButton(text='Humidity', callback_data='humid')],
                    [InlineKeyboardButton(text='Set1', callback_data='set1')],
                    [InlineKeyboardButton(text='Set2', callback_data='set2')],
                    [InlineKeyboardButton(text='Set3', callback_data='set3')],
                    [InlineKeyboardButton(text='Set4', callback_data='set4')],
                    [InlineKeyboardButton(text='Set5', callback_data='set5')],
                    [InlineKeyboardButton(text='Set6', callback_data='set6')],
                ])
    bot.sendMessage(chat_id, 'Welcome to Smart Vending Machine. What would you like to check?', reply_markup=keyboard)

#Function on_callback_query processes data from Thingspeak and react according to pushed button
def on_callback_query(msg):
    
    #Store response from GET response in variable
    response = request.urlopen('https://api.thingspeak.com/channels/1788638/feeds.json?results=2')

    #Get json data from request
    data = response.read().decode('utf-8')

    #Convert string in dictionary
    data_dict = json.loads(data)

    #Separate values
    feeds = data_dict['feeds']

    #React to button press
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('Callback Query:', query_id, from_id, query_data)

    if(query_data == 'temp'):
        bot.sendMessage(from_id, text='Temperature is: ' + str(feeds[0]['field1']) + '°C')
        
    elif(query_data == 'humid'):
        bot.sendMessage(from_id, text='Humidity is: ' + str(feeds[0]['field2']) + '%')

    elif(query_data == 'set1'):
        bot.sendMessage(from_id, text='Number of Set 1 bought: ' + str(feeds[1]['field3']))
        print (feeds[0])

    elif(query_data == 'set2'):
        bot.sendMessage(from_id, text='Number of Set 2 bought: ' + str(feeds[1]['field4']))

    elif(query_data == 'set3'):
        bot.sendMessage(from_id, text='Number of Set 3 bought: ' + str(feeds[1]['field5']))

    elif(query_data == 'set4'):
        bot.sendMessage(from_id, text='Number of Set 4 bought: ' + str(feeds[1]['field6']))

    elif(query_data == 'set5'):
        bot.sendMessage(from_id, text='Number of Set 5 bought: ' + str(feeds[1]['field7']))
    
    elif(query_data == 'set6'):
        bot.sendMessage(from_id, text='Number of Set 6 bought: ' + str(feeds[1]['field8']))

#Initialise functions
bot = telepot.Bot(TOKEN)
MessageLoop(bot, {'chat': on_chat_message,'callback_query': on_callback_query}).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)