import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from typing import List # 타입 힌트용 추가

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# --- 상수 정의 ---
DISCORD_TOKEN = "***REMOVED***" # 실제 봇 토큰
YOUR_TEST_SERVER_ID = 1356169830126059520 # 실제 테스트 서버 ID

# Poke2.py의 상수 일부 가져오기 (테스트용)
DEFAULT_PACK_ORDER = ["Shining", "Arceus", "Palkia", "Dialga", "Mew", "Pikachu", "Charizard", "Mewtwo"]
VALID_PACKS = DEFAULT_PACK_ORDER[:]
TARGET_BARRACKS_DEFAULT = 170

# --- 봇 설정 ---
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="/", intents=intents)

# --- 이벤트 핸들러 ---
@bot.event
async def on_ready():
    """봇 준비 완료 시 실행"""
    logging.info(f'✅ 로그인됨: {bot.user}')
    logging.info(f"테스트 봇 {bot.user} 준비 완료.")

    test_guild = discord.Object(id=YOUR_TEST_SERVER_ID)
    try:
        await bot.tree.sync(guild=test_guild)
        logging.info(f"🌳 테스트 서버({YOUR_TEST_SERVER_ID})에 슬래시 명령어 동기화 시도 완료.")
        await asyncio.sleep(2)
        logging.info("👀 명령어 등록 확인 시도 가능.")

    except discord.errors.Forbidden:
         logging.error(f"❌ 권한 오류: 테스트 서버({YOUR_TEST_SERVER_ID})에 명령어 동기화 권한이 없습니다.")
         logging.error("   - 봇이 'application.commands' 스코프로 초대되었는지 확인하세요.")
         logging.error("   - 서버 설정 > 연동(Integrations)에서 봇 권한을 확인하세요.")
    except Exception as e:
        logging.error(f"❌ 테스트 서버({YOUR_TEST_SERVER_ID}) 명령어 동기화 중 오류 발생: {e}", exc_info=True)

# --- 테스트 슬래시 명령어 ---

# @bot.tree.command(name="ping", description="간단한 응답 테스트")
# @app_commands.guilds(YOUR_TEST_SERVER_ID)
# async def ping_command(interaction: discord.Interaction):
#     """핑퐁 테스트 명령어"""
#     latency = bot.latency * 1000
#     await interaction.response.send_message(f"퐁! 응답 속도: {latency:.2f}ms", ephemeral=True)
#     logging.info(f"✅ /ping 명령어 처리 완료 (지연: {latency:.2f}ms)")

# # --- 추가 테스트 명령어 (Placeholder 구현) ---

# @bot.tree.command(name="내정보", description="내 프로필 정보 확인 (테스트)")
# @app_commands.guilds(YOUR_TEST_SERVER_ID)
# async def my_profile_info_placeholder(interaction: discord.Interaction):
#     """내정보 명령어 Placeholder"""
#     await interaction.response.send_message(f"✅ `/내정보` 명령어가 호출되었습니다! (사용자: {interaction.user.mention})", ephemeral=True)
#     logging.info(f"✅ /내정보 명령어 호출됨 (사용자: {interaction.user.name})")

# @bot.tree.command(name="목표배럭설정", description="내 목표 배럭 설정 (테스트)")
# @app_commands.describe(barracks="설정할 목표 배럭 수 (예: 160)")
# @app_commands.guilds(YOUR_TEST_SERVER_ID)
# async def set_target_barracks_placeholder(interaction: discord.Interaction, barracks: int):
#     """목표배럭설정 명령어 Placeholder"""
#     if barracks <= 0 or barracks > 500:
#         await interaction.response.send_message(f"값이 유효하지 않습니다 (1~500).", ephemeral=True)
#         return
#     await interaction.response.send_message(f"✅ `/목표배럭설정` 명령어가 호출되었습니다! (사용자: {interaction.user.mention}, 설정값: {barracks})", ephemeral=True)
#     logging.info(f"✅ /목표배럭설정 명령어 호출됨 (사용자: {interaction.user.name}, 값: {barracks})")

# /팩선호도 자동완성 Placeholder
async def pack_autocomplete_placeholder(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    choices = [pack for pack in VALID_PACKS if current.lower() in pack.lower()]
    # 이미 선택된 팩은 자동완성에서 제외하는 로직 (선택 사항)
    # selected_packs = []
    # if interaction.data and 'options' in interaction.data:
    #     for option in interaction.data['options']:
    #         if option['type'] == 3 and option['name'].startswith('pack') and 'value' in option: # 3 is STRING type
    #              selected_packs.append(option['value'])
    # choices = [choice for choice in choices if choice not in selected_packs]

    return [app_commands.Choice(name=choice, value=choice) for choice in choices[:25]]

@bot.tree.command(name="팩선호도", description="선호하는 팩 순서 설정 (최대 4개)")
@app_commands.describe(
    pack1="1순위 선호 팩",
    pack2="2순위 선호 팩 (선택)",
    pack3="3순위 선호 팩 (선택)",
    pack4="4순위 선호 팩 (선택)"
)
@app_commands.autocomplete(pack1=pack_autocomplete_placeholder, pack2=pack_autocomplete_placeholder, pack3=pack_autocomplete_placeholder, pack4=pack_autocomplete_placeholder)
@app_commands.guilds(YOUR_TEST_SERVER_ID)
async def set_preferred_packs_placeholder(
    interaction: discord.Interaction,
    pack1: str,
    pack2: str = None,
    pack3: str = None,
    pack4: str = None
):
    """팩선호도 명령어 Placeholder"""
    preferred_packs = [p for p in [pack1, pack2, pack3, pack4] if p is not None]

    # 간단한 유효성 검사 (예: 중복 확인 - 필요시 추가)
    if not preferred_packs: # pack1은 필수이므로 이 경우는 사실상 없음
        await interaction.response.send_message("적어도 1개의 팩을 선택해야 합니다.", ephemeral=True)
        return

    # 선택된 팩들이 유효한지 확인 (VALID_PACKS에 있는지)
    invalid_packs = [p for p in preferred_packs if p not in VALID_PACKS]
    if invalid_packs:
        await interaction.response.send_message(f"유효하지 않은 팩 이름이 포함되어 있습니다: {', '.join(invalid_packs)}", ephemeral=True)
        return

    # 중복 확인
    if len(preferred_packs) != len(set(preferred_packs)):
         await interaction.response.send_message(f"중복된 팩 이름이 있습니다. 각 팩은 한 번만 선택해주세요.", ephemeral=True)
         return


    preference_text = ", ".join([f"{i+1}: {pack}" for i, pack in enumerate(preferred_packs)])
    await interaction.response.send_message(f"✅ `/팩선호도` 명령어가 호출되었습니다! (사용자: {interaction.user.mention})\n설정된 선호도: {preference_text}", ephemeral=True)
    logging.info(f"✅ /팩선호도 명령어 호출됨 (사용자: {interaction.user.name}, 값: {preferred_packs})")

# --- 봇 실행 ---
if __name__ == "__main__":
    try:
        logging.info("🔌 테스트 봇 시작 중...")
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        logging.critical("❌ 봇 토큰이 잘못되었습니다. DISCORD_TOKEN 값을 확인하세요.")
    except Exception as e:
        logging.critical(f"봇 실행 중 치명적인 오류 발생: {e}", exc_info=True)
    finally:
        logging.info("봇 종료.")