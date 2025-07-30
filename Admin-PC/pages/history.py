import flet as ft

def show_auth_dialog(page: ft.Page):

    def close_dlg():
        page.close(dlg),
        page.update()

    def on_confirm(e):
        current_password = getattr(page, "current_password", None)
        
        if password_field.value == current_password:
            page.clean()
            close_dlg
            page.add(ft.Text("Вход успешен", size=30))
        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Ошибка: Неверный пароль"),
                bgcolor="red"
            )
            close_dlg
            page.snack_bar.open = True
        page.update()

    password_field = ft.TextField(
        label="Введите пароль",
        password=True,
        can_reveal_password=True
    )

    dlg = ft.AlertDialog(
        title=ft.Text("Подтвердите пароль"),
        content=password_field,
        actions=[
            ft.TextButton("Подтвердить", on_click=on_confirm),
            ft.TextButton("Отмена", on_click=close_dlg),
        ],
    )

    page.open(dlg),
    page.update()

def history_page(page: ft.Page):
    show_auth_dialog(page)