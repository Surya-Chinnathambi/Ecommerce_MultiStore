"""
Order API Tests
"""
import pytest
import uuid
from fastapi import status
from datetime import datetime


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_order(db_session, store_id, user_id=None, order_num=None):
    """Utility: insert a minimal Order row directly into the test DB."""
    from app.models.models import Order, OrderStatus, PaymentStatus

    order = Order(
        id=uuid.uuid4(),
        store_id=store_id,
        order_number=order_num or f"ORD-{uuid.uuid4().hex[:8].upper()}",
        customer_name="Test Customer",
        customer_phone="9999999999",
        customer_email="customer@test.com",
        delivery_address="123 Test Lane",
        delivery_city="Testville",
        subtotal=250.0,
        total_amount=275.0,
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.COD,
        user_id=user_id,
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


# ── Storefront customer order placement ──────────────────────────────────────

class TestOrderPlacement:
    """Tests for the customer-facing checkout flow."""

    def test_place_order_unauthenticated(self, client, test_store, db_session):
        """Guest checkout — no auth token required."""
        from app.models.models import Product

        product = Product(
            id=uuid.uuid4(),
            store_id=test_store.id,
            external_id="CHECKOUT-001",
            name="Checkout Product",
            slug="checkout-product",
            mrp=199.99,
            selling_price=149.99,
            quantity=50,
            is_active=True,
            is_in_stock=True,
        )
        db_session.add(product)
        db_session.commit()

        response = client.post(
            "/api/v1/storefront/orders",
            json={
                "customer_name": "Guest Buyer",
                "customer_phone": "8888888888",
                "customer_email": "guest@example.com",
                "delivery_address": "456 Nowhere St",
                "delivery_city": "Testcity",
                "delivery_state": "TS",
                "delivery_pincode": "123456",
                "payment_method": "COD",
                "items": [
                    {"product_id": str(product.id), "quantity": 2}
                ],
            },
            headers={"X-Store-ID": str(test_store.id)},
        )
        # 201 Created or 200 OK depending on implementation
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
        data = response.json()
        assert data["success"] is True
        assert "order_number" in data["data"]

    def test_place_order_out_of_stock(self, client, test_store, db_session):
        """Order placement should fail when product is out of stock."""
        from app.models.models import Product

        product = Product(
            id=uuid.uuid4(),
            store_id=test_store.id,
            external_id="OOS-CHECKOUT",
            name="OOS Checkout Product",
            slug="oos-checkout-product",
            mrp=99.99,
            selling_price=79.99,
            quantity=0,
            is_active=True,
            is_in_stock=False,
        )
        db_session.add(product)
        db_session.commit()

        response = client.post(
            "/api/v1/storefront/orders",
            json={
                "customer_name": "Eager Buyer",
                "customer_phone": "7777777777",
                "delivery_address": "789 Nowhere Ave",
                "delivery_city": "Testcity",
                "delivery_state": "TS",
                "delivery_pincode": "654321",
                "payment_method": "COD",
                "items": [
                    {"product_id": str(product.id), "quantity": 1}
                ],
            },
            headers={"X-Store-ID": str(test_store.id)},
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# ── Admin order management ────────────────────────────────────────────────────

class TestAdminOrderManagement:
    """Tests for the admin order dashboard endpoints."""

    def test_list_orders_requires_auth(self, client, test_store):
        """Unauthenticated requests to admin orders should be rejected."""
        response = client.get(
            f"/api/v1/orders/admin?store_id={test_store.id}",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_can_list_store_orders(self, client, admin_headers, db_session, test_store):
        """Admin sees only their own store's orders."""
        _make_order(db_session, test_store.id)
        _make_order(db_session, test_store.id)

        response = client.get(
            f"/api/v1/orders/admin?store_id={test_store.id}",
            headers=admin_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["meta"]["total"] >= 2

    def test_admin_orders_pagination(self, client, admin_headers, db_session, test_store):
        """Pagination works correctly for admin order list."""
        for i in range(5):
            _make_order(db_session, test_store.id, order_num=f"PAG-{i:04d}")

        response = client.get(
            f"/api/v1/orders/admin?store_id={test_store.id}&page=1&per_page=3",
            headers=admin_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) <= 3

    def test_admin_orders_filter_by_status(self, client, admin_headers, db_session, test_store):
        """Status filter returns only matching orders."""
        from app.models.models import Order, OrderStatus, PaymentStatus

        confirmed_order = Order(
            id=uuid.uuid4(),
            store_id=test_store.id,
            order_number=f"CONF-{uuid.uuid4().hex[:6].upper()}",
            customer_name="Status Tester",
            customer_phone="6666666666",
            delivery_address="1 Status Lane",
            subtotal=100.0,
            total_amount=100.0,
            order_status=OrderStatus.CONFIRMED,
            payment_status=PaymentStatus.COD,
        )
        db_session.add(confirmed_order)
        db_session.commit()

        response = client.get(
            f"/api/v1/orders/admin?store_id={test_store.id}&status_filter=confirmed",
            headers=admin_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for order in data["data"]:
            assert order["order_status"] == "confirmed"

    def test_admin_orders_search(self, client, admin_headers, db_session, test_store):
        """Search finds orders by order number."""
        order = _make_order(db_session, test_store.id, order_num="FIND-UNIQUE-999")

        response = client.get(
            f"/api/v1/orders/admin?store_id={test_store.id}&search=FIND-UNIQUE-999",
            headers=admin_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(o["order_number"] == "FIND-UNIQUE-999" for o in data["data"])

    def test_non_admin_cannot_access_admin_orders(self, client, auth_headers, test_store):
        """Regular customer should be forbidden from admin endpoint."""
        response = client.get(
            f"/api/v1/orders/admin?store_id={test_store.id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ── Customer order history ────────────────────────────────────────────────────

class TestCustomerOrderHistory:
    """Tests for the customer 'My Orders' endpoint."""

    def test_customer_sees_own_orders(self, client, auth_headers, db_session, test_store, test_user):
        """Authenticated customer retrieves their own order history."""
        _make_order(db_session, test_store.id, user_id=test_user.id)

        response = client.get(
            "/api/v1/orders/customer",
            headers={**auth_headers, "X-Store-ID": str(test_store.id)},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["meta"]["total"] >= 1

    def test_my_orders_requires_auth(self, client, test_store):
        """Unauthenticated requests to customer orders should be rejected."""
        response = client.get(
            "/api/v1/orders/customer",
            headers={"X-Store-ID": str(test_store.id)},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
