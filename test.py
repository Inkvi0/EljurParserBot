import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from main import *
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
logging.basicConfig(level=logging.INFO)


bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

mounths = {1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
           9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'}


def osn_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Расписание на сегодня",
        callback_data="schedule_for_today"),
        types.InlineKeyboardButton(
            text="Расписание на завтра",
            callback_data="get_schedule_tomorrow"),
        types.InlineKeyboardButton(
            text="Следующая пара",
            callback_data="next_class"),
        types.InlineKeyboardButton(
            text="Расписание на другой день",
            callback_data="select_day_schdeule"),
    )
    builder.adjust(1)
    return builder


def day_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Понедельник",
        callback_data="Monday"),
        types.InlineKeyboardButton(
            text="Вторник",
            callback_data="Tuesday"),
        types.InlineKeyboardButton(
            text="Среда",
            callback_data="Wednesday"),
        types.InlineKeyboardButton(
            text="Четверг",
            callback_data="Thursday"),
        types.InlineKeyboardButton(
            text="Пятница",
            callback_data="Friday"),
        types.InlineKeyboardButton(
            text="Суббота",
            callback_data="Saturday"),
        types.InlineKeyboardButton(
            text="<-- Вернуться в главное меню",
            callback_data="back_menu"),
    )
    builder.adjust(1)
    return builder


async def main():
    @dp.message(Command("start"))
    async def cmd_random(message: types.Message):
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
                text="Расписание на сегодня",
                callback_data="schedule_for_today"),
            types.InlineKeyboardButton(
            text="Расписание на завтра",
            callback_data="get_schedule_tomorrow"),
            types.InlineKeyboardButton(
                text="Следующая пара",
                callback_data="next_class"),
            types.InlineKeyboardButton(
                text="Расписание на другой день",
                callback_data="select_day_schdeule"),
        )
        builder.adjust(1)
        await message.answer(
            "Выберете необходимую функцию",
            reply_markup=builder.as_markup()

        )

    @dp.callback_query()
    async def send_tomorrow_schedule(callback: types.CallbackQuery):
        keyboard1 = day_keyboard()
        main_keyboard = osn_keyboard()

        if callback.data == 'get_schedule_tomorrow':
            current_datetime = datetime.datetime.now()
            current_hour = current_datetime.hour
            current_mounth = current_datetime.month

            tomorrow_date = current_datetime + datetime.timedelta(days=1)
            tomorrow_mounth = tomorrow_date.month

            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text=f"Расписание на {current_datetime.day} {mounths[current_mounth]}",
                callback_data="selected_today"),
                types.InlineKeyboardButton(
                    text=f"Расписание на {tomorrow_date.day} {mounths[tomorrow_mounth]}",
                    callback_data="selected_tomorrow")
            )
            builder.adjust(1)
            if current_hour in range(0, 4):
                await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                            text=f'На какой конкретно день вы хотите посмотреть расписание?',
                                            reply_markup=builder.as_markup())
            else:
                schedule = parser()
                # Получаем расписание на завтра
                tomorrow_schedule = get_schedule_for_tomorrow(schedule)
                # Отправляем информацию пользователю
                keyboard1 = osn_keyboard()
                await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                            text=tomorrow_schedule, reply_markup=keyboard1.as_markup())

        elif callback.data == 'selected_today':
            schedule = parser()
            # Получаем расписание на сегодня
            schedule_for_today = get_schedule_for_today(schedule)
            # Отправляем информацию пользователю
            keyboard1 = osn_keyboard()
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_today, reply_markup=keyboard1.as_markup())

        elif callback.data == 'selected_tomorrow':
            schedule = parser()
            # Получаем расписание на завтра
            schedule_for_today = get_schedule_for_tomorrow(schedule)
            # Отправляем информацию пользователю
            keyboard1 = osn_keyboard()
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_today, reply_markup=keyboard1.as_markup())

        elif callback.data == 'schedule_for_today':
            schedule = parser()
            # Получаем расписание на завтра
            schedule_for_today = get_schedule_for_today(schedule)
            # Отправляем информацию пользователю
            keyboard1 = osn_keyboard()
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_today, reply_markup=keyboard1.as_markup())

        elif callback.data == 'next_class':
            schedule = parser()
            # Получаем расписание на завтра
            next_class = get_next_class_info(schedule)
            # Отправляем информацию пользователю
            keyboard1 = osn_keyboard()
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=next_class, reply_markup=keyboard1.as_markup())

        elif callback.data == 'select_day_schdeule':
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text='Выберите день недели', reply_markup=keyboard1.as_markup())
        if callback.data == 'Monday':
            schedule = parser()
            schedule_for_day = get_schedule_for_day(schedule, 'Понедельник')
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_day, reply_markup=main_keyboard.as_markup())
        elif callback.data == 'Tuesday':
            schedule = parser()
            schedule_for_day = get_schedule_for_day(schedule, 'Вторник')
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_day, reply_markup=main_keyboard.as_markup())
        elif callback.data == 'Wednesday':
            schedule = parser()
            schedule_for_day = get_schedule_for_day(schedule, 'Среда')
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_day, reply_markup=main_keyboard.as_markup())
        elif callback.data == 'Thursday':
            schedule = parser()
            schedule_for_day = get_schedule_for_day(schedule, 'Четверг')
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_day, reply_markup=main_keyboard.as_markup())
        elif callback.data == 'Friday':
            schedule = parser()
            schedule_for_day = get_schedule_for_day(schedule, 'Пятница')
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_day, reply_markup=main_keyboard.as_markup())
        elif callback.data == 'Saturday':
            schedule = parser()
            schedule_for_day = get_schedule_for_day(schedule, 'Суббота')
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text=schedule_for_day, reply_markup=main_keyboard.as_markup())
        elif callback.data == 'back_menu':
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id,
                                        text='Выберете необходимую функцию', reply_markup=main_keyboard.as_markup())

    await dp.start_polling(bot)


# Запускаем бота
if __name__ == '__main__':
    asyncio.run(main())
