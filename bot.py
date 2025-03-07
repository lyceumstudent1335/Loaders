from telebot.async_telebot import AsyncTeleBot, types
import asyncio
from dotenv import load_dotenv, set_key
import os
from json import loads, dumps
import aiosqlite

load_dotenv()

API_TOKEN = os.environ.get("API_TOKEN")
GENERAL_ADMIN = int(os.environ.get("GENERAL_ADMIN"))
bot = AsyncTeleBot(API_TOKEN)
admins = loads(os.environ.get("admins"))


async def msg_args(message: types.Message):
    msg_args_list = message.text.split()
    if len(msg_args_list) > 1:
        return msg_args_list


@bot.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id not in admins:
        await bot.send_message(message.from_user.id, "Вы не являетесь администратором.")
    else:
        await bot.send_message(message.from_user.id, "Вам будут приходить оповещения о заказах.")


@bot.message_handler(commands=['add_admin'])
async def add_admin(message: types.Message):
    if message.from_user.id != GENERAL_ADMIN:
        await bot.send_message(message.from_user.id, "Вы не имеете таких привелегий.")
    else:
        args = await msg_args(message)
        if args is not None:
            admin_id = int(args[1])
            if admin_id not in admins:
                admins.append(admin_id)
                set_key('.env', 'admins', dumps(admins))
                await bot.send_message(message.from_user.id, "Администратор добавлен ➕")
            else:
                await bot.send_message(message.from_user.id, "Администратор уже был добавлен ранее.")
        else:
            await bot.send_message(message.from_user.id, "Укажите User ID администратора (можно узнать в @getmyid_bot).")


@bot.message_handler(commands=['del_admin'])
async def del_admin(message: types.Message):
    if message.from_user.id != GENERAL_ADMIN:
        await bot.send_message(message.from_user.id, "Вы не имеете таких привелегий.")
    else:
        args = await msg_args(message)
        if args is not None:
            admin_id = int(args[1])
            if admin_id in admins:
                if admin_id != GENERAL_ADMIN:
                    admins.remove(admin_id)
                    set_key('.env', 'admins', dumps(admins))
                    await bot.send_message(message.from_user.id, "Администратор удален 🗑")
                else:
                    await bot.send_message(message.from_user.id, "Вы не можете удалить главного администратора ❌")
            else:
                await bot.send_message(message.from_user.id, "Администратора нет в списке.")
        else:
            await bot.send_message(message.from_user.id, "Укажите User ID администратора (можно узнать в @getmyid_bot).")            


@bot.message_handler(commands=['close_order'])
async def close_order(message: types.Message):
    if message.from_user.id not in admins:
        await bot.send_message(message.from_user.id, "Вы не являетесь администратором.")
    else:
        args = await msg_args(message)
        if args is not None:
            async with aiosqlite.connect("./instance/orders.db") as conn:
                await conn.execute("update orders set processing=0 where order_id=?", (args[1],))
                await conn.commit()
            await bot.send_message(message.from_user.id, f"Заказ #{args[1]} закрыт✅")
        else:
            await bot.send_message(message.from_user.id, "Укажите номер заказа.")


@bot.message_handler(commands=['help'])
async def help(message: types.Message):
    if message.from_user.id not in admins:
        await bot.send_message(message.from_user.id, "Вы не являетесь администратором.")
    else:
        await bot.send_message(message.from_user.id, """/strat - запуск бота
/close_order <номер заказа> - закрывает заказ
/help - справка
                               
Доступные только главному администратору:
/add_admin <user_id> - добавляет админа
/del_admin <user_id> - удаляет админа
/admins - показывает список администраторов
""")


@bot.message_handler(commands=['admins'])
async def admins_list(message: types.Message):
    if message.from_user.id != GENERAL_ADMIN:
        await bot.send_message(message.from_user.id, "Вы не имеете таких привелегий.")
    else:
        await bot.send_message(message.from_user.id, '\n'.join([f"[adm{user_id}](tg://user?id={user_id})" for user_id in admins]), parse_mode='MarkdownV2')


asyncio.run(bot.polling())
