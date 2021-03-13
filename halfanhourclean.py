import schedule
from datetime import datetime
from pytz import timezone
import requests
import random
import vk_api
import pymysql
from pymysql.cursors import DictCursor
import json


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

    # !!!!говно недоделаное
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
            lessons_l = json.loads(lessons_l[0]['lessons'])
            hw = dict()
            for key in lessons_l:
                hw[key] = ''
            hw['kucha'] = ''
            hw = conn.escape(str(json.dumps(hw)))  # , ensure_ascii=False
            cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
            if cursor.fetchall():
                cursor.execute(f'update {"hw" + dialog_id} set hw={hw} where id="{day}"')
                cursor.execute(f'update {"hw" + dialog_id} set schedule="gg" where id="{day}"')
                conn.commit()
            else:
                cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", {hw})')
                conn.commit()
            vk.messages.send(
                peer_ids=dialog_id,
                random_id=random.random(),
                message='Очистил дз на сегодня'
            )

    conn.close()


def delete_dialog(dialog_id):
    try:
        vk.messages.removeChatUser(chat_id=dialog_id-2000000000, member_id=-group_id)
    except Exception as exc:
        print(exc)
        return
    # !!!!удалить таблицу
    print('deleted', dialog_id)


def check_if_in_dialog():
    conn = pymysql.connect(
        host='89.223.94.40',
        user='tyfooncs',
        password='P@ssw0rd',
        db=dbname,
        charset='utf8mb4',
        cursorclass=DictCursor
    )
    cursor = conn.cursor()

    cursor.execute(f'select id from dialogs')
    dialogs_ids = [list(i.values())[0] for i in cursor.fetchall()]
    for dialog_id in dialogs_ids:
        try:
            chat_info = vk.messages.getConversationMembers(peer_id=dialog_id)
        except vk_api.exceptions.ApiError as exc:
            exc = str(exc)
            if exc[exc.find('[')+1: exc.find(']')] == "917":
                try:
                    vk.messages.send(
                        peer_id=dialog_id,
                        random_id=random.random(),
                        message='Вы слишком долго не давали мне админку, я не могу работать'
                    )
                    delete_dialog(dialog_id)
                except vk_api.exceptions.ApiError as exc2:
                    exc2 = str(exc2)
                    if exc2[exc2.find('[') + 1: exc2.find(']')] == "7":
                        delete_dialog(dialog_id)
                    else:
                        print(exc2)
        else:
            print(dialog_id, chat_info)
            if chat_info['count'] == 1:
                delete_dialog(dialog_id)

    conn.close()


schedule.every().hour.at(':00').do(planned_clean)
schedule.every().hour.at(':30').do(planned_clean)
schedule.every().sunday.at('00:00').do(check_if_in_dialog)
check_if_in_dialog()

while True:
    schedule.run_pending()
