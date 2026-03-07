import { useRef, useState, ReactNode } from 'react'
import { Canvas } from '@react-three/fiber'
import { RoundedBox, MeshDistortMaterial } from '@react-three/drei'
import { motion } from 'framer-motion-3d'

interface Button3DProps {
    children: ReactNode
    onClick?: () => void
    variant?: 'primary' | 'secondary'
    className?: string
    disabled?: boolean
}

export default function Button3D({ 
    children, 
    onClick, 
    variant = 'primary', 
    className = '',
    disabled = false
}: Button3DProps) {
    const [hovered, setHovered] = useState(false)
    const [clicked, setClicked] = useState(false)

    const colors = {
        primary: "#6366f1", // Indigo
        secondary: "#334155", // Slate
    }

    const currentColor = disabled ? "#94a3b8" : colors[variant]

    return (
        <div 
            className={`relative group cursor-pointer h-14 min-w-[160px] ${className} ${disabled ? 'pointer-events-none opacity-60' : ''}`} 
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => { setHovered(false); setClicked(false) }}
            onMouseDown={() => setClicked(true)}
            onMouseUp={() => { setClicked(false); onClick?.() }}
        >
            {/* 3D Background Canvas */}
            <div className="absolute inset-0 pointer-events-none">
                <Canvas shadows camera={{ position: [0, 0, 3], fov: 40 }}>
                    <ambientLight intensity={0.7} />
                    <pointLight position={[10, 10, 10]} intensity={1} />
                    
                    <motion.group
                        animate={{
                            scale: clicked ? 0.9 : hovered ? 1.05 : 1,
                            rotateX: hovered ? 0.1 : 0,
                            rotateY: hovered ? 0.1 : 0,
                        }}
                        transition={{ type: "spring", stiffness: 400, damping: 15 }}
                    >
                        <RoundedBox args={[4, 1.2, 0.4]} radius={0.1} castShadow receiveShadow>
                            <MeshDistortMaterial 
                                color={currentColor} 
                                speed={hovered ? 4 : 0} 
                                distort={hovered ? 0.1 : 0} 
                                roughness={0.3}
                                metalness={0.7}
                            />
                        </RoundedBox>
                    </motion.group>
                </Canvas>
            </div>

            {/* Content Overlay */}
            <div className="relative z-10 h-full w-full flex items-center justify-center gap-2 px-6 text-white font-bold select-none pointer-events-none">
                {children}
            </div>
        </div>
    )
}
