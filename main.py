# BU KOD REİCHİSREAL TARAFINDAN YAZILMIŞTIR VE GİTHUB ÜZERİNDEN PAYLAŞILMIŞ PUBLİC BİR KODDUR
# DAHA FAZLA KOD İÇİN https://discord.com/users/1351199098752995509 BANA ULAŞ!
# MIT License

# Copyright (c) [2026] [REICH]

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import subprocess
import io
import asyncio
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

REQUIRED_PACKAGES = {
    "davey": "davey",
    "PyNaCl": "nacl",
    "discord.py[voice]": "discord"
}

def check_and_install_packages():
    for package, import_name in REQUIRED_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"[REICH.SYSTEMS] '{package}' eksik yükleniyor.")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])
            except Exception:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                except Exception as e:
                    print(f"[HATA] {package} yüklenemedi: {e}")

check_and_install_packages()

import discord
from discord.ext import commands

TURKEY_TZ = ZoneInfo("Europe/Istanbul")

CONFIG = {
    "TOKEN": "BURAYA BOT TOKENİNİ YAZ",
    "OWNER_IDS": [], # PARANTEZ İÇİNE OWNER ID
    "PANEL_CHANNEL_ID": , # VİRGÜLDEN HEMEN ÖNCE TİCKET MESAJININ GİDECEĞİ KANAL ID
    "CATEGORY_ID": , # VİRGÜLDEN HEMEN ÖNCE TİCKETLARIN OLUŞACAĞI KATEGORİ ID
    "STAFF_ROLE_ID": , # VİRGÜLDEN HEMEN ÖNCE TİCKET YETKİLİSİ 
    "LOG_CHANNEL_ID": , # VİRGÜLDEN HEMEN ÖNCE TİCKET LOG KANAL ID 
    "VOICE_CHANNEL_ID": None # DOKUNMANA GEREK YOK
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="+", intents=intents)

def is_staff_or_owner():
    async def predicate(ctx):
        if ctx.author.id in CONFIG["OWNER_IDS"] or ctx.author.id == ctx.guild.owner_id:
            return True
        if ctx.author.guild_permissions.administrator:
            return True
        staff_role = ctx.guild.get_role(CONFIG["STAFF_ROLE_ID"]) if CONFIG["STAFF_ROLE_ID"] else None
        if staff_role and staff_role in ctx.author.roles:
            return True
        return False
    return commands.check(predicate)

def is_only_staff():
    async def predicate(ctx):
        staff_role_id = CONFIG.get("STAFF_ROLE_ID")
        if staff_role_id and any(role.id == staff_role_id for role in ctx.author.roles):
            return True
        return False
    return commands.check(predicate)

async def generate_transcript(channel: discord.TextChannel):
    messages = []
    
    async for msg in channel.history(limit=None, oldest_first=True):
        msg_time = msg.created_at.astimezone(TURKEY_TZ)
        timestamp = msg_time.strftime("%Y-%m-%d %H:%M:%S")
        
        author = msg.author.name
        content = msg.content
        if msg.attachments:
            attachments_urls = " ".join([att.url for att in msg.attachments])
            content += f" [EKLER: {attachments_urls}]"
        messages.append(f"[{timestamp}] {author}: {content}")

    created_at_tr = channel.created_at.astimezone(TURKEY_TZ).strftime('%Y-%m-%d %H:%M:%S')
    closed_at_tr = datetime.now(TURKEY_TZ).strftime('%Y-%m-%d %H:%M:%S')

    log_text = f"=== {channel.name.upper()} MESAJ GEÇMİŞİ (TRANSCRIPT) ===\n"
    log_text += f"Oluşturulma Tarihi: {created_at_tr}\n"
    log_text += f"Kapanış Tarihi: {closed_at_tr}\n"
    log_text += "=" * 50 + "\n\n"
    log_text += "\n".join(messages)

    file_buffer = io.BytesIO(log_text.encode('utf-8'))
    return discord.File(fp=file_buffer, filename=f"{channel.name}-transcript.txt")

async def close_ticket_logic(channel, author, guild):
    if CONFIG["LOG_CHANNEL_ID"]:
        log_channel = guild.get_channel(CONFIG["LOG_CHANNEL_ID"])
        if log_channel:
            try:
                transcript_file = await generate_transcript(channel)
                log_embed = discord.Embed(
                    title="🔒 Ticket Kapatıldı & Chatlog Raporlandı",
                    description=f"**{channel.name}** isimli destek kanalı kapatıldı. Mesaj dökümü ekteki `.txt` dosyasındadır.",
                    color=discord.Color.red()
                )
                log_embed.add_field(name="Kanal Adı", value=channel.name, inline=True)
                log_embed.add_field(name="Kapatan", value=author.name, inline=True)
                log_embed.add_field(name="Kapanış Tarihi", value=f"<t:{int(time.time())}:F>", inline=True)
                log_embed.set_footer(text="Reich • Log Sistemi")

                await log_channel.send(embed=log_embed, file=transcript_file)
            except Exception as e:
                print(f"[HATA] Log atılırken bir sorun oluştu: {e}")

    await channel.delete()

async def claim_ticket_logic(channel, user, message=None, view=None):
    claim_text = f"{user.mention} ticketi üstlendi sorununuzu anlatabilirsiniz."
    
    if message and view:
        for child in view.children:
            if child.custom_id == "claim_ticket":
                child.disabled = True
        await message.edit(view=view)
        
    await channel.send(claim_text)

async def join_voice_channel(guild: discord.Guild, channel_id: int):
    voice_channel = guild.get_channel(channel_id)
    if not isinstance(voice_channel, discord.VoiceChannel):
        return False, "❌ Geçersiz ses kanalı ID'si!"

    try:
        if guild.voice_client:
            await guild.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect(reconnect=True, self_deaf=True, self_mute=True)
            
        CONFIG["VOICE_CHANNEL_ID"] = channel_id
        return True, f"✅ Reich.Systems ile **{voice_channel.name}** ses kanalına katıldım."
    except Exception as e:
        return False, f"❌ Ses kanalına katılırken bir hata oluştu: `{e}`"

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket'ı Üstlen", style=discord.ButtonStyle.success, emoji="✋", custom_id="claim_ticket")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role_id = CONFIG.get("STAFF_ROLE_ID")
        has_staff_role = False

        if staff_role_id and any(role.id == staff_role_id for role in interaction.user.roles):
            has_staff_role = True

        if not has_staff_role:
            return await interaction.response.send_message(
                "❌ Bu işlemi yalnızca **Yetkili Ekibi** gerçekleştirebilir.", ephemeral=True
            )

        await interaction.response.defer()
        await claim_ticket_logic(interaction.channel, interaction.user, interaction.message, self)

    @discord.ui.button(label="Ticket Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket kapatılıyor...")
        await asyncio.sleep(2)
        await close_ticket_logic(interaction.channel, interaction.user, interaction.guild)

async def create_ticket_channel(interaction: discord.Interaction, ticket_type: str, color: discord.Color):
    guild = interaction.guild
    user = interaction.user

    clean_username = "".join(c for c in user.name.lower() if c.isalnum())
    channel_name = f"ticket-{clean_username}"

    existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
    if existing_channel:
        return await interaction.response.send_message(
            f"Zaten açık bir destek talebiniz bulunuyor: {existing_channel.mention}", ephemeral=True
        )

    await interaction.response.defer(ephemeral=True)

    staff_role = guild.get_role(CONFIG["STAFF_ROLE_ID"]) if CONFIG["STAFF_ROLE_ID"] else None
    category_obj = guild.get_channel(CONFIG["CATEGORY_ID"]) if CONFIG["CATEGORY_ID"] else None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
        guild.me: discord.PermissionOverwrite(
            read_messages=True, 
            send_messages=True, 
            embed_links=True, 
            attach_files=True, 
            manage_channels=True,
            manage_permissions=True
        )
    }
    
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)

    try:
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category_obj,
            overwrites=overwrites
        )
    except Exception as e:
        print(f"\n[Kanal Oluşturma Hatası]: {e}")
        return await interaction.followup.send(f"❌ Ticket kanalı oluşturulamadı: `{e}`", ephemeral=True)

    try:
        ticket_embed = discord.Embed(
            title=f"Destek Talebi: {ticket_type}",
            description=(
                f"Merhaba {user.mention}, destek talebiniz başarıyla oluşturuldu.\n\n"
                f"Yetkili ekibimiz en kısa sürede sizinle ilgilenecektir. Lütfen sorununuzu detaylıca açıklayın.\n\n"
                f"**Oluşturan:** {user.name}\n"
                f"**Kategori:** {ticket_type}\n"
                f"**Tarih:** <t:{int(time.time())}:R>"
            ),
            color=color
        )
        ticket_embed.set_footer(text="Reich  • Destek Sistemi")

        staff_ping = staff_role.mention if staff_role else "@Yetkili"

        await ticket_channel.send(
            content=f"{user.mention} | {staff_ping}",
            embed=ticket_embed,
            view=TicketControlView()
        )

        await interaction.followup.send(f"Ticket kanalınız oluşturuldu: {ticket_channel.mention}", ephemeral=True)

    except Exception as e:
        print(f"\n[Mesaj Gönderme Hatası]: {e}")
        traceback.print_exc()
        await interaction.followup.send(
            f"❌ Ticket oluşturulurken bir hata oluştu: `{e}`", ephemeral=True
        )

class TicketSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Destek, Bug & Teknik Sorunlar",
                description="Oyun Dışı Sorunlar için açınız.",
                emoji="🔧",
                value="tekno_bug"
            ),
            discord.SelectOption(
                label="Oyun içi Sorunlar & Rol Hataları",
                description="Oyun içi Sorunlar için açınız.",
                emoji="🎮",
                value="ic_sorun"
            ),
            discord.SelectOption(
                label="AntiCheat",
                description="AntiCheat ile ilgili konular için açınız.",
                emoji="🚨",
                value="anticheat"
            ),
            discord.SelectOption(
                label="Diğer Kategoriler",
                description="Sebebiniz Eğer Burada Yoksa, Bu Kategoride Ticket Açın.",
                emoji="🐱",
                value="diger"
            ),
            discord.SelectOption(
                label="Seçenek Sıfırla",
                description="Seçenekleri Sıfırlamanıza Yarar.",
                emoji="🧹",
                value="reset"
            )
        ]
        super().__init__(
            placeholder="Ticket Açmak İçin Kategori Seçiniz.",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select_menu"
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]

        if selected == "reset":
            return await interaction.response.send_message(
                "🔄 Seçim sıfırlandı, yeni bir kategori seçebilirsiniz.", ephemeral=True
            )
        elif selected == "tekno_bug":
            await create_ticket_channel(interaction, "Destek, Bug & Teknik Sorunlar", discord.Color.orange())
        elif selected == "ic_sorun":
            await create_ticket_channel(interaction, "Oyun içi Sorunlar & Rol Hataları", discord.Color.green())
        elif selected == "anticheat":
            await create_ticket_channel(interaction, "AntiCheat", discord.Color.red())
        elif selected == "diger":
            await create_ticket_channel(interaction, "Diğer Kategoriler", discord.Color.gold())

class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelectMenu())

@bot.event
async def on_ready():
    bot.add_view(TicketSelectView())
    bot.add_view(TicketControlView())
    
    activity = discord.Streaming(
        name="Created By Reich",
        url="https://www.twitch.tv/twitch"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)
    
    print(f"[REICH.BOTS] {bot.user} aktif. Daha fazlası için https://discord.com/users/1351199098752995509")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None:
        voice_id = CONFIG.get("VOICE_CHANNEL_ID")
        if voice_id:
            await asyncio.sleep(3)
            await join_voice_channel(member.guild, voice_id)

@bot.command(name="ses")
@is_staff_or_owner()
async def ses_cmd(ctx, channel_id: int = None):
    """Botu belirtilen ses kanalına sokar (7/24 AFK Modu)."""
    await ctx.message.delete()

    target_channel_id = channel_id or CONFIG.get("VOICE_CHANNEL_ID")

    if not target_channel_id:
        return await ctx.send(
            "❌ Lütfen geçerli bir ses kanalı ID'si girin!\n**Kullanım:** `+ses 123456789012345678`",
            delete_after=7
        )

    success, message = await join_voice_channel(ctx.guild, target_channel_id)
    await ctx.send(message, delete_after=7)

@bot.command(name="ticket")
@is_staff_or_owner()
async def ticket_cmd(ctx):
    """Ticket Panelini oluşturur."""
    await ctx.message.delete()
    target_channel = bot.get_channel(CONFIG["PANEL_CHANNEL_ID"])
    if not target_channel:
        return await ctx.send("❌ **Hata:** `PANEL_CHANNEL_ID` bulunamadı. Lütfen CONFIG ayarlarını kontrol edin.", delete_after=5)

    embed = discord.Embed(
        title="Reich - Destek Sistemi",
        description=(
            "Sunucumuzla ilgili bir konuda yardıma ihtiyacınız varsa veya bir işlem yaptırmak istiyorsanız aşağıdaki menüyü kullanabilirsiniz.\n\n"
            "Tüm şikayetleriniz için ticket açabilirsiniz.\n"
            "Video kayıtsız işlem yapılmamaktadır.\n"
            "Anlayışınız için teşekkür ederiz.\n\n"
            "İyi roller dileriz.*"
        ),
        color=discord.Color.from_rgb(43, 45, 49)
    )
    embed.set_footer(text="Reich • Support System")

    await target_channel.send(embed=embed, view=TicketSelectView())
    await ctx.send(f"✅ Ticket paneli {target_channel.mention} kanalına gönderildi.", delete_after=5)

@bot.command(name="sahiplen")
@is_only_staff()
async def sahiplen_cmd(ctx):
    """Ticket kanalını sahiplenme komutu (Sadece Yetkili Rolüne Özel)"""
    await ctx.message.delete()
    
    if not ctx.channel.name.startswith("ticket-"):
        return await ctx.send("❌ Bu komutu yalnızca bir **ticket kanalında** kullanabilirsiniz.", delete_after=5)

    await claim_ticket_logic(ctx.channel, ctx.author)

@bot.command(name="kapat")
@is_staff_or_owner()
async def kapat_cmd(ctx):
    """Ticket kanalını kapatma ve transcript oluşturma komutu"""
    await ctx.message.delete()

    if not ctx.channel.name.startswith("ticket-"):
        return await ctx.send("❌ Bu komutu yalnızca bir **ticket kanalında** kullanabilirsiniz.", delete_after=5)

    await ctx.send("🔒 Ticket kapatılıyor ve chatlog hazırlanıyor...")
    await asyncio.sleep(2)
    await close_ticket_logic(ctx.channel, ctx.author, ctx.guild)

@ses_cmd.error
@ticket_cmd.error
@sahiplen_cmd.error
@kapat_cmd.error
async def command_error_handler(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ Bu işlemi gerçekleştirmek için yetkiniz bulunmuyor.", delete_after=5)

bot.run(CONFIG["TOKEN"])