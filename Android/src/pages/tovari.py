import flet as ft
from bdinit import get_items, get_categories
from pathlib import Path
import logging
from pages.catalogue import create_category_card

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути к изображениям
BASE_DIR = Path(__file__).parent.parent.resolve()
IMGS_DIR = BASE_DIR / "backend" / "Imgs"
DEFAULT_IMAGE_PATH = BASE_DIR / "default.jpg"

def create_item_card(page, item, categories):
    # Логирование данных товара
    logger.info(f"Creating card for item: {item.get('name')}")
    
    # Обработка изображения
    try:
        image_id = item.get('image_id')
        if image_id:
            image_path = IMGS_DIR / f"{image_id}.jpg"
            if not image_path.exists():
                logger.warning(f"Image not found: {image_path}, using default")
                image_path = DEFAULT_IMAGE_PATH
        else:
            image_path = DEFAULT_IMAGE_PATH
        
        image = ft.Image(
            src=str(image_path),
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(10),
            error_content=ft.Container(
                bgcolor=ft.Colors.GREY_300,
                border_radius=ft.border_radius.all(10),
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, color=ft.Colors.GREY_600)
            )
        )
    except Exception as e:
        logger.error(f"Error loading image: {e}")
        image = ft.Container(
            bgcolor=ft.colors.GREY_300,
            border_radius=ft.border_radius.all(10),
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.colors.RED)
        )

    # Формирование текста параметра
    parameter_text = ""
    if item.get('parameter_value'):
        category = next((cat for cat in categories if cat['id'] == item['category_id']), None)
        if category and category.get('parameter'):
            parameter_text = f"{category['parameter']}: {item['parameter_value']}"
        else:
            parameter_text = f"Параметр: {item['parameter_value']}"

    # Основные элементы карточки
    content_controls = [
        # Контейнер с изображением
        ft.Container(
            height=100,
            width=120,
            content=image,
            border_radius=ft.border_radius.all(10),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
        # Название товара
        ft.Text(
            item.get('name', 'Без названия'),
            weight=ft.FontWeight.BOLD,
            size=14,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
            text_align=ft.TextAlign.CENTER,
        ),
        # Единицы измерения
        ft.Text(
            f"Ед. изм: {item.get('unit', 'шт')}", 
            size=12,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            text_align=ft.TextAlign.CENTER,
        ),
    ]
    
    # Добавляем параметр, если есть
    if parameter_text:
        content_controls.append(
            ft.Text(
                parameter_text, 
                size=12,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
                text_align=ft.TextAlign.CENTER,
            )
        )
    
    # Добавляем разделитель и цену
    content_controls.extend([
        ft.Divider(height=1, color=ft.Colors.GREY_300),
        ft.Text(
            f"{item.get('selling_price', 0)} UZS",
            color=ft.Colors.ORANGE,
            weight=ft.FontWeight.BOLD,
            size=14,
            text_align=ft.TextAlign.CENTER,
        ),
    ])

    # Создаем карточку
    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=content_controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                tight=True,
            ),
            padding=10,
            width=150,
            height=220,
        ),
        elevation=2,
    )

    # Обработка выбора товара
    selected_items = page.session.get("selected_items") or []
    is_selected = any(entry['id'] == item['id'] for entry in selected_items)
    
    card_container = ft.Container(
        content=card,
        bgcolor=ft.Colors.GREEN_100 if is_selected else None,
        border=ft.border.all(1, ft.Colors.GREEN_300 if is_selected else ft.Colors.GREY_300),
        border_radius=ft.border_radius.all(10),
        padding=5,
        on_click=lambda e: toggle_selection(e, item),
        data=item['id'],
    )

    def toggle_selection(e, item):
        selected_items = page.session.get("selected_items") or []
        item_id = item['id']
        existing = next((entry for entry in selected_items if entry['id'] == item_id), None)
        
        if existing:
            selected_items = [entry for entry in selected_items if entry['id'] != item_id]
            e.control.bgcolor = None
            e.control.border = ft.border.all(1, ft.Colors.GREY_300)
        else:
            new_entry = {
                'id': item['id'],
                'name': item['name'],
                'selling_price': item['selling_price'],
                'image_id': item.get('image_id'),
                'quantity': 1,
                'category_name': item.get('category_name', ''),  # Добавлено
                'unit': item.get('unit', 'шт')                   # Добавлено
            }
            selected_items.append(new_entry)
            e.control.bgcolor = ft.Colors.GREEN_100
            e.control.border = ft.border.all(1, ft.Colors.GREEN_300)
        
        page.session.set("selected_items", selected_items)
        page.update()

    return card_container

def create_item_card(page, item, categories):
    # Логирование данных товара
    logger.info(f"Creating card for item: {item.get('name')}")
    
    # Обработка изображения
    try:
        image_id = item.get('image_id')
        if image_id:
            image_path = IMGS_DIR / f"{image_id}.jpg"
            if not image_path.exists():
                logger.warning(f"Image not found: {image_path}, using default")
                image_path = DEFAULT_IMAGE_PATH
        else:
            image_path = DEFAULT_IMAGE_PATH
        
        # Создаем Stack с изображением и иконкой микрофона
        image_stack = ft.Stack(
            expand=True,
            controls=[
                ft.Image(
                    src=str(image_path),
                    width=120,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(10),
                    error_content=ft.Container(
                        bgcolor=ft.Colors.GREY_300,
                        border_radius=ft.border_radius.all(10),
                        alignment=ft.alignment.center,
                        content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, color=ft.Colors.GREY_600)
                    )
                ),
                ft.Container(
                    alignment=ft.alignment.bottom_right,
                    padding=5,
                    content=ft.Container(
                        width=24,
                        height=24,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=ft.border_radius.all(12),
                        alignment=ft.alignment.center,
                        content=ft.Icon(
                            name=ft.Icons.MIC_NONE if item.get('mic', 0) == 1 else ft.Icons.MIC_OFF,
                            size=16,
                            color=ft.Colors.BLACK87
                        )
                    )
                )
            ]
        )
        
        image_container = ft.Container(
            content=image_stack,
            width=120,
            height=100,
            border_radius=ft.border_radius.all(10),
            clip_behavior=ft.ClipBehavior.HARD_EDGE
        )

    except Exception as e:
        logger.error(f"Error loading image: {e}")
        image_container = ft.Container(
            bgcolor=ft.colors.GREY_300,
            border_radius=ft.border_radius.all(10),
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.colors.RED)
        )

    # Формирование текста параметра
    parameter_text = ""
    if item.get('parameter_value'):
        category = next((cat for cat in categories if cat['id'] == item['category_id']), None)
        if category and category.get('parameter'):
            parameter_text = f"{category['parameter']}: {item['parameter_value']}"
        else:
            parameter_text = f"Параметр: {item['parameter_value']}"

    # Основные элементы карточки
    content_controls = [
        # Контейнер с изображением
        image_container,
        # Название товара
        ft.Text(
            item.get('name', 'Без названия'),
            weight=ft.FontWeight.BOLD,
            size=14,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
            text_align=ft.TextAlign.CENTER,
        ),
        # Единицы измерения
        ft.Text(
            f"Ед. изм: {item.get('unit', 'шт')}", 
            size=12,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            text_align=ft.TextAlign.CENTER,
        ),
    ]
    
    # Добавляем параметр, если есть
    if parameter_text:
        content_controls.append(
            ft.Text(
                parameter_text, 
                size=12,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
                text_align=ft.TextAlign.CENTER,
            )
        )

    price_controls = []
    
    # Форматирование стоимости
    def format_price(price):
        return f"{int(price):,} UZS".replace(",", " ").replace(" ", "\u00A0", 3)
    
    # Основная цена
    price_controls.append(
        ft.Text(
            value=f"{format_price(item.get('selling_price', 0))}",
            color=ft.Colors.ORANGE,
            weight=ft.FontWeight.BOLD,
            size=14,
            text_align=ft.TextAlign.CENTER
        )
    )
    
    # Добавляем разделитель и цены
    content_controls.extend([
        ft.Divider(height=1, color=ft.Colors.GREY_300),
        ft.Column(
            controls=price_controls,
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True
        )
    ])

    # Создаем карточку
    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=content_controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                tight=True,
            ),
            padding=10,
            width=150,
            height=220,
        ),
        elevation=2,
    )

    # Обработка выбора товара
    selected_items = page.session.get("selected_items") or []
    is_selected = any(entry['id'] == item['id'] for entry in selected_items)
    
    card_container = ft.Container(
        content=card,
        bgcolor=ft.Colors.GREEN_100 if is_selected else None,
        border=ft.border.all(1, ft.Colors.GREEN_300 if is_selected else ft.Colors.GREY_300),
        border_radius=ft.border_radius.all(10),
        padding=5,
        on_click=lambda e: toggle_selection(e, item),
        data=item['id'],
    )

    def toggle_selection(e, item):
        selected_items = page.session.get("selected_items") or []
        item_id = item['id']
        existing = next((entry for entry in selected_items if entry['id'] == item_id), None)
        
        if existing:
            selected_items = [entry for entry in selected_items if entry['id'] != item_id]
            e.control.bgcolor = None
            e.control.border = ft.border.all(1, ft.Colors.GREY_300)
        else:
            new_entry = {
                'id': item['id'],
                'name': item['name'],
                'selling_price': item['selling_price'],
                'image_id': item.get('image_id'),
                'quantity': 1,
                'category_name': item.get('category_name', ''),
                'unit': item.get('unit', 'шт'),
                'mic': item.get('mic', 0)  # Добавляем статус микрофона
            }
            selected_items.append(new_entry)
            e.control.bgcolor = ft.Colors.GREEN_100
            e.control.border = ft.border.all(1, ft.Colors.GREEN_300)
        
        page.session.set("selected_items", selected_items)
        page.update()

    return card_container

def items_page(page: ft.Page, category_id: int, on_back_click, tab=None):
    # Создаем контейнер для загрузки
    progress = ft.ProgressBar(visible=True)
    page.add(progress)
    
    try:
        # Загружаем товары для данной категории
        items_data = get_items(category_id)
        logger.info(f"Loaded {len(items_data)} items for category {category_id}")
        
        # Загружаем данные о текущей категории
        category_info = next((c for c in get_categories() if c['id'] == category_id), None)
        
        # Загружаем подкатегории
        subcategories = []
        if category_info:
            subcategories = get_categories(parent_id=category_id, tab=category_info.get('tab'))
        
        # Создаем кнопку "Назад"
        back_button = ft.ElevatedButton(
            "Назад",
            on_click=on_back_click,
            icon=ft.Icons.ARROW_BACK,
        )
        
        # Создаем контейнеры для подкатегорий
        subcategory_controls = []
        for subcat in subcategories:
            subcategory_controls.append(
                create_category_card(subcat, lambda cid=subcat['id']: on_click_handler(cid))
            )
            
        def on_click_handler(cid):
            page.session.set("current_category_id", cid)
            new_content = items_page(page, cid, on_back_click, tab)
            if tab == 0:
                page.session.get("goods_container").content = new_content
            else:
                page.session.get("services_container").content = new_content
            page.update()
        
        # Получаем все категории для параметров товаров
        all_categories = get_categories()
        
        # Создаем сетку для товаров
        items_grid = None
        if items_data:
            item_controls = []
            for item in items_data:
                item_card = create_item_card(page, item, all_categories)
                item_controls.append(item_card)
                
            items_grid = ft.GridView(
                controls=item_controls,
                runs_count=2,  # Колонки
                max_extent=180,  # Ширина элемента
                spacing=10,
                run_spacing=10,
                padding=10,
                child_aspect_ratio=0.75,  # Соотношение сторон
            )
            
        title_text = ft.Text(
            f"Категория: {category_info['name'] if category_info else 'Неизвестная категория'}", 
            size=18, 
            weight=ft.FontWeight.BOLD,
        )
        
        # Собираем итоговый контейнер
        content_controls = [
            ft.Row([back_button], alignment=ft.MainAxisAlignment.START),
            title_text,
        ]
        
        # Добавляем подкатегории, если есть
        if subcategory_controls:
            content_controls.extend([
                ft.Text("Подкатегории", size=16, weight=ft.FontWeight.BOLD),
                ft.Column(controls=subcategory_controls, spacing=10),
            ])
        
        # Добавляем товары или сообщение об их отсутствии
        if items_grid:
            content_controls.extend([
                ft.Text("Товары", size=16, weight=ft.FontWeight.BOLD),
                items_grid,
            ])
        elif not subcategory_controls:
            content_controls.append(
                ft.Text("В этой категории пока нет товаров", italic=True)
            )
        
        content = ft.Column(
            controls=content_controls,
            expand=True,
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        )
        
    except Exception as e:
        logger.error(f"Error in items_page: {e}")
        content = ft.Text(f"Ошибка загрузки: {str(e)}", color=ft.Colors.RED)
    finally:
        progress.visible = False
        page.update()
        
    return content