import nextcord
from nextcord.ext import commands
import config
OWNERS = config.OWNERS
intents = nextcord.Intents.all()
bot = commands.Bot(help_command=None, intents=intents)
import json
from nextcord.ui import TextInput, Modal, View
import requests
import os
import datetime
from myserver import server_on

# --- Helper Functions for JSON I/O ---
def load_json(filename):
    """Loads data from a JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} # Return empty dict if file not found or is invalid

def save_json(filename, data):
    """Saves data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class topupModal(nextcord.ui.Modal):

  def __init__(self):
    super().__init__(title='🧧 เติมเงินผ่านซองอั่งเปา', timeout=None, custom_id='topup-modal')
    self.link = TextInput(
        label='ลิงค์ซองอั่งเปา (TrueMoney Gift)',
        placeholder='https://gift.truemoney.com/campaign/?v=...',
        style=nextcord.TextInputStyle.short,
        required=True)
    self.add_item(self.link)

  async def callback(self, interaction: nextcord.Interaction):
    ########################################################################################
    try:
        link = str(self.link.value).replace(' ', '')
        
        data = {
            'phone': config.TRUEMONEY_PHONE,
            'gift' : link
        }

        res = requests.post("https://api.mystrix2.me/truemoney", json=data)
        response_data = res.json()

        if res.status_code == 200 and 'data' in response_data:
            amount = float(response_data['data']['voucher']['amount_baht'])
            ########################################################################################
            message = await interaction.response.send_message(embed=config.loading,ephemeral=True)


            user_data = load_json('database/users.json')
            user_id = str(interaction.user.id)
            print(float(amount))
            point = float(amount)
            if user_id in user_data:
                print("เข้าสู่ระบบสำเร็จ")
                new_point = float(user_data[user_id]['point']) + float(point)
                user_data[user_id]['point'] = str(new_point)
                new_point = float(user_data[user_id]['all-point']) + float(point)
                user_data[user_id]['all-point'] = str(new_point)
            else:
                print("ไม่พบผู้ใช้ในระบบ")

                user_data[user_id] = {
                    "userId": int(user_id),
                    "point": str(0 + float(point)),
                    "all-point": str(0 + float(point)),
                    "historybuy": [],
                    "buyrole": [],
                    "buymarket": []
                }
                print("สร้างผู้ใช้ใหม่เรียบร้อยแล้ว")




            save_json('database/users.json', user_data)
            embed = nextcord.Embed(title="✅ เติมเงินสำเร็จ!",
                                description=f"ยอดเงินของคุณเพิ่มขึ้นจำนวน **{point}** บาทเรียบร้อยแล้ว", color=nextcord.Color.green())
            await message.edit(content=None, embed=embed)
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)

        else:
            error_message = "เกิดข้อผิดพลาด ไม่สามารถทำรายการได้"
            if 'redeemResponse' in response_data and 'status' in response_data['redeemResponse']:
                error_message = response_data['redeemResponse']['status']['message']
            
            await interaction.response.send_message(embed=nextcord.Embed(title=f"⚠️ เติมเงินไม่สำเร็จ", description=f"สาเหตุ: {error_message}", color=nextcord.Color.red()), ephemeral=True)
    except Exception as e:
          await interaction.response.send_message(embed=nextcord.Embed(title="🚫 เกิดข้อผิดพลาด", description="กรุณาตรวจสอบความถูกต้องของลิงค์ซองอั่งเปา และลองใหม่อีกครั้ง", color=nextcord.Color.red()), ephemeral=True)

class sellroleView(nextcord.ui.View):

  def __init__(self, message: nextcord.Message, value: str):
    super().__init__(timeout=None)
    self.message = message
    self.value = value

  @nextcord.ui.button(label='✅ ยืนยันการสั่งซื้อ',
                      custom_id='already',
                      style=nextcord.ButtonStyle.primary,
                      row=1)
  async def already(self, button: nextcord.Button,
                    interaction: nextcord.Interaction):
    roleJSON = load_json('./database/roles.json')
    userJSON = load_json('./database/users.json')
    if (str(interaction.user.id) not in userJSON):
        embed = nextcord.Embed(description='คุณยังไม่มีบัญชีกับเรา 🏦 กรุณาเติมเงินเพื่อเริ่มต้นใช้งานครับ!',
                             color=nextcord.Color.red())
        await self.message.edit(embed=embed, view=None, content=None)
    else:
      if int(float(userJSON[str(interaction.user.id)]['point'])) >= roleJSON[self.value]['price']:
        userJSON[str(interaction.user.id)]['point'] = str(float(userJSON[str(interaction.user.id)]['point']) - roleJSON[self.value]['price'])
        userJSON[str(interaction.user.id)]['buyrole'].append({
            "role": {
                "roleId": self.value,
                "time": str(datetime.datetime.now())
            }
        })
        save_json('./database/users.json', userJSON)
        if ('package' in self.value):
          for roleId in roleJSON[self.value]['roleIds']:
            try:
              await interaction.user.add_roles(
                  nextcord.utils.get(interaction.user.guild.roles, id=roleId))
              await interaction.user.add_roles(role)
            except:
              pass
          embed = nextcord.Embed(
              description=f'💲﹒ซื้อแพ็คเกจยศ "{roleJSON[self.value]["name"]}" สำเร็จ!',
              color=nextcord.Color.green())
          await self.message.edit(embed=embed, view=None, content=None)
        else:
            transactions = userJSON[str(interaction.user.id)]["point"]
            embed = nextcord.Embed(title="🎉 การสั่งซื้อสำเร็จ!",
                                                        description=(
                                                            f"```👤 ลูกค้า: {interaction.user.name}\n"
                                                            f"🛒 สินค้า: {roleJSON[self.value]['name']}\n"
                                                            f"✅ สถานะ: สำเร็จ\n"
                                                            f"💴 เงินลดลง : {roleJSON[self.value]['price']}\n"
                                                            f"💸 เงินคงเหลือ : {transactions}\n"
                                                            "```"
                                                        ),
                                                        color=nextcord.Color.green()
                                                    )

            if interaction.user.avatar:
                                                embed.set_thumbnail(url=interaction.user.avatar.url)

            role = nextcord.utils.get(interaction.user.guild.roles,
                                        id=roleJSON[self.value]['roleId'])
            await interaction.user.add_roles(role)
            embed.add_field(name="⭐ ข้อควรจำ", value="✅ กรุณาเก็บข้อความนี้ไว้เป็นหลักฐาน สำหรับการช่วยเหลือในอนาคต")
            await self.message.edit(embed=embed, view=None, content=None)
            await interaction.user.send(embed=embed)
      else:
        embed = nextcord.Embed(
            description=f'⚠️ โอ๊ะ! ยอดเงินของคุณไม่เพียงพอ ขาดอีก **{roleJSON[str(self.value)]["price"] - float(userJSON[str(interaction.user.id)]["point"])}** บาท',color=nextcord.Color.red())
        await self.message.edit(embed=embed, view=None, content=None)

  @nextcord.ui.button(label='❌ ยกเลิก',
                      custom_id='cancel',
                      style=nextcord.ButtonStyle.red,
                      row=1)
  async def cancel(self, button: nextcord.Button,
                   interaction: nextcord.Interaction):
    return await self.message.edit(content='ยกเลิกการการสำเร็จแล้ว',embed=None,view=None)
    
class sellroleselectmain(nextcord.ui.Select):
  def __init__(self):
    options = []
    roleJSON = load_json('./database/roles.json')
    for role in roleJSON:
      options.append(
          nextcord.SelectOption(label=roleJSON[role]['name'],
                                description=roleJSON[role]['description'],
                                value=role,
                                emoji=roleJSON[role]['emoji']))
    super().__init__(custom_id='select-role',
                     placeholder='[ 🗽 ยศและบทบาท ]',
                     min_values=1,
                     max_values=1,
                     options=options,
                     row=2)

  async def callback(self, interaction: nextcord.Interaction):
    message = await interaction.response.send_message(
        content='[SELECT] กำลังตรวจสอบ', ephemeral=True)
    selected = self.values[0]
    if ('package' in selected):
      roleJSON = load_json('./database/roles.json')
      embed = nextcord.Embed()
      embed.description = f'''
E {roleJSON[selected]['name']}**
''' # This seems incomplete, you might want to review this message.
      await message.edit(content=None,
                         embed=embed,
                         view=sellroleView(message=message, value=selected))
    else:
      
      roleJSON = load_json('./database/roles.json')
      embed=nextcord.Embed(title=roleJSON[selected]['title'], description=f"```{roleJSON[selected]['embeddes']}```" , color=nextcord.Color.green())
      if 'image' in roleJSON[selected] and roleJSON[selected]['image']:
          embed.set_image(url=roleJSON[selected]['image'])
      await message.edit(content="🪙 รายละเอียดสินค้า",
                         embed=embed,
                         view=sellroleView(message=message, value=selected))


class buyrole(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellroleselectmain())

        
class menu(nextcord.ui.Select):
    def __init__(self):

        options = [
            nextcord.SelectOption(label="ซื้อยศ / BUY ROLE", description="", emoji="🟠"),
            nextcord.SelectOption(label="ซื้อสินค้าอื่นๆ", description="สินค้าพิเศษและสคริปต์ต่างๆ", emoji="🟢"),
            nextcord.SelectOption(label="Clear Selection", description="", emoji="⭐"),
        ]

        super().__init__(custom_id='menu',
                        placeholder='[ ❤️‍🔥 ยินดีต้อนรับสู่ Hope Shop ]',
                        min_values=1,
                        max_values=1,
                        options=options,
                        row=1)

    async def callback(self, interaction: nextcord.Interaction):
        selected_values = self.values
        if "ซื้อยศ / BUY ROLE" in selected_values:
             await interaction.response.send_message(view=buyrole(), ephemeral=True)
        elif "ซื้อสินค้าอื่นๆ"  in selected_values:
             await interaction.response.send_message(view=buybot() , ephemeral=True)
        else:
             pass


class buybot(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(sellmarketsellprogram())
class sellmarketsellprogram(nextcord.ui.Select):
  def __init__(self):
    options = []
    IDJSON = load_json('./database/market.json')
    for role in IDJSON:
      options.append(
          nextcord.SelectOption(label=IDJSON[role]['name'],
                                description=IDJSON[role]['description'],
                                value=role,
                                emoji=IDJSON[role]['emoji']))
    super().__init__(custom_id='sellmarketui',
                     placeholder='[ 🛒 สินค้าสคลิป ]',
                     min_values=1,
                     max_values=1,
                     options=options,
                     row=3)

  async def callback(self, interaction: nextcord.Interaction):
    message = await interaction.response.send_message(
        content='[SELECT] กำลังตรวจสอบ', ephemeral=True)
    selected = self.values[0]
    if ('package' in selected):
      IDJSON = load_json('./database/market.json')
      embed = nextcord.Embed()
      embed.description = f'''
E {IDJSON[selected]['name']}**
''' # This seems incomplete, you might want to review this message.
      await message.edit(content=None,
                         embed=embed,
                         view=sellmarket(message=message, value=selected))
    else:
      
      IDJSON = load_json('./database/market.json')
      embed=nextcord.Embed(title=IDJSON[selected]['title'], description=f"```{IDJSON[selected]['embeddes']}```" , color=nextcord.Color.green())
      if 'image' in IDJSON[selected] and IDJSON[selected]['image']:
          embed.set_image(url=IDJSON[selected]['image'])
      await message.edit(content="🪙 รายละเอียดสินค้า",
                         embed=embed,
                         view=sellmarket(message=message, value=selected))  
      
class sellmarket(nextcord.ui.View):
  def __init__(self, message: nextcord.Message, value: str):
    super().__init__(timeout=None)
    self.message = message
    self.value = value

  @nextcord.ui.button(label='✅ ยืนยันการสั่งซื้อ',
                      custom_id='already',
                      style=nextcord.ButtonStyle.primary,
                      row=3)
  async def already(self, button: nextcord.Button,
                    interaction: nextcord.Interaction):
    IDJSON = load_json('./database/market.json')
    userJSON = load_json('./database/users.json')
    if (str(interaction.user.id) not in userJSON):
        embed = nextcord.Embed(description='คุณยังไม่มีบัญชีกับเรา 🏦 กรุณาเติมเงินเพื่อเริ่มต้นใช้งานครับ!',
                             color=nextcord.Color.red())
        await self.message.edit(embed=embed, view=None, content=None)
    else:
      if int(float(userJSON[str(interaction.user.id)]['point'])) >= IDJSON[self.value]['price']:
        userJSON[str(interaction.user.id)]['point'] = str(float(userJSON[str(interaction.user.id)]['point']) - IDJSON[self.value]['price'])
        userJSON[str(interaction.user.id)]['buymarket'].append({
            "market": {
                "market": IDJSON[self.value]['name'],
                "time": str(datetime.datetime.now()),
                "market" : IDJSON[self.value]['code']
            }
        })
        save_json('./database/users.json', userJSON)
        if ('package' in self.value):
          for roleId in IDJSON[self.value]['roleIds']:
            try:
              await interaction.user.add_roles(
                  nextcord.utils.get(interaction.user.guild.roles, id=roleId))
              await interaction.user.add_roles(role)
              role = nextcord.utils.get(interaction.user.guild.roles,
                                        id=config.cusrole)
            except:
              pass
          channelLog = bot.get_channel(config.LOG_CHANNEL_ID)
          
          transactions = userJSON[str(interaction.user.id)]["point"]
          if (channelLog):
            embed = nextcord.Embed(
                                                        title="📲 รายละเอียดการสั่งซื้อสินค้า",
                                                        description=(
                                                            f"```👤 คุณ {interaction.user.name}\n"
                                                            f"🛒 ซื้อสินค้า: {IDJSON[self.value]['name']}\n"
                                                            f"✅ สถานะการสั่งซื้อ : สั่งซื้อสำเร็จ\n"
                                                            f"💴 เงินลดลง : {IDJSON[self.value]['price']}\n"
                                                            f"💸 เงินคงเหลือ : {transactions}\n"
                                                            "```"
                                                        ),
                                                        color=nextcord.Color.green()
                                                    )

            await channelLog.send(embed=embed)
          embed = nextcord.Embed(
              description=
              f'💲﹒ซื้อยศสำเร็จ ได้รับ <@&{IDJSON[self.value]["name"]}>',
              color=nextcord.Color.green())
          await self.message.edit(embed=embed, view=None, content=None)
        else:
            channelLog = bot.get_channel(config.LOG_CHANNEL_ID)
            
            transactions = userJSON[str(interaction.user.id)]["point"]
            log_embed = nextcord.Embed(
                title="📲 รายละเอียดการสั่งซื้อสินค้า",
                description=(
                    f"```👤 คุณ {interaction.user.name}\n"
                    f"🛒 ซื้อสินค้า: {IDJSON[self.value]['name']}\n"
                    f"✅ สถานะการสั่งซื้อ : สั่งซื้อสำเร็จ\n"
                    f"💴 เงินลดลง : {IDJSON[self.value]['price']}\n"
                    f"💸 เงินคงเหลือ : {transactions}\n"
                    "```"
                ),
                color=nextcord.Color.green()
            )
            if interaction.user.avatar:
                log_embed.set_thumbnail(url=interaction.user.avatar.url)
            if channelLog:
                await channelLog.send(embed=log_embed)

            user_embed = log_embed.copy() # Create a copy for the user
            user_embed.add_field(name="⭐ ข้อควรจำ", value="✅ กรุณาเก็บข้อความนี้ไว้เป็นหลักฐาน สำหรับการช่วยเหลือในอนาคต",inline=False)
            user_embed.add_field(name="🔗 ลิงค์สินค้าของคุณ", value=f"กดเพื่อรับสินค้า: [คลิกที่นี่]({IDJSON[self.value]['code']})",inline=False)
            await self.message.edit(embed=user_embed, view=None, content=None)
            await interaction.user.send(embed=user_embed)
      else:
        embed = nextcord.Embed(
            description=f'⚠️ โอ๊ะ! ยอดเงินของคุณไม่เพียงพอ ขาดอีก **{IDJSON[str(self.value)]["price"] - float(userJSON[str(interaction.user.id)]["point"])}** บาท',color=nextcord.Color.red())
        await self.message.edit(embed=embed, view=None, content=None)

  @nextcord.ui.button(label='❌ ยกเลิก',
                      custom_id='cancel',
                      style=nextcord.ButtonStyle.red,
                      row=3)
  async def cancel(self, button: nextcord.Button,
                   interaction: nextcord.Interaction):
    return await self.message.edit(content='ยกเลิกการการสำเร็จแล้ว',embed=None,view=None)


@bot.event
async def on_ready():
    print(f'BOT NAME : {bot.user}')
    bot.add_view(mainui())



class mainui(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(menu())

    @nextcord.ui.button(label='เติมเงิน',
                        emoji="🧧",
                        custom_id='t1',
                        style=nextcord.ButtonStyle.blurple,
                        row=2)
    async def t1(self, button: nextcord.Button,
                        interaction: nextcord.Interaction):
            await interaction.response.send_modal(topupModal())
    @nextcord.ui.button(label='ยอดเงิน',
                        emoji="💰",
                        custom_id='t2',
                        style=nextcord.ButtonStyle.blurple,
                        row=2)
    async def t2(self, button: nextcord.Button,
                        interaction: nextcord.Interaction):
        userJSON = load_json('./database/users.json')
        if (str(interaction.user.id) not in userJSON):
            embed = nextcord.Embed(description='คุณยังไม่มีบัญชีกับเรา 🏦\nกรุณาเติมเงินเพื่อเริ่มต้นใช้งานครับ!',
                                color=nextcord.Color.red())
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)
        else:
            embed = nextcord.Embed(
                description=
                f'ยอดเงินคงเหลือของคุณคือ:\n\n# 💳 **{userJSON[str(interaction.user.id)]["point"]}** บาท',
                color=nextcord.Color.green())
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    @nextcord.ui.button(label='บันทึกยศ',
                        emoji="💌",
                        custom_id='t3',
                        style=nextcord.ButtonStyle.green,
                        row=2)
    async def t3(self, button: nextcord.Button,
                        interaction: nextcord.Interaction):
                        user = interaction.user
                        role_data = [role.name for role in user.roles if "@everyone" not in role.name]
                        file_path = f"saveroles/role_{user.name}.json"

                        try:
                            with open(file_path, "w", encoding='utf-8') as f:
                                json.dump(role_data, f)
                        except Exception as e:
                            print(f"Error saving roles: {e}")
                            await interaction.response.send_message("An error occurred while saving roles.", ephemeral=True)
                            return

                        embed = nextcord.Embed(title="บันทึกยศที่เซฟ", color=0xdddddd)

                        if interaction.user.avatar:
                                embed.set_thumbnail(url=interaction.user.avatar.url)
                        else :
                                embed.set_thumbnail(url=None)
                        if user.avatar:
                            embed.set_author(name="ระบบเชฟยศอัติโนมัติ", url="", icon_url=user.avatar.url)
                        formatted_roles = "\n".join(role_data)
                        embed.add_field(name="ยศที่เชฟเสร็จสิ้น", value=f"```\n{formatted_roles}```", inline=False)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        CH = 123456789012345678 # <-- TODO: Replace with your actual log channel ID
                        channel = bot.get_channel(CH)
                        if channel:
                            log_embed = nextcord.Embed(title="บันทึกเรียบร้อย 📝", color=0xdddddd)
                            if interaction.user.avatar:
                                    log_embed.set_thumbnail(url=interaction.user.avatar.url)
                            log_embed.add_field(name="ยศที่เซฟ", value=f"```{formatted_roles}```", inline=False)
                            log_embed.add_field(name="ผู้เชฟ", value=f"> {interaction.user.mention}", inline=False)
                            await channel.send(embed=log_embed)
    @nextcord.ui.button(label='กู้คืนยศ',
                            emoji="🟢",
                            custom_id='t4',
                            style=nextcord.ButtonStyle.green,
                            row=2)
    async def t4(self, button: nextcord.Button,
                            interaction: nextcord.Interaction):
                    user = interaction.user
                    file_path = f"saveroles/role_{user.name}.json"
                    try:
                        with open(file_path, "r", encoding='utf-8') as f:
                            role_data = json.load(f)
                            for role_name in role_data:
                                roles = nextcord.utils.get(interaction.guild.roles, name=role_name)
                                await user.add_roles(roles)
                        await interaction.response.send_message("```diff\n+ คืนยศให้คุณเรียบร้อยแล้ว\n```", ephemeral=True)
                    except FileNotFoundError:
                        await interaction.response.send_message("```diff\n- ขออภัยไม่มีข้อมูลของคุณ```", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"```diff\n- เกิดข้อผิดพลาด: {e}\n```", ephemeral=True)

@bot.slash_command( description="ติดตั้งได้หมด")
async def setup(interaction: nextcord.Interaction):


            embed=nextcord.Embed(title=f"⭐ Hope Shop ยินดีต้อนรับ ⭐")
    

            des = '''```ansi
[2;41m[2;37m🧧﹒ร้านค้าอัตโนมัติ 24 ชั่วโมง 💚
[0m[2;41m[0m
[2;45m[2;37m・ 💳﹒เติมเงินง่ายๆ ผ่านซองอั่งเปา
・ ✨﹒ซื้อสินค้าและรับยศทันที ไม่ต้องรอแอดมิน[0m[2;45m[0m
[2;47m[2;30m・ 💲﹒สินค้าคุณภาพ ราคาคุ้มค่า
・ �﹒เติมเงินครั้งแรกเพื่อเปิดใช้งานบัญชี[0m[2;47m[0m

```'''
            embed.add_field(name="", value=des, inline=False)
            des = '''```diff
🎐 : เลือกซื้อสินค้าและยศสุดพิเศษได้ง่ายๆ ผ่านบอท
🎁 : สินค้าใหม่ๆ อัปเดตตลอด รับประกันความคุ้มค่า ไม่ผิดหวังแน่นอน!
```'''
            embed.add_field(name="`🛍️` สินค้าและบริการของเรา `🛍️`", value=des, inline=True)
            des = '''```diff
+ กดปุ่ม [เติมเงิน] แล้วใส่ลิงค์ซองอั่งเปา
+ ระบบจะทำการอัปเดตยอดเงินให้อัตโนมัติ
+ จากนั้นเลือกซื้อสินค้าที่คุณต้องการได้เลย!```'''
            embed.add_field(name="`💸` วิธีการใช้งาน `💸`", value=des, inline=True)
            des = '''```diff
- ❗ : บอทมีปัญหาโปรดแจ้งแอดมินโดยทันที
> เติมเงินด้วยระบบอั่งเปา 🧧
> ﹒เปิดบัญชีอัตโนมัติ 💸```'''
            embed.add_field(name="`❗` ข้อความจากแอดมิน `❗`", value=des, inline=False)
            
            
            
            embed.set_image(url="https://media.discordapp.net/attachments/1201027737004019782/1244129061194829897/unknown_3.jpg?ex=69286d3a&is=69271bba&hm=c1b05c80d6e3d1270fcf4d9ce697e18f72749b98e92b1b9d4704d3f856f8560b&=&format=webp&width=1730&height=864")
            rent = await interaction.channel.send(embed=embed, view=mainui())

server_on()

if __name__ == "__main__":
    bot.run(config.BOT_TOKEN)