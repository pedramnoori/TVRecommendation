#---------------------------------------------------------------------#
#Name - control.py
#Description - catch user actions
#Author - Pedram Nouri
#---------------------------------------------------------------------#
#Imports modules


import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime
import gpiozero
import mysql.connector

#==================#
#Database connection
try:
      mydb = mysql.connector.connect(
      host="s11.liara.ir",
      port="33295",
      user="root",
      password="T2uKgpP6yipXBYAoX1pW4KJo",
      auth_plugin='mysql_native_password',
      database='tvinfo',
      buffered=True
    )
except mysql.connector.Error as err:
    print ("Something went wrong: {}".format(err))
    sys.exit(0)
#==================#
while True:
    remoteName = input("Please enter your remote name: ")
    controller = False
    cursor = mydb.cursor()
    sql = "SHOW TABLES"
    cursor.execute(sql)
    for name in cursor:
        #print (name[0].decode("utf-8"))
        if name[0].decode("utf-8") == remoteName:
            controller = True
            break
    if (controller == True):
        break
    print("Make sure that you write your controller name correctly and try again!")
    cursor.close()
# Data from database
channels = {}
cursor = mydb.cursor()
sql = "SELECT * FROM "+remoteName
cursor.execute(sql)
result = cursor.fetchall()

for res in result:
    channels[res[0]] = res[1]

#channels = {'1': '0xe0e020df','2': '0xe0e0a05f','3': '0xe0e0609f','4': '0xe0e010ef', '5': '0xe0e0906f', '6': '0xe0e050af', 'on': '0xe0e040bf'}
#log = []


startTimeCommand = datetime.now()
binary = ''
inputPin = 8
log = []

# GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(inputPin, GPIO.IN)
GPIO.setwarnings(False)

#==================#
def addToDb():
    #sql = "DROP TABLE IF EXISTS data;"
    #cursor.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS data (channel VARCHAR(20), watch_duration TIME, start_watch TIME, end_watch TIME)"
    cursor.execute(sql)

    try:
        for (ch, time, start, end) in log:
            sql = "INSERT INTO data (channel, watch_duration, start_watch, end_watch) VALUES (%s, %s, %s, %s) "
            val = (ch, time, start, end)
            cursor.execute(sql, val)
            mydb.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        print("Please try again")
        
    #cursor.close()
    #GPIO.cleanup()
    #mydb.close()

#==================#
def convertToHex(): #Converts binary data to hexidecimal
    global binary
    decimal = int(binary, 2)
    return hex(decimal)

#Generate binary from timing information
def generateBinary(command):
    global binary
    
    #Check for start bit
    if (command[0][1]) < 3500:
        print("Under noise or not configured for this TV, Try Again!")
        return getData()
    elif (command[1][1]) < 3500:
        print("Under noise or not configured for this TV, Try Again!")
        return getData()
    
    #Generating binary
    for (val, time) in command:
        if val == 1:
            if time > 4250: #For pulse of start bit
                continue
            #According to signal shape of Sumsung IR Protocol
            if time > 1300:
                binary += '1'
            else:
                binary += '0'


def getData(): #Gets data from IR reciever sensor
    num1s = 0 #Number of consecutive 1s
    command = [] #Pulses and their timings
    previousValue = 0 #The previous pin value
    global binary
    binary = ''
    
    value = GPIO.input(inputPin) #Current pin value

    while value: #Waits until zero (pulse) coming
        value = GPIO.input(inputPin)
        
    startTime = datetime.now() #Sets start time

    while True:
        if value != previousValue: #Waits until change in value occurs
            now = datetime.now() #Records the current time
            pulseLength = now - startTime #Calculate time in between pulses
            startTime = now #Resets the start time
            command.append((previousValue, pulseLength.microseconds)) #Adds pulse time and value to array
        
        #Interrupts code if an extended high period is detected (End Of Command) Because by defualt the output pin of reciever sensor is '1'
        if value:
            num1s += 1
        else:
            num1s = 0
        
        if num1s > 10000: #If happens, we figure out that transmition is finished
            break
        
        #Reads values again
        previousValue = value
        value = GPIO.input(inputPin)

    #Converts data to binary
    generateBinary(command)
        
    if len(str(binary)) > 35: #Sometimes we send same IR pulses more than one time (according to remote design structure) and in this part, we prevent repeats
        binary = binary[:32] #Notice that an IR frame that transmit from Sumsung IR remote, consist of 1 start bit, 32 bit of address and data, and 1 stop bit (Probably). totaly 34 bit
    
def onMode():
    print("Turning On...")
    sleep(3)
    print("OK! Go ahead!")
    getData()
    command = str(convertToHex())
    previousCommand = ''
    startSeeChannel = datetime.now()

    while command != channels['on']:
        if command != previousCommand:
            for ch in channels:
                if command == channels[ch]:
                    now = datetime.now()
                    lengthOnThisChannel = now - startSeeChannel
                    temp = startSeeChannel
                    startSeeChannel = now
                    curTime = now.strftime("%H:%M:%S")
                    print("You are now on channel "+ str(ch) + " at " + curTime)
                    for ch in channels:
                        if channels[ch] == previousCommand:
                            log.append((str(ch), lengthOnThisChannel, temp, now))
        for ch in channels:
            if channels[ch] == command:
                previousCommand = command
        getData()
        command = str(convertToHex())

    now = datetime.now()
    lengthOnThisChannel = now - startSeeChannel
    for ch in channels:
        if channels[ch] == previousCommand:
            log.append((str(ch), lengthOnThisChannel, startSeeChannel, now))
    return False
    
    

# Main loop
print("TV ready to use, press 'ON' button on your remote to start")
while True:
    getData()
    command = convertToHex()

    if str(command) == channels['on']:
        if not onMode():
            print("Turning Off...!")
            sleep(3)
            for (ch, time, start, end) in log:
                print(str(time) + " on channel "+ ch)
            
            print("\nGoodbye and Thanks for Watching!")
            addToDb()
            log = []

