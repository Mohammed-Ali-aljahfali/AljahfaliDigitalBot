# -*- coding: utf-8 -*-
"""
بوت مؤسسة الجحفلي للحلول الرقمية - النسخة الاحترافية الكاملة v3.0
==================================================================
المميزات:
- لوحة إدارة متكاملة مع إحصائيات شاملة
- نظام حالات الطلبات مع إشعار العملاء
- شريط تقدم في نموذج الطلب
- أزرار تنقل موحدة في كل رسالة
- تقييم الخدمة بعد الإنهاء
- متابعة حالة الطلب للعميل
- البحث في الخدمات
- الرد المباشر من لوحة الإدارة
- إمكانية تعديل الطلب قبل التأكيد
- حفظ معلومات المستخدمين

Library: python-telegram-bot==21.6
طريقة التشغيل:
  1) pip install -r requirements.txt
  2) انسخ .env.example إلى .env وضع BOT_TOKEN و ADMIN_CHAT_ID
  3) python bot.py
"""

# ==============================================================
# IMPORTS
# ==============================================================
import os
import json
import logging
import sqlite3
import pathlib
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote
from typing import Dict, Any, Optional, List, Tuple

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BotCommand,
    Message,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.error import BadRequest

# ==============================================================
# إعدادات البوت
# ==============================================================
load_dotenv()

BOT_TOKEN        = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID    = os.getenv("ADMIN_CHAT_ID", "")
COMPANY_PHONE    = os.getenv("COMPANY_PHONE",   "+967782611415")
WHATSAPP_NUMBER  = os.getenv("WHATSAPP_NUMBER", "967782611415")
COMPANY_EMAIL    = os.getenv("COMPANY_EMAIL",   "info@aljahfali.com")
COMPANY_WEBSITE  = os.getenv("COMPANY_WEBSITE", "https://aljahfali.com")
COMPANY_LOCATION = os.getenv("COMPANY_LOCATION","اليمن")

BASE_DIR        = Path(__file__).resolve().parent
ASSETS_DIR      = BASE_DIR / "assets"
LOGO_PATH       = ASSETS_DIR / "logo-aljahfali.png"
DATA_DIR        = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH         = DATA_DIR / "aljahfali.db"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
ATTACHMENTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(DATA_DIR / "bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("aljahfali-bot-v3")

# ==============================================================
# حالات نموذج طلب الخدمة
# ==============================================================
(
    REQ_NAME, REQ_PHONE, REQ_SERVICE, REQ_PROJECT_NAME,
    REQ_ACTIVITY, REQ_TARGET, REQ_GOAL, REQ_STATUS_FIELD,
    REQ_FEATURES, REQ_PAGES, REQ_STYLE, REQ_CONTENT,
    REQ_REFERENCES, REQ_BUDGET, REQ_DEADLINE, REQ_CONTACT,
    REQ_NOTES, REQ_CONFIRM, REQ_EDIT_FIELD,
) = range(19)

# حالات نموذج الرد من الإدارة
ADMIN_REPLY_MSG = 100
ADMIN_BROADCAST_MSG = 101

# ==============================================================
# محتوى المؤسسة
# ==============================================================
COMPANY = {
    "name":    "مؤسسة الجحفلي للحلول الرقمية",
    "en":      "Al-Jahfali Digital Solutions",
    "tagline": "نحو حلول تقنية ذكية تصنع فرقًا في أعمالك.",
    "intro": (
        "مؤسسة تقنية إبداعية تقدم حلولًا رقمية متكاملة للأفراد والشركات والمؤسسات، "
        "تشمل تصميم المواقع، تطوير الأنظمة، تطبيقات الجوال، قواعد البيانات، "
        "الأتمتة، الهوية الرقمية، التصميم الإعلاني، وتحسين الظهور في Google."
    ),
    "about": (
        "في مؤسسة الجحفلي للحلول الرقمية نؤمن أن التقنية ليست مجرد شكل جميل، "
        "بل وسيلة لتنظيم العمل، جذب العملاء، وتحويل الأفكار إلى حلول عملية. "
        "نبدأ بفهم نشاط العميل وهدفه، ثم نبني الحل المناسب من حيث التصميم، "
        "المحتوى، تجربة المستخدم، وسهولة الإدارة والتطوير."
    ),
    "vision":  "أن نكون خيارًا موثوقًا في تقديم حلول رقمية ذكية ترفع جودة الأعمال.",
    "mission": "تقديم خدمات رقمية احترافية تجمع بين الإبداع، التقنية، الجودة، والوضوح.",
}

SERVICES: Dict[str, Dict[str, Any]] = {
    "web": {
        "title":    "🌐 تصميم وتطوير المواقع الإلكترونية",
        "emoji":    "🌐",
        "short":    "مواقع تعريفية وتجارية وخدمية جذابة ومتجاوبة مع جميع الأجهزة.",
        "details":  [
            "تصميم صفحة رئيسية قوية وجاذبة.",
            "صفحات: من نحن، خدماتنا، أعمالنا، الباقات، تواصل معنا.",
            "ربط واتساب ونموذج طلب خدمة.",
            "تهيئة SEO أساسية للظهور في Google.",
            "تصميم متجاوب للجوال والتابلت والكمبيوتر.",
            "إمكانية التطوير لاحقًا إلى لوحة تحكم.",
        ],
        "ask_hint": "عدد الصفحات، الأقسام، هل لديك شعار ومحتوى، هل لديك دومين واستضافة؟",
    },
    "systems": {
        "title":    "🖥️ تطوير الأنظمة الإلكترونية",
        "emoji":    "🖥️",
        "short":    "أنظمة إدارية مخصصة لتنظيم البيانات والعمليات والتقارير.",
        "details":  [
            "أنظمة مبيعات ومخزون وفواتير.",
            "أنظمة مدارس وطلاب ومعلمين.",
            "أنظمة موظفين ومهام وتقارير.",
            "لوحات تحكم وصلاحيات مستخدمين.",
            "تقارير وإحصائيات وتصدير Excel.",
            "قواعد بيانات ونسخ احتياطي.",
        ],
        "ask_hint": "من يستخدم النظام، ما العمليات المطلوبة، ما التقارير والصلاحيات؟",
    },
    "apps": {
        "title":    "📱 تطبيقات الجوال",
        "emoji":    "📱",
        "short":    "تطبيقات Android و iOS حسب احتياج المشروع.",
        "details":  [
            "واجهات تطبيق حديثة وسهلة الاستخدام.",
            "تسجيل دخول وحسابات مستخدمين.",
            "طلبات أو حجوزات أو عرض خدمات.",
            "ربط بلوحة تحكم وقاعدة بيانات.",
            "إشعارات وتنبيهات حسب الحاجة.",
        ],
        "ask_hint": "Android أم iOS، هل يوجد تسجيل دخول، طلبات، إشعارات، لوحة تحكم؟",
    },
    "database": {
        "title":    "🗄️ قواعد البيانات وإدارة البيانات",
        "emoji":    "🗄️",
        "short":    "تنظيم البيانات وتحويل الجداول إلى نظام واضح وتقارير.",
        "details":  [
            "تحليل ملفات Excel والبيانات الحالية.",
            "تصميم جداول وعلاقات.",
            "استيراد وتصدير البيانات.",
            "تقارير ولوحات متابعة.",
            "تنظيم وحماية ونسخ احتياطي.",
        ],
        "ask_hint": "نوع البيانات، عدد الجداول، التقارير المطلوبة، هل البيانات موجودة في Excel؟",
    },
    "automation": {
        "title":    "⚙️ الأتمتة والتحول الرقمي",
        "emoji":    "⚙️",
        "short":    "تحويل الإجراءات اليدوية إلى عمليات رقمية.",
        "details":  [
            "أتمتة النماذج والتقارير.",
            "تنظيم إجراءات العمل.",
            "إشعارات ومتابعة مهام.",
            "ربط العمليات والخدمات.",
            "تقليل الأخطاء اليدوية وتوفير الوقت.",
        ],
        "ask_hint": "ما الإجراء المتكرر، من ينفذه، ما المدخلات والمخرجات؟",
    },
    "branding": {
        "title":    "🎨 الهوية الرقمية والتصميم",
        "emoji":    "🎨",
        "short":    "شعارات، هويات بصرية، بروفايلات، واجهات، وقوالب سوشيال.",
        "details":  [
            "تصميم شعار وهوية بصرية متكاملة.",
            "اختيار ألوان وخطوط مناسبة.",
            "بروفايل شركة وسيرة ذاتية.",
            "واجهات UI/UX للمواقع والتطبيقات.",
            "قوالب منشورات وستوري.",
        ],
        "ask_hint": "اسم النشاط، الألوان المفضلة، نوع الهوية، الملفات المطلوبة.",
    },
    "greetings": {
        "title":    "🎁 تصميم التهاني والمناسبات",
        "emoji":    "🎁",
        "short":    "تهاني تخرج وزواج وعقد قران وأعياد وافتتاحات.",
        "details":  [
            "تصميم تهاني بأسماء وعبارات خاصة.",
            "تصاميم فاخرة أو بسيطة حسب المناسبة.",
            "مقاسات واتساب وسوشيال ميديا.",
            "إضافة صور أو شعارات عند الحاجة.",
            "تعديلات بسيطة حسب الاتفاق.",
        ],
        "ask_hint": "نوع المناسبة، الاسم، العبارة، المقاس، الألوان، الصور.",
    },
    "ads": {
        "title":    "📣 تصميم الإعلانات والسوشيال ميديا",
        "emoji":    "📣",
        "short":    "منشورات، ستوريات، بنرات، حملات، وكلمات تسويقية.",
        "details":  [
            "منشورات إعلانية احترافية وجذابة.",
            "ستوريات وعروض خدمات.",
            "نصوص تسويقية مقنعة.",
            "تصاميم منتجات وخدمات وعقارات.",
            "حملات متناسقة بصريًا.",
        ],
        "ask_hint": "نوع الإعلان، المنتج أو الخدمة، الجمهور، العرض، المقاس.",
    },
    "seo": {
        "title":    "🔍 SEO وتحسين الظهور في Google",
        "emoji":    "🔍",
        "short":    "تهيئة المواقع لمحركات البحث وتحسين فرص الظهور.",
        "details":  [
            "تحسين العناوين والوصف الميتا.",
            "Sitemap و Robots.txt و Schema.",
            "تنظيم الصفحات والروابط الداخلية.",
            "اقتراح كلمات مفتاحية ومقالات.",
            "تحسين تجربة المستخدم والسرعة.",
        ],
        "ask_hint": "رابط الموقع، الكلمات المستهدفة، المدينة، المنافسون، هل توجد مقالات؟",
    },
    "support": {
        "title":    "🎧 الدعم الفني والاستشارات",
        "emoji":    "🎧",
        "short":    "تحليل أفكار ومشاكل تقنية وتقديم حلول عملية.",
        "details":  [
            "مراجعة فكرة المشروع وتقييمها.",
            "اقتراح الحل التقني المناسب.",
            "تحسين موقع أو نظام موجود.",
            "حل مشاكل تقنية متنوعة.",
            "متابعة وصيانة حسب الاتفاق.",
        ],
        "ask_hint": "ما المشكلة أو القرار المطلوب، ما النظام الحالي، ما النتيجة المطلوبة؟",
    },
}

PACKAGES = {
    "basic": {
        "title":    "📦 الباقة الأساسية",
        "price":    "تبدأ من السعر المناسب",
        "desc":     "مناسبة للأفراد والمشاريع الصغيرة.",
        "features": [
            "✅ موقع تعريفي من 4 صفحات.",
            "✅ تصميم متجاوب.",
            "✅ ربط واتساب.",
            "✅ نموذج تواصل.",
            "✅ SEO أساسي.",
        ],
        "icon": "📦",
    },
    "pro": {
        "title":    "🚀 الباقة الاحترافية",
        "price":    "تبدأ من السعر الاحترافي",
        "desc":     "مناسبة للشركات والمؤسسات.",
        "features": [
            "✅ موقع من 6 إلى 8 صفحات.",
            "✅ تصميم خاص ومميز.",
            "✅ محتوى تسويقي.",
            "✅ معرض أعمال.",
            "✅ SEO احترافي.",
            "✅ دعم فني 3 أشهر.",
        ],
        "icon": "🚀",
    },
    "advanced": {
        "title":    "🏢 الباقة المتقدمة",
        "price":    "حسب حجم المشروع",
        "desc":     "مناسبة للأنظمة والمنصات الكبيرة.",
        "features": [
            "✅ تحليل متطلبات تفصيلي.",
            "✅ لوحة تحكم كاملة.",
            "✅ قاعدة بيانات.",
            "✅ صلاحيات متعددة.",
            "✅ تقارير وإحصائيات.",
            "✅ تطوير مستمر.",
        ],
        "icon": "🏢",
    },
    "design": {
        "title":    "🎨 باقة التصميم والإعلانات",
        "price":    "تبدأ من سعر التصميم",
        "desc":     "مناسبة للمناسبات والسوشيال ميديا.",
        "features": [
            "✅ تصميم تهاني احترافي.",
            "✅ منشورات إعلانية.",
            "✅ نص تسويقي.",
            "✅ مقاسات مختلفة.",
            "✅ هوية بصرية متناسقة.",
        ],
        "icon": "🎨",
    },
}

FAQ_CATEGORIES = {
    "general": {
        "title": "أسئلة عامة عن المؤسسة",
        "icon":  "ℹ️",
        "items": [
            ("ما هي مؤسسة الجحفلي للحلول الرقمية؟",
             "مؤسسة تقدم حلولًا رقمية تشمل المواقع، الأنظمة، التطبيقات، قواعد البيانات، الأتمتة، التصميم، الإعلانات، والـ SEO."),
            ("ما الذي يميز الجحفلي؟",
             "نركز على الحل العملي، التصميم الجذاب، وضوح المحتوى، سهولة الاستخدام، والتواصل السريع مع العميل."),
            ("هل تقدمون خدمات للأفراد والشركات؟",
             "نعم، نخدم الأفراد والشركات والمؤسسات والمدارس والمتاجر والعيادات والمشاريع الناشئة."),
            ("هل يمكن تنفيذ مشروع مخصص؟",
             "نعم، ندرس الفكرة والمتطلبات ثم نقترح الحل المناسب بالكامل."),
            ("هل يمكن تنفيذ أكثر من خدمة معًا؟",
             "نعم، مثل: موقع + بوت تليجرام + SEO + تصاميم إعلانية."),
            ("هل تقدمون دعمًا بعد التسليم؟",
             "نعم، يمكن الاتفاق على دعم وصيانة حسب نوع المشروع."),
        ],
    },
    "web": {
        "title": "أسئلة تصميم المواقع",
        "icon":  "🌐",
        "items": [
            ("هل يمكن عمل موقع بدون قاعدة بيانات؟",
             "نعم، يمكن عمل موقع HTML/CSS/JS ثابت وسريع ومناسب للتعريف بالخدمات."),
            ("هل الموقع يعمل على الجوال؟",
             "نعم، يتم تصميم الموقع ليعمل على الجوال والتابلت والكمبيوتر بشكل كامل."),
            ("ما الصفحات الأساسية للموقع؟",
             "الرئيسية، من نحن، الخدمات، الأعمال، الباقات، الأسئلة الشائعة، تواصل معنا."),
            ("هل يمكن ربط الموقع بواتساب؟",
             "نعم، يمكن إضافة زر واتساب ونموذج يجهز رسالة تلقائية."),
            ("هل يمكن إضافة دومين واستضافة؟",
             "نعم، بعد تجهيز الموقع يمكن رفعه على استضافة وربطه بالدومين."),
            ("هل يمكن تطوير الموقع لاحقًا؟",
             "نعم، يمكن تحويله إلى موقع بلوحة تحكم وقاعدة بيانات."),
        ],
    },
    "systems": {
        "title": "أسئلة الأنظمة وقواعد البيانات",
        "icon":  "🖥️",
        "items": [
            ("ما الفرق بين الموقع والنظام؟",
             "الموقع يعرض معلومات، أما النظام فيدير بيانات وعمليات وتقارير وصلاحيات."),
            ("هل يمكن تحويل ملفات Excel إلى نظام؟",
             "نعم، يمكن تحليل ملفات Excel وبناء قاعدة بيانات ولوحة تحكم."),
            ("هل يمكن إضافة صلاحيات؟",
             "نعم، يمكن إنشاء مدير وموظفين ومستخدمين بصلاحيات مختلفة."),
            ("هل يمكن تصدير التقارير؟",
             "نعم، يمكن إضافة تصدير Excel أو PDF حسب الحاجة."),
            ("هل النظام محمي؟",
             "يمكن إضافة تسجيل دخول وصلاحيات ونسخ احتياطي وحماية مبدئية."),
        ],
    },
    "design": {
        "title": "أسئلة التصميم والتهاني",
        "icon":  "🎨",
        "items": [
            ("هل تصممون تهاني تخرج وزواج؟",
             "نعم، نصمم تهاني تخرج وزواج وعقد قران وأعياد وافتتاحات."),
            ("هل يمكن إضافة اسم وصورة؟",
             "نعم، يمكن إضافة الاسم والصورة والشعار والعبارة المطلوبة."),
            ("هل تصممون إعلانات تجارية؟",
             "نعم، نصمم إعلانات خدمات ومنتجات وعروض وسوشيال ميديا."),
            ("هل تكتبون النص التسويقي؟",
             "نعم، يمكن صياغة نص تسويقي مناسب للتصميم."),
            ("هل يمكن اختيار الألوان؟",
             "نعم، يمكن للعميل تحديد الألوان أو نختار ألوانًا مناسبة للنشاط."),
        ],
    },
    "seo": {
        "title": "أسئلة SEO والظهور في Google",
        "icon":  "🔍",
        "items": [
            ("هل تضمنون المركز الأول في Google؟",
             "لا يمكن ضمان المركز الأول مباشرة، لكن نهيئ الموقع بشكل صحيح لتحسين فرص الظهور."),
            ("ما أهم عناصر SEO؟",
             "العنوان، الوصف، المحتوى، السرعة، الروابط الداخلية، Sitemap، Schema، وتجربة المستخدم."),
            ("هل الموقع الثابت يظهر في Google؟",
             "نعم، إذا كان مرفوعًا على دومين ومفهرسًا ومهيأ جيدًا."),
            ("هل أحتاج مقالات؟",
             "المقالات تساعد في استهداف كلمات بحث أكثر وزيادة فرص الظهور."),
            ("ما هي Google Search Console؟",
             "أداة من Google لمتابعة الفهرسة والزيارات والمشاكل وإرسال خريطة الموقع."),
        ],
    },
    "pricing": {
        "title": "أسئلة الأسعار والتنفيذ",
        "icon":  "💰",
        "items": [
            ("كم سعر الموقع؟",
             "يعتمد على عدد الصفحات ومستوى التصميم والخصائص والمحتوى والمدة. تواصل معنا لعرض سعر مخصص."),
            ("هل يمكن البدء بنسخة بسيطة؟",
             "نعم، يمكن البدء بنسخة بسيطة ثم تطويرها لاحقًا."),
            ("ما المطلوب قبل بدء التنفيذ؟",
             "الشعار، النصوص، الصور، الأقسام المطلوبة، بيانات التواصل، وأمثلة إن وجدت."),
            ("كم مدة التنفيذ؟",
             "تعتمد على حجم المشروع؛ المواقع البسيطة أسرع من الأنظمة والتطبيقات."),
            ("هل يمكن الدفع على دفعات؟",
             "يمكن الاتفاق على طريقة دفع مناسبة حسب حجم المشروع."),
        ],
    },
}

PORTFOLIO = [
    ("🏢 موقع شركة خدمات",     "موقع يعرض الخدمات والباقات والتواصل المباشر مع تهيئة SEO.",  "web"),
    ("🧾 نظام مبيعات وفواتير", "إدارة العملاء والمنتجات والفواتير والتقارير المالية.",          "systems"),
    ("🏫 نظام إدارة مدرسة",    "طلاب ومعلمون وحضور وتقارير وصلاحيات متعددة.",                  "systems"),
    ("📱 تطبيق حجز وطلبات",   "تطبيق لاستقبال الطلبات والحجوزات مع إشعارات.",               "apps"),
    ("🎁 تصاميم تهاني",        "تخرج، زواج، عقد قران، أعياد، افتتاحات باحترافية.",             "greetings"),
    ("📣 حملات إعلانية",        "منشورات وسلاسل إعلانية لجذب العملاء على السوشيال ميديا.",     "ads"),
    ("🔍 تحسين SEO موقع",      "رفع الموقع في نتائج البحث واستهداف كلمات محلية.",              "seo"),
    ("🎨 هوية بصرية متكاملة",  "شعار، ألوان، خطوط، قوالب، وبروفايل الشركة.",                  "branding"),
]

# حالات الطلبات
REQUEST_STATUSES = {
    "new":         ("🆕", "جديد"),
    "reviewing":   ("🔍", "قيد المراجعة"),
    "contacted":   ("📞", "تم التواصل"),
    "in_progress": ("⚙️", "جارٍ التنفيذ"),
    "done":        ("✅", "مكتمل"),
    "cancelled":   ("❌", "ملغي"),
}

# خطوات النموذج لعرض التقدم
FORM_STEPS = [
    "الاسم", "الهاتف", "الخدمة", "اسم المشروع",
    "النشاط", "الجمهور", "الهدف", "الوضع الحالي",
    "المميزات", "الصفحات", "التصميم", "المحتوى",
    "المراجع", "الميزانية", "الموعد", "التواصل", "ملاحظات",
]

# ==============================================================
# قاعدة البيانات
# ==============================================================
def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id     TEXT PRIMARY KEY,
            username        TEXT,
            first_name      TEXT,
            last_name       TEXT,
            phone           TEXT,
            joined_at       TEXT,
            last_seen       TEXT,
            total_requests  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS service_requests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id     TEXT,
            username        TEXT,
            name            TEXT,
            phone           TEXT,
            service         TEXT,
            service_key     TEXT,
            project_name    TEXT,
            activity        TEXT,
            target          TEXT,
            goal            TEXT,
            current_status  TEXT,
            features        TEXT,
            pages           TEXT,
            style           TEXT,
            content         TEXT,
            references_text TEXT,
            budget          TEXT,
            deadline        TEXT,
            contact_method  TEXT,
            notes           TEXT,
            attachments     TEXT DEFAULT '[]',
            req_status      TEXT DEFAULT 'new',
            rating          INTEGER DEFAULT 0,
            rating_comment  TEXT,
            created_at      TEXT,
            updated_at      TEXT
        );

        CREATE TABLE IF NOT EXISTS status_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id  INTEGER,
            old_status  TEXT,
            new_status  TEXT,
            note        TEXT,
            changed_at  TEXT,
            FOREIGN KEY (request_id) REFERENCES service_requests(id)
        );

        CREATE TABLE IF NOT EXISTS admin_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id  INTEGER,
            telegram_id TEXT,
            message     TEXT,
            sent_at     TEXT
        );
    """)
    conn.commit()
    return conn

DB_CONN: sqlite3.Connection = init_db()

# ==============================================================
# أدوات مساعدة
# ==============================================================
def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def wa_link(text: str = "") -> str:
    base = f"https://wa.me/{WHATSAPP_NUMBER}"
    if text:
        return f"{base}?text={quote(text)}"
    return base

def is_admin(chat_id) -> bool:
    return ADMIN_CHAT_ID and str(chat_id) == str(ADMIN_CHAT_ID)

def progress_bar(step: int, total: int = 17) -> str:
    filled = int((step / total) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    pct = int((step / total) * 100)
    return f"[{bar}] {pct}%  ({step}/{total})"

def upsert_user(user) -> None:
    try:
        cur = DB_CONN.cursor()
        cur.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name, joined_at, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name,
                last_name  = excluded.last_name,
                last_seen  = excluded.last_seen
        """, (
            str(user.id), user.username or "",
            user.first_name or "", user.last_name or "",
            now_text(), now_text(),
        ))
        DB_CONN.commit()
    except Exception:
        logger.exception("upsert_user failed")

def save_request(data: Dict[str, Any]) -> int:
    """حفظ طلب الخدمة وإرجاع الـ ID"""
    try:
        cur = DB_CONN.cursor()
        cur.execute("""
            INSERT INTO service_requests (
                telegram_id, username, name, phone, service, service_key,
                project_name, activity, target, goal, current_status,
                features, pages, style, content, references_text, budget,
                deadline, contact_method, notes, attachments,
                req_status, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("telegram_id"), data.get("username"),
            data.get("name"), data.get("phone"),
            data.get("service"), data.get("service_key"),
            data.get("project_name"), data.get("activity"),
            data.get("target"), data.get("goal"),
            data.get("current_status"), data.get("features"),
            data.get("pages"), data.get("style"),
            data.get("content"), data.get("references"),
            data.get("budget"), data.get("deadline"),
            data.get("contact_method"), data.get("notes"),
            json.dumps(data.get("attachments", []), ensure_ascii=False),
            "new", now_text(), now_text(),
        ))
        DB_CONN.commit()
        req_id = cur.lastrowid
        # تحديث عداد طلبات المستخدم
        cur.execute("""
            UPDATE users SET total_requests = total_requests + 1
            WHERE telegram_id = ?
        """, (data.get("telegram_id"),))
        DB_CONN.commit()
        return req_id
    except Exception:
        logger.exception("save_request failed")
        return 0

def update_request_status(req_id: int, new_status: str, note: str = "") -> bool:
    try:
        cur = DB_CONN.cursor()
        cur.execute("SELECT req_status FROM service_requests WHERE id=?", (req_id,))
        row = cur.fetchone()
        if not row:
            return False
        old_status = row["req_status"]
        cur.execute("""
            UPDATE service_requests
            SET req_status=?, updated_at=?
            WHERE id=?
        """, (new_status, now_text(), req_id))
        cur.execute("""
            INSERT INTO status_history (request_id, old_status, new_status, note, changed_at)
            VALUES (?,?,?,?,?)
        """, (req_id, old_status, new_status, note, now_text()))
        DB_CONN.commit()
        return True
    except Exception:
        logger.exception("update_request_status failed")
        return False

def get_request_by_id(req_id: int) -> Optional[Dict]:
    try:
        cur = DB_CONN.cursor()
        cur.execute("SELECT * FROM service_requests WHERE id=?", (req_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception:
        return None

def get_requests_by_user(telegram_id: str) -> List[Dict]:
    try:
        cur = DB_CONN.cursor()
        cur.execute("""
            SELECT id, service, project_name, req_status, created_at
            FROM service_requests
            WHERE telegram_id=?
            ORDER BY id DESC LIMIT 10
        """, (telegram_id,))
        return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []

def get_stats() -> Dict[str, Any]:
    try:
        cur = DB_CONN.cursor()
        cur.execute("SELECT COUNT(*) as total FROM service_requests")
        total = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) as c FROM service_requests WHERE req_status='new'")
        new_c = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM service_requests WHERE req_status='in_progress'")
        in_prog = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM service_requests WHERE req_status='done'")
        done_c = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM users")
        users_c = cur.fetchone()["c"]
        cur.execute("""
            SELECT service_key, COUNT(*) as c
            FROM service_requests
            GROUP BY service_key
            ORDER BY c DESC LIMIT 3
        """)
        top = [(r["service_key"], r["c"]) for r in cur.fetchall()]
        return {
            "total": total, "new": new_c, "in_progress": in_prog,
            "done": done_c, "users": users_c, "top_services": top,
        }
    except Exception:
        return {}

def get_recent_requests(limit: int = 5, offset: int = 0, status_filter: str = None) -> List[Dict]:
    try:
        cur = DB_CONN.cursor()
        if status_filter:
            cur.execute("""
                SELECT id, name, phone, service, req_status, created_at
                FROM service_requests
                WHERE req_status=?
                ORDER BY id DESC LIMIT ? OFFSET ?
            """, (status_filter, limit, offset))
        else:
            cur.execute("""
                SELECT id, name, phone, service, req_status, created_at
                FROM service_requests
                ORDER BY id DESC LIMIT ? OFFSET ?
            """, (limit, offset))
        return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []

# ==============================================================
# تنسيق الرسائل
# ==============================================================
def format_request_summary(data: Dict[str, Any]) -> str:
    atts = data.get("attachments", [])
    if isinstance(atts, str):
        try:
            atts = json.loads(atts)
        except Exception:
            atts = []
    return (
        "📩 <b>طلب خدمة جديد</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>الاسم:</b> {data.get('name', '-')}\n"
        f"📞 <b>الهاتف:</b> <code>{data.get('phone', '-')}</code>\n"
        f"🌐 <b>الخدمة:</b> {data.get('service', '-')}\n"
        f"🏷️ <b>اسم المشروع:</b> {data.get('project_name', '-')}\n"
        f"🏢 <b>النشاط:</b> {data.get('activity', '-')}\n"
        f"🎯 <b>الجمهور:</b> {data.get('target', '-')}\n"
        f"🚀 <b>الهدف:</b> {data.get('goal', '-')}\n"
        f"📌 <b>الوضع الحالي:</b> {data.get('current_status', '-')}\n"
        f"🧩 <b>المميزات:</b> {data.get('features', '-')}\n"
        f"📄 <b>الصفحات/العناصر:</b> {data.get('pages', '-')}\n"
        f"🎨 <b>أسلوب التصميم:</b> {data.get('style', '-')}\n"
        f"🗂️ <b>جاهزية المحتوى:</b> {data.get('content', '-')}\n"
        f"🔗 <b>أمثلة/مراجع:</b> {data.get('references', '-')}\n"
        f"💰 <b>الميزانية:</b> {data.get('budget', '-')}\n"
        f"⏱️ <b>موعد التسليم:</b> {data.get('deadline', '-')}\n"
        f"💬 <b>طريقة التواصل:</b> {data.get('contact_method', '-')}\n"
        f"📝 <b>ملاحظات:</b> {data.get('notes', '-')}\n"
        f"📎 <b>مرفقات:</b> {len(atts)} ملف(ات)\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Telegram ID:</b> <code>{data.get('telegram_id', '-')}</code>\n"
        f"🔗 <b>Username:</b> @{data.get('username', '-')}"
    )

def format_request_card(r: Dict) -> str:
    st = REQUEST_STATUSES.get(r.get("req_status", "new"), ("🆕", "جديد"))
    return (
        f"🔖 <b>طلب #{r['id']}</b>  {st[0]} {st[1]}\n"
        f"👤 {r.get('name', '-')} | 📞 <code>{r.get('phone', '-')}</code>\n"
        f"🌐 {r.get('service', '-')}\n"
        f"🕒 {r.get('created_at', '-')}"
    )

def status_label(key: str) -> str:
    s = REQUEST_STATUSES.get(key, ("🆕", "جديد"))
    return f"{s[0]} {s[1]}"

# ==============================================================
# أدوات إرسال
# ==============================================================
async def safe_edit(message: Message, text: str, markup=None, parse_mode=ParseMode.HTML) -> None:
    try:
        await message.edit_text(text, reply_markup=markup, parse_mode=parse_mode)
    except BadRequest:
        await message.reply_text(text, reply_markup=markup, parse_mode=parse_mode)

async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, text: str,
                                   markup=None) -> None:
    if not ADMIN_CHAT_ID:
        return
    try:
        await context.bot.send_message(
            chat_id=int(ADMIN_CHAT_ID),
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
    except Exception:
        logger.exception("send_admin_notification failed")

async def notify_user(context: ContextTypes.DEFAULT_TYPE, telegram_id: str, text: str,
                       markup=None) -> None:
    try:
        await context.bot.send_message(
            chat_id=int(telegram_id),
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
    except Exception:
        logger.exception("notify_user failed for %s", telegram_id)

# ==============================================================
# لوحات المفاتيح (Keyboards)
# ==============================================================
def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🌐 الخدمات"),       KeyboardButton("📦 الباقات")],
            [KeyboardButton("📩 طلب خدمة"),      KeyboardButton("❓ الأسئلة الشائعة")],
            [KeyboardButton("ℹ️ عن الجحفلي"),    KeyboardButton("🧾 أعمالنا")],
            [KeyboardButton("🔍 ترشيح الخدمة"),  KeyboardButton("☎️ تواصل معنا")],
            [KeyboardButton("📊 طلباتي"),         KeyboardButton("🏠 الرئيسية")],
        ],
        resize_keyboard=True,
    )

def nav_row(back_data: str = None, extra_buttons: list = None) -> List[InlineKeyboardButton]:
    """صف تنقل موحد"""
    row = []
    if back_data:
        row.append(InlineKeyboardButton("🔙 رجوع", callback_data=back_data))
    row.append(InlineKeyboardButton("🏠 الرئيسية", callback_data="home"))
    row.append(InlineKeyboardButton("💬 واتساب", url=wa_link()))
    if extra_buttons:
        row.extend(extra_buttons)
    return row

def welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 الخدمات",    callback_data="show_services"),
            InlineKeyboardButton("📦 الباقات",     callback_data="show_packages"),
        ],
        [
            InlineKeyboardButton("📩 طلب خدمة",   callback_data="start_request"),
            InlineKeyboardButton("❓ الأسئلة",     callback_data="show_faq"),
        ],
        [
            InlineKeyboardButton("🔍 ترشيح خدمة", callback_data="show_recommend"),
            InlineKeyboardButton("🧾 أعمالنا",     callback_data="show_portfolio"),
        ],
        [
            InlineKeyboardButton("☎️ تواصل معنا",  callback_data="contact"),
            InlineKeyboardButton("ℹ️ عن الجحفلي",  callback_data="about:intro"),
        ],
    ])

def services_keyboard(back: str = "home") -> InlineKeyboardMarkup:
    rows = []
    service_list = list(SERVICES.items())
    for i in range(0, len(service_list), 2):
        row = []
        k1, v1 = service_list[i]
        row.append(InlineKeyboardButton(v1["emoji"] + " " + v1["title"].split(" ", 1)[1], callback_data=f"service:{k1}"))
        if i + 1 < len(service_list):
            k2, v2 = service_list[i + 1]
            row.append(InlineKeyboardButton(v2["emoji"] + " " + v2["title"].split(" ", 1)[1], callback_data=f"service:{k2}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("📩 طلب خدمة متقدم", callback_data="start_request")])
    rows.append(nav_row(back_data=back))
    return InlineKeyboardMarkup(rows)

def packages_keyboard(back: str = "home") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"{v['icon']} {v['title'].split(' ', 1)[1]}", callback_data=f"package:{k}")]
            for k, v in PACKAGES.items()]
    rows.append([InlineKeyboardButton("📩 اطلب الباقة المناسبة", callback_data="start_request")])
    rows.append(nav_row(back_data=back))
    return InlineKeyboardMarkup(rows)

def about_keyboard(back: str = "home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 نبذة تفصيلية",    callback_data="about:details"),
         InlineKeyboardButton("👁️ الرؤية والرسالة", callback_data="about:vision")],
        [InlineKeyboardButton("💎 القيم",            callback_data="about:values"),
         InlineKeyboardButton("⚙️ آلية العمل",      callback_data="about:steps")],
        [InlineKeyboardButton("✨ لماذا الجحفلي؟",  callback_data="about:why")],
        [InlineKeyboardButton("📩 اطلب خدمة",        callback_data="start_request")],
        nav_row(back_data=back),
    ])

def faq_categories_keyboard(back: str = "home") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"{cat['icon']} {cat['title']}", callback_data=f"faqcat:{key}")]
            for key, cat in FAQ_CATEGORIES.items()]
    rows.append(nav_row(back_data=back))
    return InlineKeyboardMarkup(rows)

def portfolio_keyboard(back: str = "home") -> InlineKeyboardMarkup:
    rows = []
    for i, (title, _, svc_key) in enumerate(PORTFOLIO):
        rows.append([InlineKeyboardButton(title, callback_data=f"portfolio:{i}")])
    rows.append([InlineKeyboardButton("📩 طلب خدمة مشابهة", callback_data="start_request")])
    rows.append(nav_row(back_data=back))
    return InlineKeyboardMarkup(rows)

def recommend_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("أريد موقع يعرض خدماتي",    callback_data="service:web")],
        [InlineKeyboardButton("أريد نظام ينظم عملي",       callback_data="service:systems")],
        [InlineKeyboardButton("أريد تطبيق جوال",           callback_data="service:apps")],
        [InlineKeyboardButton("أريد تنظيم بيانات Excel",  callback_data="service:database")],
        [InlineKeyboardButton("أريد أتمتة إجراءات",       callback_data="service:automation")],
        [InlineKeyboardButton("أريد شعار أو هوية بصرية",  callback_data="service:branding")],
        [InlineKeyboardButton("أريد تهنئة أو مناسبة",     callback_data="service:greetings")],
        [InlineKeyboardButton("أريد إعلانات وتصاميم",     callback_data="service:ads")],
        [InlineKeyboardButton("أريد الظهور في Google",    callback_data="service:seo")],
        [InlineKeyboardButton("لا أعرف، أريد استشارة",    callback_data="service:support")],
        nav_row(back_data="home"),
    ])

def contact_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 واتساب مباشر", url=wa_link("أهلًا مؤسسة الجحفلي، أريد الاستفسار عن خدمة."))],
        [InlineKeyboardButton("📩 طلب خدمة متقدم", callback_data="start_request")],
        nav_row(back_data="home"),
    ])

def rating_keyboard(req_id: int) -> InlineKeyboardMarkup:
    stars = ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(s, callback_data=f"rate:{req_id}:{i+1}") for i, s in enumerate(stars)]
    ])

def my_requests_keyboard(requests: List[Dict]) -> InlineKeyboardMarkup:
    rows = []
    for r in requests:
        st = REQUEST_STATUSES.get(r.get("req_status", "new"), ("🆕", "جديد"))
        label = f"#{r['id']} {st[0]} {r.get('service', '')[:20]}"
        rows.append([InlineKeyboardButton(label, callback_data=f"myreq:{r['id']}")])
    rows.append(nav_row(back_data="home"))
    return InlineKeyboardMarkup(rows)

# ==============================================================
# لوحة مفاتيح الإدارة
# ==============================================================
def admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 الطلبات",        callback_data="admin:requests:0"),
            InlineKeyboardButton("📊 الإحصائيات",     callback_data="admin:stats"),
        ],
        [
            InlineKeyboardButton("🆕 الطلبات الجديدة",   callback_data="admin:filter:new:0"),
            InlineKeyboardButton("⚙️ قيد التنفيذ",        callback_data="admin:filter:in_progress:0"),
        ],
        [
            InlineKeyboardButton("📞 تم التواصل",     callback_data="admin:filter:contacted:0"),
            InlineKeyboardButton("✅ المكتملة",        callback_data="admin:filter:done:0"),
        ],
        [InlineKeyboardButton("📢 رسالة جماعية",     callback_data="admin:broadcast")],
    ])

def admin_request_keyboard(req_id: int, current_status: str, page: int = 0) -> InlineKeyboardMarkup:
    status_buttons = []
    for key, (emoji, label) in REQUEST_STATUSES.items():
        if key != current_status:
            status_buttons.append(
                InlineKeyboardButton(f"{emoji} {label}", callback_data=f"admin:setstatus:{req_id}:{key}")
            )

    rows = []
    # أزرار تغيير الحالة (صفين)
    for i in range(0, len(status_buttons), 3):
        rows.append(status_buttons[i:i+3])

    rows.append([
        InlineKeyboardButton("💬 رد مباشر", callback_data=f"admin:reply:{req_id}"),
        InlineKeyboardButton("📋 التاريخ",  callback_data=f"admin:history:{req_id}"),
    ])
    rows.append([
        InlineKeyboardButton("◀️ السابق", callback_data=f"admin:requests:{max(0, page-1)}"),
        InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin:main"),
        InlineKeyboardButton("التالي ▶️", callback_data=f"admin:requests:{page+1}"),
    ])
    return InlineKeyboardMarkup(rows)

def requests_list_keyboard(requests: List[Dict], page: int, total_pages: int,
                            filter_status: str = None) -> InlineKeyboardMarkup:
    rows = []
    for r in requests:
        st = REQUEST_STATUSES.get(r.get("req_status", "new"), ("🆕", "جديد"))
        label = f"#{r['id']} {st[0]} {r.get('name', '?')[:10]} | {r.get('service', '')[:15]}"
        rows.append([InlineKeyboardButton(label, callback_data=f"admin:viewreq:{r['id']}:{page}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            "◀️ السابق",
            callback_data=f"admin:filter:{filter_status}:{page-1}" if filter_status else f"admin:requests:{page-1}"
        ))
    nav.append(InlineKeyboardButton(f"📄 {page+1}/{max(1,total_pages)}", callback_data="noop"))
    nav.append(InlineKeyboardButton(
        "التالي ▶️",
        callback_data=f"admin:filter:{filter_status}:{page+1}" if filter_status else f"admin:requests:{page+1}"
    ))
    rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin:main")])
    return InlineKeyboardMarkup(rows)

# ==============================================================
# أوامر البوت الرئيسية
# ==============================================================
async def set_bot_commands(application: Application) -> None:
    """
    ضبط أوامر البوت لكل نطاق (Scope) على حدة:
      - المستخدمون العاديون  → default + private
      - المحادثات الجماعية   → group / supergroup
      - الإدارة (خاص)        → أوامر إضافية
    """
    from telegram import (
        BotCommandScopeDefault,
        BotCommandScopeAllPrivateChats,
        BotCommandScopeAllGroupChats,
        BotCommandScopeChat,
    )

    # ── 1. أوامر المستخدم العادي (المحادثة الخاصة)
    private_commands = [
        BotCommand("start",      "🏠 الصفحة الرئيسية"),
        BotCommand("services",   "🌐 عرض جميع الخدمات"),
        BotCommand("packages",   "📦 الباقات والأسعار"),
        BotCommand("request",    "📩 تقديم طلب خدمة"),
        BotCommand("mystatus",   "📊 متابعة طلباتي"),
        BotCommand("recommend",  "🔍 ترشيح الخدمة المناسبة"),
        BotCommand("search",     "🔎 بحث في الخدمات"),
        BotCommand("portfolio",  "🧾 أعمالنا ومشاريعنا"),
        BotCommand("about",      "ℹ️ عن مؤسسة الجحفلي"),
        BotCommand("faq",        "❓ الأسئلة الشائعة"),
        BotCommand("contact",    "☎️ تواصل معنا"),
        BotCommand("cancel",     "❌ إلغاء العملية الحالية"),
    ]

    # ── 2. أوامر المجموعات (مختصرة)
    group_commands = [
        BotCommand("start",     "🏠 ابدأ / الرئيسية"),
        BotCommand("services",  "🌐 الخدمات"),
        BotCommand("request",   "📩 طلب خدمة"),
        BotCommand("contact",   "☎️ تواصل معنا"),
        BotCommand("faq",       "❓ الأسئلة الشائعة"),
    ]

    # ── 3. أوامر الإدارة (خاصة بـ ADMIN_CHAT_ID)
    admin_commands = private_commands + [
        BotCommand("admin",          "👑 لوحة الإدارة"),
    ]

    try:
        # تطبيق على جميع المحادثات (fallback)
        await application.bot.set_my_commands(
            private_commands,
            scope=BotCommandScopeDefault(),
        )
        # تطبيق على المحادثات الخاصة
        await application.bot.set_my_commands(
            private_commands,
            scope=BotCommandScopeAllPrivateChats(),
        )
        # تطبيق على المجموعات
        await application.bot.set_my_commands(
            group_commands,
            scope=BotCommandScopeAllGroupChats(),
        )
        # تطبيق على الإدارة (محادثة خاصة بـ ADMIN)
        if ADMIN_CHAT_ID:
            try:
                await application.bot.set_my_commands(
                    admin_commands,
                    scope=BotCommandScopeChat(chat_id=int(ADMIN_CHAT_ID)),
                )
            except Exception:
                logger.warning("Could not set admin-specific commands (chat not started yet).")

        logger.info("Bot commands set successfully for all scopes.")

    except Exception:
        logger.exception("Failed to set bot commands.")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    upsert_user(user)
    name = user.first_name or "عزيزي"

    caption = (
        f"✨ <b>أهلًا وسهلًا {name}!</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>{COMPANY['tagline']}</b>\n\n"
        "نحن نقدم حلولًا رقمية متكاملة لتطوير موقعك، نظامك، تطبيقك، وهوية نشاطك.\n"
        "سواء كنت تريد مشروعًا سريعًا أو خدمة متكاملة، فنحن معك خطوة بخطوة.\n\n"
        "📌 <b>عبر هذا البوت يمكنك:</b>\n"
        "• استعراض الخدمات والباقات بسهولة\n"
        "• تقديم طلب خدمة متقدم واحترافي\n"
        "• متابعة حالة طلبك في أي وقت\n"
        "• الاطلاع على الأسئلة الشائعة\n"
        "• التواصل المباشر مع الفريق\n\n"
        "👇 <b>اختر من الأزرار أدناه للبدء:</b>"
    )

    if LOGO_PATH.exists():
        await update.message.reply_photo(
            photo=LOGO_PATH.open("rb"),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard(),
        )
    else:
        await update.message.reply_text(
            caption, parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard(),
        )

    await update.message.reply_text(
        "🎛️ يمكنك أيضًا استخدام الأزرار السريعة:",
        reply_markup=main_keyboard(),
    )

async def cmd_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    await update.message.reply_text(
        "🌐 <b>خدماتنا الرقمية الشاملة</b>\n\n"
        "اختر الخدمة لمعرفة التفاصيل الكاملة:",
        parse_mode=ParseMode.HTML,
        reply_markup=services_keyboard(),
    )

async def cmd_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    await update.message.reply_text(
        "📦 <b>باقاتنا الاحترافية</b>\n\n"
        "اختر الباقة المناسبة لمعرفة تفاصيلها:",
        parse_mode=ParseMode.HTML,
        reply_markup=packages_keyboard(),
    )

async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    text = (
        f"ℹ️ <b>{COMPANY['name']}</b>\n"
        f"<i>{COMPANY['en']}</i>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"{COMPANY['intro']}\n\n"
        "اختر القسم الذي تريد معرفة المزيد عنه:"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=about_keyboard())

async def cmd_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    lines = ["🧾 <b>نماذج من أعمالنا ومشاريعنا</b>\n"]
    for i, (title, desc, _) in enumerate(PORTFOLIO):
        lines.append(f"{i+1}. <b>{title}</b>\n   {desc}\n")
    await update.message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.HTML,
        reply_markup=portfolio_keyboard(),
    )

async def cmd_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    await update.message.reply_text(
        "❓ <b>مركز الأسئلة الشائعة</b>\n\n"
        "اختر التصنيف للاطلاع على الأسئلة:",
        parse_mode=ParseMode.HTML,
        reply_markup=faq_categories_keyboard(),
    )

async def cmd_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    text = (
        "☎️ <b>تواصل معنا</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"📞 <b>الهاتف:</b> <code>{COMPANY_PHONE}</code>\n"
        f"💬 <b>واتساب:</b> {WHATSAPP_NUMBER}\n"
        f"📧 <b>البريد:</b> {COMPANY_EMAIL}\n"
        f"🌍 <b>الموقع:</b> {COMPANY_WEBSITE}\n"
        f"📍 <b>الموقع الجغرافي:</b> {COMPANY_LOCATION}\n\n"
        "⏰ <b>أوقات الرد:</b> السبت – الخميس، 8 صباحًا – 10 مساءً"
    )
    await update.message.reply_text(
        text, parse_mode=ParseMode.HTML,
        reply_markup=contact_keyboard(),
    )

async def cmd_recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    await update.message.reply_text(
        "🔍 <b>ترشيح الخدمة المناسبة</b>\n\n"
        "اختر أقرب وصف لاحتياجك وسنوجّهك للخدمة الصحيحة:",
        parse_mode=ParseMode.HTML,
        reply_markup=recommend_keyboard(),
    )

async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    if context.args:
        query = " ".join(context.args).lower()
        results = []
        for key, svc in SERVICES.items():
            if (query in svc["title"].lower() or
                    query in svc["short"].lower() or
                    any(query in d.lower() for d in svc["details"])):
                results.append((key, svc))

        if results:
            rows = [[InlineKeyboardButton(v["title"], callback_data=f"service:{k}")] for k, v in results]
            rows.append(nav_row(back_data="home"))
            await update.message.reply_text(
                f"🔎 نتائج البحث عن: <b>{query}</b>\n\nوجدنا {len(results)} خدمة:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(rows),
            )
        else:
            await update.message.reply_text(
                f"🔎 لم يتم العثور على نتائج لـ: <b>{query}</b>\n\n"
                "جرب كلمات مختلفة أو استعرض خدماتنا كاملة.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🌐 عرض كل الخدمات", callback_data="show_services")],
                    nav_row(back_data="home"),
                ]),
            )
    else:
        await update.message.reply_text(
            "🔎 <b>البحث في الخدمات</b>\n\n"
            "اكتب الأمر مع كلمة البحث، مثال:\n"
            "<code>/search موقع</code>\n"
            "<code>/search تطبيق</code>\n"
            "<code>/search تصميم</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 عرض كل الخدمات", callback_data="show_services")]]),
        )

async def cmd_mystatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    upsert_user(update.effective_user)
    user_id = str(update.effective_user.id)
    requests = get_requests_by_user(user_id)
    if not requests:
        await update.message.reply_text(
            "📊 <b>طلباتي</b>\n\n"
            "لا توجد طلبات مسجلة باسمك حتى الآن.\n"
            "ابدأ بتقديم طلب خدمة الآن!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 تقديم طلب خدمة", callback_data="start_request")],
                nav_row(back_data="home"),
            ]),
        )
        return
    await update.message.reply_text(
        f"📊 <b>طلباتي</b> ({len(requests)} طلب)\n\n"
        "اختر الطلب لمعرفة تفاصيله وحالته:",
        parse_mode=ParseMode.HTML,
        reply_markup=my_requests_keyboard(requests),
    )

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("⛔ هذا الأمر مخصص للإدارة فقط.")
        return
    stats = get_stats()
    text = (
        "👑 <b>لوحة إدارة بوت الجحفلي</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👥 المستخدمون: <b>{stats.get('users', 0)}</b>\n"
        f"📋 إجمالي الطلبات: <b>{stats.get('total', 0)}</b>\n"
        f"🆕 جديدة: <b>{stats.get('new', 0)}</b>\n"
        f"⚙️ قيد التنفيذ: <b>{stats.get('in_progress', 0)}</b>\n"
        f"✅ مكتملة: <b>{stats.get('done', 0)}</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "اختر من لوحة التحكم:"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_main_keyboard())

# ==============================================================
# ConversationHandler – نموذج طلب الخدمة
# ==============================================================
def get_step_header(step: int, field_name: str) -> str:
    return (
        f"📩 <b>طلب خدمة متقدم</b>\n"
        f"<i>{progress_bar(step)}</i>\n"
        f"<b>الخطوة {step}/17:</b> {field_name}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
    )

CANCEL_KB = InlineKeyboardMarkup([[
    InlineKeyboardButton("❌ إلغاء الطلب", callback_data="conv_cancel")
]])
CANCEL_SKIP_KB = InlineKeyboardMarkup([[
    InlineKeyboardButton("⏭️ تخطي", callback_data="conv_skip"),
    InlineKeyboardButton("❌ إلغاء", callback_data="conv_cancel"),
]])

async def req_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نقطة بداية النموذج"""
    upsert_user(update.effective_user)
    context.user_data["req"] = {}
    context.user_data["req_step"] = 1
    name = update.effective_user.first_name or "عزيزي"
    msg = (
        get_step_header(1, FORM_STEPS[0]) +
        f"👤 مرحبًا {name}، اكتب <b>اسمك الكامل</b>:"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB)
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB)
    return REQ_NAME

async def req_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if len(val) < 2:
        await update.message.reply_text(
            "⚠️ الاسم يجب أن يكون حرفين على الأقل. أعد الكتابة:",
            reply_markup=CANCEL_KB
        )
        return REQ_NAME
    context.user_data["req"]["name"] = val
    await update.message.reply_text(
        get_step_header(2, FORM_STEPS[1]) +
        "📞 اكتب <b>رقم هاتفك</b> أو واتسابك:",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB,
    )
    return REQ_PHONE

async def req_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if len(val) < 7:
        await update.message.reply_text(
            "⚠️ رقم الهاتف غير صحيح. أعد الكتابة:",
            reply_markup=CANCEL_KB,
        )
        return REQ_PHONE
    context.user_data["req"]["phone"] = val
    buttons = [[InlineKeyboardButton(v["title"], callback_data=f"rq_svc:{k}")]
               for k, v in SERVICES.items()]
    buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="conv_cancel")])
    await update.message.reply_text(
        get_step_header(3, FORM_STEPS[2]) +
        "🌐 اختر <b>نوع الخدمة</b> المطلوبة:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return REQ_SERVICE

async def req_service_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data.split(":", 1)[1]
    svc = SERVICES[key]
    context.user_data["req"]["service"] = svc["title"]
    context.user_data["req"]["service_key"] = key
    await q.message.reply_text(
        get_step_header(4, FORM_STEPS[3]) +
        f"✅ اخترت: <b>{svc['title']}</b>\n\n"
        f"💡 <i>تلميح: {svc['ask_hint']}</i>\n\n"
        "🏷️ اكتب <b>اسم المشروع</b> أو النشاط:",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB,
    )
    return REQ_PROJECT_NAME

async def req_project_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["req"]["project_name"] = update.message.text.strip()
    await update.message.reply_text(
        get_step_header(5, FORM_STEPS[4]) +
        "🏢 ما <b>نوع النشاط</b>؟\n"
        "<i>مثال: شركة، عيادة، مدرسة، متجر، خدمات تقنية...</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB,
    )
    return REQ_ACTIVITY

async def req_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["req"]["activity"] = update.message.text.strip()
    await update.message.reply_text(
        get_step_header(6, FORM_STEPS[5]) +
        "🎯 من <b>الجمهور المستهدف</b>؟\n"
        "<i>مثال: عملاء محليون، شركات، طلاب، مرضى، زوار Google...</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB,
    )
    return REQ_TARGET

async def req_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["req"]["target"] = update.message.text.strip()
    await update.message.reply_text(
        get_step_header(7, FORM_STEPS[6]) +
        "🚀 ما <b>الهدف الأساسي</b> من المشروع؟\n"
        "<i>مثال: جذب عملاء، استقبال طلبات، تنظيم بيانات...</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB,
    )
    return REQ_GOAL

async def req_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["req"]["goal"] = update.message.text.strip()
    await update.message.reply_text(
        get_step_header(8, FORM_STEPS[7]) +
        "📌 ما <b>وضعك الحالي</b>؟\n"
        "<i>مثال: لدي شعار، موقع قديم، ملفات Excel، فكرة فقط...</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB,
    )
    return REQ_STATUS_FIELD

async def req_status_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["req"]["current_status"] = update.message.text.strip()
    await update.message.reply_text(
        get_step_header(9, FORM_STEPS[8]) +
        "🧩 ما <b>المميزات المطلوبة</b>؟\n"
        "<i>مثال: واتساب، نموذج طلب، لوحة تحكم، تقارير، حجز، دفع...</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_KB,
    )
    return REQ_FEATURES

async def req_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["req"]["features"] = update.message.text.strip()
    await update.message.reply_text(
        get_step_header(10, FORM_STEPS[9]) +
        "📄 اكتب <b>الصفحات أو العناصر المطلوبة</b>:\n"
        "<i>للموقع: الرئيسية، من نحن، خدمات، أعمال، تواصل.\n"
        "للتصميم: المقاس، النصوص، الصور.\n"
        "للنظام: الشاشات، الجداول، التقارير.</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_SKIP_KB,
    )
    return REQ_PAGES

async def req_pages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["req"]["pages"] = "—"
    else:
        context.user_data["req"]["pages"] = update.message.text.strip()

    await (update.callback_query.message if update.callback_query else update.message).reply_text(
        get_step_header(11, FORM_STEPS[10]) +
        "🎨 ما <b>أسلوب التصميم المفضل</b>؟\n"
        "<i>مثال: داكن نيون، رسمي، فاخر، بسيط، تقني، ذهبي، طبي...</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_SKIP_KB,
    )
    return REQ_STYLE

async def req_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["req"]["style"] = "—"
    else:
        context.user_data["req"]["style"] = update.message.text.strip()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ لدي الشعار والمحتوى",     callback_data="content:ready")],
        [InlineKeyboardButton("🖼️ لدي الشعار فقط",          callback_data="content:logo")],
        [InlineKeyboardButton("📝 لدي المحتوى فقط",         callback_data="content:text")],
        [InlineKeyboardButton("❓ أحتاج تجهيز كل شيء",     callback_data="content:none")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="conv_cancel")],
    ])
    msg_target = update.callback_query.message if update.callback_query else update.message
    await msg_target.reply_text(
        get_step_header(12, FORM_STEPS[11]) +
        "🗂️ هل <b>المحتوى والشعار جاهزان</b>؟",
        parse_mode=ParseMode.HTML, reply_markup=keyboard,
    )
    return REQ_CONTENT

async def req_content_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mapping = {
        "ready": "✅ لدي الشعار والمحتوى.",
        "logo":  "🖼️ لدي الشعار فقط.",
        "text":  "📝 لدي المحتوى فقط.",
        "none":  "❓ أحتاج تجهيز كل شيء.",
    }
    key = q.data.split(":", 1)[1]
    context.user_data["req"]["content"] = mapping.get(key, "—")
    await q.message.reply_text(
        get_step_header(13, FORM_STEPS[12]) +
        "🔗 هل لديك <b>أمثلة أو روابط أو تصاميم تعجبك</b>؟\n"
        "<i>أرسل رابطًا أو صورة أو اكتب: لا يوجد</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_SKIP_KB,
    )
    return REQ_REFERENCES

async def req_references(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["req"].setdefault("attachments", [])
    msg = update.message

    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["req"]["references"] = "—"
        msg_target = update.callback_query.message
    elif msg and (msg.photo or msg.document):
        try:
            if msg.photo:
                f = await msg.photo[-1].get_file()
                fname = f"attach_{now_text().replace(' ','_').replace(':','-')}_{f.file_id}.jpg"
                await f.download_to_drive(str(ATTACHMENTS_DIR / fname))
                context.user_data["req"]["attachments"].append(fname)
            elif msg.document:
                f = await msg.document.get_file()
                orig = msg.document.file_name or f.file_id
                fname = f"attach_{now_text().replace(' ','_').replace(':','-')}_{orig}"
                await f.download_to_drive(str(ATTACHMENTS_DIR / fname))
                context.user_data["req"]["attachments"].append(fname)
            await msg.reply_text("✅ تم حفظ المرفق. أضف المزيد أو أكمل بكتابة: <b>تم</b>",
                                  parse_mode=ParseMode.HTML, reply_markup=CANCEL_SKIP_KB)
            return REQ_REFERENCES
        except Exception:
            logger.exception("attachment download failed")
            await msg.reply_text("⚠️ فشل حفظ المرفق. أعد الإرسال أو اكتب: لا يوجد")
            return REQ_REFERENCES
    else:
        context.user_data["req"]["references"] = msg.text.strip()
        msg_target = msg

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 ميزانية محدودة",            callback_data="budget:low")],
        [InlineKeyboardButton("💰 ميزانية متوسطة",           callback_data="budget:mid")],
        [InlineKeyboardButton("💎 مشروع متقدم (لا حدود)",    callback_data="budget:high")],
        [InlineKeyboardButton("📊 أريد عرض سعر بعد الدراسة", callback_data="budget:quote")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="conv_cancel")],
    ])
    await msg_target.reply_text(
        get_step_header(14, FORM_STEPS[13]) +
        "💰 اختر <b>الميزانية التقريبية</b>:",
        parse_mode=ParseMode.HTML, reply_markup=keyboard,
    )
    return REQ_BUDGET

async def req_budget_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mapping = {
        "low":   "💸 ميزانية محدودة",
        "mid":   "💰 ميزانية متوسطة",
        "high":  "💎 مشروع متقدم",
        "quote": "📊 عرض سعر بعد الدراسة",
    }
    key = q.data.split(":", 1)[1]
    context.user_data["req"]["budget"] = mapping.get(key, "—")
    await q.message.reply_text(
        get_step_header(15, FORM_STEPS[14]) +
        "⏱️ متى تريد <b>التسليم</b>؟\n"
        "<i>مثال: خلال أسبوع، شهر، غير مستعجل، حسب الاتفاق</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_SKIP_KB,
    )
    return REQ_DEADLINE

async def req_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["req"]["deadline"] = "حسب الاتفاق"
        msg_target = update.callback_query.message
    else:
        context.user_data["req"]["deadline"] = update.message.text.strip()
        msg_target = update.message

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 واتساب",      callback_data="contact_m:whatsapp")],
        [InlineKeyboardButton("✈️ تليجرام",    callback_data="contact_m:telegram")],
        [InlineKeyboardButton("📞 اتصال هاتفي", callback_data="contact_m:call")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="conv_cancel")],
    ])
    await msg_target.reply_text(
        get_step_header(16, FORM_STEPS[15]) +
        "💬 ما <b>طريقة التواصل المفضلة</b>؟",
        parse_mode=ParseMode.HTML, reply_markup=keyboard,
    )
    return REQ_CONTACT

async def req_contact_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mapping = {
        "whatsapp": "💬 واتساب",
        "telegram": "✈️ تليجرام",
        "call":     "📞 اتصال هاتفي",
    }
    key = q.data.split(":", 1)[1]
    context.user_data["req"]["contact_method"] = mapping.get(key, "—")
    await q.message.reply_text(
        get_step_header(17, FORM_STEPS[16]) +
        "📝 هل لديك <b>ملاحظات إضافية</b>؟\n"
        "<i>أو اكتب: لا يوجد</i>",
        parse_mode=ParseMode.HTML, reply_markup=CANCEL_SKIP_KB,
    )
    return REQ_NOTES

async def req_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["req"]["notes"] = "—"
        msg_target = update.callback_query.message
    else:
        context.user_data["req"]["notes"] = update.message.text.strip()
        msg_target = update.message

    data = context.user_data["req"]
    summary = format_request_summary(data)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تأكيد وإرسال الطلب", callback_data="confirm_req")],
        [InlineKeyboardButton("✏️ تعديل الطلب",        callback_data="edit_req")],
        [InlineKeyboardButton("❌ إلغاء الطلب",        callback_data="conv_cancel")],
    ])
    await msg_target.reply_text(
        "📋 <b>مراجعة الطلب قبل الإرسال</b>\n\n" + summary,
        parse_mode=ParseMode.HTML, reply_markup=keyboard,
    )
    return REQ_CONFIRM

async def req_confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action = q.data

    if action == "conv_cancel":
        context.user_data.pop("req", None)
        await q.message.reply_text("❌ تم إلغاء الطلب.", reply_markup=main_keyboard())
        return ConversationHandler.END

    if action == "edit_req":
        # عرض قائمة حقول للتعديل
        edit_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 الاسم",           callback_data="edit_field:name"),
             InlineKeyboardButton("📞 الهاتف",          callback_data="edit_field:phone")],
            [InlineKeyboardButton("🏷️ اسم المشروع",     callback_data="edit_field:project_name"),
             InlineKeyboardButton("🏢 النشاط",          callback_data="edit_field:activity")],
            [InlineKeyboardButton("🎯 الجمهور",         callback_data="edit_field:target"),
             InlineKeyboardButton("🚀 الهدف",           callback_data="edit_field:goal")],
            [InlineKeyboardButton("🧩 المميزات",        callback_data="edit_field:features"),
             InlineKeyboardButton("🎨 التصميم",         callback_data="edit_field:style")],
            [InlineKeyboardButton("💰 الميزانية",       callback_data="edit_field:budget"),
             InlineKeyboardButton("⏱️ الموعد",          callback_data="edit_field:deadline")],
            [InlineKeyboardButton("📝 ملاحظات",         callback_data="edit_field:notes")],
            [InlineKeyboardButton("🔙 رجوع للمراجعة",  callback_data="back_to_review")],
        ])
        await q.message.reply_text(
            "✏️ <b>اختر الحقل الذي تريد تعديله:</b>",
            parse_mode=ParseMode.HTML, reply_markup=edit_kb,
        )
        return REQ_EDIT_FIELD

    # تأكيد الإرسال
    data = context.user_data.get("req", {})
    data["telegram_id"]  = str(update.effective_user.id)
    data["username"]     = update.effective_user.username or ""

    req_id = save_request(data)

    # إشعار الإدارة
    admin_markup = None
    if req_id:
        admin_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔍 عرض الطلب",    callback_data=f"admin:viewreq:{req_id}:0"),
                InlineKeyboardButton("💬 رد مباشر",      callback_data=f"admin:reply:{req_id}"),
            ],
            [InlineKeyboardButton("✅ تم التواصل",       callback_data=f"admin:setstatus:{req_id}:contacted")],
        ])
    await send_admin_notification(
        context,
        f"🔔 <b>طلب جديد #{req_id}</b>\n\n" + format_request_summary(data),
        markup=admin_markup,
    )

    w_text = f"أهلًا مؤسسة الجحفلي، أرسلت طلب خدمة رقم #{req_id}.\nالاسم: {data.get('name')}\nالخدمة: {data.get('service')}"
    await q.message.reply_text(
        f"🎉 <b>تم استلام طلبك بنجاح!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔖 <b>رقم طلبك:</b> <code>#{req_id}</code>\n\n"
        "✅ سيتم مراجعة تفاصيل الطلب والتواصل معك لتقديم العرض المناسب.\n"
        "⏰ وقت الرد المتوقع: خلال 24 ساعة عمل.\n\n"
        "يمكنك متابعة حالة طلبك عبر الأمر: /mystatus",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 متابعة عبر واتساب", url=wa_link(w_text))],
            [InlineKeyboardButton("📊 متابعة الطلب",      callback_data=f"myreq:{req_id}")],
            nav_row(back_data="home"),
        ]),
    )
    context.user_data.pop("req", None)
    return ConversationHandler.END

async def req_edit_field_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action = q.data

    if action == "back_to_review":
        data = context.user_data.get("req", {})
        summary = format_request_summary(data)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تأكيد وإرسال الطلب", callback_data="confirm_req")],
            [InlineKeyboardButton("✏️ تعديل الطلب",        callback_data="edit_req")],
            [InlineKeyboardButton("❌ إلغاء الطلب",        callback_data="conv_cancel")],
        ])
        await q.message.reply_text(
            "📋 <b>مراجعة الطلب:</b>\n\n" + summary,
            parse_mode=ParseMode.HTML, reply_markup=keyboard,
        )
        return REQ_CONFIRM

    field = action.split(":", 1)[1]
    field_labels = {
        "name": "الاسم الكامل", "phone": "رقم الهاتف",
        "project_name": "اسم المشروع", "activity": "نوع النشاط",
        "target": "الجمهور المستهدف", "goal": "الهدف",
        "features": "المميزات المطلوبة", "style": "أسلوب التصميم",
        "budget": "الميزانية", "deadline": "موعد التسليم", "notes": "الملاحظات",
    }
    label = field_labels.get(field, field)
    context.user_data["editing_field"] = field
    current = context.user_data.get("req", {}).get(field, "—")
    await q.message.reply_text(
        f"✏️ <b>تعديل: {label}</b>\n\n"
        f"القيمة الحالية: <i>{current}</i>\n\n"
        "اكتب القيمة الجديدة:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 إلغاء التعديل", callback_data="back_to_review")
        ]]),
    )
    return REQ_EDIT_FIELD

async def req_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data.get("editing_field")
    if field:
        context.user_data["req"][field] = update.message.text.strip()
        await update.message.reply_text(
            f"✅ تم تحديث <b>{field}</b> بنجاح.",
            parse_mode=ParseMode.HTML,
        )
    data = context.user_data.get("req", {})
    summary = format_request_summary(data)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تأكيد وإرسال الطلب", callback_data="confirm_req")],
        [InlineKeyboardButton("✏️ تعديل الطلب",        callback_data="edit_req")],
        [InlineKeyboardButton("❌ إلغاء الطلب",        callback_data="conv_cancel")],
    ])
    await update.message.reply_text(
        "📋 <b>مراجعة الطلب (بعد التعديل):</b>\n\n" + summary,
        parse_mode=ParseMode.HTML, reply_markup=keyboard,
    )
    return REQ_CONFIRM

async def conv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("req", None)
    context.user_data.pop("editing_field", None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("❌ تم إلغاء الطلب.", reply_markup=main_keyboard())
    else:
        await update.message.reply_text("❌ تم إلغاء العملية.", reply_markup=main_keyboard())
    return ConversationHandler.END

# ==============================================================
# ConversationHandler – رد الإدارة المباشر
# ==============================================================
async def admin_reply_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    req_id = int(q.data.split(":", 1)[1])
    req = get_request_by_id(req_id)
    if not req:
        await q.message.reply_text("⚠️ الطلب غير موجود.")
        return ConversationHandler.END
    context.user_data["admin_reply_req_id"]     = req_id
    context.user_data["admin_reply_telegram_id"] = req["telegram_id"]
    context.user_data["admin_reply_name"]        = req["name"]
    await q.message.reply_text(
        f"✍️ اكتب رسالتك للعميل <b>{req['name']}</b> (طلب #{req_id}):\n\n"
        "أو اكتب /cancel للإلغاء.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ إلغاء", callback_data="noop")
        ]]),
    )
    return ADMIN_REPLY_MSG

async def admin_reply_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req_id     = context.user_data.get("admin_reply_req_id")
    tg_id      = context.user_data.get("admin_reply_telegram_id")
    name       = context.user_data.get("admin_reply_name", "العميل")
    admin_msg  = update.message.text.strip()

    if tg_id:
        try:
            await context.bot.send_message(
                chat_id=int(tg_id),
                text=(
                    f"📨 <b>رسالة من مؤسسة الجحفلي</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{admin_msg}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"للتواصل المباشر: {wa_link()}"
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💬 رد عبر واتساب", url=wa_link()),
                ]]),
            )
            # حفظ في سجل الرسائل
            cur = DB_CONN.cursor()
            cur.execute("""
                INSERT INTO admin_messages (request_id, telegram_id, message, sent_at)
                VALUES (?,?,?,?)
            """, (req_id, tg_id, admin_msg, now_text()))
            DB_CONN.commit()
            await update.message.reply_text(
                f"✅ تم إرسال الرسالة بنجاح إلى <b>{name}</b>.",
                parse_mode=ParseMode.HTML,
                reply_markup=admin_main_keyboard(),
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ فشل الإرسال: {e}")
    else:
        await update.message.reply_text("⚠️ لم يتم العثور على معرف العميل.")

    context.user_data.pop("admin_reply_req_id", None)
    context.user_data.pop("admin_reply_telegram_id", None)
    context.user_data.pop("admin_reply_name", None)
    return ConversationHandler.END

# ==============================================================
# ConversationHandler – رسالة جماعية
# ==============================================================
async def admin_broadcast_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(
        "📢 <b>إرسال رسالة جماعية</b>\n\n"
        "اكتب الرسالة التي تريد إرسالها لجميع المستخدمين:\n\n"
        "أو /cancel للإلغاء.",
        parse_mode=ParseMode.HTML,
    )
    return ADMIN_BROADCAST_MSG

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_text = update.message.text.strip()
    cur = DB_CONN.cursor()
    cur.execute("SELECT telegram_id FROM users")
    users = [r["telegram_id"] for r in cur.fetchall()]
    sent, failed = 0, 0
    broadcast_text = (
        f"📢 <b>إشعار من مؤسسة الجحفلي</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"{msg_text}"
    )
    for uid in users:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=broadcast_text,
                parse_mode=ParseMode.HTML,
            )
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📊 <b>نتيجة الإرسال الجماعي</b>\n\n"
        f"✅ تم الإرسال: {sent}\n"
        f"❌ فشل: {failed}",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_main_keyboard(),
    )
    return ConversationHandler.END

# ==============================================================
# Callback Router العام
# ==============================================================
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data or ""
    await q.answer()

    # ── تجاهل noop
    if data == "noop":
        return

    # ── الرئيسية
    if data == "home":
        user = update.effective_user
        caption = (
            f"✨ <b>أهلًا {user.first_name}!</b>\n\n"
            f"<b>{COMPANY['tagline']}</b>\n\n"
            "اختر من الأزرار أدناه:"
        )
        await q.message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=welcome_keyboard())
        return

    # ── الخدمات
    if data == "show_services":
        await q.message.reply_text(
            "🌐 <b>خدماتنا الرقمية الشاملة</b>\n\nاختر الخدمة لمعرفة التفاصيل:",
            parse_mode=ParseMode.HTML, reply_markup=services_keyboard("home"),
        )
        return

    # ── الباقات
    if data == "show_packages":
        await q.message.reply_text(
            "📦 <b>الباقات الاحترافية</b>\n\nاختر الباقة لمعرفة مميزاتها:",
            parse_mode=ParseMode.HTML, reply_markup=packages_keyboard("home"),
        )
        return

    # ── الأسئلة الشائعة
    if data == "show_faq":
        await q.message.reply_text(
            "❓ <b>مركز الأسئلة الشائعة</b>\n\nاختر التصنيف:",
            parse_mode=ParseMode.HTML, reply_markup=faq_categories_keyboard("home"),
        )
        return

    # ── الترشيح
    if data == "show_recommend":
        await q.message.reply_text(
            "🔍 <b>ترشيح الخدمة المناسبة</b>\n\nاختر أقرب وصف لاحتياجك:",
            parse_mode=ParseMode.HTML, reply_markup=recommend_keyboard(),
        )
        return

    # ── أعمالنا
    if data == "show_portfolio":
        lines = ["🧾 <b>نماذج من أعمالنا</b>\n"]
        for i, (title, desc, _) in enumerate(PORTFOLIO):
            lines.append(f"{i+1}. <b>{title}</b>\n   {desc}\n")
        await q.message.reply_text(
            "\n".join(lines), parse_mode=ParseMode.HTML,
            reply_markup=portfolio_keyboard("home"),
        )
        return

    # ── تفاصيل مشروع
    if data.startswith("portfolio:"):
        idx = int(data.split(":", 1)[1])
        title, desc, svc_key = PORTFOLIO[idx]
        svc = SERVICES.get(svc_key, {})
        text = (
            f"<b>{title}</b>\n\n"
            f"📝 {desc}\n\n"
            f"🔗 <b>الخدمة المرتبطة:</b> {svc.get('title', '')}\n"
            f"📌 {svc.get('short', '')}"
        )
        await q.message.reply_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 طلب خدمة مشابهة", callback_data="start_request")],
                nav_row(back_data="show_portfolio"),
            ]),
        )
        return

    # ── التواصل
    if data == "contact":
        text = (
            "☎️ <b>تواصل معنا</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            f"📞 <b>الهاتف:</b> <code>{COMPANY_PHONE}</code>\n"
            f"💬 <b>واتساب:</b> {WHATSAPP_NUMBER}\n"
            f"📧 <b>البريد:</b> {COMPANY_EMAIL}\n"
            f"🌍 <b>الموقع:</b> {COMPANY_WEBSITE}\n"
            f"📍 <b>الموقع الجغرافي:</b> {COMPANY_LOCATION}\n\n"
            "⏰ <b>أوقات الرد:</b> السبت – الخميس، 8 ص – 10 م"
        )
        await q.message.reply_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=contact_keyboard(),
        )
        return

    # ── تفاصيل خدمة
    if data.startswith("service:"):
        key = data.split(":", 1)[1]
        s = SERVICES.get(key)
        if not s:
            return
        details = "\n".join([f"  ✔️ {x}" for x in s["details"]])
        text = (
            f"{s['title']}\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 <b>وصف مختصر:</b>\n{s['short']}\n\n"
            f"📋 <b>ماذا تشمل الخدمة؟</b>\n{details}\n\n"
            f"💡 <b>عند الطلب سنسألك عن:</b>\n{s['ask_hint']}"
        )
        await q.message.reply_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 طلب هذه الخدمة", callback_data="start_request")],
                [InlineKeyboardButton("💬 واتساب", url=wa_link(f"أريد طلب خدمة: {s['title']}"))],
                nav_row(back_data="show_services"),
            ]),
        )
        return

    # ── تفاصيل باقة
    if data.startswith("package:"):
        key = data.split(":", 1)[1]
        p = PACKAGES.get(key)
        if not p:
            return
        features = "\n".join([f"  {f}" for f in p["features"]])
        text = (
            f"{p['icon']} <b>{p['title']}</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 {p['desc']}\n\n"
            f"🌟 <b>مميزات الباقة:</b>\n{features}"
        )
        await q.message.reply_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 طلب هذه الباقة",    callback_data="start_request")],
                [InlineKeyboardButton("💬 استفسار واتساب",    url=wa_link(f"أريد الاستفسار عن: {p['title']}"))],
                nav_row(back_data="show_packages"),
            ]),
        )
        return

    # ── عن الجحفلي
    if data.startswith("about:"):
        part = data.split(":", 1)[1]
        if part == "intro":
            text = (
                f"ℹ️ <b>{COMPANY['name']}</b>\n\n"
                f"{COMPANY['intro']}"
            )
        elif part == "details":
            text = f"📌 <b>نبذة تفصيلية</b>\n\n{COMPANY['about']}"
        elif part == "vision":
            text = (
                f"👁️ <b>رؤيتنا</b>\n{COMPANY['vision']}\n\n"
                f"🎯 <b>رسالتنا</b>\n{COMPANY['mission']}"
            )
        elif part == "values":
            text = (
                "💎 <b>قيمنا الأساسية</b>\n\n"
                "• <b>الجودة:</b> إخراج عمل مرتب وواضح.\n"
                "• <b>الوضوح:</b> شرح المطلوب دون تعقيد.\n"
                "• <b>الابتكار:</b> أفكار حديثة وجذابة.\n"
                "• <b>الالتزام:</b> احترام الوقت والمتطلبات.\n"
                "• <b>الدعم:</b> متابعة حسب الاتفاق.\n"
                "• <b>الثقة:</b> حفظ بيانات العميل والشفافية."
            )
        elif part == "steps":
            text = (
                "⚙️ <b>آلية العمل</b>\n\n"
                "1️⃣ فهم الفكرة والهدف بدقة.\n"
                "2️⃣ تحليل المتطلبات والمحتوى.\n"
                "3️⃣ إعداد التصور والاقتراح.\n"
                "4️⃣ التصميم والتنفيذ التقني.\n"
                "5️⃣ المراجعة والتحسين.\n"
                "6️⃣ التسليم والمتابعة."
            )
        else:
            text = (
                "✨ <b>لماذا الجحفلي؟</b>\n\n"
                "• لأننا نربط التصميم بهدف المشروع.\n"
                "• لأننا نهتم بالمحتوى وتجربة المستخدم.\n"
                "• لأن خدماتنا متعددة في مكان واحد.\n"
                "• لأن التواصل مع العملاء يصبح أسهل.\n"
                "• لأن الحل قابل للتطوير مستقبلًا.\n"
                "• لأننا نهتم بالجودة والالتزام بالمواعيد."
            )
        await q.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=about_keyboard("home"))
        return

    # ── تصنيف الأسئلة الشائعة
    if data.startswith("faqcat:"):
        key = data.split(":", 1)[1]
        cat = FAQ_CATEGORIES.get(key)
        if not cat:
            return
        buttons = [
            [InlineKeyboardButton(f"❓ {question}", callback_data=f"faq:{key}:{i}")]
            for i, (question, _) in enumerate(cat["items"])
        ]
        buttons.append([InlineKeyboardButton("🔙 تصنيفات الأسئلة", callback_data="show_faq")])
        buttons.append(nav_row(back_data="show_faq"))
        await q.message.reply_text(
            f"{cat['icon']} <b>{cat['title']}</b>\n\nاختر السؤال:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    # ── سؤال محدد
    if data.startswith("faq:"):
        parts = data.split(":", 2)
        key, i = parts[1], int(parts[2])
        question, answer = FAQ_CATEGORIES[key]["items"][i]
        await q.message.reply_text(
            f"❓ <b>{question}</b>\n\n💡 {answer}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 أسئلة نفس التصنيف", callback_data=f"faqcat:{key}")],
                [InlineKeyboardButton("📩 طلب خدمة",           callback_data="start_request")],
                nav_row(back_data=f"faqcat:{key}"),
            ]),
        )
        return

    # ── متابعة طلب المستخدم
    if data.startswith("myreq:"):
        req_id = int(data.split(":", 1)[1])
        req = get_request_by_id(req_id)
        if not req or str(req["telegram_id"]) != str(update.effective_user.id):
            await q.message.reply_text("⚠️ لم يتم العثور على الطلب.")
            return
        st = REQUEST_STATUSES.get(req.get("req_status", "new"), ("🆕", "جديد"))
        # سجل الحالات
        cur = DB_CONN.cursor()
        cur.execute("""
            SELECT old_status, new_status, note, changed_at
            FROM status_history WHERE request_id=? ORDER BY id DESC LIMIT 5
        """, (req_id,))
        history = cur.fetchall()
        hist_text = ""
        if history:
            hist_text = "\n\n🕐 <b>سجل التحديثات:</b>\n"
            for h in reversed(history):
                os_ = REQUEST_STATUSES.get(h["old_status"], ("", h["old_status"]))
                ns_ = REQUEST_STATUSES.get(h["new_status"], ("", h["new_status"]))
                hist_text += f"• {os_[0]}{os_[1]} ➜ {ns_[0]}{ns_[1]}  <i>({h['changed_at'][:10]})</i>\n"

        text = (
            f"📋 <b>تفاصيل الطلب #{req_id}</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>الخدمة:</b> {req.get('service', '-')}\n"
            f"🏷️ <b>المشروع:</b> {req.get('project_name', '-')}\n"
            f"📊 <b>الحالة الحالية:</b> {st[0]} <b>{st[1]}</b>\n"
            f"🕒 <b>تاريخ الطلب:</b> {req.get('created_at', '-')[:10]}"
            + hist_text
        )

        extra_kb = []
        if req.get("req_status") == "done" and not req.get("rating"):
            extra_kb.append([InlineKeyboardButton("⭐ قيّم تجربتك", callback_data=f"start_rate:{req_id}")])

        extra_kb.append(nav_row(back_data="show_mystatus"))
        await q.message.reply_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(extra_kb),
        )
        return

    if data == "show_mystatus":
        user_id = str(update.effective_user.id)
        requests = get_requests_by_user(user_id)
        if not requests:
            await q.message.reply_text(
                "📊 لا توجد طلبات بعد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📩 تقديم طلب", callback_data="start_request")]
                ]),
            )
            return
        await q.message.reply_text(
            f"📊 <b>طلباتي ({len(requests)} طلب)</b>\n\nاختر الطلب:",
            parse_mode=ParseMode.HTML,
            reply_markup=my_requests_keyboard(requests),
        )
        return

    # ── تقييم
    if data.startswith("start_rate:"):
        req_id = int(data.split(":", 1)[1])
        await q.message.reply_text(
            "⭐ <b>قيّم تجربتك معنا</b>\n\n"
            "كيف تقيّم الخدمة التي تلقيتها؟",
            parse_mode=ParseMode.HTML,
            reply_markup=rating_keyboard(req_id),
        )
        return

    if data.startswith("rate:"):
        parts = data.split(":")
        req_id, stars = int(parts[1]), int(parts[2])
        req = get_request_by_id(req_id)
        if req and str(req["telegram_id"]) == str(update.effective_user.id):
            cur = DB_CONN.cursor()
            cur.execute("UPDATE service_requests SET rating=? WHERE id=?", (stars, req_id))
            DB_CONN.commit()
            star_text = "⭐" * stars
            await q.message.reply_text(
                f"🙏 <b>شكرًا على تقييمك!</b>\n\n"
                f"تقييمك: {star_text} ({stars}/5)\n\n"
                "رأيك يساعدنا على تحسين خدماتنا باستمرار.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([nav_row(back_data="home")]),
            )
            # إشعار الإدارة
            await send_admin_notification(
                context,
                f"⭐ تقييم جديد للطلب #{req_id}\n"
                f"العميل: {req.get('name', '-')}\n"
                f"التقييم: {star_text} ({stars}/5)"
            )
        else:
            await q.message.reply_text("⚠️ لا يمكن تقييم هذا الطلب.")
        return

    # ── لوحة الإدارة
    if data.startswith("admin:"):
        if not is_admin(update.effective_user.id):
            await q.message.reply_text("⛔ غير مصرح.")
            return
        await handle_admin_callback(q, data, context)
        return

    # ── conv_cancel عبر كول باك
    if data == "conv_cancel":
        context.user_data.pop("req", None)
        await q.message.reply_text("❌ تم إلغاء الطلب.", reply_markup=main_keyboard())
        return

# ==============================================================
# معالجة callbacks الإدارة
# ==============================================================
async def handle_admin_callback(q, data: str, context: ContextTypes.DEFAULT_TYPE):
    parts = data.split(":")
    action = parts[1] if len(parts) > 1 else ""

    # لوحة رئيسية
    if action == "main":
        stats = get_stats()
        text = (
            "👑 <b>لوحة إدارة بوت الجحفلي</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👥 المستخدمون: <b>{stats.get('users', 0)}</b>\n"
            f"📋 إجمالي الطلبات: <b>{stats.get('total', 0)}</b>\n"
            f"🆕 جديدة: <b>{stats.get('new', 0)}</b>\n"
            f"⚙️ قيد التنفيذ: <b>{stats.get('in_progress', 0)}</b>\n"
            f"✅ مكتملة: <b>{stats.get('done', 0)}</b>"
        )
        await q.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_main_keyboard())
        return

    # إحصائيات
    if action == "stats":
        stats = get_stats()
        top = stats.get("top_services", [])
        top_text = "\n".join([f"  • {SERVICES.get(k, {}).get('title', k)}: {c} طلب" for k, c in top])
        text = (
            "📊 <b>إحصائيات البوت</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👥 إجمالي المستخدمين: <b>{stats.get('users', 0)}</b>\n"
            f"📋 إجمالي الطلبات: <b>{stats.get('total', 0)}</b>\n\n"
            "<b>📌 توزيع الحالات:</b>\n"
            f"  🆕 جديدة: {stats.get('new', 0)}\n"
            f"  🔍 قيد المراجعة: {stats.get('reviewing', 0) if 'reviewing' in stats else 0}\n"
            f"  📞 تم التواصل: {stats.get('contacted', 0) if 'contacted' in stats else 0}\n"
            f"  ⚙️ قيد التنفيذ: {stats.get('in_progress', 0)}\n"
            f"  ✅ مكتملة: {stats.get('done', 0)}\n\n"
            f"<b>🏆 أكثر الخدمات طلبًا:</b>\n{top_text or '  لا بيانات بعد'}"
        )
        await q.message.reply_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin:main")
            ]]),
        )
        return

    # قائمة الطلبات
    if action == "requests":
        page = int(parts[2]) if len(parts) > 2 else 0
        reqs = get_recent_requests(limit=5, offset=page * 5)
        cur = DB_CONN.cursor()
        cur.execute("SELECT COUNT(*) as c FROM service_requests")
        total = cur.fetchone()["c"]
        total_pages = max(1, (total + 4) // 5)
        if not reqs:
            await q.message.reply_text(
                "📋 لا توجد طلبات.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin:main")
                ]]),
            )
            return
        text = f"📋 <b>قائمة الطلبات</b> (صفحة {page+1}/{total_pages})\n━━━━━━━━━━━━━━━━━━━\n"
        await q.message.reply_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=requests_list_keyboard(reqs, page, total_pages),
        )
        return

    # تصفية الطلبات
    if action == "filter":
        status_f = parts[2] if len(parts) > 2 else None
        page = int(parts[3]) if len(parts) > 3 else 0
        reqs = get_recent_requests(limit=5, offset=page * 5, status_filter=status_f)
        cur = DB_CONN.cursor()
        if status_f:
            cur.execute("SELECT COUNT(*) as c FROM service_requests WHERE req_status=?", (status_f,))
        else:
            cur.execute("SELECT COUNT(*) as c FROM service_requests")
        total = cur.fetchone()["c"]
        total_pages = max(1, (total + 4) // 5)
        st_label = status_label(status_f) if status_f else "جميع الطلبات"
        if not reqs:
            await q.message.reply_text(
                f"📋 لا توجد طلبات في حالة: {st_label}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin:main")
                ]]),
            )
            return
        await q.message.reply_text(
            f"📋 <b>{st_label}</b> ({total} طلب) — صفحة {page+1}/{total_pages}",
            parse_mode=ParseMode.HTML,
            reply_markup=requests_list_keyboard(reqs, page, total_pages, filter_status=status_f),
        )
        return

    # عرض طلب محدد
    if action == "viewreq":
        req_id = int(parts[2]) if len(parts) > 2 else 0
        page   = int(parts[3]) if len(parts) > 3 else 0
        req    = get_request_by_id(req_id)
        if not req:
            await q.message.reply_text("⚠️ الطلب غير موجود.")
            return
        text = format_request_summary(req)
        await q.message.reply_text(
            f"📋 <b>طلب #{req_id}</b>\n\n" + text,
            parse_mode=ParseMode.HTML,
            reply_markup=admin_request_keyboard(req_id, req.get("req_status", "new"), page),
        )
        return

    # تغيير الحالة
    if action == "setstatus":
        req_id     = int(parts[2]) if len(parts) > 2 else 0
        new_status = parts[3] if len(parts) > 3 else "new"
        req = get_request_by_id(req_id)
        if not req:
            await q.message.reply_text("⚠️ الطلب غير موجود.")
            return
        old_st = req.get("req_status", "new")
        if update_request_status(req_id, new_status):
            old_label = status_label(old_st)
            new_label = status_label(new_status)
            await q.message.reply_text(
                f"✅ تم تحديث حالة الطلب #{req_id}\n"
                f"{old_label} ➜ {new_label}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📋 عرض الطلب", callback_data=f"admin:viewreq:{req_id}:0"),
                    InlineKeyboardButton("🔙 لوحة الإدارة", callback_data="admin:main"),
                ]]),
            )
            # إشعار العميل بتغيير الحالة
            if req.get("telegram_id"):
                nl = status_label(new_status)
                await notify_user(
                    context,
                    req["telegram_id"],
                    f"🔔 <b>تحديث على طلبك #{req_id}</b>\n\n"
                    f"🌐 <b>الخدمة:</b> {req.get('service', '-')}\n"
                    f"📊 <b>الحالة الجديدة:</b> {nl}\n\n"
                    "يمكنك متابعة طلبك عبر: /mystatus",
                    markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 متابعة الطلب", callback_data=f"myreq:{req_id}")],
                        [InlineKeyboardButton("💬 تواصل معنا", url=wa_link())],
                    ]),
                )
        else:
            await q.message.reply_text("⚠️ فشل تحديث الحالة.")
        return

    # سجل الحالات
    if action == "history":
        req_id = int(parts[2]) if len(parts) > 2 else 0
        cur = DB_CONN.cursor()
        cur.execute("""
            SELECT old_status, new_status, note, changed_at
            FROM status_history WHERE request_id=? ORDER BY id DESC LIMIT 10
        """, (req_id,))
        rows = cur.fetchall()
        if not rows:
            await q.message.reply_text(f"📜 لا يوجد سجل لتغييرات الطلب #{req_id}.")
            return
        lines = [f"📜 <b>سجل حالات الطلب #{req_id}</b>\n━━━━━━━━━━━━━━━━━━━"]
        for r in reversed(rows):
            os_ = status_label(r["old_status"])
            ns_ = status_label(r["new_status"])
            lines.append(f"• {os_} ➜ {ns_}\n  <i>{r['changed_at']}</i>")
        await q.message.reply_text(
            "\n".join(lines), parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 عرض الطلب", callback_data=f"admin:viewreq:{req_id}:0"),
            ]]),
        )
        return

# ==============================================================
# Router النصوص
# ==============================================================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.strip()
    upsert_user(update.effective_user)

    dispatch = {
        "🏠 الرئيسية":       cmd_start,
        "الرئيسية":           cmd_start,
        "🌐 الخدمات":        cmd_services,
        "📦 الباقات":         cmd_packages,
        "📩 طلب خدمة":       None,  # يُعالَج بـ ConversationHandler
        "❓ الأسئلة الشائعة": cmd_faq,
        "ℹ️ عن الجحفلي":     cmd_about,
        "🧾 أعمالنا":         cmd_portfolio,
        "🔍 ترشيح الخدمة":   cmd_recommend,
        "☎️ تواصل معنا":     cmd_contact,
        "📊 طلباتي":          cmd_mystatus,
    }

    if t in dispatch:
        fn = dispatch[t]
        if fn:
            await fn(update, context)
        else:
            # طلب خدمة – يبدأ ConversationHandler
            await req_entry(update, context)
    else:
        # بحث ذكي
        query = t.lower()
        found = []
        for key, svc in SERVICES.items():
            if any(word in svc["title"].lower() or word in svc["short"].lower()
                   for word in query.split()):
                found.append((key, svc))

        if found:
            rows = [[InlineKeyboardButton(v["title"], callback_data=f"service:{k}")] for k, v in found[:3]]
            rows.append(nav_row(back_data="home"))
            await update.message.reply_text(
                f"🔎 وجدنا هذه الخدمات المشابهة لـ \"<b>{t}</b>\":",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(rows),
            )
        else:
            await update.message.reply_text(
                "🤔 لم أفهم طلبك. اختر من القائمة أو اكتب /start للعودة.",
                reply_markup=main_keyboard(),
            )

# ==============================================================
# بناء التطبيق
# ==============================================================
def build_app() -> Application:
    if BOT_TOKEN in ("PUT_YOUR_BOT_TOKEN_HERE", "") or not BOT_TOKEN:
        raise RuntimeError("❌ ضع BOT_TOKEN في ملف .env قبل التشغيل.")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .post_init(set_bot_commands)
        .build()
    )

    # ── ConversationHandler: نموذج طلب الخدمة
    request_conv = ConversationHandler(
        entry_points=[
            CommandHandler("request", req_entry),
            CallbackQueryHandler(req_entry, pattern="^start_request$"),
            MessageHandler(filters.Regex("^📩 طلب خدمة$") & ~filters.COMMAND, req_entry),
        ],
        states={
            REQ_NAME:         [MessageHandler(filters.TEXT & ~filters.COMMAND, req_name)],
            REQ_PHONE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, req_phone)],
            REQ_SERVICE:      [CallbackQueryHandler(req_service_cb, pattern="^rq_svc:")],
            REQ_PROJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_project_name)],
            REQ_ACTIVITY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, req_activity)],
            REQ_TARGET:       [MessageHandler(filters.TEXT & ~filters.COMMAND, req_target)],
            REQ_GOAL:         [MessageHandler(filters.TEXT & ~filters.COMMAND, req_goal)],
            REQ_STATUS_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_status_field)],
            REQ_FEATURES:     [MessageHandler(filters.TEXT & ~filters.COMMAND, req_features)],
            REQ_PAGES: [
                CallbackQueryHandler(req_pages, pattern="^conv_skip$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, req_pages),
            ],
            REQ_STYLE: [
                CallbackQueryHandler(req_style, pattern="^conv_skip$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, req_style),
            ],
            REQ_CONTENT:    [CallbackQueryHandler(req_content_cb, pattern="^content:")],
            REQ_REFERENCES: [
                CallbackQueryHandler(req_references, pattern="^conv_skip$"),
                MessageHandler(
                    (filters.TEXT | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND,
                    req_references
                ),
            ],
            REQ_BUDGET:   [CallbackQueryHandler(req_budget_cb, pattern="^budget:")],
            REQ_DEADLINE: [
                CallbackQueryHandler(req_deadline, pattern="^conv_skip$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, req_deadline),
            ],
            REQ_CONTACT: [CallbackQueryHandler(req_contact_cb, pattern="^contact_m:")],
            REQ_NOTES: [
                CallbackQueryHandler(req_notes, pattern="^conv_skip$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, req_notes),
            ],
            REQ_CONFIRM: [
                CallbackQueryHandler(req_confirm_cb, pattern="^(confirm_req|edit_req|conv_cancel)$"),
            ],
            REQ_EDIT_FIELD: [
                CallbackQueryHandler(req_edit_field_cb, pattern="^(edit_field:|back_to_review)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, req_edit_text),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", conv_cancel),
            CallbackQueryHandler(conv_cancel, pattern="^conv_cancel$"),
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=True,
    )

    # ── ConversationHandler: رد الإدارة
    admin_reply_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_reply_entry, pattern="^admin:reply:"),
        ],
        states={
            ADMIN_REPLY_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply_send),
            ],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel)],
        allow_reentry=True,
    )

    # ── ConversationHandler: رسالة جماعية
    broadcast_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_broadcast_entry, pattern="^admin:broadcast$"),
        ],
        states={
            ADMIN_BROADCAST_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send),
            ],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel)],
        allow_reentry=True,
    )

    # الترتيب مهم: ConversationHandlers أولًا
    app.add_handler(request_conv)
    app.add_handler(admin_reply_conv)
    app.add_handler(broadcast_conv)

    # أوامر عامة
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("services",   cmd_services))
    app.add_handler(CommandHandler("packages",   cmd_packages))
    app.add_handler(CommandHandler("about",      cmd_about))
    app.add_handler(CommandHandler("portfolio",  cmd_portfolio))
    app.add_handler(CommandHandler("faq",        cmd_faq))
    app.add_handler(CommandHandler("contact",    cmd_contact))
    app.add_handler(CommandHandler("recommend",  cmd_recommend))
    app.add_handler(CommandHandler("search",     cmd_search))
    app.add_handler(CommandHandler("mystatus",   cmd_mystatus))
    app.add_handler(CommandHandler("admin",      cmd_admin))

    # Callback عام
    app.add_handler(CallbackQueryHandler(callback_router))

    # Router النصوص
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    return app

# ==============================================================
# نقطة البداية
# ==============================================================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🚀 Al-Jahfali Digital Solutions Bot v3.0 Starting...")
    logger.info("=" * 60)
    application = build_app()
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
