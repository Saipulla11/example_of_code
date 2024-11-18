import requests
import time
import os
from dotenv import load_dotenv, set_key
import json, subprocess, sys, logging

#FINAL_VERSION
# URL вебхуков Bitrix24
webhook_url_channels = 'https://brezhnevstroy.bitrix24.ru/rest/1331/4fvucrk5852qxtt6/imopenlines.config.list.get.json'
webhook_url_sessions = 'https://brezhnevstroy.bitrix24.ru/rest/1331/4fvucrk5852qxtt6/imopenlines.session.history.get.json'
webhook_url_start_session = 'https://brezhnevstroy.bitrix24.ru/rest/1331/4fvucrk5852qxtt6/imopenlines.session.start.json'
webhook_url_open_session = 'https://brezhnevstroy.bitrix24.ru/rest/1331/4fvucrk5852qxtt6/imopenlines.session.open.json'
webhook_url_imbot_register = 'https://brezhnevstroy.bitrix24.ru/rest/1335/1lchoivntqodyk6w/imbot.register.json'

bot_id = '1467'


def get_tokens():
    load_dotenv("dotenv.env")
    refresh_token = os.getenv('REFRESH_AUTH_ID')
    response = requests.post(f'https://oauth.bitrix.info/oauth/token/'
                             f'?grant_type=refresh_token&'
                             f'client_id=local.669cb98d928e39.82404039&'
                             f'client_secret=hQeUvZInLw5nD9dhhcqYZ2QDLi0pMb8G9OERZWNaLTWJhdOfnr&'
                             f'refresh_token={refresh_token}')

    if response.status_code == 200:
        json_data = response.json()
        auth = json_data['access_token']
        refr = json_data['refresh_token']
        set_key('dotenv.env', 'REFRESH_AUTH_ID', refr)
        set_key('dotenv.env', 'AUTH_ID', auth)
        return auth
    else:
        print(response)


def transfer_to_operator(user_id):
    transfer = 'https://brezhnevstroy.bitrix24.ru/rest/1335/eedxcp3inen9sauk/imopenlines.operator.transfer'
    params = {
        "CHAT_ID": user_id,
        "TRANSFER_ID": 283,
    }
    response = requests.post(transfer, json=params)
    print(response.json())


def send_message(auth_token, bot_id, dialog_id, message):
    url = 'https://brezhnevstroy.bitrix24.ru/rest/1335/bhy44zfcpll7805x/im.message.add'
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'BOT_ID': bot_id,  # Идентификатор чат-бота
        'DIALOG_ID': dialog_id,  # Идентификатор диалога (например, chatXX или USER_ID)
        'MESSAGE': message,  # Текст сообщения
        'ATTACH': '',  # Вложение, необязательное поле
        'KEYBOARD': '',  # Клавиатура, необязательное поле
        'MENU': '',  # Контекстное меню, необязательное поле
        'SYSTEM': 'N',  # Отображать сообщения в виде системного сообщения
        'URL_PREVIEW': 'Y'  # Преобразовывать ссылки в rich-ссылки
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print('Message sent successfully:', response.json())
        logging.basicConfig(
            filename='logs.log',  # Указываем имя файла, куда будут записываться логи
            filemode='a',  # Режим записи: 'a' - добавлять в конец файла, 'w' - перезаписывать файл
            format='%(asctime)s - %(levelname)s - %(message)s',  # Формат записи логов
            level=logging.INFO  # Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        )
        logging.info(f'Отправлено письмо {dialog_id}: {message}')
        transfer_to_operator(dialog_id[4:])
    elif response.status_code == 401:
        print('REFRESHING TOKENS...')
        refr = get_tokens()
        send_message(refr, bot_id, dialog_id, message)
    else:
        print('Failed to send message:', response.status_code, response.json())


print('hello')
while True:
    python_executable = sys.executable
    subprocess.run([python_executable, "connector.py"])
    time.sleep(5)
    subprocess.run([python_executable, "Construction_gpt.py"])
    time.sleep(5)
    with open('new.json', 'r') as f:
        new_results = json.load(f)['new']
    if new_results == {}:
        print('no messages found')
        time.sleep(10)
        continue
    try:
        auth_id = os.getenv('AUTH_ID')
        for key in new_results.keys():
            dialog_id = 'chat' + key
            for message in new_results[key]:
                send_message(auth_id, bot_id, dialog_id, message)

        time.sleep(10)

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        time.sleep(20)
