#---------------------------------------------------------------------#
#Name - IR.py
#Description - Reads data from the IR reciever sensor but uses the official SUMSUNG IR Protocol
#Description2 - Note that description of this protocl exists in project file directory
#Author - Pedram Nouri
#---------------------------------------------------------------------#
#Imports modules
import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime
import mysql.connector
import sys
#==================#
#Promps for values
#Input pin
while True:
    inputPin = input("Please enter your input sensor pin (on raspberry): ")
    try:
        inputPin = int(inputPin)
        break
    except:
        pass
#Remote name
remoteName = input("Please enter a name for your remote control: ")

#Global binary value
binary = ''

#==================#
#Sets up GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(inputPin,GPIO.IN)
GPIO.setwarnings(False)

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
    
def runTest(): #Actually runs the test
    getData()
    command = convertToHex()
    print("Hex value = " + str(command)) #Shows results on console
    return command

#==================#
#Output file
output = open(remoteName+".txt", 'a')
output.writelines("Button codes regarding " + remoteName + " SUMSUNG IR controller:")
output.close()
#==================#
#Creating table for this remote
cursor = mydb.cursor()
sql = "CREATE TABLE " + remoteName + " (chnumber VARCHAR(20), chhexvalue VARCHAR(20) PRIMARY KEY)"
cursor.execute(sql)
cursor.close()
#==================#
#Main program loop
while True:
  if input("Press enter to start. Type q to quit. ") == 'q':
    break
  finalData = runTest()
  if input("Do you want to save this channel? y/n.") == 'y':
    name = input("Please enter a name for this button: ")
    output = open(remoteName+".txt", 'a')
    
    #DB process
    try:
        cursor = mydb.cursor()
        sql = "INSERT INTO "+ remoteName +" (chnumber, chhexvalue) VALUES (%s, %s) "
        val = (name, str(finalData))
        cursor.execute(sql, val)
        mydb.commit()
        output.writelines("""
Button Code - """ + name + ": " + str(finalData))
        output.close()
        cursor.close()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        print("Please try again")
        continue

print("\nSee "+remoteName + ".txt file on current directory.")
GPIO.cleanup()
mydb.close()


