from vk_api.bot_longpoll import VkBotLongPoll


class MyVkLongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                print('error vk', e)
