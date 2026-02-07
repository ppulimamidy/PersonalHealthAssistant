# E-commerce Service

Health product marketplace service for the Personal Health Assistant platform. Provides product listings, shopping cart management, order processing, and product category browsing. Currently in initial implementation with placeholder data.

## Port
- **Port**: 8013

## API Endpoints

### Infrastructure

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Service info |
| GET | `/health` | No | Health check |
| GET | `/ready` | No | Readiness probe |
| GET | `/metrics` | No | Prometheus metrics |

### Products (`/api/v1/ecommerce`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/ecommerce/products` | Yes | List health products |
| GET | `/api/v1/ecommerce/products/{product_id}` | Yes | Get product details |
| GET | `/api/v1/ecommerce/categories` | Yes | List product categories (Supplements, Devices, Personal Care) |

### Orders (`/api/v1/ecommerce`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/ecommerce/orders` | Yes | Create a new order |
| GET | `/api/v1/ecommerce/orders` | Yes | List user orders |
| GET | `/api/v1/ecommerce/orders/{order_id}` | Yes | Get order details |

### Cart (`/api/v1/ecommerce`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/ecommerce/cart` | Yes | Get user cart |
| POST | `/api/v1/ecommerce/cart/items` | Yes | Add item to cart |
| DELETE | `/api/v1/ecommerce/cart/items/{item_id}` | Yes | Remove item from cart |

## Database
- **No dedicated tables yet** — returns placeholder data. Database integration planned for future iterations.

## Dependencies
- **None** — standalone service with no external service or database dependencies at this stage.

## Configuration
Key environment variables:

| Variable | Description |
|----------|-------------|
| `ENVIRONMENT` | Environment name (`development`, `production`) |
| `CORS_ORIGINS` | Allowed CORS origins |
| `LOG_LEVEL` | Logging level (default: `INFO`) |

## Running Locally
```bash
cd apps/ecommerce
uvicorn main:app --host 0.0.0.0 --port 8013 --reload
```

## Docker
```bash
docker build -t ecommerce-service -f apps/ecommerce/Dockerfile .
docker run -p 8013:8013 ecommerce-service
```
