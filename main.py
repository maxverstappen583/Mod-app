import discord
from discord.ext import commands
from discord import app_commands, ui
import os
import datetime
import json
from flask import Flask
from threading import Thread

# -------------------------
# Flask keep-alive
# -------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# -------------------------
# Load env variables
# -------------------------
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# JSON Storage
# -------------------------
DATA_FILE = "settings.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"application_channel": None}, f)

def load_settings():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_settings(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# -------------------------
# Modal for application
# -------------------------
class ModApplication(ui.Modal, title="Moderator Application"):
    why = ui.TextInput(label="Why do you want to be a mod?", style=discord.TextStyle.paragraph)
    experience = ui.TextInput(label="Do you have moderation experience?", style=discord.TextStyle.paragraph)
    timezone = ui.TextInput(label="Your Timezone (e.g. GMT+5:30)", style=discord.TextStyle.short)
    active = ui.TextInput(label="How active can you be daily?", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user
        created_at = user.created_at
        now = datetime.datetime.utcnow()
        age = now - created_at

        # Auto-calculated account age
        years = age.days // 365
        months = (age.days % 365) // 30
        weeks = ((age.days % 365) % 30) // 7
        days = ((age.days % 365) % 30) % 7
        age_str = f"{years}y {months}m {weeks}w {days}d"

        # Checks
        if age.days < 35:
            return await interaction.response.send_message("❌ You must have an account at least **5 weeks old** to apply.", ephemeral=True)

        if years < 13:
            return await interaction.response.send_message("❌ You must be at least **13 years old** to apply.", ephemeral=True)

        # Send to configured channel
        settings = load_settings()
        channel_id = settings.get("application_channel")
        channel = interaction.guild.get_channel(channel_id) if channel_id else None

        embed = discord.Embed(title="📋 New Moderator Application", color=discord.Color.blue())
        embed.add_field(name="Applicant", value=f"{user.mention} (`{user.id}`)", inline=False)
        embed.add_field(name="Account Age", value=age_str, inline=True)
        embed.add_field(name="Why Mod?", value=self.why.value, inline=False)
        embed.add_field(name="Experience", value=self.experience.value, inline=False)
        embed.add_field(name="Timezone", value=self.timezone.value, inline=True)
        embed.add_field(name="Activity", value=self.active.value, inline=True)
        embed.timestamp = now

        if channel:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Your application has been submitted!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Application channel not set by admins.", ephemeral=True)

# -------------------------
# Commands
# -------------------------
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    print(f"Bot is ready: {bot.user}")

# Command to apply
@bot.tree.command(name="apply", description="Submit a moderator application")
async def apply(interaction: discord.Interaction):
    created_at = interaction.user.created_at
    now = datetime.datetime.utcnow()
    age = now - created_at

    if age.days < 35:
        return await interaction.response.send_message("❌ Your account must be at least 5 weeks old to apply.", ephemeral=True)

    years = age.days // 365
    if years < 13:
        return await interaction.response.send_message("❌ You must be at least 13 years old to apply.", ephemeral=True)

    await interaction.response.send_modal(ModApplication())

# Admin command to set application channel
@bot.tree.command(name="set_app_channel", description="Set the channel where applications will be sent")
@app_commands.checks.has_permissions(administrator=True)
async def set_app_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    settings = load_settings()
    settings["application_channel"] = channel.id
    save_settings(settings)
    await interaction.response.send_message(f"✅ Application channel set to {channel.mention}", ephemeral=True)

# Error handler
@set_app_channel.error
async def set_app_channel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You don’t have permission to run this command.", ephemeral=True)

# -------------------------
# Run bot
# -------------------------
bot.run(TOKEN)
