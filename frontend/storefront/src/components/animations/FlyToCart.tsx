import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect, useCallback } from 'react'

interface FlyToCartProps {
    trigger: boolean
    image?: string
    onAnimationComplete: () => void
}

export default function FlyToCart({ trigger, image, onAnimationComplete }: FlyToCartProps) {
    const [isAnimating, setIsAnimating] = useState(false)

    useEffect(() => {
        if (trigger) {
            setIsAnimating(true)
        }
    }, [trigger])

    const handleAnimationComplete = useCallback(() => {
        setIsAnimating(false)
        onAnimationComplete()
    }, [onAnimationComplete])

    if (!isAnimating || !image) return null

    return (
        <AnimatePresence>
            <motion.div
                initial={{ scale: 1, x: 0, y: 0, opacity: 1, zIndex: 9999 }}
                animate={{
                    scale: 0.2,
                    x: window.innerWidth > 768 ? window.innerWidth * 0.4 : 0, // Approximate path to header cart
                    y: -window.innerHeight * 0.8,
                    opacity: 0,
                }}
                transition={{
                    duration: 0.8,
                    ease: [0.16, 1, 0.3, 1],
                }}
                onAnimationComplete={handleAnimationComplete}
                className="fixed h-32 w-32 rounded-xl overflow-hidden shadow-2xl pointer-events-none"
            >
                <img src={image} alt="flying product" className="w-full h-full object-cover" />
            </motion.div>
        </AnimatePresence>
    )
}
