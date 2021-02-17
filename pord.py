import requests
import random
import vk_api
import pytz
from datetime import datetime
from MyLongPoll import MyVkLongPoll
# from data import db
from vk_api import VkUpload
from vk_api.bot_longpoll import VkBotEventType
import pymysql
from pymysql.cursors import DictCursor
import json

session = requests.Session()

vk_session = vk_api.VkApi(token='c2dc3932c3553f743ee9f87a78bdfce9274f9211732aa85a49d5515964c9b4175a4e604d95b3c0329bf8b')  # prod
# vk_session = vk_api.VkApi(token='a98c5a415f7abb50a92aa9b96d245dc88282c3a01b8f0a8489cae58a9d25b2bbe9b80eb40b1076803bf7e')  # test
vk = vk_session.get_api()
upload = VkUpload(vk_session)  # Для загрузки изображений
longpoll = MyVkLongPoll(vk_session, "200162959")  # prod
# longpoll = MyVkLongPoll(vk_session, "202164385")  # test
# conn, cursor = db("testdb")
'''conn = pymysql.connect(
    host='tyfooncs.mysql.pythonanywhere-services.com',
    user='tyfooncs',
    password='P@ssw0rd',
    db='tyfooncs$data',
    charset='utf8mb4',
    cursorclass=DictCursor
)
cursor = conn.cursor()'''

empty_req_answers = ("Что надо?", "Звали?", "Доброго времени суток, дамы и господа.\nЧего желаете?", "Чего изволите?")

day_name = {
    "пн": 1,
    "вт": 2,
    "ср": 3,
    "чт": 4,
    "пт": 5,
    "сб": 6,
    "понедельник": 1,
    "вторник": 2,
    "среда": 3,
    "четверг": 4,
    "пятница": 5,
    "суббота": 6,
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
}

name_day = {
    '1': 'Понедельник',
    '2': 'Вторник',
    '3': 'Среда',
    '4': 'Четверг',
    '5': 'Пятница',
    '6': 'Суббота'
}


def send_msg(msg, att=''):
    return vk.messages.send(
        peer_ids=event.object['peer_id'],
        random_id=random.random(),
        message=msg,
        attachment=att
    )


# вывод расписания с дз
def sh_out():
    cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
    data = cursor.fetchall()
    # дз есть
    if data:
        try:
            data = json.loads(data[0]['hw'])
            # data = data[0]['hw']
        except BaseException as exc:
            print("JSON FAIL in data: ", exc)
            data = eval(data[0]['hw'])
        print("DataDone ", data, type(data))
        # запись расписания + дз в text
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
        lessons = cursor.fetchall()
        try:
            lessons = json.loads(lessons[0]['lessons'])
            # lessons = lessons[0]['lessons']
        except BaseException as exc:
            print("JSON FAIL in lessons sh_out: ", exc)
            lessons = eval(lessons[0]['lessons'])
        print("data", data)
        text = name_day[str(day)] + '\n'
        for i, key in enumerate(lessons):
            corrrect_data = '\n'.join(data[key].split('-i-')[:-1])
            text += str(i + 1) + '. ' + key + ': ' + corrrect_data + '\n'
        text += 'Остальное ДЗ:\n'
        kuchka = data['kucha'].split('-i-')
        for k in kuchka:
            text += k + '\n'

        # запись фото в attach
        cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{day}"')
        att = cursor.fetchall()
        attach = ''
        if att:
            att = att[0]['schedule']
            if att != 'gg':
                try:
                    att = json.loads(att)
                    # att = att
                except BaseException as exc:
                    print("JSON FAIL in att sh_out: ", exc)
                    att = eval(att)
                attach = ','.join(att)

        # закрепление или вывод расписания
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id=-1')
        conv = cursor.fetchall()
        # че за конв я не понимаю
        if day == now_day or int(day) == ((int(now_day) + 1) if int(now_day) + 1 < 7 else 1):
            # редактирование старого дз
            try:
                if not conv:
                    raise vk_api.exceptions.ApiError
                vk.messages.edit(peer_id=event.object['peer_id'],
                                 message=text,
                                 conversation_message_id=int(conv[0]['lessons']),
                                 attachment=attach)
                vk.messages.pin(peer_id=event.object['peer_id'], conversation_message_id=conv[0]['lessons'])
                send_msg("Отредачил закреп")
            # вывод и закреп нового дз
            except Exception as exc:
                print("exc in correct old", exc)
                send_msg(text, attach)
                vk.messages.pin(peer_id=event.object['peer_id'], conversation_message_id=next_botmsg_id)
                cursor.execute(f'select * from sh{dialog_id} where id=-1')
                if cursor.fetchall():
                    cursor.execute(f'update {"sh" + dialog_id} set lessons="{str(next_botmsg_id)}" where id=-1')
                    conn.commit()
                else:
                    cursor.execute(f'insert into {"sh" + dialog_id} values (-1, "{str(next_botmsg_id)}")')
                    conn.commit()
        else:
            send_msg(text, attach)
    # в таблице нет дз
    else:
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
        schedule = cursor.fetchall()
        if schedule:
            try:
                schedule = json.loads(schedule[0]['lessons'])
            except BaseException as exc:
                print("JSON FAIL in only schedule sh_out(end): ", exc)
                schedule = eval(schedule[0]['lessons'])
            text = ''
            for i, lesson in enumerate(schedule):
                text += str(i + 1) + '. ' + lesson + '\n'
            send_msg(text)
        else:
            send_msg(
                "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")


def add_hw(user_msg, day, lessons_l):
    hw = ''
    if user_msg[0]:
        try:
            lessons_l = json.loads(lessons_l[0]['lessons'])
        except BaseException as exc:
            print("JSON FAIL in lessons_l add_hw: ", exc)
            lessons_l = eval(lessons_l[0]['lessons'])

        # достать дз из бд
        cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
        old_hw = cursor.fetchall()
        if old_hw:
            try:
                hw = json.loads(old_hw[0]['hw'])
            except BaseException as exc:
                print("JSON FAIL in old_hw add_hw: ", exc)
                hw = eval(old_hw[0]['hw'])
        else:
            hw = dict()
            for key in lessons_l:
                hw[key] = ''
            hw['kucha'] = ''

        # обработка сообщения
        kucha = ''
        for words in user_msg:
            words = words.split()
            print('words: ', words)
            if words[0].capitalize() not in lessons_l:
                kucha += ' '.join(words) + '-i-'
                continue
            subject = words[0].capitalize()
            hw[subject] = ' '.join(words[1:]) + '-i-'
        if kucha:
            hw['kucha'] = kucha
            cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{day}"')
            if cursor.fetchall():
                cursor.execute(f'update {"hw" + dialog_id} set schedule="gg" where id="{day}"')
                conn.commit()

        hw = conn.escape(str(json.dumps(hw)))

        if old_hw:
            cursor.execute(f'update {"hw" + dialog_id} set hw={hw} where id="{day}"')
        else:
            cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", {hw})')
        conn.commit()

    # обработка фото
    attach = None
    if event.object['attachments']:
        attach = downloadAttach()  # list
    if attach:
        attach = conn.escape(str(json.dumps(attach)))

        # чистка кучи в случае отсутствия текста
        if not user_msg[0]:
            cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
            hw_now = cursor.fetchall()
            if hw_now:
                try:
                    hw_now = json.loads(str(hw_now[0]['hw']))
                except BaseException as exc:
                    print("JSON FAIL in hw_now add_hw: ", exc)
                    hw_now = eval(hw_now[0]['hw'])
            hw_now['kucha'] = ''
            hw_now = conn.escape(str(json.dumps(hw_now)))
            cursor.execute(f'update {"hw" + dialog_id} set hw={hw_now} where id="{day}"')
            conn.commit()
        # ------------

        cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{day}"')
        if cursor.fetchall():
            cursor.execute(f'update {"hw" + dialog_id} set schedule={attach} where id="{day}"')
        else:
            cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", "")')
        conn.commit()
    return hw


# скачивание и загрузка обратно
def downloadAttach():
    size_letters = "smxyzw"
    attach = []
    for i in event.object['attachments']:
        if i['type'] != 'photo':
            continue
        sizes = i['photo']['sizes']
        max_size = 0
        ph_url = ''
        for size in sizes:
            now = size_letters.find(size['type'])
            if now > max_size:
                max_size = now
                ph_url = size['url']
        with open('img.jpg', 'wb+') as ph_file:
            ph_file.write(requests.get(ph_url).content)
        photo = upload.photo_messages(photos=open('img.jpg', 'rb'), peer_id=event.object['peer_id'])[0]
        attach.append(f"photo{photo['owner_id']}_{photo['id']}")
    return attach


def clean(day, lessons_l):
    try:
        lessons_l = json.loads(lessons_l[0]['lessons'])
    except BaseException as exc:
        print("clean exc", exc)
        lessons_l = eval(lessons_l[0]['lessons'])
    hw = dict()
    for key in lessons_l:
        hw[key] = ''
    hw['kucha'] = ''
    hw = conn.escape(str(json.dumps(hw)))  # , ensure_ascii=False
    # gg
    cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
    if cursor.fetchall():
        cursor.execute(f'update {"hw" + dialog_id} set hw={hw} where id="{day}"')
        cursor.execute(f'update {"hw" + dialog_id} set schedule="gg" where id="{day}"')
        conn.commit()
    else:
        cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", {hw})')
        conn.commit()


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.object['text']:
        try:
            user = vk.users.get(user_ids=event.object['from_id'])
            print('\n', event.object['peer_id'], user[0]['first_name'], user[0]['last_name'], event.object['text'],
                  '\n')

            '''conn = pymysql.connect(
                host='tyfooncs.mysql.pythonanywhere-services.com',
                user='tyfooncs',
                password='P@ssw0rd',
                db='tyfooncs$data',
                charset='utf8mb4',
                cursorclass=DictCursor
            )  # prod
            '''conn = pymysql.connect(
                host='FoonGlot.mysql.pythonanywhere-services.com',
                user='FoonGlot',
                password='P@ssw0rd',
                db='FoonGlot$data',
                charset='utf8mb4',
                cursorclass=DictCursor
            )'''  # test
            cursor = conn.cursor()

            # сплит сообщения
            user_msg = event.object['text'].split('\n')
            user_msg[0] = user_msg[0].split()

            # обработка обращений
            if '@hosbobot' in user_msg[0][0]:
                if len(user_msg[0]) == 1:
                    send_msg(random.choice(empty_req_answers))
                    conn.close()
                    continue
                user_msg[0] = user_msg[0][1:]
            if '@all' in user_msg[0]:
                send_msg("че орешь на всю беседу!?")
                conn.close()
                continue
            if '@' in user_msg[0][0]:
                conn.close()
                continue

            # проверка на восклицательный знак перед командой
            if user_msg[0][0][0] == '!':
                user_msg[0][0] = user_msg[0][0][1:]
            else:
                conn.close()
                continue

            # определение дня
            day = None
            now_day = datetime.isoweekday(datetime.now(pytz.timezone('Asia/Dubai')))
            if len(user_msg[0]) > 1:
                if user_msg[0][1] in day_name.keys():
                    day = int(day_name[user_msg[0][1]])
                    del user_msg[0][1]
            if not day:
                day = now_day + 1
            if day >= 7:
                day = 1
            print("DAAAAY: " + str(day))

            # id диалога
            dialog_id = str(event.object['peer_id'])
            dialog_id_int = int(dialog_id)
            next_botmsg_id = int(event.object['conversation_message_id']) + 1

            # авторизация по peer_id в таблице
            cursor.execute('select * from dialogs')
            ids = cursor.fetchall()
            auth_bot = False
            for id in ids:
                if int(dialog_id_int) == id['id']:
                    auth_bot = True
                    break
            if not auth_bot:
                send_msg("Эта беседа еще не приобрела подписку, либо менеджер еще не занес эту беседу в базу.")
                conn.close()
                continue

            # -------------------------------

            user_msg[0][0] = user_msg[0][0].lower()

            '''
                show schedule // вывести и закрепить дз
                format: schedule [day] (optionally)
            '''
            if user_msg[0][0] in ['sh', 'schedule', 'расписание', 'рп']:
                sh_out()
                conn.close()
                continue

            '''
                add static schedule // добавить постоянное расписание
                format: addschedule [day of week] <list of subjects>
            '''
            if user_msg[0][0] in ['addschedule', 'уроки']:
                user_msg = user_msg[0]
                if len(user_msg) > 2:
                    lessons = [i.capitalize() for i in user_msg[1:]]

                    # обновление sh таблицы
                    cursor.execute(f'select * from {"sh" + dialog_id} where id="{day}"')
                    if cursor.fetchall():
                        cursor.execute(
                            f'update {"sh" + dialog_id} set lessons={conn.escape(str(json.dumps(lessons)))} where id="{day}"')

                    # обновление hw таблицы
                    cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
                    if cursor.fetchall():
                        if len(user_msg) > 1:
                            cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                            lessons_l = cursor.fetchall()
                            if lessons_l:
                                text = add_hw(user_msg[1:], day, lessons_l)
                                if not text:
                                    send_msg("Не прикладывайте картинку.")
                                    continue
                        cursor.execute(f'update {"hw" + dialog_id} set hw="{text}" where id="{day}"')
                    else:
                        cursor.execute(
                            f'insert into {"sh" + dialog_id} values("{day}", {conn.escape(str(json.dumps(lessons)))})')
                        conn.commit()

                    schedule_now = name_day[str(now_day)] + ''.join([f'\n{n + 1}. {i}' for n, i in enumerate(lessons)])
                    send_msg(schedule_now)
                    conn.close()
                    continue

            '''
                add homework for specific date // перезаписать дз на урок (если есть день, то на него)
                format: addhomework [date](optionally)
                        [subject]: [homework]
            '''
            if user_msg[0][0] in ['addhw', 'addhomework', 'ah', 'дз']:
                if len(user_msg[0]) > 1 or event.object['attachments']:
                    user_msg[0] = ' '.join(user_msg[0][1:])

                    # есть ли расписание
                    cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                    lessons_l = cursor.fetchall()
                    if lessons_l:
                        add_hw(user_msg, day, lessons_l)
                        sh_out()
                        conn.close()
                        continue
                    else:
                        send_msg(
                            "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")
                        conn.close()
                        continue

            '''
                extend homework for specific date // дописать дз на урок (если есть день, то на него)
                format: updatehomework [date](optionally)
                        [subject]: [homework]
            '''
            if user_msg[0][0] in ['updatehomework', 'uh', 'доп']:
                if len(user_msg[0]) > 1 or event.object['attachments']:
                    user_msg[0] = ' '.join(user_msg[0][1:])

                    cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
                    lessons = cursor.fetchall()
                    cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                    schedule_now = cursor.fetchall()
                    try:
                        schedule_now = json.loads(schedule_now[0]['lessons'])
                    except BaseException as exc:
                        print("JSON FAIL in schedule_now uh: ", exc)
                        schedule_now = eval(schedule_now[0]['lessons'])
                    if lessons and schedule_now:
                        # дополнение дз
                        if user_msg[0]:
                            try:
                                lessons = json.loads(lessons[0]['hw'])
                            except BaseException as exc:
                                print("JSON FAIL in lessons uh: ", exc)
                                lessons = eval(lessons[0]['hw'])
                            print("now: ", schedule_now)
                            for i in user_msg:
                                i = i.split()
                                print("i", i)
                                if i[0].capitalize() not in schedule_now:
                                    lessons['kucha'] += ' '.join(i) + '-i-'
                                    continue
                                subject = i[0].capitalize()
                                lessons[subject] += ' '.join(i[1:]) + '-i-'
                            print("dict", lessons)

                            lessons = conn.escape(str(json.dumps(lessons)))

                            cursor.execute(f'update {"hw" + dialog_id} set hw={lessons} where id="{day}"')
                            conn.commit()
                        # дополнение фото
                        attach = None
                        if event.object['attachments']:
                            attach = downloadAttach()  # list
                        if attach:
                            cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{day}"')
                            old_att = cursor.fetchall()[0]['schedule']
                            if old_att != 'gg':
                                try:
                                    old_att = json.loads(old_att)
                                except BaseException as exc:
                                    print("JSON FAIL in old_att uh: ", exc)
                                    old_att = eval(old_att)
                                print(type(old_att), type(attach))
                                attach = str(json.dumps(old_att + attach))
                            else:
                                attach = str(json.dumps(attach))
                            attach = conn.escape(attach)
                            if old_att:
                                cursor.execute(
                                    f'update {"hw" + dialog_id} set schedule={attach} where id="{day}"')
                                conn.commit()
                            else:
                                cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", "")')
                                conn.commit()

                        sh_out()
                        conn.close()
                        continue
                    else:
                        send_msg(
                            "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу). Также возможны никто еще не заполнял первичное ДЗ командой дз, таким образом вам нечего дополнять.")
                        conn.close()
                        continue

            if user_msg[0][0] in ('cl', 'clean', 'чистка', 'стереть'):
                cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                lessons_l = cursor.fetchall()
                if lessons_l:
                    clean(day, lessons_l)
                    sh_out()
                else:
                    send_msg(
                        "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")
                    conn.close()
                    continue

            '''
                show help // показать помощь
            '''
            if user_msg[0][0] in ['help', 'помощь']:
                send_msg(
                    '''Команды и примеры:
                    https://vk.com/topic-200162959_46878569
                    !День по умолчанию завтрашний, вводить необязательно!
                    расписание [день]
                    уроки [день] <список предметов через пробел>
                    дз [день] <дз>
                    доп [день] <дз>
                    стереть [день]
                    помощь
                    '''
                )
            conn.close()
        except Exception as exc:
            print("general end exc: ", exc)
            send_msg("Хватить меня бить:`(")
            continue
