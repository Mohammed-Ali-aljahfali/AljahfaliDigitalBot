# -*- coding: utf-8 -*-
"""
بوت مؤسسة الجحفلي للحلول الرقمية - Mega Fixed Version
جاهز للتشغيل - Python 3.10+
Library: python-telegram-bot==21.6

طريقة التشغيل:
1) pip install -r requirements.txt
2) انسخ .env.example إلى .env
3) ضع BOT_TOKEN و ADMIN_CHAT_ID
4) python bot.py
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
from typing import Dict, Any

from dotenv import load_dotenv
import sqlite3
from sqlite3 import Connection
import pathlib
import json as _json
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
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

# ==========================
# إعدادات البوت
# ==========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+967782611415")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "967782611415")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "info@example.com")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "https://example.com")
COMPANY_LOCATION = os.getenv("COMPANY_LOCATION", "اليمن")

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo-aljahfali.png"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
REQUESTS_FILE = DATA_DIR / "service_requests.jsonl"
DB_PATH = DATA_DIR / "service_requests.db"
ATTACHMENTS_DIR = DATA_DIR / "attachments"
ATTACHMENTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("aljahfali-mega-bot")

# ==========================
# حالات نموذج طلب الخدمة
# ==========================
(
    REQ_NAME,
    REQ_PHONE,
    REQ_SERVICE,
    REQ_PROJECT_NAME,
    REQ_ACTIVITY,
    REQ_TARGET,
    REQ_GOAL,
    REQ_STATUS,
    REQ_FEATURES,
    REQ_PAGES,
    REQ_STYLE,
    REQ_CONTENT,
    REQ_REFERENCES,
    REQ_BUDGET,
    REQ_DEADLINE,
    REQ_CONTACT,
    REQ_NOTES,
    REQ_CONFIRM,
) = range(18)

# ==========================
# محتوى المؤسسة
# ==========================
COMPANY = {
    "name": "مؤسسة الجحفلي للحلول الرقمية",
    "en": "Al-Jahfali Digital Solutions",
    "tagline": "نحو حلول تقنية ذكية تصنع فرقًا في أعمالك.",
    "intro": (
        "مؤسسة تقنية إبداعية تقدم حلولًا رقمية متكاملة للأفراد والشركات والمؤسسات، "
        "تشمل تصميم المواقع، تطوير الأنظمة، تطبيقات الجوال، قواعد البيانات، الأتمتة، "
        "الهوية الرقمية، التصميم الإعلاني، تصميم التهاني، وتحسين الظهور في Google."
    ),
    "about": (
        "في مؤسسة الجحفلي للحلول الرقمية نؤمن أن التقنية ليست مجرد شكل جميل، بل وسيلة لتنظيم العمل، "
        "جذب العملاء، تسهيل التواصل، وتحويل الأفكار إلى حلول عملية. نبدأ بفهم نشاط العميل وهدفه، "
        "ثم نبني الحل المناسب من حيث التصميم، المحتوى، تجربة المستخدم، وسهولة الإدارة والتطوير."
    ),
    "vision": "أن نكون خيارًا موثوقًا في تقديم حلول رقمية ذكية ترفع جودة الأعمال وتحسن حضورها الرقمي.",
    "mission": "تقديم خدمات رقمية احترافية تجمع بين الإبداع، التقنية، الجودة، الوضوح، وسهولة الاستخدام.",
}

SERVICES: Dict[str, Dict[str, Any]] = {
    "web": {
        "title": "🌐 تصميم وتطوير المواقع الإلكترونية",
        "short": "مواقع تعريفية وتجارية وخدمية جذابة ومتجاوبة مع جميع الأجهزة.",
        "details": [
            "تصميم صفحة رئيسية قوية وجاذبة.",
            "صفحات: من نحن، خدماتنا، أعمالنا، الباقات، تواصل معنا.",
            "ربط واتساب ونموذج طلب خدمة.",
            "تهيئة SEO أساسية.",
            "تصميم متجاوب للجوال والتابلت والكمبيوتر.",
            "إمكانية التطوير لاحقًا إلى لوحة تحكم.",
        ],
        "ask_hint": "عدد الصفحات، الأقسام، هل لديك شعار ومحتوى، هل لديك دومين واستضافة؟",
    },
    "systems": {
        "title": "🖥️ تطوير الأنظمة الإلكترونية",
        "short": "أنظمة إدارية مخصصة لتنظيم البيانات والعمليات والتقارير.",
        "details": [
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
        "title": "📱 تطبيقات الجوال",
        "short": "تطبيقات Android و iOS حسب احتياج المشروع.",
        "details": [
            "واجهات تطبيق حديثة وسهلة.",
            "تسجيل دخول وحسابات مستخدمين.",
            "طلبات أو حجوزات أو عرض خدمات.",
            "ربط بلوحة تحكم وقاعدة بيانات.",
            "إشعارات وتنبيهات حسب الحاجة.",
        ],
        "ask_hint": "Android أم iOS، هل يوجد تسجيل دخول، طلبات، إشعارات، لوحة تحكم؟",
    },
    "database": {
        "title": "🗄️ قواعد البيانات وإدارة البيانات",
        "short": "تنظيم البيانات وتحويل الجداول إلى نظام واضح وتقارير.",
        "details": [
            "تحليل ملفات Excel والبيانات الحالية.",
            "تصميم جداول وعلاقات.",
            "استيراد وتصدير البيانات.",
            "تقارير ولوحات متابعة.",
            "تنظيم وحماية ونسخ احتياطي.",
        ],
        "ask_hint": "نوع البيانات، عدد الجداول، التقارير المطلوبة، هل البيانات موجودة في Excel؟",
    },
    "automation": {
        "title": "⚙️ الأتمتة والتحول الرقمي",
        "short": "تحويل الإجراءات اليدوية إلى عمليات رقمية توفر الوقت وتقلل الأخطاء.",
        "details": [
            "أتمتة النماذج والتقارير.",
            "تنظيم إجراءات العمل.",
            "إشعارات ومتابعة مهام.",
            "ربط العمليات والخدمات.",
            "تقليل الأخطاء اليدوية.",
        ],
        "ask_hint": "ما الإجراء المتكرر، من ينفذه، ما المدخلات والمخرجات؟",
    },
    "branding": {
        "title": "🎨 الهوية الرقمية والتصميم",
        "short": "شعارات، هويات بصرية، بروفايلات، واجهات، وقوالب سوشيال ميديا.",
        "details": [
            "تصميم شعار وهوية بصرية.",
            "اختيار ألوان وخطوط.",
            "بروفايل شركة وسيرة ذاتية.",
            "واجهات UI/UX.",
            "قوالب منشورات وستوري.",
        ],
        "ask_hint": "اسم النشاط، الألوان المفضلة، نوع الهوية، الملفات المطلوبة.",
    },
    "greetings": {
        "title": "🎁 تصميم التهاني والمناسبات",
        "short": "تهاني تخرج وزواج وعقد قران وأعياد وافتتاحات.",
        "details": [
            "تصميم تهاني بأسماء وعبارات خاصة.",
            "تصاميم فاخرة أو بسيطة حسب المناسبة.",
            "مقاسات واتساب وسوشيال ميديا.",
            "إضافة صور أو شعارات عند الحاجة.",
            "تعديلات بسيطة حسب الاتفاق.",
        ],
        "ask_hint": "نوع المناسبة، الاسم، العبارة، المقاس، الألوان، الصور.",
    },
    "ads": {
        "title": "📣 تصميم الإعلانات والسوشيال ميديا",
        "short": "منشورات، ستوريات، بنرات، حملات، وكلمات تسويقية.",
        "details": [
            "منشورات إعلانية احترافية.",
            "ستوريات وعروض خدمات.",
            "نصوص تسويقية جذابة.",
            "تصاميم منتجات وخدمات وعقارات.",
            "حملات متناسقة بصريًا.",
        ],
        "ask_hint": "نوع الإعلان، المنتج أو الخدمة، الجمهور، العرض، المقاس.",
    },
    "seo": {
        "title": "🔍 SEO وتحسين الظهور في Google",
        "short": "تهيئة المواقع لمحركات البحث وتحسين فرص الظهور.",
        "details": [
            "تحسين العناوين والوصف.",
            "Sitemap و Robots و Schema.",
            "تنظيم الصفحات والروابط الداخلية.",
            "اقتراح كلمات مفتاحية ومقالات.",
            "تحسين تجربة المستخدم والسرعة قدر الإمكان.",
        ],
        "ask_hint": "رابط الموقع، الكلمات المستهدفة، المدينة، المنافسون، هل توجد مقالات؟",
    },
    "support": {
        "title": "🎧 الدعم الفني والاستشارات",
        "short": "تحليل أفكار ومشاكل تقنية وتقديم حلول عملية.",
        "details": [
            "مراجعة فكرة المشروع.",
            "اقتراح الحل المناسب.",
            "تحسين موقع أو نظام موجود.",
            "حل مشاكل تقنية.",
            "متابعة وصيانة حسب الاتفاق.",
        ],
        "ask_hint": "ما المشكلة أو القرار المطلوب، ما النظام الحالي، ما النتيجة المطلوبة؟",
    },
}

PACKAGES = {
    "basic": {
        "title": "📦 الباقة الأساسية",
        "desc": "مناسبة للأفراد والمشاريع الصغيرة.",
        "features": ["موقع تعريفي من 4 صفحات.", "تصميم متجاوب.", "ربط واتساب.", "نموذج تواصل.", "SEO أساسي."],
    },
    "pro": {
        "title": "🚀 الباقة الاحترافية",
        "desc": "مناسبة للشركات والمؤسسات.",
        "features": ["موقع من 6 إلى 8 صفحات.", "تصميم خاص.", "محتوى تسويقي.", "معرض أعمال.", "SEO أفضل.", "دعم فني."],
    },
    "advanced": {
        "title": "🏢 الباقة المتقدمة",
        "desc": "مناسبة للأنظمة والمنصات الكبيرة.",
        "features": ["تحليل متطلبات.", "لوحة تحكم.", "قاعدة بيانات.", "صلاحيات.", "تقارير.", "تطوير مستمر."],
    },
    "design": {
        "title": "🎨 باقة التصميم والإعلانات",
        "desc": "مناسبة للمناسبات والسوشيال ميديا.",
        "features": ["تصميم تهاني.", "منشورات إعلانية.", "نص تسويقي.", "مقاسات مختلفة.", "هوية بصرية متناسقة."],
    },
}

FAQ_CATEGORIES = {
    "general": {
        "title": "أسئلة عامة عن المؤسسة",
        "icon": "ℹ️",
        "items": [
            ("ما هي مؤسسة الجحفلي للحلول الرقمية؟", "مؤسسة تقدم حلولًا رقمية تشمل المواقع، الأنظمة، التطبيقات، قواعد البيانات، الأتمتة، التصميم، الإعلانات، والـ SEO."),
            ("ما الذي يميز الجحفلي؟", "نركز على الحل العملي، التصميم الجذاب، وضوح المحتوى، سهولة الاستخدام، والتواصل السريع مع العميل."),
            ("هل تقدمون خدمات للأفراد والشركات؟", "نعم، نخدم الأفراد والشركات والمؤسسات والمدارس والمتاجر والعيادات والمشاريع الناشئة."),
            ("هل يمكن تنفيذ مشروع مخصص؟", "نعم، ندرس الفكرة والمتطلبات ثم نقترح الحل المناسب."),
            ("هل يمكن تنفيذ أكثر من خدمة معًا؟", "نعم، مثل موقع + بوت تليجرام + SEO + تصاميم إعلانية."),
            ("هل تقدمون دعمًا بعد التسليم؟", "نعم، يمكن الاتفاق على دعم وصيانة حسب نوع المشروع."),
        ],
    },
    "web": {
        "title": "أسئلة تصميم المواقع",
        "icon": "🌐",
        "items": [
            ("هل يمكن عمل موقع بدون قاعدة بيانات؟", "نعم، يمكن عمل موقع HTML/CSS/JS ثابت وسريع ومناسب للتعريف بالخدمات."),
            ("هل الموقع يعمل على الجوال؟", "نعم، يتم تصميم الموقع ليعمل على الجوال والتابلت والكمبيوتر."),
            ("ما الصفحات الأساسية للموقع؟", "الرئيسية، من نحن، الخدمات، الأعمال، الباقات، الأسئلة الشائعة، تواصل معنا."),
            ("هل يمكن ربط الموقع بواتساب؟", "نعم، يمكن إضافة زر واتساب ونموذج يجهز رسالة تلقائية."),
            ("هل يمكن إضافة دومين واستضافة؟", "نعم، بعد تجهيز الموقع يمكن رفعه على استضافة وربطه بالدومين."),
            ("هل يمكن تطوير الموقع لاحقًا؟", "نعم، يمكن تحويله إلى موقع بلوحة تحكم وقاعدة بيانات."),
        ],
    },
    "systems": {
        "title": "أسئلة الأنظمة وقواعد البيانات",
        "icon": "🖥️",
        "items": [
            ("ما الفرق بين الموقع والنظام؟", "الموقع يعرض معلومات، أما النظام فيدير بيانات وعمليات وتقارير وصلاحيات."),
            ("هل يمكن تحويل ملفات Excel إلى نظام؟", "نعم، يمكن تحليل ملفات Excel وبناء قاعدة بيانات ولوحة تحكم."),
            ("هل يمكن إضافة صلاحيات؟", "نعم، يمكن إنشاء مدير وموظفين ومستخدمين بصلاحيات مختلفة."),
            ("هل يمكن تصدير التقارير؟", "نعم، يمكن إضافة تصدير Excel أو PDF حسب الحاجة."),
            ("هل النظام محمي؟", "يمكن إضافة تسجيل دخول وصلاحيات ونسخ احتياطي وحماية مبدئية."),
        ],
    },
    "design": {
        "title": "أسئلة التصميم والتهاني والإعلانات",
        "icon": "🎨",
        "items": [
            ("هل تصممون تهاني تخرج وزواج؟", "نعم، نصمم تهاني تخرج وزواج وعقد قران وأعياد وافتتاحات."),
            ("هل يمكن إضافة اسم وصورة؟", "نعم، يمكن إضافة الاسم والصورة والشعار والعبارة المطلوبة."),
            ("هل تصممون إعلانات تجارية؟", "نعم، نصمم إعلانات خدمات ومنتجات وعروض وسوشيال ميديا."),
            ("هل تكتبون النص التسويقي؟", "نعم، يمكن صياغة نص تسويقي مناسب للتصميم."),
            ("هل يمكن اختيار الألوان؟", "نعم، يمكن للعميل تحديد الألوان أو نختار ألوانًا مناسبة للنشاط."),
        ],
    },
    "seo": {
        "title": "أسئلة SEO والظهور في Google",
        "icon": "🔍",
        "items": [
            ("هل تضمنون المركز الأول في Google؟", "لا يمكن ضمان المركز الأول مباشرة، لكن يمكن تهيئة الموقع بشكل صحيح وتحسين فرص الظهور."),
            ("ما أهم عناصر SEO؟", "العنوان، الوصف، المحتوى، السرعة، الروابط الداخلية، Sitemap، Schema، وتجربة المستخدم."),
            ("هل الموقع الثابت يظهر في Google؟", "نعم، إذا كان مرفوعًا على دومين ومفهرسًا ومهيأ جيدًا."),
            ("هل أحتاج مقالات؟", "المقالات تساعد في استهداف كلمات بحث أكثر وزيادة فرص الظهور."),
            ("ما هي Google Search Console؟", "أداة من Google لمتابعة الفهرسة والزيارات والمشاكل وإرسال خريطة الموقع."),
        ],
    },
    "pricing": {
        "title": "أسئلة الأسعار والتنفيذ",
        "icon": "💰",
        "items": [
            ("كم سعر الموقع؟", "يعتمد على عدد الصفحات ومستوى التصميم والخصائص والمحتوى والمدة."),
            ("هل يمكن البدء بنسخة بسيطة؟", "نعم، يمكن البدء بنسخة بسيطة ثم تطويرها لاحقًا."),
            ("ما المطلوب قبل بدء التنفيذ؟", "الشعار، النصوص، الصور، الأقسام المطلوبة، بيانات التواصل، وأمثلة إن وجدت."),
            ("كم مدة التنفيذ؟", "تعتمد على حجم المشروع؛ المواقع البسيطة أسرع من الأنظمة والتطبيقات."),
            ("هل يمكن الدفع على دفعات؟", "يمكن الاتفاق على طريقة دفع مناسبة حسب حجم المشروع."),
        ],
    },
}

PORTFOLIO = [
    ("🏢 موقع شركة خدمات", "موقع يعرض الخدمات والباقات والتواصل المباشر."),
    ("🧾 نظام مبيعات وفواتير", "إدارة العملاء والمنتجات والفواتير والتقارير."),
    ("🏫 نظام إدارة مدرسة", "طلاب ومعلمون وحضور وتقارير وصلاحيات."),
    ("📱 تطبيق حجز وطلبات", "تطبيق لاستقبال الطلبات والحجوزات."),
    ("🎁 تصاميم تهاني", "تخرج، زواج، عقد قران، أعياد، افتتاحات."),
    ("📣 حملات إعلانية", "منشورات وسلاسل إعلانية لجذب العملاء."),
]

# ==========================
# أدوات مساعدة
# ==========================
def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_db(path: pathlib.Path = DB_PATH) -> Connection:
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            service TEXT,
            project_name TEXT,
            activity TEXT,
            target TEXT,
            goal TEXT,
            status TEXT,
            features TEXT,
            pages TEXT,
            style TEXT,
            content TEXT,
            references_text TEXT,
            budget TEXT,
            deadline TEXT,
            contact_method TEXT,
            notes TEXT,
            attachments TEXT,
            created_at TEXT,
            telegram_user_id TEXT,
            telegram_username TEXT
        )
        """
    )
    conn.commit()
    return conn


DB_CONN: Connection = init_db()

def wa_link(text: str = "") -> str:
    if text:
        return f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(text)}"
    return f"https://wa.me/{WHATSAPP_NUMBER}"

def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🌐 الخدمات"), KeyboardButton("📦 الباقات")],
            [KeyboardButton("📩 طلب خدمة متقدم"), KeyboardButton("❓ الأسئلة الشائعة")],
            [KeyboardButton("ℹ️ عن الجحفلي"), KeyboardButton("🧾 أعمالنا")],
            [KeyboardButton("🔍 ترشيح الخدمة"), KeyboardButton("☎️ تواصل معنا")],
            [KeyboardButton("🏠 الرئيسية")],
        ],
        resize_keyboard=True,
    )

def welcome_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 الخدمات", callback_data="show_services"), InlineKeyboardButton("📦 الباقات", callback_data="show_packages")],
        [InlineKeyboardButton("📩 طلب خدمة", callback_data="start_request"), InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="show_faq")],
        [InlineKeyboardButton("☎️ تواصل معنا", callback_data="contact"), InlineKeyboardButton("ℹ️ عن الجحفلي", callback_data="about:details")],
    ])

def services_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(v["title"], callback_data=f"service:{k}")] for k, v in SERVICES.items()]
    rows.append([InlineKeyboardButton("📩 طلب خدمة متقدم", callback_data="start_request")])
    return InlineKeyboardMarkup(rows)

def packages_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(v["title"], callback_data=f"package:{k}")] for k, v in PACKAGES.items()]
    rows.append([InlineKeyboardButton("📩 طلب باقة", callback_data="start_request")])
    return InlineKeyboardMarkup(rows)

def about_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 نبذة تفصيلية", callback_data="about:details")],
        [InlineKeyboardButton("👁️ الرؤية والرسالة", callback_data="about:vision")],
        [InlineKeyboardButton("💎 القيم", callback_data="about:values")],
        [InlineKeyboardButton("⚙️ آلية العمل", callback_data="about:steps")],
        [InlineKeyboardButton("✨ لماذا الجحفلي؟", callback_data="about:why")],
        [InlineKeyboardButton("📩 اطلب خدمة", callback_data="start_request")],
    ])

def faq_categories_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{cat['icon']} {cat['title']}", callback_data=f"faqcat:{key}")]
        for key, cat in FAQ_CATEGORIES.items()
    ])

def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 الخدمات", callback_data="show_services"), InlineKeyboardButton("📦 الباقات", callback_data="show_packages")],
        [InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="show_faq"), InlineKeyboardButton("☎️ تواصل", callback_data="contact")],
        [InlineKeyboardButton("📩 طلب خدمة", callback_data="start_request")],
    ])

def save_request(data: Dict[str, Any]) -> None:
    # Persist request into SQLite database
    try:
        cur = DB_CONN.cursor()
        attachments = _json.dumps(data.get("attachments", []), ensure_ascii=False)
        cur.execute(
            """
            INSERT INTO service_requests (
                name, phone, service, project_name, activity, target, goal, status,
                features, pages, style, content, references_text, budget, deadline,
                contact_method, notes, attachments, created_at, telegram_user_id, telegram_username
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                data.get("name"),
                data.get("phone"),
                data.get("service"),
                data.get("project_name"),
                data.get("activity"),
                data.get("target"),
                data.get("goal"),
                data.get("status"),
                data.get("features"),
                data.get("pages"),
                data.get("style"),
                data.get("content"),
                data.get("references"),
                data.get("budget"),
                data.get("deadline"),
                data.get("contact_method"),
                data.get("notes"),
                attachments,
                data.get("created_at"),
                data.get("telegram_user_id"),
                data.get("telegram_username"),
            ),
        )
        DB_CONN.commit()
    except Exception:
        logger.exception("Failed saving request to DB")

def format_request(data: Dict[str, Any], user=None) -> str:
    username = f"@{user.username}" if user and user.username else "غير متوفر"
    user_id = user.id if user else "غير متوفر"
    return (
        "📩 <b>طلب خدمة متقدم جديد</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"👤 <b>الاسم:</b> {data.get('name','-')}\n"
        f"📞 <b>الهاتف:</b> {data.get('phone','-')}\n"
        f"🌐 <b>الخدمة:</b> {data.get('service','-')}\n"
        f"🏷️ <b>اسم المشروع:</b> {data.get('project_name','-')}\n"
        f"🏢 <b>النشاط:</b> {data.get('activity','-')}\n"
        f"🎯 <b>الجمهور المستهدف:</b> {data.get('target','-')}\n"
        f"🚀 <b>الهدف:</b> {data.get('goal','-')}\n"
        f"📌 <b>الوضع الحالي:</b> {data.get('status','-')}\n"
        f"🧩 <b>المميزات المطلوبة:</b> {data.get('features','-')}\n"
        f"📄 <b>الصفحات/العناصر:</b> {data.get('pages','-')}\n"
        f"🎨 <b>أسلوب التصميم:</b> {data.get('style','-')}\n"
        f"🗂️ <b>جاهزية المحتوى:</b> {data.get('content','-')}\n"
        f"🔗 <b>أمثلة/مراجع:</b> {data.get('references','-')}\n"
        f"💰 <b>الميزانية:</b> {data.get('budget','-')}\n"
        f"⏱️ <b>موعد التسليم:</b> {data.get('deadline','-')}\n"
        f"💬 <b>طريقة التواصل:</b> {data.get('contact_method','-')}\n"
        f"📝 <b>ملاحظات:</b> {data.get('notes','-')}\n"
        f"🕒 <b>وقت الطلب:</b> {data.get('created_at','-')}\n"
        f"📎 <b>مرفقات:</b> {', '.join(data.get('attachments', [])) if data.get('attachments') else '-'}\n"
        "━━━━━━━━━━━━━━━\n"
        f"🆔 <b>User ID:</b> {user_id}\n"
        f"🔗 <b>Username:</b> {username}"
    )

async def send_admin(context: ContextTypes.DEFAULT_TYPE, text: str):
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=text, parse_mode=ParseMode.HTML)
            # if there are attachments in the current conversation data, send them as documents
            req = context.user_data.get("request_data") if hasattr(context, 'user_data') else None
            if req:
                for fname in req.get("attachments", []):
                    path = ATTACHMENTS_DIR / fname
                    if path.exists():
                        try:
                            await context.bot.send_document(chat_id=int(ADMIN_CHAT_ID), document=path.open("rb"))
                        except Exception:
                            logger.exception("Failed to send attachment to admin: %s", fname)
        except Exception as exc:
            logger.exception("Admin send failed: %s", exc)

# ==========================
# أوامر البوت
# ==========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "✨ <b>أهلًا وسهلًا بك في البوت الرسمي لمؤسسة الجحفلي للحلول الرقمية</b>\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"<b>{COMPANY['tagline']}</b>\n\n"
        "نحن نقدم حلولًا رقمية متكاملة لتطوير موقعك، نظامك، تطبيقك، وهوية نشاطك.\n"
        "سواء كنت تريد مشروعًا سريعًا أو خدمة متكاملة، فنحن معك خطوة بخطوة.\n\n"
        "📌 عبر هذا البوت يمكنك:\n"
        "• استعراض الخدمات والباقات بسهولة.\n"
        "• تقديم طلب خدمة متقدم واحترافي.\n"
        "• الاطلاع على الأسئلة الشائعة والتواصل المباشر.\n"
        "• التعرف على تاريخنا وأعمالنا ومزايانا.\n\n"
        "📌 <b>أوامر البوت</b>:\n"
        "/start  /services  /packages\n"
        "/request  /about  /portfolio\n"
        "/faq  /contact  /recommend\n"
        "/admin_requests\n\n"
        "استخدم الأزرار السريعة أدناه للبدء فورًا.")
    if LOGO_PATH.exists():
        await update.message.reply_photo(
            photo=LOGO_PATH.open("rb"),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_inline_keyboard(),
        )
    else:
        await update.message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=welcome_inline_keyboard())

async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 <b>خدماتنا الرقمية</b>\n\nاختر الخدمة لمعرفة التفاصيل:", parse_mode=ParseMode.HTML, reply_markup=services_keyboard())

async def packages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📦 <b>الباقات</b>\n\nاختر باقة لمعرفة التفاصيل:", parse_mode=ParseMode.HTML, reply_markup=packages_keyboard())

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"ℹ️ <b>{COMPANY['name']}</b>\n"
        f"<b>{COMPANY['en']}</b>\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"{COMPANY['intro']}\n\n"
        "اختر القسم الذي تريد معرفته:"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=about_keyboard())

async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["🧾 <b>نماذج من الأعمال والخدمات التي ننفذها</b>\n"]
    for title, desc in PORTFOLIO:
        lines.append(f"{title}\n{desc}\n")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=back_keyboard())

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ <b>مركز الأسئلة الشائعة</b>\n\nاختر التصنيف:", parse_mode=ParseMode.HTML, reply_markup=faq_categories_keyboard())

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = wa_link("أهلًا مؤسسة الجحفلي للحلول الرقمية، أريد الاستفسار عن خدمة.")
    text = (
        "☎️ <b>تواصل معنا</b>\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"📞 الهاتف: <b>{COMPANY_PHONE}</b>\n"
        f"💬 واتساب: {link}\n"
        f"📧 البريد: {COMPANY_EMAIL}\n"
        f"🌍 الموقع: {COMPANY_WEBSITE}\n"
        f"📍 العنوان: {COMPANY_LOCATION}"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 واتساب مباشر", url=link)],
            [InlineKeyboardButton("📩 طلب خدمة متقدم", callback_data="start_request")],
        ])
    )

async def recommend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("أريد موقع يعرض خدماتي", callback_data="service:web")],
        [InlineKeyboardButton("أريد نظام ينظم عملي", callback_data="service:systems")],
        [InlineKeyboardButton("أريد تطبيق جوال", callback_data="service:apps")],
        [InlineKeyboardButton("أريد تنظيم بيانات Excel", callback_data="service:database")],
        [InlineKeyboardButton("أريد أتمتة إجراءات", callback_data="service:automation")],
        [InlineKeyboardButton("أريد شعار أو هوية", callback_data="service:branding")],
        [InlineKeyboardButton("أريد تهنئة أو مناسبة", callback_data="service:greetings")],
        [InlineKeyboardButton("أريد إعلانات وتصاميم", callback_data="service:ads")],
        [InlineKeyboardButton("أريد الظهور في Google", callback_data="service:seo")],
        [InlineKeyboardButton("لا أعرف، أريد استشارة", callback_data="service:support")],
    ])
    await update.message.reply_text("🔍 <b>ترشيح الخدمة المناسبة</b>\n\nاختر أقرب وصف لاحتياجك:", parse_mode=ParseMode.HTML, reply_markup=keyboard)

# ==========================
# نموذج طلب الخدمة المتقدم
# ==========================
async def request_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"] = {}
    await update.message.reply_text(
        "📩 <b>طلب خدمة متقدم</b>\n"
        "━━━━━━━━━━━━━━━\n\n"
        "سأجمع تفاصيل مشروعك خطوة بخطوة حتى يتم فهم احتياجك بدقة.\n\n"
        "👤 اكتب اسمك الكامل:",
        parse_mode=ParseMode.HTML,
    )
    return REQ_NAME

async def request_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["request_data"] = {}
    await query.message.reply_text(
        "📩 <b>طلب خدمة متقدم</b>\n\n👤 اكتب اسمك الكامل:",
        parse_mode=ParseMode.HTML,
    )
    return REQ_NAME

async def req_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if len(val) < 2:
        await update.message.reply_text("الاسم غير واضح. اكتب اسمك الكامل:")
        return REQ_NAME
    context.user_data["request_data"]["name"] = val
    await update.message.reply_text("📞 اكتب رقم هاتفك أو واتسابك:")
    return REQ_PHONE

async def req_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if len(val) < 7:
        await update.message.reply_text("رقم الهاتف غير واضح. اكتب رقمًا صحيحًا:")
        return REQ_PHONE
    context.user_data["request_data"]["phone"] = val
    buttons = [[InlineKeyboardButton(v["title"], callback_data=f"choose_service:{k}")] for k, v in SERVICES.items()]
    await update.message.reply_text("🌐 اختر نوع الخدمة المطلوبة:", reply_markup=InlineKeyboardMarkup(buttons))
    return REQ_SERVICE

async def req_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data.split(":", 1)[1]
    service = SERVICES[key]
    context.user_data["request_data"]["service"] = service["title"]
    await q.message.reply_text(
        f"✅ اخترت: <b>{service['title']}</b>\n\n"
        f"💡 ركز في وصفك على: {service['ask_hint']}\n\n"
        "🏷️ اكتب اسم المشروع أو النشاط:",
        parse_mode=ParseMode.HTML,
    )
    return REQ_PROJECT_NAME

async def req_project_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["project_name"] = update.message.text.strip()
    await update.message.reply_text("🏢 ما نوع النشاط؟ مثال: شركة، عيادة، مدرسة، متجر، عقارات، خدمات تقنية...")
    return REQ_ACTIVITY

async def req_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["activity"] = update.message.text.strip()
    await update.message.reply_text("🎯 من الجمهور المستهدف؟ مثال: عملاء محليون، شركات، طلاب، مرضى، زوار Google...")
    return REQ_TARGET

async def req_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["target"] = update.message.text.strip()
    await update.message.reply_text("🚀 ما الهدف الأساسي من المشروع؟ مثال: جذب عملاء، استقبال طلبات، تنظيم بيانات، تحسين الظهور...")
    return REQ_GOAL

async def req_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["goal"] = update.message.text.strip()
    await update.message.reply_text("📌 ما الوضع الحالي؟ مثال: لدي شعار، موقع قديم، ملفات Excel، فكرة فقط، صفحات تواصل...")
    return REQ_STATUS

async def req_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["status"] = update.message.text.strip()
    await update.message.reply_text("🧩 ما المميزات المطلوبة؟ مثال: واتساب، نموذج طلب، لوحة تحكم، تقارير، حجز، دفع، إشعارات...")
    return REQ_FEATURES

async def req_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["features"] = update.message.text.strip()
    await update.message.reply_text(
        "📄 اكتب الصفحات أو العناصر المطلوبة.\n"
        "للموقع: الرئيسية، من نحن، خدمات، أعمال، تواصل.\n"
        "للتصميم: المقاس، النصوص، الصور.\n"
        "للنظام: الشاشات، الجداول، التقارير."
    )
    return REQ_PAGES

async def req_pages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["pages"] = update.message.text.strip()
    await update.message.reply_text("🎨 ما أسلوب التصميم المفضل؟ مثال: داكن نيون، رسمي، فاخر، بسيط، تقني، ذهبي، طبي...")
    return REQ_STYLE

async def req_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["style"] = update.message.text.strip()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("لدي الشعار والمحتوى", callback_data="content:ready")],
        [InlineKeyboardButton("لدي الشعار فقط", callback_data="content:logo")],
        [InlineKeyboardButton("لدي المحتوى فقط", callback_data="content:text")],
        [InlineKeyboardButton("لا، أحتاج تجهيز كل شيء", callback_data="content:none")],
    ])
    await update.message.reply_text("🗂️ هل المحتوى والشعار جاهزان؟", reply_markup=keyboard)
    return REQ_CONTENT

async def req_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mapping = {
        "ready": "لدي الشعار والمحتوى.",
        "logo": "لدي الشعار فقط.",
        "text": "لدي المحتوى فقط.",
        "none": "لا، أحتاج تجهيز كل شيء.",
    }
    key = q.data.split(":", 1)[1]
    context.user_data["request_data"]["content"] = mapping.get(key, "-")
    await q.message.reply_text("🔗 هل لديك أمثلة أو روابط أو تصاميم تعجبك؟ اكتبها أو اكتب: لا يوجد.")
    return REQ_REFERENCES

async def req_references(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Support text references or attachments (photo/document)
    msg = update.message
    # initialize attachments list
    context.user_data["request_data"].setdefault("attachments", [])
    if msg.photo or msg.document:
        try:
            if msg.photo:
                f = await msg.photo[-1].get_file()
                name = f"{now_text().replace(' ', '_').replace(':','-')}_{f.file_id}.jpg"
                path = ATTACHMENTS_DIR / name
                await f.download_to_drive(str(path))
                context.user_data["request_data"]["attachments"].append(str(path.name))
            if msg.document:
                f = await msg.document.get_file()
                orig = msg.document.file_name or f.file_id
                name = f"{now_text().replace(' ', '_').replace(':','-')}_{orig}"
                path = ATTACHMENTS_DIR / name
                await f.download_to_drive(str(path))
                context.user_data["request_data"]["attachments"].append(str(path.name))
            await update.message.reply_text("✅ تم حفظ المرفق. اكتب أي مراجع إضافية أو اكتب: لا يوجد.")
            return REQ_REFERENCES
        except Exception:
            logger.exception("Failed to download attachment")
            await update.message.reply_text("حدث خطأ أثناء حفظ المرفق. أعد إرسال المرفق أو اكتب: لا يوجد.")
            return REQ_REFERENCES

    # fallback: text references
    context.user_data["request_data"]["references"] = update.message.text.strip()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ميزانية محدودة", callback_data="budget:low")],
        [InlineKeyboardButton("ميزانية متوسطة", callback_data="budget:mid")],
        [InlineKeyboardButton("مشروع متقدم", callback_data="budget:high")],
        [InlineKeyboardButton("أريد عرض سعر بعد الدراسة", callback_data="budget:quote")],
    ])
    await update.message.reply_text("💰 اختر الميزانية التقريبية:", reply_markup=keyboard)
    return REQ_BUDGET

async def req_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mapping = {
        "low": "ميزانية محدودة",
        "mid": "ميزانية متوسطة",
        "high": "مشروع متقدم",
        "quote": "أريد عرض سعر بعد دراسة الطلب",
    }
    key = q.data.split(":", 1)[1]
    context.user_data["request_data"]["budget"] = mapping.get(key, "-")
    await q.message.reply_text("⏱️ متى تريد التسليم؟ مثال: خلال أسبوع، شهر، غير مستعجل، حسب الاتفاق.")
    return REQ_DEADLINE

async def req_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["request_data"]["deadline"] = update.message.text.strip()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("واتساب", callback_data="contact:whatsapp")],
        [InlineKeyboardButton("تليجرام", callback_data="contact:telegram")],
        [InlineKeyboardButton("اتصال هاتفي", callback_data="contact:call")],
    ])
    await update.message.reply_text("💬 ما طريقة التواصل المفضلة؟", reply_markup=keyboard)
    return REQ_CONTACT

async def req_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    mapping = {"whatsapp": "واتساب", "telegram": "تليجرام", "call": "اتصال هاتفي"}
    key = q.data.split(":", 1)[1]
    context.user_data["request_data"]["contact_method"] = mapping.get(key, "-")
    await q.message.reply_text("📝 هل لديك ملاحظات إضافية؟ إذا لا توجد اكتب: لا يوجد.")
    return REQ_NOTES

async def req_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data["request_data"]
    data["notes"] = update.message.text.strip()
    data["created_at"] = now_text()
    summary = format_request(data, update.effective_user)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تأكيد وإرسال الطلب", callback_data="confirm_request")],
        [InlineKeyboardButton("❌ إلغاء الطلب", callback_data="cancel_request")],
    ])
    await update.message.reply_text("📋 <b>راجع الطلب قبل الإرسال:</b>\n\n" + summary, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    return REQ_CONFIRM

async def req_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "cancel_request":
        context.user_data.pop("request_data", None)
        await q.message.reply_text("تم إلغاء الطلب.", reply_markup=main_keyboard())
        return ConversationHandler.END

    data = context.user_data.get("request_data", {})
    data["telegram_user_id"] = update.effective_user.id
    data["telegram_username"] = update.effective_user.username
    save_request(data)

    summary = format_request(data, update.effective_user)
    await send_admin(context, summary)

    w_text = f"أهلًا مؤسسة الجحفلي، أرسلت طلب خدمة من البوت.\nالاسم: {data.get('name')}\nالخدمة: {data.get('service')}"
    await q.message.reply_text(
        "✅ <b>تم استلام طلبك بنجاح.</b>\n\n"
        "سيتم مراجعة التفاصيل والتواصل معك لتقديم العرض المناسب.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 متابعة عبر واتساب", url=wa_link(w_text))]])
    )
    context.user_data.pop("request_data", None)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("request_data", None)
    await update.message.reply_text("تم إلغاء العملية.", reply_markup=main_keyboard())
    return ConversationHandler.END

# ==========================
# Callback عام
# ==========================
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""

    if data == "show_services":
        await q.message.reply_text("🌐 اختر خدمة:", reply_markup=services_keyboard())
        return

    if data == "show_packages":
        await q.message.reply_text("📦 اختر باقة:", reply_markup=packages_keyboard())
        return

    if data == "show_faq":
        await q.message.reply_text("❓ اختر تصنيف الأسئلة:", reply_markup=faq_categories_keyboard())
        return

    if data == "contact":
        link = wa_link("أهلًا مؤسسة الجحفلي، أريد الاستفسار.")
        await q.message.reply_text(
            f"☎️ <b>تواصل معنا</b>\n\n📞 {COMPANY_PHONE}\n💬 {link}\n📧 {COMPANY_EMAIL}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 واتساب", url=link)]])
        )
        return

    if data.startswith("service:"):
        key = data.split(":", 1)[1]
        s = SERVICES.get(key)
        if not s:
            return
        details = "\n".join([f"• {x}" for x in s["details"]])
        text = (
            f"{s['title']}\n\n"
            f"<b>وصف مختصر:</b>\n{s['short']}\n\n"
            f"<b>ماذا تشمل الخدمة؟</b>\n{details}\n\n"
            f"<b>عند الطلب سنسألك عن:</b>\n{s['ask_hint']}"
        )
        await q.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 طلب هذه الخدمة", callback_data="start_request")],
                [InlineKeyboardButton("💬 واتساب", url=wa_link(f"أريد طلب خدمة: {s['title']}"))],
                [InlineKeyboardButton("🔙 رجوع للخدمات", callback_data="show_services")],
            ])
        )
        return

    if data.startswith("package:"):
        key = data.split(":", 1)[1]
        p = PACKAGES.get(key)
        if not p:
            return
        features = "\n".join([f"• {x}" for x in p["features"]])
        await q.message.reply_text(
            f"{p['title']}\n\n{p['desc']}\n\n<b>المميزات:</b>\n{features}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 طلب هذه الباقة", callback_data="start_request")],
                [InlineKeyboardButton("🔙 الباقات", callback_data="show_packages")],
            ])
        )
        return

    if data.startswith("about:"):
        part = data.split(":", 1)[1]
        if part == "details":
            text = f"📌 <b>نبذة تفصيلية</b>\n\n{COMPANY['about']}"
        elif part == "vision":
            text = f"👁️ <b>الرؤية</b>\n{COMPANY['vision']}\n\n🎯 <b>الرسالة</b>\n{COMPANY['mission']}"
        elif part == "values":
            text = (
                "💎 <b>قيمنا</b>\n\n"
                "• الجودة: إخراج عمل مرتب وواضح.\n"
                "• الوضوح: شرح المطلوب دون تعقيد.\n"
                "• الابتكار: أفكار حديثة وجذابة.\n"
                "• الالتزام: احترام الوقت والمتطلبات.\n"
                "• الدعم: متابعة حسب الاتفاق.\n"
                "• الثقة: حفظ بيانات العميل والعمل بشفافية."
            )
        elif part == "steps":
            text = (
                "⚙️ <b>آلية العمل</b>\n\n"
                "1. فهم الفكرة والهدف.\n"
                "2. تحليل المتطلبات.\n"
                "3. إعداد التصور والمحتوى.\n"
                "4. التصميم والتنفيذ.\n"
                "5. المراجعة والتحسين.\n"
                "6. التسليم والمتابعة."
            )
        else:
            text = (
                "✨ <b>لماذا الجحفلي؟</b>\n\n"
                "• لأننا نربط التصميم بهدف المشروع.\n"
                "• لأننا نهتم بالمحتوى وتجربة المستخدم.\n"
                "• لأن خدماتنا متعددة في مكان واحد.\n"
                "• لأن التواصل مع العملاء يصبح أسهل.\n"
                "• لأن الحل قابل للتطوير مستقبلًا."
            )
        await q.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=about_keyboard())
        return

    if data.startswith("faqcat:"):
        key = data.split(":", 1)[1]
        cat = FAQ_CATEGORIES.get(key)
        if not cat:
            return
        buttons = [[InlineKeyboardButton(question, callback_data=f"faq:{key}:{i}")] for i, (question, _) in enumerate(cat["items"])]
        buttons.append([InlineKeyboardButton("🔙 تصنيفات الأسئلة", callback_data="show_faq")])
        await q.message.reply_text(
            f"{cat['icon']} <b>{cat['title']}</b>\n\nاختر السؤال:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if data.startswith("faq:"):
        _, key, i = data.split(":", 2)
        question, answer = FAQ_CATEGORIES[key]["items"][int(i)]
        await q.message.reply_text(
            f"❓ <b>{question}</b>\n\n{answer}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 أسئلة نفس التصنيف", callback_data=f"faqcat:{key}")],
                [InlineKeyboardButton("📩 طلب خدمة", callback_data="start_request")],
            ])
        )
        return

# ==========================
# Router النصوص
# ==========================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.strip()
    if t in ("🏠 الرئيسية", "الرئيسية"):
        await start(update, context)
    elif t == "🌐 الخدمات":
        await services_command(update, context)
    elif t == "📦 الباقات":
        await packages_command(update, context)
    elif t == "📩 طلب خدمة متقدم":
        await request_start(update, context)
    elif t == "❓ الأسئلة الشائعة":
        await faq_command(update, context)
    elif t == "ℹ️ عن الجحفلي":
        await about_command(update, context)
    elif t == "🧾 أعمالنا":
        await portfolio_command(update, context)
    elif t == "🔍 ترشيح الخدمة":
        await recommend_command(update, context)
    elif t == "☎️ تواصل معنا":
        await contact_command(update, context)
    else:
        await update.message.reply_text("اختر من القائمة أو اكتب /start للعودة للرئيسية.", reply_markup=main_keyboard())

# ==========================
# Admin
# ==========================
async def admin_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ADMIN_CHAT_ID or str(update.effective_chat.id) != str(ADMIN_CHAT_ID):
        await update.message.reply_text("هذا الأمر مخصص للإدارة فقط.")
        return
    if not REQUESTS_FILE.exists():
        await update.message.reply_text("لا توجد طلبات محفوظة.")
        return
    lines = REQUESTS_FILE.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        await update.message.reply_text("لا توجد طلبات محفوظة.")
        return
    out = ["🗂️ <b>آخر 10 طلبات:</b>\n"]
    for raw in lines[-10:]:
        try:
            d = json.loads(raw)
            out.append(f"• {d.get('created_at')} | {d.get('name')} | {d.get('service')} | {d.get('phone')}")
        except Exception:
            pass
    await update.message.reply_text("\n".join(out), parse_mode=ParseMode.HTML)

# ==========================
# تشغيل البوت
# ==========================
def build_app() -> Application:
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        raise RuntimeError("ضع BOT_TOKEN في ملف .env قبل التشغيل.")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_read_timeout(30)
        .build()
    )

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("request", request_start),
            CallbackQueryHandler(request_start_callback, pattern="^start_request$"),
        ],
        states={
            REQ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_name)],
            REQ_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_phone)],
            REQ_SERVICE: [CallbackQueryHandler(req_service, pattern="^choose_service:")],
            REQ_PROJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_project_name)],
            REQ_ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_activity)],
            REQ_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_target)],
            REQ_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_goal)],
            REQ_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_status)],
            REQ_FEATURES: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_features)],
            REQ_PAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_pages)],
            REQ_STYLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_style)],
            REQ_CONTENT: [CallbackQueryHandler(req_content, pattern="^content:")],
            REQ_REFERENCES: [MessageHandler((filters.TEXT | filters.PHOTO | filters.Document.ALL) & ~filters.COMMAND, req_references)],
            REQ_BUDGET: [CallbackQueryHandler(req_budget, pattern="^budget:")],
            REQ_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_deadline)],
            REQ_CONTACT: [CallbackQueryHandler(req_contact, pattern="^contact:")],
            REQ_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_notes)],
            REQ_CONFIRM: [CallbackQueryHandler(req_confirm, pattern="^(confirm_request|cancel_request)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("services", services_command))
    app.add_handler(CommandHandler("packages", packages_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("portfolio", portfolio_command))
    app.add_handler(CommandHandler("faq", faq_command))
    app.add_handler(CommandHandler("contact", contact_command))
    app.add_handler(CommandHandler("recommend", recommend_command))
    app.add_handler(CommandHandler("admin_requests", admin_requests))

    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    return app

if __name__ == "__main__":
    application = build_app()
    print("Al-Jahfali Mega Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
