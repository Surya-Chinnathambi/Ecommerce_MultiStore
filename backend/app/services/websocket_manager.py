"""
WebSocket Manager for Real-Time Notifications
Handles live updates for orders, inventory, and notifications
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional
import json
import logging
import asyncio
from datetime import datetime
from uuid import UUID

from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    Supports multiple channels: orders, inventory, notifications
    """
    
    def __init__(self):
        # Store connections by channel and identifier
        # Structure: {channel: {identifier: [websocket, ...]}}
        self.connections: Dict[str, Dict[str, List[WebSocket]]] = {
            "admin": {},      # Admin dashboard updates
            "store": {},      # Store-specific updates
            "user": {},       # User-specific notifications
            "inventory": {},  # Inventory alerts
            "orders": {},     # Order status updates
        }
        self._lock = asyncio.Lock()
    
    async def connect(
        self, 
        websocket: WebSocket, 
        channel: str, 
        identifier: str
    ) -> bool:
        """
        Accept new WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            channel: Channel type (admin, store, user, etc.)
            identifier: Store ID, User ID, etc.
        
        Returns:
            True if connection successful
        """
        try:
            await websocket.accept()
            
            async with self._lock:
                if channel not in self.connections:
                    self.connections[channel] = {}
                
                if identifier not in self.connections[channel]:
                    self.connections[channel][identifier] = []
                
                self.connections[channel][identifier].append(websocket)
            
            logger.info(f"WebSocket connected: channel={channel}, id={identifier}")
            
            # Send connection confirmation
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False
    
    async def disconnect(
        self, 
        websocket: WebSocket, 
        channel: str, 
        identifier: str
    ):
        """Remove WebSocket connection"""
        async with self._lock:
            if (channel in self.connections and 
                identifier in self.connections[channel]):
                try:
                    self.connections[channel][identifier].remove(websocket)
                    if not self.connections[channel][identifier]:
                        del self.connections[channel][identifier]
                except ValueError:
                    pass
        
        logger.info(f"WebSocket disconnected: channel={channel}, id={identifier}")
    
    async def broadcast_to_channel(
        self, 
        channel: str, 
        message: dict
    ):
        """Broadcast message to all connections in a channel"""
        if channel not in self.connections:
            return
        
        message["timestamp"] = datetime.utcnow().isoformat()
        dead_connections = []
        
        for identifier, websockets in self.connections[channel].items():
            for ws in websockets:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    dead_connections.append((channel, identifier, ws))
        
        # Clean up dead connections
        for channel, identifier, ws in dead_connections:
            await self.disconnect(ws, channel, identifier)
    
    async def send_to_identifier(
        self, 
        channel: str, 
        identifier: str, 
        message: dict
    ):
        """Send message to specific identifier in channel"""
        if (channel not in self.connections or 
            identifier not in self.connections[channel]):
            # Store message in Redis for later delivery
            await self._queue_offline_message(channel, identifier, message)
            return
        
        message["timestamp"] = datetime.utcnow().isoformat()
        dead_connections = []
        
        for ws in self.connections[channel][identifier]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {identifier}: {e}")
                dead_connections.append(ws)
        
        for ws in dead_connections:
            await self.disconnect(ws, channel, identifier)
    
    async def _queue_offline_message(
        self, 
        channel: str, 
        identifier: str, 
        message: dict
    ):
        """Queue message for offline delivery via Redis"""
        key = f"ws:offline:{channel}:{identifier}"
        message["queued_at"] = datetime.utcnow().isoformat()
        await redis_client.set_json(key, message, ttl=86400)  # 24 hours
    
    async def get_offline_messages(
        self, 
        channel: str, 
        identifier: str
    ) -> List[dict]:
        """Retrieve queued offline messages"""
        key = f"ws:offline:{channel}:{identifier}"
        message = await redis_client.get_json(key)
        if message:
            await redis_client.delete(key)
            return [message]
        return []
    
    def get_connection_count(self, channel: Optional[str] = None) -> int:
        """Get total connection count"""
        if channel:
            return sum(
                len(ws_list) 
                for ws_list in self.connections.get(channel, {}).values()
            )
        return sum(
            len(ws_list)
            for ch in self.connections.values()
            for ws_list in ch.values()
        )


# Global connection manager instance
ws_manager = ConnectionManager()


# =============================================================================
# Event Publishers - Use these to send real-time updates
# =============================================================================

async def notify_order_update(
    store_id: str,
    order_id: str,
    order_number: str,
    status: str,
    customer_name: str
):
    """Notify admins about order status change"""
    await ws_manager.send_to_identifier("store", store_id, {
        "type": "order_update",
        "data": {
            "order_id": order_id,
            "order_number": order_number,
            "status": status,
            "customer_name": customer_name,
        }
    })


async def notify_new_order(
    store_id: str,
    order_id: str,
    order_number: str,
    total_amount: float,
    customer_name: str
):
    """Notify admins about new order"""
    await ws_manager.send_to_identifier("store", store_id, {
        "type": "new_order",
        "data": {
            "order_id": order_id,
            "order_number": order_number,
            "total_amount": total_amount,
            "customer_name": customer_name,
        }
    })


async def notify_inventory_alert(
    store_id: str,
    product_id: str,
    product_name: str,
    current_quantity: int,
    alert_type: str  # 'low_stock', 'out_of_stock'
):
    """Notify admins about inventory alerts"""
    await ws_manager.send_to_identifier("inventory", store_id, {
        "type": "inventory_alert",
        "data": {
            "product_id": product_id,
            "product_name": product_name,
            "current_quantity": current_quantity,
            "alert_type": alert_type,
        }
    })


async def notify_user(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: Optional[dict] = None
):
    """Send notification to specific user"""
    await ws_manager.send_to_identifier("user", user_id, {
        "type": notification_type,
        "title": title,
        "message": message,
        "data": data or {}
    })


async def broadcast_store_update(
    store_id: str,
    update_type: str,
    data: dict
):
    """Broadcast update to all store admins"""
    await ws_manager.send_to_identifier("admin", store_id, {
        "type": update_type,
        "data": data
    })
