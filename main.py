import telebot
from telebot import *
import requests
import sqlite3
from datetime import datetime, timezone, timedelta
import time
import threading
import json


with open("tokens.json", "r") as f:
    tokens = json.load(f)

bot_token = tokens["bot_token"]
weather_token = tokens["weather_token"]


bot = telebot.TeleBot(bot_token)

def create_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            chat_id TEXT NOT NULL,
            date Text NOT NULL,
            subscribe INTEGER DEFAULT 1,
            latitude TEXT,
            longitude TEXT,
            city TEXT
        )
    """)
    conn.commit()
    conn.close()

create_db()

def add_user(username, chat_id, date, latitude, longitude, city):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, chat_id, date, latitude, longitude, city) VALUES (?, ?, ?, ?, ?, ?)", 
               (username, chat_id, date, latitude, longitude, city))
    conn.commit()
    conn.close()

def user_exists(chat_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE chat_id = ?", (chat_id,),)
    count = cursor.fetchone()[0]
    
    conn.close()
    return count > 0

def update_location(chat_id, latitude, longitude, city_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
                UPDATE users 
                SET latitude = ?, longitude = ?, city = ?
                WHERE chat_id = ?
            """, (latitude, longitude, city_name, chat_id))
    
    conn.commit()
    conn.close()

def get_user_by_chatid(chat_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    user = cursor.fetchone()
    conn.close()

    return user

def update_subscribe(chat_id, subscribe):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
                UPDATE users 
                SET subscribe = ? 
                WHERE chat_id = ?
            """, (subscribe, chat_id))
    
    conn.commit()
    conn.close()

def delete_account(chat_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("""
                DELETE FROM users
                WHERE chat_id = ?
            """, (chat_id,))
    
    conn.commit()
    conn.close()

def get_city(latitude, longitude):
    try:
        res = requests.get(f"https://api.openweathermap.org/geo/1.0/reverse?lat={latitude}&lon={longitude}&lang=ru&appid={weather_token}")
        data = res.json()
        for i in data:
            ru = i["local_names"]["ru"]
        return ru
    except Exception as ex:
        print(f"Произошла ошибка: {ex}")

def get_weather(latitude, longitude):
    try:
        res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&units=metric&lang=ru&appid={weather_token}")
        data = res.json()

        description = data["weather"][0]["description"].capitalize()
        icon = data["weather"][0]["icon"]
        

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        pressure = data["main"]["pressure"]
        humidity = data["main"]["humidity"]
        sea_level = data["main"]["sea_level"]

        wind_speed = data["wind"]["speed"]
        clouds = data["clouds"]["all"]

        country = data["sys"]["country"]
        name = data["name"]

        tz = timezone(timedelta(seconds=data["timezone"]))
        sunrise = datetime.fromtimestamp(data["sys"]["sunrise"], tz=tz).strftime("%H:%M:%S")
        sunset = datetime.fromtimestamp(data["sys"]["sunset"], tz=tz).strftime("%H:%M:%S")

        
        msg = f"*{description}*\n🌡️ {temp}°C, ощущается {feels_like}°C\n⏲️ Давление {round(pressure * 0.750062, 2)} мм.рт.ст.\n💧 Влажность {humidity}%\n🌊 Уровень моря {sea_level} м\n💨 Скорость ветра {wind_speed} м/с\n☁️ Облака {clouds}%\n🌅 Восход {sunrise}\n🌇 Закат {sunset}\n🚩 Страна {country}\n🌍 Ближайшая метеостанция {name}"
        return msg
    except Exception as ex:
        print(f"Произошла ошибка: {ex}")
        return "⚠️ Не удалось загрузить прогноз. Попробуйте позже."


def get_forecast(latitude, longitude):
    try:
        res = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&units=metric&lang=ru&appid={weather_token}"
        )
        data = res.json()

        name = data["city"]["name"]
        country = data["city"]["country"]

        msg = f"🏙️ *Прогноз для метеостанции {name}, {country}*\n\n"

        forecasts = data["list"][:8]

        for item in forecasts:
            dt_txt = item["dt_txt"]
            temp = item["main"]["temp"]
            feels_like = item["main"]["feels_like"]
            humidity = item["main"]["humidity"]
            pressure = round(item["main"]["pressure"] * 0.750062, 2)
            description = item["weather"][0]["description"].capitalize()
            icon = item["weather"][0]["icon"]

            

            time_part = dt_txt.split(" ")[1][:5]

            msg += f"*{time_part}* - {description}\n🌡️ {temp}°C (ощущается как {feels_like}°C)\n💧 Влажность: {humidity}% | ⏲️ Давление: {pressure} мм.рт.ст.\n\n"

        return msg

    except Exception as ex:
        print(f"Произошла ошибка при получении прогноза: {ex}")
        return "⚠️ Не удалось загрузить прогноз. Попробуйте позже."

def send_weather():
    try:
        while True:
            time.sleep(3600)
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE subscribe = 1")
            users = cursor.fetchall()
            conn.close()

            for user in users:
                try:
                    chat_id = user[2]
                    latitude = user[5]
                    longitude = user[6]

                    msg = get_weather(latitude, longitude)
                    bot.send_message(chat_id, msg, parse_mode="Markdown")
                except Exception as ex:
                    print(f"Ошибка отправки уведомления: {ex}")

    except Exception as ex:
        print(f"Ошибка: {ex}")


threading.Thread(target=send_weather).start()

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    if not user_exists(chat_id):
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_geo = types.KeyboardButton(text="📍 Отправить местоположение", request_location=True)
        keyboard.add(button_geo)
        bot.send_message(message.chat.id, f"""Привет {message.from_user.first_name}. Это бот для отправки погоды каждый час. Поделитесь местоположением, чтобы мы показывали погоду из вашего города!""", reply_markup=keyboard)
    
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("👤 Профиль")
        btn2 = types.KeyboardButton("⛅ Получить погоду сейчас")
        btn3 = types.KeyboardButton("📅 Прогноз на 24ч")
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, f"Выберите действие", reply_markup=markup)    

    
@bot.message_handler(content_types=['location'])
def geo(message):
    if message.location != None:
        latitude = message.location.latitude
        longitude = message.location.longitude
        city_name = get_city(latitude, longitude)
        username = message.from_user.username
        chat_id = message.from_user.id
        date = datetime.strftime(datetime.now(), "%d.%m.%Y")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("👤 Профиль")
        btn2 = types.KeyboardButton("⛅ Получить погоду сейчас")
        btn3 = types.KeyboardButton("📅 Прогноз на 24ч")
        markup.add(btn1, btn2, btn3)

        if not user_exists(chat_id):
            add_user(username, chat_id, date, latitude, longitude, city_name)
            bot.send_message(message.chat.id, "Отлично! Вы зарегистрировались в боте", reply_markup=markup)    
        else:
            update_location(chat_id, latitude, longitude, city_name)
            bot.send_message(message.chat.id, f"Местоположение обновлено! Широта {latitude}, долгота: {longitude}", reply_markup=markup)    

    else:
        bot.send_message(message.chat.id, f"Упс. Местоположение не определено. Попробуйте ещё раз")    

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    chat_id = message.chat.id
    
    if message.text == "👤 Профиль":
        if user_exists(chat_id):
            markup = types.ReplyKeyboardMarkup(row_width=1)
            btn1 = types.KeyboardButton("📍 Изменить местоположение", request_location=True)
            btn2 = types.KeyboardButton("Отписаться/Подписаться на рассылку")
            btn3 = types.KeyboardButton("❌ Удалить аккаунт")
            btn4 = types.KeyboardButton("◀️ Назад")
            markup.add(btn1, btn2, btn3, btn4)

            profile = get_user_by_chatid(message.chat.id)

            bot.send_message(message.chat.id, f"*Ваш профиль: \n🆔 id: {profile[0]}\n🪪 Имя пользователя: {profile[1]}\n🗨️ Chat_id: {profile[2]}\n📲 Дата регистрации: {profile[3]}\n📤 Подписка: {profile[4]}\n📍 Широта: {profile[5]}\n📍 Долгота: {profile[6]}\n🏘️ Город: {profile[7]}*", parse_mode='Markdown', reply_markup=markup)
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь через /start")  
            
    elif message.text == "⛅ Получить погоду сейчас":
        if user_exists(chat_id):
            profile = get_user_by_chatid(message.chat.id)

            latitude = profile[5]
            longitude = profile[6]
            data = get_weather(latitude, longitude)
            
            bot.send_message(message.chat.id, data, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь через /start")  
        
    elif message.text == "Отписаться/Подписаться на рассылку":
        if user_exists(chat_id):
            bot.send_message(message.chat.id, f"Отправьте боту 1, если хотите подписаться или 0, чтобы отписаться.")
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь через /start")  


    elif message.text == "0":
        if user_exists(chat_id):
            update_subscribe(chat_id, "0")
            bot.send_message(message.chat.id, f"Вы отписались от рассылки")
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь через /start")  


    elif message.text == "1":
        if user_exists(chat_id):
            update_subscribe(chat_id, "1")
            bot.send_message(message.chat.id, f"Вы подписались на рассылку")
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь через /start")  


    elif message.text == "❌ Удалить аккаунт":
        if user_exists(chat_id):
            delete_account(chat_id)
            bot.send_message(message.chat.id, f"Вы удалили аккаунт в боте. Чтобы опять пользоваться ботом введите /start", reply_markup=types.ReplyKeyboardRemove())
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь через /start")  

    elif message.text == "◀️ Назад":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("👤 Профиль")
        btn2 = types.KeyboardButton("⛅ Получить погоду сейчас")
        btn3 = types.KeyboardButton("📅 Прогноз на 24ч")
        markup.add(btn1, btn2, btn3)

        bot.send_message(message.chat.id, f"Выберите действие", reply_markup=markup)  

    elif message.text == "📅 Прогноз на 24ч":
        if user_exists(chat_id):
            profile = get_user_by_chatid(chat_id)
            latitude = profile[5]
            longitude = profile[6]
            forecast_msg = get_forecast(latitude, longitude)
            bot.send_message(chat_id, forecast_msg, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь через /start")  



bot.infinity_polling()