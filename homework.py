import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 30
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
        try:
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
            )
        except Exception as error:
            logging.error(
                f'Ошибка при отправке сообщения:\n {error}',
                exc_info=True
            )
        else:
            logging.info('Удачная отправка сообщения.')


def get_api_answer(current_timestamp: int) -> dict:
    """Запрос и получение данных с сервера."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(
            f'При запросе к ENDPOINT возникла ошибка:\n {error}',
            exc_info=True
        )
    if response.status_code != HTTPStatus.OK.value:
        logging.error(
            f'ENDPOINT вернул ошибку. Код ответа: {response.status_code}'
        )
        raise
    return response.json()


def check_response(response: dict) -> list:
    """Проверка корректности полученных данных."""
    if response:
        if type(response['homeworks']) == list:
            if not response['homeworks']:
                logging.debug('В ответе нет новых статусов.')
            return response['homeworks']
    logging.error(
        'Отсутствуют ожидаемые ключи в ответе API.',
        exc_info=True
    )
    raise


def parse_status(homework) -> str:
    """Определение статуса домашней работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_STATUSES.keys():
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logging.error('Недокументированный статус работы.')
    raise


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
    env = check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    hw_statuses = {}
    sent_msg = ''
    if env:
        while True:
            try:
                current_timestamp = int(time.time())
                response = get_api_answer(current_timestamp - 3600 * 24 * 14)
                homeworks = check_response(response)
            except Exception as error:
                message = f'Сбой в работе программы:\n {error}'
                logging.error(message, exc_info=True)
                if message != sent_msg:
                    send_message(bot, message)
                    sent_msg = message
                time.sleep(RETRY_TIME)
            else:
                for hw in homeworks:
                    hw_name = hw['homework_name']
                    status = hw['status']
                    if hw_name not in hw_statuses.keys():
                        hw_statuses[hw_name] = status
                        message = parse_status(hw)
                        send_message(bot, message)
                    elif status != hw_statuses[hw_name]:
                        hw_statuses[hw_name] = status
                        message = parse_status(hw)
                        send_message(bot, message)
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
