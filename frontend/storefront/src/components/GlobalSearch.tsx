import { useState, useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/v1'

export default function GlobalSearch() {
    const [searchTerm, setSearchTerm] = useState('')
    const [isOpen, setIsOpen] = useState(false)
    const searchRef = useRef<HTMLDivElement>(null)
    const navigate = useNavigate()

    // Search products
    const { data: searchResults, isLoading } = useQuery({
        queryKey: ['search', searchTerm],
        queryFn: () => axios.get(`${API_BASE}/search`, { params: { q: searchTerm } }).then(res => res.data.data),
        enabled: searchTerm.length >= 2,
    })

    // Get suggestions
    const { data: suggestions } = useQuery({
        queryKey: ['suggestions', searchTerm],
        queryFn: () => axios.get(`${API_BASE}/search/suggestions`, { params: { q: searchTerm } }).then(res => res.data.data),
        enabled: searchTerm.length >= 2,
    })

    // Close dropdown on outside click
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const handleSearch = (query: string) => {
        if (query.trim()) {
            navigate(`/products?search=${encodeURIComponent(query)}`)
            setIsOpen(false)
            setSearchTerm('')
        }
    }

    const handleProductClick = (productId: string) => {
        navigate(`/products/${productId}`)
        setIsOpen(false)
        setSearchTerm('')
    }

    return (
        <div ref={searchRef} className="relative w-full max-w-2xl">
            <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => {
                        setSearchTerm(e.target.value)
                        setIsOpen(true)
                    }}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch(searchTerm)}
                    placeholder="Search products..."
                    className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                {searchTerm && (
                    <button
                        onClick={() => {
                            setSearchTerm('')
                            setIsOpen(false)
                        }}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2"
                        aria-label="Clear search"
                    >
                        <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                    </button>
                )}
            </div>

            {/* Dropdown Results */}
            {isOpen && searchTerm.length >= 2 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
                    {isLoading ? (
                        <div className="p-4 text-center text-gray-500">Searching...</div>
                    ) : (
                        <>
                            {/* Suggestions */}
                            {suggestions && suggestions.length > 0 && (
                                <div className="border-b border-gray-200">
                                    <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
                                        Suggestions
                                    </div>
                                    {suggestions.map((suggestion: string, idx: number) => (
                                        <button
                                            key={idx}
                                            onClick={() => handleSearch(suggestion)}
                                            className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-2"
                                        >
                                            <Search className="h-4 w-4 text-gray-400" />
                                            <span className="text-sm text-gray-700">{suggestion}</span>
                                        </button>
                                    ))}
                                </div>
                            )}

                            {/* Products */}
                            {searchResults && searchResults.length > 0 ? (
                                <div>
                                    <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
                                        Products
                                    </div>
                                    {searchResults.map((product: any) => (
                                        <button
                                            key={product.id}
                                            onClick={() => handleProductClick(product.id)}
                                            className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center space-x-3"
                                        >
                                            {product.thumbnail ? (
                                                <img
                                                    src={product.thumbnail}
                                                    alt={product.name}
                                                    className="w-12 h-12 object-cover rounded"
                                                />
                                            ) : (
                                                <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center">
                                                    <Search className="h-6 w-6 text-gray-400" />
                                                </div>
                                            )}
                                            <div className="flex-1">
                                                <div className="text-sm font-medium text-gray-900">{product.name}</div>
                                                <div className="text-sm text-gray-500">
                                                    ₹{product.selling_price}
                                                    {product.mrp > product.selling_price && (
                                                        <span className="ml-2 line-through text-gray-400">
                                                            ₹{product.mrp}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            {product.is_in_stock ? (
                                                <span className="text-xs text-green-600 font-medium">In Stock</span>
                                            ) : (
                                                <span className="text-xs text-red-600 font-medium">Out of Stock</span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            ) : searchTerm.length >= 2 && !isLoading ? (
                                <div className="p-4 text-center text-gray-500">
                                    No products found for "{searchTerm}"
                                </div>
                            ) : null}

                            {/* View All Results */}
                            {searchResults && searchResults.length > 0 && (
                                <button
                                    onClick={() => handleSearch(searchTerm)}
                                    className="w-full px-4 py-3 text-center text-sm font-medium text-primary-600 hover:bg-primary-50 border-t border-gray-200"
                                >
                                    View all results for "{searchTerm}"
                                </button>
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    )
}
