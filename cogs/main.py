import discord
from discord.ext import commands
from discord.interactions import Interaction
from discord import option
from func.server_config import *
from func.send_chat import Chat
from func.msg_regex import remove_ooc
from cogs.embed import Styled_Embed
from cogs.view import *
from bot import DiscordBot
from discord.ui import *
import asyncio
import traceback

class Main(commands.Cog):
    def __init__(self, bot: commands.Bot):
        print(discord.__version__)
        self.bot: DiscordBot = bot
        self.execute_cmd = {}
        self.fix_button_flag = {}
        self.ooc_count = {}
        self.bot.loop.create_task(self.init_config())
    
    def cog_unload(self):
        super().cog_unload()
    
    #config initialize
    async def init_config(self):
        self.settings = self.bot.settings
        self.Chat: Chat = self.bot.Chat
        self.path = self.bot.path
        self.embed_color = self.settings[STYLE.__name__][STYLE.EMBED_COLOR]
        try:
            await self.Chat.update_database(CHANNEL.__name__, {CHANNEL.LAST_MESSAGE_ID: None}, None)
            await self.Chat.update_database(INDIVIDUALS.__name__, {INDIVIDUALS.LAST_MESSAGE_ID: None}, None)
        except:
            pass
        
    #func
    def check_flag(self, id):
        if id not in self.ooc_count:
            self.ooc_count[id] = 0
        if id not in self.fix_button_flag:
            self.fix_button_flag[id] = False
    
    async def check_last_msg_id(self, channel, user, chat_type):
        if chat_type == CHAT_TYPE.GROUP:
            last_message_id = await self.Chat.search_database(CHANNEL.__name__, 
                                                                [CHANNEL.LAST_MESSAGE_ID], 
                                                                {CHANNEL.CHANNEL_ID: channel.id})
        else:
            last_message_id = await self.Chat.search_database(INDIVIDUALS.__name__, 
                                                                [INDIVIDUALS.LAST_MESSAGE_ID], 
                                                                {INDIVIDUALS.USER_ID: user.id})
        if last_message_id:
            last_message = await channel.fetch_message(last_message_id)
            if any(isinstance(child, discord.components.Button) for row in last_message.components for child in row.children):
                await last_message.edit(view = None)
                self.fix_button_flag[channel.id] = False
            else:
                self.fix_button_flag[channel.id] = True
                
    async def update_last_msg_id(self, channel, user, msg_id, chat_type):
        if chat_type == CHAT_TYPE.GROUP:
            await self.Chat.update_database(CHANNEL.__name__, {CHANNEL.LAST_MESSAGE_ID: msg_id}, {CHANNEL.CHANNEL_ID: channel.id})
        else:
            await self.Chat.update_database(INDIVIDUALS.__name__, {INDIVIDUALS.LAST_MESSAGE_ID: msg_id}, {INDIVIDUALS.USER_ID: user.id})
            
    async def clean_last_msg_id(self, channel, user, chat_type):
        if chat_type == CHAT_TYPE.GROUP:
            last_message_id = await self.Chat.search_database(CHANNEL.__name__, 
                                                                [CHANNEL.LAST_MESSAGE_ID], 
                                                                {CHANNEL.CHANNEL_ID: channel.id})
        else:
            last_message_id = await self.Chat.search_database(INDIVIDUALS.__name__, 
                                                                [INDIVIDUALS.LAST_MESSAGE_ID], 
                                                                {INDIVIDUALS.USER_ID: user.id})
        if last_message_id:
            last_message = await channel.fetch_message(last_message_id)
            await last_message.edit(view = None)
        
        await self.update_last_msg_id(channel, user, None, chat_type)

    async def check_admin(self, user_id):
        admin = await self.Chat.search_database(ADMIN.__name__, [ADMIN.PRIVILAGE], {ADMIN.USER_ID: user_id})
        return admin
    
    async def cmd_name(self, author, channel, guild, new, chat_type):
        res = await self.Chat.send_Name_reminder(author, channel, guild, new, chat_type)
        return res
    
    async def cmd_NSFW(self, guild, user, channel, chat_type):
        res = await self.Chat.send_NSFW_reminder(guild, user, channel, chat_type)
        return res
    
    async def cmd_clean(self, num, id, chat_type):
        await self.Chat.clean_chat_history(int(num), id, chat_type)
    
    async def cmd_reset(self, guild, channel, user, chat_type):
        await self.Chat.reset_chat(guild, channel, user, chat_type)
        
    async def cmd_info(self, author, channel, chat_type):
        if chat_type == CHAT_TYPE.GROUP:
            user_name = await self.Chat.search_database(MEMBERS.__name__, 
                                                        [MEMBERS.USER_NAME], 
                                                        {MEMBERS.GUILD_ID: channel.id, MEMBERS.USER_ID: author.id})
        else:
            user_name = await self.Chat.search_database(INDIVIDUALS.__name__,
                                                        [INDIVIDUALS.USER_NAME],
                                                        {INDIVIDUALS.USER_ID: author.id})
        return user_name
    
    async def cmd_create_chat(self, src_text, src_bot_id, dst_bot_id, channel_id, ooc_text):
        #啟用新的bot_chat_id
        bot_chat_id = await self.Chat.initial_new_chat(src_bot_id, CHAT_TYPE.BOT)
        exist = await self.Chat.search_database(BOT_CHAT.__name__, None, {BOT_CHAT.CHANNEL_ID: channel_id, BOT_CHAT.BOT_ID: dst_bot_id})
        if not exist:
            await self.Chat.insert_database(BOT_CHAT.__name__,{BOT_CHAT.BOT_CHAT_ID: bot_chat_id,
                                                               BOT_CHAT.BOT_ID: dst_bot_id,
                                                               BOT_CHAT.CHANNEL_ID: channel_id})
        else:
            await self.Chat.update_database(BOT_CHAT.__name__, {BOT_CHAT.BOT_CHAT_ID: bot_chat_id},
                                                        {BOT_CHAT.BOT_ID: dst_bot_id, BOT_CHAT.CHANNEL_ID: channel_id})
        dst_bot = self.bot.get_bot_instance(dst_bot_id)
        bot_chat_id = await dst_bot.Chat.initial_new_chat(dst_bot_id, CHAT_TYPE.BOT)
        exist = await dst_bot.Chat.search_database(BOT_CHAT.__name__, None, {BOT_CHAT.CHANNEL_ID: channel_id, BOT_CHAT.BOT_ID: dst_bot_id})
        if not exist:
            await dst_bot.Chat.insert_database(BOT_CHAT.__name__,{BOT_CHAT.BOT_CHAT_ID: bot_chat_id,
                                                               BOT_CHAT.BOT_ID: src_bot_id,
                                                               BOT_CHAT.CHANNEL_ID: channel_id})
        else:
            await dst_bot.Chat.update_database(BOT_CHAT.__name__, {BOT_CHAT.BOT_CHAT_ID: bot_chat_id},
                                                        {BOT_CHAT.BOT_ID: src_bot_id, BOT_CHAT.CHANNEL_ID: channel_id})
        #傳送給自己的chat_id
        res, res_translated, safety_flag = await self.Chat.bot_chat_recv(dst_bot_id, channel_id, src_text, ooc_text)
        res = remove_ooc(res)
        res_translated = remove_ooc(res_translated)
        
        return res, res_translated, safety_flag
    
    async def process_bot_chat(self, dst_bot_id, text, channel_id):
        src_bot_id = self.bot.user.id
        channel = self.bot.get_channel(int(channel_id))
        async with channel.typing():
            res, res_translated, safety_flag = await self.Chat.bot_chat_recv(dst_bot_id, channel_id, text)
            if safety_flag:
                embed = Styled_Embed(self.bot, EMBED_TYPE.NSFW_FILTER)
            await channel.send(res_translated, embed = embed if safety_flag else None, view = BotChatButton(self, src_bot_id, dst_bot_id, channel_id, res))
   
    async def cmd_ooc(self, text, guild, user, channel, chat_type):
        text = await self.Chat.translate_send(text, None)
        text = f"(ooc: {text})"
        res, flag = await self.Chat.send_RP_reminder(guild, user, channel, text, chat_type)
        return res
    
    #cmd   
    @commands.slash_command(name = "改變暱稱", description = "改變角色對自己的稱呼")
    async def name(self, interaction: discord.Interaction, name: str):
        try:
            channel, user, guild = interaction.channel, interaction.user, interaction.guild
            embed = Styled_Embed(self.bot, EMBED_TYPE.NAME_PROCESSING)
            await interaction.response.defer()
            msg = await interaction.followup.send(embed = embed)
            if isinstance(interaction.channel, discord.TextChannel):
                chat_type = CHAT_TYPE.GROUP
                id = channel.id
            else:
                chat_type = CHAT_TYPE.INDIVIDUAL
                id = user.id
            
            await self.check_last_msg_id(channel, user, chat_type)
            res = await self.cmd_name(user, channel, guild, name, chat_type)
            await self.update_last_msg_id(channel, user, msg.id, chat_type)
            
            embed.init_embed_type(EMBED_TYPE.NAME_COMPLETE, old = interaction.user.display_name, new = name, res = res)
            await msg.edit(embed = embed, view = ChatButton(self, id, chat_type
                                                            , embed_res=EMBED_TYPE.NAME_COMPLETE, old = interaction.user.display_name, new = name))
        except Exception as e:
            print(traceback.print_exc())
            print(e)

    @commands.slash_command(name = "nsfw", description = "關閉NSFW過濾器")
    async def NSFW(self, interaction: discord.Interaction):
        try:
            channel, user, guild = interaction.channel, interaction.user, interaction.guild
            embed = Styled_Embed(self.bot, EMBED_TYPE.NSFW_PROCESSING)
            await interaction.response.defer()
            msg = await interaction.followup.send(embed = embed)
            if isinstance(interaction.channel, discord.TextChannel):
                chat_type = CHAT_TYPE.GROUP 
                id = channel.id
            else:
                chat_type = CHAT_TYPE.INDIVIDUAL
                id = user.id

            await self.check_last_msg_id(channel, user, chat_type)
            res = await self.cmd_NSFW(guild, user, channel, chat_type)
            await self.update_last_msg_id(channel, user, msg.id, chat_type)
            
            embed.init_embed_type(EMBED_TYPE.NSFW_COMPLETE, res = res)
            await msg.edit(embed = embed, view = ChatButton(self, id, chat_type, embed_res=EMBED_TYPE.NSFW_COMPLETE))
        except Exception as e:
            print(e)
        
    @commands.slash_command(name = "清除歷史", description = "刪除指定數量的聊天紀錄")
    @option(name="數量", description = "欲清除數量")
    async def clean(self, interaction: discord.Interaction, 數量):
        msg_num = 數量
        try:
            channel, user = interaction.channel, interaction.user
            if isinstance(interaction.channel, discord.TextChannel):
                chat_type = CHAT_TYPE.GROUP 
                id = channel.id
            else:
                chat_type = CHAT_TYPE.INDIVIDUAL
                id = user.id
            await self.cmd_clean(msg_num, id, chat_type)
            await self.clean_last_msg_id(channel, user, chat_type)
            embed = Styled_Embed(self.bot, EMBED_TYPE.CLEAN_COMPLETE, num = msg_num)
            await interaction.response.send_message(embed = embed)
        except Exception as e:
            print(e)
        
    @commands.slash_command(name = "重置聊天", description = "重置角色聊天紀錄")
    async def reset(self, interaction: discord.Interaction):
        try:
            guild, channel, user = interaction.guild, interaction.channel, interaction.user
            await interaction.response.defer()
            embed = Styled_Embed(self.bot, EMBED_TYPE.RESET_PROCESSING)
            msg = await interaction.followup.send(embed=embed)
            if isinstance(interaction.channel, discord.TextChannel):
                chat_type = CHAT_TYPE.GROUP 
            else:
                chat_type = CHAT_TYPE.INDIVIDUAL
            
            await self.cmd_reset(guild, channel, user, chat_type)
            await self.clean_last_msg_id(channel, user, chat_type)
            embed.init_embed_type(EMBED_TYPE.RESET_COMPLETE)
            await msg.edit(embed = embed)
        except Exception as e:
            print(e)
            
    @commands.slash_command(name = "角色資訊", description = "取得角色基本資訊與目前使用名稱")
    async def info(self, interaction: discord.Interaction):
        try:
            chat_type = CHAT_TYPE.GROUP if isinstance(interaction.channel, discord.TextChannel) else CHAT_TYPE.INDIVIDUAL
            user_name = await self.cmd_info(interaction.user, interaction.channel, chat_type)
            embed = Styled_Embed(self.bot, EMBED_TYPE.SHOW_INFO, user_name = user_name)
            await interaction.response.send_message(embed = embed, ephemeral=True)
        except Exception as e:
            print(e)
    
    @commands.slash_command(name = "角色提示", description = "提醒角色設定/故事走向/其他")
    async def ooc(self, interaction: discord.Interaction, text):
        channel, user, guild = interaction.channel, interaction.user, interaction.guild
        await interaction.response.defer()
        embed = Styled_Embed(self.bot, EMBED_TYPE.OOC_PROCESSING)
        msg = await interaction.followup.send(embed=embed)
        if isinstance(interaction.channel, discord.TextChannel):
            chat_type = CHAT_TYPE.GROUP 
            id = channel.id
        else:
            chat_type = CHAT_TYPE.INDIVIDUAL
            id = user.id
        
        await self.check_last_msg_id(channel, user, chat_type)
        res = await self.cmd_ooc(text, guild, user, channel, chat_type)
        await self.update_last_msg_id(channel, user, msg.id, chat_type)
        
        embed.init_embed_type(EMBED_TYPE.OOC_COMPLETE, res = res)
        await msg.edit(embed = embed, view = ChatButton(self, id, chat_type, embed_res=EMBED_TYPE.OOC_COMPLETE))
    
    @commands.slash_command(name = "角色情境扮演", description = "開始與角色的故事扮演")
    async def rp(self, interaction: discord.Interaction):
        chat_type = CHAT_TYPE.GROUP if isinstance(interaction.channel, discord.TextChannel) else CHAT_TYPE.INDIVIDUAL
        await interaction.response.send_modal(RPInput_Modal(self, interaction.user, interaction.channel, interaction.guild, chat_type))
            
    @commands.slash_command(name = "線上狀態變更", description = "變更角色線上狀態（管理員限定）")
    async def status(self, interaction: discord.Interaction, status):
        try:
            admin = await self.check_admin(interaction.user.id)
            if not admin:
                embed = Styled_Embed(self.bot, EMBED_TYPE.CHECK_PRIVILAGE)
                await interaction.response.send_message(embed = embed, ephemeral=True)
                return
            embed = Styled_Embed(self.bot, EMBED_TYPE.STATUS_COMPLETE, status = status)
            modify_configs(self.path, BOT_SETTING.__name__, BOT_SETTING.STATUS, status)
            await self.bot.change_presence(activity=discord.Game(name=status))
            await interaction.response.send_message(embed = embed, ephemeral=True)
        except Exception as e:
            print(e)
                
    @commands.slash_command(name = "重啟", description = "重啟角色機器人（Debug）（管理員限定）")
    async def reboot(self, interaction: discord.Interaction):
        try:
            admin = await self.check_admin(interaction.user.id)
            if not admin:
                embed = Styled_Embed(self.bot, EMBED_TYPE.CHECK_PRIVILAGE)
                await interaction.response.send_message(embed = embed, ephemeral=True)
                return
            embed = Styled_Embed(self.bot, EMBED_TYPE.REBOOT_PROCESSING)
            await interaction.response.defer(ephemeral=True)
            msg = await interaction.followup.send(embed = embed, ephemeral=True)
            await self.bot.reboot()
            embed.init_embed_type(EMBED_TYPE.REBOOT_COMPLETE)
            await msg.edit(embed = embed)
        except Exception as e:
            print(e)
    
    @commands.slash_command(name = "指定管理員", description = "指定其他使用者為管理員（管理員）")
    @option(name = "user", descriptions = "請選擇欲指定的管理員...", input_type = discord.User)
    async def admin(self, interaction: discord.Interaction, user: discord.User):
        if isinstance(interaction.channel, discord.DMChannel):
            embed = Styled_Embed(self.bot, EMBED_TYPE.DM_NOT_AVALIABLE)
            interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            admin = await self.check_admin(interaction.user.id)
            if not admin:
                embed = Styled_Embed(self.bot, EMBED_TYPE.CHECK_PRIVILAGE)
                await interaction.response.send_message(embed = embed, ephemeral=True)
                return
            admin = await self.check_admin(user.id)
            if not admin:
                await self.Chat.insert_database(ADMIN.__name__, {ADMIN.USER_ID: user.id, ADMIN.PRIVILAGE: True})
                embed = Styled_Embed(self.bot, EMBED_TYPE.ADMIN_COMPLETE, user = user.display_name)
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(e)
    
    @commands.slash_command(name = "定時訊息啟用", description = "在特定頻道啟用訊息功能")
    @option(name = "type", description = "選擇啟用功能", choices = ["報時功能（早上/中午/晚上）", "歡迎新成員訊息功能"])
    @option(name = "state", description = "選擇功能狀態", choices = ["啟用", "禁用"])
    async def event(self, interaction: discord.Interaction, type: str, state: str):
        if isinstance(interaction.channel, discord.DMChannel):
            embed = Styled_Embed(self.bot, EMBED_TYPE.DM_NOT_AVALIABLE)
            interaction.response.send_message(embed=embed, ephemeral=True)
            return
        try:   
            admin = await self.check_admin(interaction.user.id)
            if not admin:
                embed = Styled_Embed(self.bot, EMBED_TYPE.CHECK_PRIVILAGE)
                await interaction.response.send_message(embed = embed, ephemeral=True)
                return
            if type == "報時功能（早上/中午/晚上）":
                if state == "啟用":
                    await interaction.response.send_message(view=ChannelSelectMenu(self, "schedule"), ephemeral=True)
                else:
                    await self.Chat.update_database(GUILD.__name__, {GUILD.TASK_CHANNEL_ID: None}, {GUILD.GUILD_ID: interaction.guild.id})
                    embed = Styled_Embed(self.bot, EMBED_TYPE.TASK_EVENT_DISABLED, func = type)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                if state == "啟用":
                    await interaction.response.send_message(view=ChannelSelectMenu(self, "welcome"), ephemeral=True)
                else:
                    await self.Chat.update_database(GUILD.__name__, {GUILD.EVENT_CHANNEL_ID: None}, {GUILD.GUILD_ID: interaction.guild.id})
                    embed = Styled_Embed(self.bot, EMBED_TYPE.TASK_EVENT_DISABLED, func = type)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
        except Exception as e:
            print(e)
            
    async def get_bot_list(self, ctx: discord.AutocompleteContext):
        if not ctx.interaction.guild:
            return []
        avaliable_bot_list = []
        bot_list = await self.Chat.search_database(BOT.__name__, [BOT.BOT_NAME, BOT.BOT_ID], None)
        for bot in bot_list:
            try:
                avaliable = await ctx.interaction.guild.fetch_member(int(bot[1]))
            except:
                avaliable = None
            if avaliable:
                avaliable_bot_list.append(bot[0])
        return avaliable_bot_list
    
    async def get_story_list(self, ctx: discord.AutocompleteContext):
        bot_name = ctx.options["角色名稱"]
        bot_id = await self.Chat.search_database(BOT.__name__, [BOT.BOT_ID], {BOT.BOT_NAME: bot_name})
        started = await self.Chat.search_database(BOT_CHAT.__name__, None, 
                                                  {BOT_CHAT.BOT_ID: bot_id, BOT_CHAT.CHANNEL_ID: ctx.interaction.channel.id})
        if started:
            return ["重置", "繼續"]
        else:
            return ["開始"]
        
    
    async def get_topic_list(self, ctx: discord.AutocompleteContext):
        choice = ctx.options["故事"]
        if choice in ("重置", "開始"):
            return ["詳細設定（RP）", "簡單設定（OOC）", "略過"]
        else:
            bot_name = ctx.options["角色名稱"]
            bot_id = await self.Chat.search_database(BOT.__name__, [BOT.BOT_ID], {BOT.BOT_NAME: bot_name})
            start = await self.Chat.search_database(BOT_CHAT.__name__, [BOT_CHAT.STATE], 
                                                    {BOT_CHAT.BOT_ID: bot_id, BOT_CHAT.CHANNEL_ID: ctx.interaction.channel.id})
            start_name = self.bot.user.name if start else bot_name
            return [f"從{start_name}的最後一則訊息繼續："]
    
    @commands.guild_only()
    @commands.slash_command(name = "角色一對一聊天", description = "開始該角色與其他角色的聊天")
    @option(name = "角色名稱", description = "選擇其他角色", autocomplete = get_bot_list)
    @option(name = "故事", description = "重置/繼續", autocomplete = get_story_list)
    @option(name = "主題", description = "選擇使用Role Play Topic（角色設定故事）", autocomplete = get_topic_list)
    async def create_chat(self, interaction: discord.Interaction, 角色名稱: str, 故事: str, 主題: str):
        bot_name, story, topic = 角色名稱, 故事, 主題
        if not self.settings[PROGRAM_SETTING.__name__][PROGRAM_SETTING.BOT_GROUP_CHAT]:
            embed = Styled_Embed(self.bot, EMBED_TYPE.BOT_CHAT_DISABLED)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if story in ("重置", "開始"):
            async with interaction.channel.typing():
                src_bot_id = self.bot.user.id
                src_chara_name = self.settings[PYCAI_SETTING.__name__][PYCAI_SETTING.CHAR_NAME]
                channel_id = interaction.channel.id
                dst_bot_id, dst_chara_name = await self.Chat.search_database(BOT.__name__, [BOT.BOT_ID, BOT.CHARA_NAME],
                                                                                    {BOT.BOT_NAME: bot_name})
                if topic == "詳細設定（RP）":
                    await interaction.response.send_modal(RPInput_Modal(self, None, interaction.channel, None, chat_type=CHAT_TYPE.BOT, src_bot_id = src_bot_id,
                                                                        dst_bot_id=dst_bot_id, src_chara_name = src_chara_name, dst_chara_name = dst_chara_name,
                                                                        channel_id = channel_id))
                elif topic == "簡單設定（OOC）":
                    await interaction.response.send_modal(TextInput_Modal(self, "ooc", None, interaction.channel, None, CHAT_TYPE.BOT, src_bot_id = src_bot_id,
                                                                        dst_bot_id=dst_bot_id, src_chara_name = src_chara_name, dst_chara_name = dst_chara_name,
                                                                        channel_id = channel_id, start = True))
                else:
                    embed = Styled_Embed(self.bot, EMBED_TYPE.BOT_CHAT_EMBED, bot_name = bot_name, status = "on", topic = "off")
                    await interaction.response.send_message(embed=embed)
                    src_text = f"(ooc: The character you will chat with is {dst_chara_name}\n\
                                Please be careful not to actively use ooc, just follow my ooc instructions\n\
                                Story start!)"
                    dst_text = f"(ooc: The character you will chat with is {src_chara_name}\n\
                                Please be careful not to actively use ooc, just follow my ooc instructions\n\
                                Story start!)"
                    res, res_translated, safety_flag = await self.cmd_create_chat(src_text, src_bot_id, dst_bot_id, interaction.channel.id, dst_text)
                    if safety_flag:
                        embed = Styled_Embed(self.bot, EMBED_TYPE.NSFW_FILTER)
                    view = BotChatButton(self, src_bot_id, dst_bot_id, channel_id, res, dst_text)
                    await interaction.followup.send(res_translated, embed = embed if safety_flag else None, view = view)
        else:
            try:
                embed = Styled_Embed(self.bot, EMBED_TYPE.BOT_CHAT_EMBED, bot_name = bot_name, status = "on")
                await interaction.response.send_message(embed = embed)
                src_bot_id = self.bot.user.id
                dst_bot_id = await self.Chat.search_database(BOT.__name__, [BOT.BOT_ID],{BOT.BOT_NAME: bot_name})
                channel_id = interaction.channel.id
                state, send_text = await self.Chat.search_database(BOT_CHAT.__name__, [BOT_CHAT.STATE, BOT_CHAT.LAST_MESSAGE_TEXT],
                                                                {BOT_CHAT.BOT_ID: dst_bot_id, BOT_CHAT.CHANNEL_ID: channel_id})
                dst_bot = self.bot.get_bot_instance(dst_bot_id)
                if state:
                    await self.Chat.update_database(BOT_CHAT.__name__, {BOT_CHAT.STATE: False}, 
                                                    {BOT_CHAT.BOT_ID: dst_bot_id, BOT_CHAT.CHANNEL_ID: channel_id})
                    await self.bot.send_bot_chat(src_bot_id, dst_bot_id, send_text, channel_id)
                else:
                    await dst_bot.Chat.update_database(BOT_CHAT.__name__, {BOT_CHAT.STATE: False},
                                                    {BOT_CHAT.BOT_ID: dst_bot_id, BOT_CHAT.CHANNEL_ID: channel_id})
                    send_text = await dst_bot.Chat.search_database(BOT_CHAT.__name__, [BOT_CHAT.LAST_MESSAGE_TEXT],
                                                                {BOT_CHAT.BOT_ID: dst_bot_id, BOT_CHAT.CHANNEL_ID: channel_id})
                    await self.process_bot_chat(dst_bot_id, send_text, channel_id)
            except:
                print(traceback.print_exc())
                
        return
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return
        elif message.author.bot:
            return
        user = message.author
        channel = message.channel
        guild = message.guild
        self.check_flag(channel.id)
        
        if isinstance(message.channel, discord.DMChannel):
            try:
                if not self.settings[PROGRAM_SETTING.__name__][PROGRAM_SETTING.INDIVIDUAL_CHAT]:
                    return
                
                async with message.channel.typing():
                    #查找該User最後一則message id
                    await self.check_last_msg_id(channel, user, CHAT_TYPE.INDIVIDUAL)
                        
                    response, flag = await self.Chat.send_chat(message.clean_content, guild, channel, user, self.bot.user, CHAT_TYPE.INDIVIDUAL)
                embed = Styled_Embed(self.bot, EMBED_TYPE.NSFW_FILTER)
                #Fix Continuously Send Message View
                if self.fix_button_flag[channel.id]:
                    view = None
                    self.fix_button_flag[channel.id] = False
                else:
                    view = ChatButton(self, user.id, CHAT_TYPE.INDIVIDUAL)
                    
                res = await asyncio.wait_for(message.reply(f"{response}", 
                                                            view = view, 
                                                            embed = embed if flag else None), timeout = 10)
                    
                #更新最後一則message id
                await self.update_last_msg_id(channel, user, res.id, CHAT_TYPE.INDIVIDUAL)
                    
            except asyncio.TimeoutError:
                message.reply("**[Log] Proccessing timeout, please try again, sorry!**")
            except Exception as e:
                print(traceback.print_exc())
                print(e)
                
        elif self.bot.user.mentioned_in(message) and isinstance(message.channel, discord.TextChannel):
            if not self.settings[PROGRAM_SETTING.__name__][PROGRAM_SETTING.CHANNEL_GROUP_CHAT]:
                return
            try:
                async with message.channel.typing():
                    #查找該Guild最後一則message id
                    await self.check_last_msg_id(channel, user, CHAT_TYPE.GROUP)
                    response, flag = await self.Chat.send_chat(message.clean_content, guild, channel, user, self.bot.user, CHAT_TYPE.GROUP)
                    
                embed = Styled_Embed(self.bot, EMBED_TYPE.NSFW_FILTER)
                if self.fix_button_flag[channel.id]:
                    view = None
                    self.fix_button_flag[channel.id] = False
                else:
                    view = ChatButton(self, channel.id, CHAT_TYPE.GROUP)
                    
                res = await asyncio.wait_for(message.reply(f"{response}", 
                                                            view = view, 
                                                            embed = embed if flag else None), timeout = 10)
                
                '''self.ooc_count[channel.id] += 1
                if self.ooc_count[channel.id] >= DEFINE_OOC_COUNT:
                    await self.Chat.send_ooc_reminder(channel.id)
                    self.ooc_count[channel.id] = 0'''
                    
                #更新最後一則message id
                await self.update_last_msg_id(channel, user, res.id, CHAT_TYPE.GROUP)
            except asyncio.TimeoutError:
                message.reply("**[Log] Proccessing timeout, please try again, sorry!**")
            except Exception as e:
                print(traceback.print_exc())
                print(e)
            


def setup(bot: commands.Bot):
    bot.add_cog(Main(bot))
    
