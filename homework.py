import logging
import os
import time
from datetime import timedelta
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

DAYS_CHECK = 10
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': PRACTICUM_TOKEN}

UPDATE_INTERVAL = 60 * 10

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
old_request_data = {}


def check_tokens() -> bool:
    """Проверка наличия значений необходимых токенов и ID чат-бота."""
    status = True
    if not PRACTICUM_TOKEN:
        logger.critical(
            'Отсутствует необходимая переменная PRACTICUM_TOKEN.',
            'Работа программы не возможна!')
        status = False
    if not TELEGRAM_TOKEN:
        logger.critical(
            'Отсутствует необходимая переменная TELEGRAM_TOKEN.',
            'Работа программы не возможна!')
        status = False
    if not TELEGRAM_CHAT_ID:
        logger.critical(
            'Отсутствует необходимая переменная TELEGRAM_CHAT_ID.',
            'Работа программы не возможна!')
        status = False
    return status


def send_message(bot: telegram.bot, message: str) -> None:
    """Отправка сообщения через бота."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение: {message} отправлено')
    except Exception as error:
        logger.error(f'Сообщение: {message} не отправлено. Ошибка {error}')


def get_api_answer(timestamp: int) -> dict:
    """Обращение к API практикума для получения статусов работ."""
    payload = {'from_date': timestamp}
    try:
        rec = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        logger.error(f"Ошибка обращения к API: {error}")

    if rec.status_code != 200:
        logger.error(f"Ошибка обращения к API: Статус {rec.status_code}")
        raise requests.RequestException()
    return rec.json()


def check_response(response: dict) -> None:
    """Проверка ответа от API на допустимость данных."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        logger.error("В ответе API отсутствует элемент homeworks!")
    if type(homeworks) != list:
        logger.error('В ответе API элемент homeworks не является списком!')
        raise TypeError('В ответе API элемент homeworks не является списком!')


def parse_status(homework: dict) -> str:
    """Проверка статуса домашней работы."""
    global old_request_data

    try:
        homework_name = homework['homework_name']
    except KeyError:
        logger.error('Отсутствует ключ homework_name')
    try:
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        logger.error('Отсутствует или недокументированный ',
                     f'статус домашнего задания {homework_name}')
    if old_request_data.get(homework_name) != verdict:
        old_request_data[homework_name] = verdict
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        return ""


def create_logger(logger: logging.Logger) -> logging.Logger:
    """Создает 2 типа логгеров: в стандартный вывод и в файл.
    Уровень логгирования DEBUG.
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        'bot.log', maxBytes=1000000, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)
    return logger


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical("Установлены не все необходимые переменные!")
        exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time() - timedelta(days=DAYS_CHECK).total_seconds())
    send_message(
        bot=bot,
        message=f'Бот запущен, проверяем за последние {DAYS_CHECK} дней')
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if len(response['homeworks']) != 0:
                logger.info('Найдены домашние работы')
                for homework in response['homeworks']:
                    result = parse_status(homework)
                    if len(result) != 0:
                        send_message(bot, result)
            else:
                logger.info('Домашних работ не найдено!')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot=bot, message=message)

        time.sleep(UPDATE_INTERVAL)


if __name__ == '__main__':
    logger = create_logger(logger=logger)
    main()
