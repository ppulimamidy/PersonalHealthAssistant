"""Unit tests for Ecommerce service models.

The ecommerce service only has ORM models, so we test with
simple Pydantic schemas that mirror the DB model structure.
"""
import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


# Pydantic schemas for testing (mirrors ORM model shapes)
class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str
    description: Optional[str] = None
    category: str
    price: float = Field(..., gt=0)
    currency: str = "USD"
    image_url: Optional[str] = None
    in_stock: bool = True
    stock_quantity: int = Field(default=0, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class OrderCreate(BaseModel):
    """Schema for creating an order."""

    user_id: str
    status: str = "pending"
    total_amount: float = Field(..., gt=0)
    items: List[Dict[str, Any]]
    shipping_address: Optional[Dict[str, Any]] = None


class CartItemCreate(BaseModel):
    """Schema for adding a cart item."""

    user_id: str
    product_id: str
    quantity: int = Field(default=1, ge=1)


class TestProductModels:
    def test_product_creation(self):
        """Test product creation with valid data."""
        product = ProductCreate(
            name="Health Monitoring Kit",
            description="Complete kit with blood pressure monitor and scale.",
            category="health_devices",
            price=149.99,
            stock_quantity=50,
            metadata={"weight_kg": 2.5, "warranty_months": 24},
        )
        assert product.name == "Health Monitoring Kit"
        assert product.price == 149.99
        assert product.in_stock is True
        assert product.currency == "USD"

    def test_product_minimal(self):
        """Test product creation with minimal fields."""
        product = ProductCreate(
            name="Simple Item",
            category="supplements",
            price=9.99,
        )
        assert product.description is None
        assert product.stock_quantity == 0

    def test_product_invalid_price(self):
        """Test product rejects zero or negative price."""
        with pytest.raises(Exception):
            ProductCreate(
                name="Bad Product",
                category="test",
                price=-10.0,
            )

    def test_product_invalid_stock(self):
        """Test product rejects negative stock quantity."""
        with pytest.raises(Exception):
            ProductCreate(
                name="Bad Stock",
                category="test",
                price=10.0,
                stock_quantity=-5,
            )


class TestOrderModels:
    def test_order_creation(self):
        """Test order creation with valid data."""
        order = OrderCreate(
            user_id=str(uuid4()),
            total_amount=299.98,
            items=[
                {"product_id": str(uuid4()), "quantity": 2, "price": 149.99},
            ],
            shipping_address={"street": "123 Health St", "city": "Wellness City"},
        )
        assert order.status == "pending"
        assert order.total_amount == 299.98
        assert len(order.items) == 1

    def test_order_invalid_amount(self):
        """Test order rejects zero or negative total."""
        with pytest.raises(Exception):
            OrderCreate(
                user_id=str(uuid4()),
                total_amount=0,
                items=[{"product_id": "abc", "quantity": 1}],
            )

    def test_order_missing_items(self):
        """Test order fails without items."""
        with pytest.raises(Exception):
            OrderCreate(
                user_id=str(uuid4()),
                total_amount=50.0,
            )


class TestCartItemModels:
    def test_cart_item_creation(self):
        """Test cart item creation."""
        item = CartItemCreate(
            user_id=str(uuid4()),
            product_id=str(uuid4()),
            quantity=3,
        )
        assert item.quantity == 3

    def test_cart_item_default_quantity(self):
        """Test cart item default quantity is 1."""
        item = CartItemCreate(
            user_id=str(uuid4()),
            product_id=str(uuid4()),
        )
        assert item.quantity == 1

    def test_cart_item_invalid_quantity(self):
        """Test cart item rejects zero quantity."""
        with pytest.raises(Exception):
            CartItemCreate(
                user_id=str(uuid4()),
                product_id=str(uuid4()),
                quantity=0,
            )
