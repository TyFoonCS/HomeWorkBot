import requests
import random
import vk_api
import pytz
from datetime import datetime, date
from MyLongPoll import MyVkLongPoll
# from data import db
from vk_api import VkUpload
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
import pymysql
from pymysql.cursors import DictCursor

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


def sh_out():
    print(111)
    cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{day}"')
    print(222)
    att = cursor.fetchall()
    attach = ''
    if att:
        att = att[0]['schedule']
        print(333)
        if att != 'gg':
            att = eval(att)
            attach = ','.join(att)

    cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
    data = cursor.fetchall()
    print("data: ", data)
    if data:
        # print("data: ", data)
        data = eval(data[0]['hw'])

        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
        lessons = eval(cursor.fetchall()[0]['lessons'])
        print("data", data)
        text = name_day[str(day)] + '\n'
        for i, key in enumerate(lessons):
            text += str(i + 1) + '. ' + key + ': ' + data[key] + '\n'
        text += 'Остальное ДЗ:\n'
        kuchka = data['kucha'].split('-i-')
        for k in kuchka:
            text += k + '\n'

        cursor.execute(f'select lessons from {"sh" + dialog_id} where id=-1')
        conv = cursor.fetchall()
        print("days: ", day, now_day)
        if day == now_day or int(day) == ((int(now_day) + 1) if int(now_day) + 1 < 7 else 1):
            try:
                if not conv:
                    raise vk_api.exceptions.ApiError
                vk.messages.edit(peer_id=event.object['peer_id'],
                                 message=text,
                                 conversation_message_id=int(conv[0]['lessons']),
                                 attachment=attach)
                vk.messages.pin(peer_id=event.object['peer_id'], conversation_message_id=conv[0]['lessons'])
                send_msg("Отредачил закреп")
                print(9999)
            except Exception as exc:
                print(exc)
                print(77777)
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
    else:
        print(111111111)
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
        schedule = cursor.fetchall()
        print(schedule)
        if schedule:
            print("sh: ", schedule)
            schedule = eval(schedule[0]['lessons'])
            text = ''
            for i, lesson in enumerate(schedule):
                print(i, lesson)
                text += str(i + 1) + '. ' + lesson + '\n'
            send_msg(text, attach)
        else:
            send_msg(
                "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")


def add_hw(user_msg, day, lessons_l):
    hw = ''
    if user_msg[0]:
        lessons_l = eval(lessons_l[0]['lessons'])
        cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
        now_hw = cursor.fetchall()
        if now_hw:
            hw = eval(now_hw[0]['hw'])
        else:
            hw = dict()
            for key in lessons_l:
                hw[key] = ''
            hw['kucha'] = ''

        for words in user_msg:
            words = words.split()
            print('words: ', words)
            if words[0].capitalize() not in lessons_l:
                hw['kucha'] = ' '.join(words) + '-i-'
                continue
            subject = words[0].capitalize()
            hw[subject] = ' '.join(words[1:])

        if hw['kucha']:
            cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{day}"')
            if cursor.fetchall():
                cursor.execute(f'update {"hw" + dialog_id} set schedule="gg" where id="{day}"')
                conn.commit()

        hw = str(hw).replace("'", r"\'").replace('"', r'\"')

        if now_hw:
            cursor.execute(f'update {"hw" + dialog_id} set hw="{hw}" where id="{day}"')
            conn.commit()
        else:
            cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", "{hw}")')
            conn.commit()

    attach = None
    if event.object['attachments']:
        attach = downloadAttach()  # list
    if attach:
        cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{day}"')
        if cursor.fetchall():
            cursor.execute(f'update {"hw" + dialog_id} set schedule="{str(attach)}" where id="{day}"')
            conn.commit()
        else:
            cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", "")')
            conn.commit()
    return hw


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
        # ph_url = i['photo']['sizes'][-5]['url']
        with open('img.jpg', 'wb+') as ph_file:
            ph_file.write(requests.get(ph_url).content)
        photo = upload.photo_messages(photos=open('img.jpg', 'rb'), peer_id=event.object['peer_id'])[0]
        attach.append(f"photo{photo['owner_id']}_{photo['id']}")
    return attach


def clean(day, lessons_l):
    lessons_l = eval(lessons_l[0]['lessons'])
    hw = dict()
    for key in lessons_l:
        hw[key] = ''
    hw['kucha'] = ''

    cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
    if cursor.fetchall():
        cursor.execute(f'update {"hw" + dialog_id} set hw="{str(hw)}" where id="{day}"')
        cursor.execute(f'update {"hw" + dialog_id} set schedule="gg" where id="{day}"')
        conn.commit()
    else:
        cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", "{str(hw)}")')
        conn.commit()


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.object['text']:
        try:
            conn = pymysql.connect(
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

            # godmode
            god = False
            if event.object['from_id'] in [167849130]:
                god = True

            user_msg = event.object['text'].split('\n')
            user_msg[0] = user_msg[0].split()
            if '@hosbobot' in user_msg[0][0]:
                if len(user_msg[0]) == 1:
                    send_msg(random.choice(empty_req_answers))
                    conn.close()
                    continue
                user_msg[0] = user_msg[0][1:]
            if '@all' in user_msg[0][0]:
                send_msg("че орешь на всю беседу!?")
                conn.close()
                continue
            if '@' in user_msg[0][0]:
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

            dialog_id = str(event.object['peer_id'])
            dialog_id_int = int(dialog_id)
            # автоизация по peer_id в таблице
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

            next_botmsg_id = int(event.object['conversation_message_id']) + 1

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
                # day of week: day id(1-7)
                # pin for change
                # list of subjects: 'subject name' by ' '
                user_msg = user_msg[0]
                if len(user_msg) > 2:
                    lessons = [i.capitalize() for i in user_msg[1:]]
                    cursor.execute(f'select * from {"sh" + dialog_id} where id="{day}"')
                    if cursor.fetchall():
                        cursor.execute(f'update {"sh" + dialog_id} set lessons="{str(lessons)}" where id="{day}"')
                        cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
                        if cursor.fetchall():
                            if len(user_msg) > 1:
                                # user_msg[0] = ' '.join(user_msg[0][1:])
                                # user_msg.append('-')
                                cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                                lessons_l = cursor.fetchall()
                                if lessons_l:
                                    text = add_hw(user_msg[1:], day, lessons_l)
                                    if not text:
                                        send_msg("Не прикладывайте картинку.")
                                        continue
                            cursor.execute(f'update {"hw" + dialog_id} set hw="{text}" where id="{day}"')
                    else:
                        cursor.execute(f'insert into {"sh" + dialog_id} values("{day}", "{str(lessons)}")')
                        conn.commit()
                    schedule_now = "\n".join(lessons) + "\nDone"
                    send_msg(schedule_now)
                    conn.close()
                    continue

            '''
                add homework for specific date // перезаписать дз на урок (если есть день, то на него)
                format: addhomework [date](optionally)
                        [subject]: [homework]
            '''
            if user_msg[0][0] in ['addhw', 'addhomework', 'ah', 'дз']:
                # day: пн-сб
                # subject: 'subject name'
                # homework: 'description of homework'

                # на случай пустого собщения после команды
                if len(user_msg[0]) > 1 or event.object['attachments']:
                    user_msg[0] = ' '.join(user_msg[0][1:])

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
                    schedule_now = eval(cursor.fetchall()[0]['lessons'])
                    if lessons and schedule_now:
                        if user_msg[0]:
                            lessons = eval(lessons[0]['hw'])
                            print("now: ", schedule_now)
                            for i in user_msg:
                                i = i.split()
                                print("i", i)
                                if i[0].capitalize() not in schedule_now:
                                    lessons['kucha'] += ' '.join(i) + '-i-'
                                    continue
                                subject = i[0].capitalize()
                                lessons[subject] += ' '.join(i[1:])
                            print("dict", lessons)

                            lessons = str(lessons).replace("'", r"\'").replace('"', r'\"')
                            cursor.execute(f'update {"hw" + dialog_id} set hw="{str(lessons)}" where id="{day}"')
                            conn.commit()

                        attach = None
                        if event.object['attachments']:
                            attach = downloadAttach()  # list
                        if attach:
                            cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{day}"')
                            old_att = cursor.fetchall()[0]['schedule']
                            if old_att != 'gg':
                                old_att = eval(old_att)
                                attach = old_att + attach
                            if old_att:
                                cursor.execute(
                                    f'update {"hw" + dialog_id} set schedule="{str(attach)}" where id="{day}"')
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
                    !День вводить необязательно!
                    предметы <список предметов через пробел>
                    расписание [день]
                    уроки [день] <список предметов через пробел>
                    дз [день] <дз>
                    доп [день] <дз>
                    стереть [день]
                    help, помощь
                    '''
                )
            conn.close()
        except Exception as exc:
            print(exc)
            send_msg("Хватить меня бить:`(")
            continue