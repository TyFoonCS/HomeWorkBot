import requests
import sqlite3
import vk_api
from MyLongPoll import MyVkLongPoll
from data import db
from vk_api import VkUpload
from vk_api.longpoll import VkEventType

session = requests.Session()

vk_session = vk_api.VkApi(token='c2dc3932c3553f743ee9f87a78bdfce9274f9211732aa85a49d5515964c9b4175a4e604d95b3c0329bf8b')
vk = vk_session.get_api()
upload = VkUpload(vk_session)  # Для загрузки изображений
longpoll = MyVkLongPoll(vk_session)
conn, cursor = db("testdb")


def send_msg(msg):
    vk.messages.send(
        user_id=event.user_id,
        random_id=event.random_id,
        message=msg
    )


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        send_msg("Hi")
        print("Ok")
