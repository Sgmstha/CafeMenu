"""
Campus Café - Menu Management Router
-------------------------------------
This router defines API endpoints for managing the café menu, including
creating, updating, toggling availability, and deleting menu items.
It also includes endpoints to retrieve historical menu snapshots.

Note: Write operations are restricted to admin users via FastAPI dependencies.

TODO:
    1. Add support for uploading item images using Multipart/Form files.
    2. Add sorting/ordering index weight to menu items so admins can control display order.
    3. Implement pagination or full-text search capability.
"""

from fastapi import APIRouter, Depends, HTTPException
import uuid
from datetime import date

# Import schema templates and database snapshots helper
from models.database import db, MenuItemCreate, BulkMenuDelete, save_menu_snapshot
from models.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/menu", tags=["menu"])


@router.get("")
def get_menu():
    """
    Returns the current active café menu items and unique categories list.
    Accessible to everyone (no authentication required).
    """
    items = list(db.menu_items.values())
    categories = sorted(set(i["category"] for i in items))
    return {"items": items, "categories": categories}


@router.post("")
def add_item(item: MenuItemCreate, admin=Depends(require_admin)):
    """
    Creates a new menu item.
    Saves a menu historical snapshot on creation.
    Requires administrator authorization.
    """
    iid = str(uuid.uuid4())
    db.menu_items[iid] = {
        "id": iid,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category,
        "available": True,  # Defaults to active / in stock
    }
    save_menu_snapshot()
    return {"message": "Item added successfully", "id": iid}


@router.put("/{item_id}")
def update_item(item_id: str, item: MenuItemCreate, admin=Depends(require_admin)):
    """
    Updates details of an existing menu item.
    Saves a menu historical snapshot on update.
    Requires administrator authorization.
    """
    if item_id not in db.menu_items:
        raise HTTPException(404, "Menu item not found")
        
    db.menu_items[item_id].update({
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category,
    })
    save_menu_snapshot()
    return {"message": "Item updated successfully"}


@router.patch("/{item_id}/toggle")
def toggle_availability(item_id: str, admin=Depends(require_admin)):
    """
    Toggles the in-stock / out-of-stock availability state of a menu item.
    Requires administrator authorization.
    """
    if item_id not in db.menu_items:
        raise HTTPException(404, "Menu item not found")
        
    db.menu_items[item_id]["available"] = not db.menu_items[item_id]["available"]
    return {"available": db.menu_items[item_id]["available"]}


@router.delete("/{item_id}")
def delete_item(item_id: str, admin=Depends(require_admin)):
    """
    Deletes a menu item from the list.
    Saves a menu historical snapshot on deletion.
    Requires administrator authorization.
    """
    if item_id not in db.menu_items:
        raise HTTPException(404, "Menu item not found")
        
    del db.menu_items[item_id]
    save_menu_snapshot()
    return {"message": "Item deleted successfully"}


@router.delete("")
def clear_menu(admin=Depends(require_admin)):
    """
    Archives the current menu state and clears all active menu items.
    Requires administrator authorization.
    """
    save_menu_snapshot()
    db.menu_items.clear()
    return {"message": "Menu cleared successfully"}


@router.post("/remove")
def remove_menu_items(payload: BulkMenuDelete, admin=Depends(require_admin)):
    """
    Removes a selected list of menu items from today’s menu while saving the
    current menu snapshot in menu history.
    Requires administrator authorization.
    """
    if not payload.ids:
        raise HTTPException(400, "At least one item id must be provided")

    save_menu_snapshot()
    removed_count = 0
    for item_id in payload.ids:
        if item_id in db.menu_items:
            del db.menu_items[item_id]
            removed_count += 1

    return {"message": f"Removed {removed_count} selected menu item(s)"}


@router.get("/history")
def get_history(admin=Depends(require_admin)):
    """
    Retrieves the list of dates for which a menu snapshot has been saved.
    Requires administrator authorization.
    """
    return {"history": list(db.menu_history.keys())}


@router.get("/history/{date_str}")
def get_history_date(date_str: str, admin=Depends(require_admin)):
    """
    Retrieves the menu snapshot for a specific date string (format YYYY-MM-DD).
    Requires administrator authorization.
    """
    snap = db.menu_history.get(date_str)
    if not snap:
        raise HTTPException(404, "No menu history snapshot found for this date")
    return snap
