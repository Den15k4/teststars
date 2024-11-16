import { Telegraf, Context } from 'telegraf';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

if (!process.env.BOT_TOKEN) {
    throw new Error('BOT_TOKEN is required in .env file');
}

const bot = new Telegraf(process.env.BOT_TOKEN);

interface LabeledPrice {
    label: string;
    amount: number;
}

// Обработчик команды /start
bot.command('start', async (ctx) => {
    try {
        console.log('Получена команда /start от пользователя:', ctx.from?.id);

        const chatId = ctx.chat.id;
        const text = '👋 Привет! Я тестовый бот для оплаты через Telegram Stars.\n⭐️ Нажмите кнопку, чтобы поддержать!';

        // Используем прямой вызов API через axios
        await axios.post(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/sendMessage`, {
            chat_id: chatId,
            text: text,
            reply_markup: {
                inline_keyboard: [[
                    {
                        text: "Оплатить 20 ⭐️",
                        callback_data: "pay_stars"
                    }
                ]]
            }
        });
        
    } catch (error) {
        console.error('Ошибка в команде start:', error);
        if (axios.isAxiosError(error)) {
            console.error('Ответ API:', error.response?.data);
        }
        await ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
    }
});

// Обработчик нажатия кнопки оплаты
bot.action('pay_stars', async (ctx) => {
    try {
        await ctx.answerCbQuery();

        // Отправляем сообщение для покупки звезд
        const response = await axios.post(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/sendMessage`, {
            chat_id: ctx.chat?.id,
            text: 'Поддержать канал на 20 звёзд!',
            provider_data: {
                currency: "XTR",
                amount: 20
            }
        });

        console.log('Ответ API:', response.data);
    } catch (error) {
        console.error('Ошибка при создании платежа:', error);
        if (axios.isAxiosError(error)) {
            console.error('Ответ API:', error.response?.data);
        }
        await ctx.reply('Произошла ошибка при создании платежа. Попробуйте позже.');
    }
});

// Обработчик успешной оплаты
bot.on('successful_payment', async (ctx) => {
    try {
        await ctx.reply('🌟 Спасибо за вашу поддержку! 🌟');
    } catch (error) {
        console.error('Ошибка при обработке успешного платежа:', error);
    }
});

// Запуск бота
bot.launch().then(() => {
    console.log('Бот успешно запущен!');
}).catch((err) => {
    console.error('Ошибка при запуске бота:', err);
});

// Graceful shutdown
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));