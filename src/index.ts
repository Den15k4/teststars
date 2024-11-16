import { Telegraf, Context } from 'telegraf';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

if (!process.env.BOT_TOKEN) {
    throw new Error('BOT_TOKEN is required in .env file');
}

const bot = new Telegraf(process.env.BOT_TOKEN);
const TELEGRAM_API = `https://api.telegram.org/bot${process.env.BOT_TOKEN}`;

// Обработчик команды /start
bot.command('start', async (ctx) => {
    try {
        console.log('Получена команда /start от пользователя:', ctx.from?.id);
        
        // Используем формат данных как в aiogram
        const messageData = {
            chat_id: ctx.chat.id,
            text: '👋 Привет! Я тестовый бот для оплаты через Telegram Stars.\n\n⭐️ Нажмите на кнопку со звездочкой сверху, чтобы отправить звезду!',
            params: {
                message_thread_id: undefined,
                parse_mode: undefined,
                entities: undefined,
                disable_web_page_preview: undefined,
                disable_notification: false,
                protect_content: undefined,
                reply_to_message_id: undefined,
                allow_sending_without_reply: undefined,
                reply_markup: undefined,
                star_params: {
                    star_price: {
                        amount: 100,
                        currency: "RUB"
                    }
                }
            }
        };
        
        await axios.post(`${TELEGRAM_API}/sendMessage`, messageData);
        
        console.log('Сообщение отправлено пользователю:', ctx.from?.id);
    } catch (error) {
        console.error('Ошибка в команде start:', error);
        if (axios.isAxiosError(error)) {
            console.error('Ответ API:', error.response?.data);
        }
        await ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
    }
});

// Обработчик получения звезды
bot.on('message_reaction', async (ctx: Context) => {
    try {
        console.log('Получена реакция:', ctx.update);
        // Здесь будет обработка успешной оплаты звездой
    } catch (error) {
        console.error('Ошибка при обработке реакции:', error);
    }
});

// Обработка ошибок
bot.catch((err: unknown) => {
    console.error('Ошибка в боте:', err);
});

// Запуск бота
bot.launch().then(() => {
    console.log('Бот успешно запущен!');
    console.log('Имя бота:', bot.botInfo?.username);
}).catch((err) => {
    console.error('Ошибка при запуске бота:', err);
});

// Graceful shutdown
process.once('SIGINT', () => {
    console.log('Получен сигнал SIGINT');
    bot.stop('SIGINT');
});
process.once('SIGTERM', () => {
    console.log('Получен сигнал SIGTERM');
    bot.stop('SIGTERM');
});