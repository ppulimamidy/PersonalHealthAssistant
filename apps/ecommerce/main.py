"""
Ecommerce Service Main Application

FastAPI application for the ecommerce microservice providing health product
marketplace functionality including product listings, orders, and cart management.
"""

import os
import sys
import logging
import uuid as _uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

# Add parent directories to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from common.config.settings import get_settings
from common.middleware.auth import auth_middleware
from common.middleware.error_handling import setup_error_handlers
from common.middleware.prometheus_metrics import setup_prometheus_metrics
from common.utils.logging import setup_logging
from common.database.connection import get_async_db

from apps.ecommerce.models import (
    Product as ProductModel,
    Order as OrderModel,
    CartItem as CartItemModel,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ============================================================
# Pydantic Models
# ============================================================


class ProductCategory(BaseModel):
    id: str
    name: str
    description: str


class ProductSchema(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    currency: str = "USD"
    in_stock: bool = True
    image_url: Optional[str] = None
    stock_quantity: int = 0


class CreateProductRequest(BaseModel):
    name: str
    description: str = ""
    category: str
    price: float
    currency: str = "USD"
    image_url: Optional[str] = None
    in_stock: bool = True
    stock_quantity: int = 0


class ProductListResponse(BaseModel):
    products: List[ProductSchema]
    total: int
    message: str


class OrderItemSchema(BaseModel):
    product_id: str
    quantity: int = 1


class CreateOrderRequest(BaseModel):
    items: List[OrderItemSchema]
    shipping_address: Optional[Dict[str, Any]] = None


class OrderSchema(BaseModel):
    id: str
    user_id: str
    items: List[Dict[str, Any]]
    total: float
    status: str
    created_at: str


class CartItemSchema(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    price: float


class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = 1


class CartSchema(BaseModel):
    items: List[CartItemSchema]
    total: float


# ============================================================
# Helper: default user id (in production, extract from auth token)
# ============================================================
DEFAULT_USER_ID = _uuid.UUID("00000000-0000-0000-0000-000000000001")


# ============================================================
# Router
# ============================================================

ecommerce_router = APIRouter()


@ecommerce_router.get("/products", response_model=ProductListResponse)
async def list_products(db: AsyncSession = Depends(get_async_db)):
    """List health products from the database."""
    result = await db.execute(
        select(ProductModel).order_by(ProductModel.created_at.desc())
    )
    rows = result.scalars().all()
    products = [
        ProductSchema(
            id=str(p.id),
            name=p.name,
            description=p.description or "",
            category=p.category,
            price=p.price,
            currency=p.currency or "USD",
            in_stock=p.in_stock if p.in_stock is not None else True,
            image_url=p.image_url,
            stock_quantity=p.stock_quantity or 0,
        )
        for p in rows
    ]
    return ProductListResponse(
        products=products,
        total=len(products),
        message="Products retrieved successfully",
    )


@ecommerce_router.post(
    "/products", response_model=ProductSchema, status_code=status.HTTP_201_CREATED
)
async def create_product(
    request: CreateProductRequest, db: AsyncSession = Depends(get_async_db)
):
    """Create a new product."""
    product = ProductModel(
        name=request.name,
        description=request.description,
        category=request.category,
        price=request.price,
        currency=request.currency,
        image_url=request.image_url,
        in_stock=request.in_stock,
        stock_quantity=request.stock_quantity,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return ProductSchema(
        id=str(product.id),
        name=product.name,
        description=product.description or "",
        category=product.category,
        price=product.price,
        currency=product.currency or "USD",
        in_stock=product.in_stock if product.in_stock is not None else True,
        image_url=product.image_url,
        stock_quantity=product.stock_quantity or 0,
    )


@ecommerce_router.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(product_id: str, db: AsyncSession = Depends(get_async_db)):
    """Get product details from the database."""
    try:
        pid = _uuid.UUID(product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID"
        )

    result = await db.execute(select(ProductModel).where(ProductModel.id == pid))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    return ProductSchema(
        id=str(product.id),
        name=product.name,
        description=product.description or "",
        category=product.category,
        price=product.price,
        currency=product.currency or "USD",
        in_stock=product.in_stock if product.in_stock is not None else True,
        image_url=product.image_url,
        stock_quantity=product.stock_quantity or 0,
    )


@ecommerce_router.post(
    "/orders", response_model=OrderSchema, status_code=status.HTTP_201_CREATED
)
async def create_order(
    order_request: CreateOrderRequest, db: AsyncSession = Depends(get_async_db)
):
    """Create a new order backed by the database."""
    # Calculate total from product prices
    total = 0.0
    items_data = []
    for item in order_request.items:
        try:
            pid = _uuid.UUID(item.product_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid product ID: {item.product_id}",
            )

        result = await db.execute(select(ProductModel).where(ProductModel.id == pid))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found",
            )
        total += product.price * item.quantity
        items_data.append(
            {
                "product_id": str(product.id),
                "quantity": item.quantity,
                "price": product.price,
            }
        )

    order = OrderModel(
        user_id=DEFAULT_USER_ID,
        status="pending",
        total_amount=total,
        items=items_data,
        shipping_address=order_request.shipping_address,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)

    return OrderSchema(
        id=str(order.id),
        user_id=str(order.user_id),
        items=order.items,
        total=order.total_amount,
        status=order.status,
        created_at=order.created_at.isoformat()
        if order.created_at
        else datetime.utcnow().isoformat(),
    )


@ecommerce_router.get("/orders", response_model=List[OrderSchema])
async def list_orders(db: AsyncSession = Depends(get_async_db)):
    """List user orders from the database."""
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.user_id == DEFAULT_USER_ID)
        .order_by(OrderModel.created_at.desc())
    )
    rows = result.scalars().all()
    return [
        OrderSchema(
            id=str(o.id),
            user_id=str(o.user_id),
            items=o.items or [],
            total=o.total_amount,
            status=o.status,
            created_at=o.created_at.isoformat()
            if o.created_at
            else datetime.utcnow().isoformat(),
        )
        for o in rows
    ]


@ecommerce_router.get("/orders/{order_id}", response_model=OrderSchema)
async def get_order(order_id: str, db: AsyncSession = Depends(get_async_db)):
    """Get order details from the database."""
    try:
        oid = _uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID"
        )

    result = await db.execute(select(OrderModel).where(OrderModel.id == oid))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    return OrderSchema(
        id=str(order.id),
        user_id=str(order.user_id),
        items=order.items or [],
        total=order.total_amount,
        status=order.status,
        created_at=order.created_at.isoformat()
        if order.created_at
        else datetime.utcnow().isoformat(),
    )


@ecommerce_router.get("/categories", response_model=List[ProductCategory])
async def list_categories():
    """List product categories (static reference data)."""
    return [
        ProductCategory(
            id="cat-001",
            name="Supplements",
            description="Health supplements and vitamins",
        ),
        ProductCategory(
            id="cat-002", name="Devices", description="Health monitoring devices"
        ),
        ProductCategory(
            id="cat-003",
            name="Personal Care",
            description="Personal health care products",
        ),
    ]


@ecommerce_router.post(
    "/cart/items", response_model=CartSchema, status_code=status.HTTP_201_CREATED
)
async def add_to_cart(
    request: AddToCartRequest, db: AsyncSession = Depends(get_async_db)
):
    """Add item to cart, persisted in the database."""
    try:
        pid = _uuid.UUID(request.product_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID"
        )

    # Verify product exists
    prod_result = await db.execute(select(ProductModel).where(ProductModel.id == pid))
    product = prod_result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Check if item already in cart – if so, update quantity
    existing_result = await db.execute(
        select(CartItemModel).where(
            CartItemModel.user_id == DEFAULT_USER_ID, CartItemModel.product_id == pid
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        existing.quantity += request.quantity
        await db.flush()
    else:
        cart_item = CartItemModel(
            user_id=DEFAULT_USER_ID,
            product_id=pid,
            quantity=request.quantity,
        )
        db.add(cart_item)
        await db.flush()

    # Return full cart
    return await _build_cart(db)


@ecommerce_router.get("/cart", response_model=CartSchema)
async def get_cart(db: AsyncSession = Depends(get_async_db)):
    """Get user cart from the database."""
    return await _build_cart(db)


@ecommerce_router.delete("/cart/items/{item_id}")
async def remove_from_cart(item_id: str, db: AsyncSession = Depends(get_async_db)):
    """Remove item from cart in the database."""
    try:
        iid = _uuid.UUID(item_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item ID"
        )

    result = await db.execute(
        select(CartItemModel).where(
            CartItemModel.id == iid, CartItemModel.user_id == DEFAULT_USER_ID
        )
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found"
        )

    await db.delete(cart_item)
    await db.flush()
    return {"message": f"Item {item_id} removed from cart", "status": "success"}


async def _build_cart(db: AsyncSession) -> CartSchema:
    """Helper to build the full cart response for the current user."""
    result = await db.execute(
        select(CartItemModel).where(CartItemModel.user_id == DEFAULT_USER_ID)
    )
    rows = result.scalars().all()

    items: List[CartItemSchema] = []
    total = 0.0
    for ci in rows:
        prod_result = await db.execute(
            select(ProductModel).where(ProductModel.id == ci.product_id)
        )
        product = prod_result.scalar_one_or_none()
        price = product.price if product else 0.0
        name = product.name if product else "Unknown Product"
        items.append(
            CartItemSchema(
                id=str(ci.id),
                product_id=str(ci.product_id),
                product_name=name,
                quantity=ci.quantity,
                price=price,
            )
        )
        total += price * ci.quantity

    return CartSchema(items=items, total=total)


# ============================================================
# Application Setup
# ============================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Ecommerce Service...")
    logger.info("Ecommerce Service started successfully")
    yield
    logger.info("Shutting down Ecommerce Service...")


# Create FastAPI application
app = FastAPI(
    title="Ecommerce Service",
    description="Health product marketplace service for the Personal Health Assistant",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# Setup Prometheus metrics
setup_prometheus_metrics(app, service_name="ecommerce-service")

# Configure OpenTelemetry tracing
try:
    from common.utils.opentelemetry_config import configure_opentelemetry

    configure_opentelemetry(app, "ecommerce-service")
except ImportError:
    pass

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add auth middleware
app.middleware("http")(auth_middleware)

# Add error handling
setup_error_handlers(app)

# Include router
app.include_router(ecommerce_router, prefix="/api/v1/ecommerce", tags=["ecommerce"])


@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with service information."""
    return {
        "message": "Personal Health Assistant - Ecommerce Service",
        "version": "1.0.0",
        "docs": "/docs" if ENVIRONMENT == "development" else None,
        "health": "/health",
        "ready": "/ready",
    }


@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "service": "ecommerce",
        "status": "healthy",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
    }


@app.get("/ready", tags=["health"])
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint for Kubernetes."""
    return {
        "service": "ecommerce",
        "status": "ready",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    uvicorn.run(
        "apps.ecommerce.main:app",
        host="0.0.0.0",
        port=8013,
        reload=ENVIRONMENT == "development",
        log_level=LOG_LEVEL.lower(),
    )
