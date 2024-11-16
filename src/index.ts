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

        // Отправляем запрос напрямую через axios
        const response = await fetch(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/sendMessage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                chat_id: ctx.chat!.id,
                text: "Поддержать канал на 20 звёзд!",
                parse_mode: "HTML",
                star_params: {
                    star_count: 20,
                    is_premium: false
                }
            })
        });

        const data = await response.json();
        console.log('Ответ API:', data);

    } catch (error) {
        console.error('Ошибка при создании платежа:', error);
        await ctx.reply('Произошла ошибка при создании платежа. Попробуйте позже.');
    }
});

// Обработчик получения звезды
bot.on('message_reaction', async (ctx) => {
    try {
        console.log('Получена реакция:', ctx.update);
        await ctx.reply('🌟 Спасибо за вашу поддержку! 🌟');
    } catch (error) {
        console.error('Ошибка при обработке платежа:', error);
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