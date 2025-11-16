# telegram_bot_replit.py
# Optimized untuk Replit + UptimeRobot

import os
import time
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration dari environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
APP_URL = os.getenv("APP_URL")
AUTO_SCAN_HOURS = int(os.getenv("AUTO_SCAN_HOURS", "1"))

class ReplitTelegramBot:
    def __init__(self):
        self.app = ApplicationBuilder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_cmd))
        self.app.add_handler(CommandHandler("status", self.status_cmd))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 ProTraderAI Bot is running!\n\n"
            "Commands:\n"
            "/status - Check AI Agent status\n"
            "BTCUSDT 15m - Analyze pair"
        )
    
    async def status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            response = requests.get(f"{APP_URL}/health", timeout=10)
            if response.status_code == 200:
                await update.message.reply_text("✅ AI Agent is online")
            else:
                await update.message.reply_text("❌ AI Agent is offline")
        except:
            await update.message.reply_text("❌ Cannot reach AI Agent")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        if not text:
            return
            
        # Simple pair detection
        pair = text.upper().replace(" ", "").replace("/", "")
        if len(pair) < 6:
            await update.message.reply_text("❌ Invalid pair format")
            return
            
        await update.message.reply_text(f"🔍 Analyzing {pair}...")
        
        try:
            response = requests.get(
                f"{APP_URL}/pro_signal",
                params={"pair": pair, "tf_entry": "15m"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    await update.message.reply_text(f"❌ Error: {data['error']}")
                else:
                    signal_type = data.get("signal_type", "WAIT")
                    confidence = data.get("confidence", 0)
                    await update.message.reply_text(
                        f"📊 {pair}\n"
                        f"💡 Signal: {signal_type}\n"
                        f"🎯 Confidence: {confidence}\n"
                        f"🔗 Entry: {data.get('entry')}\n"
                        f"🛑 SL: {data.get('sl')}"
                    )
            else:
                await update.message.reply_text("❌ Failed to get signal from AI Agent")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Request failed: {str(e)}")
    
    def start(self):
        logger.info("Starting Telegram Bot...")
        self.app.run_polling()

# Keep alive server untuk UptimeRobot
from flask import Flask
import threading

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Telegram Bot is running!"

@web_app.route('/health')
def health():
    return "OK"

def run_web_server():
    web_app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    # Start web server di thread terpisah
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Start bot
    bot = ReplitTelegramBot()
    bot.start()