import telebot
from telebot import types  # для указание типов
import requests
import xml.etree.ElementTree as tree
from datetime import datetime

# Текущая дата
now = datetime.now()


def get_data(date):
    """
    Получение данных о курсе валют с api Центробанка
    :param date: дата
    :return: xml данные
    """
    # Запрос данных
    response_API = requests.get('https://www.cbr.ru/scripts/'
                                'XML_daily.asp?date_req=' + date)
    # Удаление версии и кодировки, так так из-за кодировки не читает
    data = response_API.text.replace('<?xml version="1.0" encoding='
                                     '"windows-1251"?>', '')
    return tree.fromstring(data)


def get_currency_list(date_input=now.strftime("%d/%m/%Y")):
    """
    Получение массива валют
    :param date_input: xml данные
    :return: Массив с валютами
    """
    currency_list = []
    for currency in get_data(date=date_input):
        currency_list.append(currency)
    return currency_list


# Инициализация бота
bot = telebot.TeleBot('5562651062:AAFTKNV5jOBYJc_YbTFIpwL3WZMOzdv3xMY')


@bot.message_handler(commands=['start'])
def start(message):
    """
    Запуск бота
    :param message: Сообщение
    """
    # Отображение кнопок
    markup = show_keyboard()
    bot.send_message(message.chat.id,
                     text="Привет, {0.first_name}! Я бот для отслеживания "
                          "курса валют. Благодаря мне ты можешь "
                          "вывести курсы всех валют на сегодняшний день или"
                          " любой другой. Для того чтобы узнать курс"
                          " нужной валюты нужно написать ее название в"
                          " чат".format(message.from_user),
                     reply_markup=markup)


def show_keyboard():
    """
    Отображение кнопок в чате
    :return: маркап
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Текущий курс")
    btn2 = types.KeyboardButton("Выбрать дату")
    btn3 = types.KeyboardButton("❓❓❓")
    btn4 = types.KeyboardButton("Перевод курса")
    btn5 = types.KeyboardButton("Выбор одной валюты")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup


@bot.message_handler(content_types=['text'])
def get_message(message):
    # Массив с количеством валют и названием
    check = message.text.split(' ')
    if message.text == "Текущий курс":
        for curr in get_currency_list():
            # Отображение информации о валютах на сегодняшний день
            show_data_in_chat(curr, message)
    elif message.text == "❓❓❓":
        # Отображение новых кнопок для общения с пользователем
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button = types.KeyboardButton("Что я могу?")
        back = types.KeyboardButton("Вернуться в главное меню")
        markup.add(button, back)
        bot.send_message(message.chat.id, text="Задай мне вопрос",
                         reply_markup=markup)

    elif message.text == "Выбрать дату":
        bot.send_message(message.chat.id, "Введите дату, которая вас "
                                          "интересует в формате dd/mm/yyyy")

    elif message.text == "Как меня зовут?":
        bot.send_message(message.chat.id, "У меня нет имени..")

    elif message.text == "Перевод курса":
        bot.send_message(message.chat.id,
                         "Введите сумму и название валюты,например, 100 евро")

    elif message.text == "Выбор одной валюты":
        bot.send_message(message.chat.id, "Введите название валюты")

    elif message.text == "Что я могу?":
        bot.send_message(message.chat.id,
                         text="Я могу предоставлять актуальную иформацию о "
                              "курсе валют в соответствии с информацией "
                              "Центробанка")
        bot.send_message(message.chat.id,
                         text="Чтобы выбрать нужную дату просто напиши ее в "
                              "чат. Для того чтобы"
                              " получить курс по текущей валюте введите "
                              "название этой валюты")

    elif message.text == "Вернуться в главное меню":
        # Отображение изначальной клавиатуры
        markup = show_keyboard()
        bot.send_message(message.chat.id, text="Вы вернулись в главное меню",
                         reply_markup=markup)

    # Если длина строки соответствует нужному паттерну
    elif len(message.text) == 10:
        try:
            for curr in get_currency_list(message.text):
                show_data_in_chat(curr, message)
        except Exception:
            bot.send_message(message.chat.id, "Дата выглядит странно...")

    # Введенное сообщение является текстом, который может быть валютой
    elif message.text.isalpha():
        for curr in get_currency_list():
            show_data_in_chat(curr, message, message.text)

    # Если введенное сообщение является из себя количество и название валюты
    elif check[0].isdigit() and check[1].isalpha():
        counter = 0
        for curr in get_currency_list():
            name = curr.find('Name').text
            if check[1].lower() in name.lower():
                nominal = int(curr.find('Nominal').text)
                value = float(curr.find('Value').text.replace(',', '.'))
                res_in_rub = int(check[0]) * (value / nominal)
                bot.send_message(message.chat.id,
                                 text=f'{int(check[0])}'
                                 f' {name}\n = {res_in_rub}'
                                 f' Российских рублей')
                counter += 1
        if counter == 0:
            bot.send_message(message.chat.id, text='Не могу найти информацию')

    else:
        bot.send_message(message.chat.id, text="На такую команду я не "
                                               "запрограммирован...")


def show_data_in_chat(curr, message, need_name=""):
    """
    Отображение всех данных о валюте
    :param curr: Валюта
    :param message: Сообщение
    :param need_name: Имя, которое запрашивает пользователь
    """
    counter = 0
    name = curr.find('Name').text
    numCode = curr.find('NumCode').text
    charCode = curr.find('CharCode').text
    nominal = int(curr.find('Nominal').text)
    value = float(curr.find('Value').text.replace(',', '.'))
    if need_name == "" or need_name.lower() in name.lower():
        counter += 1
        bot.send_message(message.chat.id,
                         text=f'Название: {name}\nNumCode: {numCode}'
                         f'\nCharCode: {charCode}\nНоминал: {nominal}'
                         f'\nСтоимость: {value}')
    if counter == 0:
        bot.send_message(message.chat.id, text='Не могу найти информацию')


# Бесконечная работа бота
bot.polling(none_stop=True)
