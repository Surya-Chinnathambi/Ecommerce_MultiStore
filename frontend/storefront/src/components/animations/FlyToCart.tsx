import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { useState, useEffect, useCallback } from 'react'
import { MOTION_DURATION, motionTransition } from '@/lib/motion'

interface FlyToCartProps {
    trigger: boolean
    image?: string
    onAnimationComplete: () => void
}

export default function FlyToCart({ trigger, image, onAnimationComplete }: FlyToCartProps) {
    const [isAnimating, setIsAnimating] = useState(false)
    const shouldReduceMotion = useReducedMotion()

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
                initial={shouldReduceMotion ? false : { scale: 1, x: 0, y: 0, opacity: 1, rotate: 0, zIndex: 9999 }}
                animate={{
                    scale: shouldReduceMotion ? 1 : 0.15,
                    x: shouldReduceMotion ? 0 : (window.innerWidth > 768 ? window.innerWidth * 0.4 : window.innerWidth * 0.35),
                    y: shouldReduceMotion ? 0 : -window.innerHeight * 0.85,
                    opacity: shouldReduceMotion ? 1 : 0,
                    rotate: shouldReduceMotion ? 0 : 720,
                }}
                transition={motionTransition(!!shouldReduceMotion, {
                    duration: MOTION_DURATION.slow * 2,
                    x: { ease: 'linear', duration: MOTION_DURATION.slow * 2 },
                    y: { ease: 'easeIn', duration: MOTION_DURATION.slow * 2 },
                    scale: { ease: 'easeInOut', duration: MOTION_DURATION.slow * 2 },
                    opacity: { ease: 'easeIn', duration: MOTION_DURATION.slow * 2 },
                    rotate: { ease: 'linear', duration: MOTION_DURATION.slow * 2 },
                })}
                onAnimationComplete={handleAnimationComplete}
                className="fixed h-32 w-32 rounded-xl overflow-hidden shadow-2xl pointer-events-none border-4 border-theme-primary/20"
            >
                <img src={image} alt="flying product" className="w-full h-full object-cover" />
            </motion.div>
        </AnimatePresence>
    )
}
