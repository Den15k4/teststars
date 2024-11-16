import { Telegraf, Context } from 'telegraf';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

if (!process.env.BOT_TOKEN) {
    throw new Error('BOT_TOKEN is required in .env file');
}

const bot = new Telegraf(process.env.BOT_TOKEN);
const TELEGRAM_API = `https://api.telegram.org/bot${process.env.BOT_TOKEN}`;

interface LabeledPrice {
    label: string;
    amount: number;
}

// Функция для создания платежной клавиатуры
function getPaymentKeyboard() {
    return {
        inline_keyboard: [
            [{
                text: "Оплатить 20 ⭐️",
                pay: true
            }]
        ]
    };
}

// Обработчик команды /start
bot.command('start', async (ctx) => {
    try {
        console.log('Получена команда /start от пользователя:', ctx.from?.id);
        
        const prices: LabeledPrice[] = [
            { label: "XTR", amount: 20 }
        ];

        // Отправляем invoice
        await ctx.telegram.sendInvoice(ctx.chat.id, {
            title: "Поддержка канала",
            description: "Поддержать канал на 20 звёзд!",
            payload: "channel_support",
            currency: "XTR",
            prices: prices,
            provider_token: "", // Для Telegram Stars оставляем пустым
            reply_markup: getPaymentKeyboard()
        });
        
    } catch (error) {
        console.error('Ошибка в команде start:', error);
        if (axios.isAxiosError(error)) {
            console.error('Ответ API:', error.response?.data);
        }
        await ctx.reply('Произошла ошибка. Пожалуйста, попробуйте позже.');
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

// Команда /paysupport
bot.command('paysupport', async (ctx) => {
    await ctx.reply(
        'Добровольные пожертвования не подразумевают возврат средств, ' +
        'однако, если вы очень хотите вернуть средства - свяжитесь с нами.'
    );
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