# 🤖 JuftPari — Telegram Tanishuv Boti

Telegram orqali tanishuv boti. **aiogram 3**, **PostgreSQL (Supabase)** va modulli arxitektura asosida yozilgan.

## Tez boshlash

### 1. Virtual muhit

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Sozlamalar

`.env.example` ni `.env` ga nusxalang va to'ldiring:

```env
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql://...
PAYMENT_CARD=8600123456789012
PAYMENT_CARD_HOLDER=Ism Familiya
PREMIUM_PRICE_3D=9900
PREMIUM_PRICE_7D=19900
PREMIUM_PRICE_30D=29900
CHAT_REQUIRES_PREMIUM=true
```

### 3. Ishga tushirish

```bash
python main.py
```

### 4. Demo ma'lumotlar (ixtiyoriy)

```bash
set PYTHONPATH=.
python scripts/seed_demo.py
```

## Funksiyalar

- Ro'yxatdan o'tish (FSM): ism, yosh, jins, shahar, rasm, bio
- Anketa qidirish: Like / Dislike / Xabar
- Match: o'zaro like bo'lganda xabar
- Premium: karta + chek orqali to'lov
- Do'kon: stikerlar va animatsiyalar
- Xabarlar: Premium obunachilar uchun chat

## Loyiha tuzilmasi

```
├── bot/handlers/     # start, registration, search, chat, payment, shop
├── bot/keyboards/
├── bot/states/
├── config/           # settings, shop katalogi
├── database/         # SQLite va PostgreSQL
├── scripts/          # seed_demo.py
└── main.py
```

## Texnologiyalar

- Python 3.11+
- [aiogram](https://docs.aiogram.dev/) 3.x
- asyncpg + Supabase PostgreSQL
- python-dotenv

## Repozitoriy

[github.com/Boburjon0723/tanishuvbot](https://github.com/Boburjon0723/tanishuvbot)
