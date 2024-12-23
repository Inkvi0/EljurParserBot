import asyncio
import datetime
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from main import (
    get_schedule_for_today, get_schedule_for_tomorrow,
    get_schedule_for_day, get_next_class_info, schedule_cache)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ELJUR_USERNAME = os.getenv('ELJUR_USERNAME', '')
ELJUR_PASSWORD = os.getenv('ELJUR_PASSWORD', '')
ELJUR_GROUP = os.getenv('ELJUR_GROUP', '')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()


months = {
    1: 'января',   2: 'февраля', 3: 'марта',     4: 'апреля',
    5: 'мая',      6: 'июня',    7: 'июля',      8: 'августа',
    9: 'сентября', 10: 'октября',11: 'ноября',   12: 'декабря'
}
day_mapping = {
    'Monday': 'Понедельник',
    'Tuesday': 'Вторник',
    'Wednesday': 'Среда',
    'Thursday': 'Четверг',
    'Friday': 'Пятница',
    'Saturday': 'Суббота'
}


def main_keyboard() -> InlineKeyboardBuilder:
    """
    Главное меню (inline-кнопки).
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Расписание на сегодня",
            callback_data="schedule_for_today"
        ),
        types.InlineKeyboardButton(
            text="Расписание на завтра",
            callback_data="get_schedule_tomorrow"
        ),
        types.InlineKeyboardButton(
            text="Следующая пара",
            callback_data="next_class"
        ),
        types.InlineKeyboardButton(
            text="Расписание на другой день",
            callback_data="select_day_schedule"
        ),
    )
    builder.adjust(1)
    return builder


def day_keyboard() -> InlineKeyboardBuilder:
    """
    Клавиатура для выбора дня недели.
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Понедельник",
            callback_data="Monday"
        ),
        types.InlineKeyboardButton(
            text="Вторник",
            callback_data="Tuesday"
        ),
        types.InlineKeyboardButton(
            text="Среда",
            callback_data="Wednesday"
        ),
        types.InlineKeyboardButton(
            text="Четверг",
            callback_data="Thursday"
        ),
        types.InlineKeyboardButton(
            text="Пятница",
            callback_data="Friday"
        ),
        types.InlineKeyboardButton(
            text="Суббота",
            callback_data="Saturday"
        ),
        types.InlineKeyboardButton(
            text="<-- Вернуться в главное меню",
            callback_data="back_menu"
        ),
    )
    builder.adjust(1)
    return builder


async def main():
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        """
        Обработчик команды /start — выводит главное меню.
        """
        kb = main_keyboard()
        await message.answer(
            "Выберите необходимую функцию:",
            reply_markup=kb.as_markup()
        )

    @dp.callback_query()
    async def handle_callbacks(callback: types.CallbackQuery):
        """
        Обработчик всех колбэков.
        """
        kb_day = day_keyboard()
        kb_main = main_keyboard()

        schedule = schedule_cache(ELJUR_USERNAME, ELJUR_PASSWORD, ELJUR_GROUP)

        if callback.data == 'get_schedule_tomorrow':
            current_datetime = datetime.datetime.now()
            current_hour = current_datetime.hour
            current_month = current_datetime.month
            tomorrow_date = current_datetime + datetime.timedelta(days=1)
            tomorrow_month = tomorrow_date.month

            choice_kb = InlineKeyboardBuilder()
            choice_kb.add(
                types.InlineKeyboardButton(
                    text=f"Расписание на {current_datetime.day} {months[current_month]}",
                    callback_data="selected_today"
                ),
                types.InlineKeyboardButton(
                    text=f"Расписание на {tomorrow_date.day} {months[tomorrow_month]}",
                    callback_data="selected_tomorrow"
                )
            )
            choice_kb.adjust(1)

            # Если сейчас до 4 утра, даём пользователю выбор —
            # показывать «сегодня» или «завтра».
            if 0 <= current_hour < 4:
                await bot.edit_message_text(
                    chat_id=callback.from_user.id,
                    message_id=callback.message.message_id,
                    text="На какой день вы хотите посмотреть расписание?",
                    reply_markup=choice_kb.as_markup()
                )
            else:
                tomorrow_schedule = get_schedule_for_tomorrow(schedule)
                await bot.edit_message_text(
                    chat_id=callback.from_user.id,
                    message_id=callback.message.message_id,
                    text=tomorrow_schedule,
                    reply_markup=kb_main.as_markup()
                )

        elif callback.data == 'selected_today':
            schedule_for_today = get_schedule_for_today(schedule)
            await bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id,
                text=schedule_for_today,
                reply_markup=kb_main.as_markup()
            )

        elif callback.data == 'selected_tomorrow':
            schedule_for_tomorrow_text = get_schedule_for_tomorrow(schedule)
            await bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id,
                text=schedule_for_tomorrow_text,
                reply_markup=kb_main.as_markup()
            )

        elif callback.data == 'schedule_for_today':
            schedule_for_today_text = get_schedule_for_today(schedule)
            await bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id,
                text=schedule_for_today_text,
                reply_markup=kb_main.as_markup()
            )

        elif callback.data == 'next_class':
            next_class_text = get_next_class_info(schedule)
            await bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id,
                text=next_class_text,
                reply_markup=kb_main.as_markup()
            )

        elif callback.data == 'select_day_schedule':
            await bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id,
                text='Выберите день недели',
                reply_markup=kb_day.as_markup()
            )

        if callback.data in day_mapping:
            schedule_for_day_text = get_schedule_for_day(schedule, day_mapping[callback.data])
            await bot.edit_message_text(

                chat_id=callback.from_user.id,

                message_id=callback.message.message_id,

                text=schedule_for_day_text,

                reply_markup=kb_main.as_markup()

            )

        elif callback.data == 'back_menu':
            await bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id,
                text='Выберите необходимую функцию',
                reply_markup=kb_main.as_markup()
            )

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
