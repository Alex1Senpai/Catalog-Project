import json
import os
import logging
import uuid
import hashlib
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship, joinedload
import bcrypt
from enum import Enum as PyEnum

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants and paths
SERVER_DIR = r"C:\serverShiDari"
IMGS_DIR = os.path.join(SERVER_DIR, "Imgs")
CONFIG_PATH = os.path.join(SERVER_DIR, "db.json")
DEFAULT_DB_PATH = os.path.join(SERVER_DIR, "back.db")
DEFAULT_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "default.jpg")

app = FastAPI()

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(SERVER_DIR, exist_ok=True)
os.makedirs(IMGS_DIR, exist_ok=True)

# Database configuration
Base = declarative_base()

engine = create_engine(f"sqlite:///{os.path.abspath(DEFAULT_DB_PATH)}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enums
class ContentType(str, PyEnum):
    DEFAULT = "default"  # Новое значение
    CATEGORIES = "categories"
    ITEMS = "items"

# SQLAlchemy models
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parameter = Column(String, nullable=True)
    unit = Column(String)
    tab = Column(Integer)  # Оставляем tab
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    content_type = Column(Enum(ContentType), default=ContentType.DEFAULT)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete")
    items = relationship("Item", back_populates="category", cascade="all, delete")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    parameter_value = Column(String)
    unit = Column(String)
    cost_price = Column(Integer)
    selling_price = Column(Integer)
    mic = Column(Integer)  # Переносим mic сюда
    image_id = Column(String, nullable=True)
    category = relationship("Category", back_populates="items")

# Pydantic schemas
class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int
    model_config = {
        "from_attributes": True
    }

class UserBase(BaseModel):
    username: str
    full_name: str

class UserRegister(UserBase):
    password: str
    role_id: int

class UserResponse(UserBase):
    id: int
    role: Optional[str]
    model_config = {
        "from_attributes": True
    }

class CategoryBase(BaseModel):
    name: str
    unit: str
    tab: int
    parent_id: Optional[int] = None
    content_type: ContentType = ContentType.DEFAULT  # Изменено на DEFAULT

class CategoryCreate(CategoryBase):
    parameter: Optional[str] = None

class CategoryResponse(CategoryCreate):
    id: int
    children: List['CategoryResponse'] = []
    items: List['ItemResponse'] = []
    model_config = {
        "from_attributes": True
    }

class ItemBase(BaseModel):
    name: str
    category_id: int
    parameter_value: str
    unit: str
    cost_price: int
    selling_price: int
    mic: int

class ItemCreate(ItemBase):
    image_id: Optional[str] = None

class ItemResponse(ItemCreate):
    id: int
    mic: int  # Явно добавляем поле
    model_config = {
        "from_attributes": True
    }

# Update models
class RoleUpdate(RoleBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    password: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parameter: Optional[str] = None
    unit: Optional[str] = None
    mic: Optional[int] = None
    tab: Optional[int] = None
    content_type: Optional[ContentType] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    parameter_value: Optional[str] = None
    unit: Optional[str] = None
    cost_price: Optional[int] = None
    selling_price: Optional[int] = None
    image_id: Optional[str] = None

# Utility functions
def get_db_path():
    try:
        with open(CONFIG_PATH, "r") as f:
            return f"sqlite:///{os.path.abspath(json.load(f).get('db_file_path', DEFAULT_DB_PATH))}"
    except FileNotFoundError:
        logger.warning(f"Config file {CONFIG_PATH} not found. Using default path.")
        return f"sqlite:///{os.path.abspath(DEFAULT_DB_PATH)}"

def init_db():
    if not os.path.exists(DEFAULT_DB_PATH):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized with nested categories support")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    else:
        logger.info("Database already exists")

def save_db_path(db_path: str):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"db_file_path": db_path}, f)

def save_image(image_file: UploadFile) -> str:
    image_id = str(uuid.uuid4())
    image_path = os.path.join(IMGS_DIR, f"{image_id}.jpg")
    with open(image_path, "wb") as buffer:
        buffer.write(image_file.file.read())
    return image_id

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

# Database dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Service functions
def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()

def get_role_by_id(db: Session, role_id: int) -> Role:
    return db.query(Role).filter(Role.id == role_id).first()

def get_category_by_id(db: Session, category_id: int) -> Category:
    return db.query(Category).filter(Category.id == category_id).first()

def get_item_by_id(db: Session, item_id: int) -> Item:
    return db.query(Item).filter(Item.id == item_id).first()

# API endpoints
@app.post("/register", response_model=UserResponse)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    role = get_role_by_id(db, user.role_id)
    if not role:
        raise HTTPException(status_code=400, detail="Role does not exist")

    hashed_password = pwd_context.hash(user.password)
    new_user = User(
        username=user.username,
        password=hashed_password,
        full_name=user.full_name,
        role_id=user.role_id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "full_name": new_user.full_name,
        "role": role.name
    }

#################################User endpoints##############################################

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)

    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.username == "admin" and not os.path.exists(CONFIG_PATH):
        save_db_path(DEFAULT_DB_PATH)
        logger.info("Created default config for admin user")

    return {"message": "Login successful", "user_id": user.id}

@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    result = []
    for user in users:
        role = get_role_by_id(db, user.role_id)
        result.append({
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": role.name if role else None
        })
    return result

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    role = get_role_by_id(db, db_user.role_id)
    return {
        "id": db_user.id,
        "username": db_user.username,
        "full_name": db_user.full_name,
        "role": role.name if role else None
    }

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    current_data = {
        "id": db_user.id,
        "username": db_user.username,
        "full_name": db_user.full_name,
        "role": get_role_by_id(db, db_user.role_id).name if db_user.role_id else None
    }

    update_data = user.model_dump(exclude_unset=True)

    if "username" in update_data:
        existing_user = get_user_by_username(db, update_data["username"])
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Username already exists")

    if "password" in update_data:
        update_data["password"] = pwd_context.hash(update_data["password"])

    if "role_id" in update_data and not get_role_by_id(db, update_data["role_id"]):
        raise HTTPException(status_code=400, detail="Role does not exist")

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)

    role = get_role_by_id(db, db_user.role_id)
    return {
        "id": db_user.id,
        "username": db_user.username,
        "full_name": db_user.full_name,
        "role": role.name if role else None
    }

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

#################################Role endpoints##############################################

@app.post("/roles", response_model=RoleResponse)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    if db.query(Role).filter(Role.name == role.name).first():
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = Role(name=role.name)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

@app.get("/roles", response_model=List[RoleResponse])
def get_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()

@app.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@app.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role: RoleUpdate, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(status_code=404, detail="Role not found")

    current_data = RoleResponse.from_orm(db_role)

    if role.name != db_role.name:
        existing_role = db.query(Role).filter(Role.name == role.name).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="Role name already exists")

    db_role.name = role.name
    db.commit()
    db.refresh(db_role)

    return db_role

@app.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = db.get(Role, role_id)

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.delete(role)
    db.commit()
    return {"message": "Role deleted successfully"}

#################################Category endpoints##############################################

@app.post("/categories", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # Валидация tab
    if category.tab < 0:
        raise HTTPException(status_code=400, detail="tab must be positive number")
    
    # Проверяем существование родительской категории только если parent_id указан
    if category.parent_id is not None:
        parent = get_category_by_id(db, category.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
        
        # Проверяем можно ли добавить подкатегорию
        if parent.content_type == ContentType.ITEMS:
            raise HTTPException(
                status_code=400,
                detail="Cannot add subcategory to items-only category"
            )
        
        # Если родитель DEFAULT и в нем уже есть товары
        if parent.content_type == ContentType.DEFAULT and parent.items:
            raise HTTPException(
                status_code=400,
                detail="This category already contains items, cannot add subcategories"
            )

    # Создаем категорию, parent_id будет NULL если не указан
    new_category = Category(**category.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    # Обновляем родителя если нужно
    if category.parent_id:
        parent = get_category_by_id(db, category.parent_id)
        if parent.content_type == ContentType.DEFAULT:
            parent.content_type = ContentType.CATEGORIES
            db.commit()
    
    return new_category

@app.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    parent_id: Optional[int] = None, 
    tab: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Category)
    
    # Основной фильтр по tab
    if tab is not None:
        query = query.filter(Category.tab == tab)
    
    # Фильтр по parent_id
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    else:
        query = query.filter(Category.parent_id == None)
    
    # Явная проверка на корневые категории
    if tab is not None and parent_id is None:
        query = query.filter(Category.tab == tab, Category.parent_id == None)
    
    categories = query.options(
        joinedload(Category.children),
        joinedload(Category.items)
    ).all()
    
    result = []
    for cat in categories:
        children_data = [
            CategoryResponse(
                id=child.id,
                name=child.name,
                parameter=child.parameter,
                unit=child.unit,
                tab=child.tab,
                parent_id=child.parent_id,
                content_type=child.content_type,
                children=[],
                items=[]
            ) for child in cat.children
        ]
        
        items_data = [
            ItemResponse(
                id=item.id,
                name=item.name,
                category_id=item.category_id,
                parameter_value=item.parameter_value,
                unit=item.unit,
                cost_price=item.cost_price,
                selling_price=item.selling_price,
                mic=item.mic,  # Добавлено!
                image_id=item.image_id
            ) for item in cat.items
        ]
        
        category_response = CategoryResponse(
            id=cat.id,
            name=cat.name,
            parameter=cat.parameter,
            unit=cat.unit,
            tab=cat.tab,  # Добавлено!
            parent_id=cat.parent_id,
            content_type=cat.content_type,
            children=children_data,
            items=items_data
        )
        result.append(category_response)
    
    return result

@app.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    children_data = [
        CategoryResponse(
            id=child.id,
            name=child.name,
            parameter=child.parameter,
            unit=child.unit,
            tab=child.tab,
            parent_id=child.parent_id,
            content_type=child.content_type,
            children=[],
            items=[]
        ) for child in db_category.children
    ]
    
    items_data = [
        ItemResponse(
            id=item.id,
            name=item.name,
            category_id=item.category_id,
            parameter_value=item.parameter_value,
            unit=item.unit,
            cost_price=item.cost_price,
            selling_price=item.selling_price,
            mic=item.mic,
            image_id=item.image_id
        ) for item in db_category.items
    ]
    
    return CategoryResponse(
        id=db_category.id,
        name=db_category.name,
        parameter=db_category.parameter,
        unit=db_category.unit,
        tab=db_category.tab,  # Добавлено!
        parent_id=db_category.parent_id,
        content_type=db_category.content_type,
        children=children_data,
        items=items_data
    )

@app.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category.model_dump(exclude_unset=True)
    
    # Валидация tab
    if "tab" in update_data and update_data["tab"] < 0:
        raise HTTPException(status_code=400, detail="tab must be positive number")
    
    # Валидация tab
    if "tab" in update_data and update_data["tab"] < 0:
        raise HTTPException(status_code=400, detail="tab must be positive number")

    if "name" in update_data:
        existing_category = db.query(Category).filter(
            Category.name == update_data["name"],
            Category.parent_id == db_category.parent_id,
            Category.id != category_id
        ).first()
        if existing_category:
            raise HTTPException(status_code=400, detail="Category name already exists in this parent")

    if "content_type" in update_data:
        if update_data["content_type"] != db_category.content_type:
            if update_data["content_type"] == ContentType.ITEMS and db_category.children:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change to items content type when category has children"
                )
            elif update_data["content_type"] == ContentType.CATEGORIES and db_category.items:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change to categories content type when category has items"
                )
            elif update_data["content_type"] == ContentType.DEFAULT and (db_category.children or db_category.items):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change to default content type when category has content"
                )

    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}

################################# Item endpoints ##############################################
@app.post("/items", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    category = get_category_by_id(db, item.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Проверяем можно ли добавить товар
    if category.content_type == ContentType.CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail="Cannot add item to categories-only category"
        )
    
    # Если категория DEFAULT и в ней уже есть подкатегории
    if category.content_type == ContentType.DEFAULT and category.children:
        raise HTTPException(
            status_code=400,
            detail="This category already contains subcategories, cannot add items"
        )

    if item.mic not in (0, 1):
        raise HTTPException(status_code=400, detail="mic must be 0 or 1")

    new_item = Item(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    # Обновляем категорию если нужно
    if category.content_type == ContentType.DEFAULT:
        category.content_type = ContentType.ITEMS
        db.commit()
    
    return new_item

@app.get("/items/search", response_model=List[ItemResponse])
def search_items(query: str, db: Session = Depends(get_db)):
    return db.query(Item).filter(Item.name.contains(query)).all()

@app.get("/items", response_model=List[ItemResponse])
def get_items(category_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Item)
    if category_id:
        query = query.filter(Item.category_id == category_id)
    return query.all()

@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item.model_dump(exclude_unset=True)

    if "category_id" in update_data:
        new_category = get_category_by_id(db, update_data["category_id"])
        if not new_category:
            raise HTTPException(status_code=404, detail="New category not found")
        if new_category.content_type != ContentType.ITEMS:
            raise HTTPException(
                status_code=400,
                detail="New category must have content_type='items'"
            )
        
    if "mic" in update_data and update_data["mic"] not in (0, 1):
        raise HTTPException(status_code=400, detail="mic must be 0 or 1")

    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)  # Updated line
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}

#################################Image endpoints##############################################

@app.post("/upload_image")
def upload_image(image: UploadFile = File(...)):
    return {"image_id": save_image(image)}


@app.get("/imgs/{image_id}")
def get_image(image_id: str):
    image_path = os.path.join(IMGS_DIR, f"{image_id}.jpg")

    if not os.path.exists(image_path):
        if os.path.exists(DEFAULT_IMAGE_PATH):
            return FileResponse(DEFAULT_IMAGE_PATH)
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path)

#################################Files endpoint##############################################

@app.get("/list_imgs")
def list_imgs():
    if not os.path.exists(IMGS_DIR):
        raise HTTPException(status_code=404, detail="Папка Imgs не найдена")

    files = []
    for f in os.listdir(IMGS_DIR):
        if f.endswith(".jpg") and os.path.isfile(os.path.join(IMGS_DIR, f)):
            files.append(f)
    return {"files": files}

@app.get("/download_img/{image_id}")
def download_img(image_id: str):
    img_path = os.path.join(IMGS_DIR, image_id)
    if not os.path.exists(img_path):
        if os.path.exists(DEFAULT_IMAGE_PATH):
            return FileResponse(DEFAULT_IMAGE_PATH)
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(img_path)

@app.get("/download_db")
def download_db():
    if not os.path.exists(DEFAULT_DB_PATH):
        raise HTTPException(status_code=404, detail="Файл back.db не найден")
    return FileResponse(DEFAULT_DB_PATH, filename="back.db")

@app.get("/db_hash")
def get_db_hash():
    with open(DEFAULT_DB_PATH, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()
    
@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    contracts_dir = os.path.join(SERVER_DIR, "history")
    os.makedirs(contracts_dir, exist_ok=True)
    
    # Сохраняем файл с оригинальным именем
    file_path = os.path.join(contracts_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Таблицы в базе данных созданы успешно!")
