import requests
import threading
import time
import re
import asyncio
import websockets
import json
import random

# ==============================================================================
# ⚙️ الإعدادات
# ==============================================================================
BASE_URL = "http://127.0.0.1:8000"
REGISTER_URL = f"{BASE_URL}/auth/register/" 
LOGIN_URL = f"{BASE_URL}/auth/login/"
CHAT_URL = f"{BASE_URL}/chat/"

# إعدادات الضغط
TOTAL_USERS = 20       
MESSAGES_PER_USER = 10  
DELAY_BETWEEN_MSGS = 0.5 

# ==============================================================================
# 🌍 مصفوفة اللغات
# ==============================================================================
LANG_CONFIG = [
    {
        'code': 'ar', 'name': 'Arabic',
        'safe': ["مرحبا، كيف حالك؟", "أحتاج لموعد", "شكرا لك", "هل العيادة مفتوحة؟"],
        'danger': ["أشعر بنزيف حاد", "ألم شديد في الصدر", "لا أستطيع التنفس", "دم يخرج من فمي"]
    },
    {
        'code': 'uk', 'name': 'Ukrainian',
        'safe': ["Привіт", "Як справи?", "Мені потрібен лікар", "Дякую"],
        'danger': ["У мене сильний біль у грудях", "Я стікаю кров'ю", "Я не можу дихати", "Втрата свідомості"]
    },
    {
        'code': 'so', 'name': 'Somali',
        'safe': ["Iska warran", "Waan fiicanahay", "Dhakhtar baan rabaa", "Mahadsanid"],
        'danger': ["Xanuun laabta ah", "Dhiig baxaya", "Neefsashada oo dhib ah", "Suuxdin"]
    },
    {
        'code': 'ti', 'name': 'Tigrinya',
        'safe': ["ሰላም", "ከመይ አለኻ", "ትኬት ደልየ", "የቐንየለይ"],
        'danger': ["ከቢድ ናይ ልቢ ቃንዛ", "ደም ይፈስስ", "ምትንፋስ አሸጊሩኒ", "ውኖ ምጥፋእ"]
    },
    {
        'code': 'en', 'name': 'English',
        'safe': ["Hello", "How are you", "I need an appointment", "Thanks"],
        'danger': ["Severe chest pain", "Heavy bleeding", "Cannot breathe", "Fainting"]
    }
]

async def bot_task(user_index):
    # 1. تحديد اللغة
    lang_data = LANG_CONFIG[user_index % len(LANG_CONFIG)]
    
    username = f"stress_user_{user_index}"
    # 🛑 الإضافة هنا: إنشاء إيميل فريد لكل بوت
    email = f"stress_user_{user_index}@example.com"
    password = "123"
    full_name = f"Bot {user_index} ({lang_data['name']})"
    
    session = requests.Session()

    try:
        # ---------------------------------------------------------
        # 0. REGISTER (تسجيل المستخدم لضمان وجوده ولغته وايميله)
        # ---------------------------------------------------------
        # زيارة الصفحة لجلب CSRF
        session.get(REGISTER_URL)
        if 'csrftoken' in session.cookies:
            csrftoken = session.cookies['csrftoken']
            
            reg_payload = {
                "username": username,
                "email": email, # <--- تم إضافة الإيميل هنا
                "password": password,
                "confirm_password": password,
                "full_name": full_name,
                "native_language": lang_data['code'],
                "csrfmiddlewaretoken": csrftoken
            }
            # نرسل طلب التسجيل (إذا كان المستخدم موجوداً سيفشل بصمت ونكمل للدخول)
            session.post(REGISTER_URL, data=reg_payload, headers={'Referer': REGISTER_URL})

        # ---------------------------------------------------------
        # 1. LOGIN (الدخول)
        # ---------------------------------------------------------
        session.get(LOGIN_URL)
        if 'csrftoken' not in session.cookies:
            print(f"❌ Bot {user_index}: No CSRF")
            return
        
        login_data = {
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": session.cookies['csrftoken']
        }
        headers = {'Referer': LOGIN_URL}
        
        response = session.post(LOGIN_URL, data=login_data, headers=headers)
        
        if response.status_code != 200:
            # قد يكون توجيه (302)
            if not response.history:
                print(f"❌ Bot {user_index}: Login Failed (Check credentials)")
                return

        # ---------------------------------------------------------
        # 2. EXTRACT UUID (بحث ذكي في HTML)
        # ---------------------------------------------------------
        chat_page = session.get(CHAT_URL)
        html = chat_page.text
        
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        match = re.search(uuid_pattern, html)
        
        if not match:
            print(f"❌ Bot {user_index}: NO UUID FOUND in Chat Page")
            return
        
        session_uuid = match.group(0)

        # ---------------------------------------------------------
        # 3. WEBSOCKET ATTACK
        # ---------------------------------------------------------
        ws_url = f"ws://127.0.0.1:8000/ws/chat/{session_uuid}/"
        
        async with websockets.connect(ws_url) as websocket:
            for i in range(MESSAGES_PER_USER):
                if random.random() < 0.2: 
                    text = random.choice(lang_data['danger'])
                    msg_type = "🚨 DANGER"
                else:
                    text = random.choice(lang_data['safe'])
                    msg_type = "✅ SAFE"

                msg_data = {"message": f"{text} ({i})"}
                await websocket.send(json.dumps(msg_data))
                
                print(f"📤 Bot {user_index} [{lang_data['code'].upper()}]: {msg_type}")
                
                await asyncio.sleep(DELAY_BETWEEN_MSGS)

    except Exception as e:
        print(f"💀 Bot {user_index} Error: {e}")

async def main():
    total_msgs = TOTAL_USERS * MESSAGES_PER_USER
    print(f"🚀 STARTING MULTI-LANGUAGE LOAD TEST")
    print(f"🌍 Languages Configured: {', '.join([l['name'] for l in LANG_CONFIG])}")
    print(f"🔥 Target: {TOTAL_USERS} Users | {total_msgs} Messages")
    print("-" * 40)
    
    start_time = time.time()
    
    BATCH_SIZE = 25
    for i in range(0, TOTAL_USERS, BATCH_SIZE):
        batch = []
        print(f"🌊 Launching Batch {i} to {i+BATCH_SIZE}...")
        for j in range(i, min(i+BATCH_SIZE, TOTAL_USERS)):
            batch.append(bot_task(j))
        await asyncio.gather(*batch)
    
    duration = time.time() - start_time
    print("-" * 40)
    print(f"🏁 Finished in {duration:.2f} seconds")
    print(f"📊 Throughput: {total_msgs / duration:.2f} msg/sec")
    print(f"⚠️ Check Admin Panel now to verify TRANSLATIONS!")

if __name__ == "__main__":
    asyncio.run(main())