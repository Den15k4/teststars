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

        const message = {
            chat_id: ctx.chat.id,
            text: '👋 Привет! Я тестовый бот для оплаты через Telegram Stars.',
            entities: [
                {
                    type: 'stars',
                    offset: 0,
                    length: 1,
                    star_params: {
                        star_price: {
                            amount: 100,
                            currency: "RUB"
                        }
                    }
                }
            ],
            parse_mode: 'HTML',
            parse_entities: true
        };

        // Сначала логируем, что отправляем
        console.log('Отправляем сообщение:', JSON.stringify(message, null, 2));
        
        const response = await axios.post(`${TELEGRAM_API}/sendMessage`, message);
        
        // Логируем ответ
        console.log('Ответ API:', response.data);
        
    } catch (error) {
        console.error('Ошибка в команде start:', error);
        if (axios.isAxiosError(error)) {
            console.error('Ответ API:', error.response?.data);
            console.error('Данные запроса:', error.config?.data);
        }
        await ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
    }
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