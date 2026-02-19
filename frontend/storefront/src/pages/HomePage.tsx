import { useQuery } from '@tanstack/react-query'
import { storeApi } from '@/lib/api'
import ProductCard from '@/components/ProductCard'
import { Link } from 'react-router-dom'
import { ArrowRight, Package, Sparkles, TrendingUp, Shield, Truck, ShoppingBag, Star } from 'lucide-react'
import PromotionalBanner from '@/components/marketing/PromotionalBanner'
import FlashSaleTimer from '@/components/marketing/FlashSaleTimer'
import RecentlyViewed from '@/components/RecentlyViewed'

export default function HomePage() {
    useQuery({
        queryKey: ['store-info'],
        queryFn: () => storeApi.getStoreInfo().then(res => res.data.data),
    })

    const { data: categoriesData } = useQuery({
        queryKey: ['categories'],
        queryFn: () => storeApi.getCategories().then(res => res.data.data),
    })

    const { data: featuredData } = useQuery({
        queryKey: ['featured-products'],
        queryFn: () => storeApi.getFeaturedProducts(8).then(res => res.data.data),
    })

    return (
        <div className="animate-fade-in">
            {/* ── Hero Section ────────────────────────────────────────── */}
            <section className="relative overflow-hidden bg-gradient-to-br from-theme-primary/8 via-bg-secondary to-theme-accent/8 py-14 md:py-20">
                {/* Background blobs */}
                <div className="pointer-events-none absolute inset-0 overflow-hidden">
                    <div className="absolute -top-24 -right-24 h-[480px] w-[480px] rounded-full bg-theme-primary/10 blur-3xl" />
                    <div className="absolute -bottom-24 -left-24 h-[360px] w-[360px] rounded-full bg-theme-accent/10 blur-3xl" />
                </div>

                <div className="container relative z-10 mx-auto px-4">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
                        {/* Copy */}
                        <div>
                            <div className="mb-5 inline-flex animate-bounce-in items-center gap-2 rounded-full border border-theme-primary/20 bg-theme-primary/10 px-3.5 py-1.5 text-sm font-medium text-theme-primary">
                                <Sparkles className="h-4 w-4" />
                                New arrivals every week
                            </div>

                            <h1 className="mb-5 text-5xl md:text-6xl font-extrabold leading-tight tracking-tight text-text-primary">
                                Shop the{' '}
                                <span className="text-gradient">Best Deals</span>
                                <br />Near You
                            </h1>

                            <p className="mb-8 max-w-lg text-lg text-text-secondary">
                                Thousands of products from trusted stores — fresh arrivals, unbeatable prices, doorstep delivery.
                            </p>

                            <div className="mb-10 flex flex-wrap gap-3">
                                <Link to="/products" className="btn btn-primary btn-lg shadow-xl shadow-theme-primary/20">
                                    <ShoppingBag className="h-5 w-5" />
                                    Shop Now
                                </Link>
                                <Link to="/products" className="btn btn-outline btn-lg">
                                    Browse Categories
                                    <ArrowRight className="h-4 w-4" />
                                </Link>
                            </div>

                            {/* Trust stats */}
                            <div className="flex flex-wrap gap-8">
                                {[
                                    { value: '10,000+', label: 'Happy Customers' },
                                    { value: '5,000+', label: 'Products' },
                                    { value: '4.9', label: 'Avg Rating', icon: Star },
                                ].map((s) => (
                                    <div key={s.label}>
                                        <p className="flex items-center gap-1 text-2xl font-bold text-gradient">
                                            {s.value}{s.icon && <s.icon className="h-5 w-5 text-yellow-500 fill-yellow-500" />}
                                        </p>
                                        <p className="text-sm text-text-secondary">{s.label}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Floating product showcase */}
                        <div className="hidden lg:flex items-center justify-center relative h-72">
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="h-56 w-56 rounded-full bg-gradient-to-br from-theme-primary/20 to-theme-accent/20 blur-2xl" />
                            </div>
                            <div className="relative animate-float flex flex-col items-center gap-4">
                                <div className="rounded-3xl bg-bg-primary border border-border-color shadow-2xl p-6 flex flex-col items-center gap-3">
                                    <ShoppingBag className="h-16 w-16 text-theme-primary" />
                                    <p className="font-bold text-text-primary text-lg">Free Delivery</p>
                                    <p className="text-sm text-text-secondary">On orders above ₹499</p>
                                </div>
                                {/* Floating badges */}
                                <div className="absolute -top-6 -right-10 rounded-2xl bg-green-500 text-white px-3 py-1.5 text-xs font-bold shadow-lg animate-bounce-in">
                                    ✓ Verified Sellers
                                </div>
                                <div className="absolute -bottom-4 -left-10 rounded-2xl bg-bg-primary border border-border-color px-3 py-1.5 text-xs font-semibold text-text-primary shadow-lg">
                                    🔒 Secure Payments
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Promotional Banner */}
            <div className="mb-8">
                <PromotionalBanner />
            </div>

            {/* Flash Sales */}
            <FlashSaleTimer />

            <div className="container mx-auto px-4 py-12">
                {/* Value Propositions */}
                <section className="mb-16">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
                        {[
                            { icon: Truck, title: 'Free Delivery', desc: 'On orders above ₹499' },
                            { icon: Shield, title: 'Secure Payments', desc: '100% protected' },
                            { icon: TrendingUp, title: 'Best Prices', desc: 'Guaranteed savings' },
                            { icon: Sparkles, title: 'Quality Products', desc: 'Curated selection' },
                        ].map((item, idx) => (
                            <div key={idx} className="card text-center group hover-lift">
                                <div className="inline-flex p-3 rounded-2xl bg-theme-primary/10 text-theme-primary mb-3 group-hover:bg-theme-primary group-hover:text-white transition-all duration-300">
                                    <item.icon className="h-6 w-6" />
                                </div>
                                <h3 className="font-semibold text-text-primary text-sm md:text-base">{item.title}</h3>
                                <p className="text-text-tertiary text-xs md:text-sm mt-1">{item.desc}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Categories */}
                {categoriesData && categoriesData.length > 0 && (
                    <section className="mb-16">
                        <div className="flex items-center justify-between mb-8">
                            <div>
                                <h2 className="section-title">Shop by Category</h2>
                                <p className="section-subtitle">Explore our wide range of products</p>
                            </div>
                            <Link
                                to="/products"
                                className="hidden md:flex items-center gap-2 text-theme-primary hover:text-theme-primary-hover font-medium group"
                            >
                                <span>View All</span>
                                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                            </Link>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 md:gap-6">
                            {categoriesData.slice(0, 6).map((category: any, idx: number) => (
                                <Link
                                    key={category.id}
                                    to={`/products?category_id=${category.id}`}
                                    className="card card-interactive text-center group"
                                    style={{ animationDelay: `${idx * 50}ms` }}
                                >
                                    <div className="relative mb-4">
                                        <div className="aspect-square rounded-2xl bg-gradient-to-br from-theme-primary/10 to-theme-accent/10 flex items-center justify-center group-hover:from-theme-primary/20 group-hover:to-theme-accent/20 transition-all duration-300">
                                            <Package className="h-10 w-10 md:h-12 md:w-12 text-theme-primary" />
                                        </div>
                                    </div>
                                    <h3 className="font-semibold text-text-primary group-hover:text-theme-primary transition-colors text-sm md:text-base line-clamp-2">
                                        {category.name}
                                    </h3>
                                </Link>
                            ))}
                        </div>
                    </section>
                )}

                {/* Featured Products */}
                {featuredData && featuredData.length > 0 && (
                    <section className="mb-16">
                        <div className="flex items-center justify-between mb-8">
                            <div>
                                <h2 className="section-title flex items-center gap-3">
                                    <span className="text-gradient">Featured Products</span>
                                    <Sparkles className="h-6 w-6 text-theme-accent" />
                                </h2>
                                <p className="section-subtitle">Handpicked just for you</p>
                            </div>
                            <Link
                                to="/products"
                                className="btn btn-secondary group"
                            >
                                <span>View All</span>
                                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                            </Link>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
                            {featuredData.map((product: any) => (
                                <ProductCard key={product.id} product={product} viewMode="grid" />
                            ))}
                        </div>
                    </section>
                )}

                {/* CTA Section */}
                <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-theme-primary to-theme-accent p-8 md:p-12 text-white">
                    <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iLjEiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxNCAwIDYtMi42ODYgNi02cy0yLjY4Ni02LTYtNi02IDIuNjg2LTYgNiAyLjY4NiA2IDYgNnptMCA0OGMzLjMxNCAwIDYtMi42ODYgNi02cy0yLjY4Ni02LTYtNi02IDIuNjg2LTYgNiAyLjY4NiA2IDYgNnoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-30"></div>
                    <div className="relative z-10 text-center max-w-2xl mx-auto">
                        <h2 className="text-2xl md:text-4xl font-bold mb-4">Ready to start shopping?</h2>
                        <p className="text-white/80 mb-8 text-lg">
                            Join thousands of happy customers and discover amazing products at unbeatable prices.
                        </p>
                        <Link to="/products" className="inline-flex items-center gap-2 bg-white text-theme-primary px-8 py-4 rounded-2xl font-semibold hover:bg-bg-tertiary transition-all duration-300 shadow-lg hover:shadow-xl hover:-translate-y-0.5">
                            <span>Explore Products</span>
                            <ArrowRight className="h-5 w-5" />
                        </Link>
                    </div>
                </section>

                {/* ── Recently Viewed ── */}
                <RecentlyViewed />
            </div>
        </div>
    )
}
