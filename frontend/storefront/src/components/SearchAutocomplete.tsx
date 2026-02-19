import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, X, Package } from 'lucide-react'
import { api } from '@/lib/api'

interface Suggestion {
    id: string
    name: string
    price: number
    thumbnail?: string
}

export default function SearchAutocomplete() {
    const navigate = useNavigate()
    const [query, setQuery] = useState('')
    const [suggestions, setSuggestions] = useState<Suggestion[]>([])
    const [loading, setLoading] = useState(false)
    const [open, setOpen] = useState(false)
    const [selected, setSelected] = useState(-1)
    const inputRef = useRef<HTMLInputElement>(null)
    const containerRef = useRef<HTMLDivElement>(null)
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    const getSuggestions = useCallback(async (q: string) => {
        if (q.length < 2) {
            setSuggestions([])
            return
        }
        setLoading(true)
        try {
            const res = await api.get('/search/typesense/autocomplete', { params: { q, limit: 8 } })
            const data = res.data.data ?? []
            setSuggestions(data)
            setOpen(data.length > 0)
        } catch {
            // Fallback silently — Typesense may not be running in dev
            setSuggestions([])
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        if (debounceRef.current) clearTimeout(debounceRef.current)
        if (!query.trim()) {
            setSuggestions([])
            setOpen(false)
            return
        }
        debounceRef.current = setTimeout(() => getSuggestions(query), 250)
        return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
    }, [query, getSuggestions])

    // Close on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setOpen(false)
                setSelected(-1)
            }
        }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    const handleSearch = (q = query) => {
        if (!q.trim()) return
        setOpen(false)
        navigate(`/search?q=${encodeURIComponent(q.trim())}`)
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!open) return
        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setSelected((s) => Math.min(s + 1, suggestions.length - 1))
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setSelected((s) => Math.max(s - 1, -1))
        } else if (e.key === 'Enter') {
            e.preventDefault()
            if (selected >= 0 && suggestions[selected]) {
                navigate(`/products/${suggestions[selected].id}`)
                setOpen(false)
            } else {
                handleSearch()
            }
        } else if (e.key === 'Escape') {
            setOpen(false)
            setSelected(-1)
        }
    }

    return (
        <div ref={containerRef} className="relative w-full">
            <form onSubmit={(e) => { e.preventDefault(); handleSearch() }}>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary pointer-events-none" />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => { setQuery(e.target.value); setSelected(-1) }}
                        onFocus={() => suggestions.length > 0 && setOpen(true)}
                        onKeyDown={handleKeyDown}
                        placeholder="Search products..."
                        className="w-full pl-10 pr-10 py-2.5 bg-bg-tertiary/50 border border-border-color rounded-xl text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-theme-primary/40 focus:border-theme-primary transition-all"
                    />
                    {query && (
                        <button
                            type="button"
                            aria-label="Clear search"
                            onClick={() => { setQuery(''); setSuggestions([]); setOpen(false); inputRef.current?.focus() }}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-primary"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    )}
                </div>
            </form>

            {/* Dropdown */}
            {open && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-bg-primary border border-border-color rounded-xl shadow-xl z-50 overflow-hidden">
                    {loading && (
                        <div className="px-4 py-3 text-sm text-text-tertiary flex items-center gap-2">
                            <div className="h-4 w-4 border-2 border-theme-primary border-t-transparent rounded-full animate-spin" />
                            Searching...
                        </div>
                    )}
                    {!loading && suggestions.length > 0 && (
                        <ul>
                            {suggestions.map((s, idx) => (
                                <li key={s.id}>
                                    <button
                                        onMouseDown={(e) => e.preventDefault()}
                                        onClick={() => {
                                            navigate(`/products/${s.id}`)
                                            setOpen(false)
                                            setQuery(s.name)
                                        }}
                                        onMouseEnter={() => setSelected(idx)}
                                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors
                                            ${selected === idx ? 'bg-bg-tertiary' : 'hover:bg-bg-tertiary/60'}`}
                                    >
                                        <div className="w-9 h-9 rounded-lg bg-bg-tertiary flex-shrink-0 overflow-hidden">
                                            {s.thumbnail ? (
                                                <img src={s.thumbnail} alt={s.name} className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center">
                                                    <Package className="h-4 w-4 text-text-tertiary" />
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-text-primary truncate">{s.name}</p>
                                            <p className="text-xs text-text-secondary">₹{s.price?.toLocaleString()}</p>
                                        </div>
                                        <Search className="h-3.5 w-3.5 text-text-tertiary flex-shrink-0" />
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}

                    {/* Search all results */}
                    {query.trim() && (
                        <button
                            onMouseDown={(e) => e.preventDefault()}
                            onClick={() => handleSearch()}
                            aria-label={`Search all results for ${query}`}
                            className="w-full flex items-center gap-2 px-4 py-3 text-sm text-theme-primary hover:bg-bg-tertiary/60 border-t border-border-color transition-colors"
                        >
                            <Search className="h-4 w-4" />
                            Search all results for "<strong>{query}</strong>"
                        </button>
                    )}
                </div>
            )}
        </div>
    )
}
