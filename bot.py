import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile, ContentType
from googletrans import Translator
from gtts import gTTS
from config import API_TOKEN

# Логирование
logging.basicConfig(level=logging.INFO)

# Создаем папку img, если она не существует
if not os.path.exists('img'):
    os.makedirs('img')

# Инициализация бота
bot = Bot(token=API_TOKEN)

# Инициализация диспетчера и роутера
dp = Dispatcher(storage=MemoryStorage())
router = Router()

translator = Translator()

# Определение состояний
class VoiceState(StatesGroup):
    waiting_for_text = State()

# Команда /start
@router.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я твой бот-помощник. Отправь мне текст для перевода, фото для сохранения, или используй /voice для голосового сообщения.")

# Команда /help
@router.message(Command('help'))
async def send_help(message: types.Message):
    help_text = (
        "Я умею выполнять следующие команды:\n"
        "/start - Начать общение с ботом\n"
        "/help - Получить справку\n"
        "/voice - Получить голосовое сообщение\n"
        "Отправь мне любое сообщение для перевода на английский язык.\n"
        "Отправь фото, чтобы я сохранил его."
    )
    await message.answer(help_text)

# Обработка фото
@router.message(F.content_type == ContentType.PHOTO)
async def handle_photos(message: types.Message):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    photo_path = f'img/{photo.file_id}.jpg'
    await bot.download_file(file_path, photo_path)
    await message.answer("Фото сохранено!")

# Обработка команды /voice и запроса на ввод текста
@router.message(Command('voice'))
async def request_text_for_voice(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, введите текст для озвучивания:")
    await state.set_state(VoiceState.waiting_for_text)

# Отправка голосового сообщения с озвучкой текста
@router.message(VoiceState.waiting_for_text)
async def send_voice_message(message: types.Message, state: FSMContext):
    user_text = message.text
    # Определяем язык текста
    lang = 'ru' if any('а' <= char <= 'я' for char in user_text.lower()) else 'en'
    tts = gTTS(text=user_text, lang=lang)
    tts.save("voice.ogg")
    voice = FSInputFile("voice.ogg")
    await message.answer_voice(voice)
    os.remove("voice.ogg")
    await state.clear()

# Перевод текста на английский язык
@router.message(F.text)
async def translate_text(message: types.Message):
    translated = translator.translate(message.text, dest='en')
    await message.answer(translated.text)

# Запуск бота
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
