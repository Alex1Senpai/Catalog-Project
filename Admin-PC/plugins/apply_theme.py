import flet as ft
import os
import json

def apply_themes(page: ft.Page):
    # Загружаем тему из файла
    theme_settings_path = r"C:\serverShiDari\theme_settings.json"
    if os.path.exists(theme_settings_path):
        try:
            with open(theme_settings_path, "r") as f:
                theme_data = json.load(f)
                page.theme_mode = theme_data.get("theme", "dark")  # По умолчанию "dark"
        except Exception as e:
            print(f"Ошибка при чтении файла темы: {e}")
            page.theme_mode = "dark"  # Если произошла ошибка, используем тему по умолчанию
    else:
        page.theme_mode = "dark"