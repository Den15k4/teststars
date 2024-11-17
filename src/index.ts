import { Telegraf, Context } from 'telegraf';
import dotenv from 'dotenv';
import { InlineKeyboardButton } from 'telegraf/types';

dotenv.config();

if (!process.env.BOT_TOKEN) {
    throw new Error('BOT_TOKEN is required in .env file');
}

const bot = new Telegraf(process.env.BOT_TOKEN);

// Обработчик команды /start
bot.command('start', async (ctx) => {
    try {
        // Отправляем приветственное сообщение
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

        // Отправляем два сообщения: первое с кнопкой donate и второе с описанием
        const keyboard = {
            inline_keyboard: [[
                {
                    text: '⭐️ Поддержать звездой',
                    url: `https://t.me/${(await bot.telegram.getMe()).username}/donate`
                } as InlineKeyboardButton
            ]]
        };

        await ctx.reply('Поддержать канал на 20 звёзд!', {
            reply_markup: keyboard
        });

    } catch (error) {
        console.error('Ошибка при создании платежа:', error);
        await ctx.reply('Произошла ошибка при создании платежа. Попробуйте позже.');
    }
});

// Обработчик успешного платежа (для звезд это message_reaction)
bot.on('message_reaction', (ctx) => {
    try {
        console.log('Получена реакция:', ctx.update);
        ctx.reply('🌟 Спасибо за вашу поддержку! 🌟');
    } catch (error) {
        console.error('Ошибка при обработке реакции:', error);
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