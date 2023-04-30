import mysql.connector
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")


def sql_connection():
    """
    Подключение к БД
    """
    host = "+"  # "-" - localhost; "+" - Heroku host
    connection = None
    match host:
        case "+":
            connection = mysql.connector.connect(MYSQL_URL="mysql://root:ufSOrR0BXGHrjO9V5OqV@containers-us-west-25.railway.app:5442/railway",
                                                 MYSQLDATABASE="railway",
                                                 MYSQLHOST="containers-us-west-25.railway.app",
                                                 MYSQLPASSWORD="ufSOrR0BXGHrjO9V5OqV",
                                                 MYSQLPORT="5442",
                                                 MYSQLUSER="root")

        case "-":
            connection = mysql.connector.connect(user=config["my_sql"]["mysql_user_local"],
                                                 password=config["my_sql"]["mysql_password_local"],
                                                 host=config["my_sql"]["mysql_host_local"],
                                                 database=config["my_sql"]["mysql_database_local"])

    return connection


def sql_start():
    """
    Создание таблиц если они не созданы при первичном подключении к БД
    """

    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS travel(id INTEGER PRIMARY KEY auto_increment, name TEXT, "
                           "date DATE, description TEXT, price TEXT, amount TEXT, photo TEXT, book_status TEXT, "
                           "active TEXT)")

            cursor.execute("CREATE TABLE IF NOT EXISTS client_travel(id INTEGER PRIMARY KEY auto_increment, tg_user_id "
                           "BIGINT, client_name TEXT, phone TEXT, client_amount TEXT, travel_id INTEGER, payment TEXT, "
                           "tg_username TEXT)")
            con.commit()

    except Exception:
        raise


async def sql_add_travel(state):
    """
    Добававить путешествие (admin)
    """
    async with state.proxy() as data:
        query = "INSERT INTO travel (name,date,description,price,amount,photo,book_status, active) " \
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        try:
            connection = sql_connection()
            with connection as con:
                cursor = con.cursor()
                cursor.execute(query,
                               (data['name'], data['date'], data['description'], data['price'], data['amount'],
                                data['photo'],
                                'open', 'yes'))
                con.commit()
        except Exception:
            return "Error db"


async def sql_delete_travel(id):
    """
    Удалить конкретное путешествие (admin)
    """
    query_1 = "DELETE FROM travel WHERE id = %s"
    query_2 = "DELETE FROM client_travel WHERE travel_id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query_1, (id,))
            cursor.execute(query_2, (id,))
            con.commit()
    except Exception:
        raise


async def sql_put_to_archive_travel(id):
    """
    Переместить путешествие в архив  (admin)
    """
    query = "UPDATE travel SET active = 'no' WHERE id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id,))
            con.commit()
    except Exception:
        raise


async def sql_restore_from_archive(id):
    """
    Переместить путешествие в архив  (admin)
    """

    query = "UPDATE travel SET active = 'yes' WHERE id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id,))
            con.commit()
    except Exception:
        raise


def sql_list_travel():
    """
    Получить список путешествий (admin\client)
    """
    query = "Select * FROM travel WHERE active = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, ("yes",))
            message = cursor.fetchall()

    except Exception:
        raise
    return message


def sql_list_travel_archive():
    """
    Получить список прошедших путешествий (admin\client)
    """
    query = "Select * FROM travel WHERE active = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, ("no",))
            message = cursor.fetchall()
    except Exception:
        raise
    return message


def sql_info_travel(id_travel):
    """
    Получить информацию по конкретному путешествию (admin\client)
    """
    query = "Select * FROM travel WHERE id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id_travel,))
            message = cursor.fetchall()
    except Exception:
        raise
    return message


async def sql_book(state):
    """
    Записать на путешествие (admin/client)
    """

    async with state.proxy() as data:
        query = "INSERT INTO client_travel (travel_id, tg_user_id, client_amount, client_name, phone, payment, " \
                "tg_username) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        try:
            connection = sql_connection()
            with connection as con:
                cursor = con.cursor()
                cursor.execute(query, (data['id_travel'], data['tg_user_id'],
                                       data['client_amount'], data['client_name'], data['phone'], '❌',
                                       data['tg_user_name']))
                con.commit()
        except Exception:
            raise


def sql_show_me_my_book_client(tg_user_id):
    """
    Получить список бронирований (client)
    """
    query = "Select client_travel.tg_user_id, travel.id, travel.name, travel.date, travel.description, travel.price, " \
            "travel.amount, travel.photo, client_travel.client_name, travel.active from client_travel join travel " \
            "on travel.id = client_travel.travel_id WHERE tg_user_id = %s and active = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (tg_user_id, 'yes'))
            message = cursor.fetchall()
    except Exception:
        raise
    return message


def sql_show_me_my_archive_book_client(tg_user_id):
    """
    Получить список бронирований (client)
    """
    query = "Select client_travel.tg_user_id, travel.id, travel.name, travel.date, travel.description, travel.price, " \
            "travel.amount, travel.photo, client_travel.client_name from client_travel join travel on travel.id = " \
            "client_travel.travel_id WHERE tg_user_id = %s and active = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (tg_user_id, 'no'))
            message = cursor.fetchall()
    except Exception:
        raise
    return message


async def sql_cancel_travel_client_by_admin(travel_id, id):
    """
    Отмена бронирования (client)
    """
    query = "DELETE FROM client_travel WHERE travel_id = %s and id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (travel_id, id))
            con.commit()
    except Exception:
        raise


async def sql_cancel_travel_client_by_client(travel_id, tg_user_id):
    """
    Отмена бронирования (client)
    """
    query = "DELETE FROM client_travel WHERE travel_id = %s and tg_user_id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (travel_id, tg_user_id))
            con.commit()
    except Exception:
        raise


async def sql_payment_client_notification_true(id_travel, id):
    """
    Измененить статус оплаты (client) - поставить отметку "✅"
    """
    query = "UPDATE client_travel SET payment = '✅' WHERE id = %s and travel_id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id, id_travel))
            con.commit()
    except Exception:
        raise


async def sql_payment_client_notification_false(id_travel, id):
    """
    Измененить статус оплаты (client) - поставить отметку "❌"
    """
    query = "UPDATE client_travel SET payment = '❌' WHERE id = %s and travel_id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id, id_travel))
            con.commit()
    except Exception:
        raise


def sql_get_list_of_travelers_for_one_travel(id_travel):
    """
    Получить список бронирований (admin)
    """
    query = "Select client_name, phone, client_amount, payment, id, tg_user_id, travel_id FROM client_travel " \
            "WHERE travel_id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id_travel,))
            return cursor.fetchall()
    except Exception:
        raise


def sql_get_traveler_info(id, id_travel):
    """
    Получить информацию по клиенту (admin)
    """
    query = "Select client_name, phone, client_amount, payment, id, tg_user_id, tg_username FROM client_travel " \
            "WHERE travel_id = %s and id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id_travel, id))
            return cursor.fetchall()
    except Exception:
        raise


def sql_get_default_amount_book_info(id_travel):
    """
    Показать максимальное кол-во человек для записи на путешествтие (то, которое админ устаноавливает)
    """
    query = "Select amount FROM travel WHERE id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id_travel,))
            for lst in cursor.fetchall():
                for i in lst:
                    return int(i)
    except Exception:
        raise


def sql_get_current_amount_book_info(id_travel):
    """
    Показать текущее количество записавшихся человек на путешествие
    """
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            n = 0
            query = "Select client_amount FROM client_travel WHERE travel_id = %s"
            cursor.execute(query, (id_travel,))
            if len(cursor.fetchall()) == 0:
                return 0
            else:
                query = "Select client_amount FROM client_travel WHERE travel_id = %s"
                cursor.execute(query, (id_travel,))
                for lst in cursor.fetchall():
                    for i in lst:
                        n += int(i)
            return int(n)
    except Exception:
        raise


def sql_get_client_name(id_travel, tg_user_id):
    """
    Получить имя клиента
    """
    query = "Select client_travel.client_name FROM client_travel WHERE tg_user_id = %s and travel_id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (tg_user_id, id_travel))
            for lst in cursor.fetchall():
                for i in lst:
                    return i
    except Exception:
        raise


def sql_check_does_client_already_book(id_travel, tg_user_id):
    """
    Проверить есть ли у клиента уже запись на путешествие на которое он пытается зарегестрироваться
    """
    query = "Select * FROM client_travel WHERE tg_user_id = %s and travel_id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (tg_user_id, id_travel))
            return cursor.fetchall()
    except Exception:
        raise


def sql_close_book(id_travel):
    """
    Закрыть запись
    """
    query = "UPDATE travel set book_status = 'close' WHERE id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id_travel,))
            con.commit()
    except Exception:
        raise


def sql_open_book(id_travel):
    """
    Открыть запись
    """
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            query = "UPDATE travel set book_status = 'open' WHERE id = %s"
            cursor.execute(query, (id_travel,))
            con.commit()
    except Exception:
        raise


def sql_get_book_status(id_travel):
    """
    Получить статус бронирования
    """
    query = "Select book_status FROM travel WHERE id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id_travel,))
            for lst in cursor.fetchall():
                for i in lst:
                    return i
    except Exception:
        raise


def sql_get_book_archive_status(id_travel):
    """
    В архиве путешествие или нет
    """
    query = "Select active FROM travel WHERE id = %s"
    try:
        connection = sql_connection()
        with connection as con:
            cursor = con.cursor()
            cursor.execute(query, (id_travel,))
            for lst in cursor.fetchall():
                for i in lst:
                    return i
    except Exception:
        raise
