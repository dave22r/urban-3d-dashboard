import * as THREE from "three";
import { useMemo, useRef, useState } from "react";
import { ThreeEvent } from "@react-three/fiber";
import { Building } from "@/types/building";

interface BuildingMeshProps {
  building: Building;
  onSelect: (building: Building) => void;
  isSelected: boolean;
  isFiltered: boolean;
}

export function BuildingMesh({
  building,
  onSelect,
  isSelected,
  isFiltered,
}: BuildingMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const geometry = useMemo(() => {
    const shape = new THREE.Shape();
    const fp = building.footprint;

    if (fp.length === 0) return new THREE.BoxGeometry(1, 1, 1);

    // Footprint outline
    shape.moveTo(fp[0][0], fp[0][1]);
    for (let i = 1; i < fp.length; i++) {
      shape.lineTo(fp[i][0], fp[i][1]);
    }
    shape.closePath();

    // Extrude footprint (Three extrudes upward in +Z)
    const geom = new THREE.ExtrudeGeometry(shape, {
      depth: building.height,
      bevelEnabled: false,
    });

    // Rotate so buildings extend upwards on Y axis (not Z)
    geom.rotateX(-Math.PI / 2);

    return geom;
  }, [building]);

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    onSelect(building);
  };

  const getColor = () => {
    if (isSelected) return "#fbbf24"; // selected yellow
    if (isFiltered) return "#22d3ee"; // filtered cyan
    if (hovered) return "#60a5fa"; // hover light blue
    return "#5b7fa8"; // default
  };

  return (
    <mesh
      ref={meshRef}
      geometry={geometry}
      onClick={handleClick}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
        document.body.style.cursor = "pointer";
      }}
      onPointerOut={() => {
        setHovered(false);
        document.body.style.cursor = "auto";
      }}
    >
      <meshStandardMaterial
        color={getColor()}
        emissive={isSelected || isFiltered ? getColor() : "#000000"}
        emissiveIntensity={isSelected ? 0.3 : isFiltered ? 0.15 : 0}
        metalness={0.3}
        roughness={0.7}
      />
    </mesh>
  );
}
