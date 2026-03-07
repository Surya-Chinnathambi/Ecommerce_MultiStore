import { useRef, useMemo } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function Particles() {
    const ref = useRef<THREE.Points>(null!)
    const { mouse } = useThree()
    
    // Generate static particle positions
    const particles = useMemo(() => {
        const positions = new Float32Array(2000 * 3)
        for (let i = 0; i < 2000; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 15
            positions[i * 3 + 1] = (Math.random() - 0.5) * 15
            positions[i * 3 + 2] = (Math.random() - 0.5) * 15
        }
        return positions
    }, [])

    useFrame((state) => {
        const time = state.clock.getElapsedTime()
        ref.current.rotation.y = time * 0.05
        ref.current.rotation.x = time * 0.03
        
        // Reactive mouse following
        ref.current.position.x = THREE.MathUtils.lerp(ref.current.position.x, mouse.x * 0.5, 0.1)
        ref.current.position.y = THREE.MathUtils.lerp(ref.current.position.y, mouse.y * 0.5, 0.1)
    })

    return (
        <Points ref={ref} positions={particles} stride={3} frustumCulled={false}>
            <PointMaterial
                transparent
                color="#8B5CF6"
                size={0.02}
                sizeAttenuation={true}
                depthWrite={false}
                opacity={0.4}
            />
        </Points>
    )
}

export default function GlobalScene3D() {
    return (
        <div className="fixed inset-0 -z-50 pointer-events-none opacity-40">
            <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
                <Particles />
                <ambientLight intensity={0.5} />
            </Canvas>
        </div>
    )
}
