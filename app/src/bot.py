"""
Основной файл Telegram-бота для ставок на спортивные события
"""
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
from config.settings import BOT_TOKEN, ADMIN_IDS
from src.database import init_db, get_user, create_user
from src.handlers import (
    start_handler, help_handler, profile_handler, 
    balance_handler, events_handler
)

from src.admin import admin_menu_handler, is_admin, create_event_command, balance_add_command, balance_sub_command
from src.betting import bet_handler, my_bets_handler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BettingBot:
    """Основной класс Telegram-бота для ставок"""
    
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Основные команды
        self.application.add_handler(CommandHandler("start", start_handler))
        self.application.add_handler(CommandHandler("help", help_handler))
        self.application.add_handler(CommandHandler("profile", profile_handler))
        self.application.add_handler(CommandHandler("balance", balance_handler))
        self.application.add_handler(CommandHandler("events", events_handler))
        self.application.add_handler(CommandHandler("mybets", my_bets_handler))
        
        # Админ команды
        self.application.add_handler(CommandHandler("admin", admin_menu_handler))
        self.application.add_handler(CommandHandler("create_event", create_event_command))
        self.application.add_handler(CommandHandler("balance_add", balance_add_command))
        self.application.add_handler(CommandHandler("balance_sub", balance_sub_command))
        
        # Обработчики callback запросов
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов от inline клавиатур"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data.startswith("bet_"):
            # Обработка ставок
            await bet_handler(update, context, data)
        elif data.startswith("admin_"):
            # Обработка админ команд
            if is_admin(user_id):
                await self.handle_admin_callback(update, context, data)
            else:
                await query.edit_message_text("❌ У вас нет прав администратора")
        elif data == "main_menu":
            await self.show_main_menu(update, context)
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Обработчик админ callback запросов"""
        from src.admin import handle_admin_callback
        await handle_admin_callback(update, context, data)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Проверяем, есть ли пользователь в базе
        user = await get_user(user_id)
        if not user:
            await update.message.reply_text(
                "Пожалуйста, сначала зарегистрируйтесь с помощью команды /start"
            )
            return
        
        # Обработка различных состояний пользователя
        user_state = context.user_data.get('state')
        
        if user_state == 'waiting_bet_amount':
            await self.process_bet_amount(update, context, text)
        else:
            await self.show_main_menu(update, context)
    
    async def process_bet_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE, amount_text: str):
        """Обработка суммы ставки"""
        try:
            amount = float(amount_text)
            event_id = context.user_data.get('bet_event_id')
            outcome_id = context.user_data.get('bet_outcome_id')
            
            from src.betting import process_bet
            await process_bet(update, context, event_id, outcome_id, amount)
            
            # Очищаем состояние
            context.user_data.clear()
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверная сумма. Пожалуйста, введите число."
            )
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное меню"""
        keyboard = [
            [InlineKeyboardButton("🎯 События", callback_data="events")],
            [InlineKeyboardButton("💰 Мои ставки", callback_data="my_bets")],
            [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton("💳 Баланс", callback_data="balance")],
        ]
        
        user_id = update.effective_user.id
        if is_admin(user_id):
            keyboard.append([InlineKeyboardButton("⚙️ Админ", callback_data="admin_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "🏠 Главное меню\n\nВыберите действие:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "🏠 Главное меню\n\nВыберите действие:",
                reply_markup=reply_markup
            )
    
    async def run_polling(self):
        """Запуск бота в режиме polling"""
        await init_db()
        logger.info("Бот запущен в режиме polling")
        await self.application.run_polling()
    
    async def run_webhook(self, webhook_url: str, port: int):
        """Запуск бота в режиме webhook"""
        await init_db()
        logger.info(f"Бот запущен в режиме webhook на порту {port}")
        await self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )

def main():
    """Главная функция запуска бота"""
    bot = BettingBot()
    
    # Запуск в режиме polling для локальной разработки
    asyncio.run(bot.run_polling())

if __name__ == "__main__":
    main()
