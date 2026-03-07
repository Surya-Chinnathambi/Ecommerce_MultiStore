import { useRef, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { MeshDistortMaterial, Float, Environment, useTexture, Decal } from '@react-three/drei'
import * as THREE from 'three'

interface ProductCanvasProps {
    imageUrl?: string
    color?: string
    shape?: 'sphere' | 'box' | 'torus'
    interactive?: boolean
}

function ProductObject({ imageUrl, color = "#8B5CF6", shape = 'sphere' }: ProductCanvasProps) {
    const meshRef = useRef<THREE.Mesh>(null!)
    const texture = imageUrl ? useTexture(imageUrl) : null

    useFrame((state) => {
        meshRef.current.rotation.y += 0.01
        meshRef.current.rotation.x = Math.sin(state.clock.getElapsedTime()) * 0.2
    })

    return (
        <Float speed={2} rotationIntensity={1} floatIntensity={1}>
            <mesh ref={meshRef}>
                {shape === 'sphere' && <sphereGeometry args={[1, 64, 64]} />}
                {shape === 'box' && <boxGeometry args={[1.5, 1.5, 1.5]} />}
                {shape === 'torus' && <torusGeometry args={[1, 0.3, 16, 100]} />}
                
                <MeshDistortMaterial 
                    color={color} 
                    speed={2} 
                    distort={0.3} 
                    roughness={0.1} 
                    metalness={1}
                >
                    {texture && <Decal 
                        position={[0, 0, 1]} 
                        rotation={[0, 0, 0]} 
                        scale={1.5} 
                        map={texture} 
                    />}
                </MeshDistortMaterial>
            </mesh>
        </Float>
    )
}

export default function ProductCanvas({ imageUrl, color, shape, interactive = true }: ProductCanvasProps) {
    return (
        <Canvas camera={{ position: [0, 0, 4], fov: 45 }} style={{ pointerEvents: interactive ? 'auto' : 'none' }}>
            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} intensity={1.5} />
            <Suspense fallback={null}>
                <ProductObject imageUrl={imageUrl} color={color} shape={shape} />
                <Environment preset="city" />
            </Suspense>
        </Canvas>
    )
}
