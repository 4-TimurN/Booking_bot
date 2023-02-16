import sqlite3 as sql
import mysql.connector
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")


def replace_symbol(query):
    """
    Замена символа "?" на "%s", чтобы запросы были универсальные для всех СУБД
    """
    if con_type == 2:
        query = query.replace("?", "%s")
    return query


def check_connection():
    """
    Переподключиться к БД в случае потери соединения
    """
    if not base.is_connected():
        base.reconnect()


def start_sql():
    """
    Подключение к БД и создание таблиц (если они еще не созданы)
    """
    global cur, base, con_type, host
    con_type = 2  # 0 - SQLlite; 1 - MSSQL; 2 - MySql
    match con_type:
        case 0:
            base = sql.connect(config["sql_lite"]["sql_lite_db_name"])
            cur = base.cursor()

            if base:
                print("SQLlite db connection established")

            base.execute("CREATE TABLE IF NOT EXISTS travel(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "name TEXT, date TEXT, "
                         "description TEXT, price TEXT, amount TEXT, photo TEXT, book_status TEXT)")
            base.commit()
            base.execute("CREATE TABLE IF NOT EXISTS client_travel(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "tg_user_id INTEGER, "
                         "client_name TEXT, phone TEXT, client_amount TEXT, travel_id INTEGER, payment TEXT, "
                         "tg_username TEXT)")
            base.commit()

        # case 1:

            # base = pyodbc.connect(r'Driver={SQL Server}; '
            #                       r'Server=config["ms_sql"]["ms_sql_server"];'
            #                       r'Database=config["ms_sql"]["ms_sql_database"];Trusted_Connection=yes;')
            # cur = base.cursor()
            #
            # if base:
            #     print("MSSQL db connection established")
            #
            # base.execute("if not exists (select * from sysobjects where name='travel' and xtype='U')"
            #              "CREATE TABLE travel(id INTEGER PRIMARY KEY IDENTITY(1,1), name TEXT, date TEXT, "
            #              "description TEXT, price TEXT, amount TEXT, photo TEXT, book_status TEXT)")
            # base.commit()
            # base.execute("if not exists (select * from sysobjects where name='client_travel' and xtype='U') "
            #              "CREATE TABLE client_travel(id INTEGER PRIMARY KEY IDENTITY(1,1), tg_user_id INTEGER, "
            #              "client_name TEXT, phone TEXT, client_amount TEXT, travel_id INTEGER, payment TEXT, "
            #              "tg_username TEXT)")
            # base.commit()

        case 2:
            host = "+"  # "-" - localhost; "+" - Heroku host
            match host:
                case "+":
                    base = mysql.connector.connect(user=config["my_sql"]["mysql_user"],
                                                   password=config["my_sql"]["mysql_password"],
                                                   host=config["my_sql"]["mysql_host"],
                                                   database=config["my_sql"]["mysql_database_heroku"])
                    cur = base.cursor()
                    if base:
                        print("MySql Heroku host db connection established")

                case "-":
                    base = mysql.connector.connect(user=config["my_sql"]["mysql_user_local"],
                                                  password=config["my_sql"]["mysql_password_local"],
                                                  host=config["my_sql"]["mysql_host_local"],
                                                  database=config["my_sql"]["mysql_database_local"])
                    cur = base.cursor()
                    if base:
                        print("MySql localhost db connection established")

            cur.execute("CREATE TABLE IF NOT EXISTS travel(id INTEGER PRIMARY KEY auto_increment, name TEXT, "
                        "date DATE, description TEXT, price TEXT, amount TEXT, photo TEXT, book_status TEXT, "
                        "active TEXT)")
            base.commit()
            cur.execute("CREATE TABLE IF NOT EXISTS client_travel(id INTEGER PRIMARY KEY auto_increment, tg_user_id "
                        "BIGINT, client_name TEXT, phone TEXT, client_amount TEXT, travel_id INTEGER, payment TEXT, "
                        "tg_username TEXT)")
            base.commit()


async def sql_add_travel(state):
    """
    Добававить путешествие (admin)
    """
    check_connection()
    async with state.proxy() as data:
        query = "INSERT INTO travel (name,date,description,price,amount,photo,book_status, active) " \
                "VALUES (?,?,?,?,?,?,?,?)"
        cur.execute(replace_symbol(query),
                    (data['name'], data['date'], data['description'], data['price'], data['amount'], data['photo'], 'open', 'yes'))
        base.commit()


async def sql_delete_travel(id):
    """
    Удалить конкретное путешествие (admin)
    """
    check_connection()
    query = "DELETE FROM travel WHERE id = ?"
    cur.execute(replace_symbol(query), (id,))
    query = "DELETE FROM client_travel WHERE travel_id = ?"
    cur.execute(replace_symbol(query), (id,))
    base.commit()


async def sql_put_to_archive_travel(id):
    """
    Пееместить путешествие в архив  (admin)
    """
    check_connection()
    query = "UPDATE travel SET active = 'no' WHERE id = ?"
    cur.execute(replace_symbol(query), (id,))
    base.commit()


async def sql_restore_from_archive(id):
    """
    Пееместить путешествие в архив  (admin)
    """
    check_connection()
    query = "UPDATE travel SET active = 'yes' WHERE id = ?"
    cur.execute(replace_symbol(query), (id,))
    base.commit()


def sql_list_travel():
    """
    Получить список путешествий (admin\client)
    """
    check_connection()
    query = "Select * FROM travel WHERE active = ?"
    cur.execute(replace_symbol(query), ("yes",))
    message = cur.fetchall()
    return message


def sql_list_travel_archive():
    """
    Получить список прошедших путешествий (admin\client)
    """
    check_connection()
    query = "Select * FROM travel WHERE active = ?"
    cur.execute(replace_symbol(query), ("no",))
    message = cur.fetchall()
    return message


def sql_info_travel(id_travel):
    """
    Получить информацию по конкретному путешествию (admin\client)
    """
    check_connection()
    query = "Select * FROM travel WHERE id = ?"
    cur.execute(replace_symbol(query), (id_travel,))
    message = cur.fetchall()
    return message


async def sql_book(state):
    """
    Записать на путешествие (admin/client)
    """
    check_connection()
    async with state.proxy() as data:
        query = "INSERT INTO client_travel (travel_id, tg_user_id, client_amount, client_name, phone, payment, " \
                "tg_username) VALUES (?,?,?,?,?,?,?)"
        cur.execute(replace_symbol(query), (data['id_travel'], data['tg_user_id'],
                                              data['client_amount'], data['client_name'], data['phone'], '❌',
                                              data['tg_user_name']))
        base.commit()


def sql_show_me_my_book_client(tg_user_id):
    """
    Получить список бронирований (client)
    """
    check_connection()
    query = "Select client_travel.tg_user_id, travel.id, travel.name, travel.date, travel.description, travel.price, "\
            "travel.amount, travel.photo, client_travel.client_name, travel.active from client_travel join travel " \
            "on travel.id = client_travel.travel_id WHERE tg_user_id = ? and active = ?"
    cur.execute(replace_symbol(query), (tg_user_id, 'yes'))
    message = cur.fetchall()
    return message


def sql_show_me_my_archive_book_client(tg_user_id):
    """
    Получить список бронирований (client)
    """
    check_connection()
    query = "Select client_travel.tg_user_id, travel.id, travel.name, travel.date, travel.description, travel.price, "\
            "travel.amount, travel.photo, client_travel.client_name from client_travel join travel on travel.id = "\
            "client_travel.travel_id WHERE tg_user_id = ? and active = ?"
    cur.execute(replace_symbol(query), (tg_user_id, 'no'))
    message = cur.fetchall()
    return message


async def sql_cancel_travel_client_by_admin(travel_id, id):
    """
    Отмена бронирования (client)
    """
    check_connection()
    query = "DELETE FROM client_travel WHERE travel_id = ? and id = ?"
    # cur.execute("DELETE FROM client_travel WHERE tg_name = ? and id_travel = ?", (tg_name, id_travel))
    cur.execute(replace_symbol(query), (travel_id, id))
    base.commit()


async def sql_cancel_travel_client_by_client(travel_id, tg_user_id):
    """
    Отмена бронирования (client)
    """
    query = "DELETE FROM client_travel WHERE travel_id = ? and tg_user_id = ?"
    # cur.execute("DELETE FROM client_travel WHERE tg_name = ? and id_travel = ?", (tg_name, id_travel))
    cur.execute(replace_symbol(query), (travel_id, tg_user_id))
    base.commit()


async def sql_payment_client_notification_true(id_travel, id):
    """
    Измененить статус оплаты (client) - поставить отметку "✅"
    """
    check_connection()
    query = "UPDATE client_travel SET payment = '✅' WHERE id = ? and travel_id = ?"
    cur.execute(replace_symbol(query), (id, id_travel))
    base.commit()


async def sql_payment_client_notification_false(id_travel, id):
    """
    Измененить статус оплаты (client) - поставить отметку "❌"
    """
    check_connection()
    query = "UPDATE client_travel SET payment = '❌' WHERE id = ? and travel_id = ?"
    cur.execute(replace_symbol(query), (id, id_travel))
    base.commit()


def sql_get_list_of_travelers_for_one_travel(id_travel):
    """
    Получить список бронирований (admin)
    """
    check_connection()
    query = "Select client_name, phone, client_amount, payment, id, tg_user_id, travel_id FROM client_travel " \
            "WHERE travel_id = ?"
    cur.execute(replace_symbol(query), (id_travel,))
    return cur.fetchall()


def sql_get_traveler_info(id, id_travel):
    """
    Получить информацию по клиенту (admin)
    """
    check_connection()
    query = "Select client_name, phone, client_amount, payment, id, tg_user_id, tg_username FROM client_travel "\
            "WHERE travel_id = ? and id = ?"
    cur.execute(replace_symbol(query), (id_travel, id))
    return cur.fetchall()


def sql_get_default_amount_book_info(id_travel):
    """
    Показать максимальное кол-во человек для записи на путешествтие (то, которое админ устаноавливает)
    """
    check_connection()
    query = "Select amount FROM travel WHERE id = ?"
    cur.execute(replace_symbol(query), (id_travel,))
    for list in cur.fetchall():
        for i in list:
            return int(i)


def sql_get_current_amount_book_info(id_travel):
    """
    Показать текущее количество записавшихся человек на путешествие
    """
    check_connection()
    n = 0
    query = "Select client_amount FROM client_travel WHERE travel_id = ?"
    cur.execute(replace_symbol(query), (id_travel,))
    if len(cur.fetchall()) == 0:
        return 0
    else:
        query = "Select client_amount FROM client_travel WHERE travel_id = ?"
        cur.execute(replace_symbol(query), (id_travel,))
        for list in cur.fetchall():
            for i in list:
                n += int(i)
    return int(n)


def sql_get_client_name(id_travel, tg_user_id):
    """
    Получить имя клиента
    """
    check_connection()
    query = "Select client_travel.client_name FROM client_travel WHERE tg_user_id = ? and travel_id = ?"
    cur.execute(replace_symbol(query), (tg_user_id, id_travel))
    for list in cur.fetchall():
        for i in list:
            return i


def sql_check_does_client_already_book(id_travel, tg_user_id):
    """
    Проверить есть ли у клиента уже запись на путешествие на которое он пытается зарегестрироваться
    """
    check_connection()
    query = "Select * FROM client_travel WHERE tg_user_id = ? and travel_id = ?"
    cur.execute(replace_symbol(query),(tg_user_id, id_travel))
    return cur.fetchall()


def sql_close_book(id_travel):
    """
    Закрыть запись
    """
    check_connection()
    query = "UPDATE travel set book_status = 'close' WHERE id = ?"
    cur.execute(replace_symbol(query), (id_travel,))
    base.commit()


def sql_open_book(id_travel):
    """
    Открыть запись
    """
    check_connection()
    query = "UPDATE travel set book_status = 'open' WHERE id = ?"
    cur.execute(replace_symbol(query), (id_travel,))
    base.commit()


def sql_get_book_status(id_travel):
    """
    Получить статус бронирования
    """
    check_connection()
    query = "Select book_status FROM travel WHERE id = ?"
    cur.execute(replace_symbol(query), (id_travel,))
    for list in cur.fetchall():
        for i in list:
            return i


def sql_get_book_archive_status(id_travel):
    """
    В архиве путешествие или нет
    """
    check_connection()
    query = "Select active FROM travel WHERE id = ?"
    cur.execute(replace_symbol(query), (id_travel,))
    for list in cur.fetchall():
        for i in list:
            return i