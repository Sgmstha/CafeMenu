"""
Campus Café - Database Simulation & Data Models
-----------------------------------------------
This module defines the Pydantic schemas (data transfer objects and validators)
and simulates an in-memory database storage system for quick testing.

TODO:
    1. Replace the in-memory DB storage (`DB` class) with a real persistent SQL database 
       (e.g., PostgreSQL or SQLite) using an ORM like SQLAlchemy or SQLModel.
    2. Add migration support using Alembic.
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid


# ── Pydantic Schemas / Validation Models ──────────────────────────────────────

class UserCreate(BaseModel):
    """Schema validated when registering a new user."""
    name: str
    phone: str
    password: str

class UserLogin(BaseModel):
    """Schema validated when logging in a user."""
    phone: str
    password: str

class OTPVerify(BaseModel):
    """Schema validated during SMS OTP confirmation."""
    phone: str
    otp: str

class MenuItem(BaseModel):
    """Complete schema for representing a single menu item."""
    id: str = ""
    name: str
    description: str
    price: float
    category: str
    available: bool = True

class MenuItemCreate(BaseModel):
    """Schema validated when creating or updating a menu item."""
    name: str
    description: str
    price: float
    category: str

class BulkMenuDelete(BaseModel):
    """Schema validated when removing selected menu items."""
    ids: list[str]

class OrderItem(BaseModel):
    """Schema representing an individual line item inside a customer order."""
    item_id: str
    name: str
    quantity: int
    price: float

class OrderCreate(BaseModel):
    """Schema validated when placing an order from the cart."""
    items: list[OrderItem]
    payment_method: str          # Must be one of: "coin" | "cash" | "online"
    customer_name: str
    customer_phone: str

class CoinLoad(BaseModel):
    """Schema validated when loading digital coins into a user's wallet."""
    phone: str
    amount: float

class OTPRequest(BaseModel):
    """Schema validated when requesting a phone OTP verification before ordering."""
    phone: str
    name: str


# ── In-Memory Database Simulation ────────────────────────────────────────────

class DB:
    """
    Mock Database structure. All data is wiped when the server restarts.
    
    TODO: Replace this entire class with a database driver & ORM models.
    """
    # Key: phone (str) -> Value: dict {id, name, phone, password_hash, coins, role}
    users: dict = {}            
    
    # Key: item_id (str) -> Value: dict {id, name, description, price, category, available}
    menu_items: dict = {}       
    
    # Key: date_str (str, e.g., '2026-05-29') -> Value: dict {date, items: [...], saved_at}
    menu_history: dict = {}     
    
    # List of orders: list [dict]
    orders: list = []
    
    # Key: phone (str) -> Value: dict {otp, name, expires}
    otp_store: dict = {}        
    
    # Set of currently active session/auth tokens
    active_tokens: set = set()

# Instantiate the singleton mock database object
db = DB()


# ── Seed Data Seeder ──────────────────────────────────────────────────────────

def seed_db():
    """
    Populates the database with initial seed data on startup.
    This creates default Admin and User credentials, along with standard menu items.
    """
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"])

    # Seed Admin User (role: admin)
    # Default phone: 9800000000 | Default password: admin123
    db.users["9800000000"] = {
        "id": str(uuid.uuid4()),
        "name": "Admin",
        "phone": "9800000000",
        "password_hash": pwd.hash("admin123"),
        "coins": 0.0,
        "role": "admin",
    }

    # Seed Regular Student User (role: user)
    # Default phone: 9811111111 | Default password: user123
    # Starts with a pre-loaded balance of 250 NPR digital coins.
    db.users["9811111111"] = {
        "id": str(uuid.uuid4()),
        "name": "Ravi Thapa",
        "phone": "9811111111",
        "password_hash": pwd.hash("user123"),
        "coins": 250.0,
        "role": "user",
    }

    # Seed initial menu offerings
    items = [
        ("Masala Tea",        "Spiced milk tea",              25,  "Beverages"),
        ("Black Coffee",      "Strong filter coffee",         40,  "Beverages"),
        ("Cold Coffee",       "Chilled blended coffee",       80,  "Beverages"),
        ("Momo (Veg)",        "8 pcs steamed veg dumplings",  120, "Snacks"),
        ("Momo (Chicken)",    "8 pcs chicken dumplings",      150, "Snacks"),
        ("Veg Sandwich",      "Grilled veg sandwich",         90,  "Snacks"),
        ("Egg Sandwich",      "Egg & cheese sandwich",        110, "Snacks"),
        ("Dal Bhat",          "Rice, lentil soup & veggies",  180, "Meals"),
        ("Fried Rice",        "Veg fried rice",               160, "Meals"),
        ("Noodles",           "Spicy stir-fried noodles",     140, "Meals"),
        ("Chocolate Cake",    "Single slice",                 120, "Desserts"),
        ("Fruit Yogurt",      "Mixed fruit with yogurt",       80, "Desserts"),
    ]
    for name, desc, price, cat in items:
        iid = str(uuid.uuid4())
        db.menu_items[iid] = {
            "id": iid, "name": name, "description": desc,
            "price": float(price), "category": cat, "available": True,
        }

    # Generate the initial historical menu snapshot for today
    save_menu_snapshot()


def save_menu_snapshot():
    """
    Saves a snapshot of the current menu state into the menu history log.
    This runs daily and whenever the menu structure is modified.
    """
    today = date.today().isoformat()
    db.menu_history[today] = {
        "date": today,
        "items": list(db.menu_items.values()),
        "saved_at": datetime.now().isoformat(),
    }


def cleanup_old_snapshots():
    """
    Deletes menu history snapshots older than 7 days to preserve memory footprint.
    Triggered daily by the background scheduler.
    """
    from datetime import timedelta
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    to_delete = [d for d in db.menu_history if d < cutoff]
    for d in to_delete:
        del db.menu_history[d]
