import * as THREE from "three";
import { useMemo } from "react";

export default function BuildingMesh({ building, onSelect, selected }) {
  const geometry = useMemo(() => {
    const shape = new THREE.Shape();
    const fp = building.footprint;

    shape.moveTo(fp[0][0], fp[0][1]);
    for (let i = 1; i < fp.length; i++) {
      shape.lineTo(fp[i][0], fp[i][1]);
    }

    return new THREE.ExtrudeGeometry(shape, {
      depth: building.height,
      bevelEnabled: false,
    });
  }, [building]);

  return (
    <mesh
      geometry={geometry}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(building);   // send clicked building back
      }}
    >
      <meshStandardMaterial
        color={selected ? "yellow" : "#7da0d0"}  // highlight if selected
      />
    </mesh>
  );
}
