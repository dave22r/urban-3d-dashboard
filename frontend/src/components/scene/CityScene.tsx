import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, Environment } from "@react-three/drei";
import { Building } from "@/types/building";
import { BuildingMesh } from "./BuildingMesh";

interface CitySceneProps {
  buildings: Building[];
  filteredIds: number[];
  selectedId: number | null;
  onSelectBuilding: (building: Building) => void;
}

function Scene({ buildings, filteredIds, selectedId, onSelectBuilding }: CitySceneProps) {
  return (
    <>
      {/* Free camera */}
      <PerspectiveCamera makeDefault position={[120, 180, 240]} fov={60} />

      {/* Lights */}
      <ambientLight intensity={0.5} />
      <directionalLight
        position={[150, 220, 150]}
        intensity={1.2}
        castShadow
      />

      {/* Sky + reflections */}
      <Environment preset="city" />

      {/* Buildings */}
      {buildings.map((building) => (
        <BuildingMesh
          key={building.id}
          building={building}
          onSelect={onSelectBuilding}
          isSelected={selectedId === building.id}
          isFiltered={filteredIds.includes(building.id)}
        />
      ))}

      {/* FULL free 3D movement */}
      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={40}
        maxDistance={900}
      />
    </>
  );
}

function LoadingFallback() {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p className="text-muted-foreground">Loading 3D Scene...</p>
      </div>
    </div>
  );
}

export function CityScene({ buildings, filteredIds, selectedId, onSelectBuilding }: CitySceneProps) {
  return (
    <div className="w-full h-full relative">
      <Suspense fallback={<LoadingFallback />}>
        <Canvas shadows>
          <Scene
            buildings={buildings}
            filteredIds={filteredIds}
            selectedId={selectedId}
            onSelectBuilding={onSelectBuilding}
          />
        </Canvas>
      </Suspense>

      <div className="absolute bottom-4 left-4 glass-panel rounded-lg px-3 py-2 text-xs text-muted-foreground">
        🖱️ Rotate • Scroll to Zoom • Pan with Right Click
      </div>
    </div>
  );
}
