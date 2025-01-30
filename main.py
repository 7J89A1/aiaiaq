from pyrogram import Client, filters
import requests
import json
from supabase import create_client, Client as SupabaseClient

# إعدادات Pyrogram
API_ID = "20944746"  # استبدل بـ API ID الخاص بك
API_HASH = "d169162c1bcf092a6773e685c62c3894"  # استبدل بـ API Hash الخاص بك
BOT_TOKEN = "7920189349:AAEUbt2gpAqdNtgJxHcMHHz8GmL-zFxQ0x0"  # استبدل بـ توكن البوت الخاص بك

# إعدادات Supabase
SUPABASE_URL = "https://uvndjaclphljmkmtargl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV2bmRqYWNscGhsam1rbXRhcmdsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY5ODY1ODAsImV4cCI6MjA1MjU2MjU4MH0.B3K12nhDSfIP3kfSqLzHqNrAQag1u2H6sKLJ4nO81A8"
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

# إعدادات API الخارجية
API_URL = "http://pass-gpt.nowtechai.com/api/v1/pass"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# إنشاء جلسة البوت
app = Client("my_bot22211ss", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# دالة لحفظ المحادثات في Supabase
def save_conversation_to_db(user_id, conversation):
    try:
        supabase.table("conversations").insert({
            "user_id": user_id,
            "conversation": json.dumps(conversation)  # تحويل القائمة إلى JSON
        }).execute()
        print(f"تم حفظ المحادثة للمستخدم {user_id}.")
    except Exception as err:
        print(f"خطأ أثناء حفظ المحادثة: {err}")

# دالة لاسترجاع المحادثات من Supabase
def get_conversation_from_db(user_id):
    try:
        response = supabase.table("conversations").select("conversation").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        if response.data:
            return json.loads(response.data[0]['conversation'])  # تحويل JSON إلى قائمة
        return []
    except Exception as err:
        print(f"خطأ أثناء استرجاع المحادثة: {err}")
        return []

# دالة للتعامل مع API الخارجي
def send_message_to_api(conversation):
    data = {"contents": conversation}
    try:
        response = requests.post(API_URL, headers=HEADERS, data=json.dumps(data), stream=True)
        response.raise_for_status()
        reply = ""
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                content = line[5:].strip()
                try:
                    json_content = json.loads(content)
                    reply += json_content.get('content', '')
                except json.JSONDecodeError:
                    reply += content
        return reply if reply else "لم يتم الحصول على رد."
    except requests.exceptions.RequestException as e:
        return f"حدث خطأ أثناء التواصل مع API: {e}"

# وظيفة بدء البوت
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("مرحبًا! أرسل لي رسالة وسأرد عليك، وسأحتفظ بسياق المحادثة.")

# وظيفة التعامل مع الرسائل
@app.on_message(filters.text & ~filters.command("start"))
async def handle_message(client, message):
    user_id = message.from_user.id
    user_message = message.text

    # استرجاع المحادثة السابقة أو البدء بمحادثة جديدة
    user_conversation = get_conversation_from_db(user_id) or [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    # إضافة رسالة المستخدم
    user_conversation.append({"role": "user", "content": user_message})

    # إرسال الرسالة إلى API
    reply = send_message_to_api(user_conversation)

    # إضافة رد البوت إلى المحادثة
    user_conversation.append({"role": "assistant", "content": reply})

    # حفظ المحادثة في Supabase
    save_conversation_to_db(user_id, user_conversation)

    # إرسال الرد للمستخدم
    await message.reply_text(reply)

# تشغيل البوت
if __name__ == "__main__":
    print("Bot is running...")
    app.run()
