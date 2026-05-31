"""
Campus Café - Order Processing & Wallet Router
------------------------------------------------
This router defines endpoints to place customer orders, fetch order queues,
manage order status workflows (confirmed, preparing, ready, delivered),
and handle digital wallet coin allocations for students.

Note: Sensitive operations (listing orders, loading coins, listing users) 
are protected by the require_admin dependency.

TODO:
    1. Implement a distributed lock or database transaction block when deducting 
       coins from the user wallet to prevent race conditions (double spend issues).
    2. Add standard validation to prevent negative coin loads.
    3. Integrate standard third-party payment gateways (e.g. eSewa, Khalti, or Fonepay webhooks).
    4. Implement web sockets or long polling to notify the admin panel of new orders instantly.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import uuid

# Import schemas and simulated database singleton
from models.database import db, OrderCreate
from models.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("")
def place_order(order: OrderCreate, user=Depends(get_current_user)):
    """
    Submits a new order.
    Validates items' stock availability, calculates the total price,
    checks/deducts coin balances if paying with digital coins, and saves the order record.
    """
    total = 0.0
    
    # 1. Validate that all requested items exist and are available in stock
    for oi in order.items:
        item = db.menu_items.get(oi.item_id)
        if not item:
            raise HTTPException(404, f"Menu item {oi.item_id} not found")
        if not item["available"]:
            raise HTTPException(400, f"{item['name']} is currently out of stock")
        total += oi.price * oi.quantity

    # 2. Handle digital coin payment verification and deduction
    if order.payment_method == "coin":
        phone = order.customer_phone
        u = db.users.get(phone)
        if not u:
            raise HTTPException(400, "User account not found for coin payment")
            
        # Ensure user has sufficient funds
        # TODO: Implement atomic check-and-subtract database operation here
        if u["coins"] < total:
            raise HTTPException(400, f"Insufficient coins. Balance: {u['coins']} NPR, Required: {total} NPR")
            
        db.users[phone]["coins"] -= total
        db.users[phone]["points"] = db.users[phone].get("points", 0) + int(total * 0.1)

    # 3. Save the finalized order record
    order_id = str(uuid.uuid4())[:8].upper()  # Simple human-readable short order ID
    record = {
        "id": order_id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "items": [i.dict() for i in order.items],
        "total": total,
        "payment_method": order.payment_method,
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
    }
    db.orders.append(record)
    
    return {"message": "Order placed successfully", "order_id": order_id, "total": total}


@router.get("/my")
def my_orders(user=Depends(get_current_user)):
    """
    Retrieves all orders belonging to the currently authenticated user.
    Sorted by the newest order first.
    """
    if not user:
        raise HTTPException(401, "Not authenticated")
    phone = user.get("phone")
    user_orders = [o for o in db.orders if o["customer_phone"] == phone]
    return {"orders": sorted(user_orders, key=lambda o: o["created_at"], reverse=True)}


@router.get("")
def list_orders(admin=Depends(require_admin)):
    """
    Retrieves all orders in the system, sorted by the newest order first.
    Requires administrator authorization.
    """
    return {"orders": sorted(db.orders, key=lambda o: o["created_at"], reverse=True)}


@router.patch("/{order_id}/status")
def update_status(order_id: str, status: str, admin=Depends(require_admin)):
    """
    Updates the preparation or delivery status of a specific order.
    Requires administrator authorization.
    """
    for o in db.orders:
        if o["id"] == order_id:
            o["status"] = status
            return {"message": "Order status updated successfully"}
    raise HTTPException(404, "Order not found")


# ── Coin Management (Admin Only) ──────────────────────────────────────────────

@router.post("/coins/load")
def load_coins(phone: str, amount: float, admin=Depends(require_admin)):
    """
    Loads digital wallet coins onto a user's account by phone number.
    Requires administrator authorization.
    """
    if phone not in db.users:
        raise HTTPException(404, "User account not found")
        
    # Prevent negative values
    if amount <= 0:
        raise HTTPException(400, "Load amount must be greater than zero")
        
    db.users[phone]["coins"] += amount
    return {
        "message": f"Loaded {amount} coins successfully", 
        "new_balance": db.users[phone]["coins"]
    }


@router.get("/coins/balance/{phone}")
def coin_balance(phone: str, admin=Depends(require_admin)):
    """
    Queries the digital coin balance of a user by phone number.
    Requires administrator authorization.
    """
    u = db.users.get(phone)
    if not u:
        raise HTTPException(404, "User account not found")
    return {"phone": phone, "name": u["name"], "coins": u["coins"]}


@router.get("/users")
def list_users(admin=Depends(require_admin)):
    """
    Lists all registered users in the database with their current coin balances.
    Requires administrator authorization.
    """
    return {"users": [
        {"phone": p, "name": u["name"], "role": u["role"], "coins": u["coins"]}
        for p, u in db.users.items()
    ]}
