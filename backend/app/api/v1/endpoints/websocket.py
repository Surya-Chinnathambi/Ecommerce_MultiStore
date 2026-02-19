"""
WebSocket API Endpoints
Real-time notifications and updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.security import decode_token
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/store/{store_id}")
async def store_websocket(
    websocket: WebSocket,
    store_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for store admins
    Receives: New orders, order updates, inventory alerts
    
    Connect with: ws://localhost:8000/api/v1/ws/store/{store_id}?token=xxx
    """
    # Verify token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if role not in ["admin", "super_admin"]:
            await websocket.close(code=4003, reason="Unauthorized")
            return
    except Exception as e:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Connect
    connected = await ws_manager.connect(websocket, "store", store_id)
    if not connected:
        return
    
    # Send any queued offline messages
    offline_messages = await ws_manager.get_offline_messages("store", store_id)
    for msg in offline_messages:
        await websocket.send_json(msg)
    
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "subscribe":
                # Handle subscription to specific events
                logger.info(f"Store {store_id} subscribed to: {data.get('events', [])}")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "store", store_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket, "store", store_id)


@router.websocket("/ws/user/{user_id}")
async def user_websocket(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for customer notifications
    Receives: Order updates, promotions, personal notifications
    
    Connect with: ws://localhost:8000/api/v1/ws/user/{user_id}?token=xxx
    """
    # Verify token and check user ownership
    try:
        payload = decode_token(token)
        token_user_id = payload.get("sub")
        
        if token_user_id != user_id:
            await websocket.close(code=4003, reason="Unauthorized")
            return
    except Exception as e:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    connected = await ws_manager.connect(websocket, "user", user_id)
    if not connected:
        return
    
    # Send offline messages
    offline_messages = await ws_manager.get_offline_messages("user", user_id)
    for msg in offline_messages:
        await websocket.send_json(msg)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.get("type") == "mark_read":
                # Handle marking notifications as read
                notification_id = data.get("notification_id")
                logger.info(f"User {user_id} marked notification {notification_id} as read")
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "user", user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket, "user", user_id)


@router.websocket("/ws/inventory/{store_id}")
async def inventory_websocket(
    websocket: WebSocket,
    store_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint for inventory alerts
    Receives: Low stock alerts, out of stock alerts, sync updates
    
    Connect with: ws://localhost:8000/api/v1/ws/inventory/{store_id}?token=xxx
    """
    # Verify admin token
    try:
        payload = decode_token(token)
        role = payload.get("role")
        
        if role not in ["admin", "super_admin"]:
            await websocket.close(code=4003, reason="Unauthorized")
            return
    except Exception as e:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    connected = await ws_manager.connect(websocket, "inventory", store_id)
    if not connected:
        return
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "inventory", store_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket, "inventory", store_id)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection statistics"""
    return {
        "total_connections": ws_manager.get_connection_count(),
        "by_channel": {
            "store": ws_manager.get_connection_count("store"),
            "user": ws_manager.get_connection_count("user"),
            "inventory": ws_manager.get_connection_count("inventory"),
            "admin": ws_manager.get_connection_count("admin"),
        }
    }
