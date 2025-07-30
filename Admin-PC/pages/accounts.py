import flet as ft
import requests
from plugins.card_styles import create_card
from plugins.network import API_URL

def accounts_page(page: ft.Page):
    # Загрузка данных с обработкой ошибок
    def load_data():
        try:
            roles_response = requests.get(f"{API_URL}/roles")
            users_response = requests.get(f"{API_URL}/users")
            
            roles = roles_response.json() if roles_response.status_code == 200 else []
            users = users_response.json() if users_response.status_code == 200 else []
            
            return roles, users
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            return [], []

    # Обновление интерфейса
    def update_ui():
        roles, users = load_data()
        role_cards.controls = [create_role_card(r) for r in roles]
        user_cards.controls = [create_user_card(u) for u in users]
        role_dropdown.options = [ft.dropdown.Option(r["name"]) for r in roles]
        page.update()

    # Создание карточки роли
    def create_role_card(role):
        return create_card(
            title=role["name"],
            icon=ft.Icons.SECURITY_OUTLINED,
            on_click_handler=lambda e, r=role: confirm_delete_role(e, r),
            subtitle="Роль",
            description="Кликните для удаления",
            title_color=ft.Colors.BLUE_800,
            subtitle_color=ft.Colors.GREY_600,
            margin=ft.margin.symmetric(vertical=5, horizontal=10),
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
        )

    # Создание карточки пользователя
    def create_user_card(user):
        return create_card(
            title=user["username"],
            subtitle=user["full_name"],
            description=f"Роль: {user['role']}",
            icon=ft.Icons.PERSON_OUTLINE,
            on_click_handler=lambda e, u=user: confirm_delete_user(e, u),
            title_color=ft.Colors.GREEN_800,
            subtitle_color=ft.Colors.BLUE_GREY_600,
            margin=ft.margin.symmetric(vertical=5, horizontal=10),
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
        )

    # Диалог подтверждения удаления роли
    def confirm_delete_role(e, role):
        def delete_role(_):
            try:
                requests.delete(f"{API_URL}/roles/{role['id']}")
                update_ui()
                dlg.open = False
                page.update()
            except Exception as e:
                print(f"Ошибка при удалении роли: {e}")

        dlg = ft.AlertDialog(
            title=ft.Text(f"Удалить роль {role['name']}?"),
            content=ft.Text("Все пользователи с этой ролью будут сохранены!"),
            actions=[
                ft.TextButton("Удалить", on_click=delete_role),
                ft.TextButton("Отмена", on_click=lambda _: close_dialog(dlg))
            ]
        )
        page.open(dlg)
        page.update()

    def close_dialog(dlg):
        dlg.open = False
        page.update()

    # Диалог подтверждения удаления пользователя
    def confirm_delete_user(e, user):
        def delete_user(_):
            try:
                requests.delete(f"{API_URL}/users/{user['id']}")
                update_ui()
                dlg.open = False
                page.update()
            except Exception as e:
                print(f"Ошибка при удалении пользователя: {e}")

        dlg = ft.AlertDialog(
            title=ft.Text(f"Удалить пользователя {user['username']}?"),
            actions=[
                ft.TextButton("Удалить", on_click=delete_user),
                ft.TextButton("Отмена", on_click=lambda _: close_dialog(dlg))
            ]
        )
        page.open(dlg)
        page.update()

    # Форма добавления роли
    def add_role_dialog():
        new_role = ft.TextField(label="Название роли")

        def save_role(_):
            if new_role.value:
                try:
                    requests.post(f"{API_URL}/roles", json={"name": new_role.value})
                    update_ui()
                    dlg.open = False
                    page.update()
                except Exception as e:
                    print(f"Ошибка при добавлении роли: {e}")

        dlg = ft.AlertDialog(
            title=ft.Text("Добавить новую роль"),
            content=new_role,
            actions=[
                ft.TextButton("Сохранить", on_click=save_role),
                ft.TextButton("Отмена", on_click=lambda _: close_dialog(dlg))
            ]
        )
        page.open(dlg)
        page.update()

    # Форма добавления пользователя
    def add_user_dialog():
        username = ft.TextField(label="Логин")
        password = ft.TextField(label="Пароль", password=True)
        full_name = ft.TextField(label="Полное имя")
        role_dropdown = ft.Dropdown(label="Роль")

        def load_roles():
            try:
                roles = requests.get(f"{API_URL}/roles").json()
                role_dropdown.options = [ft.dropdown.Option(r["name"]) for r in roles]
                page.update()
            except Exception as e:
                print(f"Ошибка при загрузке ролей: {e}")

        load_roles()

        def save_user(_):
            if all([username.value, password.value, full_name.value, role_dropdown.value]):
                try:
                    role_id = next(r["id"] for r in requests.get(f"{API_URL}/roles").json() 
                                if r["name"] == role_dropdown.value)
                    
                    user_data = {
                        "username": username.value,
                        "password": password.value,
                        "full_name": full_name.value,
                        "role_id": role_id
                    }
                    
                    requests.post(f"{API_URL}/register", json=user_data)
                    update_ui()
                    dlg.open = False
                    page.update()
                except Exception as e:
                    print(f"Ошибка при добавлении пользователя: {e}")

        dlg = ft.AlertDialog(
            title=ft.Text("Добавить нового пользователя"),
            content=ft.Column([
                username,
                password,
                full_name,
                role_dropdown
            ], height=300),
            actions=[
                ft.TextButton("Сохранить", on_click=save_user),
                ft.TextButton("Отмена", on_click=lambda _: close_dialog(dlg))
            ]
        )
        page.open(dlg)
        page.update()

    # Интерфейс
    role_cards = ft.Column(expand=True)
    user_cards = ft.Column(expand=True)
    role_dropdown = ft.Dropdown()

    # Очистка страницы перед добавлением нового контента
    page.clean()
    update_ui()

    # Добавление контента
    page.add(
        ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Row([
                            ft.Text("Роли", size=24),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                tooltip="Добавить роль",
                                on_click=lambda _: add_role_dialog()
                            )
                        ]),
                        ft.Divider(),
                        role_cards
                    ],
                    expand=True
                ),
                ft.VerticalDivider(),
                ft.Column(
                    controls=[
                        ft.Row([
                            ft.Text("Пользователи", size=24),
                            ft.IconButton(
                                icon=ft.Icons.PERSON_ADD_ALT_OUTLINED,
                                tooltip="Добавить пользователя",
                                on_click=lambda _: add_user_dialog()
                            )
                        ]),
                        ft.Divider(),
                        user_cards
                    ],
                    expand=True
                )
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
    )