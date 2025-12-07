import { useEffect, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { Building } from "@/types/building";

interface Props {
  buildings: Building[];
  selectedId: number | null;
}

export default function AutoCameraController({ buildings, selectedId }: Props) {
  const targetPos = useRef(new THREE.Vector3(0, 100, 250)); // default camera target

  // Compute bounding box for whole city
  const computeCityCenter = () => {
    const pts: THREE.Vector3[] = [];

    buildings.forEach((b) => {
      b.footprint.forEach(([x, y]) => {
        pts.push(new THREE.Vector3(x, 0, y));
      });
    });

    if (pts.length === 0) return new THREE.Vector3(0, 0, 0);

    const box = new THREE.Box3().setFromPoints(pts);
    return box.getCenter(new THREE.Vector3());
  };

  // Compute center of selected building
  const computeBuildingCenter = (id: number) => {
    const b = buildings.find((b) => b.id === id);
    if (!b) return computeCityCenter();

    const pts = b.footprint.map(([x, y]) => new THREE.Vector3(x, b.height / 2, y));
    const box = new THREE.Box3().setFromPoints(pts);
    return box.getCenter(new THREE.Vector3());
  };

  useEffect(() => {
    if (selectedId) {
      const center = computeBuildingCenter(selectedId);
      targetPos.current = new THREE.Vector3(center.x, center.y + 80, center.z + 150);
    } else {
      const center = computeCityCenter();
      targetPos.current = new THREE.Vector3(center.x, 150, center.z + 300);
    }
  }, [selectedId, buildings]);

  // Smooth camera animation each frame
  useFrame(({ camera }) => {
    camera.position.lerp(targetPos.current, 0.05);
    camera.lookAt(0, 50, 0);
  });

  return null;
}
