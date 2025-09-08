import discord
from discord.ext import commands
import sqlite3
import requests
import xml.etree.cElementTree as ET
import re
from discord.ext import tasks
import asyncio 

TOKEN = "YOUR TOKEN HERE"
CHANNEL_ID = YOUR CHANNEL ID HERE
DISCORD_USERS = [] 

# ---------- Discord setup ----------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
channel = bot.get_channel(CHANNEL_ID)

# ---------- Database ----------
conn = sqlite3.connect("botdata.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    discord_id INT PRIMARY KEY,
    letterboxd_username TEXT NOT NULL,
    pubDate TEXT
)
""")
conn.commit()

def update_user(username, discord_id, pubDate):
    DISCORD_USERS.append(discord_id)
    cursor.execute("""
    INSERT INTO users (discord_id, letterboxd_username, pubDate)
    VALUES (?, ?, ?)
    ON CONFLICT(discord_id) DO UPDATE SET
        letterboxd_username=excluded.letterboxd_username,
        pubDate=excluded.pubDate
    """, (discord_id, username, pubDate))
    conn.commit()

def get_user(discord_id):
    cursor.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
    return cursor.fetchone()

def load_users():
    cursor.execute("SELECT discord_id FROM users")
    rows = cursor.fetchall()
    for row in rows:
        DISCORD_USERS.append(row[0])
    return

# ---------- rss ----------
def fetch_rss_for_user(letterboxd_username):
    rss_url = f"https://letterboxd.com/{letterboxd_username}/rss/"
    try:
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return 404
        else:
            return 500
    except requests.exceptions.RequestException as e:
        return 408
    
    root = ET.fromstring(response.content)
    channel = root.find("channel")
    items = channel.findall("item")

    reviews = []
    for item in items:
        pubDate = item.findtext("pubDate")
        title = item.findtext("title")
        description = item.findtext("description")
        reviews.append((pubDate, title, description))
    return reviews

def format_review(data, user):
    review = re.search(r"<p>(.*?)</p>\s*<p>(.*?)</p>", data, re.DOTALL).group(2)
    return '||"' + review + '"|| - ' + user

# ---------- Interval Check ----------
async def check_user(discord_id):
    user_data = get_user(discord_id)
    print("checking user: " + user_data[1])
    data = fetch_rss_for_user(user_data[1])
    if data in (404, 408, 500):
        print("error checking\n")
        return None
    
    new_reviews = []
    for review in data:
        pubDate, title, description = review
        if pubDate == user_data[2]:
            break
        formatted = format_review(description, user_data[1])
        new_reviews.append((pubDate, title, formatted))

    if new_reviews == None:
        print("no new reviews\n")
    if new_reviews:
        update_user(user_data[1], discord_id, new_reviews[0][0])
        print("found new reviews, updating database\n")

    return reversed(new_reviews)

@tasks.loop(seconds=60)
async def staggered_check():
    interval = 600 / len(DISCORD_USERS)
    for discord_id in DISCORD_USERS:
        reviews = await check_user(discord_id)
        if reviews != None:
            for pubDate, title, review in reviews:
                channel = bot.get_channel(CHANNEL_ID)
                await channel.send(title)
                await channel.send(review)

        await asyncio.sleep(interval)  # wait before next user

# ---------- Bot Events ----------
@bot.event
async def on_ready():
    load_users()
    staggered_check.start()

@bot.command(name="addme")
async def add_me(ctx, arg):
    print("recieved command")
    if ctx.channel.id != CHANNEL_ID:
        return
    
    discord_id = ctx.author.id
    member = await ctx.guild.fetch_member(discord_id)
    data = fetch_rss_for_user(arg)
    if data == 404:
        await ctx.send("Letterboxd User not found")
        return
    elif data == 408:
        await ctx.send("Request timed out, try again later :(")
        return
    elif data== 500:
        await ctx.send("Error occured, try again later :(")
        return
    
    update_user(arg, discord_id, data[0][0])
    await ctx.send("Account Added")
    await ctx.send(data[0][1])
    await ctx.send(format_review(data[0][2], member.display_name))


load_users()    
bot.run(TOKEN)
