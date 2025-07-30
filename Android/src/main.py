import flet as ft
import aiohttp
import sqlite3
import bcrypt
import time
from pages.home import home_page # Предполагается, что этот файл существует
from pathlib import Path
import asyncio
import os

# Конфигурация сервера
SERVER_IP = "IP"
SERVER_PORT = "PORT"
SCAN_INTERVAL = 60

# Пути для файлов
BASE_DIR = Path(os.getenv("ANDROID_PRIVATE", "")) # ANDROID_PRIVATE обычно указывает на files dir
SAVE_DIR = BASE_DIR / "backend"
SAVE_DIR.mkdir(exist_ok=True)
DEFAULT_DB_PATH = SAVE_DIR / "back.db"
IMGS_DIR = SAVE_DIR / "Imgs"
IMGS_DIR.mkdir(exist_ok=True)
LAST_SYNC_PATH = SAVE_DIR / "last_sync.txt"
HISTORY_DIR = SAVE_DIR / "history"
HISTORY_DIR.mkdir(exist_ok=True)
EXTERNAL_SELECTED_DIR = "external_selected_dir"

async def get_server_db_hash():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{SERVER_IP}:{SERVER_PORT}/db_hash") as response:
                return await response.text()
    except Exception as e:
        print(f"Ошибка получения хеша БД с сервера: {e}")
        return None

def get_local_db_hash():
    return open(LAST_SYNC_PATH, "r").read() if LAST_SYNC_PATH.exists() else ""

async def download_db():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{SERVER_IP}:{SERVER_PORT}/download_db") as response:
                with open(DEFAULT_DB_PATH, "wb") as f:
                    f.write(await response.read())
                print("DB downloaded successfully")
    except Exception as e:
        print(f"DB download failed: {e}")

async def download_imgs():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{SERVER_IP}:{SERVER_PORT}/list_imgs") as response:
                if response.ok:
                    files = (await response.json()).get("files", [])
                    print(f"Files to download: {files}")

                    for file in files:
                        start_time = time.time()
                        img_url = f"http://{SERVER_IP}:{SERVER_PORT}/download_img/{file}"
                        async with session.get(img_url) as img_response:
                            if img_response.status == 200:
                                img_data = await img_response.read()
                                (IMGS_DIR / file).write_bytes(img_data)
                                end_time = time.time()
                                file_size = len(img_data) / 1024
                                print(
                                    f"Изображение {file} скачано за {end_time - start_time:.2f} секунд. Размер: {file_size:.2f} КБ"
                                )
                            else:
                                print(f"Ошибка при скачивании {file}. Статус: {img_response.status}")
                else:
                    print(f"Ошибка при получении списка файлов. Статус: {response.status}")
    except Exception as e:
        print(f"Ошибка при скачивании изображений: {e}")

async def check_server():
    try:
        server_hash = await get_server_db_hash()
        local_hash = get_local_db_hash()

        if server_hash and server_hash != local_hash:
            await download_db()
            await download_imgs()
            with open(LAST_SYNC_PATH, "w") as f:
                f.write(server_hash)
    except Exception as e:
        print(f"Ошибка при проверке сервера и синхронизации: {e}")
        # raise # Можно не пробрасывать ошибку дальше, чтобы приложение не падало полностью

def select_external_folder(page: ft.Page):
    def on_result(e: ft.FilePickerResultEvent):
        if e.path:
            page.session.set(EXTERNAL_SELECTED_DIR, e.path)
            page.snack_bar = ft.SnackBar(ft.Text(f"Папка выбрана: {e.path}"))
            page.snack_bar.open = True
            page.update()

    picker = ft.FilePicker(on_result=on_result)
    page.overlay.append(picker)
    picker.get_directory_path()

async def main(page: ft.Page):
    try:
        await loading(page) # Загрузка и проверка разрешений/синхронизации
        login_page(page)    # Затем страница логина
        page.update()
    except Exception as e:
        print(f"Critical error in main: {e}")
        error_text = f"Критическая ошибка в приложении: {e}"
        try:
            # Попытка показать SnackBar, если page еще доступен
            snack_bar = ft.SnackBar(ft.Text(error_text), open=True)
            if page.overlay: # SnackBar обычно добавляется в page.overlay или page.snack_bar
                page.open(snack_bar) # или page.open(snack_bar) в зависимости от версии Flet
            else:
                page.add(ft.Text(error_text)) # Как запасной вариант, если overlay недоступен
            page.update()
        except Exception as E_SNACK:
            print(f"Could not display error in UI: {E_SNACK}")

async def loading(page: ft.Page):
    progress_ring = ft.ProgressRing(width=50, height=50, stroke_width=3)
    loading_container = ft.Container(
        content=ft.Column(
            [progress_ring, ft.Text("Загрузка данных...")],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.GREY_300)
    )
    
    page.overlay.append(loading_container)
    page.update()

    try:
        # Сначала: проверка и синхронизация с сервером
        await check_server()

        # Потом: проверка выбора внешней папки
        if not page.session.get(EXTERNAL_SELECTED_DIR):
            print("Папка не выбрана, запрашиваем у пользователя выбор директории...")

            picker_result = asyncio.Future()

            def on_result(e: ft.FilePickerResultEvent):
                if e.path:
                    page.session.set(EXTERNAL_SELECTED_DIR, e.path)
                    snack_bar = ft.SnackBar(ft.Text(f"Папка выбрана: {e.path}"), open=True)
                    page.open(snack_bar)
                    page.update()
                picker_result.set_result(True)

            picker = ft.FilePicker(on_result=on_result)
            page.overlay.append(picker)
            picker.get_directory_path()

            # Ожидание выбора папки
            await picker_result

    except Exception as e:
        snack_bar = ft.SnackBar(ft.Text(f"Ошибка при загрузке: {e}"), open=True)
        try:
            page.open(snack_bar)
        except:
            print(f"Не удалось показать SnackBar: {e}")
    finally:
        if loading_container in page.overlay:
            page.overlay.remove(loading_container)
        page.update()

async def upload_contracts():
    contracts_dir = HISTORY_DIR # Используем HISTORY_DIR как указано
    if not contracts_dir.exists():
        print(f"Директория для договоров {contracts_dir} не найдена.")
        return

    try:
        async with aiohttp.ClientSession() as session:
            found_files = False
            for contract_file in contracts_dir.glob("*.xlsx"):
                found_files = True
                print(f"Отправка файла: {contract_file.name}")
                with open(contract_file, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "file",
                        f,
                        filename=contract_file.name,
                        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    async with session.post(
                        f"http://{SERVER_IP}:{SERVER_PORT}/upload_contract",
                        data=data
                    ) as response:
                        if response.status == 200:
                            print(f"Файл {contract_file.name} успешно отправлен.")
                            # Опционально: удалить файл после успешной отправки или переместить
                            # contract_file.unlink()
                        else:
                            response_text = await response.text()
                            print(f"Ошибка отправки {contract_file.name}. Статус: {response.status}. Ответ: {response_text}")
            if not found_files:
                print(f"Файлы .xlsx для отправки не найдены в {contracts_dir}")
    except Exception as e:
        print(f"Ошибка при отправке договоров: {e}")

def login_page(page: ft.Page):
    def check_login(username, password):
        if not DEFAULT_DB_PATH.exists():
            print(f"База данных не найдена по пути: {DEFAULT_DB_PATH}")
            return False, None
            
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT password, full_name FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False, None

        stored_hash_str = result[0]
        if isinstance(stored_hash_str, bytes):
            stored_hash = stored_hash_str
        else:
            stored_hash = stored_hash_str.encode('utf-8')
            
        full_name = result[1]

        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash), full_name
        except Exception as e:
            print(f"Ошибка при проверке пароля bcrypt: {e}")
            return False, None

    async def on_login_click(e):
        username = user_login.current.value
        password = user_pass.current.value

        success, full_name = check_login(username, password)
        if success:
            page.session.set("full_name", full_name)
            page.session.set("username", username)
            
            print(f"Пользователь {full_name} ({username}) успешно вошел в систему.")
            
            loading_indicator_container = ft.Container(
                ft.ProgressRing(), 
                alignment=ft.alignment.center, 
                expand=True, 
                bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK12) # Полупрозрачный фон
            )
            page.overlay.append(loading_indicator_container)
            page.update()

            await upload_contracts() 
            
            if loading_indicator_container in page.overlay:
                page.overlay.remove(loading_indicator_container)
            
            page.clean()
            home_page(page) 
        else:
            snack_bar = ft.SnackBar(
                content=ft.Text("Неверный логин или пароль"),
            )
            page.open(snack_bar)
            page.update()

    user_login = ft.Ref[ft.TextField]()
    user_pass = ft.Ref[ft.TextField]()

    login_form = ft.Container(
        content=ft.Column(
            [
                ft.Text("Авторизация", size=24, weight=ft.FontWeight.BOLD), # Добавил жирность
                ft.TextField(
                    label="Логин", 
                    width=300, 
                    ref=user_login, 
                    autofocus=True, # Фокус на поле логина при открытии
                    on_submit=lambda _: user_pass.current.focus() # Переход на поле пароля по Enter
                ),
                ft.TextField(
                    label="Пароль", 
                    width=300, 
                    password=True, 
                    ref=user_pass, 
                    can_reveal_password=True,
                    on_submit=on_login_click # Попытка входа по Enter из поля пароля
                ),
                ft.ElevatedButton(
                    text="Войти", 
                    width=300, 
                    on_click=on_login_click, 
                    icon=ft.Icons.LOGIN # Добавил иконку
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=25 # Увеличил немного отступы
        ),
        alignment=ft.alignment.center,
        expand=True,
    )
    
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(login_form)

if __name__ == "__main__":
    # Проверка, что запускается на Android для специфичных вещей
    if os.name == 'posix' and "ANDROID_API_LEVEL" in os.environ: # Простой способ проверить Android
        print("Running on Android environment.")
    else:
        print("Running on non-Android environment. Android-specific features (permissions) may not work.")

    # Пример home_page, если она не импортируется
    # def home_page(page: ft.Page):
    #     page.add(ft.Text(f"Welcome, {page.session.get('full_name')}!"))
    #     page.update()

    ft.app(target=main)
