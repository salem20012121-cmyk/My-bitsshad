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

# --- بياناتك الخاصة ---
API_TOKEN = '8674259871:AAGk59I_PYk2_Y04h_fCdiEX01pLFcXOZp0'
ADMIN_ID = 25880715

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    adding_email = State()
    setting_body = State()
    setting_seconds = State()

# تخزين البيانات
db = {
    "emails": [], 
    "targets": ["abuse@telegram.org", "recover@telegram.org", "dmca@telegram.org"],
    "subjects": ["Urgent: Impersonation Report", "Trademark Violation", "Security Concern"],
    "bodies": [],
    "seconds": 60,
    "is_running": False,
    "stats": {"success": 0, "fail": 0}
}

# --- لوحة التحكم الرئسية ---
def get_main_kb():
    buttons = [
        [InlineKeyboardButton(text=f"📧 الحسابات المضافة: {len(db['emails'])}", callback_data="v_emails")],
        [InlineKeyboardButton(text="➕ إضافة حساب Gmail", callback_data="add_e"),
         InlineKeyboardButton(text="📝 إضافة كليشة", callback_data="add_b")],
        [InlineKeyboardButton(text=f"⏱ الانتظار: {db['seconds']}ث", callback_data="set_s")],
        [InlineKeyboardButton(text="🚀 بدء عملية الشد", callback_data="start_burn")],
        [InlineKeyboardButton(text="🛑 إيقاف", callback_data="stop_burn"),
         InlineKeyboardButton(text="🗑 مسح البيانات", callback_data="clear")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- محرك الإرسال ---
async def send_mail_logic(sender, pwd, target, subject, body):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = target
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        await aiosmtplib.send(
            msg, hostname="smtp.gmail.com", port=587, 
            start_tls=True, username=sender, password=pwd, timeout=10
        )
        return True
    except:
        return False

@dp.message(Command("start"))
async def start(msg: types.Message):
    if msg.from_user.id != ADMIN_ID: return
    await msg.answer("🔥 **مرحباً سالم - نظام الشد الخارجي جاهز**\n\nأضف الحسابات والكليشات ثم ابدأ الهجوم.", reply_markup=get_main_kb())

@dp.callback_query(F.data == "add_e")
async def ask_email(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل الحساب والباسورد (App Password) هكذا:\n`example@gmail.com:abcd efgh ijkl mnop`", parse_mode="Markdown")
    await state.set_state(BotStates.adding_email)

@dp.message(BotStates.adding_email)
async def save_email(msg: types.Message, state: FSMContext):
    if ":" in msg.text:
        e, p = msg.text.split(":", 1)
        db["emails"].append((e.strip(), p.strip()))
        await msg.answer(f"✅ تم إضافة {e}", reply_markup=get_main_kb())
    await state.clear()

@dp.callback_query(F.data == "add_b")
async def ask_body(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("أرسل نص الكليشة الآن:")
    await state.set_state(BotStates.setting_body)

@dp.message(BotStates.setting_body)
async def save_body(msg: types.Message, state: FSMContext):
    db["bodies"].append(msg.text)
    await msg.answer("✅ تم حفظ الكليشة بنجاح.", reply_markup=get_main_kb())
    await state.clear()

@dp.callback_query(F.data == "start_burn")
async def engine_start(call: types.CallbackQuery):
    if not db["emails"] or not db["bodies"]:
        return await call.answer("❌ أضف بيانات أولاً!", show_alert=True)
    
    db["is_running"] = True
    db["stats"] = {"success": 0, "fail": 0}
    status_msg = await call.message.answer("🚀 بدأت العملية... جاري تحديث التقارير.")

    while db["is_running"]:
        for sender_email, sender_pwd in db["emails"]:
            if not db["is_running"]: break
            
            target = random.choice(db["targets"])
            subject = random.choice(db["subjects"])
            body = random.choice(db["bodies"])

            res = await send_mail_logic(sender_email, sender_pwd, target, subject, body)
            if res: db["stats"]["success"] += 1
            else: db["stats"]["fail"] += 1

            await status_msg.edit_text(
                f"📊 **تقرير الشد المباشر:**\n\n"
                f"✅ ناجح: {db['stats']['success']}\n"
                f"❌ فشل: {db['stats']['fail']}\n"
                f"🎯 المستهدف: {target}\n"
                f"⏱ الانتظار: {db['seconds']} ثانية"
            )
            await asyncio.sleep(db["seconds"])

@dp.callback_query(F.data == "stop_burn")
async def stop(call: types.CallbackQuery):
    db["is_running"] = False
    await call.answer("🛑 تم الإيقاف بنجاح", show_alert=True)

@dp.callback_query(F.data == "clear")
async def clear_db(call: types.CallbackQuery):
    db["emails"] = []
    db["bodies"] = []
    await call.answer("🗑 تم مسح جميع البيانات", show_alert=True)
    await call.message.edit_text("🔥 النظام جاهز للاستخدام من جديد.", reply_markup=get_main_kb())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
