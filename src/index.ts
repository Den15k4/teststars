import { Telegraf } from 'telegraf';
import dotenv from 'dotenv';

dotenv.config();

if (!process.env.BOT_TOKEN) {
    throw new Error('BOT_TOKEN is required in .env file');
}

const bot = new Telegraf(process.env.BOT_TOKEN);

// Обработчик команды /start
bot.command('start', async (ctx) => {
    try {
        console.log('Получена команда /start от пользователя:', ctx.from?.id);
        
        // Используем прямой метод API для отправки сообщения с возможностью поставить звезду
        await ctx.telegram.raw('sendMessage', {
            chat_id: ctx.chat.id,
            text: '👋 Привет! Я тестовый бот для оплаты через Telegram Stars.',
            can_be_starred: true
        });
        
        console.log('Сообщение с возможностью звезды отправлено пользователю:', ctx.from?.id);
    } catch (error) {
        console.error('Ошибка в команде start:', error);
        await ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
    }
});

// Обработчик получения звезды
bot.on('message_reaction', async (ctx) => {
    try {
        console.log('Получена реакция:', ctx.messageReaction);
        if (ctx.messageReaction?.type === 'star') {
            await ctx.reply('🌟 Спасибо за звезду!');
        }
    } catch (error) {
        console.error('Ошибка при обработке реакции:', error);
    }
});

// Обработка ошибок
bot.catch((err, ctx) => {
    console.error('Ошибка в боте:', err);
    return ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
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