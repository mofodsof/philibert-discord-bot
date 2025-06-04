from keep_alive import keep_alive
import cloudscraper
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
import time
import json
import os

keep_alive()

URL = "https://www.philibertnet.com/fr/212-pokemon"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1379807819682938920/tmRFtNgkwMPf-URy-vxn12iwJqSDcIRtB29Kn_WLFGBQTf9oEpE2HEvn15F4L1cK2hc0"
scraper = cloudscraper.create_scraper()
STATE_FILE = "product_state.json"

# Charger l'état précédent
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        product_state = json.load(f)
else:
    product_state = {}

def is_product_available_and_get_image(product_url):
    r = scraper.get(product_url)
    soup = BeautifulSoup(r.text, "html.parser")
    add_button = soup.select_one('button.add-to-cart')
    is_available = add_button is not None
    image_tag = soup.select_one('img[itemprop="image"]')
    image_url = image_tag["src"] if image_tag else None
    return is_available, image_url

def get_products():
    r = scraper.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")
    product_blocks = soup.select('.product-miniature h3.product-title a')
    products = []
    for a in product_blocks:
        title = a.get_text(strip=True)
        link = "https://www.philibertnet.com" + a["href"]
        products.append((title, link))
    return products

def send_discord_notification(title, link, image_url=None):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    embed = DiscordEmbed(
        title=title,
        description=f"✅ **Disponible !**\n🔗 [Voir le produit]({link})",
        color='03b2f8'
    )
    if image_url:
        embed.set_thumbnail(url=image_url)
    webhook.add_embed(embed)
    webhook.execute()

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(product_state, f)

def check_for_updates():
    global product_state
    products = get_products()
    for title, link in products:
        available, image_url = is_product_available_and_get_image(link)
        was_available = product_state.get(link, {}).get("available", False)

        if available and not was_available:
            send_discord_notification(title, link, image_url)

        # Mettre à jour l'état du produit
        product_state[link] = {"available": available, "title": title}

    save_state()

while True:
    print("🔍 Vérification en cours...")
    check_for_updates()
    time.sleep(10)
