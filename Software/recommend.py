# import datetime
import mysql.connector
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
import sys
# import numpy
# from tkinter import *

# numpy.set_printoptions(threshold=sys.maxsize)

warnings.filterwarnings("ignore")

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

# root = Tk()
# root.title("Recommendation")
# root.geometry("500x300")

# scrollbar = Scrollbar(root, orient='vertical')
# scrollbar.pack(side=RIGHT, fill=Y)
# t = Text(root, width=100, height=100, wrap=NONE, yscrollcommand=scrollbar.set)


def createPersianStopwords():
    f = open("/Users/pedram/Desktop/Project/stop.txt").read().split("\n")
    stopwords = []
    for x in f:
        stopwords.append(x.strip())
    return stopwords


def recommend(ind, watchedChannel, row):
    recommendedPrograms = []
    # t.insert(END, "Recommendation for " +
    #          watchedChannel['title']+" on channel " + str(watchedChannel['channel'])+" is: \n")
    # print ("Recommendation for " + watchedChannel['title']+" on channel "+str(watchedChannel['channel'])+" is:" )
    for i in ind:
        if row[i] < 0.15:
            continue
        sql = "SELECT * "
        sql += "FROM conductor WHERE id= '" + str(i + 1) + "'"
        cursor.execute(sql)
        res = cursor.fetchall()
        for x in res:
            sql = "INSERT INTO recommend (channel, title, description, start_time, end_time, program_duration) VALUES (%s, %s, %s, %s, %s, %s);"
            val = (x['channel'], x['title'], x['description'],
                   x['start_time'], x['end_time'], x['program_duration'])
            cursor.execute(sql, val)
            mydb.commit()
            # t.insert(END, str(x['title']) + " || " + str(x['channel']
            #                                              ) + " || " + str(x['start_time']) + " \n")
            # print (x['title'])
            # print (x['channel'])
            # print (x['start_time'])


def main():

    sql = "SELECT * "
    sql += "FROM conductor"
    cursor.execute(sql)
    conductor = cursor.fetchall()

    documents = []
    for x in conductor:
        des = x['title'] + " " + x['description']
        documents.append(des)

    sql = "SELECT * "
    sql += "FROM seen"
    cursor.execute(sql)
    seen = cursor.fetchall()

    seenDocument = []
    for x in seen:
        des = x['title'] + " " + x['description']
        seenDocument.append(des)

    stopwords = createPersianStopwords()
    tfidf = TfidfVectorizer(stop_words=stopwords, ngram_range=(1, 3))
    tfidf.fit(documents)
    cond_mat = tfidf.transform(documents)
    seen_mat = tfidf.transform(seenDocument)

    counter = 0

    # Recommendation Table
    sql = "DROP TABLE IF EXISTS recommend"
    cursor.execute(sql)
    sql = "CREATE TABLE recommend(id INT(10) PRIMARY KEY AUTO_INCREMENT, channel VARCHAR(20), title VARCHAR(150), description VARCHAR(500), start_time TIME, end_time TIME, program_duration TIME);"
    cursor.execute(sql)
    for row in cosine_similarity(seen_mat, cond_mat):
        ind = row.argsort()[:-8:-1]
        # print ("row 164:", row[335])
        # print (seen[counter]['start_time'])
        # print (seen[counter]['title'])
        # print (seen[counter]['channel'])
        # if counter == 4:

        #     print (row)
        #     print (ind)
        #     print (seen[counter]['title'])
        #     print (seen[counter]['channel'])
        #     print (row[54])
        #     print (row[83])
        #     print (row[92])
        #     print (row[76])
        #     print (row[59])
        #     print (row[102])
        #     print (row[29])

        recommend(ind, seen[counter], row)
        # t.insert(END, "========================================== \n")
        counter += 1

    # t.pack(fill=X)
    # scrollbar.config(command=t.yview)
    # root.mainloop()
