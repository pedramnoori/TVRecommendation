import requests
from bs4 import BeautifulSoup as bs
import datetime
from dateutil.parser import parse
import mysql.connector
import warnings

warnings.filterwarnings("ignore")

channels = {'1': 'https://www.irib.ir/conductor/31/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%DB%8C%DA%A9/',
            '2': 'https://www.irib.ir/conductor/32/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%D8%AF%D9%88/',
            '3': 'https://www.irib.ir/conductor/33/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%D8%B3%D9%87/',
            '4': 'https://www.irib.ir/conductor/34/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%DA%86%D9%87%D8%A7%D8%B1/',
            '5': 'https://www.irib.ir/conductor/35/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%D9%BE%D9%86%D8%AC/',
            '6': 'https://www.irib.ir/conductor/36/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%D8%AE%D8%A8%D8%B1/',
            '7': 'https://www.irib.ir/conductor/37/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%D8%A2%D9%85%D9%88%D8%B2%D8%B4/',
            '8': 'https://www.irib.ir/conductor/38/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%D9%82%D8%B1%D8%A2%D9%86/',
            '9': 'https://www.irib.ir/conductor/39/%D8%AC%D8%AF%D9%88%D9%84-%D9%BE%D8%AE%D8%B4-%D8%B4%D8%A8%DA%A9%D9%87-%D9%85%D8%B3%D8%AA%D9%86%D8%AF/'}
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

cursor = mydb.cursor()


def validateDescription(selectedChannel, description):
    if selectedChannel == '1':
        res = description.find("شبکه یک")
        if res != -1:
            # print ("HEREEEE")
            description = description[:res]
        res = description.find("دقیقه")
        if res != -1:
            description = description[res + 6:]
    elif selectedChannel == '2':
        res = description.find("شبکه دو شبکه زندگی")
        if res != -1:
            description = description[:res]
    elif selectedChannel == '3':
        res = description.find("شبکه سه شبکه جوان")
        if res != -1:
            description = description[:res]
    elif selectedChannel == '4':
        res = description.find("شبکه چهار شبکه دانایی")
        if res != -1:
            description = description[:res]
        res = description.find("[مدت]")
        if res != -1:
            description = description[res + 11:]
    elif selectedChannel == '5':
        res = description.find("www.tv5.ir")
        if res != -1:
            description = description[:res]
        res = description.find("دقیقه")
        if res != -1:
            description = description[res + 6:]
    elif selectedChannel == '7':
        res = description.find("قالب: میان برنامه")
        if res != -1:
            description = description[:res]
        res = description.find("دقیقه")
        if res != -1:
            description = description[res + 6:]
    elif selectedChannel == '9':
        res = description.find("آدرس سایت")
        if res != -1:
            description = description[:res]
    final = description.find("توضیحات برنامه درج")
    if final != -1:
        description = ""
    return description


def stringCalculation(tim):
    startString = tim[0].partition(":")[-1].strip()
    endString = tim[1].partition(":")[-1].strip()
    startTime = parse(startString)
    endTime = parse(endString)
    duration = endTime - startTime

    # print (duration)
    return startTime.time(), endTime.time(), duration


def scrap(selectedChannel):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'}

    url = channels[selectedChannel]
    res = requests.get(url, headers=headers)
    # print(res.status_code)
    soup = bs(res.content, 'html.parser')
    results = soup.find(id='conductor')

    programs = results.find_all(
        'div', {"class": ["row box", "row box playing-now"]})

    counter = 0
    for program in programs:
        title = program.find('h4', class_='none')
        description = program.find('p', class_='cobox-description')
        time = program.find('div', class_='cobox-time')
        if None in (title, description, time):
            continue
        startTime, endTime, duration = stringCalculation(
            time.text.strip().split("\n"))
        try:
            sql = "INSERT INTO conductor (channel, title, description, start_time, end_time, program_duration) VALUES (%s, %s, %s, %s, %s, %s);"
            desc = validateDescription(
                selectedChannel, description.text.strip())
            val = (selectedChannel, title.text.strip(),
                   desc, startTime, endTime, duration)
            cursor.execute(sql, val)
            mydb.commit()
        except mysql.connector.Error as err:
            print("Something went wrong: {}".format(err))
            print("WARNING!!!")


def main():

    # try:
    #     mydb = mysql.connector.connect(
    #         host="s11.liara.ir",
    #         port="33295",
    #         user="root",
    #         password="T2uKgpP6yipXBYAoX1pW4KJo",
    #         auth_plugin='mysql_native_password',
    #         database='tvinfo',
    #         buffered=True
    #     )
    # except mysql.connector.Error as err:
    #     print("Something went wrong: {}".format(err))
    #     sys.exit(0)

    # cursor = mydb.cursor()
    sql = "DROP TABLE IF EXISTS conductor;"
    cursor.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS conductor(id INT(10) PRIMARY KEY AUTO_INCREMENT, channel VARCHAR(20), title VARCHAR(150), description VARCHAR(500), start_time TIME, end_time TIME, program_duration TIME);"
    cursor.execute(sql)
    for x in range(1, 8):
        scrap(str(x))
    cursor.close()
    mydb.close()
