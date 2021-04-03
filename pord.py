import requests
import random
import vk_api
import pytz
from datetime import datetime
from MyLongPoll import MyVkLongPoll
from vk_api import VkUpload
from vk_api.bot_longpoll import VkBotEventType
import pymysql
from pymysql.cursors import DictCursor
import json

session = requests.Session()

prod = False  # True - prod, False - test
if prod:
    vk_session = vk_api.VkApi(
        token='c2dc3932c3553f743ee9f87a78bdfce9274f9211732aa85a49d5515964c9b4175a4e604d95b3c0329bf8b')  # prod
    group_id = 200162959  # prod
    dbname = 'data'
else:
    vk_session = vk_api.VkApi(
        token='dfaee6d1e34934d7030c0bcb1d66f7922fd3c855fee5bbbdb389ac54968c28981a58434e03795943ab426')  # test
    group_id = 202164385  # test
    dbname = 'kakaha'

vk = vk_session.get_api()
upload = VkUpload(vk_session)  # Для загрузки изображений
longpoll = MyVkLongPoll(vk_session, str(group_id))

empty_req_answers = ("Что надо?", "Звали?", "Доброго времени суток, дамы и господа.\nЧего желаете?", "Чего изволите?")
error_stickers = ('17150', '53121', '50121', '8447')

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

help_msg = '''Статья для начала работы:
vk.com/@hosbobot-chto-za-bot
Подробное описание команд:
vk.com/@hosbobot-komandy
Список команд:
!расписание [день]
!уроки [день] <список предметов через пробел>
!дз [день] <дз>
!доп [день] <дз>
!стереть [день]
!помощь
'''


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
        data = json.loads(data[0]['hw'])
        print("DataDone ", data, type(data))

        # запись расписания + дз в text
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
        lessons_l = json.loads(cursor.fetchall()[0]['lessons'])

        print("data", data)
        text = name_day[str(day)] + '\n'
        for i, key in enumerate(lessons_l):
            corrrect_data = '\n'.join(data[key].split('-i-')[:-1])
            if data[key]:
                data[key] = '^^^-i-'
            print(data, corrrect_data)
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
                att = json.loads(att)
                attach = ','.join(att)

        # закрепление или вывод расписания
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id=-1')
        conv = cursor.fetchall()
        if day == now_day or int(day) == ((int(now_day) + 1) if int(now_day) < amount_days else 1):
            # редактирование старого дз
            try:
                if not conv and not personal:
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
                if not personal:
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
        send_msg(
            "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")


def get_schedules():
    schedule_days = {}
    for i in range(1, 7):
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{i}"')
        data = cursor.fetchall()
        if data:
            schedule_days[str(i)] = json.loads(data[0]['lessons'])
    return schedule_days


def to_next_lesson(day, mode):
    # день для фото
    photo_day = False
    # индикатор записи на следующий урок
    next_write = False
    # дни, на которые будет перезаписана домашка
    rewritten_days = []
    # расписание по дням
    schedule_days = get_schedules()
    kucha = []
    for k, words in enumerate(user_msg):
        # день следующего урока
        current = now_day
        # индиктор смены дня
        new_current = False
        words = words.split()
        # список дней, по которым идет этот урок
        lesson_days = []
        print('words: ', words)
        # определение дней по которым идет урок
        for schedule_day in schedule_days.keys():
            if words[0].capitalize() in schedule_days[schedule_day]:
                lesson_days.append(int(schedule_day))

        if not lesson_days:
            kucha.append(words)
            continue
        # выбор дня ближайшего урока
        for i in lesson_days:
            if i > current:
                current = i
                new_current = True
                break
        if not new_current:
            for i in lesson_days:
                if i < current:
                    current = i
                    break
        rewritten_days.append(current)
        # определения дня для записи фото
        if k == 0:
            photo_day = current
        # запись дз на следующий урок
        cursor.execute(f'select hw from {"hw" + dialog_id} where id="{current}"')
        select = cursor.fetchall()
        if select[0]:
            current_hw = json.loads(select[0]['hw'])
            if mode == "add_hw":
                current_hw[words[0].capitalize()] = ' '.join(words[1:]) + '-i-'
            elif mode == "upd_hw":
                current_hw[words[0].capitalize()] += ' '.join(words[1:]) + '-i-'
            current_hw = conn.escape(str(json.dumps(current_hw)))
            cursor.execute(f'update {"hw" + dialog_id} set hw={current_hw} where id="{current}"')
            conn.commit()
    # индикатор запсиси дз на следующий урок дня, используется при вызове функции в блоке add homework
    if day not in rewritten_days:
        next_write = True
    return photo_day, next_write, kucha


def do_kucha(day, kucha, mode):
    if isinstance(kucha, list):
        kucha = '\n'.join([' '.join(i) for i in kucha])
    cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
    hw_kucha = json.loads(cursor.fetchall()[0]['hw'])
    if mode == "add_hw":
        hw_kucha['kucha'] = kucha
    elif mode == "upd_hw":
        hw_kucha['kucha'] += '-i-' + kucha
    hw_kucha = conn.escape(json.dumps(hw_kucha))
    cursor.execute(f'update {"hw" + dialog_id} set hw={hw_kucha} where id="{day}"')
    conn.commit()


def add_hw(user_msg, day):
    photo_day = False
    next_write = False
    if user_msg[0]:
        if user_day:  # запись дз на день недели
            # есть ли расписание
            kucha = ''
            cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
            lessons_l = cursor.fetchall()
            if lessons_l:
                lessons_l = json.loads(lessons_l[0]['lessons'])
                # достать дз из бд
                cursor.execute(f'select * from {"hw" + dialog_id} where id="{day}"')
                hw = json.loads(cursor.fetchall()[0]['hw'])

                for words in user_msg:
                    words = words.split()
                    print('words: ', words)
                    if words[0].capitalize() not in lessons_l:
                        kucha += ' '.join(words) + '-i-'
                        continue
                    subject = words[0].capitalize()
                    hw[subject] = ' '.join(words[1:]) + '-i-'
                # запись дз на день
                hw = conn.escape(str(json.dumps(hw)))
                cursor.execute(f'update {"hw" + dialog_id} set hw={hw} where id="{day}"')
                conn.commit()

            else:
                send_msg(
                    "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу)")
        else:  # запись дз на следующий урок
            photo_day, next_write, kucha = to_next_lesson(day, "add_hw")

        # работа с кучей
        if kucha:
            do_kucha(day, kucha, "add_hw")
            if not user_day:
                next_write = False

    # определение дня для записи фото
    if not photo_day:
        photo_day = day
    # обработка фото
    attach = None
    if event.object['attachments']:
        attach = download_attach()  # list
    if attach:
        attach = conn.escape(str(json.dumps(attach)))

        # чистка кучи в случае отсутствия текста
        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{photo_day}"')
        if not user_msg[0] and cursor.fetchall():
            cursor.execute(f'select hw from {"hw" + dialog_id} where id="{photo_day}"')
            hw_now = json.loads(str(cursor.fetchall()[0]['hw']))

            hw_now['kucha'] = ''
            hw_now = conn.escape(str(json.dumps(hw_now)))
            cursor.execute(f'update {"hw" + dialog_id} set hw={hw_now} where id="{photo_day}"')
            # conn.commit() !!!
        # ------------
        cursor.execute(f'update {"hw" + dialog_id} set schedule={attach} where id="{photo_day}"')
        conn.commit()
    return next_write


# дополнение дз
def upd_hw(user_msg, day, lessons_l, hw):
    # день для фото
    photo_day = False
    # индикатор записи на следующий урок
    next_write = False

    kucha = ''
    if user_msg[0]:
        if user_day:
            hw = json.loads(hw[0]['hw'])
            lessons_l = json.loads(lessons_l[0]['lessons'])
            print("now: ", lessons_l)
            for i in user_msg:
                i = i.split()
                print("i", i)
                if i[0].capitalize() not in lessons_l:
                    hw['kucha'] += ' '.join(i) + '-i-'
                    continue
                subject = i[0].capitalize()
                if i[1:]:
                    hw[subject] += ' '.join(i[1:]) + '-i-'
            print("dict", hw)
            hw = conn.escape(str(json.dumps(hw)))
            cursor.execute(f'update {"hw" + dialog_id} set hw={hw} where id="{day}"')
            conn.commit()
        else:
            photo_day, next_write, kucha = to_next_lesson(day, "upd_hw")

        # работа с кучей
        if kucha:
            do_kucha(day, kucha, "upd_hw")
            if not user_day:
                next_write = False

    # определение дня для записи фото
    if not photo_day:
        photo_day = day
    # дополнение фото
    attach = None
    if event.object['attachments']:
        attach = download_attach()  # list
    if attach:
        cursor.execute(f'select schedule from {"hw" + dialog_id} where id="{photo_day}"')
        old_att = cursor.fetchall()[0]['schedule']
        if old_att != 'gg':
            old_att = json.loads(old_att)
            print(type(old_att), type(attach))
            attach = str(json.dumps(old_att + attach))
        else:
            attach = str(json.dumps(attach))
        attach = conn.escape(attach)
        if old_att:
            cursor.execute(
                f'update {"hw" + dialog_id} set schedule={attach} where id="{photo_day}"')
            conn.commit()
        else:
            cursor.execute(f'insert into {"hw" + dialog_id} values ("{photo_day}", "gg", "")')
            conn.commit()
    return next_write


# скачивание и загрузка обратно
def download_attach():
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
        with open('img.jpg', 'wb') as ph_file:
            ph_file.write(requests.get(ph_url).content)
        photo = upload.photo_messages(photos=open('img.jpg', 'rb'), peer_id=event.object['peer_id'])[0]
        attach.append(f"photo{photo['owner_id']}_{photo['id']}")
    return attach


# функция чистки дня: заменяет старое hw в таблице hw2000... на словарь hw с расписанием, но без дз
def clean(day, lessons_l):
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


for event in longpoll.listen():
    try:
        conn = pymysql.connect(
            host='89.223.94.40',
            user='tyfooncs',
            password='P@ssw0rd',
            db=dbname,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        cursor = conn.cursor()
    except Exception as e:
        print(e)
        send_msg("Проблемы с сервером. Мы уже работаем над этой проблемой.")
        continue
    if event.type == VkBotEventType.MESSAGE_NEW:
        dialog_id = int(event.object['peer_id'])
        personal = False
        admin = False
        if dialog_id in ("167849130", "182293940"):
            admin = True
        if dialog_id < 2000000000:
            personal = True
            cursor.execute(f'select conv from users where user="{dialog_id}"')
            fetch = cursor.fetchall()
            print(9, fetch)
            if fetch and fetch[0]:
                dialog_id = fetch[0]['conv']
            else:
                send_msg("Ты еще не засветился ни в одной классной беседе\nПопробуй написать !рп в беседу своего класса, а потом возвращайся сюда")
        dialog_id = str(dialog_id)
        if event.object['text']:
            try:
                user = vk.users.get(user_ids=event.object['from_id'])
                print('\n', event.object['peer_id'], user[0]['first_name'], user[0]['last_name'], event.object['text'],
                      '\n')
                if not personal:
                    from_user = int(event.object['from_id'])
                    cursor.execute(f'select user from users where user="{from_user}"')
                    if cursor.fetchall():
                        cursor.execute(f'update users set conv="{dialog_id}" where user="{from_user}"')
                    else:
                        cursor.execute(f'insert into users values ("{from_user}", "{dialog_id}")')
                    conn.commit()

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
                if '@' in user_msg[0][0]:
                    conn.close()
                    continue

                # проверка на восклицательный знак перед командой
                if user_msg[0][0][0] == '!':
                    user_msg[0][0] = user_msg[0][0][1:]
                else:
                    conn.close()
                    continue

                # id следующего сообщения бота
                next_botmsg_id = int(event.object['conversation_message_id']) + 1

                # God Mode
                if admin:
                    '''
                        !db // database manage
                        format: !db [request]
                    '''
                    if user_msg[0][0] == 'db':
                        req = ' '.join(user_msg[0][1:])
                        try:
                            cursor.execute(req)
                            conn.commit()
                        except Exception as exc:
                            send_msg('Ошибка:\n' + str(exc))
                            conn.close()
                            continue
                        raw_fetch = cursor.fetchall()
                        if raw_fetch:
                            fetch = [' '.join(list(raw_fetch[0].keys()))]
                            for n, i in enumerate(raw_fetch):
                                fetch.append([])
                                for j in list(i.keys()):
                                    if "\\u" in str(i[j]):
                                        fetch[n+1].append(json.loads(i[j]))
                                    else:
                                        fetch[n+1].append(i[j])
                                fetch[n+1] = ' '.join([str(k) for k in fetch[n+1]])
                        else:
                            fetch = raw_fetch
                        send_msg("Done Admin!\n{}".format('\n'.join(fetch)))

                    '''
                        !sc // send to some chat
                        format: !sc [chat_id without 2000....] [msg]
                    '''
                    if user_msg[0][0] == 'sc':
                        chat_id = 2000000000 + int(user_msg[0][1])
                        user_msg[0] = ' '.join(user_msg[0][2:])
                        vk.messages.send(
                            peer_id=chat_id,
                            random_id=random.random(),
                            message='\n'.join(user_msg)
                        )
                        send_msg("Done Admin!")

                    '''
                        !new // new bot chat authorization
                        format: !new [chat_id without 2000....]
                    '''
                    if user_msg[0][0] == 'new':
                        chat_id = 2000000000 + int(user_msg[0][1])
                        # проверка на уже существующую беседу в БД
                        cursor.execute(f'select id from dialogs where id="{chat_id}"')
                        if cursor.fetchall():
                            send_msg("Эта беседа уже авторизована")
                            conn.close()
                            continue
                        # создание таблиц для новой беседы
                        cursor.execute(f'insert into dialogs values("{chat_id}", NULL)')
                        cursor.execute(f'create table {"sh" + str(chat_id)} (id integer, lessons text)')
                        cursor.execute(f'create table {"hw" + str(chat_id)} (id integer, schedule text, hw text)')
                        send_msg("Бот готов работать в этой беседе. Напомни им про админку для него!")

                    '''
                        !spam // send msg to all
                        format: !spam [msg]
                    '''
                    if user_msg[0][0] == 'spam':
                        cursor.execute('select id from dialogs')
                        ids = [list(i.values())[0] for i in cursor.fetchall()]
                        user_msg[0] = ' '.join(user_msg[0][1:])
                        attach_wall = None
                        if 'wall' in user_msg[-1]:
                            attach_wall = user_msg[-1][user_msg[-1].rfind('wall'):]
                            user_msg = user_msg[:-1]
                        for chat_id in ids:
                            vk.messages.send(
                                peer_ids=chat_id,
                                random_id=random.random(),
                                message='\n'.join(user_msg),
                                attachment=attach_wall
                            )
                        send_msg("Done Admin!")

                    # разрыв соединения с БД и конец итерации
                    conn.close()
                    continue

                # определение дня
                user_day = False
                day = None
                now_day = datetime.isoweekday(datetime.now(pytz.timezone('Asia/Dubai')))
                if len(user_msg[0]) > 1:
                    if user_msg[0][1] in day_name.keys():
                        day = int(day_name[user_msg[0][1]])
                        del user_msg[0][1]
                        user_day = True
                if not day:
                    day = now_day + 1
                if day >= 7:
                    day = 1
                amount_days = 6

                # авторизация по peer_id в таблице
                '''cursor.execute('select * from dialogs')
                ids = cursor.fetchall()
                auth_bot = False
                for now_id in ids:
                    if int(dialog_id) == now_id['id']:
                        auth_bot = True
                        break
                if not auth_bot:
                    send_msg("Эта беседа еще не приобрела подписку, либо менеджер еще не занес эту беседу в базу.")
                    conn.close()
                    continue'''

                # -----------------------------------------

                user_msg[0][0] = user_msg[0][0].lower()

                '''
                    add static schedule // добавить постоянное расписание
                    format: !addschedule [day of week] <list of subjects>
                '''
                if user_msg[0][0] in ('addschedule', 'уроки') and not personal:
                    user_msg = user_msg[0]
                    if len(user_msg) > 2 and user_day:
                        lessons = [i.capitalize() for i in user_msg[1:]]
                        lessons = str(json.dumps(lessons))

                        # обновление sh таблицы
                        cursor.execute(f'select * from {"sh" + dialog_id} where id="{day}"')
                        if cursor.fetchall():
                            cursor.execute(
                                f'update {"sh" + dialog_id} set lessons={conn.escape(lessons)} where id="{day}"')
                        else:
                            cursor.execute(
                                f'insert into {"sh" + dialog_id} values("{day}", {conn.escape(lessons)})')
                            conn.commit()
                        # заполнение таблицы hw
                        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                        clean(day, cursor.fetchall())
                        sh_out()
                    else:
                        send_msg('Пожалуйста, укажите день')
                    conn.close()
                    continue

                # проверка на пятидневку
                cursor.execute(f'select id from {"hw" + dialog_id} where id=6')
                if not cursor.fetchall():
                    amount_days = 5
                    if day == 6:
                        day = 1
                else:
                    amount_days = 6
                print("DAAAAY: " + str(day))

                '''
                    show schedule // вывести и закрепить дз
                    format: !schedule [day] (optionally)
                '''
                if user_msg[0][0] in ('sh', 'schedule', 'расписание', 'рп'):
                    sh_out()
                    conn.close()
                    continue

                '''
                    add homework for specific date // перезаписать дз на урок (если есть день, то на него)
                    format: !addhomework [date](optionally)
                            [subject]: [homework]
                '''
                if user_msg[0][0] in ('addhw', 'addhomework', 'ah', 'дз') and not personal:
                    if len(user_msg[0]) > 1 or event.object['attachments']:
                        user_msg[0] = ' '.join(user_msg[0][1:])
                        not_sh_out = add_hw(user_msg, day)
                        if not_sh_out:
                            send_msg("Записал")
                        else:
                            sh_out()
                        conn.close()
                        continue

                '''
                    extend homework for specific date // дописать дз на урок (если есть день, то на него)
                    format: !updatehomework [date](optionally)
                            [subject]: [homework]
                '''
                if user_msg[0][0] in ('updatehomework', 'uh', 'доп') and not personal:
                    if len(user_msg[0]) > 1 or event.object['attachments']:
                        user_msg[0] = ' '.join(user_msg[0][1:])

                        cursor.execute(f'select hw from {"hw" + dialog_id} where id="{day}"')
                        hw = cursor.fetchall()
                        cursor.execute(f'select lessons from {"sh" + dialog_id} where id="{day}"')
                        lessons_l = cursor.fetchall()

                        if hw and lessons_l:
                            not_sh_out = upd_hw(user_msg, day, lessons_l, hw)
                            if not_sh_out:
                                send_msg("Записал")
                            else:
                                sh_out()
                            conn.close()
                            continue
                        else:
                            send_msg(
                                "У вас не заполнено расписание. Для работы бота необходимо заполнить расписание на каждый учебный день(с понедельника по субботу). Также возможны никто еще не заполнял первичное ДЗ командой дз, таким образом вам нечего дополнять.")
                            conn.close()
                            continue

                '''
                    clean specific day // очистить дз на определенный день
                    format: !clean [day]
                '''
                if user_msg[0][0] in ('cl', 'clean', 'чистка', 'стереть') and not personal:
                    if user_day:
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
                    show chat id // вывести id беседы
                    format: !id
                '''
                if user_msg[0][0] in ('id', 'айди'):
                    send_msg('ID беседы : ' + str(int(dialog_id) - 2000000000))
                    conn.close()
                    continue

                '''
                    show help // показать помощь
                    format: !help
                '''
                if user_msg[0][0] in ('help', 'помощь'):
                    send_msg(help_msg)

                conn.close()
            except Exception as exc:
                print("general end exc: ", exc)
                conn.close()
                send_msg("Хватить меня бить:`(")
                vk.messages.send(
                    peer_ids=event.object['peer_id'],
                    random_id=random.random(),
                    sticker_id=random.choice(error_stickers)
                )
                continue

        if 'action' in event.object.keys() and event.object['action']['type'] == 'chat_invite_user' and event.object['action']['member_id'] == -group_id:
            cursor.execute(f'select id from dialogs where id="{int(dialog_id)}"')
            if not cursor.fetchall():
                cursor.execute(f'insert into dialogs values("{int(dialog_id)}", NULL)')
                cursor.execute(f'create table {"sh" + str(int(dialog_id))} (id integer, lessons text)')
                cursor.execute(f'create table {"hw" + str(int(dialog_id))} (id integer, schedule text, hw text)')
                vk.messages.send(
                    peer_ids=event.object['peer_id'],
                    random_id=random.random(),
                    sticker_id='21'
                )
                send_msg(
                    'Всем привет!\nПервым делом для работы мне нужна админка\nКак только добавите, !помощь для получения команд')
            conn.close()
