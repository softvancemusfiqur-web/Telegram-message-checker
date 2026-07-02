import re
import json
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError
from telegram.helpers import escape_markdown
import html 

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import BOT_TOKEN
logging.basicConfig(level=logging.INFO)

# --- CONFIG ---
# Optional: set this to a raw URL returning a JSON array of words,
# e.g. a GitHub Gist raw link: ["call","whatsapp","skype",...]
# Leave as None to always use DEFAULT_RESTRICTED_WORDS.
REMOTE_WORDLIST_URL = None  # e.g. "https://gist.githubusercontent.com/you/xxx/raw/words.json"

# Default Fiverr-restricted words/phrases (user-supplied master list, deduplicated)
DEFAULT_RESTRICTED_WORDS = [
    # --- Communication platforms ---
    "WhatsApp", "Telegram", "Discord", "Skype", "Zoom", "Google Meet",
    "Google Chat", "Microsoft Teams", "Slack", "Signal", "Line", "WeChat",
    "KakaoTalk", "Viber", "Messenger", "Facebook", "Instagram", "Twitter",
    "X", "LinkedIn", "TikTok", "Snapchat", "Reddit", "Quora", "QQ", "Wire",
    "Session", "Element", "Matrix", "IRC", "Mumble", "Google Voice",
    "FaceTime", "iMessage" "Reviews", "Google Reviews", "Review", "Trustpilot", "Yelp",
    "Clutch", "G2", "Capterra", "Sitejabber", "BBB",

    # --- Email ---
    "Email", "E-mail", "Gmail", "Outlook", "Yahoo Mail", "ProtonMail",
    "Email Address",

    # --- Phone / calls / messaging ---
    "Phone", "Phone Number", "Mobile Number", "Cell Number", "Contact Number",
    "Call", "Voice Call", "Video Call", "SMS", "Text Me", "DM",
    "Direct Message", "PM", "Private Message", "Inbox Me", "Contact Me",
    "Reach Me", "Personal Contact", "Contact Details", "Book a Call",
    "Schedule a Call", "Discovery Call", "Consultation Call", "Screen Share",
    "Remote Session", "Meeting ID", "Meeting Password", "Invite Code",
    "Invitation Link", "Channel Link", "Server Link", "Zoom Link",
    "Calendar Invite", "Calendly", "TidyCal", "YouCanBookMe",
    "Acuity Scheduling", "Booksy",

    # --- Websites / portfolios ---
    "Portfolio Website", "Personal Website", "Website", "My Site",
    "Landing Page", "Portfolio", "Behance", "Dribbble", "GitHub", "GitLab",
    "Company Website", "Personal Domain", "Custom Domain", "Landing URL",
    "Bio Link", "Portfolio Link", "Resume Link", "CV Link",

    # --- File sharing / cloud ---
    "Dropbox", "Google Drive", "OneDrive", "Mega", "WeTransfer", "MediaFire",
    "TransferNow", "Send Anywhere", "Share Folder", "Shared Folder",
    "Drive Link", "Dropbox Link", "Cloud Storage", "Cloud Folder",
    "Sync Folder", "NAS", "FTP Server", "S3 Bucket", "Azure Blob",
    "Google Cloud", "AWS", "DigitalOcean", "VPS", "Hosting", "cPanel", "WHM",
    "Database Backup", "ZIP File", "RAR File", "APK", "Executable", "EXE",
    "MSI", "DMG", "ISO", "Torrent", "Magnet Link", "Seedbox",

    # --- Payments ---
    "PayPal", "Wise", "Payoneer", "Stripe", "Bank Transfer", "Wire Transfer",
    "Western Union", "MoneyGram", "Cash App", "Venmo", "Zelle", "Revolut",
    "Crypto", "Cryptocurrency", "Bitcoin", "BTC", "Ethereum", "ETH", "USDT",
    "USDC", "Binance", "Coinbase", "Direct Payment", "External Payment",
    "Outside Payment", "Invoice", "Invoice Me", "Direct Deposit", "Escrow",
    "Wallet Address", "Wallet", "Wallet ID", "IBAN", "SWIFT",
    "Routing Number", "Account Number", "Transfer", "Wire", "ACH", "SEPA",
    "Crypto Wallet", "MetaMask", "Trust Wallet", "Exodus", "Binance Pay",
    "CoinPayments", "Gift Card", "Amazon Gift Card", "Steam Gift Card",
    "Apple Gift Card", "Google Play Card", "Pay Link", "Checkout Link",
    "Merchant Account", "Merchant ID", "SWIFT Code", "IBAN Number",
    "Sort Code", "Routing Code", "IFSC", "UPI", "GCash", "Paytm", "PhonePe",
    "Alipay", "Apple Pay", "Google Pay", "Samsung Pay", "PIX", "Skrill",
    "Neteller", "Perfect Money", "Payeer", "Advcash", "WebMoney", "Cash",
    "Cash Payment", "Offline Payment", "Direct Invoice", "Private Invoice",
    "Personal Invoice", "Checkout", "Invoice Link", "Payment Link",

    # --- Bypassing Fiverr ---
    "Discount Outside Fiverr", "Commission Outside Fiverr", "Off Platform",
    "Outside Fiverr", "External Contract", "Independent Contract",
    "Hire Me Directly", "Private Deal", "Bypass Fiverr", "Avoid Fiverr Fee",
    "No Fiverr Fee", "Remove Fiverr Fee", "Cancel Order",
    "Refund Outside Fiverr", "Personal Account", "Alternative Payment",
    "Outside Contract", "Independent Agreement", "Freelance Contract",
    "Private Project", "Private Client", "Direct Client",
    "Existing Client", "Repeat Client Outside Fiverr", "Referral Fee",
    "Commission", "Escrow Payment",

    # --- Remote access / credentials ---
    "AnyDesk", "TeamViewer", "Parsec", "Remote Desktop", "RDP",
    "QuickSupport", "UltraViewer", "RustDesk", "Chrome Remote Desktop",
    "FTP", "SFTP", "SSH", "VPN", "Proxy", "Remote Access", "API Key",
    "Access Key", "Password", "Login", "Username", "Credentials", "PIN",
    "Verification Code", "OTP", "SSH Access", "Root Access", "Admin Access",
    "Super Admin", "API Token", "Secret Key", "Client Secret", "OAuth",
    "Webhook", "Webhook URL",

    # --- Links / forms / project tools ---
    "Invite Link", "Meeting Link", "Join Link", "External Link", "URL",
    "Hyperlink", "Referral Link", "Affiliate Link", "Checkout Page",
    "Google Docs", "Google Sheets", "Google Forms", "Notion", "ClickUp",
    "Trello", "Asana", "Monday.com", "Basecamp", "Jira", "Airtable",
    "Figma Invite", "Canva Invite", "Adobe Creative Cloud", "Creative Cloud",
    "Contact Form", "Feedback Form", "Order Form", "Booking Page",
    "Appointment Link", "Calendly Link", "CRM", "HubSpot", "Salesforce",
    "Pipedrive", "Zoho CRM", "Freshsales", "Client Portal",
    "Customer Portal", "Member Area", "Shared Workspace", "Shared Drive",
    "Workspace", "Workspace Invite", "Organization Invite",
    "Personal Profile", "Business Profile",

    # --- Websites / portfolios ---
    "Portfolio Website", "Personal Website", "Website", "My Site",
    "Landing Page", "Portfolio", "Behance", "Dribbble", "GitHub", "GitLab",
    "Company Website", "Personal Domain", "Custom Domain", "Landing URL",
    "Bio Link", "Portfolio Link", "Resume Link", "CV Link",
    "Google Reviews", "Reviews", "Review", "Trustpilot",  # ← ADD THIS LINE
]

# --- WORDLIST LOADING ---
def get_restricted_words():
    if REMOTE_WORDLIST_URL:
        try:
            req = Request(REMOTE_WORDLIST_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list) and data:
                    return data
        except (URLError, json.JSONDecodeError, ValueError) as e:
            logging.warning(f"Remote wordlist fetch failed, using default: {e}")
    return DEFAULT_RESTRICTED_WORDS

# --- WORD OBFUSCATION ---
def make_fiverr_safe(phrase: str) -> str:
    """Insert a hyphen near the middle of each word in the matched phrase,
    preserving original spacing and case. e.g. 'call' -> 'ca-ll', 'Bank Transfer' -> 'Ba-nk Tra-nsfer'."""
    def hyphenate_word(w):
        if len(w) < 2:
            return w
        mid = max(1, len(w) // 2)
        return w[:mid] + "-" + w[mid:]
    # Split on spaces but keep them, so multi-word phrases get each word hyphenated
    parts = phrase.split(" ")
    return " ".join(hyphenate_word(p) for p in parts)

def sanitize_message(text: str, restricted_words: list) -> str:
    sorted_words = sorted(restricted_words, key=len, reverse=True)
    pattern = r"(?<!\w)(" + "|".join(re.escape(w) for w in sorted_words) + r")(?!\w)"
    regex = re.compile(pattern, re.IGNORECASE)

    def replacer(match):
        safe_word = make_fiverr_safe(match.group(0))
        return f"😑<b>{safe_word}</b>"  # ← wrap in bold

    return regex.sub(replacer, text)

# --- HANDLERS ---
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    original_text = None

    if update.message.reply_to_message:
        replied = update.message.reply_to_message
        original_text = replied.text or replied.caption
    elif context.args:
        original_text = update.message.text.split(" ", 1)[1]

    if not original_text:
        await update.message.reply_text(
            "Usage:\n"
            "• /check <your message> — paste message after command\n"
            "• Reply to any message with /check — checks that message"
        )
        return

    restricted_words = get_restricted_words()

    # Escape HTML special chars FIRST so < > & in original text don't break formatting
    escaped_text = html.escape(original_text)

    safe_text = sanitize_message(escaped_text, restricted_words)

    await update.message.reply_text(safe_text, parse_mode="HTML")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send /check <message> and I'll return the same message, Fiverr-safe."
    )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("check", check_command))
    app.run_polling()

if __name__ == "__main__":
    main()