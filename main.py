import datetime
import io
import os
import random
import time

from dotenv import load_dotenv
import telebot
from sqlmodel import select
import multiprocessing as mp
import tensorflow as tf
from connection import init_db, get_session
from models import Post
from predict_anime_or_meme import predict
from schedule_processing import ScheduleManager

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
bot_manager = ScheduleManager()
CHANNEL_NAME = os.getenv("CHANNEL_NAME")
init_db()
my_model = tf.keras.models.load_model('am_best.keras')


# TODO: config sleep file
def post_img():
    session = get_session()
    session = next(session)
    prev_hour = 9
    post_add_meme = False
    while True:
        now_hour = datetime.datetime.now().hour
        if prev_hour == now_hour:
            time.sleep(600)
            continue
        else:
            gts = random.randint(0, 60 * 59 - 60 * datetime.datetime.now().minute)
            print(datetime.datetime.now(), gts)
            time.sleep(gts)
            if random.randint(1, 3) != 2 or post_add_meme:  # 33% шанс запостить 2 поста где один из них мсем
                prev_hour = now_hour
                post_add_meme = False
            else:
                post_add_meme = True

        if now_hour >= 10:
            if now_hour % 4 == 0 or post_add_meme:
                result = session.exec(select(Post).where(Post.img_type == "meme"))
            else:
                result = session.exec(select(Post).where(Post.img_type == "anime"))
        else:
            time.sleep(600)
            continue
        post = result.first()
        media_append = []
        if not post:
            result = session.exec(select(Post))
            post = result.first()
        if post:
            media_append.append(
                telebot.types.InputMediaPhoto(post.file_id, caption=post.caption, has_spoiler=post.spoiler))
            bot.send_media_group(CHANNEL_NAME, media_append)
            session.delete(post)
            session.commit()
            session.close()


@bot.message_handler(content_types=['photo'])
def get_text_messages(message):
    file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img_type = predict(img_bytes=downloaded_file, model=my_model)
    session = get_session()
    session = next(session)
    post = Post(file_id=file_info.file_id, img_type=img_type, caption=message.caption,
                spoiler=message.has_media_spoiler)

    session.add(post)
    session.commit()
    bot.send_message(message.chat.id, f"{img_type}; \nn in queue: {len(session.exec(select(Post)).all())}",
                     reply_to_message_id=message.message_id)
    session.close()


@bot.message_handler(content_types=['text'])
def manage_schedule(message):
    session = get_session()
    session = next(session)
    txt, media, markup = bot_manager.process_command(message, session)
    bot.send_message(message.chat.id, txt, reply_markup=markup)
    if media:
        bot.send_media_group(message.chat.id, media)
    session.close()


if __name__ == '__main__':
    p = mp.Process(target=post_img)
    p.start()
    while True:
        # bot.polling(non_stop=True, interval=0)
        try:
            bot.polling(non_stop=True, interval=0)
        except Exception as e:
            print(e)
            time.sleep(5)
            continue
