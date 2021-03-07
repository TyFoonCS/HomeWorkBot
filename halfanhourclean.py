import schedule
from datetime import datetime
from pytz import timezone
import requests
import random
import vk_api
import pymysql
from pymysql.cursors import DictCursor
import json
from pord import clean


session = requests.Session()

prod = True  # True - prod, False - test
with open('config.txt', 'r') as config:
    config = config.read().split('\n')
if prod:
    vk_session = vk_api.VkApi(token=config[0])
    group_id = int(config[1])
    dbname = config[2]
else:
    vk_session = vk_api.VkApi(token=config[3])
    group_id = int(config[4])
    dbname = config[5]

vk = vk_session.get_api()


# ----------------


def planned_clean():
    dt = datetime.now(timezone('Asia/Dubai'))
    day = datetime.isoweekday(dt)
    time = float('.'.join((str(i) for i in dt.timetuple()[3:5])))  # время формата ЧЧ.ММ в float (example 9.3 is 9:30)
    conn = pymysql.connect(
        host='89.223.94.40',
        user='tyfooncs',
        password='P@ssw0rd',
        db=dbname,
        charset='utf8mb4',
        cursorclass=DictCursor
    )
    cursor = conn.cursor()

    # говно недоделаное
    cursor.execute(f'')  # селект из конфига
    dialogs = {}  # словарь: ключ - id диалога, значение - время в формате float
    # +++++++++++++++++

    dialog_toclean = []
    for dialog_id in dialogs.keys():
        if dialogs[dialog_id] == time:
            dialog_toclean.append(dialog_id)

    for dialog_id in dialog_toclean:
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
        lessons_l = cursor.fetchall()
        if lessons_l:
            clean(day, lessons_l)
            vk.messages.send(
                peer_ids=dialog_id,
                random_id=random.random(),
                message='Очистил дз на сегодня'
            )

    conn.close()


schedule.every().minute.at(':00').do(planned_clean)
schedule.every().minute.at(':30').do(planned_clean)

while True:
    schedule.run_pending()
