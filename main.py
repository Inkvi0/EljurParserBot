import requests
import fake_useragent
from bs4 import BeautifulSoup
import datetime
import locale

from datetime import timedelta


CACHE_DURATION = timedelta(minutes=10)
_cached_days = None         # Здесь будем хранить парсинг
_cache_timestamp = None     # Время последнего обновления кэша


def schedule_cache(username: str, password: str, group: str = ''):
    """
    Возвращает кэш расписания.
    Если кэш устарел, парсит сайт заново.
    :param username: логин ЭлЖур
    :param password: пароль ЭлЖур
    :param group:    группа (если нужно конкретное расписание для группы)
    :return:         словарь с расписанием
    """
    global _cached_days, _cache_timestamp
    now = datetime.datetime.now()

    if _cached_days is None or _cache_timestamp is None or (now - _cache_timestamp) > CACHE_DURATION:
        _cached_days = parser(username, password, group)
        _cache_timestamp = now

    return _cached_days


def parser(username: str, password: str, group: str = '') -> dict:
    """
    Авторизуется на сайте Eljur и парсит расписание.
    """

    session = requests.session()
    link = 'https://mtkp.eljur.ru/ajaxauthorize'

    user_agent = fake_useragent.UserAgent().random
    headers = {'user-agent': user_agent}

    data = {
        'username': username,
        'password': password,
        'return_uri': ''
    }

    # Авторизация
    response_auth = session.post(link, data=data, headers=headers)
    if response_auth.status_code != 200:
        return {}

    if group:
        raspisanie_link = f'https://mtkp.eljur.ru/journal-schedule-action/class.{group}'
    else:
        raspisanie_link = 'https://mtkp.eljur.ru/journal-schedule-action/'

    # Получаем страницу с расписанием
    response = session.get(raspisanie_link, headers=headers)
    if response.status_code != 200:
        return {}

    page = BeautifulSoup(response.text, 'html.parser')
    all_days = page.findAll(class_='schedule__day__content')

    days = {}
    for day in all_days:
        day_name = day.find(class_='schedule__day__content__header').text.strip()
        days[day_name] = []
        for para in day.findAll(class_='schedule__day__content__lesson--main'):
            if "schedule__day__content__lesson--inactive" not in para.get('class', []):
                lesson = {}
                lesson['paraTime'] = para.findNext(class_='schedule__day__content__lesson__time').text.strip()
                lesson['paraNum'] = para.findNext(class_='schedule__day__content__lesson__num').text.strip()
                lesson['paraName'] = para.findNext(class_='schedule-lesson').text.strip()
                lesson['paraTeacher'] = para.findNext(class_='schedule-teacher').text.strip()
                lesson['paraRoom'] = para.findNext(class_='schedule__day__content__lesson__room').text.strip()
                days[day_name].append(lesson)

    return days


def get_schedule_for_day(days: dict, day_input: str) -> str:
    """
    Возвращает текст расписания на конкретный день недели.
    :param days       словарь с расписанием (ключ — день недели, значение — список пар)
    :param day_input  день недели, например 'Понедельник'
    :return           текстовое представление расписания
    """

    day_input = str(day_input).capitalize()
    day_schedule = days.get(day_input, [])
    if day_schedule:
        if day_input in ('Суббота', 'Среда', 'Пятница'):
            schedule_info = f"Расписание на {day_input[0:-1].lower()}у:\n"
        else:
            schedule_info = f"Расписание на {day_input.lower()}:\n"

        for para in day_schedule:
            schedule_info += (
                f"{para['paraNum']} пара: {para['paraName']}\n"
                f"Время: {para['paraTime']}\n"
                f"Преподаватель: {para['paraTeacher']}\n"
                f"Кабинет: {para['paraRoom']}\n\n"
            )
        return schedule_info
    else:
        if day_input in ('Суббота', 'Среда', 'Пятница'):
            return f"На {day_input[0:-1]}у нет расписания."
        else:
            return f"На {day_input} нет расписания."


def get_next_class_info(days: dict) -> str:
    """
    Возвращает информацию о ближайшей (следующей) паре на сегодня.
    :param days: словарь с расписанием
    :return:     текст с описанием следующей пары или 'Сегодня нет занятий' / 'На сегодня больше нет пар'
    """
    try:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    except locale.Error:
        pass

    current_time = datetime.datetime.now()
    current_weekday = current_time.strftime("%A").capitalize()
    current_hour = current_time.hour
    current_minute = current_time.minute

    if current_weekday in days:
        day_schedule = days[current_weekday]

        for para in day_schedule:
            # Разбираем время пары вида "10:00-10:45"
            time_range = para['paraTime']
            time_range = time_range.replace("–", "-")
            try:
                start_str, end_str = time_range.split('-')
                start_str = start_str.strip()
                end_str = end_str.strip()

                start_hour, start_minute = map(int, start_str.split(':'))


                if (current_hour < start_hour) or (current_hour == start_hour and current_minute < start_minute):
                    return (
                        f"Следующая пара: {para['paraNum']} \n"
                        f"Дисциплина: {para['paraName']}\n"
                        f"Начало в {para['paraTime']}\n"
                        f"Аудитория: {para['paraRoom']}\n"
                    )
            except ValueError:
                return "Ошибка в формате времени пары."

        return "На сегодня больше нет пар."
    else:
        return "Сегодня нет занятий."


def get_schedule_for_tomorrow(days: dict) -> str:
    """
    Возвращает расписание на завтрашний день.
    :param days: словарь с расписанием
    :return:     текстовое представление расписания
    """
    try:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    except locale.Error:
        pass

    current_date = datetime.datetime.now()
    tomorrow_date = current_date + datetime.timedelta(days=1)
    tomorrow_weekday = tomorrow_date.strftime("%A").capitalize()

    if tomorrow_weekday in days:
        schedule_info = f"Расписание на завтра ({tomorrow_weekday}):\n"
        day_schedule = days[tomorrow_weekday]
        for para in day_schedule:
            schedule_info += (
                f"{para['paraNum']} пара: {para['paraName']}\n"
                f"Время: {para['paraTime']}\n"
                f"Преподаватель: {para['paraTeacher']}\n"
                f"Кабинет: {para['paraRoom']}\n\n"
            )
    else:
        schedule_info = f"На завтра ({tomorrow_weekday}) нет расписания."

    return schedule_info


def get_schedule_for_today(days: dict) -> str:
    """
    Возвращает расписание на сегодня.
    :param days: словарь с расписанием
    :return:     текстовое представление расписания
    """
    try:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    except locale.Error:
        pass

    current_weekday = datetime.datetime.now().strftime("%A").capitalize()

    if current_weekday in days:
        schedule_info = f"Расписание на сегодня ({current_weekday}):\n"
        day_schedule = days[current_weekday]
        for para in day_schedule:
            schedule_info += (
                f"{para['paraNum']} пара: {para['paraName']}\n"
                f"Время: {para['paraTime']}\n"
                f"Преподаватель: {para['paraTeacher']}\n"
                f"Кабинет: {para['paraRoom']}\n\n"
            )
    else:
        schedule_info = f"На сегодня ({current_weekday}) нет расписания."

    return schedule_info
