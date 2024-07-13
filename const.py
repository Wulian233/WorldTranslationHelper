import re
import sys

import locale
from i18n import Locale

if (3,11) <= sys.version_info < (3, 15):
    getdefaultlocale = locale._getdefaultlocale()[0]
elif sys.version_info <= (3, 10):
    getdefaultlocale = locale.getdefaultlocale()[0]

# 自动切换语言
if getdefaultlocale == "zh_CN":
    lang = Locale("zh_CN")
else:
    lang = Locale("en_US")
    
current_language = lang.get_language()

global OLD_SPAWNER_FORMAT

global cfg_settings, cfg_lang, cfg_dupe, cfg_default, cfg_filters, DISABLE_COMPONENTS_LIMIT, DISABLE_MARCOS_LIMIT
cfg_settings = cfg_lang = cfg_dupe = cfg_default = cfg_filters = None
DISABLE_COMPONENTS_LIMIT = DISABLE_MARCOS_LIMIT = None

# Config
cfg_settings = cfg_lang = cfg_dupe = cfg_filters = cfg_default = {}

DISABLE_COMPONENTS_LIMIT = False
DISABLE_MARCOS_LIMIT = False

# REG
REG_ANY_TEXT = r'"((?:[^"\\]|\\\\|\\.)*)"'

REG_COMPONENT = re.compile(r'"text" *: *"((?:[^"\\]|\\\\|\\.)*)"')
REG_COMPONENT_PLAIN = re.compile(r'"((?:[^"\\]|\\\\|\\.)*)"')
REG_COMPONENT_DOUBLE_ESCAPED = re.compile(r'\\\\"text\\\\" *: *\\\\"((?:[^"\\]|\\\\.)*)\\\\"')
REG_COMPONENT_ESCAPED = re.compile(r'\\"text\\" *: *\\"((?:[^"\\]|\\\\|\\.)*)\\"')
REG_DATAPACK_CONTENTS = re.compile(r'"contents":"((?:[^"\\]|\\\\|\\.)*)"')

# Special REG
SREG_MARCO = re.compile(r'\$\(.+\)')

SREG_CMD_BOSSBAR_SET_NAME = re.compile(r'bossbar set ([^ ]+) name "(.*)"')
SREG_CMD_BOSSBAR_ADD = re.compile(r'bossbar add ([^ ]+) "(.*)"')

SREG_COMPONENT_ESCAPED = re.compile(r'\"text\" *: *\"((?:[^"\\]|\\\\.)*)\"')
SREG_COMPONENT = re.compile(r'"text" *: *"((?:[^"\\]|\\\\.)*)"')

SREG_ADV_TITLE = re.compile(r'"title" *: *"((?:[^"\\]|\\\\|\\.)*)"')
SREG_ADV_DESC = re.compile(r'"description" *: *"((?:[^"\\]|\\\\|\\.)*)"')

SREG_RECORD_NAME_TARGET_SELECTOR = re.compile(r'name=')

# Others
OLD_SPAWNER_FORMAT = False  # If this is false, uses 1.18+ nbt paths for spawners
CONTAINERS = ["chest", "furnace", "shulker_box", "barrel", "smoker", "blast_furnace", "trapped_chest", "hopper",
              "dispenser", "dropper", "brewing_stand", "campfire", "chiseled_bookshelf"]

item_counts = entity_counts = block_counts = {}

key = "no_key"
key_cnt = 0