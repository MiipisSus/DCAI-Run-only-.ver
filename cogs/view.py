import discord
from discord.ext import commands
from discord.interactions import Interaction
from func.server_config import *
from cogs.embed import Styled_Embed
from discord.ui import *
import traceback

class BotChatButton(discord.ui.View):
    def __init__(self, parent, src_bot_id, dst_bot_id, channel_id, send_text = None, ooc = None):
        super().__init__(timeout = None)
        self.parent = parent
        self.src_bot_id = src_bot_id
        self.dst_bot_id = dst_bot_id
        self.channel_id = channel_id
        self.send_text = send_text
        self.ooc = ooc if ooc else ""
    
    @discord.ui.button(custom_id="oocButton", label="", style=discord.ButtonStyle.secondary, emoji="💡")
    async def ooc_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        original_msg = await interaction.channel.fetch_message(interaction.message.id)
        try:
            await interaction.response.send_modal(TextInput_Modal(self.parent, "ooc", None, None, None, CHAT_TYPE.BOT, src_bot_id = self.src_bot_id,
                                                                dst_bot_id = self.dst_bot_id, src_chara_name = None, dst_chara_name = None,
                                                                channel_id = self.channel_id))
        except Exception as e:
            print(traceback.print_exc())
    
    @discord.ui.button(custom_id="refreshButton", label="", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        original_msg = await interaction.channel.fetch_message(interaction.message.id)
        embed = Styled_Embed(self.parent.bot, EMBED_TYPE.REFRESH_LAST_MESSAGE)
        await original_msg.edit(embed = embed, view = None)
        await interaction.response.defer()
        try:
            response, response_translated, flag = await self.parent.Chat.refresh_chat(self.dst_bot_id, self.channel_id, CHAT_TYPE.BOT)
            if response == None:
                response = ""
            if flag:
                embed.init_embed_type(EMBED_TYPE.NSFW_FILTER)
            self.send_text = response
            await self.parent.Chat.update_database(BOT_CHAT.__name__, {BOT_CHAT.LAST_MESSAGE_TEXT: f"{self.ooc}\n{response}"},
                                                   {BOT_CHAT.BOT_ID: self.dst_bot_id, BOT_CHAT.CHANNEL_ID: self.channel_id})
            await original_msg.edit(f"{response_translated}", embed = embed if flag else None, view = self)
        except Exception as e:
            print(traceback.print_exc())
    
    @discord.ui.button(custom_id="continueButton", label="", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def continue_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await self.parent.Chat.update_database(BOT_CHAT.__name__, {BOT_CHAT.STATE: False},
                                                   {BOT_CHAT.BOT_ID: self.dst_bot_id, BOT_CHAT.CHANNEL_ID: self.channel_id})
            
            src_chara_name = self.parent.settings[PYCAI_SETTING.__name__][PYCAI_SETTING.CHAR_NAME]
            
            original_msg = await interaction.channel.fetch_message(interaction.message.id)
            if not self.send_text:
                self.send_text = original_msg.content
            await original_msg.edit(view=None)
            await interaction.response.defer()
            await self.parent.bot.send_bot_chat(self.src_bot_id, self.dst_bot_id, 
                                                f"{self.ooc}\n{src_chara_name}: {self.send_text}", self.channel_id)
        except Exception as e:
            print(e)
            
        
class ChatButton(discord.ui.View):
    def __init__(self, parent, id, chat_type, embed_res = None, **kwargs):
        super().__init__(timeout = None)
        self.parent = parent
        self.id = id
        self.chat_type = chat_type
        self.embed_res = embed_res
        self.kwargs = kwargs
    
    @discord.ui.button(custom_id="removeButton", label="", style=discord.ButtonStyle.secondary, emoji="❌")
    async def remove_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.parent.Chat.clean_chat_history(2, self.id, self.chat_type)
        await self.parent.clean_last_msg_id(interaction.channel, interaction.user, self.chat_type)
        embed = Styled_Embed(self.parent.bot, EMBED_TYPE.REMOVE_LAST_MESSAGE)
        original_msg = await interaction.channel.fetch_message(interaction.message.id)
        await original_msg.edit(content="", embed=embed, view=None)
        
    @discord.ui.button(custom_id="refreshButton", label="", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        original_msg = await interaction.channel.fetch_message(interaction.message.id)
        embed = Styled_Embed(self.parent.bot, EMBED_TYPE.REFRESH_LAST_MESSAGE)
        await original_msg.edit(embed = embed, view = None)
        await interaction.response.defer()
        try:
            response, flag = await self.parent.Chat.refresh_chat(self.id, chat_type= self.chat_type)
            if response == None:
                response = ""
            if self.embed_res:
                if flag:
                    embed_2 = Styled_Embed(EMBED_TYPE.NSFW_FILTER)
                if self.embed_res == EMBED_TYPE.NAME_COMPLETE:
                    embed.init_embed_type(self.embed_res, new = self.kwargs["new"], old = self.kwargs["old"], res = response)
                else:
                    embed.init_embed_type(self.embed_res, res = response)
                await original_msg.edit(embeds = [embed, embed_2] if flag else [embed], view=self)
            else:
                if flag:
                    embed.init_embed_type(EMBED_TYPE.NSFW_FILTER)
                await original_msg.edit(f"{response}", embed = embed if flag else None, view = self)
            
        except Exception as e:
            print(traceback.print_exc())
            
    @discord.ui.button(custom_id="continueButton", label="", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def continue_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            user, channel, guild = interaction.user, interaction.channel, interaction.guild
            if self.chat_type == CHAT_TYPE.GROUP:
                async with channel.typing():
                    await self.parent.check_last_msg_id(channel, user, self.chat_type)
                    response, flag = await self.parent.Chat.send_RP_reminder(guild, user, channel, "(Continue)", self.chat_type)
                    if response == None:
                        response = ""
                    if flag:
                        embed = Styled_Embed(self.parent.bot, EMBED_TYPE.NSFW_FILTER)
                    res = await interaction.followup.send(f"{response}", embed = embed if flag else None, view = ChatButton(self.parent, self.id, self.chat_type))
                    await self.parent.update_last_msg_id(channel, user, res.id, self.chat_type)
            else:
                await channel.trigger_typing()
                await self.parent.check_last_msg_id(channel, user, self.chat_type)
                response, flag = await self.parent.Chat.send_RP_reminder(guild, user, channel, "(Continue)", self.chat_type)
                if response == None:
                    response = ""
                if flag:
                    embed = Styled_Embed(self.parent.bot, EMBED_TYPE.NSFW_FILTER)
                res = await interaction.followup.send(f"{response}", embed = embed if flag else None, view = ChatButton(self.parent, self.id, self.chat_type))
                await self.parent.update_last_msg_id(channel, user, res.id, self.chat_type)
            
        except Exception as e:
            print(e)


class CommandList(discord.ui.Select):
    def __init__(self, parent, chat_type, admin = False):
        options = [
            discord.SelectOption(value="info", label="Bot資訊", description="取得Bot基本資訊與目前使用名稱", default=False),
            discord.SelectOption(value="name", label="修改暱稱", description="改變角色對自己的稱呼", default=False),
            discord.SelectOption(value="clean", label="清除歷史", description="刪除指定數量的聊天紀錄", default=False),
            discord.SelectOption(value="reset", label="重置聊天", description="重置角色聊天紀錄", default=False),
            discord.SelectOption(value="NSFW", label="NSFW", description="關閉NSFW過濾器", default=False),
            discord.SelectOption(value="RP", label="Role Play", description="開始與角色的故事扮演", default=False),
            discord.SelectOption(value="ooc", label="角色提示", description="提醒角色設定/故事走向/其他", default=False)
            ]
        if admin:
            options.extend([discord.SelectOption(value="status", label="變更狀態", description="更改角色上線狀態", default=False),
                            discord.SelectOption(value="reboot", label="重啟Bot", description="重新啟動Bot\n", default=False),
                            discord.SelectOption(value="admin", label="管理權限", description="指定其他使用者為管理員", default=False)])
        self.chat_type = chat_type
        self.parent = parent
        super().__init__(placeholder = "選擇欲執行的命令...", max_values = 1, min_values = 1,
                         options = options)
    
    async def callback(self, interaction: Interaction):
        user, channel, guild = interaction.user, interaction.channel, interaction.guild
        if self.values[0] == "RP":
            await interaction.response.send_modal(RPInput_Modal(self.parent, user, channel, guild, self.chat_type))
        if self.values[0] in ("name", "clean", "status", "ooc"):
            await interaction.response.send_modal(TextInput_Modal(self.parent, self.values[0], user, channel, guild, self.chat_type))
        elif self.values[0] == "info":
            await interaction.response.defer(ephemeral=True)
            user_name = await self.parent.cmd_info(interaction.user, interaction.channel, self.chat_type)
            embed = Styled_Embed(self.parent.bot, EMBED_TYPE.SHOW_INFO, user_name = user_name)
            await interaction.followup.send(embed = embed, ephemeral=True)
        elif self.values[0] == "reset":
            await interaction.response.defer()
            id = channel.id if self.chat_type == CHAT_TYPE.GROUP else user.id
            await self.parent.cmd_reset(id, self.chat_type)
            await self.parent.clean_last_msg_id(channel, user, self.chat_type)
            embed = Styled_Embed(self.parent.bot, EMBED_TYPE.RESET_COMPLETE)
            await interaction.followup.send(embed = embed)
        elif self.values[0] == "NSFW":
            await interaction.response.defer()
            embed = Styled_Embed(self.parent.bot, EMBED_TYPE.NSFW_PROCESSING)
            id = channel.id if self.chat_type == CHAT_TYPE.GROUP else user.id
            msg = await interaction.followup.send(embed = embed)
            await self.parent.check_last_msg_id(channel, user, self.chat_type)
            res = await self.parent.cmd_NSFW(guild, user, channel, self.chat_type)
            await self.parent.update_last_msg_id(channel, user, msg.id, self.chat_type)
            embed.init_embed_type(EMBED_TYPE.NSFW_COMPLETE, res = res)
            await msg.edit(embed = embed, view = ChatButton(self.parent, id, self.chat_type, embed_res=EMBED_TYPE.NSFW_COMPLETE))
        elif self.values[0] == "admin":
            await interaction.response.send_message(view=UserSelectMenu(self.parent), ephemeral=True)

        
class CommandSelectMenu(discord.ui.View):
    def __init__(self, parent, chat_type, admin):
        super().__init__(timeout=None)
        self.parent = parent
        self.add_item(CommandList(parent, chat_type, admin))


class UserSelectMenu(discord.ui.View):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(timeout=None)
        
    @discord.ui.user_select(placeholder="請選擇欲指定的管理員...", min_values=1, max_values=1)
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        admin = await self.parent.check_admin(select.values[0].id)
        if not admin:
            await self.parent.Chat.insert_database(ADMIN.__name__, {ADMIN.USER_ID: select.values[0].id, ADMIN.PRIVILAGE: True})
        embed = Styled_Embed(self.parent.bot, EMBED_TYPE.ADMIN_COMPLETE, user = select.values[0].display_name)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ChannelSelectMenu(discord.ui.View):
    def __init__(self, parent, cmd_type):
        self.parent = parent
        self.cmd_type = cmd_type
        super().__init__(timeout=None)
    
    @discord.ui.channel_select(placeholder="請選擇欲指定的頻道...（僅能選擇一個）", min_values=1, max_values=1)
    async def callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        await self.parent.Chat.check_guild(interaction.guild)
        if self.cmd_type == "schedule":
            await self.parent.Chat.update_database(GUILD.__name__, {GUILD.TASK_CHANNEL_ID: select.values[0].id}, {GUILD.GUILD_ID: interaction.guild.id})
            await self.parent.bot.get_task_channels()
        else:
            await self.parent.Chat.update_database(GUILD.__name__, {GUILD.EVENT_CHANNEL_ID: select.values[0].id}, {GUILD.GUILD_ID: interaction.guild.id})
        embed = Styled_Embed(self.parent.bot, EMBED_TYPE.TASK_COMPLETE, channel = select.values[0].name)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        chat_id = await self.parent.Chat.search_database(GUILD.__name__, [GUILD.NOTIFY_CHAT_ID], {GUILD.GUILD_ID: interaction.guild.id})
        if not chat_id:
            chat_id = await self.parent.Chat.initial_new_chat(interaction.guild.id, CHAT_TYPE.NOTIFY)
            await self.parent.Chat.update_database(GUILD.__name__, {GUILD.NOTIFY_CHAT_ID: chat_id}, {GUILD.GUILD_ID: interaction.guild.id})
    
class TextInput_Modal(discord.ui.Modal):
    def __init__(self, parent, cmd_type, user = None, channel = None, guild = None, chat_type = None, **kwargs) -> None:
        self.parent = parent
        self.cmd_type = cmd_type
        self.user = user
        self.channel = channel
        self.guild = guild
        self.chat_type = chat_type
        self.kwargs = kwargs
        self.placeholder = {
            "name": "請輸入新的稱呼...", 
            "clean": "請輸入欲刪除的聊天紀錄數量...(最多50則)",
            "status": "請輸入欲變更的狀態...",
            "ooc": "請輸入提示訊息..."}
        self.text_input = discord.ui.InputText(
            label = cmd_type,
            style = discord.InputTextStyle.short if cmd_type != "ooc" else discord.InputTextStyle.long,
            placeholder = self.placeholder[cmd_type],
        )
        super().__init__(self.text_input, title="")
        
    async def callback(self, interaction: discord.Interaction):
        if self.cmd_type == "clean":
            try:
                await interaction.response.defer()
                user_input = int(self.children[0].value)
                if user_input > 50:
                    user_input = 50
                id = self.channel.id if self.chat_type == CHAT_TYPE.GROUP else self.user.id
                await self.parent.cmd_clean(user_input, id, self.chat_type)
                await self.parent.clean_last_msg_id(self.channel, self.user, self.chat_type)
                embed = Styled_Embed(self.parent.bot, EMBED_TYPE.CLEAN_COMPLETE, num = user_input)
                await interaction.followup.send(embed = embed)
            except Exception as e:
                print(e)
        elif self.cmd_type == "name":
            new_name = self.children[0].value
            try:
                await interaction.response.defer()
                id = self.channel.id if self.chat_type == CHAT_TYPE.GROUP else self.user.id
                embed = Styled_Embed(self.parent.bot, EMBED_TYPE.NAME_PROCESSING)
                msg = await interaction.followup.send(embed = embed)
                await self.parent.check_last_msg_id(self.channel, self.user, self.chat_type)
                res = await self.parent.cmd_name(self.user, self.channel, self.guild, new_name, self.chat_type)
                await self.parent.update_last_msg_id(self.channel, self.user, msg.id, self.chat_type)
                embed.init_embed_type(EMBED_TYPE.NAME_COMPLETE, old = self.user.name, new = new_name, res = res)
                await msg.edit(embed=embed, view = ChatButton(self.parent, id, self.chat_type, embed_res=EMBED_TYPE.NAME_COMPLETE))
            except Exception as e:
                print(e)
        elif self.cmd_type == "status":
            status = self.children[0].value
            try:
                await interaction.response.defer(ephemeral=True)
                embed = Styled_Embed(self.parent.bot, EMBED_TYPE.STATUS_COMPLETE, status = status)
                modify_configs(self.parent.path, BOT_SETTING.__name__, BOT_SETTING.STATUS, status)
                await self.parent.bot.change_presence(activity=discord.Game(name=status))
                await interaction.followup.send(embed = embed, ephemeral=True)
            except Exception as e:
                print(e)
        elif self.cmd_type == "ooc":
            text = self.children[0].value
            if self.chat_type == CHAT_TYPE.BOT:
                src_bot_id, dst_bot_id, src_chara_name , dst_chara_name, channel_id= self.kwargs['src_bot_id'], self.kwargs['dst_bot_id'],\
                                                        self.kwargs['src_chara_name'], self.kwargs['dst_chara_name'], self.kwargs['channel_id']
                text = await self.parent.Chat.translate_send(text, None, CHAT_TYPE.BOT)
                if 'start' in self.kwargs:
                    embed = Styled_Embed(self.parent.bot, EMBED_TYPE.BOT_CHAT_EMBED, bot_name = dst_chara_name, status = "on", topic = "on")
                    await interaction.response.send_message(embed=embed)
                    async with interaction.channel.typing():
                        src_text = f"(ooc: The character you will chat with is {dst_chara_name}\n\
                                    Please be careful not to actively use ooc, just follow my ooc instructions)\n\
                                    (ooc: {text}\nStory start!)"
                        dst_text = f"(ooc: The character you will chat with is {src_chara_name}\n\
                                    Please be careful not to actively use ooc, just follow my ooc instructions)\n\
                                    (ooc: {text}\nStory start!)"
                        res, res_translated, safety_flag = await self.parent.cmd_create_chat(src_text, src_bot_id, dst_bot_id, self.channel.id, dst_text)
                    if safety_flag:
                        embed = Styled_Embed(self.parent.bot, EMBED_TYPE.NSFW_FILTER)
                    view = BotChatButton(self.parent, src_bot_id, dst_bot_id, channel_id, res, ooc = dst_text)
                    await interaction.followup.send(res_translated, embed=embed if safety_flag else None, view=view)
                else:
                    await interaction.response.defer()
                    original_msg = await interaction.channel.fetch_message(interaction.message.id)
                    await original_msg.edit(view=None)
                    ooc_text = f"(ooc: {text})"
                    async with interaction.channel.typing():
                        res, res_translated, safety_flag = await self.parent.Chat.bot_chat_recv(dst_bot_id, channel_id, ooc_text, ooc_text)
                    await self.parent.Chat.update_database(BOT_CHAT.__name__, {BOT_CHAT.LAST_MESSAGE_TEXT: f"{ooc_text}\n{res}"},
                                                           {BOT_CHAT.BOT_ID: dst_bot_id, BOT_CHAT.CHANNEL_ID: channel_id})
                    if safety_flag:
                        embed = Styled_Embed(self.parent.bot, EMBED_TYPE.NSFW_FILTER)
                    view = BotChatButton(self.parent, src_bot_id, dst_bot_id, channel_id, res, ooc = ooc_text)
                    await interaction.followup.send(res_translated, embed=embed if safety_flag else None, view=view)
            
            else:
                await interaction.response.defer()
                embed = Styled_Embed(self.parent.bot, EMBED_TYPE.OOC_PROCESSING)
                msg = await interaction.followup.send(embed=embed)
                id = self.channel.id if self.chat_type == CHAT_TYPE.GROUP else self.user.id
                await self.parent.check_last_msg_id(self.channel, self.user, self.chat_type)
                res = await self.parent.cmd_ooc(text, self.guild, self.user, self.channel, self.chat_type)
                await self.parent.update_last_msg_id(self.channel, self.user, msg.id, self.chat_type)
                embed.init_embed_type(EMBED_TYPE.OOC_COMPLETE, res = res)
                await msg.edit(embed=embed, view = ChatButton(self.parent, id, self.chat_type, embed_res=EMBED_TYPE.OOC_COMPLETE))
        else:
            return
        
class RPInput_Modal(discord.ui.Modal):
    def __init__(self, parent, user = None, channel = None, guild = None, chat_type = CHAT_TYPE.GROUP, **kwargs) -> None:
        self.parent = parent
        self.user = user
        self.channel = channel
        self.guild = guild
        self.kwargs = kwargs
        self.chat_type = chat_type
        title = ("故事主題", "主要情節", "故事起始（可不填）", "故事目標（可不填）", "額外設定（可不填）")
        placeholder = ("請輸入你想扮演的故事主題...", "請輸入你想該故事的主要情節...", 
                       "請輸入故事開始的時間點或劇情...", "請輸入你想達成的目標...",
                       "請輸入該故事的額外設定...")
        self.topic_input = discord.ui.InputText(
            label = title[0],
            style = discord.InputTextStyle.short,
            placeholder = placeholder[0],
        )
        self.plot_input = discord.ui.InputText(
            label = title[1],
            style = discord.InputTextStyle.long,
            placeholder = placeholder[1],
        )
        self.start_input = discord.ui.InputText(
            label = title[2],
            style = discord.InputTextStyle.long,
            placeholder = placeholder[2],
            required = False
        )
        self.goal_input = discord.ui.InputText(
            label = title[3],
            style = discord.InputTextStyle.long,
            placeholder = placeholder[3],
            required = False
        )
        self.extra_input = discord.ui.InputText(
            label = title[4],
            style = discord.InputTextStyle.long,
            placeholder = placeholder[4],
            required = False
        )
        super().__init__(self.topic_input, self.plot_input, self.start_input, self.goal_input, self.extra_input, title = "")
        
    async def callback(self, interaction: discord.Interaction):
        text = f"Hey, I want to start a role play with the following settings: \n\
                    The topic about the story is: {self.children[0].value}\n\
                    The main plot about the story is: {self.children[1].value}\n"
        if self.children[2].value != "":
            text += f"The plot will start with: {self.children[2].value}\n"
        if self.children[3].value != "":
            text += f"The goal I want to arrived with the story is: {self.children[3].value}\n"
        if self.children[4].value != "":
            text += f"And PLEASE remember these role setting: {self.children[4].value}\n"
        text += "If you have any questions, please let me know, thank you!"
            
        if self.chat_type == CHAT_TYPE.BOT:
            src_bot_id, dst_bot_id, src_chara_name , dst_chara_name, channel_id = self.kwargs['src_bot_id'], self.kwargs['dst_bot_id'],\
                                                                self.kwargs['src_chara_name'], self.kwargs['dst_chara_name'],\
                                                                self.kwargs['channel_id']
            text = await self.parent.Chat.translate_send(text, None, CHAT_TYPE.BOT)
            embed = Styled_Embed(self.parent.bot, EMBED_TYPE.BOT_CHAT_EMBED, bot_name = dst_chara_name, status = "on", topic = "on")
            await interaction.response.send_message(embed=embed)
            async with interaction.channel.typing():
                src_text = f"(ooc: The character you will chat with is {dst_chara_name}\n\
                            Please be careful not to actively use ooc, just follow my ooc instructions)\n\
                            (ooc: {text}\nStory start!)"
                dst_text = f"(ooc: The character you will chat with is {src_chara_name}\n\
                            Please be careful not to actively use ooc, just follow my ooc instructions)\n\
                            (ooc: {text}\nStory start!)"
                res, res_translated, safety_flag = await self.parent.cmd_create_chat(src_text, src_bot_id, dst_bot_id, self.channel.id, dst_text)
            if safety_flag:
                embed = Styled_Embed(self.parent.bot, EMBED_TYPE.NSFW_FILTER)
            view = BotChatButton(self.parent, src_bot_id, dst_bot_id, channel_id, res, ooc = dst_text)
            await interaction.followup.send(res_translated, embed=embed if safety_flag else None, view=view)
            
        else:
            embed = Styled_Embed(self.parent.bot, EMBED_TYPE.RP_PROCESSING)
            await interaction.response.defer()
            msg = await interaction.followup.send(embed=embed)
            id = self.channel.id if self.chat_type == CHAT_TYPE.GROUP else self.user.id
            await self.parent.check_last_msg_id(self.channel, self.user, self.chat_type)
            res = await self.parent.cmd_ooc(text, self.guild, self.user, self.channel, self.chat_type)
            await self.parent.update_last_msg_id(self.channel, self.user, msg.id, self.chat_type)
            
            embed.init_embed_type(EMBED_TYPE.RP_COMPLETE, res = res)
            await msg.edit(embed=embed, view = ChatButton(self.parent, id, self.chat_type, EMBED_TYPE.RP_COMPLETE))
            return  
        
        
def setup(bot: commands.Bot):
    pass