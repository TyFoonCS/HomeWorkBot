import requests
import random
import vk_api
import pytz
from datetime import datetime, date
from MyLongPoll import MyVkLongPoll
from data import db
from vk_api import VkUpload
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

session = requests.Session()

vk_session = vk_api.VkApi(token='c2dc3932c3553f743ee9f87a78bdfce9274f9211732aa85a49d5515964c9b4175a4e604d95b3c0329bf8b')
vk = vk_session.get_api()
upload = VkUpload(vk_session)  # Для загрузки изображений
longpoll = MyVkLongPoll(vk_session, "200162959")
# longpoll = VkBotLongPoll(vk_session, "200162959")
conn, cursor = db("testdb")

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


def send_msg(msg):
    return vk.messages.send(
        peer_ids=event.object['peer_id'],
        random_id=random.random(),
        message=msg
    )


def sh_out():
    cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
    data = cursor.fetchall()
    if data:
        data = eval(data[0][0])
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
        lessons = eval(cursor.fetchall()[0][0])
        print("data", data)
        text = ''
        for i, key in enumerate(lessons):
            text += str(i + 1) + '. ' + key + ': ' + data[key] + '\n'
        text += 'Остальное ДЗ:\n' + data['kucha']

        cursor.execute(f'select lessons from {"sh" + dialog_id} where id=-1')
        try:
            print(7777)
            vk.messages.edit(peer_id=event.object['peer_id'],
                             message=text,
                             conversation_message_id=int(cursor.fetchall()[0][0]))
            print(8888)
            send_msg("Отредачил закреп")
            print(9999)
        except vk_api.exceptions.ApiError as exc:
            print(exc)
            if str(exc).split()[0][1:-1] in ('900', '15', '910', '914', '909'):
                send_msg(text)
                vk.messages.pin(peer_id=event.object['peer_id'], conversation_message_id=next_botmsg_id)
                cursor.execute(f'select * from sh{dialog_id} where id=-1')
                if cursor.fetchall():
                    cursor.execute(f'update {"sh" + dialog_id} set lessons="{str(next_botmsg_id)}" where id=-1')
                    conn.commit()
                else:
                    cursor.execute(f'insert into {"sh" + dialog_id} values (-1, "{str(next_botmsg_id)}")')
                    conn.commit()
    else:
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
        schedule = cursor.fetchall()
        print(schedule)
        if schedule:
            schedule = eval(schedule[0][0])
            text = ''
            for i, lesson in enumerate(schedule):
                print(i, lesson)
                text += str(i + 1) + '. ' + lesson + '\n'
            send_msg(text)
        else:
            send_msg(
                "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.object['text']:

        # godmode
        god = False
        if event.object['from_id'] in [167849130]:
            god = True

        user_msg = event.object['text'].split('\n')
        user_msg[0] = user_msg[0].split()
        if '@' in user_msg[0][0]:
            if len(user_msg[0]) == 1:
                send_msg(random.choice(empty_req_answers))
                continue
            user_msg[0] = user_msg[0][1:]

        # определение дня
        day = datetime.isoweekday(datetime.now(pytz.timezone('Asia/Dubai'))) + 1
        if len(user_msg[0]) > 1:
            if user_msg[0][1] in day_name.keys():
                day = int(day_name[user_msg[0][1]])
                del user_msg[0][1]
        if day == 7:
            day = 1

        dialog_id = str(event.object['peer_id'])
        dialog_id_int = int(dialog_id)
        # автоизация по peer_id в таблице
        cursor.execute('select * from dialogs')
        ids = cursor.fetchall()
        auth_bot = False
        for id in ids:
            if dialog_id_int in id:
                auth_bot = True
                break
        if not auth_bot:
            send_msg("Эта беседа еще не приобрела подписку, либо менеджер еще не занес эту беседу в базу.")
            continue
        # -------------------------------

        next_botmsg_id = int(event.object['conversation_message_id']) + 1

        ''' 
            show schedule // вывести и закрепить дз
            format: schedule [day] (optionally)
        '''
        if user_msg[0][0] in ['sh', 'schedule', 'расписание', 'рп']:
            sh_out()
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
                else:
                    cursor.execute(f'insert into {"sh" + dialog_id} values("{day}", "{str(lessons)}")')
                    conn.commit()
                schedule_now = "\n".join(lessons) + "\nDone"
                send_msg(schedule_now)
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
            if len(user_msg[0]) > 1:
                user_msg[0] = ' '.join(user_msg[0][1:])

                cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                lessons_l = cursor.fetchall()
                if lessons_l:
                    lessons_l = eval(lessons_l[0][0])
                    lessons = dict()
                    for les in lessons_l:
                        lessons[les] = ''
                    lessons['kucha'] = ''
                    print(user_msg)
                    for i in user_msg:
                        i = i.split()
                        print("i", i)
                        if i[0].capitalize() not in lessons_l:
                            lessons['kucha'] += ' '.join(i) + '\n'
                            continue
                        subject = i[0].capitalize()
                        lessons[subject] += ' ' + ''.join(i[1:])
                    print("dict", lessons)
                    cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
                    if cursor.fetchall():
                        cursor.execute(f'update {"hw" + dialog_id} set hw="{str(lessons)}" where id="{day}"')
                        conn.commit()
                    else:
                        cursor.execute(f'insert into {"hw" + dialog_id} values ("{day}", "gg", "{str(lessons)}")')
                    sh_out()
                else:
                    send_msg(
                        "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")
                    continue

        '''
            extend homework for specific date // дописать дз на урок (если есть день, то на него)
            format: updatehomework [date](optionally)
                    [subject]: [homework]
        '''
        if user_msg[0][0] in ['updatehomework', 'uh', 'допдз']:

            if len(user_msg[0]) > 1:
                user_msg[0] = ' '.join(user_msg[0][1:])

                cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
                lessons = cursor.fetchall()
                cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                schedule_now = cursor.fetchall()
                if lessons and schedule_now:
                    lessons = eval(lessons[0][0])

                    for i in user_msg:
                        i = i.split()
                        print("i", i)
                        if i[0].capitalize() not in lessons_l:
                            lessons['kucha'] += ' '.join(i) + '\n'
                            continue
                        subject = i[0].capitalize()
                        lessons[subject] += ' ' + ''.join(i[1:])
                    print("dict", lessons)
                    cursor.execute(f'update {"hw" + dialog_id} set hw="{str(lessons)}" where id="{day}"')
                    conn.commit()
                    sh_out()
                else:
                    send_msg(
                        "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")
                    continue

        '''
            show help // показать помощь
        '''
        if user_msg[0][0] in ['help', 'помощь']:
            send_msg(
                '''Команды и примеры:
                https://vk.com/topic-200162959_46878569
                предметы <список предметов через пробел>
                расписание [день]
                уроки [день] <список предметов через пробел>
                дз [день] <дз>
                допдз [день] <дз>
                help, помощь
                '''
            )
