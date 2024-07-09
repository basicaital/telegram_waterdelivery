from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message
import keyboard.kb
import config
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from common.text import welcome_text, logo_id, help_text
from keyboard.kb import support_rm, user_kb
from Filters.filter import is_admin

user_router = Router()
bot = Bot(token=config.TOKEN)


@user_router.message(F.text.lower() == "запустить бота")
@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer_photo(photo=logo_id, caption=welcome_text,
                               reply_markup=user_kb.as_markup(resize_keyboard=True,
                                                              input_field_placeholder="Утоли жажду"))
    if is_admin(message.from_user.id):
        await message.answer(
            f"<b>Вы авторизовались, как администратор</b>!",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard.kb.admin_kb
        )


@user_router.message(F.text.lower() == "инструкция")
@user_router.message(Command('help'))
async def help_handler(message: Message):
    await message.answer(help_text)


@user_router.message(F.text.lower() == "поддержка")
@user_router.message(Command("support"))
async def support_handler(message: Message):
    await message.answer("Если у вас возникли вопросы нажмите на кнопку ниже", reply_markup=support_rm)


# @user_router.callback_query(F.data == "to_support")
# async def to_support(query: CallbackQuery):
#     await query.message.forward(chat_id=config.FEED_BACK_ID)
# @user_router.message(F.sticker)
# async def echo(message: Message):
#     await message.answer(message.sticker.file_id)
# @user_router.message(F.voice)
# async def voice(message: Message):
#     await message.answer(message.voice.file_id)
@user_router.message(F.text.lower() == "канал")
async def channel(message: Message):
    await message.answer_photo(
        photo='AgACAgIAAxkBAAIOe2Z_fUYTCtD9HelWf3RZujo6i-5zAALh2jEbo-D5S3qwu2RTZTBPAQADAgADeQADNQQ',
        caption="Подписывайтесь на наш канал, чтобы не пропустить выгодные акции",
        reply_markup=keyboard.kb.build_info_kb())


@user_router.message(F.photo)
async def photo(message: Message):
    await message.answer(message.photo[-1].file_id)


@user_router.message(F.text.lower() == "админ")
async def show_admin(message: Message):
    await message.reply(str(config.ADMIN_ID))
