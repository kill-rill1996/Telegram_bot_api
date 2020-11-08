import urllib

import telebot
from telebot import types
import requests

import config


bot = telebot.TeleBot(config.token)


def load_photo(url):
    """Обработка фото с url"""
    f = open('images/out.jpg', 'wb')
    f.write(urllib.request.urlopen(url).read())
    f.close()
    return open('images/out.jpg', 'rb')


def create_markup(id=None):
    """Кнопки для подробной информации и добавления товара в корзину"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    detail = types.InlineKeyboardButton('Описание 🔍', callback_data=f'd{id}')
    add_to_cart = types.InlineKeyboardButton('В корзину ✅', callback_data=f'+{id}')
    return markup.add(detail, add_to_cart)


def create_markup_sale(id):
    """Кнопки для уменьшение и увелечения количества товаров в корзине"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    add_to_cart = types.InlineKeyboardButton('➕', callback_data=f'+{id}')
    remove_from_cart = types.InlineKeyboardButton('➖', callback_data=f'-{id}')
    return markup.add(add_to_cart, remove_from_cart)


def get_data(pref):
    """
    Возвращает данные по url
    :param pref: добавочный url
    :return: json data
    """
    url = config.url + pref
    return requests.get(url).json()


def is_sale(item):
    """Добавляет SALE и скидку в % для товаров со скидкой"""
    if item['discount_price']:
        sale = round((1 - (item['discount_price'] / item['price'])) * 100)
        mess = f'<b>{item["title"]}</b>' + '\n' + f'Категория: {item["category"]}' + '\n' + f'Цена {item["discount_price"]}' \
               + '❗️💸' + f' (SALE {sale}%)'
    else:
        mess = f'<b>{item["title"]}</b>' + '\n' + f'Категория: {item["category"]}' + '\n' + f'Цена {item["price"]}'
    return mess


def item_detail(item):
    mess = is_sale(item)
    mess += '\n' + f'\n {item["description"]}'
    return mess


def get_item(item, message):
    """Выводит товар с фото"""
    mess = is_sale(item)
    img = load_photo(item['image'])
    markup = create_markup(item['id'])
    bot.send_photo(message.from_user.id, img, caption=mess, parse_mode='html', reply_markup=markup)


def get_token():
    """Возвращает токен для авторизации"""
    f = open('auth_token.txt')
    token = f.read()
    f.close()
    return token


def items_for_cart(message, item):
    """Отображение добавленых в корзину товаров"""
    if item['discount_price']:
        sale = round((1 - (item['discount_price'] / item['price'])) * 100)
        mess = f'<b>{item["item"]}</b>' + '\n' + \
               f'Цена {item["discount_price"]} $ ' + f'x {item["quantity"]}' \
               + f'= {item["total_amount"]} $' + f' (SALE {sale}%)'
    else:
        mess = f'<b>{item["item"]}</b>' + '\n' + \
               f'Цена {item["price"]} $ ' + f'x {item["quantity"]}' \
               + f'= {item["total_amount"]} $'
    markup = create_markup_sale(item['id'])
    bot.send_message(message.from_user.id, mess, parse_mode='html', reply_markup=markup)


@bot.message_handler(commands=['start'])
def handle_text(message):
    sticker = open('stickers/ok.tgs', 'rb')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    categories = types.KeyboardButton('Категории 🗂')
    items = types.KeyboardButton('Все товары 👕')
    cart = types.KeyboardButton('Корзина 🗑')
    markup.add(items, categories, cart)
    bot.send_message(message.from_user.id, text='Здравствуйте, вы в магазине ECOMMERCE', reply_markup=markup)
    bot.send_sticker(message.from_user.id, sticker)


@bot.message_handler(commands=['login'])
def handle_text(message):
    # Инструкция по авторизации пользователю
    mess = '<b>Для авторизации вам необходимо отправить данные в следущей форме:</b>\nlogin:\nusername\npassword'
    bot.send_message(message.from_user.id, mess, parse_mode='html')


@bot.message_handler(content_types=['text'])
def handle_text(message):
    """Вывод всех категорий, всех товаров, корзиныб авторизация пользователя"""

    # Автоизация пользователя
    if message.text[:6] == 'login:':
        try:
            data = message.text[7:].split('\n')
            username = data[0]
            password = data[1]
            response = requests.post('http://127.0.0.1:8000/auth/token/login/', data={
                'username': username,
                'password': password,
            }).json()
            auth_token = response["auth_token"]

            f = open('auth_token.txt', 'w')
            f.write(auth_token)
            f.close()

            sticker = open('stickers/Welcome.tgs', 'rb')
            mess = f'Выполнен вход под логином <b>{username}</b>'
            bot.send_message(message.from_user.id, mess, parse_mode='html')
            mess = 'Welcome to the club, buddy!'
            bot.send_message(message.from_user.id, mess, parse_mode='html')
            bot.send_sticker(message.from_user.id, sticker)
        except:
            mess = f'Ошибка! Что-то пошло не так...'
            bot.send_message(message.from_user.id, mess, parse_mode='html')
            sticker = open('stickers/fuck.tgs', 'rb')
            bot.send_sticker(message.from_user.id, sticker)

    # Вывод всех категорий
    if message.text == 'Категории 🗂' or message.text == 'категории':
        categories = get_data('category')
        mess = ''
        for category in categories:
            mess += f'{category["id"]}' + ') ' + f'<b>{category["title"]}</b>' + ' ' + f'(товаров - {category["items_count"]})' \
                    + '\n'
        mess += '\n'
        mess += '📩Отправте сообщение категории с ее номером для просмотра товаров, например "категория 1"'
        bot.send_message(message.from_user.id, mess, parse_mode='html')

    # Вывод товаров выбранной категории
    if message.text[0:9] == 'категория' or message.text[0:9] == 'Категория':
        try:
            category = get_data(f'category/{message.text[10:]}')
            bot.send_message(message.from_user.id, f'Товары категории {category["title"]}: \n', parse_mode='html')
            for item in category['category_items']:
                get_item(item, message)
        except:
            sticker = open('stickers/incorrect_cat.webp', 'rb')
            bot.send_message(message.from_user.id, 'Введите корректный номер категории', parse_mode='html')
            bot.send_sticker(message.from_user.id, sticker)

    # Вывод всех товаров
    if message.text == 'Все товары 👕':
        items = get_data('items')
        for item in items:
            get_item(item, message)

    # Вывод списка товаров в корзине
    if message.text == 'Корзина 🗑':
        token = get_token()
        data = requests.get('http://127.0.0.1:8000/api/v1/order/', headers={
                'Authorization': f'Token {token}',
            }).json()
        bot.send_message(message.from_user.id, 'Список ваших товаров:', parse_mode='html')
        for item in data[0]['items']:
            items_for_cart(message=message, item=item)
        bot.send_message(message.from_user.id,
                         f'Общая сумма вашего заказа: <b>{data[0]["total_order_amount"]} $</b>',
                         parse_mode='html')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    """ Handling messages from inline keyboard (add to cart, delete from cart)"""

    if call.message:

    # Увелечение количчества товара в корзине
        if call.data[0] == '+':
            id = call.data[1:]
            url = config.url + f'order/{id}/'
            token = get_token()
            response = requests.post(url, headers={'Authorization': f'Token {token}'})
            bot.send_message(call.message.chat.id, 'Товар был добавлен в корзину ✅')

    # Уменьшение количества товара в корзине
        if call.data[0] == '-':
            id = call.data[1:]
            url = config.url + f'order/{id}/'
            token = get_token()
            response = requests.delete(url, headers={'Authorization': f'Token {token}'})
            bot.send_message(call.message.chat.id, 'Товар был удален из корзины ❌')

    # Вывод подробной информации о товаре
        if call.data[0] == 'd':
            id = call.data[1:]
            url = f'items/{id}/'
            item = get_data(url)
            mess = item_detail(item)
            img = load_photo(item['image'])
            markup = types.InlineKeyboardMarkup(row_width=1)
            add_to_cart = types.InlineKeyboardButton('В корзину ✅', callback_data=f'+{item["id"]}')
            markup.add(add_to_cart)
            bot.send_photo(call.message.chat.id, img, caption=mess, parse_mode='html', reply_markup=markup)

bot.polling(none_stop=True)