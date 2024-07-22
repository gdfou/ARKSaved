# ARKSave
Script de sauvegarde et restitue une sauvegarde locale de ARK ASE ou ASA.
Ce script nécessite python version 3 minimum.

Il compresse le dossier 'Saved' d'ARK et le stocke dans le dossier de sauvegarde.
A la restitution d'une sauvegarde, il supprime le dossier 'Saved' et le remplace par la version sauvegardée.

## Installation
`pip install -r requirements.txt`
ou
`python -m pip install -r requirements.txt`

## Configuration
La configuration passe par un fichier au format json qui l'on donne en argument du script.

Pour créer le fichier de configuration 'asa.json', taper simplement:
`python save-ark.py asa.json`

Editer le fichier de config:
- `game_ark_dir = "C:/Program Files (x86)/Steam/steamapps/common/ARK Survival Ascended/ShooterGame/"` doit pointer sur le dossier d'ARK contenant le dossier 'Saved'.
- `save_dir = "J:/ARK/Saved_ASA"` doit pointer vers l'emplacement des sauvegardes.
- `backup_limit = 30` définit le nombre max d'archives à garder.

```json
{
  "game_ark_dir": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\ARK Survival Ascended\\ShooterGame",
  "save_dir": "J:\\ARK\\Saved",
  "backup_limit": 30
}
```

## Utilisation
`python save-ark.py <fichier de config>`
`python save-ark.py asa.json`
