# Test script to check if products are available and cart works

Write-Host "Testing E-commerce Platform - Products & Cart" -ForegroundColor Cyan
Write-Host "=" * 50

# Test 1: Check if backend is running
Write-Host "`n1. Checking backend status..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
    Write-Host "   ✓ Backend is running (Status: $($health.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Backend is not responding" -ForegroundColor Red
    exit 1
}

# Test 2: Check if products exist
Write-Host "`n2. Checking if products are available..." -ForegroundColor Yellow
try {
    $productsResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/storefront/featured-products?limit=5" -UseBasicParsing
    $products = $productsResponse.Content | ConvertFrom-Json
    
    if ($products.data -and $products.data.Count -gt 0) {
        Write-Host "   ✓ Found $($products.data.Count) products" -ForegroundColor Green
        Write-Host "   Sample products:" -ForegroundColor Cyan
        foreach ($product in $products.data | Select-Object -First 3) {
            Write-Host "      - $($product.name) (₹$($product.selling_price))" -ForegroundColor White
        }
    }
    else {
        Write-Host "   ⚠ No products found in database!" -ForegroundColor Red
        Write-Host "   You need to add products to the database first." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ✗ Error fetching products: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Check frontend
Write-Host "`n3. Checking frontend status..." -ForegroundColor Yellow
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
    Write-Host "   ✓ Frontend is running (Status: $($frontend.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Frontend is not responding" -ForegroundColor Red
    Write-Host "   Make sure you run: cd frontend\storefront; npm run dev" -ForegroundColor Yellow
}

# Test 4: List all products with pagination
Write-Host "`n4. Checking products list API..." -ForegroundColor Yellow
try {
    $uri = "http://localhost:8000/api/v1/storefront/products?page=1&per_page=100"
    $allProducts = Invoke-WebRequest -Uri $uri -UseBasicParsing
    $productsList = $allProducts.Content | ConvertFrom-Json
    
    if ($productsList.data.items) {
        Write-Host "   ✓ Total products in database: $($productsList.data.total)" -ForegroundColor Green
        Write-Host "   Products per page: $($productsList.data.per_page)" -ForegroundColor White
        Write-Host "   Current page: $($productsList.data.page)" -ForegroundColor White
    }
}
catch {
    Write-Host "   ⚠ Error: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n" + ("=" * 50)
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "- Backend API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "- Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "- Products Page: http://localhost:3000/products" -ForegroundColor White
Write-Host "- Cart Page: http://localhost:3000/cart" -ForegroundColor White
Write-Host "`nTo test cart functionality:" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:3000/products in your browser" -ForegroundColor White
Write-Host "2. Click 'Add to Cart' on any product" -ForegroundColor White
Write-Host "3. Click the cart icon in the header" -ForegroundColor White
Write-Host "4. You should see your products in the cart" -ForegroundColor White
