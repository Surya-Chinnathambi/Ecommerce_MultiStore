import { useRef, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Environment, useTexture, Decal, OrbitControls, useGLTF } from '@react-three/drei'
import * as THREE from 'three'

interface ProductCanvasProps {
    imageUrl?: string
    modelUrl?: string
    color?: string
    shape?: 'sphere' | 'box' | 'torus'
    interactive?: boolean
}

function ProductModel({ modelUrl }: { modelUrl: string }) {
    const { scene } = useGLTF(modelUrl)
    return <primitive object={scene} scale={[1.5, 1.5, 1.5]} position={[0, -0.5, 0]} />
}

function ProductObject({ imageUrl, color = "#8B5CF6", shape = 'sphere' }: Omit<ProductCanvasProps, 'interactive' | 'modelUrl'>) {
    const meshRef = useRef<THREE.Mesh>(null!)
    const texture = imageUrl ? useTexture(imageUrl) : null

    useFrame((state) => {
        meshRef.current.rotation.y += 0.005
        meshRef.current.rotation.x = Math.sin(state.clock.getElapsedTime()) * 0.1
    })

    return (
        <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
            <mesh ref={meshRef} castShadow receiveShadow>
                {shape === 'sphere' && <sphereGeometry args={[1, 64, 64]} />}
                {shape === 'box' && <boxGeometry args={[1.4, 1.4, 1.4]} />}
                {shape === 'torus' && <torusGeometry args={[1, 0.35, 32, 100]} />}
                
                <meshPhysicalMaterial 
                    color={color}
                    roughness={0.1}
                    metalness={0.8}
                    clearcoat={1.0}
                    clearcoatRoughness={0.1}
                    envMapIntensity={2.0}
                    transparent={true}
                    opacity={0.9}
                >
                    {texture && <Decal 
                        position={[0, 0, 1]} 
                        rotation={[0, 0, 0]} 
                        scale={1.5} 
                        map={texture} 
                    />}
                </meshPhysicalMaterial>
            </mesh>
        </Float>
    )
}

export default function ProductCanvas({ imageUrl, modelUrl, color, shape, interactive = true }: ProductCanvasProps) {
    return (
        <Canvas camera={{ position: [0, 0, 4.5], fov: 45 }} style={{ pointerEvents: interactive ? 'auto' : 'none' }}>
            <ambientLight intensity={0.5} />
            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color={color || "#8B5CF6"} />
            <Suspense fallback={null}>
                {modelUrl ? (
                    <ProductModel modelUrl={modelUrl} />
                ) : (
                    <ProductObject imageUrl={imageUrl} color={color} shape={shape} />
                )}
                <Environment preset="city" />
            </Suspense>
            {interactive && (
                <OrbitControls 
                    enableZoom={false} 
                    enablePan={false} 
                    autoRotate 
                    autoRotateSpeed={2}
                    minPolarAngle={Math.PI / 3}
                    maxPolarAngle={Math.PI / 1.5}
                />
            )}
        </Canvas>
    )
}
