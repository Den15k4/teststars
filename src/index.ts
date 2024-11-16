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
            '👋 Привет! Я тестовый бот для оплаты через Telegram Stars.\n\n' +
            '⭐️ Нажми на кнопку ниже, чтобы отправить 1 звезду!',
            {
                reply_markup: {
                    inline_keyboard: [
                        [{
                            text: '⭐️ Поддержать 1 звездой',
                            url: 'tg://stars/subscribe?id=teststarsbot'
                        }]
                    ]
                }
            }
        );
    } catch (error) {
        console.error('Ошибка в команде start:', error);
        await ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
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