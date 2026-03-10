import { useRef, useMemo, useEffect, useState } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function Particles() {
    const ref = useRef<THREE.Points>(null!)
    const { mouse } = useThree()
    const [scrollY, setScrollY] = useState(0)

    useEffect(() => {
        const handleScroll = () => setScrollY(window.scrollY)
        window.addEventListener('scroll', handleScroll, { passive: true })
        return () => window.removeEventListener('scroll', handleScroll)
    }, [])
    
    // Generate static particle positions
    const particles = useMemo(() => {
        const positions = new Float32Array(3000 * 3)
        for (let i = 0; i < 3000; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 20
            positions[i * 3 + 1] = (Math.random() - 0.5) * 20
            positions[i * 3 + 2] = (Math.random() - 0.5) * 20
        }
        return positions
    }, [])

    useFrame((state) => {
        const time = state.clock.getElapsedTime()
        ref.current.rotation.y = time * 0.03
        ref.current.rotation.x = time * 0.02
        
        // Reactive mouse following + scroll parallax
        const targetX = mouse.x * 1.5
        const targetY = mouse.y * 1.5 + (scrollY * 0.005)
        
        ref.current.position.x = THREE.MathUtils.lerp(ref.current.position.x, targetX, 0.05)
        ref.current.position.y = THREE.MathUtils.lerp(ref.current.position.y, targetY, 0.05)
    })

    return (
        <Points ref={ref} positions={particles} stride={3} frustumCulled={false}>
            <PointMaterial
                transparent
                color="#8B5CF6"
                size={0.03}
                sizeAttenuation={true}
                depthWrite={false}
                opacity={0.6}
                blending={THREE.AdditiveBlending}
            />
        </Points>
    )
}

export default function GlobalScene3D() {
    return (
        <div className="fixed inset-0 -z-50 pointer-events-none opacity-50 bg-gradient-to-b from-transparent to-bg-primary/20">
            <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
                <Particles />
                <ambientLight intensity={0.5} />
            </Canvas>
        </div>
    )
}
