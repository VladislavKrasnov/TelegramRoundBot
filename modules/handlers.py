import os
import tempfile
import logging

from aiogram import types
from aiogram.filters import Command
from aiogram.types import FSInputFile

from bot_loader import bot, dp
from .database import register_user, get_profile, increment_video_note
from .video_processing import process_video

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

@dp.message(Command("start"))
async def handle_start(msg: types.Message):
    await register_user(msg.from_user.id)
    await msg.answer(
        "Отправьте видео для создания кружка. "
        "Используйте /help для справки."
    )

@dp.message(Command("profile"))
async def handle_profile(msg: types.Message):
    await register_user(msg.from_user.id)
    profile = await get_profile(msg.from_user.id)
    await msg.answer(
        f"🆔 ID: <code>{profile['id']}</code>\n\n"
        f"🎞 Создано кружков: <code>{profile['video_note_count']}</code>",
        parse_mode="HTML"
    )

@dp.message(Command("help"))
async def handle_help(msg: types.Message):
    await msg.answer(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/profile - Статистика\n"
        "/change_size - Как уменьшить вес видео\n"
        "/forward - Как переслать кружок от своего имени\n"
        "/help - Справка\n\n"
        "Отправьте видео для обработки."
    )

@dp.message(Command("change_size"))
async def handle_change_size(msg: types.Message):
    photo_file_id = "AgACAgIAAxkDAAIBpmg5drP-7WNiacYcsP_dh70KzYA7AAIw8jEbM3vRSQxJLKL1WXcuAQADAgADdwADNgQ"
    caption = (
        "Для уменьшения размера видео, пожалуйста, воспользуйтесь функцией "
        "снижения качества в видеоредакторе вашего устройства перед отправкой."
    )
    await msg.answer_photo(photo_file_id, caption=caption)

@dp.message(Command("forward"))
async def handle_forward(msg: types.Message):
    video_file_id = "BAACAgIAAxkDAAIBvmg5edSXijhfAkNzfFhKflR2iwhhAAIfcQACiT_QSRMH1kpwJ7OUNgQ"
    caption = (
        "Как переслать кружок от своего имени (без пометки \"переслано от\"):\n\n"
        "1. Выберите кружок, затем нажмите \"Переслать\".\n"
        "2. Выберите, кому отправить.\n"
        "3. Перед отправкой, в окне чата, коснитесь пересылаемого кружка (он будет над полем для ввода текста).\n"
        "4. В появившемся меню выберите \"Скрыть имя отправителя\".\n"
        "5. Теперь можно отправлять."
    )
    await msg.answer_video(
        video=video_file_id,
        caption=caption
    )

@dp.message(lambda m: m.video)
async def handle_video(msg: types.Message):
    status_message = None
    temp_files = []

    try:
        if msg.video.file_size > MAX_FILE_SIZE_BYTES:
            video_size_mb = msg.video.file_size / 1024 / 1024
            await msg.answer(
                f"❌ Размер видео превышает допустимый лимит.\n"
                f"Максимальный размер: 20 МБ. Размер вашего видео: {video_size_mb:.2f} МБ.\n\n"
                f"Инструкцию по уменьшению размера видео можно найти здесь: /change_size"
            )
            logger.warning(
                f"Video too large from user {msg.from_user.id}. Size: {video_size_mb:.2f}MB"
            )
            return

        status_message = await msg.answer("📥 Загрузка...")
        await register_user(msg.from_user.id)

        file = await bot.get_file(msg.video.file_id)
        file_data_stream = await bot.download_file(file.file_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input_file:
            temp_input_file.write(file_data_stream.read())
            input_path = temp_input_file.name
            temp_files.append(input_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_output_file:
            output_path = temp_output_file.name
            temp_files.append(output_path)

        await status_message.edit_text("📦 Обработка...")
        await process_video(input_path, output_path)

        await status_message.edit_text("📤 Выгрузка...")
        video_note_to_send = FSInputFile(output_path)
        await msg.answer_video_note(video_note_to_send)
        await increment_video_note(msg.from_user.id)

    except ValueError as e:
        await msg.answer(f"❌ Ошибка: {str(e)}")
        logger.warning(f"ValueError in handle_video for user {msg.from_user.id}: {str(e)}")
    except RuntimeError as e:
        await msg.answer(f"❌ Ошибка обработки видео: {str(e).splitlines()[-1]}")
        logger.error(f"RuntimeError in handle_video for user {msg.from_user.id}: {str(e)}", exc_info=True)
    except Exception as e:
        await msg.answer("❌ Произошла непредвиденная ошибка при обработке видео.")
        logger.error(f"Unhandled exception in handle_video for user {msg.from_user.id}: {str(e)}", exc_info=True)
    finally:
        if status_message:
            try:
                await status_message.delete()
            except Exception as e:
                logger.error(f"Error deleting status message: {str(e)}")
        
        for path in temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary file {path}: {str(e)}")

@dp.message()
async def handle_unknown(msg: types.Message):
    await msg.answer("Неизвестная команда или тип сообщения. Используйте /help для справки.")
