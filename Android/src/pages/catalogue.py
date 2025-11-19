import flet as ft
from plugins.card_styles import create_card
from bdinit import get_categories
from itertools import groupby

def create_category_card(category, on_click_handler):
    return ft.Container(
        content=create_card(
            title=category['name'],
            subtitle=f"Параметр: {category['parameter'] or 'Не указан'}",
            description=f"Ед. измерения: {category['unit']}",
            on_click_handler=lambda e: on_click_handler(category['id']),  # Передаем ID категории
            description_color=ft.Colors.BLUE_800,
        ),
        margin=ft.margin.all(5),  # Добавляем отступы вокруг карточки
        width=float("inf"),  # Растягиваем карточку на всю доступную ширину
        expand=True,  # Разрешаем растягивание
    )

def categories_page(page: ft.Page, on_category_click, tab: int):
    progress = ft.ProgressBar(visible=True)
    page.add(progress)

    try:
        # Получаем только категории верхнего уровня для выбранной вкладки
        top_categories = get_categories(parent_id=None, tab=tab)

        if not top_categories:
            return ft.Text("Нет категорий в этой вкладке")

        # Группируем категории по полю 'group'
        grouped_categories = {k: list(v) for k, v in groupby(top_categories, key=lambda x: x.get('group') or 'Uncategorized')}

        # Создаем UI для каждой категории верхнего уровня
        category_columns = []
        for group, categories in grouped_categories.items():
            category_columns.append(ft.Text(group, size=20, weight=ft.FontWeight.BOLD))
            for category in categories:
                # Создаем карточку категории
                card = create_category_card(category, on_category_click)
                category_columns.append(card)

    finally:
        progress.visible = False
        page.update()

    return ft.Container(
        content=ft.ListView(
            controls=category_columns,
            expand=True
        ),
        expand=True,
        padding=10
    )
