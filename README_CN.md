# 存档翻译提取助手（WTH）
World Translation Helper

由[WTEM](https://github.com/3093FengMing/WorldTranslationExtractor)修改而来的Fork版

[English](README.md)

## 对原作的改进
### 更规范的Python项目结构
- 加入`requirements.txt`简化环境安装
- 完善`.gitignore`规则
- 加入Pyinstaller打包exe的批处理`.bat`文件（仅Windows）
### 更人性化的使用体验
- 改进的提示信息
- 移除参数式使用，让用户输入路径
- 支持本地化，根据系统语言显示多种语言
### 技术性改进
- 加入对Python 3.12的支持（仅Windows）
- 加入对非Windows系统的支持
- 简化大量代码
- 改进大量代码
- 现在对Python的版本要求为>=3.10（不支持Windows7）

~~Python官方不支持。原作也不支持。但通过特殊方法可支持~~

## 运行
通过源代码
- 依赖 `amulet-core` 、 `tqdm`
- 安装: `pip install -r requirements.txt`
- 打包（仅Windows）：运行`win_build_pyinstaller.bat`后并把`lang`和`config.json`放在`dist`文件夹内

运行可执行程序exe（仅Windows10+）
- 双击运行即可

## 提示
WTEH无法更改目标选择器`name=`，以及容器的`Lock`标签，但是会记录下来，方便后期查找更正。

## 功能
扫描整个存档，搜索json文本中的`"text"`组件，并替换为`"translate"`组件，生成一个与资源包一起使用的lang文件。

会在以下搜索json文本:
1. **方块**
  - 刷怪笼: SpawnData (下一个生成的实体), SpawnPotentials (要生成实体的列表)
  - 容器: items (物品), 容器名称 (`"chest"`, `"furnace"`, `"shulker_box"`, `"barrel"`, `"smoker"`, `"blast_furnace"`, `"trapped_chest"`, `"hopper"`, `"dispenser"`, `"dropper"`, `"brewing_stand"`, `"campfire"`, `"chiseled_bookshelf"`, `"decorated_pot"`)
  - (悬挂)告示牌: text1-4 (一至四行文本), front_text, back_text (正反面文本)
  - 讲台: Book (成书)
  - 唱片机: RecordItem (唱片)
  - **蜂窝与蜂巢: Bees (蜜蜂)
  - 命令方块: Command (命令)
2. **实体**
  - Name (名称)
  - Items (背包)
  - ArmorItems (盔甲)
  - HandItems (手持物品)
  - Inventory (物品栏)
  - Villager offers (村民交易)
  - Passengers (乘骑实体)
  - Text Display (文本展示实体)
  - Item Display (物品展示实体)
3. **物品**
  - Name (名称)
  - Lore
  - Book pages (书页)
  - Book title (书本标题): 以防没有，会添加customname
  - BlockEntityTag (方块实体标签)
  - EntityTag (实体标签)
4. **记分板**: objective names (记分项名称), team names and affixes (队伍名称以及前后缀)
5. **Boss栏**: names (名称)
6. **数据包**: functions (函数), json files (json文件)
7. **结构**: blocks (方块), entities (实体)
