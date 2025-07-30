import flet as ft
from pages.tovari import tovari_page
from pages.accounts import accounts_page
from pages.history import history_page

def home(page: ft.Page):
    # Функция для отображения sidebar с сообщением
    def show_beta_message(e):
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Эта функция недоступна в бета-режиме.", size=20),
            action="OK",
            action_color=ft.colors.WHITE,
            bgcolor=ft.colors.RED_700,
            duration=3000
        )
        page.snack_bar.open = True
        page.update()

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.OutlinedButton(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(name=ft.Icons.SHOPPING_BASKET_OUTLINED, size=50),
                                        ft.Text(value="Товары", size=50),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    spacing=10,
                                ),
                                padding=ft.padding.all(20),
                                width=400,  # Фиксированная ширина для всех кнопок
                                on_click=tovari_page
                            ),
                        ),
                        ft.OutlinedButton(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(name=ft.Icons.PEOPLE_OUTLINE, size=50),
                                        ft.Text(value="Уч. записи", size=50),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    spacing=10,
                                ),
                                padding=ft.padding.all(20),
                                width=400,
                                on_click=lambda e: accounts_page(page)  # Изменение здесь
                            ),
                        ),
                        ft.OutlinedButton(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(name=ft.Icons.HISTORY_OUTLINED, size=50),
                                        ft.Text(value="История", size=50),
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    spacing=10,
                                ),
                                padding=ft.padding.all(20),
                                width=400,
                                on_click=lambda e: history_page(page)
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,  # Центровка колонки внутри строки
        ),
        alignment=ft.alignment.center,  # Центровка всего контейнера на странице
        expand=True,  # Растянуть контейнер на весь экран
    )