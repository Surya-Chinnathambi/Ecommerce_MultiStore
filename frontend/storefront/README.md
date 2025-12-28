# E-Commerce Multi-Tenant Platform - Storefront

Customer-facing React application for the multi-tenant e-commerce platform.

## Tech Stack

- **React 18.2** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **React Router v6** - Client-side routing
- **TanStack Query (React Query)** - Server state management
- **Zustand** - Client state management (cart)
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Hook Form + Zod** - Form validation
- **Lucide React** - Icons

## Features

### Customer Features
- ✅ **Product Browsing** - View all products with images, prices, stock status
- ✅ **Category Filtering** - Browse products by category
- ✅ **Product Search** - Search products by name/description
- ✅ **Product Details** - View detailed product information
- ✅ **Shopping Cart** - Add, remove, update quantities
- ✅ **Checkout** - Complete order with delivery details
- ✅ **Order Tracking** - Track order status with order number + phone
- ✅ **Responsive Design** - Mobile-first responsive UI

### Technical Features
- ✅ **Multi-Tenant Support** - Store identification via URL parameter
- ✅ **Optimistic Updates** - Instant UI feedback
- ✅ **Error Handling** - User-friendly error messages
- ✅ **Loading States** - Skeleton screens and spinners
- ✅ **Persistent Cart** - Cart saved to localStorage
- ✅ **Toast Notifications** - Success/error feedback
- ✅ **SEO Friendly** - Proper meta tags and semantic HTML

## Getting Started

### Prerequisites
- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Navigate to storefront directory
cd frontend/storefront

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Environment Variables

Create a `.env` file in the root:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Available Scripts

```bash
# Development server (with hot reload)
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Project Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── Header.tsx        # Navigation header with search & cart
│   │   ├── Footer.tsx        # Store info footer
│   │   └── Layout.tsx        # Main layout wrapper
│   ├── ui/
│   │   └── Toaster.tsx       # Toast notifications
│   └── ProductCard.tsx       # Reusable product card component
│
├── pages/
│   ├── HomePage.tsx          # Landing page with featured products
│   ├── ProductsPage.tsx      # Product listing with filters
│   ├── ProductDetailPage.tsx # Single product view
│   ├── CartPage.tsx          # Shopping cart
│   ├── CheckoutPage.tsx      # Checkout & order placement
│   ├── OrderSuccessPage.tsx  # Order confirmation
│   └── TrackOrderPage.tsx    # Order tracking
│
├── store/
│   └── cartStore.ts          # Zustand cart state
│
├── lib/
│   └── api.ts                # Axios API client
│
├── App.tsx                   # Main app with routing
├── main.tsx                  # Entry point
└── index.css                 # Global styles
```

## State Management

### Server State (TanStack Query)
- Product listings
- Store information
- Order data
- Caching and automatic refetching

### Client State (Zustand)
- Shopping cart items
- Persisted to localStorage
- Actions: add, remove, update quantity, clear

## API Integration

### Endpoints Used

```typescript
// Store Info
GET /api/v1/storefront/store-info
GET /api/v1/storefront/categories
GET /api/v1/storefront/featured-products

// Products
GET /api/v1/storefront/products
GET /api/v1/storefront/products/:id

// Orders
POST /api/v1/orders
GET /api/v1/orders/track/:orderNumber
```

### Request Headers
```
X-Store-ID: <store_id>        # Auto-added from URL param
Content-Type: application/json
```

## Multi-Tenant Configuration

The app identifies stores via URL parameter:

```
http://localhost:5173?store_id=STORE123
```

The `store_id` is:
- Extracted from URL query parameter
- Saved to localStorage for persistence
- Automatically added to all API requests

## Styling

### Tailwind Configuration

Custom theme colors match store branding:

```javascript
colors: {
  primary: {
    50: '#eff6ff',
    500: '#3b82f6',
    600: '#2563eb',
    // ...
  }
}
```

### Component Classes

Reusable classes in `index.css`:

```css
.btn                  # Base button
.btn-primary          # Primary action button
.btn-secondary        # Secondary button
.input                # Text input
.card                 # Card container
```

## Form Validation

Using React Hook Form + Zod:

```typescript
const schema = z.object({
  customer_name: z.string().min(2),
  customer_phone: z.string().regex(/^\+?[1-9]\d{9,14}$/),
  delivery_address: z.string().min(10),
  // ...
})
```

## Cart Management

```typescript
// Add item
addItem({
  product_id: 'prod_123',
  name: 'Product Name',
  price: 999.99,
  quantity: 2,
  image: 'https://...'
})

// Update quantity
updateQuantity('prod_123', 5)

// Remove item
removeItem('prod_123')

// Get totals
const totalItems = getTotalItems()
const totalPrice = getTotalPrice()

// Clear cart
clearCart()
```

## Production Build

### Docker Build

```bash
# Build image
docker build -t ecommerce-storefront .

# Run container
docker run -p 80:80 -e VITE_API_URL=https://api.yourdomain.com/api/v1 ecommerce-storefront
```

### Manual Build

```bash
# Build static files
npm run build

# Output in dist/ directory
# Deploy to any static host (Vercel, Netlify, S3, etc.)
```

## Performance Optimizations

- ✅ Code splitting with React Router
- ✅ Image lazy loading
- ✅ Query result caching (5min TTL)
- ✅ Debounced search inputs
- ✅ Optimistic UI updates
- ✅ Gzip compression in production
- ✅ Static asset caching (1 year)

## Browser Support

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Mobile browsers (iOS Safari, Chrome Android)

## Troubleshooting

### TypeScript Errors

```bash
# Install all type definitions
npm install --save-dev @types/react @types/react-dom @types/node
```

### API Connection Issues

1. Verify backend is running: `http://localhost:8000/api/health`
2. Check CORS configuration in backend
3. Verify `VITE_API_URL` environment variable

### Build Failures

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test thoroughly
3. Run type checking: `npm run type-check`
4. Build to verify: `npm run build`
5. Submit pull request

## License

Proprietary - All rights reserved
