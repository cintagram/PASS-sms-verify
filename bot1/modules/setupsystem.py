import os
from . import config

def write_file_if_not_exists(file_path, content=""):
    if not os.path.exists(file_path):
        with open(file_path, "a+", encoding="utf-8") as file:
            file.write(content)

def bootup():
    capt_dir = os.path.join(config.DB_Path, "captchas")
    if not os.path.exists(capt_dir):
        os.mkdir(capt_dir)
    db_files = [
        {"path": os.path.join(config.DB_Path, "guild_manager.csv"), "content": "GuildID,Permitted,LogChnlID,LicenseKey,RoleID,WebhookLink,BTN\n"},
        {"path": os.path.join(config.DB_Path, "license.csv"), "content": "LicenseKey,LicenseDay,ValidUntil,AssignedGuildID\n"},
        {"path": os.path.join(config.DB_Path, "srvbl.json"), 'content': r'{"test_guildid": {"userid": [], "name": [], "phone": []}}'},
        {"path": os.path.join(config.DB_Path, "whitelist.json"), 'content': r'{"userid": [], "name": [], "phone": []}'}
    ]

    for file_info in db_files:
        write_file_if_not_exists(file_info["path"], file_info.get("content", ""))
