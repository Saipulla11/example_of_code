import requests
import datetime
import json
import logging
from dotenv import set_key

# Ваши данные
url_get = "https://brezhnevstroy.bitrix24.ru/rest/1335/u4yiuycnya9tz1vd/im.dialog.messages.get"
url_read = 'https://brezhnevstroy.bitrix24.ru/rest/1335/oxf8f45x69vl8n6d/im.dialog.read'
url_chats = 'https://brezhnevstroy.bitrix24.ru/rest/1335/al1ynyiuk44v86of/im.recent.get'
webhook_url_start_session = 'https://brezhnevstroy.bitrix24.ru/rest/1335/v64nm1vza5q90lv1/imopenlines.session.join'

# Параметры запроса
results = {}


def start_new(chat_id):
    """Функция для начала новой сессии."""
    web = 'https://brezhnevstroy.bitrix24.ru/rest/1335/afwe8nvr40xagil1/imopenlines.operator.answer'
    params = {
        'CHAT_ID': chat_id
    }

    response = requests.post(web, json=params)
    return response.status_code  # 400 - ошибка, 200 - успех


def log_message(message):
    """Функция для логирования сообщений."""
    logging.basicConfig(
        filename='logs.log',  # Указываем имя файла, куда будут записываться логи
        filemode='a',  # Режим записи: 'a' - добавлять в конец файла, 'w' - перезаписывать файл
        format='%(asctime)s - %(levelname)s - %(message)s',  # Формат записи логов
        level=logging.INFO  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    )
    logging.info(f"{message.get('chat_id')}: {message.get('text')}")

    chat_id = message.get('chat_id')
    text = message.get('text')
    if chat_id in results:
        results[chat_id].append(text)
    else:
        results[chat_id] = [text]


def get_message(dialog_id):
    """Получение сообщений из диалога по ID."""
    params = {
        "DIALOG_ID": dialog_id,  # Замените на ID вашего чата
        "LIMIT": 50,  # Количество сообщений для получения
        "OFFSET": 0  # Смещение от начала списка сообщений
    }

    # Выполнение запроса для получения сообщений
    response = requests.post(url_get, json=params)

    if response.status_code == 200:
        try:
            messages = response.json().get('result', {}).get('messages', [])
        except (ValueError, KeyError) as e:
            print(f"Ошибка при парсинге JSON или доступе к данным: {e}")
            messages = []

        try:
            # Преобразуем dialog_id в строку и берем срез с четвертого символа
            response_status = start_new(str(dialog_id)[4:])

            if response_status == 400:
                for message in messages:
                    if message.get('author_id') == 283:
                        try:
                            results.pop(message.get('chat_id'))
                        except KeyError:
                            pass
                        break
                    if message.get('unread'):
                        if message.get('author_id') == 283:
                            try:
                                results.pop(message.get('chat_id'))
                            except KeyError:
                                pass
                            break
                        elif message.get('author_id') in [1335, 0]:
                            continue
                        else:
                            log_message(message)
            else:
                for message in messages:
                    if message.get('text') == 'Обращение направлено на [USER=1335 REPLACE], БрежневСтрой[/USER]':
                        break
                    elif message.get('author_id') in [1335, 0]:
                        continue
                    else:
                        log_message(message)

        except Exception as e:
            print(f"Произошла ошибка: {e}")
    else:
        print(f"Запрос не выполнен успешно. Код ошибки: {response.status_code}")


def get_all_chats():
    """Получение списка всех чатов."""
    response = requests.post(url_chats)
    if response.status_code == 200:
        return response.json().get('result', [])
    else:
        print('Failed to retrieve chat list:', response.status_code, response.text)
        return []


# Основной процесс
ids = get_all_chats()
for id in ids:
    if id['id'] == 1467 or id['id'] == 9 or id['id'] == 237 or id['id'] == 'chat1':
        continue
    else:
        get_message(id['id'])
        mark_as_read_params = {
            "DIALOG_ID": id['id']
        }
        read_response = requests.post(url_read, json=mark_as_read_params)

# Сохранение результатов в файл
with open('data.json', 'w') as f:
    json.dump({"variable": results}, f)

print(results)
