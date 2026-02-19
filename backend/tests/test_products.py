"""
Product API Tests
"""
import pytest
from fastapi import status
import uuid


class TestProductListing:
    """Test product listing endpoints"""
    
    def test_list_products_empty(self, client, test_store):
        """Test listing products when store is empty"""
        response = client.get(
            "/api/v1/products/",
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 0
    
    def test_list_products_with_pagination(self, client, db_session, test_store):
        """Test product listing with pagination"""
        from app.models.models import Product
        
        # Create test products
        for i in range(25):
            product = Product(
                id=uuid.uuid4(),
                store_id=test_store.id,
                external_id=f"PROD-{i:04d}",
                name=f"Test Product {i}",
                slug=f"test-product-{i}",
                mrp=100.0 + i,
                selling_price=90.0 + i,
                quantity=100,
                is_active=True,
                is_in_stock=True,
            )
            db_session.add(product)
        db_session.commit()
        
        # Test first page
        response = client.get(
            "/api/v1/products/?page=1&per_page=10",
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["total"] == 25
        assert len(data["data"]["products"]) == 10
        assert data["data"]["page"] == 1
        assert data["data"]["total_pages"] == 3
    
    def test_list_products_with_search(self, client, db_session, test_store):
        """Test product search"""
        from app.models.models import Product
        
        # Create specific product
        product = Product(
            id=uuid.uuid4(),
            store_id=test_store.id,
            external_id="UNIQUE-001",
            name="Unique Searchable Product",
            slug="unique-searchable-product",
            mrp=199.99,
            selling_price=149.99,
            quantity=50,
            is_active=True,
            is_in_stock=True,
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.get(
            "/api/v1/products/?search=Unique",
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["total"] >= 1
        assert any("Unique" in p["name"] for p in data["data"]["products"])


class TestProductDetails:
    """Test single product endpoints"""
    
    def test_get_product_success(self, client, db_session, test_store):
        """Test getting single product"""
        from app.models.models import Product
        
        product = Product(
            id=uuid.uuid4(),
            store_id=test_store.id,
            external_id="SINGLE-001",
            name="Single Test Product",
            slug="single-test-product",
            mrp=299.99,
            selling_price=249.99,
            quantity=10,
            is_active=True,
            is_in_stock=True,
        )
        db_session.add(product)
        db_session.commit()
        
        response = client.get(
            f"/api/v1/products/{product.id}",
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Single Test Product"
    
    def test_get_product_not_found(self, client, test_store):
        """Test getting nonexistent product"""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/products/{fake_id}",
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProductFilters:
    """Test product filtering"""
    
    def test_filter_by_price_range(self, client, db_session, test_store):
        """Test filtering products by price range"""
        from app.models.models import Product
        
        # Create products with different prices
        for price in [50, 100, 150, 200, 250]:
            product = Product(
                id=uuid.uuid4(),
                store_id=test_store.id,
                external_id=f"PRICE-{price}",
                name=f"Product at {price}",
                slug=f"product-at-{price}",
                mrp=float(price + 50),
                selling_price=float(price),
                quantity=10,
                is_active=True,
                is_in_stock=True,
            )
            db_session.add(product)
        db_session.commit()
        
        response = client.get(
            "/api/v1/products/?min_price=100&max_price=200",
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        products = data["data"]["products"]
        for p in products:
            assert 100 <= p["selling_price"] <= 200
    
    def test_filter_in_stock_only(self, client, db_session, test_store):
        """Test filtering only in-stock products"""
        from app.models.models import Product
        
        # Out of stock product
        out_of_stock = Product(
            id=uuid.uuid4(),
            store_id=test_store.id,
            external_id="OOS-001",
            name="Out of Stock Product",
            slug="out-of-stock-product",
            mrp=99.99,
            selling_price=79.99,
            quantity=0,
            is_active=True,
            is_in_stock=False,
        )
        db_session.add(out_of_stock)
        db_session.commit()
        
        response = client.get(
            "/api/v1/products/?in_stock=true",
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for p in data["data"]["products"]:
            assert p["is_in_stock"] is True
