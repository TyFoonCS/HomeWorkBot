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


def send_msg(msg):
    vk.messages.send(
        peer_id=event.object['peer_id'],
        random_id=random.random(),
        message=msg
    )


for event in longpoll.listen():
    print(event.object.keys())
    if event.type == VkBotEventType.MESSAGE_NEW and event.object['text']:

        # vk.messages.send(user_id=event.object.message['user_id'], message='Привет', random_id=random.random())

        user_msg = event.object['text'].split()

        '''if event.object['attachments']:
            print(12, event.object['attachments'])
            id_owner = str(event.object['attachments'][0]['photo']['owner_id'])
            id_image = str(event.object['attachments'][0]['photo']['id'])
            key = event.object['attachments'][0]['photo']['access_key']
            id = id_owner + '_' + id_image + '_' + key
            image = vk.photos.getById(photos="182293940_457246115")
            print(image)'''

        if '@' in user_msg[0]:
            if len(user_msg) == 1:
                send_msg(random.choice(empty_req_answers))
                continue
            user_msg = user_msg[1:]
        print(user_msg)

        ''' 
            show schedule // показать расписание с дз 
            format: schedule [day] (optionally)
        '''
        if user_msg[0] in ['sh', 'schedule']:
            # получение расписания
            day = None
            if len(user_msg) > 1 and user_msg[1].isdigit():
                day = int(user_msg[1])
                if day >= 7:
                    day = 1
                cursor.execute(f'select lessons from schedule where id="{day}"')
            else:
                day = datetime.isoweekday(date.today()) + 1
                if day >= 7:
                    day = 1
                cursor.execute(f'select lessons from schedule where id="{day}"')
            data = eval(cursor.fetchall()[0][0])
            # получение ДЗ

            if not day:
                day = datetime.isoweekday(date.today()) + 1
            cursor.execute(f'select hw from days where id="{day}"')
            hw = cursor.fetchall()
            if hw:
                hw = "\nДомашка:\n" + hw[0][0]
            else:
                hw = '\nДомашка:\nнеизвестно'
            # отправка
            schedule = "\n".join(data)

            send_msg(schedule + hw)
        '''
            add static schedule // добавить постоянное расписание
            format: addschedule [day of week] <list of subjects>
        '''
        if user_msg[0] in ['addschedule']:
            # day of week: day id(1-7)
            # pin for change
            # list of subjects: 'subject name' by ' '
            if user_msg[1] == pin_now:
                id_day = int(user_msg[2])
                if id_day < 1 or id_day > 6:
                    send_msg(f"Воу-воу, палехче! Учебных дней шесть, а не {id_day}")
                else:
                    lessons = user_msg[3:]
                    cursor.execute(f'select * from schedule where id="{id_day}"')
                    if cursor.fetchall():
                        cursor.execute(f'update schedule set lessons="{str(lessons)}" where id="{id_day}"')
                    else:
                        cursor.execute(f'insert into schedule values("{id_day}", "{str(lessons)}")')
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
        if user_msg[0] in ['addhw', 'addhomework', 'ah']:
            # day: 1-6
            # subject: 'subject name'
            # homework: 'description of homework'
            day = user_msg[1]
            if day.isdigit():
                day = int(day)
                if day >= 1 or day <= 6:
                    text = " ".join(user_msg[2::])
                    if len(text) < 400:
                        cursor.execute(f'select hw from days where id="{day}"')
                        now = cursor.fetchall()[0][0]
                        if now:
                            text = now + '\n' + text
                            cursor.execute(f'update days set hw="{text}" where id="{day}"')
                        cursor.execute(f'insert into days values ("{day}", "schedule", "{text}")')
                        conn.commit()
                        send_msg('Done')
                    else:
                        send_msg("ты гей")
            else:
                send_msg("ты гей")

        '''
            show help // показать помощь
        '''
        if user_msg[0] in ['help']:
            send_msg(
                '''К боту в беседе нужно обращаться через @hosbobot
                Примеры команд можете посмотреть в обсуждениях группы
                schedule [дата в формате дд.мм]
                    - показывает расписание на завтрашний день и закрепляет в беседе, или на определенную дату (опционально), можно sh
                addsсhedule [день недели типа "Понедельник"] <список предметов через запятую>
                    - добавляет постоянное расписание на определенный день недели (по умолчанию на следующий учебный день)
                updateschedule [дата в формате дд.мм] <список предметов через запятую>
                    - изменить расписание на определенную дату (по умолчанию на следующий учебный день), можно us
                addhomework [дата в формате дд.мм] <список заданий по предметам на каждой строке, [предмет]: [задание]>
                    - добавить или изменить задание на определенную дату (по умолчанию на следующий учебный день), можно addhw, ah
                commands
                    - показать список команд, cm
                help
                    - показать помощь
                '''
            )

        '''
            show commands // показать команды
        '''
        if user_msg[0] in ['commands', 'cm']:
            send_msg(
                '''schedule [дата в формате дд.мм]
                addsсhedule [день недели типа "Понедельник"] <список предметов через запятую>
                addhomework [дата в формате дд.мм] <список заданий по предметам на каждой строке, [предмет]: [задание]>
                commands
                help
                '''
            )
