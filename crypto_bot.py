"""
ربات تلگرام مدیریت پرتفوی کریپتو
نوشته شده برای مدیریت آسان دارایی‌های کریپتو
"""

import os
import json
import requests
from datetime import datetime

# ==============================
# تنظیمات اصلی - اینجا رو پر کن
# ==============================
BOT_TOKEN = "8980251065:AAFRHrKDjL0j3KODd1UdnUhAndf_WManluw"  # از BotFather میگیری
CHAT_ID = "781364024"  # از @userinfobot میگیری

# ==============================
# پرتفوی فعلی تو
# ==============================
PORTFOLIO = {
    "BTC":  {"amount": 0.05544353,  "alert_low": 58000,  "alert_high": 90000},
    "ETH":  {"amount": 0.74,        "alert_low": 1700,   "alert_high": 4000},
    "USDT": {"amount": 1445.7,      "alert_low": None,   "alert_high": None},
    "XAUT": {"amount": 0.17447091,  "alert_low": 2800,   "alert_high": 4000},
    "LINK": {"amount": 16.8424,     "alert_low": 8,      "alert_high": 30},
    "ARB":  {"amount": 1001.385778, "alert_low": 0.3,    "alert_high": 2},
    "SOL":  {"amount": 0,           "alert_low": 70,     "alert_high": 200},
    "TAO":  {"amount": 0,           "alert_low": 200,    "alert_high": 800},
}

IRT_AMOUNT = 30_590_523  # تومان نقد


# ==============================
# دریافت قیمت از CoinGecko (رایگان)
# ==============================
COINGECKO_IDS = {
    "BTC":  "bitcoin",
    "ETH":  "ethereum",
    "USDT": "tether",
    "XAUT": "tether-gold",
    "LINK": "chainlink",
    "ARB":  "arbitrum",
    "SOL":  "solana",
    "TAO":  "bittensor",
}

def get_prices():
    """دریافت قیمت‌های لحظه‌ای"""
    ids = ",".join(COINGECKO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        prices = {}
        for symbol, gecko_id in COINGECKO_IDS.items():
            prices[symbol] = data.get(gecko_id, {}).get("usd", 0)
        return prices
    except Exception as e:
        return None

def get_usd_to_irt():
    """دریافت نرخ دلار به تومان"""
    try:
        # از navasan.ir برای نرخ دلار
        r = requests.get("https://api.navasan.tech/latest/?api_key=free&item=usd_sell", timeout=10)
        data = r.json()
        return float(data.get("usd_sell", {}).get("value", 70000))
    except:
        return 70000  # نرخ پیش‌فرض اگه API کار نکرد


# ==============================
# ارسال پیام به تلگرام
# ==============================
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"خطا در ارسال پیام: {e}")


# ==============================
# گزارش روزانه پرتفو
# ==============================
def daily_report():
    prices = get_prices()
    if not prices:
        send_message("⚠️ خطا در دریافت قیمت‌ها. لطفاً بعداً دوباره امتحان کن.")
        return

    usd_to_irt = get_usd_to_irt()
    total_usd = 0
    lines = []

    lines.append(f"📊 <b>گزارش پرتفوی - {datetime.now().strftime('%Y/%m/%d %H:%M')}</b>")
    lines.append(f"💱 نرخ دلار: {usd_to_irt:,.0f} تومان")
    lines.append("─" * 30)

    for symbol, info in PORTFOLIO.items():
        amount = info["amount"]
        if amount == 0:
            continue
        price = prices.get(symbol, 0)
        value_usd = amount * price
        value_irt = value_usd * usd_to_irt
        total_usd += value_usd

        lines.append(
            f"<b>{symbol}</b>: {amount} واحد\n"
            f"   قیمت: ${price:,.2f}\n"
            f"   ارزش: {value_irt:,.0f} تومان"
        )

    # اضافه کردن تومان نقد
    total_irt_cash = IRT_AMOUNT
    total_usd += total_irt_cash / usd_to_irt

    lines.append("─" * 30)
    total_irt = total_usd * usd_to_irt
    lines.append(f"💰 <b>مجموع: {total_irt:,.0f} تومان</b>")
    lines.append(f"   (≈ ${total_usd:,.0f})")

    send_message("\n".join(lines))


# ==============================
# بررسی آلرت‌های قیمتی
# ==============================
def check_alerts():
    prices = get_prices()
    if not prices:
        return

    alerts = []
    for symbol, info in PORTFOLIO.items():
        price = prices.get(symbol, 0)
        if price == 0:
            continue

        low = info.get("alert_low")
        high = info.get("alert_high")

        if low and price <= low:
            alerts.append(f"🔴 <b>{symbol}</b> به کف رسید!\n   قیمت: ${price:,.2f} (کف: ${low:,.2f})\n   ⏰ فرصت خرید!")

        if high and price >= high:
            alerts.append(f"🟢 <b>{symbol}</b> به سقف رسید!\n   قیمت: ${price:,.2f} (سقف: ${high:,.2f})\n   ⚠️ فکر به فروش!")

    if alerts:
        msg = "🚨 <b>آلرت قیمتی!</b>\n\n" + "\n\n".join(alerts)
        send_message(msg)


# ==============================
# هندلر دستورات تلگرام
# ==============================
def handle_updates():
    """دریافت و پردازش پیام‌های کاربر"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    last_update_id = 0

    while True:
        try:
            r = requests.get(url, params={"offset": last_update_id + 1, "timeout": 30}, timeout=35)
            updates = r.json().get("result", [])

            for update in updates:
                last_update_id = update["update_id"]
                message = update.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")

                if str(chat_id) != str(CHAT_ID):
                    continue

                if text == "/start":
                    send_message(
                        "👋 سلام! ربات پرتفوی کریپتوی تو آماده‌ست!\n\n"
                        "دستورات:\n"
                        "/portfolio - مشاهده پرتفو\n"
                        "/alerts - بررسی آلرت‌ها\n"
                        "/prices - قیمت‌های لحظه‌ای\n"
                        "/help - راهنما"
                    )

                elif text == "/portfolio":
                    daily_report()

                elif text == "/alerts":
                    check_alerts()
                    send_message("✅ آلرت‌ها بررسی شدن!")

                elif text == "/prices":
                    prices = get_prices()
                    if prices:
                        lines = ["💹 <b>قیمت‌های لحظه‌ای:</b>\n"]
                        for symbol in PORTFOLIO:
                            if symbol in prices and PORTFOLIO[symbol]["amount"] > 0:
                                lines.append(f"• <b>{symbol}</b>: ${prices[symbol]:,.2f}")
                        send_message("\n".join(lines))

                elif text == "/help":
                    send_message(
                        "📖 <b>راهنما:</b>\n\n"
                        "/portfolio - گزارش کامل پرتفو با ارزش تومانی\n"
                        "/alerts - چک کردن آلرت‌های قیمتی\n"
                        "/prices - قیمت لحظه‌ای ارزها\n\n"
                        "🔔 هر روز ساعت ۹ صبح گزارش خودکار میگیری\n"
                        "⚡ آلرت‌های قیمتی هر ساعت چک میشن"
                    )

        except Exception as e:
            print(f"خطا: {e}")
            import time
            time.sleep(5)


# ==============================
# اجرای اصلی با زمان‌بندی
# ==============================
if __name__ == "__main__":
    import threading
    import time
    import schedule

    print("🤖 ربات شروع به کار کرد...")
    send_message("✅ ربات پرتفوی کریپتو فعال شد!\nبرای شروع /start بزن.")

    # زمان‌بندی گزارش روزانه
    schedule.every().day.at("09:00").do(daily_report)

    # بررسی آلرت‌ها هر ساعت
    schedule.every().hour.do(check_alerts)

    # اجرای زمان‌بند در thread جداگانه
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # شروع دریافت پیام‌ها
    handle_updates()
