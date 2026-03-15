import asyncio
import logging
import aiosmtplib
import random
from email.message import EmailMessage
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- بياناتك ---
API_TOKEN = '8674259871:AAGk59I_PYk2_Y04h_fCdiEX01pLFcXOZp0'
ADMIN_ID = 25880715

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- سيرفر وهمي لمنع توقف Render ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

class BotStates(StatesGroup):
    adding_email = State()
    setting_body = State()

db = {
    "emails": [], 
    "targets": ["abuse@telegram.org", "recover@telegram.org", "dmca@telegram.org"],
    "subjects": ["Urgent: Impersonation Report", "Trademark Violation"],
    "bodies": [],
    "seconds": 60,
    "is_running": False,
    "stats": {"success": 0, "fail": 0}
}

def get_main_kb():
    buttons = [
        [InlineKeyboardButton(text=f"📧 الحسابات: {len(db['emails'])}", callback_data="v_emails")],
        [InlineKeyboardButton(text="➕ إضافة حساب", callback_data="add_e"),
         InlineKeyboardButton(text="📝 إضافة كليشة", callback_data="add_b")],
        [InlineKeyboardButton(text="🚀 بدء الشد", callback_data="start_burn")],
        [InlineKeyboardButton(text="🛑 إيقاف", callback_data="stop_burn")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_mail_logic(sender, pwd, target, subject, body):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = target
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        await aiosmtplib.send(msg, hostname="smtp.gmail.com", port=587, start_tls=True, username=sender, password=pwd, timeout=10)
        return True
    except: return False

@dp.message(Command("start"))
async def start(msg: types.Message):
    if msg.from_user.id == ADMIN_ID:
        await msg.answer("🔥 نظام الشد جاهز يا سالم", reply_markup=get_main_kb())

@dp.callback_query(F.data == "add_e")
async def add_e(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل `الحساب:الباسورد`")
    await state.set_state(BotStates.adding_email)

@dp.message(BotStates.adding_email)
async def save_e(msg: types.Message, state: FSMContext):
    if ":" in msg.text:
        db["emails"].append(msg.text.split(":", 1))
        await msg.answer("✅ تم الحفظ", reply_markup=get_main_kb())
    await state.clear()

@dp.callback_query(F.data == "start_burn")
async def run_engine(call: types.CallbackQuery):
    db["is_running"] = True
    status_msg = await call.message.answer("🚀 بدأ الشد...")
    while db["is_running"]:
        for e, p in db["emails"]:
            res = await send_mail_logic(e, p, random.choice(db["targets"]), random.choice(db["subjects"]), random.choice(db["bodies"]))
            if res: db["stats"]["success"] += 1
            else: db["stats"]["fail"] += 1
            await status_msg.edit_text(f"📊 نجاح: {db['stats']['success']} | فشل: {db['stats']['fail']}")
            await asyncio.sleep(db["seconds"])

@dp.callback_query(F.data == "stop_burn")
async def stop(call: types.CallbackQuery):
    db["is_running"] = False
    await call.answer("🛑 توقف")

async def main():
    # تشغيل السيرفر الوهمي والبوت معاً
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
