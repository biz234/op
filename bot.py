import asyncio
import base64
import os
import re
import discord
from discord.ext import commands

# ==================== CONFIGURATION ====================
BOT_TOKEN = "MTU3MjcwMzEyNDUwNDcxMTQyOQ.GK_tMt.gqcxEKdzrdihPGHgRhxZ38uIjpicV3Zjovljzk"
PC_KEY = "cats"
MOBILE_KEY = "cats"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
# =======================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def parse_linkvertise_url(url: str):
    match = re.search(r'linkvertise\.com/(\d+)/(\d+)/dynamic\?r=([A-Za-z0-9+/=_-]+)', url)
    if not match:
        raise ValueError("Invalid Linkvertise URL format")
    
    pid, lid, encoded_route = match[1], match[2], match[3]
    decoded_dest = base64.b64decode(encoded_route + '==').decode('utf-8', errors='ignore')
    domain_match = re.search(r'https?://([^/?#]+)', decoded_dest)
    domain = domain_match[1] if domain_match else "receb.net"
    
    return pid, lid, encoded_route, decoded_dest, domain

async def run_bypass(target_url: str):
    print(f"[LOG] 🚀 Starting Playwright (Headless) for URL: {target_url}")
    _, _, _, _, dest_domain = parse_linkvertise_url(target_url)
    final_url = None

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            # รันบนคลาวด์ต้องใช้ headless=True เสมอเพราะไม่มีหน้าจอจริง
            context = await pw.chromium.launch_persistent_context(
                user_data_dir="./chrome_profile",
                headless=True,
                user_agent=USER_AGENT,
                viewport={"width": 1366, "height": 768},
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.navigator.chrome = { runtime: {} };
                setInterval(() => {
                    document.querySelectorAll('button, a').forEach(el => {
                        if (el.disabled) el.disabled = false;
                        if (el.style.pointerEvents === 'none') el.style.pointerEvents = 'auto';
                    });
                }, 500);
            """)
            
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            # Step 1: Get access
            for _ in range(15):
                try:
                    btn = page.locator("text=Get access").first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        await asyncio.sleep(1.5)
                        break
                except:
                    pass
                await asyncio.sleep(0.5)

            # Step 2: Watch Ads
            try:
                watch_btn = page.locator("text=Watch Ads").first
                if await watch_btn.count() > 0 and await watch_btn.is_visible():
                    await watch_btn.click()
                    await asyncio.sleep(1.5)

                for fallback_text in ["Continue", "Watch Ads", "Try for free", "Get access"]:
                    confirm_btn = page.locator(f"text={fallback_text}").last
                    if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
                        await confirm_btn.click()
                        break
            except:
                pass

            # Step 3: Passive Wait & Skip Hunter
            for _ in range(120):
                for p in context.pages:
                    try:
                        p_url = p.url
                        if dest_domain in p_url and "error" not in p_url and "lv-verify" in p_url:
                            final_url = p_url
                            break
                    except:
                        pass
                
                if final_url:
                    break

                try:
                    for query in ["Open here", "Skip Ad", "Skip", "Close"]:
                        target_btn = page.locator(f"text={query}").first
                        if await target_btn.count() > 0 and await target_btn.is_visible():
                            await target_btn.click()
                            await asyncio.sleep(2.0)
                            break
                except:
                    pass

                await asyncio.sleep(1)

            if not final_url:
                for p in context.pages:
                    if dest_domain in p.url and "error" not in p_url:
                        final_url = p.url
                        break

            await context.close()
    except Exception as e:
        print(f"[LOG] ❌ Bypass error: {e}")

    return final_url

@bot.event
async def on_ready():
    print(f"[✓] Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("[✓] Cloud Bot is ready and listening...")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if "linkvertise.com" in message.content:
        url_match = re.search(r'(https?://[^\s]+)', message.content)
        if not url_match:
            return
        
        target_url = url_match.group(1)
        print(f"\n[LOG] 📥 Detected Linkvertise URL from {message.author.name}: {target_url}")

        try:
            await message.delete()
        except:
            pass

        status_msg = await message.channel.send(f"⏳ กำลังบายพาสลิงก์ให้คุณ `{message.author.name}` รอสักครู่...")

        final_url = await run_bypass(target_url)

        try:
            await status_msg.delete()
        except:
            pass

        if final_url:
            embed = discord.Embed(
                title="✅ crim condo — ready",
                color=0x57F287
            )
            embed.add_field(name="🖥️ PC Key", value=f"```\n{PC_KEY}\n```", inline=True)
            embed.add_field(name="📱 Mobile Key", value=f"```\n{MOBILE_KEY}\n```", inline=True)
            embed.set_footer(text=f"Requested by {message.author.name}")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="play", emoji="▶️", url=final_url))

            await message.channel.send(embed=embed, view=view)
        else:
            await message.channel.send(f"❌ บายพาสไม่สำเร็จหรือหมดเวลาสำหรับลิงก์ของ `{message.author.name}`", delete_after=10)

bot.run(BOT_TOKEN)
