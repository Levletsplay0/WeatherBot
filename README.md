# 🌤️ Telegram Weather Bot

Простой, но функциональный Telegram-бот для получения актуальной информации о погоде в любом городе мира.

---

## 📸 Скриншоты

![Screenshot1](https://raw.githubusercontent.com/Levletsplay0/WeatherBot/refs/heads/main/Screenshot%201.png)

![Screenshot2](https://github.com/Levletsplay0/WeatherBot/blob/main/Screenshot%202.png)

![Screenshot3](https://github.com/Levletsplay0/WeatherBot/blob/main/Screenshot%203.png)

---

## 🚀 Возможности

- Узнать погоду по названию города
- Автоматическое определение погоды по текущему местоположению (если пользователь разрешил геолокацию)
- Краткое описание: температура, влажность, давление, скорость ветра

---

## 🛠 Технологии

- **Язык**: Python 3.12
- **Библиотеки**:
  - `telebot`
  - `requests`
  - `sqlite3`
  - `datetime и time`
- **API погоды**: [OpenWeatherMap](https://openweathermap.org/api)

---

## 📦 Установка и запуск

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/Levletsplay0/WeatherBot
   cd WeatherBot
2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
3. **Добавьте токены OpenWeatherMap и TelegramBotApi в файл: tokens.json**
      ```bash
   {
    "bot_token": "*****",
    "weather_token": "*****"
   }
