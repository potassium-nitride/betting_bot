"""
Модуль для обработки ставок
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.src.database import (
    get_event_by_id, get_user, create_bet, get_user_bets,
    BetStatus, EventStatus
) # Исправлен импорт
from app.config.settings import MIN_BET_AMOUNT, MAX_BET_AMOUNT

async def bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Обработчик ставок"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if callback_data.startswith("event_"):
        # Показать исходы события
        event_id = int(callback_data.split("_")[1])
        await show_event_outcomes(update, context, event_id)
    
    elif callback_data.startswith("outcome_"):
        # Начать процесс ставки на исход
        parts = callback_data.split("_")
        event_id = int(parts[1])
        outcome_id = int(parts[2])
        await start_betting_process(update, context, event_id, outcome_id)

async def show_event_outcomes(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int):
    """Показать исходы события"""
    event = await get_event_by_id(event_id)
    
    if not event:
        await update.callback_query.edit_message_text("❌ Событие не найдено")
        return
    
    if event.status != EventStatus.UPCOMING:
        await update.callback_query.edit_message_text("❌ Ставки на это событие больше не принимаются")
        return
    
    text = (
        f"🏆 **{event.title}**\n\n"
        f"📅 Начало: {event.start_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"📝 {event.description}\n\n"
        f"💰 **Доступные исходы:**\n\n"
    )
    
    keyboard = []
    
    for outcome in event.outcomes:
        text += f"• {outcome.title} - коэффициент {outcome.odds:.2f}\n"
        keyboard.append([InlineKeyboardButton(
            f"{outcome.title} ({outcome.odds:.2f})",
            callback_data=f"outcome_{event_id}_{outcome.id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к событиям", callback_data="events")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )

async def start_betting_process(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, outcome_id: int):
    """Начать процесс создания ставки"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Проверяем пользователя
    user = await get_user(user_id)
    if not user:
        await query.edit_message_text("❌ Пользователь не найден. Используйте /start для регистрации")
        return
    
    # Проверяем событие
    event = await get_event_by_id(event_id)
    if not event or event.status != EventStatus.UPCOMING:
        await query.edit_message_text("❌ Ставки на это событие больше не принимаются")
        return
    
    # Находим исход
    outcome = None
    for o in event.outcomes:
        if o.id == outcome_id:
            outcome = o
            break
    
    if not outcome:
        await query.edit_message_text("❌ Исход не найден")
        return
    
    # Сохраняем данные для ставки в контексте
    context.user_data['state'] = 'waiting_bet_amount'
    context.user_data['bet_event_id'] = event_id
    context.user_data['bet_outcome_id'] = outcome_id
    
    text = (
        f"💰 **Создание ставки**\n\n"
        f"🏆 Событие: {event.title}\n"
        f"🎯 Исход: {outcome.title}\n"
        f"📊 Коэффициент: {outcome.odds:.2f}\n\n"
        f"💳 Ваш баланс: {user.balance:.2f} единиц\n\n"
        f"💸 Введите сумму ставки (от {MIN_BET_AMOUNT} до {MAX_BET_AMOUNT}):"
    )
    
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="events")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def process_bet(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id: int, outcome_id: int, amount: float):
    """Обработать создание ставки"""
    user_id = update.effective_user.id
    
    # Валидация суммы
    if amount < MIN_BET_AMOUNT:
        await update.message.reply_text(f"❌ Минимальная сумма ставки: {MIN_BET_AMOUNT} единиц")
        return
    
    if amount > MAX_BET_AMOUNT:
        await update.message.reply_text(f"❌ Максимальная сумма ставки: {MAX_BET_AMOUNT} единиц")
        return
    
    # Проверяем пользователя и баланс
    user = await get_user(user_id)
    if not user:
        await update.message.reply_text("❌ Пользователь не найден")
        return
    
    if user.balance < amount:
        await update.message.reply_text(f"❌ Недостаточно средств. Ваш баланс: {user.balance:.2f} единиц")
        return
    
    # Получаем событие и исход
    event = await get_event_by_id(event_id)
    if not event or event.status != EventStatus.UPCOMING:
        await update.message.reply_text("❌ Ставки на это событие больше не принимаются")
        return
    
    outcome = None
    for o in event.outcomes:
        if o.id == outcome_id:
            outcome = o
            break
    
    if not outcome:
        await update.message.reply_text("❌ Исход не найден")
        return
    
    # Создаем ставку
    bet = await create_bet(user_id, event_id, outcome_id, amount, outcome.odds)
    
    if bet:
        text = (
            f"✅ **Ставка успешно создана!**\n\n"
            f"🏆 Событие: {event.title}\n"
            f"🎯 Исход: {outcome.title}\n"
            f"💰 Сумма ставки: {amount:.2f} единиц\n"
            f"📊 Коэффициент: {outcome.odds:.2f}\n"
            f"🎁 Потенциальный выигрыш: {bet.potential_win:.2f} единиц\n\n"
            f"💳 Новый баланс: {user.balance - amount:.2f} единиц"
        )
        
        keyboard = [
            [InlineKeyboardButton("💰 Мои ставки", callback_data="my_bets")],
            [InlineKeyboardButton("🎯 Другие события", callback_data="events")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Ошибка при создании ставки. Попробуйте еще раз.")

async def my_bets_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /mybets"""
    user_id = update.effective_user.id
    user_bets = await get_user_bets(user_id)
    
    if not user_bets:
        text = "💰 **Ваши ставки**\n\n❌ У вас пока нет ставок"
        keyboard = [
            [InlineKeyboardButton("🎯 Сделать ставку", callback_data="events")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
    else:
        text = "💰 **Ваши ставки:**\n\n"
        
        # Группируем ставки по статусу
        pending_bets = [bet for bet in user_bets if bet.status == BetStatus.PENDING]
        won_bets = [bet for bet in user_bets if bet.status == BetStatus.WON]
        lost_bets = [bet for bet in user_bets if bet.status == BetStatus.LOST]
        
        if pending_bets:
            text += "⏳ **В ожидании:**\n"
            for bet in pending_bets[-5:]:  # Показываем последние 5
                text += (
                    f"• {bet.event.title}\n"
                    f"  Исход: {bet.outcome.title}\n"
                    f"  Ставка: {bet.amount:.2f} (коэф. {bet.odds:.2f})\n"
                    f"  Потенциальный выигрыш: {bet.potential_win:.2f}\n\n"
                )
        
        if won_bets:
            text += "✅ **Выигранные:**\n"
            for bet in won_bets[-3:]:  # Показываем последние 3
                text += (
                    f"• {bet.event.title}\n"
                    f"  Выигрыш: {bet.potential_win:.2f} единиц\n\n"
                )
        
        if lost_bets:
            text += "❌ **Проигранные:**\n"
            for bet in lost_bets[-3:]:  # Показываем последние 3
                text += (
                    f"• {bet.event.title}\n"
                    f"  Потеря: {bet.amount:.2f} единиц\n\n"
                )
        
        # Статистика
        total_amount = sum(bet.amount for bet in user_bets)
        total_won = sum(bet.potential_win for bet in won_bets)
        profit = total_won - total_amount
        
        text += (
            f"📊 **Статистика:**\n"
            f"Всего ставок: {len(user_bets)}\n"
            f"Общая сумма: {total_amount:.2f}\n"
            f"Выигрыши: {total_won:.2f}\n"
            f"Прибыль/убыток: {profit:+.2f}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎯 Новая ставка", callback_data="events")],
            [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
