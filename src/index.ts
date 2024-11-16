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
        
        await axios.post(`${TELEGRAM_API}/sendMessage`, {
            chat_id: ctx.chat.id,
            text: '👋 Привет! Я тестовый бот для оплаты через Telegram Stars.\n\n⭐️ Нажмите на кнопку со звездочкой сверху, чтобы отправить звезду!',
            stars_watermark: true,
            stars_prices: [{
                amount: 100,
                currency: "RUB"
            }]
        });
        
        console.log('Сообщение отправлено пользователю:', ctx.from?.id);
    } catch (error) {
        console.error('Ошибка в команде start:', error);
        if (axios.isAxiosError(error)) {
            console.error('Ответ API:', error.response?.data);
            console.error('Запрос:', error.config?.data);
        }
        await ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
    }
});

// Обработчик получения звезды
bot.on('message_reaction', async (ctx: Context) => {
    try {
        console.log('Получена реакция:', ctx.update);
    } catch (error) {
        console.error('Ошибка при обработке реакции:', error);
    }
});

bot.catch((err: unknown) => {
    console.error('Ошибка в боте:', err);
});

bot.launch().then(() => {
    console.log('Бот успешно запущен!');
    console.log('Имя бота:', bot.botInfo?.username);
}).catch((err) => {
    console.error('Ошибка при запуске бота:', err);
});

process.once('SIGINT', () => {
    console.log('Получен сигнал SIGINT');
    bot.stop('SIGINT');
});
process.once('SIGTERM', () => {
    console.log('Получен сигнал SIGTERM');
    bot.stop('SIGTERM');
});