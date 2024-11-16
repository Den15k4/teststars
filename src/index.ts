import { Telegraf, Context } from 'telegraf';
import dotenv from 'dotenv';

dotenv.config();

if (!process.env.BOT_TOKEN) {
    throw new Error('BOT_TOKEN is required in .env file');
}

const bot = new Telegraf(process.env.BOT_TOKEN);

// Обработчик команды /start
bot.command('start', async (ctx) => {
    try {
        await ctx.reply(
            '👋 Привет! Я тестовый бот для оплаты через Telegram Stars.\n⭐️ Нажмите кнопку, чтобы поддержать!', 
            {
                reply_markup: {
                    inline_keyboard: [[{
                        text: 'Оплатить 20 ⭐️',
                        callback_data: 'buy_stars'
                    }]]
                }
            }
        );
    } catch (error) {
        console.error('Ошибка в команде start:', error);
        await ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
    }
});

// Обработчик нажатия кнопки
bot.action('buy_stars', async (ctx) => {
    try {
        await ctx.answerCbQuery();
        
        // Создаем invoice для звезд, как в Python примере
        const invoice = {
            chat_id: ctx.chat!.id,
            title: "Поддержка канала",
            description: "Поддержать канал на 20 звёзд!",
            payload: "channel_support",
            provider_token: "", // для звезд оставляем пустым
            currency: "XTR",
            prices: [{
                label: "XTR",
                amount: 20
            }]
        };

        // Отправляем через прямой вызов API
        await ctx.telegram.callApi('createInvoice', invoice);

    } catch (error) {
        console.error('Ошибка при создании платежа:', error);
        await ctx.reply('Произошла ошибка при создании платежа. Попробуйте позже.');
    }
});

// Обработчик пре-чекаута
bot.on('pre_checkout_query', async (ctx) => {
    try {
        await ctx.answerPreCheckoutQuery(true);
    } catch (error) {
        console.error('Ошибка при пре-чекауте:', error);
    }
});

// Обработчик успешного платежа
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