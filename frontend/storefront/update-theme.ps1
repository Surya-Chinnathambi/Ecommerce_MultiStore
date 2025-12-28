#!/usr/bin/env pwsh
# Theme Update Script - Batch update all remaining files with theme-aware colors

Write-Host "🎨 Starting theme update for all components..." -ForegroundColor Cyan

$files = @(
    "src/pages/LoginPage.tsx",
    "src/pages/RegisterPage.tsx",
    "src/pages/ProductDetailPage.tsx",
    "src/pages/ProductsPage.tsx",
    "src/pages/CheckoutPage.tsx",
    "src/pages/TrackOrderPage.tsx",
    "src/pages/MyOrdersPage.tsx",
    "src/pages/ProfilePage.tsx",
    "src/pages/AdminOrdersPage.tsx",
    "src/pages/AdminInventoryAlertsPage.tsx",
    "src/pages/AdminReviewsPage.tsx",
    "src/pages/BillingIntegrationPage.tsx",
    "src/pages/MonitoringDashboard.tsx",
    "src/components/GlobalSearch.tsx",
    "src/components/SearchFilters.tsx",
    "src/components/ProductReviews.tsx",
    "src/components/AnalyticsDashboard.tsx",
    "src/components/payment/PaymentGateway.tsx",
    "src/components/payment/RazorpayPayment.tsx",
    "src/components/payment/StripePayment.tsx"
)

$replacements = @{
    # Background colors
    'bg-white(?!\-)' = 'bg-bg-primary'
    'bg-gray-50(?!\-)' = 'bg-bg-secondary'
    'bg-gray-100(?!\-)' = 'bg-bg-tertiary'
    'bg-gray-200(?!\-)' = 'bg-bg-tertiary'
    
    # Text colors
    'text-gray-900(?!\-)' = 'text-text-primary'
    'text-gray-800(?!\-)' = 'text-text-primary'
    'text-gray-700(?!\-)' = 'text-text-primary'
    'text-gray-600(?!\-)' = 'text-text-secondary'
    'text-gray-500(?!\-)' = 'text-text-tertiary'
    'text-gray-400(?!\-)' = 'text-text-tertiary'
    
    # Border colors
    'border-gray-200(?!\-)' = 'border-border-color'
    'border-gray-300(?!\-)' = 'border-border-color'
    'border-gray-400(?!\-)' = 'border-border-color'
    
    # Brand colors
    'bg-blue-600(?!\-)' = 'bg-theme-primary'
    'bg-blue-700(?!\-)' = 'bg-theme-primary-hover'
    'bg-primary-600(?!\-)' = 'bg-theme-primary'
    'bg-primary-700(?!\-)' = 'bg-theme-primary-hover'
    'text-blue-600(?!\-)' = 'text-theme-primary'
    'text-blue-700(?!\-)' = 'text-theme-primary-hover'
    'text-primary-600(?!\-)' = 'text-theme-primary'
    'text-primary-700(?!\-)' = 'text-theme-primary-hover'
    'hover:bg-blue-700(?!\-)' = 'hover:bg-theme-primary-hover'
    'hover:bg-primary-700(?!\-)' = 'hover:bg-theme-primary-hover'
    'hover:text-blue-700(?!\-)' = 'hover:text-theme-primary-hover'
    'hover:text-primary-700(?!\-)' = 'hover:text-theme-primary-hover'
    
    # Accent colors
    'bg-purple-600(?!\-)' = 'bg-theme-accent'
    'text-purple-600(?!\-)' = 'text-theme-accent'
    'bg-pink-600(?!\-)' = 'bg-theme-accent'
    'text-pink-600(?!\-)' = 'text-theme-accent'
}

$baseDir = "c:\ecommerce-platform\frontend\storefront"
$updatedCount = 0
$errorCount = 0

foreach ($file in $files) {
    $filePath = Join-Path $baseDir $file
    
    if (Test-Path $filePath) {
        Write-Host "📝 Processing: $file" -ForegroundColor Yellow
        
        try {
            $content = Get-Content $filePath -Raw -Encoding UTF8
            $originalContent = $content
            
            foreach ($pattern in $replacements.Keys) {
                $replacement = $replacements[$pattern]
                $content = $content -replace $pattern, $replacement
            }
            
            if ($content -ne $originalContent) {
                Set-Content $filePath $content -Encoding UTF8 -NoNewline
                Write-Host "  ✅ Updated successfully" -ForegroundColor Green
                $updatedCount++
            } else {
                Write-Host "  ℹ️  No changes needed" -ForegroundColor Gray
            }
        }
        catch {
            Write-Host "  ❌ Error: $_" -ForegroundColor Red
            $errorCount++
        }
    }
    else {
        Write-Host "  ⚠️  File not found: $filePath" -ForegroundColor Magenta
    }
}

Write-Host "`n=======================" -ForegroundColor Cyan
Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "  Updated: $updatedCount files" -ForegroundColor Green
Write-Host "  Errors: $errorCount files" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host "=======================" -ForegroundColor Cyan

if ($updatedCount -gt 0) {
    Write-Host "`n✨ Theme update completed! Run 'npm run dev' to see the changes." -ForegroundColor Green
}
