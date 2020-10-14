import mysql.connector
import datetime
import warnings
import sys


warnings.filterwarnings("ignore")

seenChannels = []

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
    print("Something went wrong: {}".format(err))
    sys.exit(0)

cursor = mydb.cursor(dictionary=True)


def detectSeen(data):
    seenAmount = 0
    global seenChannels
    if (data['start_watch'] <= data['start_time']) and (data['end_watch'] <= data['end_time']):
        seenAmount = data['end_watch'] - data['start_time']
        if (seenAmount / data['program_duration']) > 0.58:
            if (data['program_duration'] > datetime.timedelta(minutes=3)) and (data['title'] != "میان برنامه") and (data['title'] != "آگهی بازرگانی"):
                seenChannels.append(data)

    elif (data['start_watch'] >= data['start_time']) and (data['end_watch'] >= data['end_time']):
        seenAmount = data['end_time'] - data['start_watch']
        if (seenAmount / data['program_duration']) > 0.58:
            if (data['program_duration'] > datetime.timedelta(minutes=3)) and (data['title'] != "میان برنامه") and (data['title'] != "آگهی بازرگانی"):
                seenChannels.append(data)

    elif (data['start_watch'] <= data['start_time']) and (data['end_watch'] >= data['end_time']):
        seenAmount = data['end_time'] - data['start_time']
        if (seenAmount / data['program_duration']) > 0.58:
            if (data['program_duration'] > datetime.timedelta(minutes=3)) and (data['title'] != "میان برنامه") and (data['title'] != "آگهی بازرگانی"):
                seenChannels.append(data)

    elif (data['start_watch'] >= data['start_time']) and (data['end_watch'] <= data['end_time']):
        seenAmount = data['end_watch'] - data['start_watch']
        if (seenAmount / data['program_duration']) > 0.58:
            if (data['program_duration'] > datetime.timedelta(minutes=3)) and (data['title'] != "میان برنامه") and (data['title'] != "آگهی بازرگانی"):
                seenChannels.append(data)


def main():

    sql = "SELECT * "
    sql += "FROM data JOIN conductor WHERE (conductor.channel = data.channel) AND "
    sql += "(conductor.start_time < data.end_watch AND conductor.end_time > data.start_watch)"
    cursor.execute(sql)

    res = cursor.fetchall()

# Can we delete this??
    sql_cond = "SELECT * "
    sql_cond += "FROM conductor"
    cursor.execute(sql_cond)
    conductor = cursor.fetchall()
# Till here

    for x in res:
        detectSeen(x)

    sql = "DROP TABLE IF EXISTS seen"
    cursor.execute(sql)
    sql = "CREATE TABLE seen (id INT(10) PRIMARY KEY AUTO_INCREMENT, channel VARCHAR(20), title VARCHAR(150), description VARCHAR(500), start_time TIME, end_time TIME, program_duration TIME);"
    cursor.execute(sql)

    for x in seenChannels:
        try:
            sql = "INSERT INTO seen (channel, title, description, start_time, end_time, program_duration) VALUES (%s, %s, %s, %s, %s, %s);"
            val = (x['channel'], x['title'], x['description'],
                   x['start_time'], x['end_time'], x['program_duration'])
            cursor.execute(sql, val)
            mydb.commit()
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
            print("WARNING!!!")
