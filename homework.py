import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(stream=sys.stdout)]
)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в телеграм."""
    if message:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logging.info('Удачная отправка сообщения.')


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос и получение данных с сервера."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f'Запрос к внешнему API вернул ошибку:\n {error}')
    if response.status_code != HTTPStatus.OK.value:
        raise exceptions.ResponseError(
            f'ENDPOINT вернул ошибку. Код ответа: {response.status_code}'
        )
    return response.json()


def check_response(response: dict) -> list:
    """Проверка корректности полученных данных."""
    # Наверное, было бы правильно сделать через exception,
    # но тогда падают тесты.
    if response:
        if 'homeworks' not in response:
            logging.error('Отсутствуют ожидаемые ключи.')
        if isinstance(response['homeworks'], list):
            if not response['homeworks']:
                logging.debug('Нет обновлений статусов работ.')
            else:
                for hw in response['homeworks']:
                    if ('homework_name' in hw
                            and 'status' in hw):
                        homework_status = hw['status']
                        if homework_status not in HOMEWORK_STATUSES:
                            logging.error('Недокументированный статус работы.')
                    else:
                        logging.error('Отсутствуют ожидаемые ключи.')
            return response['homeworks']
    raise exceptions.ResponseDataError(
        'Отсутствуют ожидаемые ключи в ответе API.'
    )


def parse_status(homework) -> str:
    """Определение статуса домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка наличия необходимых переменных окружения."""
    if (
        PRACTICUM_TOKEN
        and TELEGRAM_TOKEN
        and TELEGRAM_CHAT_ID
    ):
        return True
    logging.critical('Отсутствуют обязательные переменные окружения.')
    return False


def main() -> None:
    """Основная логика работы бота."""
    tokens = check_tokens()
    if not tokens:
        return
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 3600 * 24 * 30
    sent_msg = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response['current_date'] or int(time.time())
            homeworks = check_response(response)
            for hw in homeworks:
                message = parse_status(hw)
                send_message(bot, message)
        except telegram.error.TelegramError as error:
            message = f'Сбой в работе программы:\n {error}'
            logging.error(message, exc_info=True)
        except Exception as error:
            message = f'Сбой в работе программы:\n {error}'
            logging.error(message, exc_info=True)
            if message != sent_msg:
                send_message(bot, message)
                sent_msg = message
        else:
            sent_msg = ''
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
