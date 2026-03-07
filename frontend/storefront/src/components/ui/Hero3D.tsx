import { useRef, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Environment, Float, Sphere, MeshDistortMaterial, ContactShadows } from '@react-three/drei'
import * as THREE from 'three'

function AbstractShapes() {
    const sphereRef = useRef<THREE.Mesh>(null!)
    const torusRef = useRef<THREE.Mesh>(null!)
    const boxRef = useRef<THREE.Mesh>(null!)

    useFrame((state) => {
        const time = state.clock.getElapsedTime()
        if (torusRef.current) {
            torusRef.current.rotation.x = time * 0.2
            torusRef.current.rotation.y = time * 0.3
        }
        if (boxRef.current) {
            boxRef.current.rotation.x = time * 0.4
            boxRef.current.rotation.y = time * 0.1
        }
    })

    return (
        <group>
            {/* Central Distorted Sphere */}
            <Float speed={2} rotationIntensity={1} floatIntensity={2}>
                <Sphere ref={sphereRef} args={[1.5, 64, 64]} position={[0, 0, 0]}>
                    <MeshDistortMaterial
                        color="#8B5CF6"
                        attach="material"
                        distort={0.4}
                        speed={2}
                        roughness={0.2}
                        metalness={0.8}
                    />
                </Sphere>
            </Float>

            {/* Floating Torus */}
            <Float speed={1.5} rotationIntensity={2} floatIntensity={1.5}>
                <mesh ref={torusRef} position={[2.5, 1, -1]}>
                    <torusGeometry args={[0.8, 0.2, 16, 100]} />
                    <meshStandardMaterial color="#FF6B6B" roughness={0.1} metalness={0.5} />
                </mesh>
            </Float>

            {/* Floating Box */}
            <Float speed={2.5} rotationIntensity={1.5} floatIntensity={2}>
                <mesh ref={boxRef} position={[-2, -1, 1]} rotation={[Math.PI / 4, Math.PI / 4, 0]}>
                    <boxGeometry args={[1, 1, 1]} />
                    <meshStandardMaterial color="#4ECDC4" roughness={0.3} metalness={0.7} />
                </mesh>
            </Float>

            {/* Small decorative spheres */}
            <Float speed={3} rotationIntensity={1} floatIntensity={1}>
                <Sphere args={[0.3, 32, 32]} position={[1.5, -1.5, 2]}>
                    <meshStandardMaterial color="#FBBF24" roughness={0.2} metalness={0.8} />
                </Sphere>
            </Float>
            <Float speed={2} rotationIntensity={1.5} floatIntensity={1.5}>
                <Sphere args={[0.2, 32, 32]} position={[-2.5, 1.5, -2]}>
                    <meshStandardMaterial color="#3B82F6" roughness={0.1} metalness={0.9} />
                </Sphere>
            </Float>
        </group>
    )
}

export default function Hero3D() {
    return (
        <div className="w-full h-full min-h-[400px]">
            <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 10, 5]} intensity={1} />
                <directionalLight position={[-10, -10, -5]} intensity={0.5} color="#8B5CF6" />
                
                <Suspense fallback={null}>
                    <AbstractShapes />
                    
                    <ContactShadows
                        position={[0, -2.5, 0]}
                        opacity={0.4}
                        scale={20}
                        blur={2}
                        far={4.5}
                    />
                    
                    <Environment preset="city" />
                </Suspense>
            </Canvas>
        </div>
    )
}
