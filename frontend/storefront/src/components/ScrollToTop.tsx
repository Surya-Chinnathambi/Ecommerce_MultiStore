import { useState, useEffect } from 'react'
import { ArrowUp } from 'lucide-react'

/** Floating scroll-to-top button that appears after scrolling 400 px. */
export default function ScrollToTop() {
    const [visible, setVisible] = useState(false)

    useEffect(() => {
        const onScroll = () => setVisible(window.scrollY > 400)
        window.addEventListener('scroll', onScroll, { passive: true })
        return () => window.removeEventListener('scroll', onScroll)
    }, [])

    const scrollUp = () => window.scrollTo({ top: 0, behavior: 'smooth' })

    if (!visible) return null

    return (
        <button
            onClick={scrollUp}
            aria-label="Scroll to top"
            className={`
                fixed bottom-20 right-4 z-40
                md:bottom-6 md:right-6
                h-11 w-11 rounded-full
                bg-theme-primary text-white
                shadow-lg shadow-theme-primary/30
                flex items-center justify-center
                hover:bg-theme-primary-hover hover:-translate-y-0.5
                transition-all duration-200
                animate-scale-in
            `}
        >
            <ArrowUp className="h-5 w-5" />
        </button>
    )
}
