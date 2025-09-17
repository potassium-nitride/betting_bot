"""
Админ-функционал для управления событиями и ставками
"""
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config.settings import ADMIN_IDS
from src.database import (
    create_event, get_active_events, get_event_by_id,
    Event, Outcome, EventStatus, BetStatus, get_db, SessionLocal,
    update_user_balance, DATABASE_URL, User, Bet
) # Добавлены DATABASE_URL, User, Bet для show_admin_stats

def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик админ-меню"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    text = "⚙️ **Панель администратора**\n\nВыберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("➕ Создать событие", callback_data="admin_create_event")],
        [InlineKeyboardButton("📋 Управление событиями", callback_data="admin_manage_events")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("💰 Управление балансами", callback_data="admin_balances")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработчик админ callback запросов"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text("❌ У вас нет прав администратора")
        return
    
    if data == "admin_menu":
        await admin_menu_handler(update, context)
    
    elif data == "admin_create_event":
        await start_event_creation(update, context)
    
    elif data == "admin_manage_events":
        await show_events_management(update, context)
    
    elif data == "admin_stats":
        await show_admin_stats(update, context)
    
    elif data == "admin_balances":
        await show_balance_management(update, context)
    
    elif data.startswith("admin_event_"):
        event_id = int(data.split("_")[2])
        await show_event_management(update, context, event_id)
    
    elif data.startswith("admin_finish_"):
        event_id = int(data.split("_")[2])
        await show_finish_event(update, context, event_id)
    
    elif data.startswith("admin_outcome_"):
        parts = data.split("_")
        event_id = int(parts[2])
        outcome_id = int(parts[3])
        await set_winning_outcome(update, context, event_id, outcome_id)

async def start_event_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание события"""
    text = (
        "➕ **Создание нового события**\n\n"
        "Для создания события отправьте сообщение в формате:\n\n"
        "`/create_event Название события | Описание | ДД.ММ.ГГГГ ЧЧ:ММ | Исход1:Коэф1 | Исход2:Коэф2 | ...`\n\n"
        "**Пример:**\n"
        "`/create_event Матч Спартак - ЦСКА | Футбольный матч | 25.12.2024 19:00 | Победа Спартака:2.1 | Ничья:3.2 | Победа ЦСКА:2.8`"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_events_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать управление событиями"""
    events = await get_active_events()
    
    if not events:
        text = "📋 **Управление событиями**\n\n❌ Нет активных событий"
        keyboard = [
            [InlineKeyboardButton("➕ Создать событие", callback_data="admin_create_event")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_menu")]
        ]
    else:
        text = "📋 **Управление событиями:**\n\n"
        keyboard = []
        
        for event in events:
            status_emoji = "🔴" if event.status == EventStatus.LIVE else "🟡"
            text += f"{status_emoji} {event.title} - {event.start_time.strftime('%d.%m %H:%M')}\n"
            keyboard.append([InlineKeyboardButton(
                f"⚙️ {event.title}",
                callback_data=f"admin_event_{event.id}"
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Создать событие", callback_data="admin_create_event")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_event_management(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    """Показать управление конкретным событием"""
    event = await get_event_by_id(event_id)
    
    if not event:
        await update.callback_query.edit_message_text("❌ Событие не найдено")
        return
    
    # Подсчитываем статистику ставок
    total_bets = len(event.bets)
    total_amount = sum(bet.amount for bet in event.bets)
    
    text = (
        f"⚙️ **Управление событием**\n\n"
        f"🏆 **{event.title}**\n"
        f"📅 {event.start_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"📝 {event.description}\n"
        f"📊 Статус: {event.status.value}\n\n"
        f"💰 **Статистика ставок:**\n"
        f"Всего ставок: {total_bets}\n"
        f"Общая сумма: {total_amount:.2f} единиц\n\n"
        f"🎯 **Исходы:**\n"
    )
    
    keyboard = []
    
    for outcome in event.outcomes:
        outcome_bets = len([bet for bet in event.bets if bet.outcome_id == outcome.id])
        outcome_amount = sum(bet.amount for bet in event.bets if bet.outcome_id == outcome.id)
        
        status_text = ""
        if outcome.is_winning is True:
            status_text = " ✅"
        elif outcome.is_winning is False:
            status_text = " ❌"
        
        text += (
            f"• {outcome.title} (коэф. {outcome.odds:.2f}){status_text}\n"
            f"  Ставок: {outcome_bets}, Сумма: {outcome_amount:.2f}\n"
        )
    
    # Кнопки управления
    if event.status == EventStatus.UPCOMING:
        keyboard.append([InlineKeyboardButton("🔴 Начать событие", callback_data=f"admin_start_{event_id}")])
    
    if event.status in [EventStatus.UPCOMING, EventStatus.LIVE]:
        keyboard.append([InlineKeyboardButton("🏁 Завершить событие", callback_data=f"admin_finish_{event_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 К событиям", callback_data="admin_manage_events")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_finish_event(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    """Показать завершение события"""
    event = await get_event_by_id(event_id)
    
    if not event:
        await update.callback_query.edit_message_text("❌ Событие не найдено")
        return
    
    text = (
        f"🏁 **Завершение события**\n\n"
        f"🏆 {event.title}\n\n"
        f"Выберите выигрышный исход:"
    )
    
    keyboard = []
    
    for outcome in event.outcomes:
        keyboard.append([InlineKeyboardButton(
            f"✅ {outcome.title}",
            callback_data=f"admin_outcome_{event_id}_{outcome.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"admin_event_{event_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def set_winning_outcome(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, outcome_id: int):
    """Установить выигрышный исход и произвести выплаты"""
    from src.database import DATABASE_URL
    
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        
        # Получаем событие
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            await update.callback_query.edit_message_text("❌ Событие не найдено")
            return
        
        # Устанавливаем выигрышный исход
        for outcome in event.outcomes:
            if outcome.id == outcome_id:
                outcome.is_winning = True
            else:
                outcome.is_winning = False
        
        # Завершаем событие
        event.status = EventStatus.FINISHED
        
        # Обрабатываем ставки
        winning_bets = []
        losing_bets = []
        
        for bet in event.bets:
            if bet.outcome_id == outcome_id:
                bet.status = BetStatus.WON
                winning_bets.append(bet)
                # Выплачиваем выигрыш
                await update_user_balance(bet.user_id, bet.potential_win)
            else:
                bet.status = BetStatus.LOST
                losing_bets.append(bet)
        
        db.commit()
        
        # Статистика выплат
        total_payout = sum(bet.potential_win for bet in winning_bets)
        total_lost = sum(bet.amount for bet in losing_bets)
        
        winning_outcome = db.query(Outcome).filter(Outcome.id == outcome_id).first()
        
        text = (
            f"✅ **Событие завершено!**\n\n"
            f"🏆 {event.title}\n"
            f"🎯 Выигрышный исход: {winning_outcome.title}\n\n"
            f"📊 **Результаты:**\n"
            f"Выигрышных ставок: {len(winning_bets)}\n"
            f"Проигрышных ставок: {len(losing_bets)}\n"
            f"Общие выплаты: {total_payout:.2f} единиц\n"
            f"Прибыль дома: {total_lost - total_payout:.2f} единиц"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 К событиям", callback_data="admin_manage_events")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику для админа"""
    from src.database import DATABASE_URL, User, Bet
    
    if DATABASE_URL.startswith('sqlite'):
        db = get_db()
        
        # Общая статистика
        total_users = db.query(User).count()
        total_bets = db.query(Bet).count()
        total_bet_amount = db.query(db.func.sum(Bet.amount)).scalar() or 0
        total_payouts = db.query(db.func.sum(Bet.potential_win)).filter(Bet.status == BetStatus.WON).scalar() or 0
        
        # Активные пользователи (с балансом > 0)
        active_users = db.query(User).filter(User.balance > 0).count()
        
        # Прибыль дома
        house_profit = total_bet_amount - total_payouts
        
        text = (
            f"📊 **Статистика системы**\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"🟢 Активных пользователей: {active_users}\n\n"
            f"🎯 Всего ставок: {total_bets}\n"
            f"💰 Общая сумма ставок: {total_bet_amount:.2f}\n"
            f"💸 Общие выплаты: {total_payouts:.2f}\n"
            f"🏦 Прибыль дома: {house_profit:.2f}\n\n"
            f"📈 Маржа: {(house_profit/total_bet_amount*100):.1f}%" if total_bet_amount > 0 else "📈 Маржа: 0%"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_balance_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать управление балансами"""
    text = (
        f"💰 **Управление балансами**\n\n"
        f"Для изменения баланса пользователя отправьте команду:\n\n"
        f"`/balance_add USER_ID AMOUNT` - добавить средства\n"
        f"`/balance_sub USER_ID AMOUNT` - списать средства\n\n"
        f"**Пример:**\n"
        f"`/balance_add 123456789 100` - добавить 100 единиц пользователю 123456789"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# Команды для создания событий и управления балансами
async def create_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда создания события"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Неверный формат. Используйте:\n"
            "/create_event Название | Описание | ДД.ММ.ГГГГ ЧЧ:ММ | Исход1:Коэф1 | Исход2:Коэф2"
        )
        return
    
    try:
        # Парсим аргументы
        full_text = " ".join(context.args)
        parts = [part.strip() for part in full_text.split("|")]
        
        if len(parts) < 4:
            raise ValueError("Недостаточно параметров")
        
        title = parts[0]
        description = parts[1]
        datetime_str = parts[2]
        outcomes_data = parts[3:]
        
        # Парсим дату и время
        start_time = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
        start_time = start_time.replace(tzinfo=timezone.utc)
        
        # Создаем событие
        event = await create_event(title, description, start_time, user_id)
        
        # Создаем исходы
        from src.database import DATABASE_URL, Outcome
        
        if DATABASE_URL.startswith('sqlite'):
            db = get_db()
            
            for outcome_data in outcomes_data:
                outcome_parts = outcome_data.split(":")
                if len(outcome_parts) != 2:
                    continue
                
                outcome_title = outcome_parts[0].strip()
                outcome_odds = float(outcome_parts[1].strip())
                
                outcome = Outcome(
                    event_id=event.id,
                    title=outcome_title,
                    odds=outcome_odds
                )
                db.add(outcome)
            
            db.commit()
        
        await update.message.reply_text(
            f"✅ Событие '{title}' успешно создано!\n"
            f"📅 Начало: {start_time.strftime('%d.%m.%Y %H:%M')}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при создании события: {str(e)}")

async def balance_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда добавления баланса"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("❌ Используйте: /balance_add USER_ID AMOUNT")
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = float(context.args[1])
        
        success = await update_user_balance(target_user_id, amount)
        
        if success:
            await update.message.reply_text(f"✅ Баланс пользователя {target_user_id} увеличен на {amount:.2f} единиц")
        else:
            await update.message.reply_text(f"❌ Пользователь {target_user_id} не найден")
            
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Используйте числа.")

async def balance_sub_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда списания баланса"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("❌ Используйте: /balance_sub USER_ID AMOUNT")
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = float(context.args[1])
        
        success = await update_user_balance(target_user_id, -amount)
        
        if success:
            await update.message.reply_text(f"✅ Баланс пользователя {target_user_id} уменьшен на {amount:.2f} единиц")
        else:
            await update.message.reply_text(f"❌ Пользователь {target_user_id} не найден")
            
    except ValueError:
        await update.message.reply_text("❌ Неверный формат. Используйте числа.")
