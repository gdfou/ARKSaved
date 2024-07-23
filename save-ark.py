# Version 1.1
import io, os, sys, fnmatch, pathlib, shutil, datetime, re
import json
from pathlib import Path
from consolemenu.prompt_utils import PromptFormatter, UserQuit
from consolemenu.validators.base import BaseValidator
from py7zr import FILTER_LZMA, FILTER_LZMA2, PRESET_DEFAULT, SevenZipFile, ArchiveInfo
from consolemenu import *
from consolemenu.items import *

# Création d'un archive du dossier de sauvegarde ARK
# game_ark_dir: C:\Program Files (x86)\Steam\steamapps\common\ARK\ShooterGame
# game_ark_dir: C:\Program Files (x86)\Steam\steamapps\common\ARK Survival Ascended\ShooterGame
# save_dir: J:\ARK\Saved_ASA
# nomage des fichiers: Saved.<index>.<name>.7z
# backup_limit = 30

# la configuration passe par un fichier json en argument
if len(sys.argv) == 1:
    print("Le script nécessite un fichier de configuration")
    sys.exit(1)

if len(sys.argv) == 2 and not os.path.isfile(sys.argv[1]):
    print(f"Le fichier de configuration '{sys.argv[1]}' a été créé.")
    print("Editez-le pour le mettre à jour avec les bonnes valeurs.")
    json_out = {}
    json_out["game_ark_dir"] = "C:\Program Files (x86)\Steam\steamapps\common\ARK Survival Ascended\ShooterGame"
    json_out["save_dir"] = "J:\ARK\Saved_ASA"
    json_out["backup_limit"] = 30
    with io.open(sys.argv[1], mode="w", encoding="utf-8") as json_file:
        json.dump(json_out, json_file, ensure_ascii=False, indent="  ")
    sys.exit(2)

# load config
json_in = {}
with io.open(sys.argv[1], mode="r", encoding="utf-8") as file_in:
    json_in = json.load(file_in)

# check
if not json_in.get('game_ark_dir'):
    print("Le fichier de configuration ne contient pas de champ 'game_ark_dir'")
    sys.exit(3)
if not json_in.get('save_dir'):
    print("Le fichier de configuration ne contient pas de champ 'save_dir'")
    sys.exit(3)
if not json_in.get('backup_limit'):
    print("Le fichier de configuration ne contient pas de champ 'backup_limit'")
    sys.exit(3)

game_ark_dir = json_in['game_ark_dir']
save_dir = json_in['save_dir']
backup_limit = json_in['backup_limit']

def get_file_timestamp(fullfilename):
    filedate = pathlib.Path(fullfilename).stat().st_mtime
    return datetime.datetime.fromtimestamp(filedate).strftime("%d/%m/%y %H:%M:%S")

def build_item(fullfilename):
    # format nom pour la liste: Saved.<index>.<name>.7z => <index> '<name>'
    strs = Path(os.path.basename(fullfilename)).stem.split('.')
    index = int(strs[1])
    name = strs[2] if len(strs) == 3 else None
    print_name = f"{strs[1]} '{name}'" if name != None else strs[1]
    return {'filename':fullfilename, 'datetime':get_file_timestamp(fullfilename), 'index':index, 'name':name, 'print_name':print_name}

def sort_by_index(list):
    return list['index']

def find_with_timestamps(pattern, path):
    result = []
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            if fnmatch.fnmatch(item, pattern):
                result.append(build_item(os.path.join(path, item)))
    result.sort(key=sort_by_index)
    return result

def copy_file(dir, name, new_name):
    filename = os.path.join(dir, name)
    if os.path.isfile(filename):
        new_filename = os.path.join(dir, new_name)
        os.rename(filename, new_filename)
        print(f"Copie de {filename} vers {new_filename}")

def rename_save(item, new_index=None, new_name=None):
    if new_index == None:
        new_index = item['index']
    if new_name == None:
        new_name = item['name']
    base_dir = os.path.dirname(item['filename'])
    new_filename = f"Saved.{(new_index):02d}.{new_name}.7z" if new_name != None else f"Saved.{(new_index):02d}.7z"
    new_fullfilename = os.path.join(base_dir, new_filename)
    if os.path.isfile(new_fullfilename):
        os.remove(new_fullfilename)
    filename = item['filename']
    print(f"Rename {filename} to {new_fullfilename}")
    os.rename(filename, new_fullfilename)

def backup(list):
    # "Saved.<index>.<name>.7z" -> "Saved.<index+1>.<name>.7z" avec une limite 
    print(f"Backup limite : {backup_limit}")
    list.sort(key=sort_by_index, reverse=True)
    for item in list:
        filename = item['filename']
        index = item['index']
        name = item['name']
        if index < backup_limit:
            rename_save(item, index+1)

def build_archive():
    print("Construction de l'archive 'Saved.00.7z'")
    os.chdir(game_ark_dir)
    filters = [{'id': FILTER_LZMA, 'preset': 0}]
    with SevenZipFile(os.path.join(save_dir,'Saved.00.7z'), mode='w', filters=filters) as archive:
        archive.writeall("Saved/")
    print("ok")

def save(list):
    backup(list)
    build_archive()
    input("Appuyez sur une touche pour continuer...")
    exit()

def remove_saved_dir(onlyLocal: bool=False):
    saved_dir = os.path.join(game_ark_dir, "Saved")
    if onlyLocal:
        sub_folder = os.path.join(saved_dir, "LocalProfiles")
        if os.path.exists(sub_folder):
            shutil.rmtree(sub_folder, onerror=True)
        sub_folder = os.path.join(saved_dir, "SavedArksLocal")
        if os.path.exists(sub_folder):
            shutil.rmtree(sub_folder, onerror=True)
    else:
    if os.path.exists(saved_dir):
        shutil.rmtree(saved_dir, onerror=True)

def restore_only_local(filename):
    remove_saved_dir(True)
    print(f"RESTAURATION DES DOSSIERS 'LocalProfiles' et 'SavedArksLocal' DE LA PARTIE '{os.path.basename(filename)}'")
    archive = SevenZipFile(filename, mode='r')
    allfiles = archive.getnames()
    filter_pattern = re.compile(r'Saved/LocalProfiles.*')
    folder_list = [f for f in allfiles if filter_pattern.match(f) ]
    archive.extract(path=game_ark_dir, targets=folder_list)
    archive.reset()
    filter_pattern = re.compile(r'Saved/SavedArksLocal.*')
    folder_list = [f for f in allfiles if filter_pattern.match(f) ]
    archive.extract(path=game_ark_dir, targets=folder_list)
    archive.close()
    print("ok")
    input("Appuyez sur une touche pour continuer...")
    exit()

def restore_full(filename):
    remove_saved_dir()
    print(f"RESTAURATION DE LA PARTIE '{os.path.basename(filename)}'")
    archive = SevenZipFile(filename, mode='r')
    archive.extractall(path=game_ark_dir)
    archive.close()
    print("ok")
    input("Appuyez sur une touche pour continuer...")
    exit()

def restore_specific(filename, full_restore):
    if full_restore:
        restore_full(filename)
    else:
        restore_only_local(filename)

class SaveNameValidator(BaseValidator):
    def validate(self, input_string):
        return False if '.' in input_string else True

def rename_current(item):
    save_name_validator = SaveNameValidator()
    menu_prompt = PromptUtils(screen=Screen())
    name = item['name']
    try:
        if name != None:
            menu_prompt.println(f"Nom actuel: '{name}'")
        new_name = menu_prompt.input(prompt="Entrée le nom de la sauvegarde", validators=save_name_validator, enable_quit=True)
    except UserQuit:
        return
    if new_name.validation_result and len(new_name.input_string) > 0:
        # renomme 'Saved.00.7z' ou 'Saved.00.<name>.7z' en 'Saved.00.<new_name>.7z'
        print(new_name.input_string)
        rename_save(item, new_name=new_name.input_string)
        exit()
    else:
        menu_prompt.println("Erreur dans le nom")
        menu_prompt.enter_to_continue()

def build_menu():
    list = find_with_timestamps("Saved.*.7z", save_dir)

    menu = ConsoleMenu("Sauvegarder ou restaurer une partie de ARK")
    
    # Sauvegarder la partie courante
    menu.append_item(FunctionItem("Sauvegarder la partie courante", save, args=[list]))

    # Renommer la partie courante
    if len(list) > 0:
        menu.append_item(FunctionItem("Renommer la partie courante", rename_current, args=[list[0]]))

        # Restaurer la dernière sauvegarde (index 00)
        restore_last_title = f"Restaurer la dernière sauvegarde ({list[0]['datetime']})"
        restore_last_submenu = ConsoleMenu(restore_last_title)

        title_1 = "Restaurer LocalProfiles/SavedArksLocal de la sauvegarde."
        title_2 = "Restaurer complètement la sauvegarde."
        restore_last_submenu.append_item(FunctionItem(title_1, restore_specific, args=[list[0]['filename'],False]))
        restore_last_submenu.append_item(FunctionItem(title_2, restore_specific, args=[list[0]['filename'],True]))
        menu.append_item(SubmenuItem(restore_last_title, restore_last_submenu))

        # Restaurer une partie spécifique - local
        restore_submenu_title = "Restaurer LocalProfiles/SavedArksLocal d'une partie spécifique"
        restore_submenu = ConsoleMenu(restore_submenu_title)
        # compute string length
        str_item_len = 0
        for file_item in list:
            str_item_len = max(str_item_len, len(file_item['print_name']))
        # build menu
        for file_item in list:
            item_name = f"{file_item['print_name']:<{str_item_len}} - {file_item['datetime']}"
            restore_submenu.append_item(FunctionItem(item_name, restore_specific, args=[file_item['filename'],False]))
        menu.append_item(SubmenuItem(restore_submenu_title, restore_submenu, menu))

        # Restaurer une partie spécifique - complète
        restore_submenu_title = "Restaurer complètement une partie spécifique"
        restore_submenu = ConsoleMenu(restore_submenu_title)
        # compute string length
        str_item_len = 0
        for file_item in list:
            str_item_len = max(str_item_len, len(file_item['print_name']))
        # build menu
        for file_item in list:
            item_name = f"{file_item['print_name']:<{str_item_len}} - {file_item['datetime']}"
            restore_submenu.append_item(FunctionItem(item_name, restore_specific, args=[file_item['filename'],True]))
        menu.append_item(SubmenuItem(restore_submenu_title, restore_submenu, menu))

    menu.show()

build_menu()