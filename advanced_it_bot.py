import logging
import json
import os
import random
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (берем из переменной окружения для безопасности)
TOKEN = os.getenv('BOT_TOKEN', "8005359232:AAEDgsNYtgbQHigxVH6__mLS0f3QvujHP3o")

# Файл для сохранения данных пользователей
USER_DATA_FILE = "user_data.json"

# IT фразы для изучения
conversation_phrases = [
    # Daily Stand-up фразы
    {"en": "What did you work on yesterday?", "ru": "Над чем ты работал вчера?", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "What are you planning to do today?", "ru": "Что планируешь делать сегодня?", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "Do you have any blockers?", "ru": "У тебя есть какие-то блокеры?", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "I'm blocked by the API issue", "ru": "Меня блокирует проблема с API", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "I finished the user authentication feature", "ru": "Я закончил функционал аутентификации пользователей", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "I'm working on the database migration", "ru": "Я работаю над миграцией базы данных", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "I need help with the deployment script", "ru": "Мне нужна помощь со скриптом деплоя", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "The testing is taking longer than expected", "ru": "Тестирование занимает больше времени, чем ожидалось", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "I'm waiting for the design mockups", "ru": "Я жду дизайн-макеты", "category": "daily", "context": "Daily stand-up meeting"},
    {"en": "Can you review my pull request?", "ru": "Можешь просмотреть мой пул реквест?", "category": "daily", "context": "Daily stand-up meeting"},
    
    # Демо с заказчиком
    {"en": "Let me show you the new dashboard", "ru": "Позвольте показать вам новую панель управления", "category": "demo", "context": "Client demonstration"},
    {"en": "This feature will save you a lot of time", "ru": "Эта функция сэкономит вам много времени", "category": "demo", "context": "Client demonstration"},
    {"en": "We've implemented all your requirements", "ru": "Мы реализовали все ваши требования", "category": "demo", "context": "Client demonstration"},
    {"en": "Let me walk you through the workflow", "ru": "Позвольте провести вас через рабочий процесс", "category": "demo", "context": "Client demonstration"},
    {"en": "Do you have any questions about this feature?", "ru": "У вас есть вопросы по этой функции?", "category": "demo", "context": "Client demonstration"},
    
    # Общение с коллегами
    {"en": "Could you help me debug this issue?", "ru": "Можешь помочь с отладкой этой проблемы?", "category": "colleagues", "context": "Team communication"},
    {"en": "Let's pair program on this task", "ru": "Давай запрограммируем это вместе", "category": "colleagues", "context": "Team communication"},
    {"en": "I think there's a better approach", "ru": "Думаю, есть более хороший подход", "category": "colleagues", "context": "Team communication"},
    {"en": "Can you share your screen?", "ru": "Можешь расшарить свой экран?", "category": "colleagues", "context": "Team communication"},
    {"en": "Let's schedule a code review session", "ru": "Давай запланируем сессию ревью кода", "category": "colleagues", "context": "Team communication"},
    
    # Планирование и задачи
    {"en": "How long will this take to implement?", "ru": "Сколько времени займет реализация?", "category": "planning", "context": "Project planning"},
    {"en": "Let's break this down into smaller tasks", "ru": "Давайте разобьем это на более мелкие задачи", "category": "planning", "context": "Project planning"},
    {"en": "We're ahead of schedule", "ru": "Мы опережаем график", "category": "planning", "context": "Project planning"},
    {"en": "This might affect the deadline", "ru": "Это может повлиять на дедлайн", "category": "planning", "context": "Project planning"},
    {"en": "Let's prioritize this feature", "ru": "Давайте приоритизируем эту функцию", "category": "planning", "context": "Project planning"},
    
    # Проблемы и решения
    {"en": "I'm getting an error message", "ru": "Я получаю сообщение об ошибке", "category": "problems", "context": "Problem solving"},
    {"en": "Let's check the server logs", "ru": "Давайте проверим логи сервера", "category": "problems", "context": "Problem solving"},
    {"en": "This works on my machine", "ru": "У меня на машине это работает", "category": "problems", "context": "Problem solving"},
    {"en": "Have you tried restarting the service?", "ru": "Ты пробовал перезапустить сервис?", "category": "problems", "context": "Problem solving"},
    {"en": "Let's revert to the previous version", "ru": "Давайте откатимся к предыдущей версии", "category": "problems", "context": "Problem solving"},
    
    # Встречи и совещания
    {"en": "Let's start with the agenda", "ru": "Давайте начнем с повестки дня", "category": "meetings", "context": "Team meetings"},
    {"en": "Can everyone see my screen?", "ru": "Все видят мой экран?", "category": "meetings", "context": "Team meetings"},
    {"en": "Let's take this offline", "ru": "Давайте обсудим это отдельно", "category": "meetings", "context": "Team meetings"},
    {"en": "We're running out of time", "ru": "У нас заканчивается время", "category": "meetings", "context": "Team meetings"},
    {"en": "I'll send the meeting notes", "ru": "Я отправлю заметки со встречи", "category": "meetings", "context": "Team meetings"},
    
    # Обратная связь и ревью
    {"en": "The code looks good overall", "ru": "Код в целом выглядит хорошо", "category": "feedback", "context": "Code review"},
    {"en": "I have a few suggestions", "ru": "У меня есть несколько предложений", "category": "feedback", "context": "Code review"},
    {"en": "This could be simplified", "ru": "Это можно упростить", "category": "feedback", "context": "Code review"},
    {"en": "Great job on this feature", "ru": "Отличная работа над этой функцией", "category": "feedback", "context": "Code review"},
    {"en": "Consider using a more descriptive name", "ru": "Подумай об использовании более описательного имени", "category": "feedback", "context": "Code review"},
    
    # Запуск и развертывание
    {"en": "The build is failing", "ru": "Сборка падает", "category": "deployment", "context": "Deployment process"},
    {"en": "Let's deploy to staging first", "ru": "Давайте сначала развернем на staging", "category": "deployment", "context": "Deployment process"},
    {"en": "The deployment was successful", "ru": "Развертывание прошло успешно", "category": "deployment", "context": "Deployment process"},
    {"en": "We need to rollback immediately", "ru": "Нам нужно немедленно откатиться", "category": "deployment", "context": "Deployment process"},
    {"en": "All tests are passing", "ru": "Все тесты проходят", "category": "deployment", "context": "Deployment process"},
]

# Технические термины
tech_terms = [
    {"en": "algorithm", "ru": "алгоритм", "example": "An algorithm is a step-by-step procedure for solving a problem.", "example_ru": "Алгоритм - это пошаговая процедура для решения задачи."},
    {"en": "array", "ru": "массив", "example": "An array is a collection of elements identified by index or key.", "example_ru": "Массив - это коллекция элементов, идентифицируемых по индексу или ключу."},
    {"en": "binary", "ru": "двоичный", "example": "Binary code uses 0s and 1s to represent data.", "example_ru": "Двоичный код использует 0 и 1 для представления данных."},
    {"en": "bit", "ru": "бит", "example": "A bit is the smallest unit of data in computing, either 0 or 1.", "example_ru": "Бит - это наименьшая единица данных в вычислениях, либо 0, либо 1."},
    {"en": "byte", "ru": "байт", "example": "A byte consists of 8 bits and represents a single character.", "example_ru": "Байт состоит из 8 битов и представляет один символ."},
    {"en": "cache", "ru": "кэш", "example": "A cache stores frequently accessed data for faster retrieval.", "example_ru": "Кэш хранит часто используемые данные для более быстрого доступа."},
    {"en": "class", "ru": "класс", "example": "A class is a blueprint for creating objects in programming.", "example_ru": "Класс - это шаблон для создания объектов в программировании."},
    {"en": "code", "ru": "код", "example": "Code is a set of instructions written in a programming language.", "example_ru": "Код - это набор инструкций, написанных на языке программирования."},
    {"en": "compiler", "ru": "компилятор", "example": "A compiler translates source code into machine code.", "example_ru": "Компилятор переводит исходный код в машинный код."},
    {"en": "database", "ru": "база данных", "example": "A database is an organized collection of data.", "example_ru": "База данных - это организованная коллекция данных."},
    {"en": "frontend", "ru": "фронтенд", "example": "Frontend development focuses on user interface and experience.", "example_ru": "Фронтенд-разработка сосредоточена на пользовательском интерфейсе и опыте."},
    {"en": "backend", "ru": "бэкенд", "example": "Backend development handles server-side logic and databases.", "example_ru": "Бэкенд-разработка занимается серверной логикой и базами данных."},
    {"en": "API", "ru": "API", "example": "API defines how software components communicate.", "example_ru": "API определяет, как компоненты программного обеспечения взаимодействуют."},
    {"en": "debugging", "ru": "отладка", "example": "Debugging is the process of finding and fixing errors in code.", "example_ru": "Отладка - это процесс поиска и исправления ошибок в коде."},
    {"en": "function", "ru": "функция", "example": "A function is a block of code that performs a specific task.", "example_ru": "Функция - это блок кода, который выполняет определенную задачу."},
    {"en": "variable", "ru": "переменная", "example": "A variable stores data that can be changed during program execution.", "example_ru": "Переменная хранит данные, которые могут изменяться во время выполнения программы."},
    {"en": "loop", "ru": "цикл", "example": "A loop repeats a block of code until a condition is met.", "example_ru": "Цикл повторяет блок кода до выполнения условия."},
    {"en": "object", "ru": "объект", "example": "An object is an instance of a class in programming.", "example_ru": "Объект - это экземпляр класса в программировании."},
    {"en": "Python", "ru": "Python", "example": "Python is known for its simple and readable syntax.", "example_ru": "Python известен своим простым и читаемым синтаксисом."},
    {"en": "JavaScript", "ru": "JavaScript", "example": "JavaScript adds interactivity to web pages.", "example_ru": "JavaScript добавляет интерактивность веб-страницам."},
]

# Глобальные переменные
user_data = {}

def load_user_data():
    """Загружает данные пользователей из файла"""
    global user_data
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                logger.info(f"Загружены данные {len(user_data)} пользователей")
        else:
            user_data = {}
            logger.info("Файл данных не найден, создан новый")
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        user_data = {}

def save_user_data():
    """Сохраняет данные пользователей в файл"""
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        logger.info("Данные пользователей сохранены")
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")

def get_user_stats(user_id):
    """Получает статистику пользователя"""
    user_id = str(user_id)
    if user_id not in user_data:
        user_data[user_id] = {
            'phrases_learned': 0,
            'terms_learned': 0,
            'quiz_correct': 0,
            'quiz_total': 0,
            'last_activity': datetime.now().isoformat(),
            'daily_streak': 0,
            'last_daily_activity': None,
            'notifications_enabled': True,
            'learned_phrases': [],
            'learned_terms': []
        }
    return user_data[user_id]

def update_user_activity(user_id):
    """Обновляет активность пользователя"""
    stats = get_user_stats(user_id)
    today = datetime.now().date().isoformat()
    
    if stats['last_daily_activity'] != today:
        if stats['last_daily_activity'] == (datetime.now().date() - timedelta(days=1)).isoformat():
            stats['daily_streak'] += 1
        else:
            stats['daily_streak'] = 1
        stats['last_daily_activity'] = today
    
    stats['last_activity'] = datetime.now().isoformat()
    save_user_data()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню бота"""
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Пользователь"
        
        update_user_activity(user_id)
        
        keyboard = [
            [InlineKeyboardButton("📚 Изучать фразы", callback_data="learn_phrases"),
             InlineKeyboardButton("🔧 Изучать термины", callback_data="learn_terms")],
            [InlineKeyboardButton("🎯 Пройти квиз", callback_data="quiz_menu"),
             InlineKeyboardButton("📊 Моя статистика", callback_data="stats")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
             InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"🚀 *Привет, {user_name}!*\n"
            f"*Добро пожаловать в IT English Bot!*\n\n"
            f"🎯 *Что умеет бот:*\n"
            f"📚 Изучение IT фраз и терминов\n"
            f"🎮 Интерактивные квизы\n"
            f"📊 Отслеживание прогресса\n"
            f"🔔 Ежедневные напоминания\n"
            f"🏆 Система достижений\n\n"
            f"*Выберите действие:*"
        )
        
        if update.message:
            await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
            
        logger.info(f"Пользователь {user_id} ({user_name}) запустил бота")
        
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        error_text = "Произошла ошибка. Попробуйте позже."
        if update.message:
            await update.message.reply_text(error_text)
        elif update.callback_query:
            await update.callback_query.answer(error_text, show_alert=True)

async def learn_phrases_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню изучения фраз"""
    try:
        query = update.callback_query
        await query.answer()
        
        categories = list(set([phrase['category'] for phrase in conversation_phrases]))
        
        keyboard = []
        category_names = {
            'daily': 'Ежедневные встречи',
            'demo': 'Демо с клиентом',
            'colleagues': 'Общение с коллегами',
            'planning': 'Планирование',
            'problems': 'Решение проблем',
            'meetings': 'Встречи',
            'feedback': 'Обратная связь',
            'deployment': 'Развертывание'
        }
        
        for i in range(0, len(categories), 2):
            row = []
            cat1 = categories[i]
            row.append(InlineKeyboardButton(f"📝 {category_names.get(cat1, cat1.title())}", callback_data=f"phrases_{cat1}"))
            
            if i + 1 < len(categories):
                cat2 = categories[i+1]
                row.append(InlineKeyboardButton(f"📝 {category_names.get(cat2, cat2.title())}", callback_data=f"phrases_{cat2}"))
            
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🎲 Случайная фраза", callback_data="phrases_random")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"📚 *Изучение IT фраз*\n\n"
            f"Выберите категорию или получите случайную фразу:\n\n"
            f"*Доступные категории:* {len(categories)}\n"
            f"*Всего фраз:* {len(conversation_phrases)}"
        )
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в learn_phrases_menu: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def show_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает фразу пользователю"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        update_user_activity(user_id)
        
        category = query.data.split('_')[1] if len(query.data.split('_')) > 1 else "random"
        
        if category == "random":
            phrase = random.choice(conversation_phrases)
        else:
            category_phrases = [p for p in conversation_phrases if p['category'] == category]
            if not category_phrases:
                phrase = random.choice(conversation_phrases)
            else:
                phrase = random.choice(category_phrases)
        
        # Обновляем статистику
        stats = get_user_stats(user_id)
        phrase_id = f"{phrase['en']}_{phrase['ru']}"
        if phrase_id not in stats['learned_phrases']:
            stats['learned_phrases'].append(phrase_id)
            stats['phrases_learned'] += 1
            save_user_data()
        
        text = (
            f"📚 *Фраза #{stats['phrases_learned']}*\n\n"
            f"🇬🇧 *{phrase['en']}*\n"
            f"🇷🇺 *{phrase['ru']}*\n\n"
            f"📝 *Категория:* {phrase['category'].title()}\n"
            f"🎯 *Контекст:* {phrase['context']}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Еще фраза", callback_data=f"phrases_{category}"),
             InlineKeyboardButton("❤️ В избранное", callback_data=f"fav_phrase_{category}")],
            [InlineKeyboardButton("📚 Категории", callback_data="learn_phrases"),
             InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в show_phrase: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def learn_terms_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню изучения терминов"""
    try:
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("💻 Программирование", callback_data="terms_programming"),
             InlineKeyboardButton("🌐 Веб-разработка", callback_data="terms_web")],
            [InlineKeyboardButton("🗄️ Базы данных", callback_data="terms_database"),
             InlineKeyboardButton("☁️ Облачные технологии", callback_data="terms_cloud")],
            [InlineKeyboardButton("🎲 Случайный термин", callback_data="terms_random")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"🔧 *Изучение IT терминов*\n\n"
            f"Выберите категорию терминов:\n\n"
            f"*Всего терминов:* {len(tech_terms)}\n"
            f"*Категории:* Программирование, Веб-разработка, Базы данных, Облачные технологии"
        )
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в learn_terms_menu: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def show_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает термин пользователю"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        update_user_activity(user_id)
        
        # Выбираем случайный термин
        term = random.choice(tech_terms)
        
        # Обновляем статистику
        stats = get_user_stats(user_id)
        term_id = f"{term['en']}_{term['ru']}"
        if term_id not in stats['learned_terms']:
            stats['learned_terms'].append(term_id)
            stats['terms_learned'] += 1
            save_user_data()
        
        text = (
            f"🔧 *Термин #{stats['terms_learned']}*\n\n"
            f"🇬🇧 *{term['en']}*\n"
            f"🇷🇺 *{term['ru']}*\n\n"
            f"📖 *Пример:*\n"
            f"🇬🇧 {term['example']}\n\n"
            f"🇷🇺 {term['example_ru']}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Еще термин", callback_data="terms_random"),
             InlineKeyboardButton("❤️ В избранное", callback_data="fav_term")],
            [InlineKeyboardButton("🔧 Категории", callback_data="learn_terms"),
             InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в show_term: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def quiz_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню квизов"""
    try:
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("📚 Квиз по фразам", callback_data="quiz_phrases"),
             InlineKeyboardButton("🔧 Квиз по терминам", callback_data="quiz_terms")],
            [InlineKeyboardButton("🎯 Смешанный квиз", callback_data="quiz_mixed")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"🎯 *Квизы и тесты*\n\n"
            f"Проверьте свои знания!\n\n"
            f"📚 *Квиз по фразам* - переводы IT фраз\n"
            f"🔧 *Квиз по терминам* - технические термины\n"
            f"🎯 *Смешанный квиз* - фразы + термины"
        )
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в quiz_menu: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает квиз"""
    try:
        query = update.callback_query
        await query.answer()
        
        quiz_type = query.data.split('_')[1]
        
        # Выбираем вопрос в зависимости от типа квиза
        if quiz_type == "phrases":
            question_data = random.choice(conversation_phrases)
            question = f"Переведите фразу:\n🇬🇧 *{question_data['en']}*"
            correct_answer = question_data['ru']
            wrong_pool = conversation_phrases
        elif quiz_type == "terms":
            question_data = random.choice(tech_terms)
            question = f"Переведите термин:\n🇬🇧 *{question_data['en']}*"
            correct_answer = question_data['ru']
            wrong_pool = tech_terms
        else:  # mixed
            all_items = conversation_phrases + tech_terms
            question_data = random.choice(all_items)
            question = f"Переведите:\n🇬🇧 *{question_data['en']}*"
            correct_answer = question_data['ru']
            wrong_pool = all_items
        
        # Генерируем неправильные варианты
        wrong_answers = []
        attempts = 0
        while len(wrong_answers) < 3 and attempts < 50:
            item = random.choice(wrong_pool)
            if item['ru'] != correct_answer and item['ru'] not in wrong_answers:
                wrong_answers.append(item['ru'])
            attempts += 1
        
        # Если не хватает вариантов, добавляем дефолтные
        while len(wrong_answers) < 3:
            wrong_answers.append(f"Неправильный ответ {len(wrong_answers) + 1}")
        
        answers = [correct_answer] + wrong_answers[:3]
        random.shuffle(answers)
        
        keyboard = []
        for i, answer in enumerate(answers):
            is_correct = answer == correct_answer
            callback_data = f"answer_{i}_{is_correct}_{quiz_type}"
            keyboard.append([InlineKeyboardButton(f"{chr(65+i)}. {answer}", callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад к квизам", callback_data="quiz_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(question, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в start_quiz: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ответ на квиз"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        stats = get_user_stats(user_id)
        
        parts = query.data.split('_')
        is_correct = parts[2] == "True"
        quiz_type = parts[3]
        
        stats['quiz_total'] += 1
        if is_correct:
            stats['quiz_correct'] += 1
            result_text = "✅ *Правильно!*"
            result_emoji = "🎉"
        else:
            result_text = "❌ *Неправильно*"
            result_emoji = "😔"
        
        save_user_data()
        
        accuracy = (stats['quiz_correct'] / stats['quiz_total']) * 100 if stats['quiz_total'] > 0 else 0
        
        text = (
            f"{result_emoji} {result_text}\n\n"
            f"📊 *Ваша статистика:*\n"
            f"✅ Правильных ответов: {stats['quiz_correct']}\n"
            f"📝 Всего вопросов: {stats['quiz_total']}\n"
            f"🎯 Точность: {accuracy:.1f}%"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Еще вопрос", callback_data=f"quiz_{quiz_type}"),
             InlineKeyboardButton("🎯 Другой квиз", callback_data="quiz_menu")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в handle_quiz_answer: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику пользователя"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        stats = get_user_stats(user_id)
        
        accuracy = (stats['quiz_correct'] / stats['quiz_total']) * 100 if stats['quiz_total'] > 0 else 0
        
        # Определяем уровень
        total_learned = stats['phrases_learned'] + stats['terms_learned']
        if total_learned < 10:
            level = "🌱 Новичок"
        elif total_learned < 50:
            level = "📚 Изучающий"
        elif total_learned < 100:
            level = "💪 Продвинутый"
        elif total_learned < 200:
            level = "🏆 Эксперт"
        else:
            level = "🚀 Мастер"
        
        text = (
            f"📊 *Ваша статистика*\n\n"
            f"🏅 *Уровень:* {level}\n"
            f"🔥 *Дневная серия:* {stats['daily_streak']} дней\n\n"
            f"📚 *Изучено:*\n"
            f"• Фразы: {stats['phrases_learned']}\n"
            f"• Термины: {stats['terms_learned']}\n"
            f"• Всего: {total_learned}\n\n"
            f"🎯 *Квизы:*\n"
            f"• Правильных: {stats['quiz_correct']}\n"
            f"• Всего: {stats['quiz_total']}\n"
            f"• Точность: {accuracy:.1f}%\n\n"
            f"📅 *Последняя активность:* {stats['last_activity'][:10]}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в show_stats: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню настроек"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        stats = get_user_stats(user_id)
        
        notifications_status = "🔔 Включены" if stats['notifications_enabled'] else "🔕 Выключены"
        
        keyboard = [
            [InlineKeyboardButton(f"🔔 Уведомления: {notifications_status}", callback_data="toggle_notifications")],
            [InlineKeyboardButton("🗑️ Сбросить прогресс", callback_data="reset_progress")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            f"⚙️ *Настройки*\n\n"
            f"🔔 *Уведомления:* {notifications_status}\n"
            f"📊 *Сохранение данных:* Включено\n\n"
            f"Настройте бота под себя!"
        )
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в settings_menu: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню помощи"""
    try:
        query = update.callback_query
        await query.answer()
        
        text = (
            f"ℹ️ *Помощь по боту*\n\n"
            f"🎯 *Основные функции:*\n"
            f"• `/start` - запустить бота\n"
            f"• Изучение IT фраз и терминов\n"
            f"• Интерактивные квизы\n"
            f"• Отслеживание прогресса\n"
            f"• Ежедневные напоминания\n\n"
            f"📚 *Как пользоваться:*\n"
            f"1. Выберите \"Изучать фразы\" или \"Изучать термины\"\n"
            f"2. Изучайте материал по категориям\n"
            f"3. Проходите квизы для закрепления\n"
            f"4. Отслеживайте прогресс в статистике\n\n"
            f"🏆 *Система уровней:*\n"
            f"🌱 Новичок (0-9)\n"
            f"📚 Изучающий (10-49)\n"
            f"💪 Продвинутый (50-99)\n"
            f"🏆 Эксперт (100-199)\n"
            f"🚀 Мастер (200+)\n\n"
            f"❓ *Вопросы?* Пишите разработчику!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в help_menu: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключает уведомления"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        stats = get_user_stats(user_id)
        stats['notifications_enabled'] = not stats['notifications_enabled']
        save_user_data()
        
        await settings_menu(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка в toggle_notifications: {e}")
        await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех callback запросов"""
    try:
        query = update.callback_query
        data = query.data
        
        logger.info(f"Получен callback: {data} от пользователя {update.effective_user.id}")
        
        if data == "back_to_main":
            await start(update, context)
        elif data == "learn_phrases":
            await learn_phrases_menu(update, context)
        elif data.startswith("phrases_"):
            await show_phrase(update, context)
        elif data == "learn_terms":
            await learn_terms_menu(update, context)
        elif data.startswith("terms_"):
            await show_term(update, context)
        elif data == "quiz_menu":
            await quiz_menu(update, context)
        elif data.startswith("quiz_"):
            await start_quiz(update, context)
        elif data.startswith("answer_"):
            await handle_quiz_answer(update, context)
        elif data == "stats":
            await show_stats(update, context)
        elif data == "settings":
            await settings_menu(update, context)
        elif data == "help":
            await help_menu(update, context)
        elif data == "toggle_notifications":
            await toggle_notifications(update, context)
        elif data.startswith("fav_"):
            await query.answer("Функция в разработке! 🚧", show_alert=True)
        elif data == "reset_progress":
            await query.answer("Функция в разработке! 🚧", show_alert=True)
        else:
            await query.answer("Неизвестная команда", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_callback: {e}")
        if update.callback_query:
            await update.callback_query.answer("Произошла ошибка", show_alert=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        text = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Получено сообщение от {user_id}: {text}")
        
        if text.lower() in ['/start', 'старт', 'начать']:
            await start(update, context)
        else:
            await update.message.reply_text(
                "Используйте кнопки меню или команду /start для навигации! 😊"
            )
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update and update.effective_user:
        try:
            error_text = "Произошла ошибка. Попробуйте позже или обратитесь к разработчику."
            if update.message:
                await update.message.reply_text(error_text)
            elif update.callback_query:
                await update.callback_query.answer(error_text, show_alert=True)
        except:
            pass

def main():
    """Главная функция"""
    print("🚀 Запуск IT English бота...")
    print(f"📱 Токен: {TOKEN[:10]}...")
    
    # Загружаем данные пользователей
    load_user_data()
    
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(handle_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Добавляем обработчик ошибок
        app.add_error_handler(error_handler)
        
        print("✅ Бот успешно запущен!")
        print("📱 Найдите бота в Telegram")
        print("💬 Отправьте команду: /start")
        print("🛑 Остановка: Ctrl+C")
        print("-" * 50)
        
        # Запускаем бота
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка: {e}")
        input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
