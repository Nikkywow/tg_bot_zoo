import os
import logging
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from dotenv import load_dotenv

# Логи
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
STYLE_CONFIG = {
    "colors": {
        "dark_green": "#006455",
        "emerald": "#00AF96",
        "yellow": "#F5E646",
        "black": "#000000"
    },
    "logo_path": "assets/logos/mzoo-logo-circle-mono-black.jpg",
    "website": "https://moscowzoo.ru/my-zoo/become-a-guardian/",
    "social_media": {
        "share_text": "Я прошел викторину Московского зоопарка и мое тотемное животное - {animal}!\n\nПройди и ты: https://t.me/{bot_username}",
        "contact_email": "zoo-guardians@moscowzoo.ru",
        "contact_phone": "+7 (495) 255-57-63"
    }
}

# Данные для викторины
QUESTIONS = [
    {
        "text": "Какой у вас характер?",
        "options": [
            {"text": "Спокойный и мудрый", "traits": ["слон"]},
            {"text": "Независимый и загадочный", "traits": ["манул"]},
            {"text": "Общительный и энергичный", "traits": ["сурикат"]},
            {"text": "Яркий и артистичный", "traits": ["фламинго"]},
            {"text": "Любопытный и изобретательный", "traits": ["енот"]}
        ]
    },
    {
        "text": "Как вы проводите свободное время?",
        "options": [
            {"text": "Размышляю и помогаю другим", "traits": ["слон"]},
            {"text": "Наблюдаю за происходящим", "traits": ["манул"]},
            {"text": "Общаюсь с друзьями", "traits": ["сурикат"]},
            {"text": "Занимаюсь творчеством", "traits": ["фламинго"]},
            {"text": "Исследую что-то новое", "traits": ["енот"]}
        ]
    },
    {
        "text": "Как вы реагируете на проблемы?",
        "options": [
            {"text": "Решаю основательно", "traits": ["слон"]},
            {"text": "Действую осторожно", "traits": ["манул"]},
            {"text": "Собираю команду", "traits": ["сурикат"]},
            {"text": "Подхожу творчески", "traits": ["фламинго"]},
            {"text": "Ищу нестандартные решения", "traits": ["енот"]}
        ]
    }
]

ANIMALS = {
    "слон": {
        "description": "Вы - слон! Мудрый, сильный и заботливый. Как азиатский слон Памир из нашего зоопарка, вы отличаетесь спокойствием и надежностью.",
        "image": "assets/animals/african_elephant.jpg",
        "sponsor_info": "50 000₽/мес - кормление, уход и ветеринарное обслуживание",
        "traits": ["мудрость", "спокойствие", "забота"]
    },
    "манул": {
        "description": "Вы - манул! Независимый и загадочный, как наш символ - дикий кот манул. Вы цените личное пространство и наблюдательны.",
        "image": "assets/animals/manul.jpg",
        "sponsor_info": "30 000₽/мес - спецрацион из мяса и витаминов",
        "traits": ["независимость", "осторожность", "наблюдательность"]
    },
    "сурикат": {
        "description": "Вы - сурикат! Энергичный и общительный, как наши сурикаты. Вы любите компанию и всегда готовы помочь своей 'семье'.",
        "image": "assets/animals/meerkat.jpg",
        "sponsor_info": "15 000₽/мес - кормление насекомыми и фруктами",
        "traits": ["общительность", "энергичность", "преданность"]
    },
    "фламинго": {
        "description": "Вы - фламинго! Грациозный и артистичный, как наши розовые фламинго. Вы выделяетесь из толпы и цените красоту.",
        "image": "assets/animals/flamingo.jpg",
        "sponsor_info": "20 000₽/мес - специальный корм для поддержания окраса",
        "traits": ["артистичность", "грация", "яркость"]
    },
    "енот": {
        "description": "Вы - енот-полоскун! Изобретательный и любопытный, как наши еноты. Вы всегда находите нестандартные решения и любите исследовать новое.",
        "image": "assets/animals/raccoon.jpg",
        "sponsor_info": "18 000₽/мес - разнообразный рацион и обогащение среды",
        "traits": ["любопытство", "изобретательность", "адаптивность"]
    }
}

# Хранение состояния пользователей
user_data = {}

async def setup_commands(application: Application):
    """Настройка команд меню бота"""
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("share", "Поделиться результатом"),
        BotCommand("contact", "Связаться с сотрудником")
    ]
    await application.bot.set_my_commands(commands)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error("Ошибка:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("⚠️ Произошла ошибка. Пожалуйста, попробуйте позже.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главное меню с кнопкой контактов"""
    user_id = update.effective_user.id
    user_data[user_id] = {"answers": [], "current_question": 0}

    keyboard = [
        [InlineKeyboardButton("🐾 Начать викторину", callback_data='start_quiz')],
        [InlineKeyboardButton("ℹ️ О программе опеки", callback_data='about')],
        [InlineKeyboardButton("📞 Контакты зоопарка", callback_data='show_contacts')]
    ]

    try:
        if os.path.exists(STYLE_CONFIG["logo_path"]):
            with open(STYLE_CONFIG["logo_path"], 'rb') as logo:
                await update.message.reply_photo(
                    photo=logo,
                    caption="Добро пожаловать в бот Московского зоопарка!\n\n"
                     "Пройдите викторину и узнайте, какое животное вам соответствует!",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            await update.message.reply_text(
                "Добро пожаловать в бот Московского зоопарка!\n\n"
                     "Пройдите викторину и узнайте, какое животное вам соответствует!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logger.error(f"Ошибка при старте: {e}")
        await update.message.reply_text(
            "Добро пожаловать в бот Московского зоопарка!\n\n"
                     "Пройдите викторину и узнайте, какое животное вам соответствует!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def show_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Улучшенная функция показа контактов с надежной обработкой URL"""
    query = update.callback_query
    await query.answer()

    # Основной текст сообщения
    contacts_text = (
        "📞 <b>Контакты Московского зоопарка:</b>\n\n"
        "🕒 Часы работы: ежедневно с 9:00 до 18:00\n\n"
        "☎️ Телефон для справок:\n"
        "<code>+7 (495) 255-57-63</code>\n\n"
        "📧 Электронная почта:\n"
        "<code>info@moscowzoo.ru</code>\n\n"
        "📍 Адрес:\n"
        "Москва, Б. Грузинская ул., 1\n\n"
    )

    keyboard = []

    # 1. Кнопка карты
    maps_url = "https://yandex.ru/maps/-/CDb8NXL1"
    if maps_url and maps_url.startswith('http'):
        keyboard.append([InlineKeyboardButton("🗺️ Открыть в Яндекс Картах", url=maps_url)])

    # 2. Кнопка сайта
    website_url = "https://moscowzoo.ru"
    if website_url and website_url.startswith('http'):
        keyboard.append([InlineKeyboardButton("🌐 Посетить сайт", url=website_url)])

    # 3. Кнопка возврата
    keyboard.append([InlineKeyboardButton("🏠 На главную", callback_data='main_menu')])

    try:
        # Отправляем новое сообщение (не редактируем существующее)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=contacts_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке контактов: {e}")

        # Упрощенный вариант без кнопок, если основной крякнул
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                "Контакты зоопарка:\n"
                "Телефон: +7 (495) 255-57-63\n"
                "Адрес: Москва, Б. Грузинская ул., 1\n"
                "Сайт: https://www.moscowzoo.ru"
            )
        )

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало викторины"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data[user_id] = {"answers": [], "current_question": 0}
    await ask_question(query.message, user_id)


async def ask_question(message, user_id: int) -> None:
    """Задаем вопрос пользователю"""
    try:
        current_q = user_data[user_id]["current_question"]

        if current_q >= len(QUESTIONS):
            await show_result(message, user_id)
            return

        question = QUESTIONS[current_q]
        keyboard = [
            [InlineKeyboardButton(opt["text"], callback_data=f'ans_{i}')]
            for i, opt in enumerate(question["options"])
        ]

        await message.reply_text(
            text=f"Вопрос {current_q + 1}/{len(QUESTIONS)}:\n{question['text']}",
            reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Ошибка при задании вопроса: {e}")
        await message.reply_text("Произошла ошибка. Попробуйте начать викторину заново /start")


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ответов пользователя"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_data:
        await start_quiz(update, context)
        return

    try:
        answer_idx = int(query.data.split('_')[1])
        current_q = user_data[user_id]["current_question"]

        # Добавляем выбранные черты в ответы
        selected_traits = QUESTIONS[current_q]["options"][answer_idx]["traits"]
        user_data[user_id]["answers"].extend(selected_traits)

        # Переходим к следующему вопросу
        user_data[user_id]["current_question"] += 1
        await ask_question(query.message, user_id)

    except Exception as e:
        logger.error(f"Ошибка обработки ответа: {e}")
        await query.message.reply_text("Произошла ошибка. Начинаем викторину заново.")
        await start_quiz(update, context)


async def show_result(message, user_id: int) -> None:
    """Показываем результат викторины с изображением животного"""
    try:
        # Получаем результат
        result_animal = calculate_result(user_data[user_id]["answers"])
        animal_info = ANIMALS.get(result_animal, ANIMALS["слон"])

        # Формируем сообщение
        caption = (
            f"<b>MOSCOW ZOO PRESENTS</b>\n\n"
            f"🎉 <b>Ваше тотемное животное - {result_animal.upper()}!</b>\n\n"
            f"{animal_info['description']}\n\n"
            f"<b>Характерные черты:</b> {', '.join(animal_info['traits'])}\n\n"
            f"<b>Cтоимость опеки:</b> {animal_info['sponsor_info']}"

        )

        # Пытаемся отправить фото животного
        try:
            if os.path.exists(animal_info["image"]):
                with open(animal_info["image"], 'rb') as photo:
                    await message.reply_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode='HTML'
                    )
            else:
                # Если фото по какой-то неведомой причине нет, отправляем только текст
                await message.reply_text(
                    text=caption,
                    parse_mode='HTML'
                )
                logger.warning(f"Изображение животного не найдено по пути: {animal_info['image']}")
        except Exception as photo_error:
            logger.error(f"Ошибка при отправке фото: {photo_error}")
            await message.reply_text(
                text=caption,
                parse_mode='HTML'
            )

        # Кнопки действий
        keyboard = [
            [InlineKeyboardButton("📢 Поделиться в соцсетях", callback_data='share_result')],
            [InlineKeyboardButton(
                text=f"🛡 Взять под опеку",
                url=STYLE_CONFIG["website"]
            )],
            [InlineKeyboardButton("🔁 Пройти тест заново", callback_data='start_quiz')],
            [InlineKeyboardButton("ℹ️ Все животные программы", url=STYLE_CONFIG["website"])],
            [InlineKeyboardButton("🏠 Назад в главное меню", callback_data='main_menu')]
        ]

        await message.reply_text(
            text="Хотите поддержать своего тотемного животного?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Ошибка при показе результата: {e}")
        await message.reply_text(
            "Произошла ошибка при обработке вашего результата. Попробуйте позже."
        )
        await main_menu(message)


def calculate_result(answers: list) -> str:
    """Определяем результат викторины"""
    if not answers:
        return "слон"

    # Подсчитываем количество упоминаний каждого животного
    animal_counts = {}
    for animal in answers:
        if animal in ANIMALS:
            animal_counts[animal] = animal_counts.get(animal, 0) + 1

    # Возвращаем животное с максимальным количеством упоминаний
    return max(animal_counts.items(), key=lambda x: x[1])[0] if animal_counts else "слон"


async def share_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Поделиться результатом в соцсетях"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id not in user_data or not user_data[user_id].get("answers"):
        await query.message.reply_text("Сначала пройдите викторину!")
        return

    result_animal = calculate_result(user_data[user_id]["answers"])
    bot_username = context.bot.username

    share_text = (
        f"Я прошел викторину Московского зоопарка и мое тотемное животное - {result_animal}!\n\n"
        f"Пройди и ты: https://t.me/{bot_username}"
    )

    keyboard = [
        [
            InlineKeyboardButton("Telegram", url=f"https://t.me/share/url?text={share_text}"),
            InlineKeyboardButton("VK", url=f"https://vk.com/share.php?comment={share_text}")
        ],
        [
            InlineKeyboardButton("Назад", callback_data='main_menu')
        ]
    ]

    await query.edit_message_text(
        text="Выберите соцсеть для публикации:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def about_program(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Информация о программе опеки"""
    query = update.callback_query
    await query.answer()

    text = (
        "🐯 <b>Программа «Возьми животное под опеку»</b> 🐻\n\n"
        "Это возможность помочь Московскому зоопарку заботиться о его обитателях.\n\n"
        "<b>Став опекуном, вы получаете:</b>\n"
        "✅ Именной сертификат\n"
        "✅ Информацию о вашем подопечном\n"
        "✅ Возможность навещать его\n\n"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 На главную", callback_data='main_menu')],
        [InlineKeyboardButton("🛡 Стать опекуном", url=STYLE_CONFIG["website"])]
    ]

    try:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        await query.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
            disable_web_page_preview=True
        )



async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат в главное меню"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🐾 Начать викторину", callback_data='start_quiz')],
        [InlineKeyboardButton("ℹ️ О программе опеки", callback_data='about')],
        [InlineKeyboardButton("📞 Контакты зоопарка", callback_data='show_contacts')]
    ]

    try:
        # Пытаемся отправить лого с кнопками
        if os.path.exists(STYLE_CONFIG["logo_path"]):
            with open(STYLE_CONFIG["logo_path"], 'rb') as logo:
                await query.message.reply_photo(
                    photo=logo,
                    caption="Добро пожаловать в бот Московского зоопарка!\n\n"
                            "Пройдите викторину и узнайте, какое животное вам соответствует!",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            # Если лого не найдено, отправляем текст
            await query.edit_message_text(
                text="Добро пожаловать в бот Московского зоопарка!\n\n"
                     "Пройдите викторину и узнайте, какое животное вам соответствует!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            logger.warning(f"Логотип не найден по пути: {STYLE_CONFIG['logo_path']}")
    except Exception as e:
        logger.error(f"Ошибка при возврате в меню: {e}")
        await query.edit_message_text(
            text="Добро пожаловать!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def main() -> None:
    """Запуск приложения"""
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("Токен бота не найден в переменных окружения")

    application = Application.builder().token(token).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start_quiz, pattern='^start_quiz$'))
    application.add_handler(CallbackQueryHandler(about_program, pattern='^about$'))
    application.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern='^ans_'))
    application.add_handler(CallbackQueryHandler(show_contacts, pattern='^show_contacts$'))
    application.add_handler(CallbackQueryHandler(share_result, pattern='^share_result$'))
    application.add_error_handler(error_handler)

    # Запуск бота
    logger.info("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()