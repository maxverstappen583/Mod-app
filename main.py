import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
from flask import Flask
from threading import Thread
import sys
import socket

# === Flask keep-alive ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# === Bot setup ===
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

OWNER_ID = 1319292111325106296  # your ID
application_channel_id = None   # will be set with a command

# === Ready Event ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    # Send DM to owner
    try:
        owner = await bot.fetch_user(OWNER_ID)
        host = socket.gethostname()
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        await owner.send(f"✅ {bot.user.name} is now online!\n🖥️ Host: `{host}`\n⏰ Time: {now}")
    except Exception as e:
        print(f"⚠️ Could not DM owner: {e}")

# === Ping Command ===
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# === Set Application Result Channel ===
@bot.command()
@commands.has_permissions(administrator=True)
async def set_app_channel(ctx, channel: discord.TextChannel):
    global application_channel_id
    application_channel_id = channel.id
    await ctx.send(f"✅ Application results will now go to {channel.mention}")

# === Apply Command ===
@bot.tree.command(name="apply", description="Submit an application")
async def apply(interaction: discord.Interaction, age: int, reason: str):
    global application_channel_id

    # Account age check
    account_age = (discord.utils.utcnow() - interaction.user.created_at).days
    if account_age < 35:  # ~5 weeks
        return await interaction.response.send_message(
            "❌ Your account must be at least 5 weeks old to apply.", ephemeral=True
        )

    # Age check (under 13 reject)
    if age < 13:
        return await interaction.response.send_message(
            "❌ You must be 13 or older to apply.", ephemeral=True
        )

    # If no app channel is set
    if not application_channel_id:
        return await interaction.response.send_message(
            "⚠️ The application channel has not been set yet.", ephemeral=True
        )

    # Send application embed
    embed = discord.Embed(
        title="📩 New Application",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="👤 User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
    embed.add_field(name="📆 Account Age", value=f"{account_age} days", inline=False)
    embed.add_field(name="🎂 Stated Age", value=str(age), inline=False)
    embed.add_field(name="📝 Reason", value=reason, inline=False)

    channel = bot.get_channel(application_channel_id)
    if channel:
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Your application has been submitted!", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Application channel not found.", ephemeral=True)

# === Sync Commands ===
@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

# === Run bot ===
keep_alive()
token = os.getenv("DISCORD_BOT_TOKEN")

if not token:
    print("❌ ERROR: No token found! Did you set DISCORD_BOT_TOKEN in your .env or Render environment?")
    sys.exit(1)

try:
    bot.run(token)
except discord.LoginFailure:
    print("❌ ERROR: Invalid bot token! Please check your DISCORD_BOT_TOKEN value.")
    sys.exit(1)
