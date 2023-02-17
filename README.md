# Booking_bot
EN

Telegram @GFTrips_bot.

This bot was made for an organization that is engaged in one-day trips (departure in the morning, return in the evening) in Kazan and Tatarstan.
The bot was made in order to automate the process of registering a client for a trip and administering these records, i.e.: 
    - the client can sign up for a trip himself, cancel it, leave a review, notify the admin about payment, monitor information about those trips for which he signed up; 
    - the administrator can create trips, delete them, move them to an archive, freeze an appointment for a specific trip, get information about who paid and who didn't, cancel a client's appointment for a specific trip, get full information about the client, send a message to a group of people who signed up.
Also, with a slight change, the bot can be used in any other areas where an appointment is required to receive any services, goods, etc.
The bot is written in python using the aiogram library, a database - MySQL and a server from Heroku.
In the environment variables (bot_token.py) you need to specify:
BOT_TOKEN - unique bot token
ADMIN_ID - telegram ID of the user you want to make admin
MSG_STOREGE - telegram ID of the user where messages on records will be sent (for example: the client signed up, canceled the record, canceled the review or confirmed the payment)

RU

Данный бот был сделан для организации, которая занимается однодневными путешествиями (утром выезд, вечером возвращение) в Казани и Татарстане.

Бот был сделан с целью автоматизации процессов записи клиента на путешествие и администрирования этих записей, т.е.:
	- клиент может сам записаться на путешествие, отменить его, оставить отзыв, уведомить админа об оплате, мониторить информацию о тех путешествиях на которые записался;
	- администратор может создавать путешествия, удалять, перемещать их в архив, замораживать запись на конкретное путешествие, получать информацию о том кто заплатил а кто нет,  отменять запись клиента на конкретное путешествие, получать полную информацию по клиенту, отправить сообщение группе записавшихся.
Также при небольшом изменении бот может быть использован в любых других сферах где необходима предварительная запись для получения каких-либо услуг, товаров и т.д.
Бот написан на языке python с использованием библиотеки aiogram, БД - MySQL и сервера от Heroku.
В переменных окружения (bot_token.py) необходимо указать:
BOT_TOKEN - уникальный токен бота
ADMIN_ID - telegram ID пользователя которого хотите сделать админом 
MSG_STOREGE - telegram ID пользователя куда будут приходить сообщения по записям (например: клиент записался, отменил запись, отставил отзыв или подтвердил оплату )


