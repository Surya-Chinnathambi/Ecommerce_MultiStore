import { Link } from 'react-router-dom'
import { Clock, X } from 'lucide-react'
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed'

interface Props {
    /** Product id to exclude from the list (the one currently being viewed) */
    exclude?: string
    title?: string
}

/**
 * Self-contained recently-viewed shelf.
 * Reads from localStorage via the useRecentlyViewed hook.
 */
export default function RecentlyViewed({ exclude, title = 'Recently Viewed' }: Props) {
    const { viewed, clearViewed } = useRecentlyViewed()
    const items = exclude ? viewed.filter(p => p.id !== exclude) : viewed

    if (items.length === 0) return null

    return (
        <section className="mb-12 animate-fade-in">
            <div className="flex items-center justify-between mb-5">
                <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
                    <Clock className="h-5 w-5 text-theme-primary" />
                    {title}
                </h2>
                <button
                    onClick={clearViewed}
                    className="flex items-center gap-1 text-xs text-text-tertiary hover:text-red-500 transition-colors"
                    aria-label="Clear recently viewed"
                >
                    <X className="h-3 w-3" />
                    Clear
                </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 md:gap-4">
                {items.map(product => (
                    <Link
                        key={product.id}
                        to={`/products/${product.id}`}
                        className="card card-hover overflow-hidden p-0 group"
                    >
                        {/* Image */}
                        <div className="aspect-square bg-bg-tertiary relative overflow-hidden">
                            {product.thumbnail ? (
                                <img
                                    src={product.thumbnail}
                                    alt={product.name}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                    loading="lazy"
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-text-tertiary text-xs">
                                    No Image
                                </div>
                            )}
                            {product.discount_percent > 0 && (
                                <span className="absolute top-2 left-2 badge badge-danger py-0.5 text-[10px]">
                                    -{product.discount_percent}%
                                </span>
                            )}
                            {!product.is_in_stock && (
                                <div className="absolute inset-0 bg-bg-primary/60 flex items-center justify-center">
                                    <span className="text-[10px] font-semibold text-text-secondary">Out of Stock</span>
                                </div>
                            )}
                        </div>

                        {/* Info */}
                        <div className="p-2.5">
                            <p className="text-xs font-medium text-text-primary line-clamp-2 mb-1 group-hover:text-theme-primary transition-colors leading-snug">
                                {product.name}
                            </p>
                            <div className="flex items-baseline gap-1.5">
                                <span className="text-sm font-bold text-gradient">
                                    ₹{product.selling_price.toFixed(0)}
                                </span>
                                {product.discount_percent > 0 && (
                                    <span className="text-[10px] text-text-tertiary line-through">
                                        ₹{product.mrp.toFixed(0)}
                                    </span>
                                )}
                            </div>
                        </div>
                    </Link>
                ))}
            </div>
        </section>
    )
}
