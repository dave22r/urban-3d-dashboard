import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useState } from "react";
import BuildingMesh from "./BuildingMesh";

export default function CityScene({ buildings }) {
  const [selected, setSelected] = useState(null);

  return (
    <>
      <Canvas camera={{ position: [0, 200, 300], fov: 50 }}>
        <ambientLight intensity={0.9} />
        <directionalLight position={[50, 200, 50]} intensity={1} />

        {buildings.map((b) => (
          <BuildingMesh
            key={b.id}
            building={b}
            selected={selected?.id === b.id}
            onSelect={(build) => setSelected(build)}
          />
        ))}

        <OrbitControls />
      </Canvas>

      {selected && (
        <div style={{
          position: "absolute",
          top: 20,
          left: 20,
          padding: "12px 16px",
          background: "white",
          borderRadius: 6,
          boxShadow: "0 3px 10px rgba(0,0,0,0.2)",
          width: "220px",
          fontFamily: "sans-serif"
        }}>
          <h3 style={{ margin: "0 0 10px" }}>Building Info</h3>
          <p><strong>ID:</strong> {selected.id}</p>
          <p><strong>Struct ID:</strong> {selected.struct_id}</p>
          <p><strong>Height:</strong> {selected.height.toFixed(2)} m</p>
          <p><strong>Stage:</strong> {selected.stage}</p>
        </div>
      )}
    </>
  );
}
