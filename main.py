import requests
import fake_useragent
from bs4 import BeautifulSoup
import datetime
import locale
from dotenv import load_dotenv
import os

load_dotenv()

ELJUR_USERNAME = os.getenv('ELJUR_USERNAME')
ELJUR_PASSWORD = os.getenv('ELJUR_PASSWORD')


def parser(username=ELJUR_USERNAME, password=ELJUR_PASSWORD, group=''):
    session = requests.session()
    link = 'https://mtkp.eljur.ru/ajaxauthorize'

    user = fake_useragent.UserAgent().random
    header = {
        'user-agent': user
    }

    data = {
        'username': username,
        'password': password,
        'return_uri': ''
    }
    # Авторизация
    response = session.post(link, data=data, headers=header).text
    if group != '':
        raspisanie_link = f'https://mtkp.eljur.ru/journal-schedule-action/class.{group}'
    else:
        raspisanie_link = 'https://mtkp.eljur.ru/journal-schedule-action/'

    # Парсим расписание

    response = session.get(raspisanie_link, headers=header)  # Получаем ответ
    page = BeautifulSoup(response.text, 'html.parser')

    all_days = page.findAll(class_='schedule__day__content')

    days = dict()
    for day in all_days:
        day_name = day.find(class_='schedule__day__content__header').text.strip()
        days[day_name] = []
        for para in day.findAll(class_='schedule__day__content__lesson--main'):
            # Проверяем, что урок не является неактивным
            if "schedule__day__content__lesson--inactive" not in para.get('class', []):
                lesson = dict()
                lesson['paraTime'] = para.findNext(class_='schedule__day__content__lesson__time').text.strip()
                lesson['paraNum'] = para.findNext(class_='schedule__day__content__lesson__num').text.strip()
                lesson['paraName'] = para.findNext(class_='schedule-lesson').text.strip()
                lesson['paraTeacher'] = para.findNext(class_='schedule-teacher').text.strip()
                lesson['paraRoom'] = para.findNext(class_='schedule__day__content__lesson__room').text.strip()
                days[day_name].append(lesson)
    return days


def get_schedule_for_day(days, day_input):
    """Прнимает массив данных с парсера и день недели"""
    day_input = str(day_input).capitalize()
    day_schedule = days.get(day_input, [])
    if day_schedule:
        if day_input in ('Суббота', 'Среда', 'Пятница'):
            schedule_info = f"Расписание на {day_input[0:-1].lower()}у:\n"
        else:
            schedule_info = f"Расписание на {day_input.lower()}:\n"

        for para in day_schedule:
            schedule_info += f"{para['paraNum']} пара: {para['paraName']}\nВремя: {para['paraTime']}\nПреподаватель: {para['paraTeacher']}\nКабинет: {para['paraRoom']}\n\n"
        return schedule_info
    else:
        if day_input in ('Суббота', 'Среда', 'Пятница'):
            return f"На {day_input[0:-1]}у нет расписания."
        else:
            return f"На {day_input} нет расписания."


def get_info(day_input: str, para_num: str, days):
    day_input = str(day_input)
    para_num = str(para_num)
    try:
        day_schedule = days.get(day_input, [])

        if day_schedule:
            para_found = False
            for para in day_schedule:
                if para['paraNum'] == para_num:
                    para_found = True
                    info = f"Информация о {para['paraNum']}-ой паре в {day_input.lower()}:\n"
                    info += f"Время: {para['paraTime']}\n"
                    info += f"Название предмета: {para['paraName']}\n"
                    info += f"Преподаватель: {para['paraTeacher']}\n"
                    info += f"Аудитория: {para['paraRoom']}\n"
                    return info
            if not para_found:
                if day_input == 'Вторник':
                    return f"Во {day_input.lower()} нет пары с номером {para_num}."
                elif day_input in ('Среда', 'Пятница', 'Суббота'):
                    return f"В {day_input.lower()[0:-1]}у нет пары с номером {para_num}."
                else:
                    return f"В {day_input.lower()} нет пары с номером {para_num}."
        else:
            if day_input in ('Суббота', 'Среда', 'Пятница'):
                return f"На {day_input.lower()[0:-1]}у нет расписания."
    except Exception:
        return 'Вы дурак, передайте день и номер пары через пробел'


def get_next_class_info(days):
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    # Получаем текущее время и день недели
    current_time = datetime.datetime.now()
    current_weekday = current_time.strftime("%A").capitalize()
    current_hour = current_time.hour
    current_minute = current_time.minute

    # Определяем следующую пару
    next_class_info = ""
    if current_weekday in days:
        day_schedule = days[current_weekday]
        for para in day_schedule:
            para_num = int(para['paraNum'])
            para_time_start = int(para['paraTime'].split(':')[0])
            para_time_end = (para['paraTime'].split(':')[1].split('-')[0])

            # Проверяем, прошла ли уже пара
            if current_hour < para_time_start or (current_hour == para_time_start and current_minute < 30):
                next_class_info += f"Следующая пара: {para['paraNum']}-я\nДисциплина :{para['paraName']}\nНачало в {para['paraTime']}\nАудитория: {para['paraRoom']}\n"
                break
        if not next_class_info:
            next_class_info = "На сегодня больше нет пар."
    else:
        next_class_info = "Сегодня нет занятий."

    return next_class_info


def get_schedule_for_tomorrow(days):
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    current_date = datetime.datetime.now()
    tomorrow_date = current_date + datetime.timedelta(days=1)
    tomorrow_weekday = tomorrow_date.strftime("%A").capitalize()

    # Получаем расписание на завтра
    schedule_info = ""
    if tomorrow_weekday in days:
        schedule_info += f"Расписание на завтра ({tomorrow_date.strftime('%A').capitalize()}):\n"
        day_schedule = days[tomorrow_weekday]
        for para in day_schedule:
            schedule_info += f"{para['paraNum']} пара: {para['paraName']}\nВремя: {para['paraTime']}\nПреподаватель: {para['paraTeacher']}\nКабинет: {para['paraRoom']}\n\n"
    else:
        schedule_info = f"На завтра ({tomorrow_date.strftime('%A').capitalize()}) нет расписания."

    return schedule_info


def get_schedule_for_today(days):
    # Устанавливаем русскую локаль
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    # Получаем текущую дату
    current_date = datetime.datetime.now().strftime("%A").capitalize()

    # Получаем расписание на завтра
    schedule_info = ""
    if current_date in days:
        schedule_info += f"Расписание на сегодня ({current_date}):\n"
        day_schedule = days[current_date]
        for para in day_schedule:
            schedule_info += f"{para['paraNum']} пара: {para['paraName']}\nВремя: {para['paraTime']}\nПреподаватель: {para['paraTeacher']}\nКабинет: {para['paraRoom']}\n\n"
    else:
        schedule_info = f"На сегодня ({current_date.capitalize()}) нет расписания."

    return schedule_info
