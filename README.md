# Organizer Chat Bot

> یک ربات تلگرامی که چت‌های انتخابی شما را با یک پرامپت دلخواه بررسی می‌کند و پیام‌های منطبق را به یک چت مقصد فوروارد می‌کند.
>
> A Telegram bot that scans your selected chats with a custom prompt and forwards matching messages to a destination chat.

---

## ✨ قابلیت‌ها / Features

| 🇮🇷 فارسی | 🇬🇧 English |
|---|---|
| ورود با اکانت شخصی شما (Telethon Userbot) | Logs in with **your personal Telegram account** (Telethon userbot) |
| فقط-خواندنی به‌صورت **سخت‌افزاری در سطح کد** | Hard read-only enforced **at code level**, not just by promise |
| رابط کاربری از طریق **BotFather** فقط برای شما | BotFather interface restricted to **your Telegram User ID** |
| پشتیبانی از **OpenRouter** یا **Google AI Studio** (فقط یکی) | Supports **OpenRouter** or **Google AI Studio** (provide exactly one) |
| پنجره زمانی قابل تنظیم در همان جلسه | Per-session adjustable time window |
| ذخیره **۱۰ پرامپت آخر** در Saved Messages | Stores the **last 10 prompts** in Saved Messages (cross-device) |
| رابط **دو زبانه فارسی/انگلیسی** (`/lang fa\|en`) | **Bilingual** UI: Persian / English (`/lang fa\|en`) |
| **حالت امن: ارسال خلاصه با لینک** (پیش‌فرض) | **Safe mode: digest with links** (default) |
| **حالت فوروارد** (اگه خواستید) | **Forward mode** (optional) |
| **خواندن آرام** برای جلوگیری از FloodWait | **Slow read** to avoid FloodWait |
| اجرا روی PC شخصی (بدون Docker) یا Docker | Runs on your PC (no Docker needed) or on Docker |

---

## ⚠️ نکات مهم قبل از شروع / Important Notes

> ⚠️ **استفاده از Telethon Userbot طبق ToS تلگرام یک gray area است.** اگر اکانتتان ban شود، مسئولیت با خودتان است. پیشنهاد می‌شود از شماره‌ای استفاده کنید که برایتان critical نیست.
>
> ⚠️ **Session file حتماً باید persistent باشد.** اگر session از بین برود، باید دوباره کد تأیید SMS بزنید. اسکریپت‌ها session را در `./data/` ذخیره می‌کنند — آن پوشه را پاک نکنید.
>
> ⚠️ **API ID/Hash از [my.telegram.org](https://my.telegram.org/apps)** گرفته می‌شود (متفاوت از BotFather token).
>
> ⚠️ **هرگز `.env` را commit نکنید** — در `.gitignore` هست اما باز هم دقت کنید.

> Using a Telethon userbot is a Telegram ToS gray area. If your account gets banned, that's on you. Prefer a non-critical phone number. The session file must persist or you'll be re-prompted for SMS codes.

---

## 🚀 راه‌اندازی قدم به قدم / Step-by-Step Setup

دو روش اجرا دارید: **🅰️ بدون Docker (ساده‌تر)** یا **🅱️ با Docker**.

قبل از هر دو، باید **۵ مقدار** زیر را داشته باشید. راهنمای کامل گرفتن هر کدام در بخش [📋 راهنمای دریافت اطلاعات](#-راهنمای-دریافت-اطلاعات--getting-credentials) آمده است.

| مقدار / Value | توضیح کوتاه |
|---|---|
| `TELEGRAM_API_ID` | عددی (مثل `123456`) |
| `TELEGRAM_API_HASH` | یک رشته ۳۲ کاراکتری hex |
| `BOT_TOKEN` | از BotFather: `123456789:AAxxx...` |
| `ALLOWED_USER_ID` | عددی (مثل `111111111`) |
| `OPENROUTER_API_KEY` *یا* `GOOGLE_AI_API_KEY` | یکی از این دو |

---

### 🅰️ روش ۱ — بدون Docker (توصیه‌شده برای PC شخصی)

**پیش‌نیاز:** Python 3.11+ ([دانلود از python.org](https://www.python.org/downloads/))

ساده‌ترین روش: فقط **دو بار کلیک** کافیست.

#### گام ۱ — اجرای اسکریپت

**ویندوز (PowerShell — پیش‌فرض):**

```powershell
cd "e:\programming\New folder\Organizer_chat_bot"
.\run.ps1
```

> اگه خطای `running scripts is disabled` گرفتید، یک‌بار این دستور رو اجرا کنید:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

**ویندوز (CMD):**

```cmd
cd "e:\programming\New folder\Organizer_chat_bot"
run.bat
```

**Linux / macOS:**

```bash
cd Organizer_chat_bot
chmod +x run.sh
./run.sh
```

#### گام ۲ — اسکریپت چه می‌کند؟

اسکریپت به‌صورت خودکار:

1. اگه `.venv` (محیط مجازی) نبود، می‌سازدش
2. `pip install -r requirements.txt` را اجرا می‌کند
3. اگه `.env` نبود، از `.env.example` کپی می‌کند و **متوقف می‌شود** تا پرش کنید
4. ربات را اجرا می‌کند

#### گام ۳ — پر کردن `.env`

وقتی اسکریپت متوقف شد، فایل `.env` ساخته شده است. آن را با notepad باز کنید:

```powershell
notepad .env
```

و **۵ مقدار** را با مقادیر واقعی خودتان پر کنید (راهنمای گرفتن هر کدام در بخش بعدی است):

```ini
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=abc123def456abc123def456abc123de
BOT_TOKEN=123456789:AAH-your-real-token-here
ALLOWED_USER_ID=111111111
FORWARD_DESTINATION=@your_channel_or_chat_id

# فقط یکی از دو خط زیر را پر کنید:
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
# GOOGLE_AI_API_KEY=  ← این را خالی بگذارید
```

> 💡 مقادیر نمونه (123456, your_api_hash_here, etc.) که در `.env` هست، **فیک** هستند — حتماً عوض‌شان کنید.

#### گام ۴ — اجرای واقعی ربات

```powershell
.\run.ps1
```

**اولین اجرا:** Telethon از شما می‌پرسد:

```
Please enter your phone (or bot token): +989123456789
Please enter the code you received: 12345
Please enter your password (if 2FA enabled): ******
```

بعد از لاگین موفق، ربات شروع به کار می‌کند. خروجی شبیه این خواهد بود:

```
2026-09-02 22:57:59 | INFO    | __main__ | Organizer Chat Bot v0.1.0 starting up
2026-09-02 22:57:59 | INFO    | __main__ | Config: ai=openrouter/google/gemini-2.0-flash | allowed_user_id=111111111 | lang_default=fa
2026-09-02 22:57:59 | INFO    | src.ai.analyzer | AI Provider: OpenRouter (model=google/gemini-2.0-flash) — API key present=True
2026-09-02 22:57:59 | INFO    | src.bot.interface | Telegram bot application built
2026-09-02 22:57:59 | INFO    | __main__ | Connecting Telethon userbot...
2026-09-02 22:58:02 | INFO    | __main__ | Userbot logged in as YourName (id=987654321)
2026-09-02 22:58:02 | INFO    | __main__ | Bot is running. Press Ctrl+C to stop.
```

> 📌 **Session فایل** در پوشه `./data/` ساخته شده. دفعه بعد که `.\run.ps1` را اجرا کنید، SMS code نمی‌خواهد.

#### گام ۵ — استفاده در تلگرام

در تلگرام به **ربات BotFather** (که قبلاً ساخته‌اید) پیام `/start` بفرستید:

```
1. منو شیشه‌ای نمایش داده می‌شود
2. روی "💬 انتخاب چت" بزنید → یکی از چت‌هایتان را انتخاب کنید
3. روی "⏱ پنجره زمانی" بزنید → مثلاً "24h" یا دستی "48h" بفرستید
4. روی "📝 پرامپت جدید" بزنید → توضیح دهید دنبال چه نوع پیام‌هایی هستید
   (مثلاً: "پیام‌هایی که شامل آگهی استخدام برنامه‌نویس هستند")
5. (اختیاری) روی "📨 مقصد فوروارد" → یا از پیش‌فرض `.env` استفاده کنید
6. (اختیاری) روی "📤 حالت ارسال" → انتخاب کنید:
   • 📋 ارسال خلاصه با لینک (پیش‌فرض، امن) — یک پیام شامل لینک + متن کوتاه
   • ↪️ فوروارد پیام‌ها — مستقیم فوروارد می‌کنه
7. روی "▶️ اجرا" بزنید
```

> 💡 **حالت پیش‌فرض «خلاصه با لینک» است.** این حالت امن‌تره چون فقط یک پیام (digest) به مقصد می‌فرسته و پیام‌های اصلی را touch نمی‌کنه. در حالت digest، شما لینک مستقیم به پیام اصلی دریافت می‌کنید و خودتان تصمیم می‌گیرید چه کار کنید.

---

### 🅱️ روش ۲ — با Docker (برای سرور یا اجرای ۲۴/۷)

```bash
cd Organizer_chat_bot
cp .env.example .env
# Edit .env (same as method A, step 3 above).

# First run (interactive SMS-code input — DON'T use -d here):
docker compose run --rm organizer-bot

# After successful login (you see "Bot is running"):
# Press Ctrl+C, then:
docker compose up -d      # background mode

# View logs:
docker compose logs -f    # follow

# Stop:
docker compose down
```

**نکته Docker:** volume در `docker-compose.yml` پوشه `./data` را mount می‌کند. **هرگز آن را پاک نکنید** — session اکانت شما در آنجاست.

---

## 📋 راهنمای دریافت اطلاعات / Getting Credentials

### ۱) `TELEGRAM_API_ID` و `TELEGRAM_API_HASH`

این‌ها از تلگرام رسمی گرفته می‌شوند (اکانت خودتان):

1. به <https://my.telegram.org/apps> بروید
2. با شماره تلفن اکانتی که می‌خواهید ربات با آن لاگین شود، وارد شوید
3. روی **"Create new application"** بزنید
4. یک `title` و `shortname` دلخواه بگذارید (مثلاً "OrganizerBot")
5. بعد از submit، `api_id` (عدد) و `api_hash` (رشته ۳۲ کاراکتری) به شما نشان داده می‌شود

> ⚠️ `api_hash` را **به هیچ‌کس** نشان ندهید — دسترسی کامل به اکانتتان می‌دهد.

### ۲) `BOT_TOKEN` (از BotFather)

این یک ربات جداگانه است (BotFather bot) که فقط **رابط کاربری** است:

1. در تلگرام به [@BotFather](https://t.me/BotFather) پیام `/newbot` بفرستید
2. یک `name` بگذارید (مثلاً "My Organizer")
3. یک `username` یکتا بگذارید که به `bot` ختم شود (مثلاً `my_organizer_xyz_bot`)
4. BotFather یک **token** به شما می‌دهد شبیه `123456789:AAH_your-token-here`
5. کل token را در `BOT_TOKEN` بگذارید

### ۳) `ALLOWED_USER_ID` (User ID شما)

این User ID شما (نه username) است که ربات فقط به او پاسخ می‌دهد:

1. در تلگرام به [@userinfobot](https://t.me/userinfobot) یا [@RawDataBot](https://t.me/RawDataBot) پیام `/start` بفرستید
2. ربات یک JSON برمی‌گرداند. عدد `"id":` (مثلاً `111111111`) همان User ID شماست
3. آن را در `ALLOWED_USER_ID` بگذارید

### ۴) `OPENROUTER_API_KEY` (توصیه‌شده)

1. به <https://openrouter.ai/keys> بروید
2. با Google/GitHub sign in کنید
3. روی **"Create Key"** بزنید، یک نام بگذارید
4. Key شبیه `sk-or-v1-xxxxxxxxxxxxxxxxxxxx` را کپی کنید
5. در `OPENROUTER_API_KEY` بگذارید
6. **اختیاری:** در `OPENROUTER_MODEL` می‌توانید مدل را عوض کنید. پیش‌فرض `google/gemini-2.0-flash` ارزان و سریع است.

### ۵) `GOOGLE_AI_API_KEY` (جایگزین OpenRouter)

1. به <https://aistudio.google.com/app/apikey> بروید
2. روی **"Create API key"** بزنید
3. Key را کپی کرده و در `GOOGLE_AI_API_KEY` بگذارید
4. **اختیاری:** `GOOGLE_AI_MODEL` را می‌توانید عوض کنید.

> ⚠️ **فقط یکی** از `OPENROUTER_API_KEY` یا `GOOGLE_AI_API_KEY` را پر کنید. اگه هر دو یا هیچ‌کدام را پر کنید، ربات اجرا نمی‌شود.

### ۶) `FORWARD_DESTINATION` (پیش‌فرض مقصد فوروارد)

یک chat ID یا username:

- برای **کانال/گروه عمومی**: `@channel_username` (مثلاً `@my_channel`)
- برای **کانال/گروه خصوصی**: chat ID عددی (مثلاً `-1001234567890`)
  - برای گرفتن chat ID، ربات [@RawDataBot](https://t.me/RawDataBot) را به آن چت اضافه کنید و `/start` بزنید.

> می‌توانید این مقدار را بعداً در ربات با دکمه «📨 مقصد فوروارد» تغییر دهید.

---

## 🏗️ ساختار پروژه / Project Structure

```
Organizer_chat_bot/
├── src/
│   ├── main.py                    # Entry point
│   ├── config.py                  # pydantic-settings (loads .env, validates)
│   ├── ai/
│   │   ├── analyzer.py            # Auto-detect provider orchestrator
│   │   └── providers/
│   │       ├── base.py            # Abstract Analyzer
│   │       ├── openrouter.py      # OpenRouter (OpenAI-compatible)
│   │       └── google_ai.py       # Google AI Studio (Gemini)
│   ├── bot/
│   │   ├── interface.py           # python-telegram-bot Application
│   │   ├── handlers.py            # /start, /lang, callbacks, text
│   │   ├── auth.py                # ALLOWED_USER_ID decorator
│   │   ├── i18n.py                # MESSAGES_FA + MESSAGES_EN + t()
│   │   ├── state.py               # In-memory per-user state
│   │   └── prompt_history.py      # Saved-Messages persistence
│   ├── userbot/
│   │   ├── client.py              # Telethon factory
│   │   ├── wrapper.py             # ReadOnlyClient (HARD read-only)
│   │   ├── reader.py              # fetch_messages + list_dialogs
│   │   └── forwarder.py           # forward_messages
│   └── utils/logging.py
├── pyproject.toml
├── requirements.txt
├── run.ps1              # Windows PowerShell runner (auto venv + deps)
├── run.bat              # Windows CMD runner (auto venv + deps)
├── run.sh               # Linux/macOS runner (auto venv + deps)
├── tests_smoke.py       # Smoke tests (.venv\Scripts\python.exe tests_smoke.py)
├── Dockerfile
├── docker-compose.yml
├── data/                # Created at runtime — Telethon session files (gitignored)
├── .env.example
├── .gitignore
└── README.md
```

---

## 🔒 امنیت / Security Model

| لاTwo delivery modes** | پیش‌فرض: **digest (امن)** — یک پیام خلاصه با لینک ارسال می‌شود. اختیاری: **forward** — پیام‌های اصلی مستقیماً فوروارد می‌شوند. هیچ‌کدام پیامی به افراد دیگر نمی‌فرستد. |
| **Slow-read pacing** | حالت پیش‌فرض، خواندن پیام‌ها را با ۱.۵ ثانیه مکث بین هر batch انجام می‌دهد تا الگوی رفتاری شبیه کاربر انسانی باشد
|---|---|
| **Hard read-only wrapper** | `ReadOnlyClient` در `src/userbot/wrapper.py` فقط متدهای allowlist‌شده را expose می‌کند. حتی در سطح کد، فراخوانی `client.send_message` به دلیل `__getattr__` غیرفعال‌کننده، **runtime AttributeError** می‌دهد. |
| **Single-user authorization** | تمام handlerها با decorator `authorized` محافظت می‌شوند. هر `Update` از User ID متفرقه silent ignore می‌شود. |
| **AI output validation** | خروجی AI همیشه در برابر مجموعه‌ی id های واقعی fetch‌شده فیلتر می‌شود (`[i for i in ids if i in allowed_ids]`). |
| **Forward-only, never send** | هیچ متنی توسط ربات ارسال نمی‌شود؛ فقط `forward_messages` (با حفظ اطلاعات اصلی). |
| **`.env` + `*.session` در gitignore** | session file ها و کلیدها هرگز commit نمی‌شوند. |

---

## 🛠️ توسعه محلی / Local Development

اگه می‌خواهید ربات رو با IDE اجرا کنید:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
# Copy .env.example to .env and edit.
python -m src.main
```

ولی برای استفاده‌ی عادی، **اسکریپت‌های آماده** (`run.ps1` / `run.bat` / `run.sh`) خودشان venv و deps را هندل می‌کنند.

برای اجرای تست‌های smoke:

```bash
.venv\Scripts\python.exe tests_smoke.py
```

---

## 🧪 عیب‌یابی / Troubleshooting

| مشکل / Issue | راه‌حل / Fix |
|---|---|
| `No AI provider configured` | در `.env` دقیقاً **یکی** از `OPENROUTER_API_KEY` یا `GOOGLE_AI_API_KEY` را پر کنید. |
| `Both providers are set` | هر دو کلید را پاک کنید، فقط یکی نگه دارید. |
| `running scripts is disabled on this system` | PowerShell: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `Rejected update from unauthorized user` | یعنی کاربر دیگری `/start` زده. نگران نباشید — این رفتار صحیح است. |
| Session از بین رفته / Login expired | پوشه `./data` را چک کنید که خالی نباشد. اگه خالی است، باید دوباره SMS code بزنید. |
| `ReadOnlyClient does not expose ...` | یعنی کدی سعی کرده متد write را صدا بزند. این **باگ** است — لطفاً issue باز کنید. |
| Bot stops when PC shuts down | برای اجرای ۲۴/۷، روش Docker (🅱️) یا یک VPS استفاده کنید. |
| `python: command not found` | Python 3.11+ نصب نیست: [python.org/downloads](https://www.python.org/downloads/) |

---

## 📄 مجوز / License

MIT — see [LICENSE](LICENSE).

---

## 🙏 تشکر / Acknowledgements

- [Telethon](https://github.com/LonamiWebs/Telethon) — قدرتمند و قابل‌اعتماد برای Telegram MTProto.
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — بهترین wrapper برای Bot API.
- [OpenRouter](https://openrouter.ai) — یکپارچه‌سازی چندین LLM با یک کلید.
- [Google AI Studio](https://aistudio.google.com) — free tier عالی برای Gemini.