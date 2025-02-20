import telebot
import requests
from configbot import create_connection
import os
import psycopg2
from psycopg2.extras import DictCursor  

# TOKEN = "7247228:AAFpXcjGEzSH1IPAS6r3l1qHSwyU0p-KryY"
TOKEN = "7610501316:AAEqYV6QinsOFysgT-dIZEwFajbgRV-4GrE"
WEATHER_API_KEY = "4284c9e5caf7fc1317b4af603c11d0d1"
IMAGES_DIR = "src\photos"

bot = telebot.TeleBot(TOKEN)
chat_states = {}

def get_available_countries():
    conn = create_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:  # Используем DictCursor
                query = "SELECT DISTINCT name FROM countries;"
                cur.execute(query)
                countries = cur.fetchall()
                available_countries = [country["name"] for country in countries]
                return available_countries
        except Exception as e:
            print(f"Error executing SQL query: {e}")
        finally:
            conn.close()
    else:
        print("Failed to connect to the database.")
        return []

def get_cities_by_country(country):
    conn = create_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = """SELECT name FROM cities 
                          WHERE country_id = (SELECT id FROM countries WHERE name = %s);"""
                cur.execute(query, (country,))
                cities = cur.fetchall()
                available_cities = [city["name"] for city in cities]
                return available_cities
        except Exception as e:
            print(f"Error executing SQL query: {e}")
        finally:
            conn.close()
    else:
        print("Failed to connect to the database.")
        return []

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if data["cod"] == 200:
        weather_description = data["weather"][0]["description"].capitalize()
        temperature = data["main"]["temp"]
        return f"Погода в {city.capitalize()}: Температура 🌡️: {temperature}°C"
    elif data["cod"] == 404:
        return f"Не вдалося отримати дані про погоду для міста '{city}'."
    else:
        return "Не вдалося отримати дані про погоду для цього міста."

def get_places(city):
    conn = create_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                query = """SELECT p.name, p.description, p.image
                          FROM places p
                          JOIN cities c ON p.city_id = c.id
                          WHERE LOWER(c.name) = LOWER(%s)
                          LIMIT 5;"""
                cur.execute(query, (city,))
                places = cur.fetchall()
                return places if places else f"Не знайдено цікавих місць для міста '{city}'"
        except Exception as e:
            print(f"Error executing SQL query: {e}")
            return f"Помилка бази даних: {e}"
        finally:
            conn.close()
    else:
        print("Failed to connect to the database.")
        return "Не вдалося підключитися до бази даних."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    chat_states[chat_id] = {"state": "choose_country"}

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(telebot.types.KeyboardButton("Обрати країну 🌍"))

    sent_message = bot.send_message(chat_id, "Вітаю! Я допоможу вам спланувати вашу подорож. 🌍✈️", reply_markup=markup)
    chat_states[chat_id]["message_id"] = sent_message.message_id

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get("state") in ["start", "choose_country"])
def handle_choose_country(message):
    chat_id = message.chat.id

    if message.text == "Обрати країну 🌍":
        chat_states[chat_id] = {"state": "choose_country"}

        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        available_countries = get_available_countries()
        
        for country in available_countries:
            markup.add(telebot.types.KeyboardButton(country))
        
        bot.send_message(chat_id, "Оберіть країну: 🌍", reply_markup=markup)
    
    elif message.text in get_available_countries():
        chat_states[chat_id] = {"state": "choose_city", "country": message.text, "city_index": 0}
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        available_cities = get_cities_by_country(message.text)
        for city in available_cities:
            markup.add(telebot.types.KeyboardButton(city))
        markup.add(telebot.types.KeyboardButton("На головну 🏠"))
        bot.send_message(chat_id, f"Оберіть місто в {message.text}: 🏙️", reply_markup=markup)

    else:
        bot.send_message(chat_id, "Будь ласка, натисніть кнопку з назвою країни.")

@bot.message_handler(func=lambda message: chat_states.get(message.chat.id, {}).get("state") == "choose_city")
def show_place(message):
    chat_id = message.chat.id
    if message.text == "На головну 🏠":
        chat_states[chat_id] = {"state": "start"}
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("Обрати країну 🌍"))
        bot.send_message(chat_id, "Ви повернулися на головну сторінку. 🏠", reply_markup=markup)
        return

    print(f'chat_states: {chat_states}')
    city = message.text
    chat_state = chat_states[chat_id]
    country = chat_state["country"]
    city_index = chat_state["city_index"]

    weather_info = get_weather(city)
    places = get_places(city)

    bot.send_message(chat_id, weather_info)

    if isinstance(places, str):
        bot.send_message(chat_id, places)
    else:
        place = places[city_index]
        try:
            with open(place["image"], "rb") as image_file:
                sent_message = bot.send_photo(chat_id, image_file, caption=f"{place['name']} – {place['description']}")
        except (FileNotFoundError, IOError):
            sent_message = bot.send_message(chat_id, f"{place['name']} – {place['description']}")

    markup = telebot.types.InlineKeyboardMarkup()

    print(city_index)
    if city_index > 0:
        markup.add(telebot.types.InlineKeyboardButton("⬅️ Назад", callback_data="prev"))
    if city_index < len(places) - 1:
        markup.add(telebot.types.InlineKeyboardButton("Далі ➡️", callback_data="next"))

    markup.add(telebot.types.InlineKeyboardButton("Обрати інше місто 🏙️", callback_data="choose_city"))

    chat_states[chat_id] = {"state": "show_place", "country": country, "city": city, "places": places,
                            "city_index": city_index, "message_id": sent_message.message_id}
    bot.send_message(chat_id, "Натисніть 'Далі', 'Назад' або 'Обрати інше місто'.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    chat_state = chat_states.get(chat_id, {})

    if chat_state.get("state") == "show_place":
        places = chat_state["places"]
        city_index = chat_state["city_index"]
        message_ids = chat_state.get("message_ids", [])

        message_ids.append(chat_state.get("message_id"))
        for message_id in message_ids:
            if message_id is not None:
                try:
                    bot.delete_message(chat_id, message_id)
                except telebot.apihelper.ApiTelegramException as e:
                    if e.error_code == 400 and "message to delete not found" in e.description:
                        pass
                    else:
                        raise e

    if call.data == "next":
        city_index += 1
    elif call.data == "prev":
        city_index -= 1
    elif call.data == "choose_city":
        chat_states[chat_id] = {"state": "choose_city", "country": chat_state["country"], "city_index": 0}
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        available_cities = get_cities_by_country(chat_state["country"])
        for city in available_cities:
            markup.add(telebot.types.KeyboardButton(city))
        markup.add(telebot.types.KeyboardButton("На головну 🏠"))
        bot.send_message(chat_id, f"Оберіть місто в {chat_state['country']}: 🏙️", reply_markup=markup)

        return
    place = places[city_index]
    image_path = os.path.join(IMAGES_DIR, place["image"])
    try:
        with open(image_path, "rb") as image_file:
            sent_photo = bot.send_photo(chat_id, image_file, caption=f"{place['name']} – {place['description']}")
    except (FileNotFoundError, IOError):
        sent_photo = bot.send_message(chat_id, f"{place['name']} – {place['description']}")

    markup = telebot.types.InlineKeyboardMarkup()
    if city_index > 0:
        markup.add(telebot.types.InlineKeyboardButton("⬅️ Назад", callback_data="prev"))
    if city_index < len(places) - 1:
        markup.add(telebot.types.InlineKeyboardButton("Далі ➡️", callback_data="next"))
    markup.add(telebot.types.InlineKeyboardButton("Обрати інше місто 🏙️", callback_data="choose_city"))

    sent_message = bot.send_message(chat_id, "Натисніть 'Далі', 'Назад' або 'Обрати інше місто'.", reply_markup=markup)

    chat_states[chat_id] = {
        "state": "show_place", 
        "country": chat_state["country"], 
        "city": chat_state["city"],
        "places": places, 
        "city_index": city_index,
        "message_ids": [sent_photo.message_id, sent_message.message_id]
    }

if __name__ == '__main__':
    bot.polling()