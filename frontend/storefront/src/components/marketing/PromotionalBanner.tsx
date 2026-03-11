import { useEffect, useState } from 'react'
import { Boxes, ChevronLeft, ChevronRight, Sparkles, Timer, Users } from 'lucide-react'
import { marketingApi } from '@/lib/marketing-api'

interface Banner {
    id: string
    title: string
    subtitle?: string
    image_url?: string
    link_url?: string
    banner_type: string
    display_order: number
    end_date?: string
    click_count?: number
}

type BannerTheme = {
    shell: string
    leftGlow: string
    chip: string
    cta: string
    fallback: string
}

const THEME_BY_TYPE: Record<string, BannerTheme> = {
    hero: {
        shell: 'from-slate-900 via-slate-800 to-slate-900',
        leftGlow: 'from-cyan-500/20 via-transparent to-transparent',
        chip: 'border-white/20 bg-white/10 text-white',
        cta: 'from-emerald-500 to-cyan-500 text-slate-950',
        fallback: 'from-slate-900 via-cyan-900/40 to-slate-800',
    },
    promotional: {
        shell: 'from-indigo-900 via-violet-900 to-indigo-950',
        leftGlow: 'from-fuchsia-500/20 via-transparent to-transparent',
        chip: 'border-indigo-200/30 bg-indigo-100/10 text-indigo-100',
        cta: 'from-fuchsia-500 to-rose-500 text-white',
        fallback: 'from-indigo-900 via-fuchsia-900/40 to-violet-900',
    },
    category: {
        shell: 'from-emerald-900 via-teal-900 to-emerald-950',
        leftGlow: 'from-lime-400/20 via-transparent to-transparent',
        chip: 'border-emerald-200/30 bg-emerald-100/10 text-emerald-100',
        cta: 'from-lime-400 to-emerald-500 text-emerald-950',
        fallback: 'from-emerald-900 via-lime-700/35 to-teal-900',
    },
    flash_sale: {
        shell: 'from-rose-950 via-fuchsia-900 to-rose-950',
        leftGlow: 'from-rose-400/25 via-transparent to-transparent',
        chip: 'border-rose-200/35 bg-rose-100/10 text-rose-100',
        cta: 'from-amber-300 to-orange-400 text-rose-950',
        fallback: 'from-rose-950 via-orange-800/35 to-fuchsia-950',
    },
}

function parseUrgency(subtitle = '') {
    const match = subtitle.match(/(\d+)\s+left\s*[\u00b7\-|,]?\s*(\d+)\s+viewing/i)
    if (!match) return null
    return {
        stockLeft: Number(match[1]),
        viewers: Number(match[2]),
    }
}

function countdownTo(endDate?: string, nowMs = Date.now()) {
    if (!endDate) return null
    const end = new Date(endDate).getTime()
    if (!end || Number.isNaN(end)) return null
    const diff = end - nowMs
    if (diff <= 0) return 'Expired'
    const total = Math.floor(diff / 1000)
    const h = Math.floor(total / 3600)
    const m = Math.floor((total % 3600) / 60)
    const s = total % 60
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export default function PromotionalBanner() {
    const [banners, setBanners] = useState<Banner[]>([])
    const [currentIndex, setCurrentIndex] = useState(0)
    const [isLoading, setIsLoading] = useState(true)
    const [nowMs, setNowMs] = useState(Date.now())
    const [viewerPulse, setViewerPulse] = useState(0)
    const [failedImages, setFailedImages] = useState<Record<string, boolean>>({})
    const [slideElapsedMs, setSlideElapsedMs] = useState(0)

    useEffect(() => {
        fetchBanners()
    }, [])

    const fetchBanners = async () => {
        try {
            const response = await marketingApi.getBanners()
            // Backend returns a plain array of banners
            const list: Banner[] = Array.isArray(response.data)
                ? response.data
                : (response.data?.data ?? response.data?.banners ?? [])
            if (list.length > 0) {
                setBanners(list)
            }
        } catch (error) {
            console.error('Error fetching banners:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleBannerClick = async (banner: Banner) => {
        try {
            await marketingApi.trackBannerClick(banner.id)
            if (banner.link_url) {
                window.location.href = banner.link_url
            }
        } catch (error) {
            console.error('Error tracking banner click:', error)
        }
    }

    const nextBanner = () => {
        setCurrentIndex((prev) => (prev + 1) % banners.length)
    }

    const prevBanner = () => {
        setCurrentIndex((prev) => (prev - 1 + banners.length) % banners.length)
    }

    // Auto-advance banners every 5 seconds
    useEffect(() => {
        if (banners.length > 1) {
            const interval = setInterval(nextBanner, 5000)
            return () => clearInterval(interval)
        }
    }, [banners.length])

    useEffect(() => {
        setSlideElapsedMs(0)
    }, [currentIndex])

    useEffect(() => {
        const t = setInterval(() => {
            setNowMs(Date.now())
            setViewerPulse(Math.floor(Math.random() * 5) - 2)
            setSlideElapsedMs((v) => (v + 1000) % 5000)
        }, 1000)
        return () => clearInterval(t)
    }, [])

    if (isLoading || banners.length === 0) {
        return null
    }

    const currentBanner = banners[currentIndex]
    const theme = THEME_BY_TYPE[currentBanner.banner_type] ?? THEME_BY_TYPE.hero
    const urgency = parseUrgency(currentBanner.subtitle)
    const liveViewers = urgency ? Math.max(1, urgency.viewers + viewerPulse) : null
    const countdown = countdownTo(currentBanner.end_date, nowMs)
    const showRealtimeStrip = currentBanner.banner_type === 'flash_sale' || Boolean(urgency)
    const clickCount = currentBanner.click_count ?? 0
    const slideProgressPct = Math.min(100, Math.round((slideElapsedMs / 5000) * 100))
    const imageAvailable = Boolean(currentBanner.image_url) && !failedImages[currentBanner.id]

    return (
        <div className={`relative w-full overflow-hidden rounded-3xl border border-border-color shadow-2xl bg-gradient-to-br ${theme.shell}`}>
            <div className="pointer-events-none absolute inset-0 opacity-90 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.08),transparent_45%),radial-gradient(circle_at_85%_80%,rgba(255,255,255,0.07),transparent_35%)]" />
            <div className={`pointer-events-none absolute inset-y-0 left-0 w-[46%] bg-gradient-to-r ${theme.leftGlow}`} />

            <div
                className="relative cursor-pointer group"
                onClick={() => handleBannerClick(currentBanner)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        handleBannerClick(currentBanner)
                    }
                }}
                aria-label={`Open promotion: ${currentBanner.title}`}
            >
                <div className="grid min-h-[360px] md:min-h-[440px] grid-cols-1 lg:grid-cols-[1.15fr_0.85fr]">
                    <div className="relative z-10 p-6 md:p-10 flex flex-col justify-center">
                        <div className={`mb-4 inline-flex w-fit items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${theme.chip}`}>
                            <Sparkles className="h-3.5 w-3.5" />
                            {currentBanner.banner_type.replace('_', ' ')} campaign
                        </div>

                        <h1 className="max-w-3xl text-3xl md:text-5xl font-extrabold leading-[1.08] tracking-tight text-white drop-shadow-sm">
                            {currentBanner.title}
                        </h1>

                        {currentBanner.subtitle && (
                            <p className="mt-4 max-w-2xl text-base md:text-xl text-slate-200/95">
                                {currentBanner.subtitle}
                            </p>
                        )}

                        <div className="mt-6 flex flex-wrap items-center gap-3">
                            {currentBanner.link_url && (
                                <div className={`inline-flex px-7 py-3 bg-gradient-to-r ${theme.cta} font-semibold rounded-full transition-all duration-300 shadow-lg group-hover:shadow-glow`}>
                                    Explore Offer
                                </div>
                            )}
                            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-2 text-xs font-medium text-slate-100">
                                <Users className="h-3.5 w-3.5" />
                                {liveViewers ?? 18} viewing now
                            </div>
                        </div>

                        <div className="mt-6 grid max-w-2xl grid-cols-2 md:grid-cols-4 gap-2.5 text-[11px]">
                            <div className="rounded-xl border border-white/15 bg-black/20 px-2.5 py-2">
                                <p className="uppercase tracking-wide text-white/60">Clicks</p>
                                <p className="font-bold text-cyan-200">{clickCount}</p>
                            </div>
                            <div className="rounded-xl border border-white/15 bg-black/20 px-2.5 py-2">
                                <p className="uppercase tracking-wide text-white/60">Stock Left</p>
                                <p className="font-bold text-amber-200">{urgency?.stockLeft ?? '--'}</p>
                            </div>
                            <div className="rounded-xl border border-white/15 bg-black/20 px-2.5 py-2">
                                <p className="uppercase tracking-wide text-white/60">Ends In</p>
                                <p className="font-bold text-rose-200 tabular-nums">{countdown ?? '--:--:--'}</p>
                            </div>
                            <div className="rounded-xl border border-white/15 bg-black/20 px-2.5 py-2">
                                <p className="uppercase tracking-wide text-white/60">Priority</p>
                                <p className="font-bold text-lime-200">P{Math.max(1, 10 - currentIndex)}</p>
                            </div>
                        </div>
                    </div>

                    <div className="relative min-h-[220px] lg:min-h-full border-t lg:border-t-0 lg:border-l border-white/10">
                        {imageAvailable ? (
                            <>
                                <img
                                    src={currentBanner.image_url}
                                    alt={currentBanner.title}
                                    className="absolute inset-0 h-full w-full object-cover scale-100 group-hover:scale-105 transition-transform duration-700"
                                    loading="eager"
                                    onError={() => setFailedImages((m) => ({ ...m, [currentBanner.id]: true }))}
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/15 to-black/20" />
                                <div className="absolute right-4 top-4 rounded-full border border-white/25 bg-black/30 px-3 py-1 text-[11px] font-semibold text-white/90 backdrop-blur-sm">
                                    {currentIndex + 1}/{banners.length}
                                </div>
                            </>
                        ) : (
                            <div className={`absolute inset-0 bg-gradient-to-br ${theme.fallback}`}>
                                <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_25%,rgba(255,255,255,0.2),transparent_40%)]" />
                                <div className="absolute bottom-5 left-5 rounded-xl border border-white/20 bg-black/25 px-3 py-2 text-white/90">
                                    <p className="text-xs uppercase tracking-wide text-white/60">Creative Missing</p>
                                    <p className="text-sm font-semibold">Using premium fallback surface</p>
                                </div>
                                <div className="absolute top-5 right-5 rounded-xl border border-white/20 bg-black/30 px-3 py-2 text-white/90">
                                    <p className="text-[10px] uppercase tracking-wide text-white/60">Auto Layout</p>
                                    <p className="text-sm font-semibold">Studio Generated</p>
                                </div>
                            </div>
                        )}

                        {showRealtimeStrip && (
                            <div className="absolute inset-x-4 bottom-4 rounded-2xl border border-white/20 bg-black/35 p-3 backdrop-blur-sm text-xs text-slate-100">
                                <div className="flex items-center justify-between gap-2">
                                    <div className="flex items-center gap-1.5">
                                        <Timer className="h-3.5 w-3.5 text-rose-200" />
                                        <span className="font-semibold tabular-nums">{countdown ?? '--:--:--'}</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <Boxes className="h-3.5 w-3.5 text-amber-200" />
                                        <span>{urgency?.stockLeft ?? '--'} left</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Navigation Arrows */}
            {banners.length > 1 && (
                <>
                    <button
                        onClick={prevBanner}
                        className="absolute left-3 md:left-4 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/60 border border-white/20 backdrop-blur-sm text-white p-2 rounded-full transition-all duration-300"
                        aria-label="Previous banner"
                    >
                        <ChevronLeft className="w-6 h-6" />
                    </button>
                    <button
                        onClick={nextBanner}
                        className="absolute right-3 md:right-4 top-1/2 -translate-y-1/2 bg-black/40 hover:bg-black/60 border border-white/20 backdrop-blur-sm text-white p-2 rounded-full transition-all duration-300"
                        aria-label="Next banner"
                    >
                        <ChevronRight className="w-6 h-6" />
                    </button>
                </>
            )}

            {/* Dots Indicator */}
            {banners.length > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2">
                    {banners.map((_, index) => (
                        <button
                            key={index}
                            onClick={() => setCurrentIndex(index)}
                            className={`h-2 rounded-full transition-all duration-300 ${index === currentIndex
                                ? 'w-8 bg-white'
                                : 'w-2 bg-white/50 hover:bg-white/75'
                                }`}
                            aria-label={`Go to banner ${index + 1}`}
                        />
                    ))}
                </div>
            )}

            {/* Autoplay progress HUD */}
            {banners.length > 1 && (
                <div className="pointer-events-none absolute left-6 right-6 top-4 z-20">
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/15 backdrop-blur-sm">
                        <style dangerouslySetInnerHTML={{ __html: `.banner-progress-${currentIndex}{width:${slideProgressPct}%}` }} />
                        <div className={`banner-progress-${currentIndex} h-full rounded-full bg-gradient-to-r from-cyan-300 via-white to-cyan-300`} />
                    </div>
                </div>
            )}
        </div>
    )
}
