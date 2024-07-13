## World Translation Helper(WTH)
Forked by [WorldTranslationExtractor](https://github.com/3093FengMing/WorldTranslationExtractor)

[中文](README_CN.md)

## Improvements to the Original
### More Standard Python Project Structure
- Added `requirements.txt` for simplified environment setup
- More `.gitignore` rules
- Included a batch file `.bat` for Pyinstaller to package into exe (Windows only)

### Enhanced User Experience
- Improved prompt messages
- Removed parameter-based usage, allowing users to input paths
- Supported localization, displaying multiple languages based on system language

### Technical Improvements
- Added support for Python 3.12 (Windows only)
- Added support for non-Windows systems
- Simplified and improved a large amount of code
- Python version requirement now >= 3.10 (not support Windows 7)

~~Not supported by Python official. The original is not supported. However, it can be supported through special methods.~~

## How to Run
From source code:
- Dependencies: `amulet-core`, `tqdm`
- Installation: `pip install -r requirements.txt`
- Build (Windows only): Run `win_build_pyinstaller.bat` and copy `lang` and `config.json` to the `dist` folder.

Run the executable exe (Windows 10+ only):
- Double-click to run.

### Tip

1. WTEM cannot change the target selector `name=` and the container's `Lock` tag, but it will be recorded for later reference and correction.

## Functions
Scans a full world searching for json `"text"` components and replaces them with `"translation"` components, generating a lang file to be used with a resourcepack

Finds json components in:
1. **Blocks**
  - Spawners: SpawnData, SpawnPotentials
  - Containers: items, container name (`"chest"`, `"furnace"`, `"shulker_box"`, `"barrel"`, `"smoker"`, `"blast_furnace"`, `"trapped_chest"`, `"hopper"`, `"dispenser"`, `"dropper"`, `"brewing_stand"`, `"campfire"`, <u>`"chiseled_bookshelf"`, `"decorated_pot"`)
  - (Hanging) Signs: text1-4, front_text, back_text
  - Lecterns: Book
  - Jukeboxes: RecordItem
  - Beehives & Bee nests: Bees
  - Command block: Command
2. **Entities**
  - Name
  - Items
  - ArmorItems
  - HandItems
  - Inventory
  - Villager offers
  - Passengers
  - Text Display
  - Item Display
3. **Items**
  - Name
  - Lore
  - Book pages
  - Book title: adds a customname in case it doesn't already have one
  - BlockEntityTag
  - EntityTag
4. **Scoreboard**: objective names, team names and affixes
5. **Bossbars**: names
6. **Datapacks**: functions, json files
7. **Structures**: blocks, entities
