import { Canvas } from '@react-three/fiber'
import { Icosahedron, MeshDistortMaterial, Float } from '@react-three/drei'

export default function Loader3D() {
    return (
        <div className="flex flex-col items-center justify-center gap-4 py-20">
            <div className="h-24 w-24">
                <Canvas camera={{ position: [0, 0, 3] }}>
                    <ambientLight intensity={0.5} />
                    <pointLight position={[10, 10, 10]} />
                    <Float speed={5} rotationIntensity={2} floatIntensity={2}>
                        <Icosahedron args={[1, 15]}>
                            <MeshDistortMaterial
                                color="#8B5CF6"
                                speed={4}
                                distort={0.5}
                                roughness={0.1}
                                metalness={0.9}
                            />
                        </Icosahedron>
                    </Float>
                </Canvas>
            </div>
            <p className="text-theme-primary font-bold animate-pulse">Loading Immersive Experience...</p>
        </div>
    )
}
