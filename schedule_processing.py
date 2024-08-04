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
        return "Здарова, кореш", None, buttons

    def last(self, session) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.now_status = "showing_post"

        result = session.exec(select(Post))
        post = result.first()
        if not self.context_data.get("iteration"):
            self.context_data = {"iteration": {"offset": 0}, "post_data": {"post_id": post.id}}
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]

        return f"id: {post.id}, file_id: {post.file_id}, caption: {post.caption}, type:{post.img_type}", [
            telebot.types.InputMediaPhoto(
                post.file_id, caption=post.caption,
                has_spoiler=post.spoiler)], buttons

    def next_post(self, session) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.context_data["iteration"]["offset"] += 1
        result = session.exec(select(Post).offset(self.context_data["iteration"]["offset"]))
        post = result.first()
        self.context_data["post_data"]["post_id"] = post.id
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]

        return f"id: {post.id}, file_id: {post.file_id}, caption: {post.caption}, type:{post.img_type}", [
            telebot.types.InputMediaPhoto(
                post.file_id, caption=post.caption,
                has_spoiler=post.spoiler)], buttons

    def prev_post(self, session) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        if self.context_data["iteration"]["offset"] > 0:
            self.context_data["iteration"]["offset"] -= 1
        else:
            self.context_data["iteration"]["offset"] = len(session.exec(select(Post)).all()) - 1
        result = session.exec(select(Post).offset(self.context_data["iteration"]["offset"]))
        post = result.first()
        self.context_data["post_data"]["post_id"] = post.id
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]

        return f"id: {post.id}, file_id: {post.file_id}, caption: {post.caption}, type:{post.img_type}", [
            telebot.types.InputMediaPhoto(
                post.file_id, caption=post.caption,
                has_spoiler=post.spoiler)], buttons

    def return_context(self, **kwargs) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        if self.context_data["prev_context"]:
            self.now_status = self.context_data["prev_context"]["prev_status"]
        else:
            self.now_status = "main"

        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]
        return f"Почапали...", None, buttons

    def edit_post(self, **kwargs) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.context_data["prev_context"] = {"prev_status": self.now_status}
        self.now_status = "editing"
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]
        return f"Что делаем?", None, buttons

    def delete_post(self, **kwargs) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.now_status = "deleting"
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]
        return f"Удаляем?", None, buttons

    def delete_yes(self, session) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.now_status = "main"
        post = session.get(Post, self.context_data["post_data"]["post_id"])
        session.delete(post)
        session.commit()
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]
        return f"Удалили...", None, buttons

    def delete_no(self, **kwargs) -> Tuple[str, List[telebot.types.InputMediaPhoto] | None, List]:
        self.now_status = "main"
        buttons = [telebot.types.KeyboardButton(key) for key in self.get_status()]
        return f"га га га", None, buttons

    def get_status(self):
        return self.__context_status.get(self.now_status, []).keys()

    def get_status_action(self, text):
        return self.__context_status[self.now_status][text]

    def set_context(self):
        if not self.__context_status:
            self.__context_status = {
                "main": {"Последний": self.last, "Очередь (общая)": {}, "Очередь мемов": {}, "Очередь аниме": {},
                         "Найти и изменить": {}},
                "showing_post": {"Следующий": self.next_post, "Предыдущий": self.prev_post, "Изменить": self.edit_post,
                                 "Главная": self.goto_main},
                "showing_list": {"Следующие 10", "Предыдущие 10", "Главная"},
                "editing": {"Изменить содержание": {}, "Удалить": self.delete_post, "Назад": self.return_context,
                            "Главная": self.goto_main},
                "deleting": {"Да": self.delete_yes, "Нет": self.goto_main},
                "search": {}

            }
            self.now_status = "main"
            self.context_data = {}

    def process_command(self, message: telebot.types.Message, session):
        self.set_context()
        print(self.now_status)

        if self.now_status == "search" or message.text in self.get_status():
            print(self.context_data)
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
