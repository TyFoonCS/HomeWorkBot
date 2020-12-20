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


def send_msg(msg):
    vk.messages.send(
        peer_id=event.object['peer_id'],
        random_id=random.random(),
        message=msg
    )


for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW and event.object['text']:
        # vk.messages.send(user_id=event.object.message['user_id'], message='Привет', random_id=random.random())
        user_msg = event.object['text']
        if '@' in user_msg.split()[0]:
            user_msg = user_msg[user_msg.find(' ') + 1:]
        print(user_msg)

        ''' 
            show schedule // показать расписание с дз 
            format: schedule [date] (optionally)
        '''
        if user_msg.split()[0] in ['sh', 'shed', 'schedule']:
            # date: 'dd.mm'
            pass

        '''
            add static schedule // добавить постоянное расписание
            format: addschedule [day of week] <list of subjects>
        '''
        if user_msg.split()[0] in ['addschedule']:
            # day of week: 'day name'
            # list of subjects: 'subject name' by ', '
            pass

        '''
            update schedule for specific date // обновить расписание на конкретную дату
            format: updateschedule [date](optionally) <list of subjects>
        '''
        if user_msg.split()[0] in ['updateschedule', 'us']:
            # date: 'dd.mm'
            # list of subjects: 'subject name' by ', '
            pass

        '''
            add homework for specific date // добавить дз на определенную дату
            format: addhomework [date](optionally)
                    [subject]: [homework]
        '''
        if user_msg.split()[0] in ['addhw', 'addhomework', 'ah']:
            # date: 'dd.mm'
            # subject: 'subject name'
            # homework: 'description of homework'
            pass

        '''
            show help // показать помощь
        '''
        if user_msg.split()[0] in ['help']:
            send_msg(
                '''К боту нужно обращаться через @hosbobot
                Примеры команд можете посмотреть в обсуждениях группы
                schedule [дата в формате дд.мм]
                    - показывает расписание на завтрашний день и закрепляет в беседе, или на определенную дату (опционально), можно sh, shed
                addsсhedule [день недели типа "Понедельник"] <список предметов через запятую>
                    - добавляет постоянное расписание на определенный день недели (по умолчанию на следующий учебный день)
                updateshedule [дата в формате дд.мм] <список предметов через запятую>
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
        if user_msg.split()[0] in ['commands', 'cm']:
            send_msg(
                '''schedule [дата в формате дд.мм]
                addsсhedule [день недели типа "Понедельник"] <список предметов через запятую>
                updateshedule [дата в формате дд.мм] <список предметов через запятую>
                addhomework [дата в формате дд.мм] <список заданий по предметам на каждой строке, [предмет]: [задание]>
                commands
                help
                '''
            )
