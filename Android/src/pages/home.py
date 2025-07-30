import flet as ft
from pages.catalogue import categories_page
from pages.tovari import items_page, IMGS_DIR, DEFAULT_IMAGE_PATH
from plugins.theme_manager import create_theme_button
from pages.calculator import build_calculate_content

def home_page(page: ft.Page):
    if not page.session.get("file_picker"):
        file_picker = ft.FilePicker()
        page.overlay.append(file_picker)
        page.session.set("file_picker", file_picker)

    goods_container = ft.Container(expand=True)
    services_container = ft.Container(expand=True)
    calculate_content_container = ft.Container(expand=True)
    
    # Сохраняем контейнеры в сессии для доступа из других функций
    page.session.set("goods_container", goods_container)
    page.session.set("services_container", services_container)
    page.session.set("current_category_id", None)
    page.session.set("current_tab", 0)

    # 1. Объявляем обработчики событий в первую очередь
    def on_category_click(category_id: int):
        show_items(category_id)

    def on_back_click(e: ft.ControlEvent):
        show_categories()

    # 2. Основные функции управления интерфейсом
    def show_categories(tab_index=None):
        """Показывает список категорий для указанной tab"""
        if tab_index is not None:
            page.session.set("current_tab", tab_index)
        
        current_tab = page.session.get("current_tab")
        
        if current_tab == 0:
            goods_container.content = categories_page(page, on_category_click, tab=0)
        else:
            services_container.content = categories_page(page, on_category_click, tab=1)
        
        page.update()

    def show_items(category_id: int):
        current_tab = page.session.get("current_tab")
        page.session.set("current_category_id", category_id)
        
        if current_tab == 0:
            goods_container.content = items_page(page, category_id, on_back_click, tab=0)
        else:
            services_container.content = items_page(page, category_id, on_back_click, tab=1)
            
        page.update()
        
    show_categories(0)

    def update_item_list():
        """Обновляет список товаров/услуг для текущей вкладки"""
        current_tab = page.session.get("current_tab")
        category_id = page.session.get("current_category_id")
        if category_id is not None:
            if current_tab == 0:
                goods_container.content = items_page(page, category_id, on_back_click, tab=0)
            else:
                services_container.content = items_page(page, category_id, on_back_click, tab=1)
            page.update()

    # 3. Обработчик переключения вкладок
    def on_tab_change(e: ft.ControlEvent):
        index = tab.selected_index
        if index == 0:
            show_categories(0)
        elif index == 1:
            show_categories(1)
        elif index == 2:
            calculate_content_container.content = build_calculate_content(
                page,
                calculate_content_container,
                lambda: show_categories(page.session.get("current_tab")),
                lambda: update_item_list()
            )
            page.update()

    tab = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(
                text="Товары",
                content=goods_container
            ),
            ft.Tab(
                text="Услуги",
                content=services_container
            ),
            ft.Tab(
                text="Посчитать",
                content=calculate_content_container
            )
        ],
        expand=True,
        on_change=on_tab_change
    )

    appbar = ft.AppBar(
        title=ft.Row(
            controls=[ft.Text("ShiDari Informator")],
            expand=True,
            alignment=ft.MainAxisAlignment.START,
        ),
        actions=[
            ft.IconButton(
                ft.Icons.HOME,
                on_click=lambda e: home(page)
            ),
            create_theme_button(page)
        ],
        bgcolor=ft.Colors.BLUE_500,
        toolbar_height=40
    )

    page.appbar = appbar
    page.add(tab)

def home(page: ft.Page):
    page.clean()
    home_page(page)