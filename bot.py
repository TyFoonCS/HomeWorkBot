import requests
import random
import vk_api
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

pin_now = "1488"
empty_req_answers = ("Что надо?", "Звали?", "Доброго времени суток, дамы и господа.\nЧего желаете?", "Чего изволите?")

subjects_list = [
    "алгебра", "биология", "история", "обществознание", "география", "программирование", "английский", "информатика",
    "мп", "физ-ра", "геометрия", "химия", "литература", "астрономия", "русский", "физика", "обж", "поу", "тпнс"
]

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


for event in longpoll.listen():
    print(event.object.keys())
    if event.type == VkBotEventType.MESSAGE_NEW and event.object['text']:
        user_msg = event.object['text'].split()
        if '@' in user_msg[0]:
            if len(user_msg) == 1:
                send_msg(random.choice(empty_req_answers))
                continue
            user_msg = user_msg[1:]
        print(user_msg)

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

        # Проверка на заполнение списка предметов
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id=0')
        fet = cursor.fetchall()
        print(888888, user_msg[0])
        if fet:
            subjects_list = eval(fet[0][0])
        elif user_msg[0] in ['lessons', 'ls', 'предметы']:
            print(777777777777777777)
            lessons_list = user_msg[1:]
            cursor.execute(f'select lessons from {"sh" + dialog_id} where id=0')
            if cursor.fetchall():
                cursor.execute(f'update {"sh" + dialog_id} set lessons="{lessons_list}" where id=0')
                conn.commit()
                send_msg("Список предметов обновлен")
            else:
                cursor.execute(f'insert into {"sh" + dialog_id} values (0, "{lessons_list}")')
                conn.commit()
                send_msg("Список предметов добавлен")
        else:
            send_msg("У вас не заполнен список предметов. Заполните командой ls")
            continue
        # ---------------------------------------

        next_botmsg_id = int(event.object['conversation_message_id']) + 1
        # admin_id = vk.messages.getConversationMembers(peer_id=event.object['peer_id'],
        #                                               fields=event.object['from_id'])
        # print(admin_id)

        # vk.messages.edit(peer_id=event.object['peer_id'],
        #                 message='Working ebat',
        #                 conversation_message_id=next_msg_id)

        '''if event.object['attachments']:
            print(event.object['attachments'])
            attach = ''
            for i in event.object['attachments']:
                attach += i['type']
                attach_obj = i[i['type']]
                attach += str(attach_obj['owner_id']) + '_' + str(attach_obj['id']) + ('_' + attach_obj['access_key']) if attach_obj['access_key'] else '' + ','
            print(attach)
            print(12, event.object['attachments'])
            id_owner = str(event.object['attachments'][0]['photo']['owner_id'])
            id_image = str(event.object['attachments'][0]['photo']['id'])
            key = event.object['attachments'][0]['photo']['access_key']
            id = id_owner + '_' + id_image + '_' + key
            image = vk.photos.getById(photos="182293940_457246115")
            print(image)'''

        ''' 
            show schedule // показать расписание с дз 
            format: schedule [day] (optionally)
        '''
        if user_msg[0] in ['sh', 'schedule', 'расписание', 'рп']:
            # получение расписания
            day = None
            if len(user_msg) > 1 and user_msg[1].isdigit():
                day = int(user_msg[1])
                if day >= 7:
                    day = 1
                cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
            else:
                day = datetime.isoweekday(date.today()) + 1
                if day >= 7:
                    day = 1
                cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')

            data = cursor.fetchall()
            if data:
                data = data[0][0].split('\n')
                for n, i in enumerate(data):
                    if i == 'Остальное ДЗ:':
                        break
                    data[n] = str(n + 1) + '. ' + data[n]

                send_msg('\n'.join(data))

                vk.messages.pin(peer_id=event.object['peer_id'],
                                conversation_message_id=next_botmsg_id)
            else:
                send_msg(
                    "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")
                continue

        '''
            add static schedule // добавить постоянное расписание
            format: addschedule [day of week] <list of subjects>
        '''
        if user_msg[0] in ['addschedule', 'уроки']:
            # day of week: day id(1-7)
            # pin for change
            # list of subjects: 'subject name' by ' '
            if user_msg[1] == pin_now:
                id_day = int(user_msg[2])
                if id_day < 1 or id_day > 6:
                    send_msg(f"Воу-воу, палехче! Учебных дней шесть, а не {id_day}")
                else:
                    lessons = user_msg[3:]
                    cursor.execute(f'select * from {"sh" + dialog_id} where id="{id_day}"')
                    if cursor.fetchall():
                        cursor.execute(f'update {"sh" + dialog_id} set lessons="{str(lessons)}" where id="{id_day}"')
                    else:
                        cursor.execute(f'insert into {"sh" + dialog_id} values("{id_day}", "{str(lessons)}")')
                        conn.commit()
                    schedule_now = "\n".join(lessons) + "\nDone"
                    send_msg(schedule_now)
            else:
                send_msg("Тебе так делать нельзя, фу!")

        '''
            add homework for specific date // добавить дз на определенную дату
            format: addhomework [date](optionally)
                    [subject]: [homework]
        '''
        if user_msg[0] in ['addhw', 'addhomework', 'ah', 'дз']:
            # day: пн-сб
            # subject: 'subject name'
            # homework: 'description of homework'
            day = None

            # на случай пустого собщения после команды
            if len(user_msg) > 1:
                # определение дня для записи
                if user_msg[1] in day_name.keys():
                    day = day_name[user_msg[1]]
                else:
                    day = datetime.isoweekday(date.today()) + 1
                    if day == 7:
                        day = 1

                user_msg = event.object['text'].split('\n')
                user_msg[0] = ' '.join(user_msg[0].split()[2:])
                kucha = ''
                kucha_old = ''
                subject = ''
                subject_hw = ''

                # Уточнение - был ли уже выбранный учебный день на этой неделе
                now_day = datetime.isoweekday(date.today())
                if now_day < day or now_day == 7:
                    cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
                    old = cursor.fetchall()[0][0].split('\n')
                    if len(old) > 5:
                        kucha_old_index = old.index("Остальное ДЗ:")
                        kucha_old = '\n'.join(old[kucha_old_index + 1:]) + '\n'
                        print(12222, kucha_old)
                # ------------------------------------------------------------

                cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                lessons = cursor.fetchall()
                if lessons:
                    lessons = eval(lessons[0][0])
                    text = '\n'.join(lessons)

                    for i in user_msg:
                        i = i.split()
                        print(888, i)
                        if i[0].lower() not in subjects_list:
                            kucha += ' '.join(i) + '\n'
                            continue
                        subject = i[0].capitalize()
                        subject_hw = subject + ' - ' + ' '.join(i[1:])
                        text = text.replace(subject, subject_hw)
                    text += '\nОстальное ДЗ:\n' + kucha_old + kucha
                    print(777, text)
                    cursor.execute(f'update {"hw" + dialog_id} set hw="{text}" where id="{day}"')
                    conn.commit()
                    send_msg("Записано")
                else:
                    send_msg(
                        "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")
                    continue

        '''
            Добавление списка всех предметов. (subjects_list)
            format: ls [subject1] [subject2] ... [subjectN]
        '''
        if user_msg[0] in ['lessons', 'ls', 'предметы']:
            lessons_list = user_msg[1:]
            cursor.execute(f'select lessons from {"sh" + dialog_id} where id=0')
            if cursor.fetchall():
                cursor.execute(f'update {"sh" + dialog_id} set lessons="{lessons_list}" where id=0')
                conn.commit()
                send_msg("Список предметов обновлен")
            else:
                cursor.execute(f'insert into {"sh" + dialog_id} values (0, "{lessons_list}")')
                conn.commit()
                send_msg("Список предметов добавлен")

        '''
            Просмотр списка всех прдеметов. (subjects_list)
            format: list
        '''
        if user_msg[0] in ['list']:
            l = str()
            for i in subjects_list:
                l += ' ' + i
            send_msg(l)

        '''
            show help // показать помощь
        '''
        if user_msg[0] in ['help', 'помощь']:
            send_msg(
                '''Команды и примеры:
                https://vk.com/topic-200162959_46878569
                предметы <список предметов через пробел>
                расписание [день]
                уроки [день] <список предметов через пробел>
                дз [день] <дз>
                help, помощь
                '''
            )
