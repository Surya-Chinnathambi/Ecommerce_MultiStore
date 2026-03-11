import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Megaphone, Zap, Plus, X, Trash2, Clock, Eye, ExternalLink, Image as ImageIcon, Layers, Activity, Sparkles, BarChart3 } from 'lucide-react'
import api from '@/lib/api'
import { toast } from '@/components/ui/Toaster'
import Modal, { ModalBody, ModalHeader } from '@/components/ui/Modal'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Banner {
    id: string
    title: string
    subtitle?: string
    description?: string
    image_url?: string
    link_url?: string
    banner_type: string
    status: string
    start_date: string
    end_date?: string
    display_order: number
    click_count: number
}

interface FlashSale {
    id: string
    name: string
    description?: string
    product_id: string
    original_price: number
    sale_price: number
    discount_percent: number
    start_time: string
    end_time: string
    max_quantity?: number
    sold_quantity: number
    is_active: boolean
    product?: { id: string; name: string; thumbnail?: string; sku: string }
}

const storeId = () => localStorage.getItem('store_id') ?? ''

// ─── Empty forms ──────────────────────────────────────────────────────────────

const emptyBanner = {
    title: '', subtitle: '', description: '', image_url: '', link_url: '',
    banner_type: 'promotional', display_order: 0,
    start_date: new Date().toISOString().slice(0, 16),
    end_date: '',
}

const emptyFlash = {
    name: '', description: '',
    product_id: '', sale_price: '',
    start_time: new Date().toISOString().slice(0, 16),
    end_time: new Date(Date.now() + 86400000).toISOString().slice(0, 16),
    max_quantity: '',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const BANNER_TYPES = ['hero', 'promotional', 'category', 'flash_sale']
const STAGGER_DELAY_CLASSES = ['[animation-delay:0ms]', '[animation-delay:80ms]', '[animation-delay:160ms]', '[animation-delay:240ms]', '[animation-delay:320ms]', '[animation-delay:400ms]', '[animation-delay:480ms]', '[animation-delay:560ms]']

// ─── Offer Templates ─────────────────────────────────────────────────────────

const OFFER_TEMPLATES = [
    { id: 'flash-deal', bannerType: 'hero', name: 'Flash Deal', desc: 'Urgent limited-time offer', emoji: '⚡', headerBg: 'bg-gradient-to-br from-red-600 to-orange-500', badgeBg: 'bg-yellow-400', badgeText: 'text-black', cardBorder: 'border-red-500/40' },
    { id: 'weekend-sale', bannerType: 'hero', name: 'Weekend Sale', desc: 'Weekend promotions & events', emoji: '🎉', headerBg: 'bg-gradient-to-br from-purple-600 to-pink-500', badgeBg: 'bg-white', badgeText: 'text-purple-700', cardBorder: 'border-purple-500/40' },
    { id: 'new-arrival', bannerType: 'promotional', name: 'New Arrival', desc: 'Showcase just-dropped products', emoji: '✨', headerBg: 'bg-gradient-to-br from-emerald-500 to-teal-600', badgeBg: 'bg-white', badgeText: 'text-emerald-700', cardBorder: 'border-emerald-500/40' },
    { id: 'clearance', bannerType: 'promotional', name: 'Clearance', desc: 'Clear old inventory fast', emoji: '🔥', headerBg: 'bg-gradient-to-br from-amber-400 to-orange-600', badgeBg: 'bg-red-600', badgeText: 'text-white', cardBorder: 'border-amber-500/40' },
    { id: 'bundle-offer', bannerType: 'promotional', name: 'Bundle Offer', desc: 'Buy more, save more deals', emoji: '🎁', headerBg: 'bg-gradient-to-br from-blue-600 to-indigo-700', badgeBg: 'bg-cyan-400', badgeText: 'text-blue-900', cardBorder: 'border-blue-500/40' },
    { id: 'seasonal', bannerType: 'hero', name: 'Seasonal', desc: 'Holiday & seasonal campaigns', emoji: '🌟', headerBg: 'bg-gradient-to-br from-rose-400 to-pink-600', badgeBg: 'bg-white', badgeText: 'text-rose-700', cardBorder: 'border-rose-500/40' },
    { id: 'luxury-drop', bannerType: 'hero', name: 'Luxury Drop', desc: 'Premium launch with cinematic look', emoji: '💎', headerBg: 'bg-gradient-to-br from-zinc-900 via-slate-800 to-zinc-700', badgeBg: 'bg-amber-300', badgeText: 'text-zinc-900', cardBorder: 'border-amber-400/40' },
    { id: 'midnight-tech', bannerType: 'category', name: 'Midnight Tech', desc: 'Sharp neon style for electronics', emoji: '🛰️', headerBg: 'bg-gradient-to-br from-slate-950 via-cyan-900 to-blue-900', badgeBg: 'bg-cyan-300', badgeText: 'text-slate-950', cardBorder: 'border-cyan-400/40' },
    { id: 'monsoon-fresh', bannerType: 'promotional', name: 'Monsoon Fresh', desc: 'Lifestyle look with soft gradients', emoji: '🌧️', headerBg: 'bg-gradient-to-br from-teal-700 via-emerald-600 to-lime-500', badgeBg: 'bg-white', badgeText: 'text-teal-800', cardBorder: 'border-emerald-400/40' },
    { id: 'realtime-rush', bannerType: 'flash_sale', name: 'Realtime Rush', desc: 'Live countdown + shoppers pulse', emoji: '📈', headerBg: 'bg-gradient-to-br from-fuchsia-700 via-violet-700 to-indigo-700', badgeBg: 'bg-white', badgeText: 'text-fuchsia-700', cardBorder: 'border-fuchsia-400/50' },
]

const emptyTemplateForm = {
    productImage: '',
    productName: '',
    originalPrice: '',
    offerPrice: '',
    discountPercent: '',
    tagline: '',
    linkUrl: '',
    start_date: new Date().toISOString().slice(0, 16),
    end_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 16),
    viewersNow: '41',
    stockLeft: '24',
    realtimeMode: true,
}

function fmtDate(d: string) {
    return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function isActive(start: string, end?: string) {
    const now = Date.now()
    const s = new Date(start).getTime()
    const e = end ? new Date(end).getTime() : Infinity
    return now >= s && now <= e
}

function formatCountdown(endDate: string, nowMs: number) {
    const end = new Date(endDate).getTime()
    if (!end || Number.isNaN(end)) return 'No end date'
    const diff = end - nowMs
    if (diff <= 0) return 'Expired'
    const total = Math.floor(diff / 1000)
    const h = Math.floor(total / 3600)
    const m = Math.floor((total % 3600) / 60)
    const s = total % 60
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function AdminAdsPage() {
    const qc = useQueryClient()
    const [tab, setTab] = useState<'banners' | 'flash' | 'templates'>('banners')
    const [showBannerForm, setShowBannerForm] = useState(false)
    const [showFlashForm, setShowFlashForm] = useState(false)
    const [bannerForm, setBannerForm] = useState({ ...emptyBanner })
    const [flashForm, setFlashForm] = useState({ ...emptyFlash })
    const [deletingId, setDeletingId] = useState<string | null>(null)
    const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
    const [templateForm, setTemplateForm] = useState({ ...emptyTemplateForm })
    const [previewNowMs, setPreviewNowMs] = useState(Date.now())
    const [viewerPulse, setViewerPulse] = useState(0)

    useEffect(() => {
        if (tab !== 'templates' || !selectedTemplate) return
        const t = setInterval(() => {
            setPreviewNowMs(Date.now())
            setViewerPulse(Math.floor(Math.random() * 7) - 3)
        }, 1000)
        return () => clearInterval(t)
    }, [tab, selectedTemplate])

    // ── Queries ────────────────────────────────────────────────────────────────

    const { data: banners = [], isLoading: bannersLoading } = useQuery<Banner[]>({
        queryKey: ['admin-banners'],
        queryFn: () =>
            api.get(`/marketing/banners?store_id=${storeId()}&include_inactive=true`).then(r => r.data.data ?? r.data),
    })

    const { data: flashSales = [], isLoading: flashLoading } = useQuery<FlashSale[]>({
        queryKey: ['admin-flash-sales'],
        queryFn: () =>
            api.get(`/marketing/flash-sales?store_id=${storeId()}&active_only=false`).then(r => r.data.data ?? r.data),
    })

    // ── Mutations ──────────────────────────────────────────────────────────────

    const createBanner = useMutation({
        mutationFn: (data: typeof emptyBanner) => api.post('/marketing/banners', data),
        onSuccess: () => {
            toast.success('Banner created!')
            qc.invalidateQueries({ queryKey: ['admin-banners'] })
            setShowBannerForm(false)
            setBannerForm({ ...emptyBanner })
        },
        onError: (err: any) => {
            const status = err?.response?.status
            const detail = err?.response?.data?.detail
            if (status === 401) {
                toast.error('Session expired. Please sign in again.')
                return
            }
            if (typeof detail === 'string' && detail.trim()) {
                toast.error(detail)
                return
            }
            toast.error('Failed to create banner')
        },
    })

    const deleteBanner = useMutation({
        mutationFn: (id: string) => api.delete(`/marketing/banners/${id}`),
        onSuccess: () => {
            toast.success('Banner deleted')
            qc.invalidateQueries({ queryKey: ['admin-banners'] })
            setDeletingId(null)
        },
        onError: () => toast.error('Failed to delete banner'),
    })

    const createFlash = useMutation({
        mutationFn: (data: typeof emptyFlash) => api.post('/marketing/flash-sales', data),
        onSuccess: () => {
            toast.success('Flash sale created!')
            qc.invalidateQueries({ queryKey: ['admin-flash-sales'] })
            setShowFlashForm(false)
            setFlashForm({ ...emptyFlash })
        },
        onError: () => toast.error('Failed to create flash sale'),
    })

    const deactivateFlash = useMutation({
        mutationFn: (id: string) => api.patch(`/marketing/flash-sales/${id}`, { is_active: false }),
        onSuccess: () => {
            toast.success('Flash sale deactivated')
            qc.invalidateQueries({ queryKey: ['admin-flash-sales'] })
        },
        onError: () => toast.error('Failed to deactivate'),
    })

    const liveBannerCount = banners.filter(b => isActive(b.start_date, b.end_date)).length
    const scheduledBannerCount = banners.length - liveBannerCount
    const activeFlashCount = flashSales.filter(fs => fs.is_active && isActive(fs.start_time, fs.end_time)).length
    const totalBannerClicks = banners.reduce((sum, b) => sum + (b.click_count || 0), 0)
    const avgClicksPerBanner = banners.length ? Math.round(totalBannerClicks / banners.length) : 0
    const campaignHealth = banners.length ? Math.round((liveBannerCount / banners.length) * 100) : 0
    const featuredBanners = [...banners].sort((a, b) => (b.click_count || 0) - (a.click_count || 0)).slice(0, 3)

    // ── Render ─────────────────────────────────────────────────────────────────

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in relative overflow-hidden">
            <div className="pointer-events-none absolute -top-16 -right-20 h-52 w-52 rounded-full bg-theme-primary/10 blur-3xl animate-float" />
            <div className="pointer-events-none absolute top-28 -left-24 h-48 w-48 rounded-full bg-cyan-500/10 blur-3xl animate-float [animation-delay:800ms]" />

            {/* Header */}
            <div className="relative mb-6 rounded-3xl border border-border-color bg-gradient-to-br from-bg-primary via-bg-primary to-theme-primary/5 p-5 sm:p-6 shadow-lg overflow-hidden">
                <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full border border-theme-primary/30 animate-spin-slow" />
                <div className="pointer-events-none absolute right-20 bottom-0 h-16 w-16 rounded-full bg-theme-accent/20 blur-2xl animate-float" />

                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    <div>
                        <h1 className="section-title flex items-center gap-2">
                            <Megaphone className="h-6 w-6 text-theme-primary animate-bounce-in" />
                            Ads Command Center
                        </h1>
                        <p className="section-subtitle">Redesigned campaign workspace with live previews and one-click publishing.</p>
                    </div>
                    <div className="grid grid-cols-3 gap-2 sm:gap-3 lg:w-auto">
                        <div className="rounded-xl border border-border-color bg-bg-secondary/70 px-3 py-2">
                            <p className="text-[11px] uppercase tracking-wide text-text-tertiary">Live Banners</p>
                            <p className="text-lg font-bold text-emerald-500">{liveBannerCount}</p>
                        </div>
                        <div className="rounded-xl border border-border-color bg-bg-secondary/70 px-3 py-2">
                            <p className="text-[11px] uppercase tracking-wide text-text-tertiary">Scheduled</p>
                            <p className="text-lg font-bold text-amber-500">{scheduledBannerCount}</p>
                        </div>
                        <div className="rounded-xl border border-border-color bg-bg-secondary/70 px-3 py-2">
                            <p className="text-[11px] uppercase tracking-wide text-text-tertiary">Flash Active</p>
                            <p className="text-lg font-bold text-cyan-500">{activeFlashCount}</p>
                        </div>
                    </div>
                </div>
                {tab !== 'templates' && (
                    <button
                        onClick={() => tab === 'banners' ? setShowBannerForm(true) : setShowFlashForm(true)}
                        className="btn btn-primary mt-4"
                    >
                        <Plus className="h-4 w-4" />
                        {tab === 'banners' ? 'New Banner' : 'New Flash Sale'}
                    </button>
                )}

                <div className="mt-5 grid lg:grid-cols-3 gap-3">
                    <div className="lg:col-span-2 rounded-2xl border border-border-color bg-bg-secondary/70 p-4">
                        <div className="flex items-center justify-between gap-2 mb-3">
                            <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                                <Activity className="h-4 w-4 text-cyan-500" /> Campaign Intelligence
                            </h3>
                            <span className="text-xs text-text-tertiary">Live analytics snapshot</span>
                        </div>
                        <div className="grid sm:grid-cols-3 gap-2">
                            <div className="rounded-xl border border-border-color bg-bg-primary/80 p-3">
                                <p className="text-[11px] uppercase tracking-wide text-text-tertiary">Total Clicks</p>
                                <p className="text-lg font-black text-cyan-400">{totalBannerClicks}</p>
                            </div>
                            <div className="rounded-xl border border-border-color bg-bg-primary/80 p-3">
                                <p className="text-[11px] uppercase tracking-wide text-text-tertiary">Avg/Banner</p>
                                <p className="text-lg font-black text-violet-400">{avgClicksPerBanner}</p>
                            </div>
                            <div className="rounded-xl border border-border-color bg-bg-primary/80 p-3">
                                <p className="text-[11px] uppercase tracking-wide text-text-tertiary">Health Score</p>
                                <p className="text-lg font-black text-emerald-400">{campaignHealth}%</p>
                                <div className="mt-2 h-1.5 rounded-full bg-bg-tertiary overflow-hidden">
                                    <style dangerouslySetInnerHTML={{ __html: `.ad-health-meter{width:${campaignHealth}%}` }} />
                                    <div className="ad-health-meter h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400" />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-border-color bg-bg-secondary/70 p-4">
                        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-2">
                            <Sparkles className="h-4 w-4 text-amber-400" /> Creative Quality
                        </h3>
                        <p className="text-xs text-text-secondary mb-3">Realistic ads convert better when creative and urgency are both present.</p>
                        <div className="space-y-2 text-xs">
                            <div className="flex items-center justify-between rounded-lg bg-bg-primary/70 border border-border-color px-2.5 py-1.5">
                                <span className="text-text-secondary">Visual richness</span>
                                <span className="font-semibold text-emerald-400">Good</span>
                            </div>
                            <div className="flex items-center justify-between rounded-lg bg-bg-primary/70 border border-border-color px-2.5 py-1.5">
                                <span className="text-text-secondary">Urgency signals</span>
                                <span className="font-semibold text-cyan-400">Realtime</span>
                            </div>
                            <div className="flex items-center justify-between rounded-lg bg-bg-primary/70 border border-border-color px-2.5 py-1.5">
                                <span className="text-text-secondary">Campaign variety</span>
                                <span className="font-semibold text-violet-400">{OFFER_TEMPLATES.length} templates</span>
                            </div>
                        </div>
                    </div>
                </div>

                {featuredBanners.length > 0 && (
                    <div className="mt-4 rounded-2xl border border-border-color bg-bg-secondary/65 p-3">
                        <div className="flex items-center gap-2 mb-2 text-xs uppercase tracking-wider text-text-tertiary">
                            <BarChart3 className="h-3.5 w-3.5" /> Top Campaigns
                        </div>
                        <div className="grid md:grid-cols-3 gap-2">
                            {featuredBanners.map((b) => (
                                <div key={b.id} className="rounded-xl border border-border-color bg-bg-primary/80 p-2.5">
                                    <p className="text-sm font-semibold text-text-primary truncate">{b.title}</p>
                                    <div className="mt-1 flex items-center justify-between text-[11px] text-text-tertiary">
                                        <span className="capitalize">{b.banner_type.replace('_', ' ')}</span>
                                        <span className="text-cyan-400 font-semibold">{b.click_count} clicks</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Tabs */}
            <div className="flex gap-1 p-1.5 bg-bg-tertiary/80 rounded-2xl mb-6 w-fit border border-border-color shadow-sm">
                {(['banners', 'flash', 'templates'] as const).map(t => (
                    <button
                        key={t}
                        onClick={() => setTab(t)}
                        className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${tab === t ? 'bg-bg-primary shadow-md text-text-primary scale-[1.02]' : 'text-text-secondary hover:text-text-primary hover:bg-bg-primary/40'
                            }`}
                    >
                        {t === 'banners' ? (
                            <><Megaphone className="inline h-4 w-4 mr-1.5" />Banners</>
                        ) : t === 'flash' ? (
                            <><Zap className="inline h-4 w-4 mr-1.5" />Flash Sales</>
                        ) : (
                            <><Layers className="inline h-4 w-4 mr-1.5" />Templates</>
                        )}
                    </button>
                ))}
            </div>

            {/* ── BANNERS TAB ── */}
            {tab === 'banners' && (
                <>
                    {bannersLoading ? (
                        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {[1, 2, 3].map(i => <div key={i} className="skeleton h-48 rounded-2xl" />)}
                        </div>
                    ) : banners.length === 0 ? (
                        <div className="card text-center py-16">
                            <ImageIcon className="h-12 w-12 mx-auto text-text-tertiary mb-3" />
                            <p className="text-text-secondary">No banners yet. Create your first banner!</p>
                        </div>
                    ) : (
                        <div className="grid sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-5">
                            {banners.map(b => {
                                const live = isActive(b.start_date, b.end_date)
                                return (
                                    <div
                                        key={b.id}
                                        className={`card p-0 overflow-hidden border transition-all duration-300 hover:-translate-y-1 hover:shadow-xl animate-slide-up ${STAGGER_DELAY_CLASSES[b.display_order % STAGGER_DELAY_CLASSES.length]} ${live ? 'border-emerald-500/40 shadow-[0_10px_30px_rgba(16,185,129,0.12)]' : 'border-border-color'
                                            }`}
                                    >
                                        {/* Image preview */}
                                        {b.image_url ? (
                                            <img src={b.image_url} alt={b.title} className="w-full h-32 object-cover" />
                                        ) : (
                                            <div className="w-full h-32 bg-gradient-to-br from-theme-primary/20 to-theme-accent/20 flex items-center justify-center">
                                                <Megaphone className="h-10 w-10 text-theme-primary/40" />
                                            </div>
                                        )}
                                        <div className="p-4 space-y-2">
                                            <div className="flex items-start justify-between gap-2">
                                                <h3 className="font-semibold text-text-primary text-sm leading-tight">{b.title}</h3>
                                                <span className={`badge flex-shrink-0 text-xs ${live ? 'bg-emerald-500/10 text-emerald-600' : 'bg-bg-tertiary text-text-tertiary'
                                                    }`}>
                                                    {live ? (
                                                        <>
                                                            <span className="relative inline-flex h-2 w-2 mr-1.5 rounded-full bg-emerald-500">
                                                                <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 animate-ping" />
                                                            </span>
                                                            Live
                                                        </>
                                                    ) : <><Clock className="h-3 w-3 inline mr-1" />Inactive</>}
                                                </span>
                                            </div>
                                            {b.subtitle && <p className="text-xs text-text-secondary line-clamp-2">{b.subtitle}</p>}
                                            <div className="flex items-center justify-between text-xs text-text-tertiary">
                                                <span className="capitalize badge bg-bg-tertiary text-text-secondary">{b.banner_type}</span>
                                                <span className="flex items-center gap-1"><Eye className="h-3 w-3" />{b.click_count} clicks</span>
                                            </div>
                                            <p className="text-xs text-text-tertiary">From {fmtDate(b.start_date)}</p>
                                            {b.link_url && (
                                                <a href={b.link_url} target="_blank" rel="noopener noreferrer"
                                                    className="text-xs text-theme-primary flex items-center gap-1 hover:underline truncate">
                                                    <ExternalLink className="h-3 w-3 flex-shrink-0" />{b.link_url}
                                                </a>
                                            )}
                                        </div>
                                        <div className="px-4 pb-4">
                                            {deletingId === b.id ? (
                                                <div className="flex gap-2">
                                                    <button onClick={() => deleteBanner.mutate(b.id)} className="btn btn-sm flex-1 bg-red-500 text-white hover:bg-red-600">
                                                        Confirm Delete
                                                    </button>
                                                    <button onClick={() => setDeletingId(null)} className="btn btn-sm btn-outline">Cancel</button>
                                                </div>
                                            ) : (
                                                <button onClick={() => setDeletingId(b.id)} className="btn btn-sm btn-ghost text-red-500 hover:bg-red-500/10 w-full">
                                                    <Trash2 className="h-3.5 w-3.5" /> Delete Banner
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </>
            )}

            {/* ── FLASH SALES TAB ── */}
            {tab === 'flash' && (
                <>
                    {flashLoading ? (
                        <div className="space-y-3">
                            {[1, 2].map(i => <div key={i} className="skeleton h-24 rounded-2xl" />)}
                        </div>
                    ) : flashSales.length === 0 ? (
                        <div className="card text-center py-16">
                            <Zap className="h-12 w-12 mx-auto text-text-tertiary mb-3" />
                            <p className="text-text-secondary">No flash sales yet. Launch your first one!</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {flashSales.map(fs => {
                                const live = fs.is_active && isActive(fs.start_time, fs.end_time)
                                const soldPct = fs.max_quantity ? Math.round((fs.sold_quantity / fs.max_quantity) * 100) : null
                                return (
                                    <div key={fs.id} className={`card border-2 transition-all ${live ? 'border-yellow-500/30 bg-yellow-500/5' : 'border-border-color'
                                        }`}>
                                        <div className="flex items-center gap-4">
                                            {fs.product?.thumbnail && (
                                                <img src={fs.product.thumbnail} alt="" className="h-16 w-16 rounded-xl object-cover flex-shrink-0" />
                                            )}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h3 className="font-semibold text-text-primary">{fs.name}</h3>
                                                    <span className={`badge text-xs ${live ? 'bg-yellow-500/10 text-yellow-600' : 'bg-bg-tertiary text-text-tertiary'
                                                        }`}>
                                                        <Zap className="h-3 w-3 inline mr-0.5" />{live ? 'Active' : 'Ended'}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-text-secondary">
                                                    {fs.product?.name ?? fs.product_id} &bull;&nbsp;
                                                    <span className="line-through text-text-tertiary">₹{fs.original_price.toFixed(0)}</span>
                                                    &nbsp;→&nbsp;
                                                    <span className="text-green-600 font-bold">₹{fs.sale_price.toFixed(0)}</span>
                                                    &nbsp;<span className="badge bg-red-500/10 text-red-500 text-xs">-{fs.discount_percent.toFixed(0)}%</span>
                                                </p>
                                                <p className="text-xs text-text-tertiary mt-1">
                                                    {fmtDate(fs.start_time)} → {fmtDate(fs.end_time)}
                                                    {fs.max_quantity && ` · ${fs.sold_quantity}/${fs.max_quantity} sold`}
                                                </p>
                                                {soldPct !== null && (
                                                    <div className="mt-2 h-1.5 bg-bg-tertiary rounded-full overflow-hidden w-48">
                                                        <style dangerouslySetInnerHTML={{ __html: `.fs-sold-${fs.id.slice(0, 8)}{width:${soldPct}%}` }} />
                                                        <div className={`fs-sold-${fs.id.slice(0, 8)} h-full rounded-full ${soldPct >= 80 ? 'bg-red-500' : 'bg-yellow-500'}`} />
                                                    </div>
                                                )}
                                            </div>
                                            {fs.is_active && (
                                                <button
                                                    onClick={() => deactivateFlash.mutate(fs.id)}
                                                    className="btn btn-sm btn-ghost text-orange-500 hover:bg-orange-500/10 flex-shrink-0"
                                                >
                                                    <X className="h-4 w-4" /> Stop
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </>
            )}

            {/* ── TEMPLATES TAB ── */}
            {tab === 'templates' && (
                <div className="space-y-6">
                    <div className="rounded-2xl border border-border-color bg-gradient-to-r from-bg-primary to-bg-tertiary/70 p-4 sm:p-5">
                        <p className="text-text-secondary">Choose a pre-built design, fill in your product details, and publish instantly as a banner. Added realistic campaign skins plus a realtime template with live countdown, viewer pulse, and stock urgency.</p>
                    </div>

                    {/* Template picker grid */}
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
                        {OFFER_TEMPLATES.map((tmpl, idx) => (
                            <button
                                key={tmpl.id}
                                onClick={() => setSelectedTemplate(selectedTemplate === tmpl.id ? null : tmpl.id)}
                                className={`card p-0 overflow-hidden text-left transition-all duration-300 hover:-translate-y-1 hover:shadow-xl animate-slide-up ${STAGGER_DELAY_CLASSES[idx % STAGGER_DELAY_CLASSES.length]} ${selectedTemplate === tmpl.id
                                    ? `border ${tmpl.cardBorder} shadow-xl ring-1 ring-theme-primary/20`
                                    : 'border border-transparent'
                                    }`}
                            >
                                <div className={`${tmpl.headerBg} h-24 flex items-end justify-between p-3 relative overflow-hidden`}>
                                    <div className="absolute -top-4 -right-4 h-14 w-14 rounded-full bg-white/15 animate-float" />
                                    <span className="text-3xl animate-bounce-in">{tmpl.emoji}</span>
                                    <span className={`${tmpl.badgeBg} ${tmpl.badgeText} text-xs font-bold px-2 py-0.5 rounded-full`}>20% OFF</span>
                                </div>
                                <div className="p-3">
                                    <h3 className="font-semibold text-text-primary text-sm">{tmpl.name}</h3>
                                    <p className="text-xs text-text-secondary mt-0.5">{tmpl.desc}</p>
                                </div>
                            </button>
                        ))}
                    </div>

                    {/* Live preview + form */}
                    {selectedTemplate && (() => {
                        const tmpl = OFFER_TEMPLATES.find(t => t.id === selectedTemplate)!
                        const discPct = templateForm.discountPercent
                            || (templateForm.originalPrice && templateForm.offerPrice
                                ? Math.round((1 - +templateForm.offerPrice / +templateForm.originalPrice) * 100).toString()
                                : '')
                        const liveViewers = Math.max(3, Number(templateForm.viewersNow || 0) + viewerPulse)
                        const stockLeft = Math.max(1, Number(templateForm.stockLeft || 0))
                        const countdown = formatCountdown(templateForm.end_date, previewNowMs)
                        return (
                            <div className="grid lg:grid-cols-2 gap-6 animate-fade-in">

                                {/* Live Preview */}
                                <div>
                                    <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Live Preview</h3>
                                    <div className={`rounded-2xl overflow-hidden shadow-xl border border-border-color`}>
                                        <div className={`relative ${tmpl.headerBg}`}>
                                            {templateForm.productImage ? (
                                                <div className="relative h-44 overflow-hidden">
                                                    <img src={templateForm.productImage} alt="" className="w-full h-full object-cover" />
                                                    <div className={`absolute inset-0 ${tmpl.headerBg} opacity-50`} />
                                                </div>
                                            ) : (
                                                <div className="h-44 flex items-center justify-center">
                                                    <span className="text-7xl opacity-40">{tmpl.emoji}</span>
                                                </div>
                                            )}
                                            <span className="absolute top-3 left-3 bg-black/30 backdrop-blur-sm text-white text-xs font-bold px-2 py-0.5 rounded-full">
                                                {tmpl.emoji} {tmpl.name.toUpperCase()}
                                            </span>
                                            {discPct && (
                                                <span className={`absolute top-3 right-3 ${tmpl.badgeBg} ${tmpl.badgeText} text-xl font-black px-3 py-1 rounded-full shadow-lg`}>
                                                    {discPct}% OFF
                                                </span>
                                            )}
                                        </div>
                                        <div className={`p-5 ${tmpl.headerBg}`}>
                                            <h2 className="text-xl font-black text-white leading-tight">
                                                {templateForm.productName || 'Your Product Name'}
                                            </h2>
                                            <p className="text-sm text-white/70 mt-1">
                                                {templateForm.tagline || tmpl.desc}
                                            </p>
                                            {(templateForm.originalPrice || templateForm.offerPrice) && (
                                                <div className="flex items-center gap-3 mt-3">
                                                    {templateForm.originalPrice && (
                                                        <span className="text-sm text-white/50 line-through">₹{templateForm.originalPrice}</span>
                                                    )}
                                                    {templateForm.offerPrice && (
                                                        <span className="text-2xl font-black text-white">₹{templateForm.offerPrice}</span>
                                                    )}
                                                </div>
                                            )}
                                            <div className={`inline-block mt-4 ${tmpl.badgeBg} ${tmpl.badgeText} text-sm font-bold px-5 py-2 rounded-full animate-bounce-in`}>
                                                Shop Now →
                                            </div>

                                            {templateForm.realtimeMode && (
                                                <div className="mt-4 grid grid-cols-3 gap-2 text-[11px]">
                                                    <div className="rounded-lg bg-black/25 px-2 py-1.5 text-white/90">
                                                        <p className="uppercase tracking-wide text-white/60">Live Viewers</p>
                                                        <p className="font-bold text-cyan-200">{liveViewers}</p>
                                                    </div>
                                                    <div className="rounded-lg bg-black/25 px-2 py-1.5 text-white/90">
                                                        <p className="uppercase tracking-wide text-white/60">Stock Left</p>
                                                        <p className="font-bold text-amber-200">{stockLeft}</p>
                                                    </div>
                                                    <div className="rounded-lg bg-black/25 px-2 py-1.5 text-white/90">
                                                        <p className="uppercase tracking-wide text-white/60">Ends In</p>
                                                        <p className="font-bold text-rose-200 tabular-nums">{countdown}</p>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Customise form */}
                                <div>
                                    <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Customise Banner</h3>
                                    <div className="card space-y-3">
                                        <div>
                                            <label className="block text-xs font-medium text-text-secondary mb-1">Product Image URL</label>
                                            <input
                                                className="input w-full text-sm"
                                                placeholder="https://example.com/product.jpg"
                                                value={templateForm.productImage}
                                                onChange={e => setTemplateForm(f => ({ ...f, productImage: e.target.value }))}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-text-secondary mb-1">Product / Offer Name *</label>
                                            <input
                                                className="input w-full text-sm"
                                                placeholder="e.g. Classic White Sneakers"
                                                value={templateForm.productName}
                                                onChange={e => setTemplateForm(f => ({ ...f, productName: e.target.value }))}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs font-medium text-text-secondary mb-1">Tagline</label>
                                            <input
                                                className="input w-full text-sm"
                                                placeholder="e.g. Hurry! Only 10 left in stock"
                                                value={templateForm.tagline}
                                                onChange={e => setTemplateForm(f => ({ ...f, tagline: e.target.value }))}
                                            />
                                        </div>
                                        <div className="grid grid-cols-3 gap-2">
                                            <div>
                                                <label className="block text-xs font-medium text-text-secondary mb-1">Original ₹</label>
                                                <input
                                                    type="number" min={0}
                                                    className="input w-full text-sm"
                                                    placeholder="999"
                                                    value={templateForm.originalPrice}
                                                    onChange={e => setTemplateForm(f => ({ ...f, originalPrice: e.target.value }))}
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-medium text-text-secondary mb-1">Offer ₹ *</label>
                                                <input
                                                    type="number" min={0}
                                                    className="input w-full text-sm"
                                                    placeholder="599"
                                                    value={templateForm.offerPrice}
                                                    onChange={e => setTemplateForm(f => ({ ...f, offerPrice: e.target.value }))}
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-medium text-text-secondary mb-1">Disc %</label>
                                                <input
                                                    type="number" min={0} max={100}
                                                    className="input w-full text-sm"
                                                    placeholder="auto"
                                                    value={templateForm.discountPercent}
                                                    onChange={e => setTemplateForm(f => ({ ...f, discountPercent: e.target.value }))}
                                                />
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-2">
                                            <div>
                                                <label className="block text-xs font-medium text-text-secondary mb-1">Starting Viewers</label>
                                                <input
                                                    type="number" min={1}
                                                    className="input w-full text-sm"
                                                    placeholder="41"
                                                    value={templateForm.viewersNow}
                                                    onChange={e => setTemplateForm(f => ({ ...f, viewersNow: e.target.value }))}
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-medium text-text-secondary mb-1">Stock Left</label>
                                                <input
                                                    type="number" min={1}
                                                    className="input w-full text-sm"
                                                    placeholder="24"
                                                    value={templateForm.stockLeft}
                                                    onChange={e => setTemplateForm(f => ({ ...f, stockLeft: e.target.value }))}
                                                />
                                            </div>
                                        </div>
                                        <label className="flex items-center gap-2 text-xs text-text-secondary">
                                            <input
                                                type="checkbox"
                                                className="h-4 w-4"
                                                checked={templateForm.realtimeMode}
                                                onChange={e => setTemplateForm(f => ({ ...f, realtimeMode: e.target.checked }))}
                                            />
                                            Enable realtime strip (countdown, viewer pulse, stock urgency)
                                        </label>
                                        <div>
                                            <label className="block text-xs font-medium text-text-secondary mb-1">Link URL</label>
                                            <input
                                                className="input w-full text-sm"
                                                placeholder="/products?sale=1"
                                                value={templateForm.linkUrl}
                                                onChange={e => setTemplateForm(f => ({ ...f, linkUrl: e.target.value }))}
                                            />
                                        </div>
                                        <div className="grid grid-cols-2 gap-2">
                                            <div>
                                                <label className="block text-xs font-medium text-text-secondary mb-1">Start Date *</label>
                                                <input
                                                    title="Banner start date"
                                                    type="datetime-local"
                                                    className="input w-full text-sm"
                                                    value={templateForm.start_date}
                                                    onChange={e => setTemplateForm(f => ({ ...f, start_date: e.target.value }))}
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-medium text-text-secondary mb-1">End Date</label>
                                                <input
                                                    title="Banner end date"
                                                    type="datetime-local"
                                                    className="input w-full text-sm"
                                                    value={templateForm.end_date}
                                                    onChange={e => setTemplateForm(f => ({ ...f, end_date: e.target.value }))}
                                                />
                                            </div>
                                        </div>
                                        <div className="flex gap-2 pt-1">
                                            <button
                                                onClick={() => { setSelectedTemplate(null); setTemplateForm({ ...emptyTemplateForm }) }}
                                                className="btn btn-outline btn-sm flex-1"
                                            >
                                                Reset
                                            </button>
                                            <button
                                                onClick={() => {
                                                    if (templateForm.productImage && templateForm.productImage.length > 2048) {
                                                        toast.error('Image URL is too long. Use a shorter direct image URL.')
                                                        return
                                                    }
                                                    if (templateForm.linkUrl && templateForm.linkUrl.length > 2048) {
                                                        toast.error('Link URL is too long. Keep it below 2048 characters.')
                                                        return
                                                    }

                                                    const payload = {
                                                        title: templateForm.productName || tmpl.name,
                                                        description: templateForm.originalPrice && templateForm.offerPrice
                                                            ? `Was \u20b9${templateForm.originalPrice} \u00b7 Now \u20b9${templateForm.offerPrice}`
                                                            : tmpl.desc,
                                                        // Append realtime hints to subtitle so storefront copy stays urgency-focused.
                                                        subtitle: templateForm.realtimeMode
                                                            ? `${templateForm.tagline || (discPct ? `${discPct}% OFF` : tmpl.desc)} · ${stockLeft} left · ${liveViewers} viewing`
                                                            : templateForm.tagline || (discPct ? `${discPct}% OFF` : tmpl.desc),
                                                        image_url: templateForm.productImage.trim(),
                                                        link_url: templateForm.linkUrl.trim(),
                                                        banner_type: tmpl.bannerType,
                                                        display_order: 0,
                                                        start_date: templateForm.start_date,
                                                        end_date: templateForm.end_date,
                                                    }
                                                    createBanner.mutate(payload, {
                                                        onSuccess: () => {
                                                            setSelectedTemplate(null)
                                                            setTemplateForm({ ...emptyTemplateForm })
                                                            setTab('banners')
                                                        },
                                                    })
                                                }}
                                                disabled={!templateForm.productName || !templateForm.offerPrice || createBanner.isPending}
                                                className="btn btn-primary btn-sm flex-1"
                                            >
                                                {createBanner.isPending ? 'Publishing…' : '\uD83D\uDE80 Publish Banner'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )
                    })()}
                </div>
            )}

            {/* ── BANNER FORM MODAL ── */}
            {showBannerForm && (
                <Modal open={showBannerForm} onClose={() => setShowBannerForm(false)} maxWidthClassName="max-w-lg" panelClassName="card w-full max-h-[90vh] overflow-y-auto">
                    <ModalHeader title="Create Banner" onClose={() => setShowBannerForm(false)} className="px-0 py-0 pb-5 mb-5 border-b border-border-color rounded-none" />
                    <ModalBody className="p-0">
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Title *</label>
                                <input className="input w-full" value={bannerForm.title} onChange={e => setBannerForm(f => ({ ...f, title: e.target.value }))} placeholder="Summer Sale — Up to 50% off" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Subtitle</label>
                                <input className="input w-full" value={bannerForm.subtitle} onChange={e => setBannerForm(f => ({ ...f, subtitle: e.target.value }))} placeholder="Limited time offer" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Description</label>
                                <textarea title="Banner description" className="input w-full h-20 resize-none" placeholder="Describe this banner..." value={bannerForm.description} onChange={e => setBannerForm(f => ({ ...f, description: e.target.value }))} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Image URL</label>
                                <input className="input w-full" value={bannerForm.image_url} onChange={e => setBannerForm(f => ({ ...f, image_url: e.target.value }))} placeholder="https://..." />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Link URL</label>
                                <input className="input w-full" value={bannerForm.link_url} onChange={e => setBannerForm(f => ({ ...f, link_url: e.target.value }))} placeholder="/products?sale=1" />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-1">Type</label>
                                    <select title="Banner type" className="input w-full" value={bannerForm.banner_type} onChange={e => setBannerForm(f => ({ ...f, banner_type: e.target.value }))}>
                                        {BANNER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-1">Display Order</label>
                                    <input title="Display order" type="number" className="input w-full" placeholder="0" value={bannerForm.display_order} onChange={e => setBannerForm(f => ({ ...f, display_order: +e.target.value }))} min={0} />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-1">Start Date *</label>
                                    <input title="Start date" type="datetime-local" className="input w-full" value={bannerForm.start_date} onChange={e => setBannerForm(f => ({ ...f, start_date: e.target.value }))} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-1">End Date</label>
                                    <input title="End date" type="datetime-local" className="input w-full" value={bannerForm.end_date} onChange={e => setBannerForm(f => ({ ...f, end_date: e.target.value }))} />
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button onClick={() => setShowBannerForm(false)} className="btn btn-outline flex-1">Cancel</button>
                            <button
                                onClick={() => createBanner.mutate(bannerForm)}
                                disabled={!bannerForm.title || createBanner.isPending}
                                className="btn btn-primary flex-1"
                            >
                                {createBanner.isPending ? 'Creating…' : 'Create Banner'}
                            </button>
                        </div>
                    </ModalBody>
                </Modal>
            )}

            {/* ── FLASH SALE FORM MODAL ── */}
            {showFlashForm && (
                <Modal open={showFlashForm} onClose={() => setShowFlashForm(false)} maxWidthClassName="max-w-lg" panelClassName="card w-full max-h-[90vh] overflow-y-auto">
                    <ModalHeader title="Create Flash Sale" onClose={() => setShowFlashForm(false)} className="px-0 py-0 pb-5 mb-5 border-b border-border-color rounded-none" />
                    <ModalBody className="p-0">
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Campaign Name *</label>
                                <input className="input w-full" value={flashForm.name} onChange={e => setFlashForm(f => ({ ...f, name: e.target.value }))} placeholder="48h Mega Sale" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Product ID *</label>
                                <input className="input w-full font-mono text-sm" value={flashForm.product_id} onChange={e => setFlashForm(f => ({ ...f, product_id: e.target.value }))} placeholder="UUID of the product" />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-1">Flash Price (₹) *</label>
                                    <input type="number" className="input w-full" value={flashForm.sale_price} onChange={e => setFlashForm(f => ({ ...f, sale_price: e.target.value }))} min={0} placeholder="199" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-1">Max Qty (optional)</label>
                                    <input type="number" className="input w-full" value={flashForm.max_quantity} onChange={e => setFlashForm(f => ({ ...f, max_quantity: e.target.value }))} min={0} placeholder="100" />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Description</label>
                                <textarea title="Flash sale description" className="input w-full h-16 resize-none" placeholder="What makes this deal special?" value={flashForm.description} onChange={e => setFlashForm(f => ({ ...f, description: e.target.value }))} />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-1">Start *</label>
                                    <input title="Flash sale start time" type="datetime-local" className="input w-full" value={flashForm.start_time} onChange={e => setFlashForm(f => ({ ...f, start_time: e.target.value }))} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-1">End *</label>
                                    <input title="Flash sale end time" type="datetime-local" className="input w-full" value={flashForm.end_time} onChange={e => setFlashForm(f => ({ ...f, end_time: e.target.value }))} />
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button onClick={() => setShowFlashForm(false)} className="btn btn-outline flex-1">Cancel</button>
                            <button
                                onClick={() => createFlash.mutate(flashForm)}
                                disabled={!flashForm.name || !flashForm.product_id || !flashForm.sale_price || createFlash.isPending}
                                className="btn btn-primary flex-1"
                            >
                                {createFlash.isPending ? 'Launching…' : 'Launch Flash Sale'}
                            </button>
                        </div>
                    </ModalBody>
                </Modal>
            )}
        </div>
    )
}
