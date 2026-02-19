"""
Returns & Refunds API
Customer initiates, admin processes, refund is issued.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import random, string
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.auth_models import User, UserRole
from app.models.models import Order, OrderItem, OrderStatus
from app.models.marketplace_models import (
    ReturnRequest, ReturnItem, ReturnStatus, ReturnReason
)
from app.schemas.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _gen_return_number() -> str:
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"RET-{suffix}"


def _is_returnable(order: Order) -> bool:
    """Order must be delivered and within return window."""
    if order.order_status != OrderStatus.DELIVERED:
        return False
    if not order.delivered_at:
        return False
    delta = (datetime.utcnow() - order.delivered_at).days
    return delta <= 7   # 7-day return window


def _serialize_return(r: ReturnRequest) -> dict:
    return {
        "id": str(r.id),
        "return_number": r.return_number,
        "order_id": str(r.order_id),
        "reason": r.reason.value if hasattr(r.reason, "value") else r.reason,
        "description": r.description,
        "images": r.images or [],
        "status": r.status.value if hasattr(r.status, "value") else r.status,
        "admin_notes": r.admin_notes,
        "rejection_reason": r.rejection_reason,
        "tracking_id": r.tracking_id,
        "refund_amount": r.refund_amount,
        "refund_method": r.refund_method,
        "refunded_at": r.refunded_at.isoformat() if r.refunded_at else None,
        "requested_at": r.requested_at.isoformat(),
        "items": [
            {
                "id": str(i.id),
                "order_item_id": str(i.order_item_id),
                "product_name": i.product_name,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "refund_amount": i.refund_amount,
            }
            for i in (r.items or [])
        ],
    }


# ─── customer routes ─────────────────────────────────────────────────────────

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED,
             summary="Initiate a return request")
async def create_return(
    request: Request,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Payload example:
    {
      "order_id": "uuid",
      "reason": "defective",
      "description": "Screen cracked on arrival",
      "images": ["https://..."],
      "items": [
          {"order_item_id": "uuid", "quantity": 1}
      ]
    }
    """
    store_id = request.state.store_id

    order_id = payload.get("order_id")
    if not order_id:
        raise HTTPException(status_code=422, detail="order_id is required")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.store_id == store_id,
        Order.user_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not _is_returnable(order):
        raise HTTPException(
            status_code=400,
            detail="This order is not eligible for a return. "
                   "Only delivered orders within 7 days are eligible."
        )

    # Prevent duplicate active return
    active = db.query(ReturnRequest).filter(
        ReturnRequest.order_id == order_id,
        ReturnRequest.status.notin_([ReturnStatus.REJECTED, ReturnStatus.CLOSED]),
    ).first()
    if active:
        raise HTTPException(status_code=400,
                            detail=f"A return request (#{active.return_number}) already exists for this order.")

    reason_str = payload.get("reason", "other")
    try:
        reason = ReturnReason(reason_str)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid reason '{reason_str}'")

    return_req = ReturnRequest(
        order_id=order_id,
        store_id=store_id,
        user_id=current_user.id,
        return_number=_gen_return_number(),
        reason=reason,
        description=payload.get("description"),
        images=payload.get("images", []),
        status=ReturnStatus.REQUESTED,
    )
    db.add(return_req)
    db.flush()   # get return_req.id

    # Add items
    item_entries = payload.get("items", [])
    if not item_entries:
        # Default: return all items
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        item_entries = [{"order_item_id": str(oi.id), "quantity": oi.quantity}
                        for oi in order_items]

    for entry in item_entries:
        oi = db.query(OrderItem).filter(
            OrderItem.id == entry["order_item_id"],
            OrderItem.order_id == order_id,
        ).first()
        if not oi:
            raise HTTPException(status_code=404,
                                detail=f"Order item {entry['order_item_id']} not found")

        qty = min(int(entry.get("quantity", oi.quantity)), oi.quantity)
        ri = ReturnItem(
            return_request_id=return_req.id,
            order_item_id=oi.id,
            product_name=oi.product_name,
            quantity=qty,
            unit_price=oi.unit_price,
            refund_amount=round(oi.unit_price * qty, 2),
        )
        db.add(ri)

    db.commit()
    db.refresh(return_req)

    # Reload with items
    return_req = (db.query(ReturnRequest)
                  .options(joinedload(ReturnRequest.items))
                  .filter(ReturnRequest.id == return_req.id).first())

    logger.info(f"Return created: {return_req.return_number} for order {order_id}")
    return APIResponse(success=True, data=_serialize_return(return_req))


@router.get("/my", response_model=APIResponse, summary="My return requests")
async def my_returns(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    store_id = request.state.store_id
    query = (
        db.query(ReturnRequest)
        .options(joinedload(ReturnRequest.items))
        .filter(
            ReturnRequest.user_id == current_user.id,
            ReturnRequest.store_id == store_id,
        )
        .order_by(ReturnRequest.requested_at.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return APIResponse(success=True, data=[_serialize_return(r) for r in items],
                       meta={"total": total, "page": page})


@router.get("/{return_id}", response_model=APIResponse, summary="Get return detail")
async def get_return(
    return_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = (db.query(ReturnRequest)
         .options(joinedload(ReturnRequest.items))
         .filter(ReturnRequest.id == return_id).first())
    if not r:
        raise HTTPException(status_code=404, detail="Return request not found")

    # Customers can only see their own; admins see all
    if current_user.role == UserRole.CUSTOMER and r.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return APIResponse(success=True, data=_serialize_return(r))


# ─── admin routes ─────────────────────────────────────────────────────────────

@router.get("/admin/list", response_model=APIResponse, summary="[Admin] All returns")
async def admin_list_returns(
    request: Request,
    status_filter: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin only")

    store_id = request.state.store_id
    query = (
        db.query(ReturnRequest)
        .options(joinedload(ReturnRequest.items))
        .filter(ReturnRequest.store_id == store_id)
    )
    if status_filter:
        query = query.filter(ReturnRequest.status == status_filter)

    total = query.count()
    items = query.order_by(ReturnRequest.requested_at.desc()) \
                 .offset((page - 1) * per_page).limit(per_page).all()

    return APIResponse(success=True, data=[_serialize_return(r) for r in items],
                       meta={"total": total, "page": page})


@router.post("/admin/{return_id}/process", response_model=APIResponse,
             summary="[Admin] Approve, reject, or mark refunded")
async def admin_process_return(
    return_id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin only")

    r = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Return not found")

    action = payload.get("action")   # approve | reject | schedule_pickup | refund

    if action == "approve":
        r.status = ReturnStatus.APPROVED
        r.admin_notes = payload.get("admin_notes")
    elif action == "reject":
        r.status = ReturnStatus.REJECTED
        r.rejection_reason = payload.get("rejection_reason", "Does not meet return criteria")
        r.resolved_at = datetime.utcnow()
    elif action == "schedule_pickup":
        r.status = ReturnStatus.APPROVED
        r.pickup_scheduled_at = payload.get("pickup_date")
        r.tracking_id = payload.get("tracking_id")
    elif action == "mark_picked_up":
        r.status = ReturnStatus.PICKED_UP
        r.pickup_completed_at = datetime.utcnow()
    elif action == "refund":
        r.status = ReturnStatus.REFUNDED
        r.refund_amount = payload.get("refund_amount", r.refund_amount)
        r.refund_method = payload.get("refund_method", "original")
        r.refund_ref = payload.get("refund_ref")
        r.refunded_at = datetime.utcnow()
        r.resolved_at = datetime.utcnow()
    else:
        raise HTTPException(status_code=422, detail=f"Unknown action '{action}'")

    r.updated_at = datetime.utcnow()
    db.commit()
    return APIResponse(success=True, data={"return_id": str(return_id),
                                           "new_status": r.status.value})
