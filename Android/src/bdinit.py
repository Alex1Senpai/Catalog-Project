from typing import Optional
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
SAVE_DIR = BASE_DIR / "backend"
DEFAULT_DB_PATH = SAVE_DIR / "back.db"

def connect_db():
    return sqlite3.connect(DEFAULT_DB_PATH)

def check_db_structure():
    """Проверяет и создает всю необходимую структуру БД"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Создаем таблицы если их нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                parameter TEXT,
                unit TEXT,
                parent_id INTEGER,
                tab INTEGER DEFAULT 0,
                content_type TEXT DEFAULT 'default'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                parameter_value TEXT,
                unit TEXT,
                cost_price INTEGER,
                selling_price INTEGER,
                image_id TEXT,
                mic INTEGER DEFAULT 0,
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )
        """)
        
        # Добавляем недостающие колонки
        cursor.execute("PRAGMA table_info(categories)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'parent_id' not in columns:
            cursor.execute("ALTER TABLE categories ADD COLUMN parent_id INTEGER")
        if 'tab' not in columns:
            cursor.execute("ALTER TABLE categories ADD COLUMN tab INTEGER DEFAULT 0")
        
        cursor.execute("PRAGMA table_info(items)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'mic' not in columns:
            cursor.execute("ALTER TABLE items ADD COLUMN mic INTEGER DEFAULT 0")
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"DB structure error: {e}")
    finally:
        conn.close()


# Инициализация БД при старте
check_db_structure()

def get_categories(parent_id=None, tab=None):
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT 
                id, 
                name, 
                parameter,
                unit,
                parent_id,
                tab,
                content_type
            FROM categories
            WHERE 1=1
        """
        
        params = []
        
        if parent_id is not None:
            query += " AND parent_id = ?"
            params.append(parent_id)
        else:
            query += " AND parent_id IS NULL"
            
        if tab is not None:
            query += " AND tab = ?"
            params.append(tab)
            
        cursor.execute(query, params)
        
        return [
            {
                'id': row[0],
                'name': row[1],
                'parameter': row[2],
                'unit': row[3],
                'parent_id': row[4],
                'tab': row[5],
                'content_type': row[6] if len(row) > 6 else 'default'  # Добавляем content_type
            }
            for row in cursor.fetchall()
        ]
    except sqlite3.Error as e:
        print(f"Get categories error: {e}")
        return []
    finally:
        conn.close()


def get_items(category_id: int) -> list[dict]:
    """Получает все товары/услуги для указанной категории"""
    conn = connect_db()
    cursor = conn.cursor()
    
    query = """
    WITH RECURSIVE subcategories AS (
        SELECT id FROM categories WHERE id = ?
        UNION ALL
        SELECT c.id FROM categories c
        INNER JOIN subcategories s ON c.parent_id = s.id
    )
    SELECT 
        i.id, 
        i.name, 
        i.category_id,
        i.parameter_value, 
        i.unit, 
        i.cost_price, 
        i.selling_price, 
        i.image_id,
        i.mic,
        c.name as category_name,
        c.parameter as category_parameter
    FROM items i
    JOIN categories c ON i.category_id = c.id
    WHERE i.category_id IN (SELECT id FROM subcategories)
    """
    
    params = [category_id]
        
    try:
        cursor.execute(query, [category_id])
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0],
                'name': row[1],
                'category_id': row[2],
                'parameter_value': row[3],
                'unit': row[4],
                'cost_price': row[5],
                'selling_price': row[6],
                'image_id': row[7],
                'mic': row[8],
                'category_name': row[9],
                'category_parameter': row[10]
            })
        return items
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        conn.close()