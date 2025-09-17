"""
Обработчики основных команд Telegram-бота
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database import get_user, create_user, get_user_bets, get_active_events

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - регистрация пользователя"""
    user = update.effective_user
    user_id = user.id
    
    # Проверяем, есть ли пользователь в базе
    existing_user = await get_user(user_id)
    
    if existing_user:
        welcome_text = f"👋 С возвращением, {user.first_name}!\n\n"
    else:
        # Создаем нового пользователя
        await create_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        welcome_text = f"🎉 Добро пожаловать, {user.first_name}!\n\nВы успешно зарегистрированы в системе ставок.\n\n"
    
    welcome_text += (
        "🎯 Здесь вы можете делать ставки на различные события\n"
        "💰 Следить за своими ставками и балансом\n"
        "📊 Просматривать статистику\n\n"
        "Используйте /help для получения списка команд"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎯 Посмотреть события", callback_data="events")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📋 **Доступные команды:**\n\n"
        "🏠 /start - Главное меню и регистрация\n"
        "ℹ️ /help - Показать эту справку\n"
        "👤 /profile - Ваш профиль\n"
        "💳 /balance - Текущий баланс\n"
        "🎯 /events - Доступные события для ставок\n"
        "💰 /mybets - Ваши ставки\n\n"
        "**Как делать ставки:**\n"
        "1. Выберите событие из списка /events\n"
        "2. Выберите исход события\n"
        "3. Введите сумму ставки\n"
        "4. Подтвердите ставку\n\n"
        "**Правила:**\n"
        "• Минимальная ставка: 10 единиц\n"
        "• Максимальная ставка: 10,000 единиц\n"
        "• Ставки принимаются до начала события\n"
        "• Выплаты производятся автоматически после завершения события\n\n"
        "❓ Если у вас есть вопросы, обратитесь к администратору"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /profile"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации")
        return
    
    # Получаем статистику пользователя
    user_bets = await get_user_bets(user_id)
    total_bets = len(user_bets)
    total_amount = sum(bet.amount for bet in user_bets)
    won_bets = len([bet for bet in user_bets if bet.status == 'won'])
    lost_bets = len([bet for bet in user_bets if bet.status == 'lost'])
    pending_bets = len([bet for bet in user_bets if bet.status == 'pending'])
    
    win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
    
    profile_text = (
        f"👤 **Профиль пользователя**\n\n"
        f"🆔 ID: {user.user_id}\n"
        f"👤 Имя: {user.first_name}"
    )
    
    if user.last_name:
        profile_text += f" {user.last_name}"
    
    if user.username:
        profile_text += f"\n📱 Username: @{user.username}"
    
    profile_text += (
        f"\n📅 Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}\n"
        f"💰 Баланс: {user.balance:.2f} единиц\n\n"
        f"📊 **Статистика ставок:**\n"
        f"🎯 Всего ставок: {total_bets}\n"
        f"💸 Общая сумма ставок: {total_amount:.2f}\n"
        f"✅ Выигранных: {won_bets}\n"
        f"❌ Проигранных: {lost_bets}\n"
        f"⏳ В ожидании: {pending_bets}\n"
        f"📈 Процент побед: {win_rate:.1f}%"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 Баланс", callback_data="balance")],
        [InlineKeyboardButton("💰 Мои ставки", callback_data="my_bets")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')

async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /balance"""
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Пользователь не найден. Используйте /start для регистрации")
        return
    
    balance_text = (
        f"💳 **Ваш баланс**\n\n"
        f"💰 Текущий баланс: **{user.balance:.2f}** единиц\n\n"
        f"ℹ️ Для пополнения баланса обратитесь к администратору"
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(balance_text, reply_markup=reply_markup, parse_mode='Markdown')

async def events_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /events"""
    events = await get_active_events()
    
    if not events:
        text = "🎯 **Доступные события**\n\n❌ В данный момент нет активных событий для ставок"
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    else:
        text = "🎯 **Доступные события для ставок:**\n\n"
        keyboard = []
        
        for event in events:
            text += (
                f"🏆 **{event.title}**\n"
                f"📅 {event.start_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"📝 {event.description}\n\n"
            )
            keyboard.append([InlineKeyboardButton(
                f"🎯 {event.title}", 
                callback_data=f"event_{event.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
