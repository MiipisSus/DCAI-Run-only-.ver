from enum import IntEnum, auto
from configparser import ConfigParser

def modify_configs(path, type, attr, value):
    path = "configs/" + path
    config = ConfigParser()
    config.read(path)
    config.set(type, attr, value)
    with open(path, "w") as configfile:
        config.write(configfile)

def init_configs(path):
    config_file = ConfigParser()
    config_file.read(path)
    settings = {}
    for section in config_file.sections():
        settings[section] = {}
        for option in config_file.options(section):
            value = config_file.get(section, option)
            if value.lower() in ('true', 'false'):
                settings[section][option.upper()] = config_file.getboolean(section, option)
            elif value.isdigit():
                settings[section][option.upper()] = config_file.getint(section, option)
            elif value.startswith("0x"):
                settings[section][option.upper()] = int(value, 16)
            else:
                settings[section][option.upper()] = value
    return settings
                    
class API_KEY():
    OPENAI_APIKEY = "OPENAI_APIKEY"
    PYCAI_APIKEY = "PYCAI_APIKEY"
    AZURE_KEY = "AZURE_KEY"
    
class PYCAI_SETTING():
    CREATOR_ID = "CREATOR_ID"
    CHAR_ID = "CHAR_ID"
    CHAR_NAME = "CHAR_NAME"
    
class OPENAI_SETTING():
    MODEL = "MODEL"
    USER = "USER"

class AZURE_SETTING():
    ENDPOINT = "ENDPOINT"
    LOCATION = "LOCATION"

class DATA_PATH():
    DATABASE_CREATE = "DATABASE_CREATE"
    
class BOT_SETTING():
    STATUS = "STATUS"
    BOT_TOKEN = "BOT_TOKEN"
    AVATAR_PATH = "AVATAR_PATH"
    
class STYLE():
    EMBED_COLOR = "EMBED_COLOR"
    
class PROGRAM_SETTING():
    SRC_TRANSLATE_MODE = "SRC_TRANSLATE_MODE"
    DST_TRANSLATE_MODE = "DST_TRANSLATE_MODE"
    BOT_TRANSLATE_MODE = "BOT_TRANSLATE_MODE"
    VOCAB = "VOCAB"
    LANGUAGE = "LANGUAGE"
    INDIVIDUAL_CHAT = "INDIVIDUAL_CHAT"
    CHANNEL_GROUP_CHAT = "CHANNEL_GROUP_CHAT"
    BOT_GROUP_CHAT = "BOT_GROUP_CHAT"

#PROGRAM
DEFINE_OOC_COUNT = 15

class CHAT_TYPE(IntEnum):
    GROUP = 0
    INDIVIDUAL = 1
    NOTIFY = 2
    BOT = 3

class TRANSLATE_MODE(IntEnum):
    GOOGLE = 0
    OPENAI = 1
    AZURE = 2

#DATABASE

class GUILD():
    GUILD_ID = "GUILD_ID"
    TASK_CHANNEL_ID = "TASK_CHANNEL_ID"
    EVENT_CHANNEL_ID = "EVENT_CHANNEL_ID"
    NOTIFY_CHAT_ID = "NOTIFY_CHAT_ID"
    ACCESS = "ACCESS"
    
class CHANNEL():
    CHANNEL_ID = "CHANNEL_ID"
    GUILD_ID = "GUILD_ID"
    GROUP_CHAT_ID = "GROUP_CHAT_ID"
    ACCESS = "ACCESS"
    LAST_MESSAGE_ID = "LAST_MESSAGE_ID"
    LAST_TURN_ID = "LAST_TURN_ID"

class INDIVIDUALS():
    USER_ID = "USER_ID"
    USER_NAME = "USER_NAME"
    CHAT_ID = "CHAT_ID"
    ACCESS = "ACCESS"
    LAST_MESSAGE_ID = "LAST_MESSAGE_ID"
    LAST_TURN_ID = "LAST_TURN_ID"
    
class MEMBERS():
    GUILD_ID = "GUILD_ID"
    USER_ID = "USER_ID"
    USER_NAME = "USER_NAME"
    ACCESS = "ACCESS"
    
class ADMIN():
    USER_ID = "USER_ID"
    PRIVILAGE = "PRIVILAGE"

class BOT():
    BOT_ID = "BOT_ID"
    BOT_NAME = "BOT_NAME"
    CHARA_NAME = "CHARA_NAME"

class BOT_CHAT():
    BOT_ID = "BOT_ID"
    BOT_CHAT_ID = "BOT_CHAT_ID"
    LAST_TURN_ID = "LAST_TURN_ID"
    CHANNEL_ID = "CHANNEL_ID"
    STATE = "STATE"
    LAST_MESSAGE_TEXT = "LAST_MESSAGE_TEXT"
    
class EMBED_TYPE(IntEnum):
    NAME_PROCESSING = auto()
    NAME_COMPLETE = auto()
    NSFW_PROCESSING = auto()
    NSFW_COMPLETE = auto()
    CLEAN_COMPLETE = auto()
    RESET_PROCESSING = auto()
    RESET_COMPLETE = auto()
    SHOW_INFO = auto()
    SHOW_LIST = auto()
    NSFW_FILTER = auto()
    EXECUTED_FLAG = auto()
    REMOVE_LAST_MESSAGE = auto()
    REFRESH_LAST_MESSAGE = auto()
    STATUS_COMPLETE = auto()
    REBOOT_PROCESSING = auto()
    REBOOT_COMPLETE = auto()
    RP_PROCESSING = auto()
    RP_COMPLETE = auto()
    OOC_PROCESSING = auto()
    OOC_COMPLETE = auto()
    ADMIN_COMPLETE = auto()
    CHECK_PRIVILAGE = auto()
    SHOW_TASK = auto()
    SHOW_EVENT = auto()
    TASK_COMPLETE = auto()
    EVENT_COMPLETE = auto()
    TASK_EVENT_DISABLED = auto()
    BOT_CHAT_EMBED = auto()
    BOT_CHAT_DISABLED = auto()
    DM_NOT_AVALIABLE = auto()
    
    