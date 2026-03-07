import { useRef, useState, ReactNode } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { RoundedBox, MeshDistortMaterial } from '@react-three/drei'
import * as THREE from 'three'

interface Button3DProps {
    children: ReactNode
    onClick?: () => void
    variant?: 'primary' | 'secondary'
    className?: string
    disabled?: boolean
}

function ButtonMesh({ hovered, clicked, color }: { hovered: boolean; clicked: boolean; color: string }) {
    const groupRef = useRef<THREE.Group>(null!)

    useFrame(() => {
        if (!groupRef.current) return
        const targetScale = clicked ? 0.88 : hovered ? 1.06 : 1
        const targetRotY = hovered ? 0.1 : 0
        groupRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.15)
        groupRef.current.rotation.y += (targetRotY - groupRef.current.rotation.y) * 0.15
        groupRef.current.rotation.x += ((hovered ? 0.08 : 0) - groupRef.current.rotation.x) * 0.15
    })

    return (
        <group ref={groupRef}>
            <RoundedBox args={[4, 1.2, 0.4]} radius={0.1} castShadow receiveShadow>
                <MeshDistortMaterial
                    color={color}
                    speed={hovered ? 4 : 0}
                    distort={hovered ? 0.1 : 0}
                    roughness={0.3}
                    metalness={0.7}
                />
            </RoundedBox>
        </group>
    )
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
        primary: '#6366f1',
        secondary: '#334155',
    }

    const currentColor = disabled ? '#94a3b8' : colors[variant]

    return (
        <div
            className={`relative cursor-pointer h-14 min-w-[160px] ${className} ${disabled ? 'pointer-events-none opacity-60' : ''}`}
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
                    <ButtonMesh hovered={hovered} clicked={clicked} color={currentColor} />
                </Canvas>
            </div>

            {/* Content Overlay */}
            <div className="relative z-10 h-full w-full flex items-center justify-center gap-2 px-6 text-white font-bold select-none pointer-events-none">
                {children}
            </div>
        </div>
    )
}
