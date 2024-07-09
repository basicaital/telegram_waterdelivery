from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import (Message, CallbackQuery,
                           InlineKeyboardMarkup, InlineKeyboardButton,
                           ReplyKeyboardMarkup, KeyboardButton,
                           InlineQuery, InlineQueryResultArticle,
                           InputTextMessageContent)

import config
from database.requests import register_user, create_order, get_last_address
from handlers.admin import notify_admin
from keyboard.kb import get_delivery_time_keyboard, user_kb
from scripts.utils import get_bottle_word
from aiogram.enums import ChatAction

order_router = Router()
PRICE_PER_BOTTLE = 130


class OrderState(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_address = State()
    waiting_for_phone = State()
    waiting_for_time = State()
    confirm_order = State()


@order_router.message(StateFilter(None), Command('order'))
@order_router.message(F.text.casefold() == "заказать воду")
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Введите количество бутылей, которое вы хотите заказать?", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="2"), KeyboardButton(text="3"), KeyboardButton(text="4")],
            [KeyboardButton(text="Отменить")]
        ], resize_keyboard=True, input_field_placeholder="Вы можете отменить действия нажав на кнопку ниже"))
    await message.answer_sticker(config.STICKER_ID)
    await state.set_state(OrderState.waiting_for_quantity)


@order_router.message(StateFilter(None), Command(commands=["cancel"]))
@order_router.message(default_state, F.text.lower() == "отменить")
async def cmd_cancel_no_state(message: Message, state: FSMContext):
    # Стейт сбрасывать не нужно, удалим только данные
    await state.set_data({})
    await message.answer(
        text="Нечего отменять",
        reply_markup=user_kb.as_markup(resize_keyboard=True,
                                       input_field_placeholder="Утоли жажду")
    )


@order_router.message(Command(commands=["cancel"]))
@order_router.message(F.text.lower() == "отменить")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Действие отменено",
        reply_markup=user_kb.as_markup(resize_keyboard=True,
                                       input_field_placeholder="Утоли жажду")
    )


@order_router.message(OrderState.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    quantity = message.text
    if not quantity.isdigit():
        await message.reply("Пожалуйста, введите корректное количество бутылей")
        return
    quantity = int(quantity)
    if quantity < 1:
        await message.reply("❌Недопустимое число. Мы доставляем от 1 до 50 бутылей")
        return
    if quantity > 50:
        await message.reply("❗Максимальное число бутылей - 50")
        return
    await state.update_data(quantity=quantity)
    await message.answer("Введите адрес доставки 🚚", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="отменить")]
        ], resize_keyboard=True
    ))
    await state.set_state(OrderState.waiting_for_address)


# Обработка адреса
@order_router.inline_query(OrderState.waiting_for_address)
async def process_inline_address(query: InlineQuery):
    user_id = query.from_user.id
    recent_address = await get_last_address(user_id) or "Введите адрес"
    results = [
        InlineQueryResultArticle(
            id='1',
            title="Предыдущий адрес",
            description=recent_address,
            input_message_content=InputTextMessageContent(message_text=recent_address)
        )
    ]
    await query.answer(results, cache_time=1, is_personal=True)


@order_router.message(OrderState.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    address = message.text
    await state.update_data(address=address)
    await message.answer("Введите контактные данные для связи с вами 📞")
    await state.set_state(OrderState.waiting_for_phone)


@order_router.message(OrderState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text
    # Check correct phone_num
    if not phone.isdigit() or len(phone) != 11:
        await message.reply("❗Некорректный номер телефона. Пожалуйста, введите корректный номер, состоящий из 11 цифр.")
        return
    # if not phone.isdigit():
    #     await message.reply("❗Некорректный номер телефона. Пожалуйста, введите только цифры.")
    #     return
    # if phone and not phone.isdigit():
    #     await message.reply("❗Некорректный номер телефона. Пожалуйста, введите номер еще раз.")
    # if len(phone) != 11:
    #     await message.reply("❗Некорректный номер телефона. Пожалуйста, введите корректный номер.")
    #     return
    await state.update_data(phone=phone)
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )
    await message.answer("Выберите удобное время для доставки🕓", reply_markup=get_delivery_time_keyboard())
    await state.set_state(OrderState.waiting_for_time)


@order_router.callback_query(OrderState.waiting_for_time)
async def process_delivery_time(query: CallbackQuery, state: FSMContext):
    delivery_time = query.data.split('_', 1)[1]
    await state.update_data(delivery_time=delivery_time)
    await query.answer()
    data = await state.get_data()
    quantity = data['quantity']
    address = data['address']
    bottle_word = get_bottle_word(quantity)
    # Починить вывод суммы
    total_cost = PRICE_PER_BOTTLE * quantity

    await query.message.edit_text(
        f"Вы заказали {quantity} {bottle_word} по адресу {address}\n"
        f"Время доставки: {delivery_time},\n"
        f"Итого к оплате: {total_cost} руб.\n"
        f"Верно?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить✔", callback_data="confirm")],
            [InlineKeyboardButton(text="Исправить заказ📝", callback_data="edit")]
        ]))
    await state.set_state(OrderState.confirm_order)


@order_router.callback_query(OrderState.confirm_order, F.data == "confirm")
async def confirm_order_callback(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await query.message.bot.send_chat_action(
        chat_id=query.message.chat.id,
        action=ChatAction.TYPING
    )
    await query.message.edit_text("Ваш заказ принят в обработку.🔍")
    await query.answer()
    quantity = data.get('quantity')
    address = data.get('address')
    phone = data.get('phone')
    delivery_time = data.get('delivery_time')
    user_id = query.from_user.id
    name = query.from_user.full_name
    register_user(user_id, name, address)
    order_id = create_order(user_id, quantity,
                            address, phone, delivery_time
                            )
    await notify_admin(
        order_id, query.message, user_id,
        address, quantity,
        phone, delivery_time
    )
    await state.clear()


@order_router.callback_query(OrderState.confirm_order, F.data == "edit")
async def edit_order_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Пожалуйста, введите количество бутылей воды, которые вы хотите заказать.💧")
    await state.set_state(OrderState.waiting_for_quantity)
