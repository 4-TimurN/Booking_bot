import time
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext, filters
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import bot_token
from aiogram.utils import executor
import sql_part
import datetime


async def on_startup(_):
    """
    Действия при запуске
    """
    sql_part.sql_start()
    print("DB is ready")

""" Инициализация бота """

storage = MemoryStorage()
bot = Bot(token=bot_token.BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

""" Машины состояний для считывания значений input """


class FSMAdmin(StatesGroup):
    """
    Машина состояния для создания путешествия
    """
    name = State()
    date = State()
    description = State()
    price = State()
    amount = State()
    photo = State()


class FSMClient(StatesGroup):
    """
    Машина состояния для записи на путешественника самим клиентом
    """
    travel_id = State()
    tg_user_id = State()
    travel_name = State()
    travel_date = State()
    tg_user_name = State()
    client_amount = State()
    client_name = State()
    phone = State()
    payment = State()


class FSMBookClient(StatesGroup):
    """
    Машина состояния для записи на путешественника самим клиентом
    """
    travel_id = State()
    tg_user_id = State()
    travel_name = State()
    travel_date = State()
    tg_user_name = State()
    client_amount = State()
    client_name = State()
    phone = State()
    payment = State()


class FSMClientReview(StatesGroup):
    """
    Машина состояния для того, чтобы оставить отзыв
    """
    name = State()
    date = State()
    id_travel = State()
    review = State()


class FSMAdminSendToClient(StatesGroup):
    """
    Машина состояния для того, чтобы отправить сообщение группе пользователей
    """
    id_travel = State()
    message_send = State()
    id_users = State()


""" Инициализация кнопок """

button_create_travel = InlineKeyboardButton("Создать путешествие 🏕", callback_data="#1#")  # create_command
button_list_travel = InlineKeyboardButton("Список путешествий 🏕🏕🏕", callback_data="#2#")  # list_of_travel_command
button_archive_list_travel = InlineKeyboardButton("Архив путешествий 📼", callback_data="#38#")  # list_of_travel_command

button_hide_menu = InlineKeyboardButton(text="Свернуть задачи", callback_data="hide_menu")
button_hide = InlineKeyboardMarkup().add(button_hide_menu)

admin_buttons = InlineKeyboardMarkup()  # one_time_keyboard=True
admin_buttons.add(button_create_travel).add(button_list_travel).add(button_archive_list_travel)  # .add(button_travelers_summary).add(button_book)

client_button_book = InlineKeyboardButton("Записаться на путешествие 🏕", callback_data="#3#")  # list_travel_client
client_button_my_books = InlineKeyboardButton("Мои бронирования 🏕🏕🏕", callback_data="#4#")  # all_client_book_list
button_archive_list_travel_client = InlineKeyboardButton("Мои завершённые путешествия 🍃", callback_data="#47#")  # list_of_travel_command

client_buttons = InlineKeyboardMarkup()
client_buttons.add(client_button_book).add(client_button_my_books).add(button_archive_list_travel_client)

""" functions """

""" Обертки для контроля инпута """


def admin(function):
    """
    Декоратор, с помощью которого можно запретить отправлять какие-либо сообщения (в данном случае можно отправлять
    от админа)
    """

    async def wrapper(message):
        if message.from_user.id != bot_token.ADMIN_ID:
            await message.answer("Это команда админа! 😡")
        else:
            return await function(message)

    return wrapper


def control_message_create_travel_admin(function):
    """
    Декоратор, котороый контролит команду "Создать путешествие" по количеству символов
    """

    async def wrapper(message):
        if len(message.text) > 21:
            await message.answer("прости, не знаю такую команду! 🤷‍♂")
        else:
            return await function(message)

    return wrapper


def control_message_list_of_travels_admin(function):
    """
    Декоратор, который контролит команду "Список путешествий" по количеству символов
    """

    async def wrapper(message):
        if len(message.text) > 24:
            await message.answer("прости, не знаю такую команду! 🤷‍♂")
        else:
            return await function(message)

    return wrapper


def exist_or_not(function):
    """
    Декоратор, который контролит существует ли конкретное путешествие или нет
    """

    async def wrapper(callback, id_travel):
        diction = sql_part.sql_info_travel(id_travel)
        if len(diction) == 0:
            await bot.delete_message(message_id=callback.message.message_id,
                                     chat_id=callback.message.chat.id)
            await callback.answer("Путешествие уже было удалено ранее 🙄")
        else:
            return await function(callback, id_travel)

    return wrapper


async def clear_chat(message):
    """
    Очистить историю чата, удалить все сообщения чата
    """
    last_message = message.message_id
    while last_message > 1:
        try:
            await bot.delete_message(message_id=last_message, chat_id=message.chat.id)
            last_message -= 1
        except Exception:
            break


async def clear_chat_2(message, how_many_msg):
    """
    Очистить историю чата, удалить 20 последних сообщений
    """
    last_message, i = message.message_id, 0
    while i < how_many_msg:
        try:
            await bot.delete_message(message_id=last_message, chat_id=message.chat.id)
        except Exception:
            pass
        i += 1
        last_message -= 1


async def confirm_action_admin_delete_travel(callback, id_travel, travel_name, travel_date):
    """
    Запрос на подтверждение удаления путешестаия - админ
    """
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    await callback.message.answer("<b>Точно?</b>😱",reply_markup=keyboard
                         .insert(InlineKeyboardButton('Да, 100% 😤', callback_data=f'#5#&{id_travel}&{travel_name}&{travel_date}'))  # admin_delete_travel_yes_action
                         .insert(InlineKeyboardButton('Нет 😰', callback_data='#6#')), parse_mode="html"  # admin_delete_travel_no_action
                         )


async def confirm_action_admin_client_book(callback, id_travel, id):
    """
    Запрос на подтверждение удаления записи клиента  - админ
    """
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    await callback.message.answer("<b>Точно?</b> 😱", reply_markup=keyboard
                         .insert(InlineKeyboardButton('Да, 100% 😤', callback_data=f'#7#&{id_travel}&{id}'))  # admin_delete_client_book_yes_action
                         .insert(InlineKeyboardButton('Нет 😰', callback_data='#8#')), parse_mode="html"  # admin_delete_client_book_no_action
                         )


async def exist_or_not_travel():
    """
    Существует ли хоть одно созданное путешествие
    """
    diction = sql_part.sql_list_travel()
    if len(diction) == 0:
        return False
    return True


async def archive_exist_or_not_travel():
    """
    Существует ли хоть одно архивное путешествие
    """
    diction = sql_part.sql_list_travel_archive()
    if len(diction) == 0:
        return False
    return True


async def list_travel_admin(message):
    """
    Получить список путешествий (admin) / в виде строки
    """
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for string in sql_part.sql_list_travel():
        button = InlineKeyboardButton(f"🏕 {string[1]}  {string[2]}",  # string[1] - название пут. string[2] - дата
                                      callback_data=f"#9#&{string[0]}")  # string[0] - id  # admin_all_info_travel
        keyboard.add(button)
    await message.answer(f"💁‍♂ вот список путешествий:", reply_markup=keyboard
                           .add(InlineKeyboardButton('Назад', callback_data='#10#')))  # drop_travel_list


async def archive_list_travel_admin(message):
    """
    Получить список прошедших путешествий (admin) / в виде строки
    """
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for string in sql_part.sql_list_travel_archive():
        button = InlineKeyboardButton(f"🏕 {string[1]}  {string[2]}",  # string[1] - название пут. string[2] - дата
                                      callback_data=f"#39#&{string[0]}")  # string[0] - id  # admin_all_info_travel
        keyboard.add(button)
    await message.answer(f"💁‍♂ вот архив прошедших путешествий:", reply_markup=keyboard
                           .add(InlineKeyboardButton('Назад', callback_data='#10#')))  # drop_travel_list


async def all_info_travel_admin(message, callback, id_travel):
    """
    Получить полную информацию по конкретному путешествию (admin) - с кнопкой закрыть запись
    """
    for string in sql_part.sql_info_travel(id_travel):
        # date_from_mysql = string[2].strftime('%Y-%m-%d')
        # date_split = date_from_mysql.split("-")
        # date_value_2 = f'{date_split[2]}-{date_split[1]}-{date_split[0]}'  # меняю порядок отображения даты с yyyy-mm-dd на dd-mm-yyyy
        await bot.send_photo(callback.from_user.id, string[6],  # string[6] - фото
                             f'{string[1]}\n\nДата: {string[2]}\nОписание: {string[3]} '
                             f'\nСтоимость: {string[4]}\nКоличево мест: {string[5]}',
                             reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                             .add(InlineKeyboardButton("Список записавшихся ⛷🚣‍♀🏂",
                                                       callback_data=f"#11#&{string[0]}"))  # string[0] - id пут  # list_of_travelers
                             .add(
                                 InlineKeyboardButton("Записать желающего 🙋‍♀🙋",
                                                      callback_data=f"#12#&{string[0]}&{string[1]}&{string[2]}"))  # string[0] - id пут book_client_by_admin  # book_client_by_admin
                             .add(InlineKeyboardButton("Закрыть запись ❄",
                                                       callback_data=f"#13#&{id_travel}"))  # close_book
                             .add(InlineKeyboardButton("Назад",
                                                       callback_data=f"#14#"))  # back_to_travel_list_admin
                             .add(InlineKeyboardButton("Удалить путешествие ❌",
                                                       callback_data=f"#15#&{string[0]}&{string[1]}&{string[2]}"))  # delete_travel_admin
                               # string[0] - id пут, string[1] - название, string[2] - дата
                             .add(InlineKeyboardButton("Убрать в архив 📦",
                                  callback_data=f"#45#&{string[0]}")))


async def all_info_travel_admin_2(message, callback, id_travel):
    """
    Получить полную информацию по конкретному путешествию (admin) - с кнопкой открыть запись
    """
    for string in sql_part.sql_info_travel(id_travel):
        await bot.send_photo(callback.from_user.id, string[6],  # string[6] - фото
                             f'{string[1]}\n\nДата: {string[2]}\nОписание: {string[3]} '
                             f'\nСтоимость: {string[4]}\nКоличево мест: {string[5]}',
                             reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                             .add(InlineKeyboardButton("Список записавшихся ⛷🚣‍♀🏂",
                                                       callback_data=f"#11#&{string[0]}"))  # string[0] - id пут
                             .add(
                                 InlineKeyboardButton("Записать желающего 🙋‍♀🙋",
                                                      callback_data=f"#12#&{string[0]}&{string[1]}&{string[2]}"))  # string[0] - id пут book_client_by_admin
                             .add(InlineKeyboardButton("Открыть запись 🥳",
                                                       callback_data=f"#16#&{id_travel}"))  # open_book
                             .add(InlineKeyboardButton("Назад",
                                                       callback_data=f"#14#"))  # back_to_travel_list_admin
                             .add(InlineKeyboardButton("Удалить путешествие ❌",
                                                       callback_data=f"#15#&{string[0]}&{string[1]}&{string[2]}"))  # delete_travel_admin
                             .add(InlineKeyboardButton("Убрать в архив 📦",
                                                       callback_data=f"#45#&{string[0]}")))


async def archive_all_info_travel_admin(message, callback, id_travel):
    """
    Получить полную информацию по конкретному архивному путешествию (admin)
    """
    for string in sql_part.sql_info_travel(id_travel):
        # date_from_mysql = string[2].strftime('%Y-%m-%d')
        # date_split = date_from_mysql.split("-")
        # date_value_2 = f'{date_split[2]}-{date_split[1]}-{date_split[0]}'  # меняю порядок отображения даты с yyyy-mm-dd на dd-mm-yyyy
        await bot.send_photo(callback.from_user.id, string[6],  # string[6] - фото
                             f'{string[1]}\n\nДата: {string[2]}\nОписание: {string[3]} '
                             f'\nСтоимость: {string[4]}\nКоличево мест: {string[5]}',
                             reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                             .add(InlineKeyboardButton("Список записавшихся ⛷🚣‍♀🏂",
                                                       callback_data=f"#42#&{string[0]}"))  # string[0] - id пут  # list_of_travelers
                             # .add(
                             #     InlineKeyboardButton("Записать желающего 🙋‍♀🙋",
                             #                          callback_data=f"#12#&{string[0]}&{string[1]}&{string[2]}"))  # string[0] - id пут book_client_by_admin  # book_client_by_admin
                             # .add(InlineKeyboardButton("Закрыть запись ❄",
                             #                           callback_data=f"#13#&{id_travel}"))  # close_book
                             .add(InlineKeyboardButton("Назад",
                                                       callback_data=f"#40#"))  # back_to_travel_list_admin
                             .add(InlineKeyboardButton("Удалить путешествие ❌",
                                                       callback_data=f"#15#&{string[0]}&{string[1]}&{string[2]}"))  # delete_travel_admin
                               # string[0] - id пут, string[1] - название, string[2] - дата
                             .add(InlineKeyboardButton("Убрать из архива 📦",
                                                       callback_data=f"#46#&{string[0]}")))


async def exist_or_not_client_list_travel(id_travel):
    """
    Есть записавшиеся на путешествие или нет
    """
    diction = sql_part.sql_get_list_of_travelers_for_one_travel(id_travel)  # call[1] - id_travel
    if len(diction) == 0:
        return False
    return True


async def get_client_list_travel(message, callback, id_travel):
    """
    Получить список записавшихся клиентов
    """
    diction = sql_part.sql_get_list_of_travelers_for_one_travel(id_travel)  # call[1] - id_travel
    max_book = sql_part.sql_get_default_amount_book_info(id_travel)
    current_book = sql_part.sql_get_current_amount_book_info(id_travel)
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for string in diction:
        button = InlineKeyboardButton(f"🤠 {string[0]} | 💸 оплата: {string[3]}",  # string[0] - имя, string[3] - оплата
                                      callback_data=f"#37#&{string[4]}&{string[6]}&{string[5]}")  # string[4] - id, string[6] - travel_id   # info_client
        keyboard.add(button)
    await bot.send_message(callback.from_user.id, f"📍 Всего записалось: {current_book} из {max_book}\n\n💁‍♂ вот кто записался:",
                           reply_markup=keyboard
                           .add(InlineKeyboardButton("Отправить всем сообщение ✉",
                                                                          callback_data=f"#17#&{id_travel}"))  # send_message_to
                           .add(InlineKeyboardButton("Назад",
                                                     callback_data=f"#18#&{id_travel}"))  # back_to_all_info_travel
                           )


async def archive_get_client_list_travel(message, callback, id_travel):
    """
    Получить список записавшихся клиентов (архивное путешествие)
    """
    diction = sql_part.sql_get_list_of_travelers_for_one_travel(id_travel)  # call[1] - id_travel
    max_book = sql_part.sql_get_default_amount_book_info(id_travel)
    current_book = sql_part.sql_get_current_amount_book_info(id_travel)
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for string in diction:
        button = InlineKeyboardButton(f"🤠 {string[0]} | 💸 оплата: {string[3]}",  # string[0] - имя, string[3] - оплата
                                      callback_data=f"#43#&{string[4]}&{string[6]}&{string[5]}")  # string[4] - id, string[6] - travel_id   # info_client
        keyboard.add(button)
    await bot.send_message(callback.from_user.id, f"📍 Всего записалось: {current_book} из {max_book}\n\n💁‍♂ вот кто записался:",
                           reply_markup=keyboard
                           # .add(InlineKeyboardButton("Отправить всем сообщение ✉",
                           #                                                callback_data=f"#17#&{id_travel}"))  # send_message_to
                           .add(InlineKeyboardButton("Назад",
                                                     callback_data=f"#41#&{id_travel}"))  # back_to_all_info_travel
                           )


async def get_traveler_info(message, id, travel_id, tg_user_id):
    """
    Получить информацию о конкретном клиенте
    """
    await bot.delete_message(message_id=message.message_id, chat_id=message.chat.id)
    diction = sql_part.sql_get_traveler_info(id, travel_id)  # call[1] - id, call[2] - travel_id
    tg_user_id = tg_user_id  # tg id user
    for element in [f"✳ Имя: {dict[0]}\n@{dict[6]}\n\n- тел.: {dict[1]}\n- забранировано мест: {dict[2]}\n" \
                    f"- подтверждение отплаты от клиента: {dict[3]}\n" for dict in diction]:
        await bot.send_message(bot_token.ADMIN_ID, element,
                               reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True).add(
                                   InlineKeyboardButton(f"оплата ✅",
                                                        callback_data=f"#19#&{travel_id}&{tg_user_id}&{id}")).insert(  # payment_ok
                                   InlineKeyboardButton("оплата ❌",
                                                        callback_data=f"#20#&{travel_id}&{tg_user_id}&{id}"))  # payment_cancel
                               .add(InlineKeyboardButton("🙅‍♂ отменить запись",
                                                         callback_data=f"#21#&{travel_id}&{id}"))  # cancel_by_admin
                               .add(InlineKeyboardButton(f"Назад",
                                                         callback_data=f"#22#&{travel_id}"))  # back_to_all_travelers_list
                               )


async def archive_get_traveler_info(message, id, travel_id, tg_user_id):
    """
    Получить информацию о конкретном клиенте (архивное путешествие)
    """
    await bot.delete_message(message_id=message.message_id, chat_id=message.chat.id)
    diction = sql_part.sql_get_traveler_info(id, travel_id)  # call[1] - id, call[2] - travel_id
    tg_user_id = tg_user_id  # tg id user
    for element in [f"✳ Имя: {dict[0]}\n@{dict[6]}\n\n- тел.: {dict[1]}\n- забранировано мест: {dict[2]}\n" \
                    f"- подтверждение отплаты от клиента: {dict[3]}\n" for dict in diction]:
        await bot.send_message(bot_token.ADMIN_ID, element,
                               reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
                               # .add(InlineKeyboardButton(f"оплата ✅",
                               #                          callback_data=f"#19#&{travel_id}&{tg_user_id}&{id}")).insert(  # payment_ok
                               #     InlineKeyboardButton("оплата ❌",
                               #                          callback_data=f"#20#&{travel_id}&{tg_user_id}&{id}"))  # payment_cancel
                               # .add(InlineKeyboardButton("🙅‍♂ отменить запись",
                               #                           callback_data=f"#21#&{travel_id}&{id}"))  # cancel_by_admin
                               .add(InlineKeyboardButton(f"Назад",
                                                         callback_data=f"#44#&{travel_id}"))  # back_to_all_travelers_list
                               )


async def delete_travel_admin(callback, id_travel, travel_name, travel_date):
    """
    Удаление путешествия - админ
    """
    await sql_part.sql_delete_travel(id_travel)
    await callback.answer(f"Путешествие {travel_name} от {travel_date} удалено 👌")
    await clear_chat_2(callback.message, 10)
    if await exist_or_not_travel() is False:
        # await bot.delete_message(message_id=callback.message.message_id,
        #                          chat_id=callback.message.chat.id)
        await callback.message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=admin_buttons)
    else:
        await list_travel_admin(callback.message) #


async def put_to_archive(callback, id_travel):
    """
    Переместить путешествие в архив - админ
    """
    await sql_part.sql_put_to_archive_travel(id_travel)
    await callback.answer(f"Переместил путешествие в архив 👌")
    await clear_chat_2(callback.message, 10)
    if await exist_or_not_travel() is False:
        # await bot.delete_message(message_id=callback.message.message_id,
        #                          chat_id=callback.message.chat.id)
        await callback.message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=admin_buttons)
    else:
        await list_travel_admin(callback.message)


async def restore_from_archive(callback, id_travel):
    """
    Восстановить путешествие из архива - админ
    """
    await sql_part.sql_restore_from_archive(id_travel)
    await callback.answer(f"Вернул в 'Список путешествий' 👌")
    await clear_chat_2(callback.message, 10)
    if await archive_exist_or_not_travel() is False:
        # await bot.delete_message(message_id=callback.message.message_id,
        #                          chat_id=callback.message.chat.id)
        await callback.message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=admin_buttons)
    else:
        await archive_list_travel_admin(callback.message)


async def cancel_book_by_admin(callback, travel_id, id):  #####
    """
    Отмена записи клиента админом
    """
    await sql_part.sql_cancel_travel_client_by_admin(travel_id, id)
    await callback.answer("❗ Бронирование отменено")
    await clear_chat_2(callback.message, 10)
    if await exist_or_not_client_list_travel(travel_id):
        await get_client_list_travel(callback.message, callback, travel_id)
    else:
        status = sql_part.sql_get_book_status(travel_id)
        if status == "open":
            await all_info_travel_admin(callback.message, callback, travel_id)
        else:
            await all_info_travel_admin_2(callback.message, callback, travel_id)


""" Описание handlers """

""" Стандартные команды """


@dp.message_handler(commands="cancel", state="*")
async def cancel_command(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        last_msg = await message.answer("Нет активных команд. Я ничего и не делал ))")
        time.sleep(1.5)
        await clear_chat_2(last_msg, 25)
        if message.from_user.id == bot_token.ADMIN_ID or message.from_user.id == bot_token.MARAT:
            await message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=admin_buttons)
        else:
            await message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=client_buttons)
    else:
        await state.finish()
        last_msg = await message.answer("Команда отменена 👌")
        time.sleep(1.5)
        await clear_chat_2(last_msg, 25)
        if message.from_user.id == bot_token.ADMIN_ID or message.from_user.id == bot_token.MARAT:
            await message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=admin_buttons)
        else:
            await message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=client_buttons)


@dp.message_handler(commands="start")
async def start_command(message: types.Message):
    await clear_chat_2(message, 10)
    if message.from_user.id == bot_token.ADMIN_ID:
        await message.answer(
            'Привет! 👋\n\nЯ твой бот - помощник 🤖'
            '\n\nНачнем?\n\nНажми /help, чтобы узнать как взаимодействовать '
            'со мной 🔧\n\nИли нажимай /menu, чтобы сразу приступить к делу 🤓', parse_mode="Markdown")

    else:
        await message.answer('Привет! 👋\n\nЯ бот - помощник 🤖 из команды friendstrip!\n\nБольше информации о нас:\n\nInstagram - [friendstrip](https://www.instagram.com/friends_trip/)\nГруппа в telegram - @friendstrip'
                             '\n\nНачнем?\n\nНажми /help, чтобы узнать как взаимодействовать '
                             'со мной 🔧\n\nИли нажимай /menu, чтобы сразу приступить к делу 🤓', parse_mode="Markdown")


@dp.message_handler(commands="help")
async def help_command(message: types.Message):
    await clear_chat_2(message, 25)
    if message.from_user.id != bot_token.ADMIN_ID:
        await message.answer('Спешу на помощь! 🚑 \n\nЧтобы увидеть список команд которые можно мне отправить, '
                             'просто набери "/" в строке ввода.  '
                             '\n\nСамые главные команды это: /menu и /cancel. \n\nС помощью /menu тебе '
                             'откроется '
                             'список различных команд связаных с путешествиями. \n\nКоманда /cancel отменит '
                             'взаимодействие с текущей командой и вернет тебя в изначальное положение. \n\nВперед к '
                             'приключениям! 🏃‍♀🏃‍♂\n\nP.S.\nВступай в нашу группу в telegram- @friendstrip'
                             '\nи не забудь подписаться на нас в instagram - '
                             '[friendstrip](https://www.instagram.com/friends_trip/)', parse_mode="Markdown")
    else:
        await message.answer('Спешу на помощь! 🚑 \n\nНабрав "/" в строке ввода,  '
                             'увидишь список команд которые можешь мне '
                             'отправить. \n\nСамые главные это: /menu и /cancel. \n\nС помощью /menu тебе '
                             'откроется '
                             'список различных команд связаных с путешествиями. \n\nКоманда /cancel отменит '
                             'взаимодействие с текущей командой и вернет тебя в изначальное положение.\n\n Надеюсь '
                             'все понятно 😉')


@dp.message_handler(commands="menu")
async def menu_command(message: types.Message):
    await clear_chat_2(message, 25)
    if message.from_user.id == bot_token.ADMIN_ID or message.from_user.id == bot_token.MARAT:
        await message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=admin_buttons)
    else:
        await message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=client_buttons)



# @dp.message_handler(commands="hide_menu")
# async def hide_menu_command(message: types.Message):
#     await message.answer('Ок, свернул 🤓', reply_markup=ReplyKeyboardRemove())


"""""""""""""""""""admin-handlers"""""""""""""""""""""

""" Список путешествий  -  админ """


@dp.callback_query_handler(filters.Text(contains="#2#"))
async def list_of_travel_command_call(callback: types.CallbackQuery):
    if await exist_or_not_travel() is False:
        await callback.answer("Не нашел путешествий 😔, надо их создать! 😉")
    else:
        await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await list_travel_admin(callback.message)
        await callback.answer()


""" Список прошедших путешествий  -  админ """


@dp.callback_query_handler(filters.Text(contains="#38#"))
async def archive_list_of_travel_command_call(callback: types.CallbackQuery):
    if await archive_exist_or_not_travel() is False:
        await callback.answer("Не нашел архивных путешествий! 🤓")
    else:
        await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await archive_list_travel_admin(callback.message)
        await callback.answer()


""" Свернуть список путешествий  -  админ """


@dp.callback_query_handler(filters.Text(contains="#10#"))
async def drop_travel_list_call(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await callback.message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=admin_buttons)
    await callback.answer()


""" Получить полную информацию по путешествию  -  админ"""


@dp.callback_query_handler(filters.Text(contains="#9#"))
async def get_admin_list_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    status = sql_part.sql_get_book_status(call[1])
    if status == "open":
        await all_info_travel_admin(callback.message, callback, call[1])
    else:
        await all_info_travel_admin_2(callback.message, callback, call[1])
    await callback.answer()


""" Получить полную информацию по архивному путешествию  -  админ"""


@dp.callback_query_handler(filters.Text(contains="#39#"))
async def get_admin_list_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await archive_all_info_travel_admin(callback.message, callback, call[1])
    await callback.answer()


""" Список записавшихся  -  админ """


@dp.callback_query_handler(filters.Text(contains="#11#"))
async def get_client_list_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    if await exist_or_not_client_list_travel(call[1]) is False:
        await callback.answer("Упс! Пока записавшихся нет 🥺")
    else:
        await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await get_client_list_travel(callback.message, callback, call[1])


""" Список записавшихся  -  админ (архтвное путешествие) """


@dp.callback_query_handler(filters.Text(contains="#42#"))
async def archive_get_client_list_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    if await exist_or_not_client_list_travel(call[1]) is False:
        await callback.answer("Упс! Записавшихся нет 🥺")
    else:
        await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await archive_get_client_list_travel(callback.message, callback, call[1])


""" Подробная информация о записавшимся клиенте  -  админ """


@dp.callback_query_handler(filters.Text(contains="#37#"))
async def get_admin_list_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await get_traveler_info(callback.message, call[1], call[2], call[3])
    await callback.answer()


""" Подробная информация о записавшимся клиенте  -  админ (архивное путешествие) """


@dp.callback_query_handler(filters.Text(contains="#43#"))
async def get_admin_list_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await archive_get_traveler_info(callback.message, call[1], call[2], call[3])
    await callback.answer()


""" Оплата  -  админ """


@dp.callback_query_handler(filters.Text(contains="#19#"))
async def mark_payment_true_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await sql_part.sql_payment_client_notification_true(call[1], call[3])
    await callback.answer("Поставил ✅")
    await get_traveler_info(callback.message, call[3], call[1], call[2])


@dp.callback_query_handler(filters.Text(contains="#20#"))
async def mark_payment_false_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await sql_part.sql_payment_client_notification_false(call[1], call[3])
    await callback.answer("Поставил ❌")
    await get_traveler_info(callback.message, call[3], call[1], call[2])


""" Отмена записи клиента  -  админ """


@dp.callback_query_handler(filters.Text(contains="#21#"))
async def cancel_travel_admin_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await confirm_action_admin_client_book(callback, call[1], call[2])
    await callback.answer()


""" Отправить всем сообщение  -  админ """


@dp.callback_query_handler(filters.Text(contains="#17#"), state=None)
async def get_client_list_travel_call(callback: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    call = callback.data.split("&")
    await FSMAdminSendToClient.id_travel.set()
    id_travel = call[1]
    async with state.proxy() as data:
        data["id_travel"] = id_travel
    await FSMAdminSendToClient.next()
    await callback.message.answer(text="Что отправить?\n\n👉 Или нажми /cancel для выхода из "
                                       "режима отправки сообщения записавшимся.")
    await callback.answer()


@dp.message_handler(state=FSMAdminSendToClient.message_send)
async def load_client_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["text_to_client"] = message.text
    diction = sql_part.sql_get_list_of_travelers_for_one_travel(data["id_travel"])
    id_user_list = [dic[5] for dic in diction]
    await FSMAdminSendToClient.id_users.set()
    async with state.proxy() as data:
        data["id_users"] = id_user_list  # call - список с id клиентов
    for id_user in data["id_users"]:
        if id_user == str(bot_token.ADMIN_ID):
            continue
        else:
            await bot.send_message(id_user, f"Сообщение от @friendstrip 🤗\n________________________________________"
                                            f"___\n\n{data['text_to_client']}")
    last_msg = await bot.send_message(bot_token.ADMIN_ID, "Сообщение отправлено 👌")
    await state.finish()
    time.sleep(1.5)
    await clear_chat_2(last_msg, 20)
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for string in diction:
        button = InlineKeyboardButton(f"🤠 {string[0]} | 💸 оплата: {string[3]}",
                                      # string[0] - имя, string[3] - оплата
                                      callback_data=f"#37#&{string[4]}&{string[6]}&{string[5]}")  # string[4] - id, string[6] - travel_id  # info_client
        keyboard.add(button)
    await bot.send_message(message.from_user.id, f"💁‍♂ вот кто записался:",
                           reply_markup=keyboard
                           .add(InlineKeyboardButton("Отправить всем сообщение",
                                                     callback_data=f"#17#&{data['id_travel']}"))  # send_message_to
                           .add(InlineKeyboardButton("Назад",
                                                     callback_data=f"#18#&{data['id_travel']}"))  # back_to_all_info_travel
                           )


""" Удаление путешествия  -  админ """


@dp.callback_query_handler(filters.Text(contains="#15#"))
async def delete_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await confirm_action_admin_delete_travel(callback, call[1], call[2], call[3])
    await callback.answer()
    # await delete_travel_admin(callback, call[1], call[2], call[3])


""" Создание путешествия  -  админ """


@dp.callback_query_handler(filters.Text(contains="#1#"), state=None)
async def create_travel(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id,
                             chat_id=callback.message.chat.id)
    await FSMAdmin.name.set()
    await callback.message.answer("Введи название путешествия\n\n👉 Или нажми /cancel для выхода из "
                                       "режима создания путешествия.")
    await callback.answer()


@dp.message_handler(state=FSMAdmin.name)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["name"] = message.text
    await FSMAdmin.next()
    await message.answer("Введи дату путешествия в формате: дд-мм-гг\n\n👉 Или нажми /cancel для выхода из "
                                       "режима создания путешествия.")


@dp.message_handler(state=FSMAdmin.date)
async def load_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            date_1 = datetime.datetime.strptime(message.text, '%d-%m-%y')
            data["date"] = date_1
            # tt = datetime.datetime.now()  # текущая дата
            # print(tt.date())  # дата без времени
            await FSMAdmin.next()
            await message.answer("Введи описание путешествия\n\n👉 Или нажми /cancel для выхода из "
                               "режима создания путешествия.")
        except ValueError:
            await bot.send_message(message.from_user.id,
                                   "🤔 Возможно такой даты не существует, либо дата указана в некорректном формате, попробуй еще раз 🤓\n\n👉 Или нажми /cancel для выхода из "
                                   "режима создания путешествия.")


@dp.message_handler(state=FSMAdmin.description)
async def load_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["description"] = message.text
    await FSMAdmin.next()
    await message.answer("Введи стоимость путешествия\n\n👉 Или нажми /cancel для выхода из "
                                       "режима создания путешествия.")


@dp.message_handler(state=FSMAdmin.price)
async def load_price(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await bot.send_message(message.from_user.id, "Некорректное значение, попробуй еще раз 🤓\n\n👉 Или нажми /cancel для выхода из "
                                       "режима создания путешествия.")
    else:
        async with state.proxy() as data:
            data["price"] = message.text + " руб."
        await FSMAdmin.next()
        await message.answer("Введи количество мест для желающих\n\n👉 Или нажми /cancel для выхода из "
                                       "режима создания путешествия.")


@dp.message_handler(state=FSMAdmin.amount)
async def load_amount(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False:
        await bot.send_message(message.from_user.id, "Некорректное значение, попробуй еще раз 🤓\n\n👉 Или нажми /cancel для выхода из "
                                       "режима создания путешествия.")
    else:
        async with state.proxy() as data:
            data["amount"] = message.text
        await FSMAdmin.next()
        await message.answer("Теперь загрузи фото\n\n👉 Или нажми /cancel для выхода из "
                                       "режима создания путешествия.")


@dp.message_handler(content_types="photo", state=FSMAdmin.photo)
async def load_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["photo"] = message.photo[0].file_id
    await FSMAdmin.next()
    if await sql_part.sql_add_travel(state) == "Error db":
        await state.finish()
        last_msg = await message.answer("Не получилось добавить путушествие, попробуй позже 😔")
        time.sleep(1.5)
        await clear_chat_2(last_msg, 25)
    else:
        await state.finish()
        last_msg = await message.answer("Путешествие создано ❤")
        time.sleep(1.5)
        await clear_chat_2(last_msg, 25)
        await bot.send_message(message.chat.id, '🟢 Что будем делать? Выбери ниже ⬇', reply_markup=admin_buttons)


""" Назад  -  из полного описания путешествия (где фото) обратно к списку путешествий  -  админ """


@dp.callback_query_handler(filters.Text(contains="#14#"))
async def back_to_travel_list_admin_call(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await list_travel_admin(callback.message)


""" Назад  -  из полного описания архивного путешествия (где фото) обратно к списку архивных путешествий  -  админ """


@dp.callback_query_handler(filters.Text(contains="#40#"))
async def archive_back_to_travel_list_admin_call(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await archive_list_travel_admin(callback.message)


""" Назад  -  из списка записавшихся в полное описание путешествия  -  админ"""


@dp.callback_query_handler(filters.Text(contains="#18#"))
async def back_to_all_info_travel_call(callback: types.CallbackQuery):
    call = callback.data.split('&')
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    status = sql_part.sql_get_book_status(call[1])
    if status == "open":
        await all_info_travel_admin(callback.message, callback, call[1])
    else:
        await all_info_travel_admin_2(callback.message, callback, call[1])
    await callback.answer()


""" Назад  -  из списка записавшихся в полное описание архивного путешествия  -  админ"""


@dp.callback_query_handler(filters.Text(contains="#41#"))
async def archive_back_to_all_info_travel_call(callback: types.CallbackQuery):
    call = callback.data.split('&')
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await archive_all_info_travel_admin(callback.message, callback, call[1])
    await callback.answer()


""" Назад  -  от конкретного описания клиента к списку записавшихся  -  админ """


@dp.callback_query_handler(filters.Text(contains="#22#"))
async def back_to_all_travelers_list_call(callback: types.CallbackQuery):
    call = callback.data.split('&')
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await get_client_list_travel(callback.message, callback, call[1])


""" Назад  -  от конкретного описания клиента к списку записавшихся  -  админ  (архивное путешествие)"""


@dp.callback_query_handler(filters.Text(contains="#44#"))
async def archive_back_to_all_travelers_list_call(callback: types.CallbackQuery):
    call = callback.data.split('&')
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await archive_get_client_list_travel(callback.message, callback, call[1])


""" Записать клиента - админ """


@dp.callback_query_handler(filters.Text(contains="#12#"), state=None)
async def book_client_by_admin_command(callback: types.CallbackQuery, state: FSMContext):
    call = callback.data.split("&")
    default_amount_book_info = sql_part.sql_get_default_amount_book_info(call[1])
    current_amount_book_info = sql_part.sql_get_current_amount_book_info(call[1])
    if current_amount_book_info == default_amount_book_info:
        await callback.answer("Полная запись! Мест нет 🤓")
    else:
        await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await FSMBookClient.travel_id.set()
        id_travel = call[1]
        async with state.proxy() as data:
            data["id_travel"] = id_travel
        await FSMBookClient.tg_user_id.set()
        tg_user_id = callback.from_user.id
        async with state.proxy() as data:
            data["tg_user_id"] = tg_user_id
        await FSMBookClient.travel_name.set()
        travel_name = call[2]
        async with state.proxy() as data:
            data["travel_name"] = travel_name
        await FSMBookClient.travel_date.set()
        travel_date = call[3]
        async with state.proxy() as data:
            data["travel_date"] = travel_date
        await FSMBookClient.tg_user_name.set()
        tg_user_name = callback.from_user.username
        async with state.proxy() as data:
            data["tg_user_name"] = tg_user_name
        await FSMBookClient.next()
        await callback.message.answer(text="Сколько человек записать? 🤔\n\n👉 Или нажми /cancel для выхода из "
                                       "режима записи на путешествие.")  # Введи свое имя, пожалуйста 😊
        await callback.answer()


@dp.message_handler(state=FSMBookClient.client_amount)
async def load_client_amount(messsage: types.Message, state: FSMContext):
    if messsage.text.isdigit() is False:
        await bot.send_message(messsage.from_user.id, "Некорректное значение, попробуй еще раз 🤓\n\n👉 Или нажми /cancel для выхода из "
                                       "режима записи на путешествие.")
    else:
        async with state.proxy() as data:
            default_amount_book_info = sql_part.sql_get_default_amount_book_info(data['id_travel'])
            current_amount_book_info = sql_part.sql_get_current_amount_book_info(data['id_travel'])
            # if current_amount_book_info == default_amount_book_info:
            #     await bot.send_message(messsage.from_user.id,
            #                            f"😔 К сожалению, на данный момент, полная запись, попробуй позже, "
            #                            f"может у кого-нибудь изменяться планы. \n\nНажми "
            #                            f"/cancel для выхода из режима записи.")
            if default_amount_book_info < current_amount_book_info + int(messsage.text):
                free_places = default_amount_book_info - current_amount_book_info
                await bot.send_message(messsage.from_user.id,
                                       f"😱 Ой, слишком много, cвободных мест всего - {free_places}, "
                                       f"введи поменьше. \n\nИли нажми /cancel для выхода из "
                                       "режима записи на путешествие.")
            else:
                data["client_amount"] = messsage.text
                await FSMBookClient.next()
                await messsage.answer("Введи ФИО путешественника, пожалуйста, в формате: Иванов Иван Иванович 😊\n\n👉 Или нажми /cancel для выхода из "
                                       "режима записи на путешествие.")


@dp.message_handler(state=FSMBookClient.client_name)
async def load_client_name(messsage: types.Message, state: FSMContext):
    if len(messsage.text.split()) != 3:
        await bot.send_message(messsage.from_user.id, "Введи ФИО полностью, пожалуйста 🙏\n\n👉 Или нажми /cancel для выхода из "
                                       "режима записи на путешествие.")
    else:
        async with state.proxy() as data:
            data["client_name"] = messsage.text
        await FSMBookClient.next()
        await messsage.answer("Теперь номер телефона ☎\n👉 без 8 и +7 в начале, в формате: 9998887776\n\n👉 Или нажми /cancel для выхода из "
                                       "режима записи на путешествие.")


@dp.message_handler(state=FSMBookClient.phone)
async def load_phone(message: types.Message, state: FSMContext):
    if message.text.isdigit() is False or len(message.text) != 10:
        await bot.send_message(message.from_user.id,
                               "Некорректный номер, попробуйте еще раз 🤓,\n👉 без 8 и +7 в начале, в формате: 9998887776\n\n👉 Или нажми /cancel для выхода из "
                                       "режима записи на путешествие.")
        await FSMBookClient.phone.set()
    else:
        async with state.proxy() as data:
            data["phone"] = "+7" + message.text
        # del data['travel_name']
        # del data['travel_date']
        await sql_part.sql_book(state)
        await state.finish()
        last_msg = await message.answer('Записал! 😎')
        time.sleep(1.5)
        await clear_chat_2(last_msg, 20)
        status = sql_part.sql_get_book_status(data["id_travel"])
        if status == "open":
            for string in sql_part.sql_info_travel(data["id_travel"]):
                await bot.send_photo(message.from_user.id, string[6],  # string[6] - фото
                                     f'{string[1]}\n\nДата: {string[2]}\nОписание: {string[3]} '
                                     f'\nСтоимость: {string[4]}\nКоличево мест: {string[5]}',
                                     reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                                     .add(InlineKeyboardButton("Список записавшихся ⛷🚣‍♀🏂",
                                                               callback_data=f"#11#&{string[0]}"))  # string[0] - id пут
                                     .add(
                                         InlineKeyboardButton("Записать желающего 🙋‍♀🙋",
                                                              callback_data=f"#12#&{string[0]}&{string[1]}&{string[2]}"))  # string[0] - id пут book_client_by_admin
                                     .add(InlineKeyboardButton("Закрыть запись ❄",
                                                               callback_data=f"#13#&{string[0]}"))  # close_book
                                     .add(InlineKeyboardButton("Назад",
                                                               callback_data=f"#14#"))  # back_to_travel_list_admin
                                     .add(InlineKeyboardButton("Удалить путешествие ❌",
                                                               callback_data=f"#15#&{string[0]}&{string[1]}&{string[2]}")))  # delete_travel_admin
        else:
            for string in sql_part.sql_info_travel(data["id_travel"]):
                await bot.send_photo(message.from_user.id, string[6],  # string[6] - фото
                                     f'{string[1]}\n\nДата: {string[2]}\nОписание: {string[3]} '
                                     f'\nСтоимость: {string[4]}\nКоличево мест: {string[5]}',
                                     reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                                     .add(InlineKeyboardButton("Список записавшихся ⛷🚣‍♀🏂",
                                                               callback_data=f"#11#&{string[0]}"))  # string[0] - id пут
                                     .add(
                                         InlineKeyboardButton("Записать желающего 🙋‍♀🙋",
                                                              callback_data=f"#12#&{string[0]}&{string[1]}&{string[2]}"))  # string[0] - id пут book_client_by_admin
                                     .add(InlineKeyboardButton("Открыть запись 🥳",
                                                               callback_data=f"#16#&{string[0]}"))  # open_book
                                     .add(InlineKeyboardButton("Назад",
                                                               callback_data=f"#14#"))  # back_to_travel_list_admin
                                     .add(InlineKeyboardButton("Удалить путешествие ❌",
                                                               callback_data=f"#15#&{string[0]}&{string[1]}&{string[2]}")))  # delete_travel_admin
        await bot.send_message(bot_token.MSG_STOREGE, f"✅ @{message.from_user.username}\n{data['client_name']}"
                                           f"\n___________________________________________\n\n"
                                           f"🥳 Записался(лась) на путешествие:\n{data['travel_name']} от "
                                                      f"{data['travel_date']}")


""" Подтверждение удаление путешествия - админ """


@dp.callback_query_handler(filters.Text(contains="#5#"))
async def admin_delete_travel_yes_action(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await delete_travel_admin(callback, call[1], call[2], call[3])


""" Перемещение путешествия в архив - админ """


@dp.callback_query_handler(filters.Text(contains="#45#"))
async def put_to_archive_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await put_to_archive(callback, call[1])


""" Вернуть путешествие из архива в Список путешествий - админ """


@dp.callback_query_handler(filters.Text(contains="#46#"))
async def put_to_archive_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await restore_from_archive(callback, call[1])


""" Отмена операции удаления путешествия - админ """


@dp.callback_query_handler(filters.Text(contains="#6#"))
async def admin_delete_travel_no_action(callback: types.CallbackQuery):
    await clear_chat_2(callback.message, 1)
    await callback.answer()


""" Подтверждение удаление записи клиента - админ """


@dp.callback_query_handler(filters.Text(contains="#7#"))
async def yes_command(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await cancel_book_by_admin(callback, call[1], call[2])


""" Отмена операции удаления записи клиента - админ """


@dp.callback_query_handler(filters.Text(contains="#8#"))
async def yes_command(callback: types.CallbackQuery):
    await clear_chat_2(callback.message, 1)
    await callback.answer()


""" Закрыть запись  -  админ """


@dp.callback_query_handler(filters.Text(contains="#13#"))
async def close_book_call(callback: types.CallbackQuery):
    call = callback.data.split('&')
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    sql_part.sql_close_book(call[1])
    await all_info_travel_admin_2(callback.message, callback, call[1])


""" Открыть запись  -  админ """


@dp.callback_query_handler(filters.Text(contains="#16#"))
async def open_book_call(callback: types.CallbackQuery):
    call = callback.data.split('&')
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    sql_part.sql_open_book(call[1])
    await all_info_travel_admin(callback.message, callback, call[1])

""""""""""""""""""" client """""""""""""""""""""""""""""


"""""""""""" functions """""""""""


async def list_travel_client(message):
    """
    Получить список путешествий (client)
    """
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for string in sql_part.sql_list_travel():
        button = InlineKeyboardButton(f"🏕 {string[1]}  {string[2]}",
                                      callback_data=f"#23#&{string[0]}")  # client_all_info_travel
        keyboard.add(button)
    await message.answer(f"Что по душе? 💁‍♂", reply_markup=keyboard
                         .add(InlineKeyboardButton('Назад', callback_data='#24#')))  # drop_client_travel_list


async def all_client_book_list(message, callback):
    """
    Получить список бронирований (client)
    """
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for string in sql_part.sql_show_me_my_book_client(callback.from_user.id):
        button = InlineKeyboardButton(f"🏕 {string[2]}  {string[3]}",
                                      callback_data=f"#25#&{string[1]}")  # client_all_book
        keyboard.add(button)
    await message.answer(f"💁‍♂ вот твои бронирования:", reply_markup=keyboard
                         .add(InlineKeyboardButton('Назад', callback_data='#26#')))  # back_to_head_menu_client


async def all_client_archive_book_list(message, callback):
    """
    Получить список завершенных бронирований (client)
    """
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    for string in sql_part.sql_show_me_my_archive_book_client(callback.from_user.id):
        button = InlineKeyboardButton(f"🏕 {string[2]}  {string[3]}",
                                      callback_data=f"#48#&{string[1]}")  # client_all_book
        keyboard.add(button)
    await message.answer(f"💁‍♂ вот твои заершённые путешествия:", reply_markup=keyboard
                         .add(InlineKeyboardButton('Назад', callback_data='#26#')))  # back_to_head_menu_client


async def all_info_travel_client(message, callback, id_travel):
    """
    Получить полную информацию по конкретному путешествию (client)
    """
    await bot.delete_message(message_id=message.message_id, chat_id=message.chat.id)
    for string in sql_part.sql_info_travel(id_travel):
        await bot.send_photo(callback.from_user.id, string[6],
                             f'{string[1]}\n\nДата: {string[2]}\nОписание: {string[3]} '
                             f'\nСтоимость: {string[4]}\nКоличево мест: {string[5]}',
                             reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                             .add(InlineKeyboardButton("Записаться ⛷🚣‍♀🏂",
                                                       callback_data=f"#27#&{string[0]}&{string[1]}&{string[2]}"))  # book_me
                             .add(InlineKeyboardButton("Назад",
                                                       callback_data=f"#28#"))  # back_to_client_travel_list
                             )


async def all_info_client_book(message, callback, id_travel):
    """
    Получить информацию по конкретному бронированию (client)
    """
    for string in sql_part.sql_info_travel(id_travel):
        await bot.send_photo(callback.from_user.id, string[6],
                             f'{string[1]}\n\nДата: {string[2]}\nОписание: {string[3]} '
                             f'\nСтоимость: {string[4]}\nКоличево мест: {string[5]}',
                             reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                             .add(InlineKeyboardButton("Уведомить об оплате 💸",
                                                       callback_data=f"#29#&{string[0]}&{string[1]}&{string[2]}"))  # payment
                             .add(InlineKeyboardButton("Оставить отзыв ✏",
                                                       callback_data=f"#30#&{string[1]}&{string[2]}&{string[0]}"))  # review
                             .add(InlineKeyboardButton("Реквизиты для оплаты 💳",
                                                       callback_data=f"#31#&{id_travel}"))  # info_to_pay
                             .add(InlineKeyboardButton("Назад",
                                                       callback_data=f"#32#"))  # back_to_client_book_list
                             .add(InlineKeyboardButton("Отменить запись ❌",
                                                       callback_data=f"#33#&{string[0]}&{string[1]}&{string[2]}"))  # cancel_by_client
                             )


async def all_info_client_archive_book(message, callback, id_travel):
    """
    Получить информацию по конкретному завершенному бронированию (client)
    """
    for string in sql_part.sql_info_travel(id_travel):
        await bot.send_photo(callback.from_user.id, string[6],
                             f'{string[1]}\n\nДата: {string[2]}\nОписание: {string[3]} '
                             f'\nСтоимость: {string[4]}',
                             reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                             # .add(InlineKeyboardButton("Уведомить об оплате 💸",
                             #                           callback_data=f"#29#&{string[0]}&{string[1]}&{string[2]}"))  # payment
                             .add(InlineKeyboardButton("Оставить отзыв ✏",
                                                       callback_data=f"#30#&{string[1]}&{string[2]}&{string[0]}"))  # review
                             # .add(InlineKeyboardButton("Реквизиты для оплаты 💳",
                             #                           callback_data=f"#31#&{id_travel}"))  # info_to_pay
                             .add(InlineKeyboardButton("Назад",
                                                       callback_data=f"#49#"))  # back_to_client_book_list
                             # .add(InlineKeyboardButton("Отменить запись ❌",
                             #                           callback_data=f"#33#&{string[0]}&{string[1]}&{string[2]}"))  # cancel_by_client
                             )


async def client_cancel_book(callback, id_travel, travel_name, travel_date):
    """
    Отмена записи  -  клиент
    """
    tg_user_id = callback.from_user.id
    client_name = sql_part.sql_get_client_name(id_travel, tg_user_id)
    await sql_part.sql_cancel_travel_client_by_client(id_travel, tg_user_id)
    await callback.answer(text=f"😢 Бронирование:\n{travel_name} от {travel_date} отменено")
    await clear_chat_2(callback.message, 10)
    await bot.send_message(bot_token.MSG_STOREGE, f"❌ @{callback.from_user.username}\n{client_name}"
                                                  f"\n___________________________________________\n\n"
                                                  f"😕 Отменил(а) запись на путешествие:\n{travel_name} oт {travel_date}")
    if len(sql_part.sql_show_me_my_book_client(callback.from_user.id)) == 0:
        await callback.message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=client_buttons)
    else:
        await all_client_book_list(callback.message, callback)
        await callback.answer()


async def confirm_action_client_cancel_book(callback, id_travel, travel_name, travel_date):
    """
    Запрос на подтверждение удаления записи клиента  -  клиент
    """
    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    await callback.message.answer(f"<b>Точно?</b>😱", reply_markup=keyboard
                         .insert(InlineKeyboardButton('Да, 100% 😤', callback_data=f'#34#&{id_travel}&{travel_name}&{travel_date}'))  # client_delete__book_yes_action
                         .insert(InlineKeyboardButton('Нет 😰', callback_data='#35#')), parse_mode="html"  # client_delete__book_no_action
                         )


""""""""""""""""""" client-handlers """""""""""""""""""""

""" Получить список путешествий - клиент """


@dp.callback_query_handler(filters.Text(contains="#3#"))
async def book_list_command_call(callback: types.CallbackQuery):
    if await exist_or_not_travel() is False:
        await callback.answer("Не нашел путешествий, пока не получится записаться 😔")
    else:
        await clear_chat_2(callback.message, 10)
        await list_travel_client(callback.message)
        await callback.answer()


""" Назад - из списка путешествий к главному меню - client"""


@dp.callback_query_handler(filters.Text(contains="#24#"))
async def drop_travel_list_call(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await callback.message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=client_buttons)
    await callback.answer()


""" Получить информацию по конкрентному путешествию - клиент """


@dp.callback_query_handler(filters.Text(contains="#23#"))
async def get_info_list_travel_client_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await all_info_travel_client(callback.message, callback, call[1])
    await callback.answer()


""" Назад - от информации о конкретном путешествии к списку путешествий """


@dp.callback_query_handler(filters.Text(contains="#28#"))
async def back_to_client_travel_list_call(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await list_travel_client(callback.message)


""" Записаться  -  клиент """


@dp.callback_query_handler(filters.Text(contains="#27#"), state=None)
async def book_me_command_call(callback: types.CallbackQuery, state: FSMContext):
    call = callback.data.split("&")
    default_amount_book_info = sql_part.sql_get_default_amount_book_info(call[1])
    current_amount_book_info = sql_part.sql_get_current_amount_book_info(call[1])
    if len(sql_part.sql_check_does_client_already_book(call[1], callback.from_user.id)) != 0:
        await callback.answer('Ты уже записался(лась) на это путешествие! 😀')
        await callback.answer()
    elif current_amount_book_info == default_amount_book_info:
        await callback.answer("😔 К сожалению, на данный момент, полная запись.")
    elif sql_part.sql_get_book_status(call[1]) == "close":
        await callback.answer('Сорри, пока запись закрыта 😔')
        await callback.answer()
    else:
        await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await FSMClient.travel_id.set()
        id_travel = call[1]
        async with state.proxy() as data:
            data["id_travel"] = id_travel
        await FSMClient.tg_user_id.set()
        tg_user_id = callback.from_user.id
        async with state.proxy() as data:
            data["tg_user_id"] = tg_user_id
            print(data["tg_user_id"])
        await FSMClient.travel_name.set()
        travel_name = call[2]
        async with state.proxy() as data:
            data["travel_name"] = travel_name
        await FSMClient.travel_date.set()
        travel_date = call[3]
        async with state.proxy() as data:
            data["travel_date"] = travel_date
        await FSMClient.tg_user_name.set()
        tg_user_name = callback.from_user.username
        async with state.proxy() as data:
            data["tg_user_name"] = tg_user_name
        await FSMClient.next()
        await callback.message.answer("Сколько человек записать? 🤔\n\n👉 Или нажми "
                                      "/cancel, чтобы выйти из режима записи на путешествие.\n\n"
                                      "❗ Записываясь на путешествие ты подтверждаешь\n[согласие на передачу и "
                                      "обработку персональных данных](https://docs.google.com/document/d/1dcrCyFlqhcJBn"
                                      "xXuG93DSFixqZ5XAwdCDU3aDNIGzQY/edit?usp=sharing)", parse_mode="Markdown", disable_web_page_preview=True)
        await callback.answer()  # [friendstrip](https://www.instagram.com/friends_trip/)
                                 # <a href='{path}'>Пользовательское соглашение</a>"


@dp.message_handler(state=FSMClient.client_amount)
async def load_client_amount(messsage: types.Message, state: FSMContext):
    if messsage.text.isdigit() is False:
        await bot.send_message(messsage.from_user.id, "Некорректное значение, попробуй еще раз 🤓\n\n👉 Или нажми "
                                                      "/cancel, чтобы выйти из режима записи на путешествие.")
    else:
        async with state.proxy() as data:
            default_amount_book_info = sql_part.sql_get_default_amount_book_info(data['id_travel'])
            current_amount_book_info = sql_part.sql_get_current_amount_book_info(data['id_travel'])
            # if current_amount_book_info == default_amount_book_info:
            #     await bot.send_message(messsage.from_user.id,
            #                            f"😔 К сожалению, на данный момент, полная запись, попробуй позже, "
            #                            f"может у кого-нибудь изменяться планы. \n\nНажми "
            #                            f"/cancel для выхода из режима записи.")
            if default_amount_book_info < current_amount_book_info + int(messsage.text):
                free_places = default_amount_book_info - current_amount_book_info
                await bot.send_message(messsage.from_user.id,
                                       f"😱 Ой, слишком много, cвободных мест всего - {free_places}, "
                                       f"введи поменьше. \n\n👉 Или нажми "
                                                      "/cancel, чтобы выйти из режима записи на путешествие.")
            else:
                data["client_amount"] = messsage.text
                await FSMClient.next()
                await messsage.answer("Введи свое ФИО, пожалуйста, в формате: Иванов Иван Иванович 😊\n\n👉 Или нажми "
                                                      "/cancel, чтобы выйти из режима записи на путешествие.")


@dp.message_handler(state=FSMClient.client_name)
async def load_client_name(messsage: types.Message, state: FSMContext):
    if len(messsage.text.split()) != 3:
        await bot.send_message(messsage.from_user.id, "Введи ФИО полностью, пожалуйста 🙏\n\n👉 Или нажми "
                                                      "/cancel, чтобы выйти из режима записи на путешествие.")
    else:
        async with state.proxy() as data:
            data["client_name"] = messsage.text
        await FSMClient.next()
        await messsage.answer("Теперь номер телефона ☎\n👉 без 8 и +7 в начале, в формате: 9998887776\n\n👉 Или нажми "
                                                      "/cancel, чтобы выйти из режима записи на путешествие.")


@dp.message_handler(state=FSMClient.phone)
async def load_phone(message: types.Message, state: FSMContext):
    last_msg = message
    if message.text.isdigit() is False or len(message.text) != 10:
        await bot.send_message(message.from_user.id,
                               "Некорректный номер, попробуйте еще раз 🤓,\n👉 без 8 и +7 в начале, в формате: 9998887776\n\n👉 Или нажми "
                                                      "/cancel, чтобы выйти из режима записи на путешествие.")
        await FSMClient.phone.set()
    else:
        async with state.proxy() as data:
            data["phone"] = "+7" + message.text
        # del data['travel_name']
        # del data['travel_date']
        await sql_part.sql_book(state)
        await state.finish()
        await clear_chat_2(last_msg, 20)
        await message.answer(f"Записали тебя! ❤\n\nПутешествие: {data['travel_name']}\nДата: {data['travel_date']}\n\nРады, что ты теперь в нашей команде! 🤗\nПозже пришлем информацию о "
                              "времени и месте встречи.\n\n🙏 Просьба перевести оплату по номеру карты или "
                              "по номеру телефона:\n"
                              "💳 4058 7031 3342 ****\n☎ тел. 952 502 ** **\n\nУведомить об оплате можно через вкладку "
                              "'Мои бронирования' в меню.\n\nДо связи!")
        time.sleep(2)
        await bot.send_message(message.chat.id, '🟢 Что будем делать? Выбери ниже ⬇', reply_markup=client_buttons)
        await bot.send_message(bot_token.MSG_STOREGE, f"✅ @{message.from_user.username}\n{data['client_name']}"
                                                      f"\n___________________________________________\n\n"
                                                      f"🥳 Записался(лась) на путешествие:\n{data['travel_name']} от "
                                                      f"{data['travel_date']}")


""" Мои бронирования  -  клиент """


@dp.callback_query_handler(filters.Text(contains="#4#"))
async def get_my_book_command(callback: types.CallbackQuery):
    if len(sql_part.sql_show_me_my_book_client(callback.from_user.id)) == 0:
        await callback.answer("Не нашел бронирований 😔")
    else:
        await clear_chat_2(callback.message, 10)
        await all_client_book_list(callback.message, callback)
        await callback.answer()


""" Мои завершенные бронирования  -  клиент """


@dp.callback_query_handler(filters.Text(contains="#47#"))
async def get_my_archive_book_command(callback: types.CallbackQuery):
    if len(sql_part.sql_show_me_my_archive_book_client(callback.from_user.id)) == 0:
        await callback.answer("Не нашел завершенных поездок!")
    else:
        await clear_chat_2(callback.message, 10)
        await all_client_archive_book_list(callback.message, callback)
        await callback.answer()


""" Назад - от списка бронирований к главному меню - клиент"""


@dp.callback_query_handler(filters.Text(contains="#26#"))
async def back_to_head_menu_client_call(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await callback.message.answer('🟢 Что будем делать? Выбери ниже ⬇', reply_markup=client_buttons)
    await callback.answer()


# @dp.callback_query_handler(filters.Text(contains="back_to_all_info_travel"))
# async def back_to_all_info_travel(callback: types.CallbackQuery):
#     call = callback.data.split('&')
#     await all_info_travel_admin(callback.message, callback, call[1])
#     await callback.answer()


""" Получить инофрмацию по конкретному бронированию """


@dp.callback_query_handler(filters.Text(contains="#25#"))
async def client_all_book_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await all_info_client_book(callback.message, callback, call[1])
    await callback.answer()


""" Получить инофрмацию по конкретному завершенному бронированию """


@dp.callback_query_handler(filters.Text(contains="#48#"))
async def client_all_archive_book_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await all_info_client_archive_book(callback.message, callback, call[1])
    await callback.answer()


""" Назад - от конкретной информации по бронированию к списку бронирований """


@dp.callback_query_handler(filters.Text(contains="#32#"))
async def back_to_client_all_book_call(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await all_client_book_list(callback.message, callback)
    await callback.answer()


""" Назад - от конкретной информации по бронированию к списку завершенных путешествий  """


@dp.callback_query_handler(filters.Text(contains="#49#"))
async def back_to_client_all_archive_book_call(callback: types.CallbackQuery):
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await all_client_archive_book_list(callback.message, callback)
    await callback.answer()


""" Уведомить об оплате  -  клиент """


@dp.callback_query_handler(filters.Text(contains="#29#"))
async def cancel_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    if sql_part.sql_get_book_archive_status(call[1]) == 'no':
        await callback.answer("Путешествие прошло, не могу выпонить команду! нажми назад")
    else:
        tg_user_id = callback.from_user.id
        client_name = sql_part.sql_get_client_name(call[1], tg_user_id)
        await bot.send_message(bot_token.MSG_STOREGE, f"💸 @{callback.from_user.username}\n{client_name}"
                                                   f"\n___________________________________________\n\n"
                                                   f"Подтвердил(а) оплату за путешествие:\n{call[2]} oт {call[3]}👌"
                                                   f"\n\nПроверь поступление 🔎")
        await callback.answer(text=f"👌 Спасибо, уведомление получили")
        await callback.answer()


""" Оставить отзыв  -  клиент """


@dp.callback_query_handler(filters.Text(contains="#30#"), state=None)
async def get_my_book_command(callback: types.CallbackQuery, state: FSMContext):
    call = callback.data.split("&")
    await FSMClientReview.name.set()
    name = call[1]
    async with state.proxy() as data:
        data["name"] = name
    await FSMClientReview.date.set()
    date = call[2]
    async with state.proxy() as data:
        data["date"] = date
    await FSMClientReview.id_travel.set()
    id_travel = call[3]
    async with state.proxy() as data:
        data["id_travel"] = id_travel
    await FSMClientReview.review.set()
    await callback.message.answer("С нетерпением ждем твой отзыв 🧐\nРасскажи, что понравилось, а что нет."
                                  "\n\n👉 Или нажми /cancel для выхода из "
                                       "режима отправки отзыва.")
    await callback.answer()


@dp.message_handler(state=FSMClientReview.review)
async def load_review(messsage: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["review"] = messsage.text
    tg_user_id = messsage.from_user.id
    client_name = sql_part.sql_get_client_name(data["id_travel"], tg_user_id)
    await bot.send_message(bot_token.MSG_STOREGE,
                           f"✏ Отзыв от @{messsage.from_user.username}\n{client_name}\n "
                           f"\nПутешествие:\n{data['name']} от {data['date']}"
                           f"\n___________________________________________\n\n{data['review']}")
    await state.finish()
    last_msg = await messsage.answer("Спасибо, нам важно каждое мнение! 🤗")
    time.sleep(2)
    await clear_chat_2(last_msg, 4)


""" Реквизиты для оплаты  -  клиент """


@dp.callback_query_handler(filters.Text(contains="#31#"))
async def cancel_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    if sql_part.sql_get_book_archive_status(call[1]) == 'no':
        await callback.answer("Путешествие прошло, не могу выпонить команду! Нажми 'Назад'")
    else:
        await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
        await callback.message.answer("Оплату можно перевести по номеру карты или "
                                  "по номеру телефона:\n"
                                  "💳 4058 7031 3342 ****\n☎ тел. 952 502 ** **\n\nСообщить об оплате можно по кнопке "
                                  "'Уведоить об оплате' в предыдущем меню.\n\nСпасибо! 🙏",
                                      reply_markup=InlineKeyboardMarkup(row_width=2, resize_keyboard=True) \
                                 .insert(InlineKeyboardButton("Назад",
                                                           callback_data=f"#36#&{call[1]}")))  # back_to_all_info_book


""" Назад - от информации об оплате к информации о конкретном путешествии """


@dp.callback_query_handler(filters.Text(contains="#36#"))
async def back_to_all_info_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await bot.delete_message(message_id=callback.message.message_id, chat_id=callback.message.chat.id)
    await all_info_client_book(callback.message, callback, call[1])
    await callback.answer()


""" Отменить запись  -  клиент """


@dp.callback_query_handler(filters.Text(contains="#33#"))
async def cancel_travel_call(callback: types.CallbackQuery):
    call = callback.data.split("&")
    if sql_part.sql_get_book_archive_status(call[1]) == 'no':
        await callback.answer("Путешествие прошло, не могу выпонить команду! Нажми 'Назад'")
    else:
        await confirm_action_client_cancel_book(callback, call[1], call[2], call[3])
        await callback.answer()


""" Подтверждение удаление записи клиента - клиент """


@dp.callback_query_handler(filters.Text(contains="#34#"))
async def yes_command(callback: types.CallbackQuery):
    call = callback.data.split("&")
    await client_cancel_book(callback, call[1], call[2], call[3])


""" Отмена операции удаления записи клиента - клиент """


@dp.callback_query_handler(filters.Text(contains="#35#"))
async def yes_command(callback: types.CallbackQuery):
    await clear_chat_2(callback.message, 1)
    await callback.answer()


""" Ответ на неизвестный звпрос  -  админ/клиент """


@dp.message_handler()
async def unknown_command(message: types.Message):
    last_msg = await message.answer("прости, не знаю такую команду! 🤷‍♂")
    time.sleep(1.5)
    await clear_chat_2(last_msg, 2)


""" Запуск бота """
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

