from typing import List, Tuple

import telebot
from sqlmodel import select

from models import Post


class ScheduleManager:

    def __init__(self):
        self.now_status = None
        self.context_data = None
        self.__context_status = None

    def goto_main(self, **kwargs) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.now_status = "main"
        self.context_data = {}
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]
        return "здарова, кореш", None, buttons

    def last(self, session) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.now_status = "showing_post"
        self.context_data = {"iteration": {"offset": 0}}
        result = session.exec(select(Post))
        post = result.first()
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]

        return f"id: {post.id}, file_id: {post.file_id}, caption: {post.caption}", [telebot.types.InputMediaPhoto(
            post.file_id, caption=post.caption,
            has_spoiler=post.spoiler)], buttons

    def next_post(self, session) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.context_data["iteration"]["offset"] += 1
        result = session.exec(select(Post).offset(self.context_data["iteration"]["offset"]))
        post = result.first()
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]

        return f"id: {post.id}, file_id: {post.file_id}, caption: {post.caption}", [telebot.types.InputMediaPhoto(
            post.file_id, caption=post.caption,
            has_spoiler=post.spoiler)], buttons

    def get_status(self):
        return self.__context_status.get(self.now_status, []).keys()

    def get_status_action(self, text):
        return self.__context_status[self.now_status][text]

    def set_context(self):
        if not self.__context_status:
            self.__context_status = {
                "main": {"Последний": self.last, "Очередь (общая)": {}, "Очередь мемов": {}, "Очередь аниме": {},
                         "Найти и изменить": {}},
                "showing_post": {"Следующий": self.next_post, "Предыдущий": {}, "Изменить": {},
                                 "Главная": self.goto_main},
                "showing_list": {"Следующие 10", "Предыдущие 10", "Главная"},
                "editing": {"Изменить содержание", "Удалить", "Назад", "Главная"},
                "deleting": {"Да", "Нет"},
                "search": {}

            }
            self.now_status = "main"
            self.context_data = {}

    def process_command(self, message: telebot.types.Message, session):
        self.set_context()
        print(self.now_status)

        if self.now_status == "search" or message.text in self.get_status():
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            action_for_command = self.get_status_action(message.text)
            txt, media, buttons = action_for_command(session=session)
            if buttons is None:
                return txt, media, None
            else:
                markup.add(*buttons)
            return txt, media, markup
        else:
            txt, media, buttons = self.goto_main()
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(*buttons)
            return txt, media, markup

