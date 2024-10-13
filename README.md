# DCAI
> :point_right:  **IMPORTANT**:point_left:
> 
> 該版本不包含管理機器人的 GUI，僅包含運行檔

DCAI 是一款針對 Character ai 的多項聊天功能，整理並串接到 Discord 機器人上的專案。
目前僅有繁體中文(zh-tw)的版本。
## How to set-up
> 請先在 [Discord.dev](https://ptb.discord.com/developers/applications) 創建一個 Discord bot，並記下其 token
1. 執行 bot.py 並關閉
2. 手動編輯一個 .ini 檔，並且放入 DCAI 根目錄下的 configs 資料夾。
> [[DCAI] 如何取得 CAI Token 和 Character ID](https://hackmd.io/@MiipisSus/BJXOGRh_a)
> 
> [[DCAI] 如何取得Discord Bot Token](https://hackmd.io/@MiipisSus/Hkffw62O6)

格式：
```
[API_KEY]
openai_apikey = # 英翻中用，不需要則不填
pycai_apikey = # 必填
azure_key = # 英翻中用，不需要則不填

[PYCAI_SETTING]
creator_id = # 必填
char_id = # 必填
char_name = # 必填

[OPENAI_SETTING]
model = # 英翻中用，不需要則不填
user = user

[AZURE_SETTING]
endpoint = # 英翻中用，不需要則不填
location = eastasia

[DATA_PATH]
database_create = False

[BOT_SETTING]
status = # bot 啟動時的線上狀態
bot_token = # 必填
prefix = 

[STYLE]
embed_color = 0x3e6860 # 自行修改色碼

[PROGRAM_SETTING] # 英翻中用，不需要則不填
src_translate_mode = 2 # NONE=0, OPENAI=1, AZURE=2, GOOGLETRANS=3
dst_translate_mode = 1 # NONE=0, OPENAI=1, AZURE=2, GOOGLETRANS=3
bot_translate_mode = 3 # NONE=0, OPENAI=1, AZURE=2, GOOGLETRANS=3
vocab = True
language = zh-tw
```
