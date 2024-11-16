import { Telegraf, Context } from 'telegraf';
import axios from 'axios';
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
            '👋 Привет! Я тестовый бот для оплаты через Telegram Stars.',
            {
                reply_markup: {
                    inline_keyboard: [
                        [{
                            text: '⭐️ Поддержать звездой',
                            callback_data: 'give_star'
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

// Обработчик нажатия кнопки
bot.action('give_star', async (ctx) => {
    try {
        await ctx.answerCbQuery();
        
        // Отправляем сообщение с запросом звезды
        await ctx.reply('⭐️ Отправьте звезду в ответ на это сообщение');
        
    } catch (error) {
        console.error('Ошибка при обработке кнопки:', error);
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