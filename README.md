# بوت مؤسسة الجحفلي للحلول الرقمية - النسخة الصحيحة الكاملة

هذه النسخة تحتوي على كود كامل داخل `bot.py` وليست فارغة.

## المميزات
- شعار المؤسسة يظهر في رسالة الترحيب إذا كان الملف موجودًا في `assets/logo-aljahfali.png`.
- رسالة ترحيب احترافية.
- قسم خدمات كامل.
- قسم باقات.
- قسم عن الجحفلي مفصل.
- قسم أعمالنا.
- قسم أسئلة شائعة كبير ومصنف.
- نموذج طلب خدمة متقدم ومفصل.
- حفظ الطلبات في `data/service_requests.jsonl`.
- إرسال الطلبات للإدارة عبر `ADMIN_CHAT_ID`.
- أزرار واتساب مباشرة.

## التشغيل
```bash
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

في ويندوز:
```bash
pip install -r requirements.txt
copy .env.example .env
python bot.py
```

## إعداد ملف .env
افتح `.env` وضع:
- BOT_TOKEN من BotFather.
- ADMIN_CHAT_ID رقم حسابك في تليجرام.
- بيانات التواصل الحقيقية.

> ملاحظة: رسالة الترحيب في البوت تحتوي الآن على أزرار سريعة للتنقل بين الخدمات والباقات والأسئلة والتواصل.

## أوامر البوت
/start
/services
/packages
/request
/about
/portfolio
/faq
/contact
/recommend
/admin_requests
