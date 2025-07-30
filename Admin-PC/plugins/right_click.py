import flet as ft
import requests


class RightClickHandler:
    def __init__(self, page: ft.Page):
        self.page = page
        self.plural_mapping = {
            "category": "categories",
            "item": "items",
            "role": "roles",
            "user": "users",
        }
        self.context_menu = None  # Хранит текущее контекстное меню

    def create_right_clickable(self, content, obj, obj_type, on_delete_success, on_edit_success=None):
        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Удалить {obj_type}?"),
            content=ft.Text(f"Вы уверены, что хотите удалить {obj['name']}?"),
            actions=[
                ft.TextButton("Да", on_click=lambda e: self.delete(obj, obj_type, on_delete_success, confirm_dialog)),
                ft.TextButton("Нет", on_click=lambda e: self.close_dialog(confirm_dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def open_dialog(e: ft.ControlEvent):
            # Проверяем, есть ли глобальные координаты
            if not e.global_position:
                return

                # Смещение меню относительно клика
            menu_offset_top = 10
            menu_offset_left = 10

            # Координаты мыши
            mouse_x = e.global_position.x + menu_offset_left
            mouse_y = e.global_position.y + menu_offset_top

            # Удаляем старое меню, если оно есть
            if self.context_menu:
                self.page.overlay.remove(self.context_menu)

            # Создаем контекстное меню
            self.context_menu = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.TextButton("Редактировать", on_click=lambda e: self.edit(obj, obj_type, on_edit_success)),
                        ft.TextButton("Удалить", on_click=lambda e: self.open_delete_dialog(confirm_dialog)),
                    ],
                ),
                bgcolor=ft.colors.WHITE,
                border=ft.border.all(1, ft.colors.BLACK),
                padding=10,
                left=mouse_x,
                top=mouse_y,
            )

            # Добавляем меню на страницу
            self.page.overlay.append(self.context_menu)
            self.page.update()

        return ft.GestureDetector(
            content=content,
            on_secondary_tap=open_dialog,  # Вызываем меню при правом клике
        )

    def open_delete_dialog(self, dialog):
        dialog.open = True
        self.page.update()

    def delete(self, obj, obj_type, on_delete_success, dialog):
        endpoint = self.plural_mapping.get(obj_type, f"{obj_type}s")
        url = f"http://localhost:8000/{endpoint}/{obj['id']}"

        try:
            response = requests.delete(url)
            if response.status_code == 200:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"{obj_type.capitalize()} успешно удален!"))
                on_delete_success()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {response.text}"))
            self.page.snack_bar.open = True
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка подключения: {ex}"))
            self.page.snack_bar.open = True

        self.close_dialog(dialog)
        self.page.update()

    def edit(self, obj, obj_type, on_edit_success):
        edit_dialog = self.create_edit_dialog(obj, obj_type, on_edit_success)
        edit_dialog.open = True
        self.page.update()

    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()
