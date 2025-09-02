import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from flask import Flask
from threading import Thread

# -------------------- CONFIG --------------------
DATA_FILE = "mod_applications.json"  # JSON file to store applications
CONFIG_FILE = "config.json"  # JSON file for persistent settings
MIN_ACCOUNT_AGE_DAYS = 35  # Minimum account age in days (5 weeks)
MIN_USER_AGE = 13  # Minimum reported age
# ------------------------------------------------

TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Bot token from environment variable
APPLICATION_CHANNEL_ID = None  # Will load from config or be set dynamically

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load existing applications
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        applications = json.load(f)
else:
    applications = []

# Load saved config
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        APPLICATION_CHANNEL_ID = config.get("application_channel_id", APPLICATION_CHANNEL_ID)

# ----------------- Helper -----------------
def get_account_age(created_at: datetime):
    now = datetime.utcnow()
    delta = now - created_at.replace(tzinfo=None)
    days = delta.days
    years, days = divmod(days, 365)
    months, days = divmod(days, 30)
    weeks, days = divmod(days, 7)
    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years>1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months>1 else ''}")
    if weeks > 0:
        parts.append(f"{weeks} week{'s' if weeks>1 else ''}")
    if days > 0:
        parts.append(f"{days} day{'s' if days>1 else ''}")
    return ", ".join(parts) if parts else "0 days"

# ----------------- Modal Definition -----------------
class ModApplicationModal(discord.ui.Modal, title="MIDNIGHT VIBE – Moderator Application"):

    age = discord.ui.TextInput(label="Age", style=discord.TextStyle.short, required=True)
    time_zone = discord.ui.TextInput(label="Time Zone", style=discord.TextStyle.short, required=True)

    experience = discord.ui.TextInput(label="Previous moderation experience", style=discord.TextStyle.paragraph, required=True)
    tools = discord.ui.TextInput(label="Familiarity with Discord tools", style=discord.TextStyle.paragraph, required=True)
    handle_rules = discord.ui.TextInput(label="Handling repeated rule-breakers", style=discord.TextStyle.paragraph, required=True)
    resolve_conflicts = discord.ui.TextInput(label="Resolving conflicts between members/staff", style=discord.TextStyle.paragraph, required=True)
    maintain_authority = discord.ui.TextInput(label="Maintaining authority fairly", style=discord.TextStyle.paragraph, required=True)

    availability = discord.ui.TextInput(label="Hours per day/week available", style=discord.TextStyle.paragraph, required=True)
    respond_immediately = discord.ui.TextInput(label="Willingness to respond immediately", style=discord.TextStyle.paragraph, required=True)
    multiple_incidents = discord.ui.TextInput(label="Handling multiple simultaneous violations", style=discord.TextStyle.paragraph, required=True)

    situational_1 = discord.ui.TextInput(label="Member harasses claiming 'it's just a joke'", style=discord.TextStyle.paragraph, required=True)
    situational_2 = discord.ui.TextInput(label="Moderator abusing power observed", style=discord.TextStyle.paragraph, required=True)
    situational_3 = discord.ui.TextInput(label="Member ignores repeated warnings", style=discord.TextStyle.paragraph, required=True)
    situational_4 = discord.ui.TextInput(label="Member challenges your authority publicly", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Validate reported age
        try:
            user_age = int(self.age.value)
        except ValueError:
            await interaction.response.send_message("❌ Invalid age provided. Please enter a number.", ephemeral=True)
            return

        if user_age < MIN_USER_AGE:
            await interaction.response.send_message(f"❌ You must be {MIN_USER_AGE}+ years old to apply.", ephemeral=True)
            return

        # Auto-calculate account age
        account_age_str = get_account_age(interaction.user.created_at)

        embed = discord.Embed(
            title="⭑⭑｡̣̩̩͙✩̣̩̩̥ੈ MIDNIGHT VIBE ⭑⭑｡̣̩̩͙✩̣̩̩̥ੈ – Moderator Application",
            description=f"Moderator application submitted by {interaction.user.mention}",
            color=0x6A0DAD
        )

        embed.add_field(name="1️⃣ Personal Information",
                        value=f"• **Age:** {self.age.value}\n"
                              f"• **Time Zone:** {self.time_zone.value}\n"
                              f"• **Discord Account Age:** {account_age_str}",
                        inline=False)

        embed.add_field(name="2️⃣ Experience & Competency",
                        value=f"1. Previous experience: {self.experience.value}\n"
                              f"2. Discord tools: {self.tools.value}\n"
                              f"3. Handling repeated rule-breakers: {self.handle_rules.value}\n"
                              f"4. Resolving conflicts: {self.resolve_conflicts.value}\n"
                              f"5. Maintaining authority: {self.maintain_authority.value}",
                        inline=False)

        embed.add_field(name="3️⃣ Availability & Commitment",
                        value=f"1. Hours available: {self.availability.value}\n"
                              f"2. Respond immediately: {self.respond_immediately.value}\n"
                              f"3. Multiple incidents: {self.multiple_incidents.value}",
                        inline=False)

        embed.add_field(name="4️⃣ Situational Assessment",
                        value=f"1. Harassment 'joke': {self.situational_1.value}\n"
                              f"2. Moderator abuse: {self.situational_2.value}\n"
                              f"3. Ignoring warnings: {self.situational_3.value}\n"
                              f"4. Authority challenge: {self.situational_4.value}",
                        inline=False)

        embed.add_field(name="5️⃣ Final Declaration",
                        value="☐ I am 13+ years old\n"
                              "☐ My Discord account is older than 5 weeks\n"
                              "☐ I have read, understood, and will strictly follow all server rules\n"
                              "☐ I understand failure to perform duties will result in immediate removal",
                        inline=False)

        channel = bot.get_channel(APPLICATION_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)

            # Save application
            applications.append({
                "user_id": interaction.user.id,
                "username": str(interaction.user),
                "age": self.age.value,
                "time_zone": self.time_zone.value,
                "account_age": account_age_str,
                "experience": self.experience.value,
                "tools": self.tools.value,
                "handle_rules": self.handle_rules.value,
                "resolve_conflicts": self.resolve_conflicts.value,
                "maintain_authority": self.maintain_authority.value,
                "availability": self.availability.value,
                "respond_immediately": self.respond_immediately.value,
                "multiple_incidents": self.multiple_incidents.value,
                "situational_1": self.situational_1.value,
                "situational_2": self.situational_2.value,
                "situational_3": self.situational_3.value,
                "situational_4": self.situational_4.value,
                "timestamp": str(interaction.created_at)
            })
            with open(DATA_FILE, "w") as f:
                json.dump(applications, f, indent=4)

            await interaction.response.send_message("✅ Your moderator application has been submitted.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Application channel not set. Ask an admin to set it using `/set_application_channel`.", ephemeral=True)

# ---------------- Slash Command to open modal -----------------
@bot.tree.command(name="apply_mod", description="Open the moderator application form")
async def apply_mod(interaction: discord.Interaction):
    # Check account age
    account_age_days = (datetime.utcnow() - interaction.user.created_at.replace(tzinfo=None)).days
    if account_age_days < MIN_ACCOUNT_AGE_DAYS:
        await interaction.response.send_message(
            f"❌ You are not allowed to submit a moderator application. Your account is under 5 weeks old.",
            ephemeral=True
        )
        return

    modal = ModApplicationModal()
    await interaction.response.send_modal(modal)

# ---------------- Admin Command to Send Embed -----------------
@bot.tree.command(name="send_mod_application", description="Send the mod application embed to a channel")
async def send_mod_application(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    if not APPLICATION_CHANNEL_ID:
        await interaction.response.send_message("❌ Application channel not set. Use `/set_application_channel` first.", ephemeral=True)
        return

    embed = discord.Embed(
        title="⭑⭑｡̣̩̩͙✩̣̩̩̥ੈ MIDNIGHT VIBE ⭑⭑｡̣̩̩͙✩̣̩̩̥ੈ – MODERATOR APPLICATION",
        description="Complete all sections carefully. Incomplete or dishonest applications will be rejected.",
        color=0x6A0DAD
    )

    embed.add_field(name="1️⃣ Requirements",
                    value="• 13 years or older\n"
                          "• Discord account older than 5 weeks\n"
                          "• Must read, understand, and follow all server rules\n"
                          "• Must act with professionalism, authority, and fairness\n"
                          "• Failure to uphold duties will result in immediate removal",
                    inline=False)

    embed.add_field(name="2️⃣ Personal Information",
                    value="• **Age:**\n• **Time Zone:**\n• **Discord Account Age:**",
                    inline=False)

    embed.add_field(name="3️⃣ Experience & Competency",
                    value="1. Previous moderation experience (platforms and duration):\n"
                          "2. Familiarity with Discord moderation tools (bots, roles, permissions, audit logs):\n"
                          "3. How would you handle a member repeatedly breaking rules?\n"
                          "4. How would you resolve conflicts between members or staff without bias?\n"
                          "5. How do you maintain authority while ensuring fairness?",
                    inline=False)

    embed.add_field(name="4️⃣ Availability & Commitment",
                    value="1. Hours per day/week available for moderation:\n"
                          "2. Willingness to respond to incidents immediately:\n"
                          "3. Approach to handling multiple simultaneous rule violations:",
                    inline=False)

    embed.add_field(name="5️⃣ Situational Assessment",
                    value="1. A member harasses someone claiming “it’s just a joke.” Action:\n"
                          "2. Observing another moderator abusing power. Steps:\n"
                          "3. A member ignores repeated warnings. How do you proceed?\n"
                          "4. A member challenges your authority publicly. Response:",
                    inline=False)

    embed.add_field(name="6️⃣ Final Declaration",
                    value="☐ I am 13+ years old\n"
                          "☐ My Discord account is older than 5 weeks\n"
                          "☐ I have read, understood, and will strictly follow all server rules\n"
                          "☐ I understand failure to perform duties will result in immediate removal",
                    inline=False)

    channel = bot.get_channel(APPLICATION_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Moderator application embed sent.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Application channel not found.", ephemeral=True)

# ----------------- Set Application Channel -----------------
@bot.tree.command(name="set_application_channel", description="Set the channel where mod applications will be sent")
async def set_application_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    global APPLICATION_CHANNEL_ID
    APPLICATION_CHANNEL_ID = channel.id

    # Save channel ID to config
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    config["application_channel_id"] = APPLICATION_CHANNEL_ID
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    await interaction.response.send_message(f"✅ Application channel set to {channel.mention}", ephemeral=True)

# -------------------- Flask for keep-alive --------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

Thread(target=run).start()

bot.run(TOKEN)
