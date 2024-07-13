__author__ = "Wulian233 <admin@vmct-cn.top>"
__version__ = "1.0"

import json
import os
import re
import pathlib

import amulet_nbt

from const import *
from i18n import lang

class CSFilter:
    def __init__(self):
        self.include_namespaces = []
        self.include_paths = []
        self.exclude_namespaces = []
        self.exclude_paths = []

    def add(self, mode, namespace, path):
        if mode == 'include':
            self.include_namespaces.append(namespace)
            self.include_paths.append(path)
        elif mode == 'exclude':
            self.exclude_namespaces.append(namespace)
            self.exclude_paths.append(path)
        else:
            raise RuntimeError(f"Filter mode {mode} does not exist!")

    def filter(self, namespace, path):
        if namespace in self.include_namespaces and path in self.include_paths:
            return True
        if namespace in self.exclude_namespaces and path in self.exclude_paths:
            return False
        return True

class WPFilter:
    def __init__(self):
        self.include_worlds = []
        self.include_positions = []
        self.exclude_worlds = []
        self.exclude_positions = []

    class Vector3i:
        def __init__(self, x, y, z):
            self.x, self.y, self.z = x, y, z

    def add(self, mode, world, start_coords, end_coords):
        start = [0, 0, 0]
        end = [0, 0, 0]
        
        for i in range(3):
            start[i] = min(start_coords[i], end_coords[i])
            end[i] = max(start_coords[i], end_coords[i])

        start_pos = self.Vector3i(*start)
        end_pos = self.Vector3i(*end)
        start_and_end = [start_pos, end_pos]

        if mode == 'include':
            self.include_worlds.append(world)
            self.include_positions.append(start_and_end)
        elif mode == 'exclude':
            self.exclude_worlds.append(world)
            self.exclude_positions.append(start_and_end)
        else:
            raise ValueError(f"Filter mode {mode} does not exist!")

    def is_in(self, x, y, z, sae):
        start, end = sae
        return start.x <= x <= end.x and start.y <= y <= end.y and start.z <= z <= end.z

    def filter(self, world, x, y, z):
        if world in self.include_worlds:
            return any(self.is_in(x, y, z, sae) for sae in self.include_positions)

        if world in self.exclude_worlds:
            return not any(self.is_in(x, y, z, sae) for sae in self.exclude_positions)

        return True


class MetaDict(dict):
    class Metadata:
        def __init__(self, key, value, dupe: bool):
            self.key, self.value, self.dupe = key, value, dupe

    def __init__(self, _type):
        super().__init__()
        self.inner_dict = {}
        self.type = _type

    def put(self, key, value, dupe):
        self.inner_dict[key] = self.Metadata(key, value, dupe)

    def get(self, key):
        return self.inner_dict.get(key)

    def __getitem__(self, item):
        return self.inner_dict[item].value

    def __len__(self):
        return len(self.inner_dict)

    def items(self):
        return [(meta.key, meta.value) for meta in self.inner_dict.values()]

    def __iter__(self):
        return iter(self.inner_dict)

CS_FILTER = CSFilter()
WP_FILTER = WPFilter()
rev_lang: dict = {}  # Keep duplicates (reversed)
rel_lang = MetaDict("rel")

# keys
def set_key(k):
    global key, key_cnt
    key = k
    key_cnt = 0

def get_key():
    global key_cnt
    key_cnt += 1
    return f"{key}.{key_cnt}"

# match & replace
def sub_replace(pattern, string, repl, dupe=False, search_all=True, is_marco=False):
    if search_all:
        ls = list(string)
        loop_count = 0
        last_match = None
        match = pattern.search(string)
        if match is None:
            return string
        
        while match is not None:
            # 防止死循环
            if not DISABLE_COMPONENTS_LIMIT and last_match is not None and last_match.string == match.string:
                loop_count += 1
                if loop_count >= cfg_settings['components_max']:
                    print(lang.t("main.components_max", string=string))
                    break

            span = match.span()
            ls[span[0]:span[1]] = repl(match, dupe=dupe, is_marco=is_marco)
            match = pattern.search(''.join(ls))
            last_match = match
        return ''.join(ls)
    else:
        if match := pattern.match(string):
            return repl(match, dupe=dupe)
        else:
            return string

def marcos_extract(string: str):
    marcos = []
    ls = list(string)
    loop_count = 0
    last_match = None

    while match := SREG_MARCO.search(string):
        # prevent endless loop
        if not DISABLE_MARCOS_LIMIT and last_match and last_match.string == match.string:
            loop_count += 1
            if loop_count >= cfg_settings['marcos_max']:
                print(lang.t("main.marcos_max", string=string))
                break

        span = match.span()
        marcos.append(''.join(ls[span[0]:span[1]]))
        ls[span[0]:span[1]] = "[extracted]"
        string = ''.join(ls)
        last_match = match
    return marcos

def get_plain_from_match(match, escaped=False, ord=1):
    plain = match if isinstance(match, str) else match.group(ord)
    if escaped:
        plain = re.sub(pattern=r'\\\\', string=plain, repl=r'\\')
    plain = re.sub(pattern=r'\\\\([^\\])', string=plain, repl=r'\\\1')
    plain = re.sub(pattern=r"\\'", string=plain, repl=r"'")
    return plain


def match_text(match, escaped=False, dupe=False, is_marco=False, double_escaped=False):
    plain = get_plain_from_match(match, escaped)
    rk = get_key()
    if is_marco:
        crk = rk + ".marco"
        for m in marcos_extract(plain):
            crk = crk + "." + m
        rk = crk
    if plain not in rev_lang:
        rev_lang[plain] = rk
    if plain in cfg_default:
        print(f'[text default] {cfg_default[plain]}: {plain}')
        return (f'\\\\"translate\\\\":\\\\"{cfg_default[plain]}\\\\"' if double_escaped else f'\\"translate\\":\\"{cfg_default[plain]}\\"') if escaped else f'"translate":"{cfg_default[plain]}"'
    rel_lang.put(rk, plain, dupe)
    if dupe:
        print(f'[text dupeIf] put key: {rk}: {rel_lang[rk]}')
        return (f'\\\\"translate\\\\":\\\\"{rk}\\\\"' if double_escaped else f'\\"translate\\":\\"{rk}\\"') if escaped else f'"translate":"{rk}"'
    print(f'[text dupeElse] put key: {rev_lang[plain]}: {plain}')
    return (f'\\\\"translate\\\\":\\\\"{rev_lang[plain]}\\\\"' if double_escaped else f'\\"translate\\":\\"{rev_lang[plain]}\\"') if escaped else f'"translate":"{rev_lang[plain]}"'


def match_plain_text(match, dupe=False, is_marco=False):
    plain = match.string[1:-1]
    rk = get_key()
    if plain not in rev_lang:
        rev_lang[plain] = rk
    if plain in cfg_default:
        print(f'[plain default] {cfg_default[plain]}: {plain}')
        return f'{{"translate":"{cfg_default[plain]}"}}'
    rel_lang.put(rk, plain, dupe)
    if dupe:
        print(f'[plain dupeIf] put key: {rk}: {rel_lang[rk]}')
        return f'{{"translate":"{rk}"}}'
    print(f'[plain dupeElse] put key: {rev_lang[plain]}: {plain}')
    return f'{{"translate":"{rev_lang[plain]}"}}'


def match_contents(match, dupe=False, is_marco=False):
    plain = get_plain_from_match(match)
    rk = get_key()
    if plain not in rev_lang:
        rev_lang[plain] = rk
    if plain in cfg_default:
        print(f'[contents default] {cfg_default[plain]}: {plain}')
        return f'"contents":{{"translate":"{cfg_default[plain]}"}}'
    rel_lang.put(rk, plain, dupe)
    if dupe:
        print(f'[contents dupeIf] put key: {rk}: {rel_lang[rk]}')
        return f'"contents":{{"translate":"{rk}"}}'
    print(f'[contents dupeElse] put key: {rev_lang[plain]}: {plain}')
    return f'"contents":{{"translate":"{rev_lang[plain]}"}}'


def match_bossbar_common(match, action, dupe=False, is_marco=False):
    plain = get_plain_from_match(match, ord=2)
    name = match.group(1)
    rk = get_key()
    
    if is_marco:
        rk = rk + ".marco" + "".join(f".{m}" for m in marcos_extract(plain))
    
    if plain not in rev_lang:
        rev_lang[plain] = rk
    
    if plain in cfg_default:
        print(f'[bossbar {action} default] {cfg_default[plain]}: {plain}')
        return f'bossbar {action} {name} name {{{cfg_default[plain]}}}'
    
    rel_lang.put(rk, plain, dupe)
    
    if dupe:
        print(f'[bossbar {action} dupeIf] put key: {rk}: {rel_lang[rk]}')
        return f'bossbar {action} {name} name {{"translate":"{rk}"}}'
    
    print(f'[bossbar {action} dupeElse] put key: {rev_lang[plain]}: {plain}')
    return f'bossbar {action} {name} name {{"translate":"{rev_lang[plain]}"}}'

def match_bossbar(match, dupe=False, is_marco=False):
    return match_bossbar_common(match, "set", dupe, is_marco)

def match_bossbar2(match, dupe=False, is_marco=False):
    return match_bossbar_common(match, "add", dupe, is_marco)


def match_advancement_common(match, field, dupe=False, is_marco=False):
    plain = get_plain_from_match(match)
    rk = get_key()
    
    if plain not in rev_lang:
        rev_lang[plain] = rk
    
    if plain in cfg_default:
        print(f'[adv {field} default] {cfg_default[plain]}: {plain}')
        return f'"{field}":{{"translate":"{cfg_default[plain]}"}}'
    
    rel_lang.put(rk, plain, dupe)
    
    if dupe:
        print(f'[adv {field} dupeIf] put key: {rk}: {rel_lang[rk]}')
        return f'"{field}":{{"translate":"{rk}"}}'
    
    print(f'[adv {field} dupeElse] put key: {rev_lang[plain]}: {plain}')
    return f'"{field}":{{"translate":"{rev_lang[plain]}"}}'

def match_advancement_title(match, dupe=False, is_marco=False):
    return match_advancement_common(match, "title", dupe, is_marco)

def match_advancement_desc(match, dupe=False, is_marco=False):
    return match_advancement_common(match, "description", dupe, is_marco)

def match_text_double_escaped(match, dupe=False, is_marco=False):
    return match_text(match, True, dupe, is_marco, True)

def match_text_escaped(match, dupe=False, is_marco=False):
    return match_text(match, True, dupe, is_marco)


def replace_component(text, dupe=False):
    text = sub_replace(SREG_COMPONENT_ESCAPED, str(text), match_text, dupe, False)
    text = sub_replace(REG_COMPONENT_DOUBLE_ESCAPED, text, match_text_double_escaped, dupe)
    text = sub_replace(REG_COMPONENT_ESCAPED, text, match_text_escaped, dupe)
    text = sub_replace(SREG_COMPONENT, text, match_text, dupe, False)
    text = sub_replace(REG_COMPONENT, text, match_text, dupe)
    text = sub_replace(REG_COMPONENT_PLAIN, text, match_plain_text, dupe, False)
    return amulet_nbt.TAG_String(text)

def handle_item(item, dupe=False):
    if not item or 'tag' not in item:
        return False

    id = str(item['id'])[10:]
    item_counts.setdefault(id, 1)
    translation_cnt = len(rel_lang)
    changed = False

    if display := item['tag'].get('display'):
        if name := display.get('Name'):
            set_key(f"item.{id}.{item_counts[id]}.name")
            display['Name'] = replace_component(name, dupe or cfg_dupe["items_name"] or cfg_dupe["items_all"])
            changed = True

        if lore := display.get('Lore'):
            for line, lore_line in enumerate(lore):
                set_key(f"item.{id}.{item_counts[id]}.lore.{line}")
                lore[line] = replace_component(lore_line, dupe or cfg_dupe["items_lore"] or cfg_dupe["items_all"])
            changed = True

    if pages := item['tag'].get('pages'):
        for page, content in enumerate(pages):
            set_key(f"item.{id}.{item_counts[id]}.page.{page}")
            pages[page] = replace_component(content, dupe or cfg_dupe["items_pages"] or cfg_dupe["items_all"])
        changed = True

    if title := item['tag'].get('title'):
        title = str(title)
        display = item['tag'].setdefault('display', amulet_nbt.TAG_Compound())
        if 'Name' not in display:
            rk = f"item.{id}.{item_counts[id]}.title.1"
            rel_lang.put(rk, title, dupe)
            rev_lang.setdefault(title, rk)
            key = rk if dupe or cfg_dupe["items_title"] or cfg_dupe["items_all"] else rev_lang[title]
            display['Name'] = amulet_nbt.TAG_String(f'{{"translate":"{key}","italic":false}}')
            print(f'[json book title] put key: {key}: {rel_lang[rk]}')
            changed = True

    if translation_cnt != len(rel_lang):
        item_counts[id] += 1

    if block_entity_tag := item['tag'].get('BlockEntityTag'):
        block_entity_changed = handle_block_entity_nbt(block_entity_tag, item['id'])
        if block_entity_changed: changed = True

    if entity_tag := item['tag'].get('EntityTag'):
        entity_changed = handle_entity(entity_tag, None)
        if entity_changed: changed = True

    return changed

def handle_container(container, type):
    block_counts.setdefault(type, 1)
    changed = False
    translation_cnt = len(rel_lang)

    if custom_name := container.get("CustomName"):
        set_key(f"block.{type}.{block_counts[type]}.name")
        container['CustomName'] = replace_component(custom_name, cfg_dupe["containers_name"])
        changed = True

    if translation_cnt != len(rel_lang):
        block_counts[type] += 1

    if lock := container.get("Lock"):
        if not lock:
            print(lang.t("main.skip_lock", lock=lock))

    if items := container.get("Items"):
        for item in items:
            item_changed = handle_item(item, cfg_dupe["items_in_same"])
            if item_changed: changed = True

    return changed

def handle_item_entity_block(block, nbt_path):
    try:
        if isinstance(nbt_path, str):
            item = block[nbt_path]
        elif isinstance(nbt_path, list):
            item = block
            for path in nbt_path:
                item = item[path]
        return handle_item(item)
    except KeyError:
        return False

def handle_command_block(command_block):
    block_counts.setdefault("command_block", 1)
    translation_cnt = len(rel_lang)
    set_key(f"block.command_block.{block_counts['command_block']}.command")

    command = str(command_block['Command'])

    command = sub_replace(SREG_COMPONENT_ESCAPED, command, match_text, cfg_dupe["command_blocks"])
    command = sub_replace(REG_COMPONENT_ESCAPED, command, match_text_escaped, cfg_dupe["command_blocks"])
    command = sub_replace(SREG_COMPONENT, command, match_text, cfg_dupe["command_blocks"])
    command = sub_replace(REG_COMPONENT, command, match_text, cfg_dupe["command_blocks"])
    # command = sub_replace(REG_COMPONENT_PLAIN, command, match_text, cfg_dupe["command_blocks"], False)
    command = sub_replace(REG_DATAPACK_CONTENTS, command, match_contents, cfg_dupe["command_blocks"])

    command = sub_replace(SREG_CMD_BOSSBAR_SET_NAME, command, match_bossbar, cfg_dupe["command_blocks"])
    command = sub_replace(SREG_CMD_BOSSBAR_ADD, command, match_bossbar2, cfg_dupe["command_blocks"])

    command_block['Command'] = amulet_nbt.TAG_String(command)

    # m = SREG_RECORD_NAME_TARGET_SELECTOR.search(command)
    # if m is not None:
    #     print("[record] Target Selector Name: ", str(m.start()))

    if translation_cnt != len(rel_lang):
        block_counts["command_block"] += 1

    return True


def handle_sign(sign, hanging):
    name = "hanging_sign" if hanging else "sign"
    block_counts.setdefault(name, 1)
    translation_cnt = len(rel_lang)

    if not hanging and 'Text1' in sign:
        set_key(f"block.sign.{block_counts['sign']}.text1")
        sign['Text1'] = replace_component(sign['Text1'], cfg_dupe["signs"])
        set_key(f"block.sign.{block_counts['sign']}.text2")
        sign['Text2'] = replace_component(sign['Text2'], cfg_dupe["signs"])
        set_key(f"block.sign.{block_counts['sign']}.text3")
        sign['Text3'] = replace_component(sign['Text3'], cfg_dupe["signs"])
        set_key(f"block.sign.{block_counts['sign']}.text4")
        sign['Text4'] = replace_component(sign['Text4'], cfg_dupe["signs"])
    else:
        # for 1.19+
        if 'front_text' in sign:
            for i in range(len(sign['front_text']['messages'])):
                set_key(f"block.{name}.{block_counts[name]}.front_text{i + 1}")
                sign['front_text']['messages'][i] = replace_component(sign['front_text']['messages'][i], cfg_dupe["signs"])
        if 'back_text' in sign:
            for i in range(len(sign['back_text']['messages'])):
                set_key(f"block.{name}.{block_counts[name]}.back_text{i + 1}")
                sign['back_text']['messages'][i] = replace_component(sign['back_text']['messages'][i], cfg_dupe["signs"])

    if translation_cnt != len(rel_lang):
        block_counts[name] += 1

    return True


def handle_spawner(spawner):
    changed = False
    try:
        spawn_data_key = 'entity' if not OLD_SPAWNER_FORMAT else None
        
        spawn_data_changed = handle_entity(spawner['SpawnData'][spawn_data_key] if spawn_data_key else spawner['SpawnData'], None)
        if spawn_data_changed: changed = True

        for p in spawner['SpawnPotentials']:
            potential_key = 'data' if not OLD_SPAWNER_FORMAT else 'Entity'
            potential_changed = handle_entity(p[potential_key]['entity'] if potential_key == 'data' else p[potential_key], None)
            if potential_changed: changed = True
    except KeyError:
        pass
    return changed

def handle_entity(entity, type=None):
    def update_entity_key(entity_id, count, key, replace_cfg):
        set_key(f"entity.{entity_id}.{count}.{key}")
        entity[key] = replace_component(entity[key], replace_cfg)
        return True

    def handle_items(items):
        for item in items:
            if handle_item(item): return True
        return False

    if type: entity_id = type
    else: entity_id = str(entity.get('id', 'unknown'))[10:]

    entity_counts.setdefault(entity_id, 1)
    initial_translation_cnt = len(rel_lang)
    changed = False

    for key, cfg in (('CustomName', cfg_dupe["entities_name"]), ('text', cfg_dupe["show_entity_text"])):
        if key in entity:
            changed = update_entity_key(entity_id, entity_counts[entity_id], key, cfg) or changed

    if initial_translation_cnt != len(rel_lang):
        entity_counts[entity_id] += 1

    item_keys = ["Items", "ArmorItems", "HandItems", "Item", "Inventory"]
    for item_key in item_keys:
        if item_key in entity:
            changed = handle_items(entity[item_key]) or changed

    if "Offers" in entity and "Recipes" in entity["Offers"]:
        for recipe in entity["Offers"]["Recipes"]:
            changed = handle_item(recipe.get('buy')) or changed
            changed = handle_item(recipe.get('buyB')) or changed
            changed = handle_item(recipe.get('sell')) or changed

    if "Passengers" in entity:
        for passenger in entity["Passengers"]:
            changed = handle_entity(passenger) or changed

    if 'item' in entity:
        changed = handle_item(entity['item']) or changed

    return changed

def handle_beehive(beehive):
    changed = False
    if 'Bees' in beehive:
        for bee in beehive['Bees']:
            changed = handle_entity(bee['EntityData'], None) or changed
    return changed


def handle_block_entity_base(block_entity, name):
    match name:
        case "spawner":
            return handle_spawner(block_entity)
        case name if name in CONTAINERS:
            return handle_container(block_entity, name)
        case "sign":
            return handle_sign(block_entity, False)
        case "hanging_sign":
            return handle_sign(block_entity, True)
        case "lectern":
            return handle_item_entity_block(block_entity, "Book")
        case "jukebox":
            return handle_item_entity_block(block_entity, "RecordItem")
        case "decorated_pot":
            return handle_item_entity_block(block_entity, "item")
        case "command_block":
            return handle_command_block(block_entity)
        case "beehive", "bee_nest":
            return handle_beehive(block_entity)
        case _:
            return False

def handle_block_entity_nbt(block_entity, id):
    changed = handle_block_entity_base(block_entity, str(id)[10:])  # after "minecraft:"
    if changed:
        print(f"[block entity nbt handler] {str(id)[10:]}: (Structure/ItemLike)")
        print('---------------------------')
    return changed


def handle_block_entity(block_entity, dimension):
    if not WP_FILTER.filter(dimension, block_entity.x, block_entity.y, block_entity.z):
        return False
    nbt = block_entity.nbt.tag['utags']
    changed = handle_block_entity_base(nbt, block_entity.base_name)
    if changed:
        print(f"[block entity handler] {block_entity.base_name}: (/tp {block_entity.x} {block_entity.y} {block_entity.z})")
        print('---------------------------')
    return changed


def handle_chunk(chunk, dimension):
    for block_entity in chunk.block_entities:
        chunk.changed |= handle_block_entity(block_entity, dimension)


def handle_entities(level, coords, dimension, entities):
    changed = False
    for e in entities:
        if not WP_FILTER.filter(dimension, e.x, e.y, e.z):
            continue
        changed |= handle_entity(e.nbt.tag, e.base_name)
        if changed:
            print(f"[entity handler] {e.base_name}: (/tp {e.x} {e.y} {e.z})")
            print('---------------------------')
    if changed:
        level.set_native_entites(coords[0], coords[1], dimension, entities)


# scanner
def scan_world(level):
    from tqdm import tqdm

    threshold = cfg_settings["save_threshold"]
    for dimension in level.dimensions:
        chunk_coords = sorted(level.all_chunk_coords(dimension))
        if len(chunk_coords) < 1: continue
        print(f"Dimension {dimension}: ")
        try:
            count = 0
            for coords in tqdm(chunk_coords, unit=lang.t("main.chunks"), desc=lang.t("main.scan_chunks"), colour="green"):
                try:
                    chunk = level.get_chunk(coords[0], coords[1], dimension)
                    entities = level.get_native_entities(coords[0], coords[1], dimension)[0]
                except Exception:
                    pass
                else:
                    handle_chunk(chunk, dimension)
                    handle_entities(level, coords, dimension, entities)
                    count += 1
                    if count < threshold:
                        continue
                    count = 0
                    print(lang.t("main.saving"))
                    level.save()
                    level.unload()
            level.save()
        except KeyboardInterrupt:
            print(lang.t("main.interrupted", threshold=threshold))
            level.close()
            exit(0)
        level.unload()
    level.close()



def scan_scores(path):
    try:
        scores = amulet_nbt.load(path)
        
        for s in scores.tag['data']['Objectives']:
            set_key(f"score.{s['Name']}.name")
            s['DisplayName'] = replace_component(s['DisplayName'], cfg_dupe["scores_name"] | cfg_dupe["scores_all"])
        
        for t in scores.tag['data']['Teams']:
            set_key(f"score.{t['Name']}.name")
            t['DisplayName'] = replace_component(t['DisplayName'], cfg_dupe["scores_teams_name"] | cfg_dupe["scores_all"])
            
            set_key(f"score.{t['Name']}.prefix")
            t['MemberNamePrefix'] = replace_component(t['MemberNamePrefix'], cfg_dupe["scores_teams_prefix"] | cfg_dupe["scores_all"])
            
            set_key(f"score.{t['Name']}.suffix")
            t['MemberNameSuffix'] = replace_component(t['MemberNameSuffix'], cfg_dupe["scores_teams_suffix"] | cfg_dupe["scores_all"])
        scores.save_to(path)
    
    except Exception as e:
        print(lang.t("main.noscoreboard_data", e=e))

def scan_level(path):
    try:
        level = amulet_nbt.load(path)
        for b in level.tag['Data']['CustomBossEvents']:
            set_key(f"bossbar.{b}.name")
            level.tag['Data']['CustomBossEvents'][b]['Name'] = replace_component(
                level.tag['Data']['CustomBossEvents'][b]['Name'], cfg_dupe["bossbar"])
        level.save_to(path)
    except Exception as e:
        print(lang.t("main.nobossbar_data", e=e))


def scan_structure(path):
    try:
        structure = amulet_nbt.load(path)
        for b in structure.tag['blocks']:
            handle_block_entity_nbt(b['nbt'], b['nbt']['id'])
        for e in structure.tag['entities']:
            handle_entity(e['nbt'], None)
        structure.save_to(path)
    except Exception as e:
        print(lang.t("main.nostructure", e=e))

def scan_command_storages(path):
    for root, _, files in os.walk(path):
        for f in files:
            if f.startswith("command_storage"):
                # "(command_storage_)minecraft(.dat)"
                scan_command_storage(os.path.join(root, f), f[16:-4])


def scan_command_storage(path, namespace):
    try:
        data = amulet_nbt.load(path)
        ctx = data.tag['data']['contents']
        for c in ctx:
            traverse_tags(c, ctx[c], namespace, "")
        data.save_to(path)
    except Exception as e:
        print(lang.t("main.nocommand", e=e))


def traverse_tags(c, tag, namespace, path):
    if c is not None:
        path = path + ("." if path else "") + c
    for key1 in tag:
        k = str(key1)
        path_ = path + "." + k
        next_data = tag[k]
        if isinstance(next_data, amulet_nbt.ListTag):
            for i in range(len(next_data)):
                path__ = path_ + "[" + str(i) + "]"
                e = next_data[i]
                if isinstance(e, amulet_nbt.StringTag):
                    if CS_FILTER.filter(namespace, path__):
                        set_key("command_storage." + path__)
                        e = replace_component(e, cfg_dupe["command_storage"])
                elif isinstance(e, amulet_nbt.CompoundTag):
                    traverse_tags(None, e, namespace, path__)
                else:
                    break
                next_data[i] = e
        elif isinstance(next_data, amulet_nbt.CompoundTag):
            traverse_tags(None, next_data, namespace, path_)
        elif isinstance(next_data, amulet_nbt.StringTag):
            if CS_FILTER.filter(namespace, path_):
                set_key("command_storage." + path_)
                next_data = replace_component(next_data, cfg_dupe["command_storage"])
        else:
            continue
        tag[k] = next_data

def scan_file(file_path: str, base_path: pathlib.Path):
    try:
        path_obj = pathlib.Path(file_path)
        if path_obj.suffix == ".nbt":
            scan_structure(file_path)
            return
        
        if path_obj.suffix not in (".mcfunction", ".json"):
            return
        
        # 计算相对路径并转换为键名格式
        relative_path = path_obj.relative_to(base_path)
        key_name = relative_path.with_suffix("").as_posix().replace("/", ".")

        set_key(key_name)

        with open(file_path, 'r', encoding="utf-8") as f:
            lines = f.readlines()
        
        modified_lines = []

        for i, line in enumerate(lines):
            if line.startswith('#'):  # 如果是注释行，则跳过
                modified_lines.append(line)
                continue

            is_marco = line.startswith('$')  # 判断是否是宏命令

            # 使用正确的参数名称 'is_marco'
            txt = sub_replace(SREG_COMPONENT_ESCAPED, line, match_text, cfg_dupe["datapacks"], is_marco=is_marco)
            txt = sub_replace(REG_COMPONENT_DOUBLE_ESCAPED, txt, match_text_double_escaped, cfg_dupe["datapacks"], is_marco=is_marco)
            txt = sub_replace(REG_COMPONENT_ESCAPED, txt, match_text_escaped, cfg_dupe["datapacks"], is_marco=is_marco)
            txt = sub_replace(SREG_COMPONENT, txt, match_text, cfg_dupe["datapacks"], is_marco=is_marco)
            txt = sub_replace(REG_COMPONENT, txt, match_text, cfg_dupe["datapacks"], is_marco=is_marco)
            txt = sub_replace(REG_DATAPACK_CONTENTS, txt, match_contents, cfg_dupe["datapacks"])

            txt = sub_replace(SREG_ADV_TITLE, txt, match_advancement_title, cfg_dupe["advancements"])
            txt = sub_replace(SREG_ADV_DESC, txt, match_advancement_desc, cfg_dupe["advancements"])

            txt = sub_replace(SREG_CMD_BOSSBAR_SET_NAME, txt, match_bossbar, cfg_dupe["datapacks"], is_marco=is_marco)
            txt = sub_replace(SREG_CMD_BOSSBAR_ADD, txt, match_bossbar2, cfg_dupe["datapacks"], is_marco=is_marco)

            modified_lines.append(txt)

            # 搜索目标选择器名称
            m = SREG_RECORD_NAME_TARGET_SELECTOR.search(txt)
            if m:
                print(f"[record] Datapack {path_obj.relative_to(base_path)}, target Selector Name: Line {i}")

        # 将修改后的内容写回文件
        with open(file_path, 'w', encoding="utf-8") as f:
            f.writelines(modified_lines)

    except Exception as e:
        print(lang.t("main.replace_datapack", file_path=file_path, e=e))

def scan_datapacks(path: str):
    path_obj = pathlib.Path(path)
    for root, _, files in os.walk(path_obj):
        for f in files:
            file_path = pathlib.Path(root) / f
            scan_file(file_path, path_obj)

# main
def clearup_keys():
    global mix_lang
    mix_lang = {}
    mixed = {}
    for k in rel_lang:
        v: MetaDict.Metadata = rel_lang.get(k)
        if v.dupe or v.value not in mixed.values():
            mixed[v.key] = v.value
    mix_lang = mixed


def gen_lang(path: str):
    obj = json.dumps(rel_lang, indent=cfg_lang["indent"], ensure_ascii=cfg_lang["ensure_ascii"], sort_keys=cfg_lang["sort_keys"])
    with open(path + "_original.json", 'w', encoding="utf-8") as f:
        f.write(obj)

    obj = json.dumps(mix_lang, indent=cfg_lang["indent"], ensure_ascii=cfg_lang["ensure_ascii"], sort_keys=cfg_lang["sort_keys"])
    with open(path + "_cleared.json", 'w', encoding="utf-8") as f:
        f.write(obj)

def backup_saves(path: str, source: str):
    try:
        import shutil
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.exists(path):
            shutil.rmtree(path)
        shutil.copytree(source, path)
    except Exception as e:
        print(lang.t("main.error_backup", e=e))
        exit(1)

def pause():
    # Windows
    if os.name == 'nt': 
        os.system('pause')
    else:
        input(lang.t("main.pause"))

def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as file_cfg:
            config = json.loads(file_cfg.read())
            return config
    except Exception as e:
        print(lang.t("main.error_config", e=e))
        pause()

def main():
    world_path = input(lang.t("main.input"))
    if not os.path.isdir(world_path):
        print(lang.t("main.notdir")) 
        pause()
        exit(1)
    config = load_config()

    global cfg_settings, cfg_lang, cfg_dupe, cfg_default, cfg_filters
    cfg_settings = config["settings"]
    cfg_lang = cfg_settings["lang"]
    cfg_dupe = cfg_settings["keep_duplicate_keys"]
    cfg_default = cfg_settings["default_keys"]
    cfg_filters = cfg_settings["filters"]
    
    global DISABLE_COMPONENTS_LIMIT, DISABLE_MARCOS_LIMIT
    DISABLE_COMPONENTS_LIMIT = cfg_settings['components_max'] == -1
    DISABLE_MARCOS_LIMIT = cfg_settings['marcos_max'] == -1
    
    for f in cfg_filters['command_storages']:
        CS_FILTER.add(f['mode'], f['namespace'], f['path'])
    for f in cfg_filters['world_positions']:
        WP_FILTER.add(f['mode'], f['world'], f['start'], f['end'])

    if cfg_settings.get("backup"):
        backup_name = os.path.basename(os.path.abspath(world_path))
        backup_path = os.path.join(os.path.abspath('.'), f"backup_{backup_name}")
        print(lang.t("main.backup", backup_path=backup_path))
        backup_saves(backup_path, world_path)

    rev_lang.update({k: cfg_default for k in cfg_default})
    for k in cfg_default:
        rel_lang.put(cfg_default[k], k, True)

    print(lang.t("main.scanning_chunks"))
    try:
        import amulet
        level = amulet.load_level(world_path)
        if level.level_wrapper.version < 2826:
            global OLD_SPAWNER_FORMAT
            OLD_SPAWNER_FORMAT = True
            print(lang.t("main.old_spawner_format"))
        scan_world(level)
    except Exception as e:
        print(lang.t("main.error_loading", e=e))
        exit(1)

    print(lang.t("main.scanning_nbt"))
    scan_command_storages(os.path.join(world_path, "data"))
    scan_scores(os.path.join(world_path, "data", "scoreboard.dat"))
    scan_level(os.path.join(world_path, "level.dat"))

    print(lang.t("main.scanning_datapack"))
    scan_datapacks(os.path.join(world_path, "datapacks"))
    scan_datapacks(os.path.join(world_path, "generated"))

    print(lang.t("main.remove_redundant"))
    clearup_keys()

    print(lang.t("main.gen_lang"))
    gen_lang(cfg_lang["file_name"])

    print(lang.t("main.done"))

if __name__ == "__main__":
    import sys
    py_version = sys.version_info
    # 用到match case和:=运算符等特性为Python 3.10+新功能
    # locale.getdefaultlocale已弃用，将在Python 3.15（2026年）删除 -> const.py
    if not (3, 10) < py_version < (3, 15):
        print(lang.t("main.unsupported_version", 
                       cur=f"{py_version.major}.{py_version.minor}.{py_version.micro}"))
        pause()

    print(f'''
WTH v{__version__} By {__author__}
Core: Amulet
Credits: Suso, 3093FengMing''')
    main()
    