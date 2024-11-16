import { Telegraf } from 'telegraf';
import dotenv from 'dotenv';

dotenv.config();

const bot = new Telegraf(process.env.BOT_TOKEN!);

// Приветственное сообщение с кнопкой оплаты
bot.command('start', async (ctx) => {
    await ctx.reply(
        'Привет! Я тестовый бот для оплаты через Telegram Stars.',
        {
            reply_markup: {
                inline_keyboard: [
                    [{ text: '⭐️ Купить за 1 звезду', url: 'tg://star?id=YOUR_BOT_USERNAME' }]
                ]
            }
        }
    );
});

bot.launch().then(() => {
    console.log('Бот запущен');
});

// Graceful shutdown
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));