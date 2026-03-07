import { Canvas } from '@react-three/fiber'
import { Float, MeshDistortMaterial } from '@react-three/drei'

interface EmptyState3DProps {
    title: string
    description: string
}

export default function EmptyState3D({ title, description }: EmptyState3DProps) {
    return (
        <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
            <div className="h-48 w-48 mb-6">
                <Canvas camera={{ position: [0, 0, 5] }}>
                    <ambientLight intensity={0.5} />
                    <pointLight position={[10, 10, 10]} />
                    <Float speed={2} rotationIntensity={2} floatIntensity={1}>
                        <mesh>
                            <torusKnotGeometry args={[1, 0.3, 128, 16]} />
                            <MeshDistortMaterial
                                color="#E5E7EB"
                                distort={0.4}
                                speed={1}
                                roughness={0.1}
                                metalness={0.5}
                                transparent
                                opacity={0.6}
                            />
                        </mesh>
                    </Float>
                </Canvas>
            </div>
            <h2 className="text-2xl font-bold text-text-primary mb-2">{title}</h2>
            <p className="text-text-tertiary max-w-sm">{description}</p>
        </div>
    )
}
