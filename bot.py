import requests
import random
import vk_api
import datetime
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


def send_msg(msg):
    vk.messages.send(
        peer_id=event.object['peer_id'],
        random_id=random.random(),
        message=msg
    )


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.object['text']:

        # vk.messages.send(user_id=event.object.message['user_id'], message='Привет', random_id=random.random())

        user_msg = event.object['text'].split()

        if '@' in user_msg[0]:
            user_msg = user_msg[1:]
        print(user_msg)

        ''' 
            show schedule // показать расписание с дз 
            format: schedule [day] (optionally)
        '''
        if user_msg[0] in ['sh', 'schedule']:
            cursor.execute(f'select lessons from schedule where id="{user_msg[1]}"')
            data = eval(cursor.fetchall()[0][0])
            schedule = "\n".join(data)
            send_msg(schedule)
        '''
            add static schedule // добавить постоянное расписание
            format: addschedule [day of week] <list of subjects>
        '''
        if user_msg[0] in ['addschedule']:
            # day of week: day id(1-7)
            # pin for change
            # list of subjects: 'subject name' by ' '
            if user_msg[1] == pin_now:
                id_day = user_msg[2]
                lessons = user_msg[3:]
                cursor.execute(f'select * from schedule where id="{id_day}"')
                if cursor.fetchall():
                    cursor.execute(f'update schedule set lessons="{str(lessons)}" where id="{id_day}"')
                else:
                    cursor.execute(f'insert into schedule values("{id_day}", "{str(lessons)}")')
                    conn.commit()
                schedule_now = "\n".join(lessons) + "Done"
                send_msg(schedule_now)
            else:
                send_msg("Тебе так делать нельзя, фу!")
        '''
            update schedule for specific date // обновить расписание на конкретную дату
            format: updateschedule [date](optionally) <list of subjects>
        '''
        if user_msg[0] in ['updateschedule', 'us']:
            # date: 'dd.mm'
            # list of subjects: 'subject name' by ', '
            pass

        '''
            add homework for specific date // добавить дз на определенную дату
            format: addhomework [date](optionally)
                    [subject]: [homework]
        '''
        if user_msg[0] in ['addhw', 'addhomework', 'ah']:
            # date: 'dd.mm'
            # subject: 'subject name'
            # homework: 'description of homework'
            pass

        '''
            show help // показать помощь
        '''
        if user_msg[0] in ['help']:
            send_msg(
                '''К боту нужно обращаться через @hosbobot
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
                updateschedule [дата в формате дд.мм] <список предметов через запятую>
                addhomework [дата в формате дд.мм] <список заданий по предметам на каждой строке, [предмет]: [задание]>
                commands
                help
                '''
            )
