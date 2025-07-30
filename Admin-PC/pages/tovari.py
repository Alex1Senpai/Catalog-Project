import flet as ft
import requests
import os
from functools import lru_cache
from contextlib import contextmanager
from datetime import datetime
from plugins.network import API_URL

class TovariPage:
    IMAGES_BASE_URL = f"{API_URL}/imgs"
    IMAGES_DIR = r"C:\\serverShiDari\\Imgs"
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_tab = 0
        self.state = AppState()
        self.current_dialog = None
        self.selected_image_path = None
        self._init_ui()
        self._setup_file_picker()
        self._setup_directories()
        self.update_interface()

    def _init_ui(self):
        # Создаем отдельные элементы для каждой вкладки
        self.tab_contents = {
            0: {
                "main_container": ft.Container(),
                "category_list": ft.ListView(expand=True, spacing=10, padding=10),
                "content_view": ft.GridView(
                    expand=True, runs_count=5, max_extent=260,
                    child_aspect_ratio=0.8, spacing=10, padding=10
                )
            },
            1: {
                "main_container": ft.Container(),
                "category_list": ft.ListView(expand=True, spacing=10, padding=10),
                "content_view": ft.GridView(
                    expand=True, runs_count=5, max_extent=260,
                    child_aspect_ratio=0.8, spacing=10, padding=10
                )
            }
        }
        
        self.tabs = ft.Tabs(
            tabs=[
                ft.Tab(
                    text="Товары", 
                    content=self.tab_contents[0]["main_container"]
                ),
                ft.Tab(
                    text="Услуги", 
                    content=self.tab_contents[1]["main_container"]
                )
            ],
            selected_index=0,
            expand=True,
            on_change=self._handle_tab_change
        )
        self.page.add(self.tabs)

    def _setup_file_picker(self):
        self.image_picker = ft.FilePicker()
        self.page.overlay.append(self.image_picker)

    def _setup_directories(self):
        os.makedirs(self.IMAGES_DIR, exist_ok=True)

    @property
    def current_tab_content(self):
        return self.tab1_content if self.selected_tab == 0 else self.tab2_content

    def _handle_tab_change(self, e):
        self.selected_tab = self.tabs.selected_index
        self.update_interface()

    def _handle_delete_category(self, category):
        try:
            response = requests.delete(f"{API_URL}/categories/{category['id']}")
            response.raise_for_status()
            self.load_categories()
            self._show_snackbar("Категория успешно удалена")
        except Exception as e:
            self._show_snackbar(f"Ошибка при удалении: {str(e)}")

    def _handle_edit_category(self, category):
        name_field = ft.TextField(label="Название", value=category['name'])
        param_field = ft.TextField(label="Параметр", value=category.get('parameter', ''))
        unit_field = ft.TextField(label="Единица измерения", value=category['unit'])

        def save_changes(e):
            try:
                update_data = {
                    "name": name_field.value,
                    "parameter": param_field.value,
                    "unit": unit_field.value
                }
                response = requests.put(
                    f"{API_URL}/categories/{category['id']}",
                    json=update_data
                )
                response.raise_for_status()
                self.load_categories()
                self.page.close(dlg)
                self._show_snackbar("Изменения сохранены")
            except Exception as e:
                self._show_snackbar(f"Ошибка: {str(e)}")

        dlg = ft.AlertDialog(
            title=ft.Text("Редактировать категорию"),
            content=ft.Column(
                controls=[
                    name_field,
                    param_field,
                    unit_field,
                    ft.Row(
                        [
                            ft.ElevatedButton("Сохранить", on_click=save_changes),
                            ft.ElevatedButton("Отмена", on_click=lambda e: self.page.close(dlg))
                        ],
                        alignment=ft.MainAxisAlignment.END
                    )
                ],
                tight=True
            )
        )
        self.page.open(dlg)
        self.page.update()

    def _handle_delete_item(self, item, category):
        try:
            response = requests.delete(f"{API_URL}/items/{item['id']}")
            response.raise_for_status()
            
            # Принудительно обновляем список товаров
            self._load_category_items(category, force_refresh=True)
            self._show_snackbar("Товар успешно удален")
            
        except Exception as e:
            self._show_snackbar(f"Ошибка при удалении: {str(e)}")

    def _handle_edit_item(self, item, category):
        self.selected_image_path = None
        self.mic_checkbox = ft.Checkbox(label="Имеется микрофон", value=item['mic'] == 1)

        try:
            response = requests.get(f"{API_URL}/items/{item['id']}")
            updated_item = response.json()
        except Exception as e:
            self._show_snackbar(f"Ошибка загрузки данных: {str(e)}")
            return

        self.mic_checkbox = ft.Checkbox(
            label="Имеется микрофон", 
            value=updated_item['mic'] == 1
        )

        parameter_label = category.get('parameter', 'Параметр')
        
        fields = [
            {"label": "Название товара", "value": item['name'], "required": True},
            {"label": parameter_label, "value": item['parameter_value'], "required": True},
            {"label": "Себестоимость", "value": str(item['cost_price']), 
            "required": True, "keyboard": ft.KeyboardType.NUMBER},
            {"label": "Цена с наценкой", "value": str(item['selling_price']), 
            "required": True, "keyboard": ft.KeyboardType.NUMBER},
            {"type": "checkbox", "control": self.mic_checkbox},
            {"label": "Изображение", "type": "file", "value": item.get('image_id')}
        ]

        self._create_edit_dialog(item, category, fields)

    def _create_edit_dialog(self, item, category, fields):
        self.selected_image_path = None
        self.dialog_fields = []
        controls = []

        current_image_text = "Файл не выбран"
        if item.get('image_id'):
            current_image_text = f"Текущее: {item['image_id']}"
        
        for field in fields:
            if field.get('type') == 'file':
                row = ft.Row([
                    ft.ElevatedButton(
                        "Выбрать изображение",
                        on_click=lambda e: self.image_picker.pick_files()
                    ),
                    ft.Text(current_image_text, color=ft.Colors.GREY)  # <-- Отображение текущего
                ])
                self.dialog_fields.append((field, row.controls[1]))
                controls.append(row)
            elif field.get('type') == 'checkbox':
                controls.append(field['control'])
            else:
                tf = ft.TextField(
                    label=field['label'],
                    value=field.get('value', ''),
                    keyboard_type=field.get('keyboard'),
                    expand=True
                )
                self.dialog_fields.append((field, tf))
                controls.append(tf)

        controls.extend([
            ft.Row([
                ft.ElevatedButton(
                    "Сохранить",
                    on_click=lambda e: self._update_item(item, category)
                ),
                ft.ElevatedButton("Отмена", on_click=self._close_dialog)
            ], alignment=ft.MainAxisAlignment.END)
        ])

        self.current_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Редактировать товар"),
            content=ft.Column(
                controls=controls,
                spacing=15,
                scroll=ft.ScrollMode.ADAPTIVE
            )
        )
        
        self.image_picker.on_result = self._handle_image_picked
        self.page.open(self.current_dialog)
        self.page.update()

    def _update_item(self, item, category):
        errors = self._validate_dialog_fields()
        if errors:
            self._show_snackbar("\n".join(errors))
            return

        image_id = item.get('image_id')
        if self.selected_image_path:
            with open(self.selected_image_path, "rb") as f:
                files = {"image": (os.path.basename(self.selected_image_path), f)}
                try:
                    response = requests.post(f"{API_URL}/upload_image", files=files)
                    response.raise_for_status()
                    image_id = response.json()["image_id"]
                except Exception as e:
                    self._show_snackbar(f"Ошибка загрузки изображения: {str(e)}")
                    return

        item_data = {
            "name": self.dialog_fields[0][1].value.strip(),
            "parameter_value": self.dialog_fields[1][1].value.strip(),
            "cost_price": int(self.dialog_fields[2][1].value),
            "selling_price": int(self.dialog_fields[3][1].value),
            "category_id": category['id'],
            "unit": category['unit'],
            "image_id": image_id,
            "mic": 1 if self.mic_checkbox.value else 0
        }

        try:
            response = requests.put(
                f"{API_URL}/items/{item['id']}",
                json=item_data
            )
            response.raise_for_status()
            self._load_category_items(category)
            self._close_dialog()
            self._show_snackbar("Товар успешно обновлен!")

            self._load_category_items(category, force_refresh=True)
        except Exception as e:
            self._show_snackbar(f"Ошибка: {str(e)}")

    def update_interface(self):
        # Сбрасываем выбранную категорию при возврате
        self.state.selected_category = None  # <-- Добавлено сброс состояния
        
        current_tab = self.tab_contents[self.selected_tab]
        current_tab["category_list"] = ft.ListView(expand=True, spacing=10, padding=10)
        current_tab["main_container"].content = self._create_interface_layout(
            "Поиск", 
            current_tab["category_list"]
        )
        
        if self.selected_tab in self.state.categories_by_tab:
            del self.state.categories_by_tab[self.selected_tab]
        
        self.load_categories()

    def tovari_interface(self):
        self.state.selected_category = None
        self.tab1_content.content = self._create_interface_layout(
            "Поиск товаров", self.category_list_view
        )
        self.load_categories()

    def _create_interface_layout(self, search_label, category_list):
        return ft.Container(
            margin=20,
            padding=10,
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.TextField(label=search_label, expand=True),
                            ft.ElevatedButton(
                                "Добавить категорию",
                                on_click=self._show_add_category_dialog
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    category_list,
                ],
                expand=True,
                spacing=10            
            )
        )
    
    @contextmanager
    def _loading_indicator(self):
        progress_bar = ft.ProgressBar()
        current_tab = self.tab_contents[self.selected_tab]
        
        loading_container = ft.Container(
            content=ft.Column(
                [progress_bar],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            expand=True
        )
        
        original_content = current_tab["main_container"].content
        current_tab["main_container"].content = ft.Stack(
            controls=[
                original_content,
                loading_container
            ],
            expand=True
        )
        
        try:
            self.page.update()
            yield
        finally:
            current_tab["main_container"].content = original_content
            self.page.update()

    def load_categories(self):
        with self._loading_indicator():
            # Всегда очищаем кеш перед загрузкой
            if self.selected_tab in self.state.categories_by_tab:
                del self.state.categories_by_tab[self.selected_tab]
                
            data = self._fetch_data(
                f"{API_URL}/categories",
                params={
                    "tab": self.selected_tab,
                    "parent_id": None
                },
                error_message="Ошибка при загрузке категорий"
            )
            if data:
                self.state.categories_by_tab[self.selected_tab] = data
                # Принудительно обновляем все категории
                for cat in data:
                    cat['content_type'] = cat.get('content_type', 'default')
            self._update_category_list()
            
            # Явное обновление интерфейса
            self.page.update()

    def _fetch_data(self, url, params=None, error_message=""):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self._show_snackbar(f"{error_message}: {str(e)}")
            return None

    def _update_category_list(self):
        current_tab = self.tab_contents[self.selected_tab]
        current_categories = self.state.categories_by_tab.get(self.selected_tab, [])
        
        # Полная пересборка элементов списка
        current_tab["category_list"].controls = [
            self._create_category_card(category) 
            for category in current_categories
        ]
        
        # Явное обновление всех связанных элементов
        current_tab["category_list"].update()
        current_tab["main_container"].update()
        self.page.update()

    def _create_category_card(self, category):
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                ft.Text(category['name'], size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Параметр: {category['parameter'] or 'Не указан'}", size=14),
                                ft.Text(f"Ед. измерения: {category['unit']}", size=14)
                            ],
                            expand=True,
                            spacing=5
                        ),
                        ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(
                                    text="Изменить",
                                    on_click=lambda e, cat=category: self._handle_edit_category(cat)
                                ),
                                ft.PopupMenuItem(
                                    text="Удалить", 
                                    on_click=lambda e, cat=category: self._handle_delete_category(cat)
                                )
                            ]
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=10,
                margin=5,
                on_click=lambda e: self._show_category_content(category),
            ),
            elevation=3,
            margin=5
        )
    
    def _show_category_content(self, category):
        self.state.selected_category = category
        current_tab = self.tab_contents[self.selected_tab]
        
        # Очищаем предыдущие данные перед загрузкой новых
        current_tab["content_view"].controls = []  # <-- Очистка товаров
        current_tab["category_list"].controls = [] # <-- Очистка подкатегорий
        
        new_content = ft.Container(
            margin=20,
            padding=10,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.ElevatedButton("Назад", on_click=lambda e: self.update_interface()),
                            ft.TextField(label="Поиск", expand=True),
                            self._create_content_button(category)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    current_tab["category_list"] if category['content_type'] == 'categories' 
                        else current_tab["content_view"]
                ],
                expand=True
            )
        )
        
        current_tab["main_container"].content = new_content
        self.page.update()  # <-- Принудительное обновление интерфейса
        
        if category['content_type'] in ['default', 'items']:
            self._load_category_items(category)
        elif category['content_type'] == 'categories':
            self._load_subcategories(category)

    def _create_content_button(self, category):
        # Для всех категорий с content_type=default показываем оба варианта
        if category['content_type'] == 'default':
            return ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(
                        text="Создать товар",
                        on_click=lambda e, cat=category: self._show_add_item_dialog(cat)
                    ),
                    ft.PopupMenuItem(
                        text="Создать категорию",
                        on_click=lambda e, cat=category: self._show_add_subcategory_dialog(cat)
                    )
                ]
            )
        
        # Для категорий с другим content_type сохраняем текущую логику
        elif category['content_type'] == 'categories':
            return ft.ElevatedButton(
                "Создать категорию", 
                on_click=lambda e, cat=category: self._show_add_subcategory_dialog(cat)
            )
        
        elif category['content_type'] == 'items':
            return ft.ElevatedButton(
                "Создать товар", 
                on_click=lambda e, cat=category: self._show_add_item_dialog(cat)
            )
        
        return ft.Container()

    def _load_category_items(self, category, force_refresh=False):
        if force_refresh:
            # Добавляем параметр для обхода кеша
            params = {"category_id": category['id'], "_": datetime.now().timestamp()}
        else:
            params = {"category_id": category['id']}

        data = self._fetch_data(
            f"{API_URL}/items",
            params=params,
            error_message="Ошибка при загрузке товаров"
        )
        current_tab = self.tab_contents[self.selected_tab]
        with self._loading_indicator():
            # Явная очистка перед загрузкой новых данных
            current_tab["content_view"].controls = []  # <-- Добавлено
            self.page.update()
            
            data = self._fetch_data(
                f"{API_URL}/items",
                params={"category_id": category['id']},
                error_message="Ошибка при загрузке товаров"
            )
            if data:
                current_tab["content_view"].controls = [
                    self._create_item_card(item, category)
                    for item in data
                ]
                if not data:
                    self._show_snackbar("В этой категории пока нет товаров")
            else:
                current_tab["content_view"].controls = []

    def _load_subcategories(self, category):
        current_tab = self.tab_contents[self.selected_tab]
        with self._loading_indicator():
            data = self._fetch_data(
                f"{API_URL}/categories",
                params={"parent_id": category['id']},
                error_message="Ошибка при загрузке подкатегорий"
            )
            if data:
                current_tab["category_list"].controls = [
                    self._create_category_card(subcat) for subcat in data
                ]
                if not data:
                    self._show_snackbar("В этой категории пока нет подкатегорий")

    @lru_cache(maxsize=32)
    def _get_image_url(self, image_id):
        return f"{self.IMAGES_BASE_URL}/{image_id}" if image_id else f"{self.IMAGES_BASE_URL}/default"

    def _create_item_card(self, item, category):
        image_with_icon = ft.Container(
            width=120,
            height=100,
            border_radius=ft.border_radius.all(10),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Image(
                        src=self._get_image_url(item.get("image_id")),
                        width=120,
                        height=100,
                        fit=ft.ImageFit.COVER,
                        error_content=ft.Container(
                            bgcolor=ft.Colors.GREY_300,
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
                                name=ft.Icons.MIC_NONE if item.get("mic") == 1 else ft.Icons.MIC_OFF_OUTLINED,
                                size=16,
                                color=ft.Colors.BLACK87
                            )
                        )
                    )
                ]
            )
        )

        parameter_text = ""
        if category and category.get('parameter') and item.get('parameter_value'):
            parameter_text = f"{category['parameter']}: {item['parameter_value']}"

        return ft.Container(
            content=ft.Card(
                content=ft.Column(
                    controls=[
                        image_with_icon,
                        ft.Container(
                            content=ft.Text(
                                value=item['name'], 
                                weight=ft.FontWeight.BOLD, 
                                size=16,
                                text_align=ft.TextAlign.CENTER),
                            padding=ft.padding.only(top=5),
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            content=ft.Text(
                                value=f"Ед. измерения: {item['unit']}", 
                                size=14,
                                text_align=ft.TextAlign.CENTER),
                            padding=ft.padding.only(top=5),
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            content=ft.Text(
                                value=parameter_text,
                                size=14,
                                text_align=ft.TextAlign.CENTER),
                            padding=ft.padding.only(top=5),
                            alignment=ft.alignment.center,
                            visible=bool(parameter_text)
                        ),
                        ft.Divider(height=1, color=ft.Colors.GREY_300),
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                value=f"Стоймость: {item['cost_price']:,} UZS".replace(",", " ").replace(" ", "\u00A0", 3),
                                                color=ft.Colors.ORANGE, 
                                                size=14,
                                                text_align=ft.TextAlign.START
                                            ),
                                            ft.Text(
                                                value=f"Цена: {item['selling_price']:,} UZS".replace(",", " ").replace(" ", "\u00A0", 3),
                                                color=ft.Colors.ORANGE,
                                                weight=ft.FontWeight.BOLD, 
                                                size=16,
                                                text_align=ft.TextAlign.START
                                            ),
                                        ],
                                        spacing=5,
                                        horizontal_alignment=ft.CrossAxisAlignment.START,
                                    ),
                                    ft.PopupMenuButton(
                                        items=[
                                            ft.PopupMenuItem(
                                                text="Изменить",
                                                on_click=lambda e, it=item: self._handle_edit_item(it, category)
                                            ),
                                            ft.PopupMenuItem(
                                                text="Удалить",
                                                on_click=lambda e, it=item: self._handle_delete_item(it, category)
                                            )
                                        ]
                                    )
                                ],
                            ),
                            padding=ft.padding.symmetric(horizontal=10),
                            expand=True
                        )
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True
                ),
                elevation=2
            ),
            width=300,
            height=250
        )

    def _show_add_subcategory_dialog(self, parent_category):
        name_field = ft.TextField(label="Название подкатегории", autofocus=True)
        param_field = ft.TextField(
            label="Параметр (необязательно)",
            value=parent_category.get('parameter', '')
        )
        unit_field = ft.TextField(label="Единица измерения", value=parent_category['unit'])

        def close_dlg(e):
            self.page.close(dlg)
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Добавить подкатегорию"),
            content=ft.Column(
                controls=[
                    name_field,
                    param_field,
                    unit_field,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Создать",
                                on_click=lambda e: [
                                    self._create_subcategory(
                                        parent_category,
                                        name_field.value,
                                        param_field.value,
                                        unit_field.value
                                    ),
                                    close_dlg(e)
                                ]
                            ),
                            ft.ElevatedButton("Отмена", on_click=close_dlg)
                        ],
                        alignment=ft.MainAxisAlignment.END
                    )
                ],
                tight=True
            )
        )
        self.page.open(dlg)
        self.page.update()

    def _create_subcategory(self, parent_category, name, param, unit):
        try:
            if not name.strip():
                raise ValueError("Название подкатегории обязательно")
            if not unit.strip():
                raise ValueError("Единица измерения обязательна")

            # Создаем подкатегорию и проверяем ответ
            response = requests.post(
                f"{API_URL}/categories",
                json={
                    "name": name,
                    "parameter": param,
                    "unit": unit,
                    "tab": parent_category['tab'],
                    "parent_id": parent_category['id'],
                    "content_type": "default"
                }
            )
            response.raise_for_status()  # Важно: проверяем статус ответа

            # Обновляем тип контента родителя при необходимости
            if parent_category['content_type'] == 'default':
                update_response = requests.put(
                    f"{API_URL}/categories/{parent_category['id']}",
                    json={"content_type": "categories"}
                )
                update_response.raise_for_status()
                parent_category['content_type'] = 'categories'

            self._load_subcategories(parent_category)
            self._show_snackbar("Подкатегория успешно создана!")

        except requests.exceptions.HTTPError as err:
            error_msg = err.response.json().get("detail", err.response.text)
            self._show_snackbar(f"Ошибка сервера: {error_msg}")
        except Exception as err:
            self._show_snackbar(str(err))
        finally:
            if self.page.overlay:
                self.page.close(self.page.overlay[-1])
            self.page.update()

    def _show_add_category_dialog(self, e):
        name_field = ft.TextField(label="Название категории", autofocus=True)
        param_field = ft.TextField(label="Параметр (необязательно)")
        unit_field = ft.TextField(label="Единица измерения")

        def close_dlg(e):
            self.page.close(dlg)
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Добавить категорию"),
            content=ft.Column(
                controls=[
                    name_field,
                    param_field,
                    unit_field,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Создать",
                                on_click=lambda e: [
                                    self._create_category(
                                        name_field.value,
                                        param_field.value,
                                        unit_field.value
                                    ),
                                    self.page.close(dlg)
                                ]
                            ),
                            ft.ElevatedButton("Отмена", on_click=close_dlg)
                        ],
                        alignment=ft.MainAxisAlignment.END
                    )
                ],
                tight=True
            )
        )
        self.page.open(dlg)
        self.page.update()

    def _show_add_item_dialog(self, category):
        self.selected_image_path = None
        self.mic_checkbox = ft.Checkbox(label="Имеется микрофон")

        # Берем название параметра из категории для label
        parameter_label = category.get('parameter', 'Параметр')

        fields = [
            {"label": "Название товара", "required": True},
            {
                "label": parameter_label,  # Используем параметр из категории только как заголовок
                "required": True
            },
            {"label": "Себестоимость", "required": True, "keyboard": ft.KeyboardType.NUMBER},
            {"label": "Цена с наценкой", "required": True, "keyboard": ft.KeyboardType.NUMBER},
            {"type": "checkbox", "control": self.mic_checkbox},
            {"label": "Изображение", "type": "file"}
        ]

        self._create_dialog(
            title="Добавить товар",
            category=category,
            fields=fields,
            on_confirm=lambda e: self._create_item(category)
        )

    def _handle_image_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_image_path = e.files[0].path
            # Всегда обновляем текстовый элемент текущего диалога
            if hasattr(self, 'dialog_fields'):
                for field, control in self.dialog_fields:
                    if field.get('type') == 'file':
                        control.value = os.path.basename(self.selected_image_path)  # Только имя файла
                        control.update()  # Принудительное обновление элемента
                        break

    def _create_item(self, category):
        errors = self._validate_dialog_fields()
        if errors:
            self._show_snackbar("\n".join(errors))
            return

        image_id = None
        if self.selected_image_path:
            with open(self.selected_image_path, "rb") as f:
                files = {"image": (os.path.basename(self.selected_image_path), f)}
                try:
                    response = requests.post(f"{API_URL}/upload_image", files=files)
                    response.raise_for_status()
                    image_id = response.json()["image_id"]
                except Exception as e:
                    self._show_snackbar(f"Ошибка загрузки изображения: {str(e)}")
                    return

        item_data = {
            "name": self.dialog_fields[0][1].value.strip(),
            "parameter_value": self.dialog_fields[1][1].value.strip(),
            "cost_price": int(self.dialog_fields[2][1].value),
            "selling_price": int(self.dialog_fields[3][1].value),
            "category_id": category['id'],
            "unit": category['unit'],
            "image_id": image_id,
            "mic": 1 if self.mic_checkbox.value else 0  # Добавляем значение чекбокса
        }


        try:
            response = requests.post(f"{API_URL}/items", json=item_data)
            if response.ok:
                if category['content_type'] == 'default':
                    # Обновляем контент тип на 'items'
                    requests.put(
                        f"{API_URL}/categories/{category['id']}",
                        json={"content_type": "items"}
                    )
                    category['content_type'] = 'items'
                self._load_category_items(category)
                self._show_snackbar("Товар успешно создан!")
            else:
                self._show_snackbar(f"Ошибка: {response.text}")
        except Exception as e:
            self._show_snackbar(f"Ошибка: {str(e)}")
        finally:
            self._close_dialog()

    # Обновленная фабрика диалогов
    def _create_dialog(self, title, category, fields, on_confirm):
        self.selected_image_path = None
        self.dialog_fields = []
        controls = []
        
        for field in fields:
            if field.get('type') == 'file':
                row = ft.Row([
                    ft.ElevatedButton(
                        "Выбрать изображение",
                        on_click=lambda e: self.image_picker.pick_files(
                            allow_multiple=False,
                            allowed_extensions=["jpg", "png", "jpeg"]
                        )
                    ),
                    ft.Text("Файл не выбран", color=ft.Colors.GREY)
                ])
                self.dialog_fields.append((field, row.controls[1]))
                controls.append(row)
            elif field.get('type') == 'checkbox':
                controls.append(field['control'])
            else:
                # Создаем TextField с label но без предустановленного значения
                tf = ft.TextField(
                    label=field['label'],
                    keyboard_type=field.get('keyboard'),
                    expand=True,
                    # Убрали read_only и value
                )
                self.dialog_fields.append((field, tf))
                controls.append(tf)

        controls.extend([
            ft.Row([
                ft.ElevatedButton("Создать", on_click=on_confirm),
                ft.ElevatedButton("Отмена", on_click=self._close_dialog)
            ], alignment=ft.MainAxisAlignment.END)
        ])

        self.current_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Column(
                controls=controls,
                spacing=15,
                scroll=ft.ScrollMode.ADAPTIVE
            )
        )
        
        self.image_picker.on_result = self._handle_image_picked
        self.page.open(self.current_dialog)
        self.page.update()

    def _create_category(self, name, param, unit):
        try:
            if not name.strip():
                raise ValueError("Название категории обязательно")
            if not unit.strip():
                raise ValueError("Единица измерения обязательна")

            response = requests.post(
                f"{API_URL}/categories",
                json={
                    "name": name,
                    "parameter": param,
                    "unit": unit,
                    "tab": self.selected_tab,
                    "content_type": "default"
                }
            )
            response.raise_for_status()

            # Принудительное обновление данных
            self.state.categories_by_tab.pop(self.selected_tab, None)
            self.load_categories()
            
            # Явное обновление всех элементов интерфейса
            current_tab = self.tab_contents[self.selected_tab]
            current_tab["main_container"].content = self._create_interface_layout(
                "Поиск", 
                current_tab["category_list"]
            )
            current_tab["main_container"].update()
            self.page.update()

            self._show_snackbar("Категория успешно создана!")
            
        except requests.exceptions.HTTPError as err:
            self._show_snackbar(f"Ошибка сервера: {err.response.text}")
        except Exception as err:
            self._show_snackbar(str(err))
        finally:
            self.page.close(self.page.overlay[-1])  # Гарантированное закрытие диалога
            self.page.update()

    def _close_dialog(self, e=None):
        # Закрывает последнее открытое диалоговое окно
        if self.page.overlay and isinstance(self.page.overlay[-1], ft.AlertDialog):
            self.page.close(self.page.overlay[-1])
            self.page.update()

    def _validate_dialog_fields(self):
        errors = []
        for (field, control) in self.dialog_fields:
            value = control.value if isinstance(control, ft.TextField) else control.value
            if field.get('required') and not str(value).strip():
                errors.append(f"Поле '{field['label']}' обязательно для заполнения")
            if field.get('keyboard') == ft.KeyboardType.NUMBER and not str(value).isdigit():
                errors.append(f"Поле '{field['label']}' должно быть числом")
        return errors

    def _show_snackbar(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

class AppState:
    def __init__(self):
        self.categories_by_tab = {}
        self.selected_category = None

def tovari_page(e: ft.ControlEvent):
    page = e.page
    page.clean()
    TovariPage(page)