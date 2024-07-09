from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram import Bot
from keyboard.kb import user_kb
from scripts.utils import get_bottle_word
import config
from database.requests import update_order_status, get_user_id_by_order, get_nonconfirmed_orders, get_all_users, \
    get_nondelivered_orders, get_nonsended_orders, add_review, get_reviews_by_order, get_delivered_orders, \
    get_order_details, get_admin_orders
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from common.text import thank_you_text
from Filters.filter import is_admin

router = Router()
bot = Bot(token=config.TOKEN)


class OrderCallback(CallbackData, prefix="order"):
    action: str
    order_id: int


class ArriveCallback(CallbackData, prefix="arrive"):
    action: str
    order_id: int


class DeliverCallback(CallbackData, prefix="deliver"):
    action: str
    order_id: int


class BroadcastStates(StatesGroup):
    waiting_for_broadcast = State()


class ReviewStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_comment = State()


class Monitoring(StatesGroup):
    waiting_for_orders = State()


# async def notify_admins_about_order(order_id, taken_by=None):
#     admin_orders = get_admin_orders(order_id)
#     order_details = get_order_details(order_id)
#     if order_details:
#         order_id, user_id, quantity, status, address, order_date, phone, delivery_time = order_details
#         for admin_id, message_id in admin_orders:
#             await bot.edit_message_text(
#                 chat_id=admin_id,
#                 message_id=message_id,  # предполагаем, что order_id используется как message_id, адаптируйте по
#                 # необходимости
#                 text=f"Заказ #{order_id} обновлен.\n"
#                      f"Пользователь ID: {user_id}\n"
#                      f"Количество: {quantity}\n"
#                      f"Адрес: {address}\n"
#                      f"Время доставки: {delivery_time}\n"
#                      f"Номер телефона: {phone}\n"
#                      f"Статус: {status}\n"
#                      f"Заказ взял: {taken_by}" if taken_by else "",
#                 reply_markup=arriving_admin_markup(order_id)
#                 if status == 'Оформлен'
#                 else deliver_admin_markup(order_id)
#                 if status == 'В пути' else None
#             )


@router.callback_query(OrderCallback.filter(F.action == "confirm"))
async def confirm_order(query: CallbackQuery, callback_data: OrderCallback):
    order_id = callback_data.order_id
    user_id = get_user_id_by_order(order_id)
    await query.message.bot.send_message(user_id, "Ваш заказ оформлен. Ожидайте.✅")
    await query.answer("Статус заказа обновлен.")
    order_details = get_order_details(order_id)
    if order_details:
        order_id, user_id, quantity, status, address, order_date, phone, delivery_time = order_details
        await query.message.edit_text(f"Заказ оформлен #{order_id}, {user_id}\n"
                                      f"Количество {quantity}\n"
                                      f"Адрес: {address}\n"
                                      f"Время доставки:{delivery_time}\n"
                                      f"Контакт для связи: {phone}\n"
                                      f"Время оформления: {order_date}",
                                      reply_markup=arriving_admin_markup(order_id))


@router.callback_query(ArriveCallback.filter(F.action == 'arrived'))
async def arrive_order(query: CallbackQuery, callback_data: ArriveCallback):
    order_id = callback_data.order_id
    update_order_status(order_id, 'В пути')
    user_id = get_user_id_by_order(order_id)
    await query.message.bot.send_message(user_id, "Ваш заказ в пути.")
    await query.answer("Статус заказа обновлен.")
    order_details = get_order_details(order_id)
    if order_details:
        order_id, user_id, quantity, status, address, order_date, phone, delivery_time = order_details
        await query.message.edit_text(f"Заказ отправлен #{order_id}.\n"
                                      f"Пользователь ID: {user_id}\n"
                                      f"Количество: {quantity}\n"
                                      f"Адрес: {address}\n"
                                      f"Время доставки:{delivery_time}\n"
                                      f"Номер телефона: {phone}\n"
                                      f"Статус: {status}\n", reply_markup=deliver_admin_markup(order_id))


@router.callback_query(DeliverCallback.filter(F.action == "delivered"))
async def delivered_order(query: CallbackQuery, callback_data: DeliverCallback, state: FSMContext):
    order_id = callback_data.order_id
    update_order_status(order_id, 'Доставлен')
    user_id = get_user_id_by_order(order_id)
    await query.message.bot.send_message(user_id,
                                         "Ваш заказ доставлен.🎉",
                                         message_effect_id="5046509860389126442")
    await query.answer("Статус заказа обновлен.")
    order_details = get_order_details(order_id)
    if order_details:
        order_id, user_id, quantity, status, address, order_date, phone, delivery_time = order_details
        await query.message.edit_text(f"Заказ доставлен #{order_id}.\n"
                                      f"Пользователь ID: {user_id}\n"
                                      f"Количество: {quantity}\n"
                                      f"Адрес: {address}\n"
                                      f"Время доставки: {delivery_time}\n"
                                      f"Номер телефона: {phone}\n"
                                      f"Статус: {status}\n"
                                      f"Время оформления: {order_date}")

        await query.message.bot.send_message(user_id,
                                             "Как вы оценивает нашу службу? Пожалуйста, оставьте оценку",
                                             reply_markup=rating_ikb())
        await state.set_state(ReviewStates.waiting_for_rating)
        await state.update_data(order_id=order_id, user_id=user_id)


@router.message(ReviewStates.waiting_for_rating)
async def receive_rating(message: Message, state: FSMContext):
    rating = message.text
    if not rating.isdigit() or not (1 <= int(rating) <= 5):
        await message.reply("Пожалуйста, введите корректную оценку от 1 до 5.")
        return
    rating = int(rating)
    await state.update_data(rating=rating)
    await message.answer("Пожалуйста, оставьте комментарий:")
    await state.set_state(ReviewStates.waiting_for_comment)


@router.callback_query(F.data.startswith("rate_"))
async def process_raiting(query: CallbackQuery, state: FSMContext):
    rating = int(query.data.split('_')[1])
    await state.update_data(rating=rating)
    await query.message.edit_text("Пожалуйста, оставьте комментарий:")
    await state.set_state(ReviewStates.waiting_for_comment)
    await query.answer()


@router.callback_query(F.data == "skip")
async def process_skip(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.edit_text("Хорошего дня",
                                  reply_markup=user_kb.as_markup())


@router.message(ReviewStates.waiting_for_comment)
async def receive_comment(message: Message, state: FSMContext):
    if message.sticker or message.photo:
        await message.reply("Извините, но мы ожидаем текстовый комментарий. "
                            "Пожалуйста, введите текстовый комментарий.")
        return
    comment = message.text
    data = await state.get_data()
    user_id = data['user_id']
    order_id = data['order_id']
    rating = data['rating']
    add_review(user_id, order_id, rating, comment)
    await message.answer(thank_you_text)
    await message.answer_sticker("CAACAgIAAxkBAAIM-mZ-xlu03Qc16wjlGSbY-MZu-diAAAJUAQACMNSdETURa_CgIFbrNQQ",
                                 reply_markup=user_kb.as_markup(
                                     resize_keyboard=True,
                                     input_field_placeholder="Утоли жажду"))
    await state.clear()


@router.message(F.text.lower() == "посмотреть отзывы")
async def view_reviews_handler(message: types.Message):
    orders = get_delivered_orders()
    if not orders:
        await message.answer("Нет заказов.")
        return

    for order in orders:
        order_id, user_id, quantity, status, address, order_date, phone, delivery_time = order
        reviews = get_reviews_by_order(order_id)
        reviews_text = "\n".join(
            [f"Рейтинг: {rating}\n"
             f"Комментарий: {comment}\n"
             f"Дата: {review_date}" for rating, comment, review_date in
             reviews])
        await message.answer(
            f"Заказ #{order_id}\n"
            f"Пользователь ID: {user_id}\n"
            f"Количество: {quantity}\n"
            f"Адрес: {address}\n"
            f"Время доставки: {delivery_time}\n"
            f"Статус: {status}\n"
            f"Номер телефона: {phone}\n"
            f"Отзывы:\n{reviews_text if reviews else 'Нет отзывов'}"
        )


def confirm_admin_markup(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Принять заказ",
                              callback_data=OrderCallback(action="confirm", order_id=order_id).pack())]

    ])


def arriving_admin_markup(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Поехал", callback_data=ArriveCallback(action="arrived", order_id=order_id).pack())]
    ])


def deliver_admin_markup(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Доставлен",
                              callback_data=DeliverCallback(action="delivered", order_id=order_id).pack())]
    ])


def rating_ikb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐", callback_data="rate_1")],
        [InlineKeyboardButton(text="⭐⭐", callback_data="rate_2")],
        [InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4")],
        [InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5")],
        [InlineKeyboardButton(text="Пропустить", callback_data="skip")]
    ])


def contact():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пожертвовать", callback_data="donate")]
    ])


async def notify_admin(order_id, query, user_id, address, quantity, phone, delivery_time):
    # ID чата администратора
    admin_chat_ids = config.ADMIN_ID
    bottle_word = get_bottle_word(quantity)

    for admin_chat_id in admin_chat_ids:
        if delivery_time == "Как можно быстрее":
            await query.bot.send_message(
                admin_chat_id,
                f"Новый заказ #{order_id}\n"
                f"Пользователь ID: {user_id}\n"
                f"Количество: {quantity} {bottle_word}\n"
                f"Адрес: {address}\n"
                f"Время доставки: {delivery_time}\n"
                f"Номер телефона: {phone}\n",
                reply_markup=confirm_admin_markup(order_id), message_effect_id="5104841245755180586"
            )
        else:
            await query.bot.send_message(
                admin_chat_id,
                f"Новый заказ #{order_id}\n"
                f"Пользователь ID: {user_id}\n"
                f"Количество: {quantity} {bottle_word}\n"
                f"Адрес: {address}\n"
                f"Время доставки: {delivery_time}\n"
                f"Номер телефона: {phone}\n",
                reply_markup=confirm_admin_markup(order_id)
            )


@router.message(F.text == "Посмотреть не обработанные заказы")
async def nonconfirmed_orders_handler(message: types.Message):
    orders = get_nonconfirmed_orders()
    if not orders:
        await message.answer("Нет новых заказов.")
        return

    for order in orders:
        order_id, user_id, quantity, status, address, order_date, phone, delivery_time = order
        await message.answer(
            f"Новый заказ #{order_id}\n"
            f"Пользователь ID: {user_id}\n"
            f"Количество: {quantity}\n"
            f"Адрес: {address}\n"
            f"Время доставки:{delivery_time}\n"
            f"Статус: {status}"
            f"Номер телефона: {phone}",
            reply_markup=confirm_admin_markup(order_id)
        )


@router.message(F.text.lower() == "заказы в пути")
async def nondelivered_orders_handler(message: types.Message):
    orders = get_nondelivered_orders()
    if not orders:
        await message.answer("Все заказы доставлены.")
        return

    for order in orders:
        order_id, user_id, quantity, status, address, order_date, phone, delivery_time = order
        await message.answer(
            f"Заказ отправлен #{order_id}\n"
            f"Пользователь ID: {user_id}\n"
            f"Количество: {quantity}\n"
            f"Адрес: {address}\n"
            f"Время доставки:{delivery_time}\n"
            f"Статус: {status}\n"
            f"Номер телефона: {phone}",
            reply_markup=deliver_admin_markup(order_id)
        )


@router.message(F.text.lower() == "не в пути")
async def nonsended_orders_handler(message: Message):
    orders = get_nonsended_orders()
    if not orders:
        await message.answer("Все заказы выехали")
        return
    for order in orders:
        order_id, user_id, quantity, status, address, order_date, phone, delivery_time = order
        await message.answer(
            f"Заказ оформлен #{order_id}, {user_id}\n"
            f"Количество {quantity}\n"
            f"Адрес: {address}\n"
            f"Контакт для связи: {phone}\n"
            f"Время доставки:{delivery_time}\n"
            f"Время оформления: {order_date}", reply_markup=arriving_admin_markup(order_id)
        )


@router.message(F.text.lower() == "отправить рассылку")
async def start_broadcast(message: Message, state: FSMContext):
    if is_admin(message.from_user.id):
        await message.answer("Введите сообщение для рассылки всем пользователям.")
        await state.set_state(BroadcastStates.waiting_for_broadcast)
    else:
        await message.reply("У вас нет доступа к этой команде!")


@router.message(BroadcastStates.waiting_for_broadcast,
                F.content_type.in_(['text', 'photo', 'video',
                                    'document', 'sticker', 'voice', 'video_note']))
async def process_broadcast_message(message: Message, state: FSMContext):
    if is_admin(message.from_user.id):
        users = get_all_users()
        failed_users = []
        for user in users:
            try:
                if message.content_type == 'text':
                    await bot.send_message(user[0], message.text)
                elif message.content_type == 'photo':
                    await bot.send_photo(user[0], message.photo[-1].file_id, caption=message.caption)
                elif message.content_type == 'video':
                    await bot.send_video(user[0], message.video.file_id, caption=message.caption)
                elif message.content_type == 'document':
                    await bot.send_document(user[0], message.document.file_id, caption=message.caption)
                elif message.content_type == "sticker":
                    await bot.send_sticker(user[0], message.sticker.file_id)
                elif message.content_type == 'voice':
                    await bot.send_voice(user[0], message.voice.file_id, caption=message.caption)
                elif message.content_type == 'video_note':
                    await bot.send_video_note(user[0], message.video_note.file_id)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user[0]}: {e}")
                failed_users.append(user[0])
        await message.answer("Сообщение отправлено всем пользователям.")
        if failed_users:
            await message.answer(
                f"Не удалось отправить сообщение следующим пользователям: {', '.join(map(str, failed_users))}")
        await state.clear()
        await state.set_state(Monitoring.waiting_for_orders)
    else:
        await message.reply("f")


@router.message(Monitoring.waiting_for_orders)
async def monitoring(state: FSMContext):
    await state.clear()
