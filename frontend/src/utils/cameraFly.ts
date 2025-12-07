import * as THREE from "three";

/**
 * Smooth camera fly-to animation
 * camera   = Three.js camera
 * target   = THREE.Vector3 the camera should look at
 * distance = how far away the camera should stop
 */
export function flyToCamera(
  camera: THREE.PerspectiveCamera,
  target: THREE.Vector3,
  distance = 140
) {

  const startPos = camera.position.clone();

  const endPos = new THREE.Vector3(
    target.x + distance,
    target.y + distance * 0.35,
    target.z + distance
  );

  let progress = 0;
  const duration = 45; // frames (smooth but fast)

  const animate = () => {
    progress += 1 / duration;
    const t = Math.min(progress, 1);

    camera.position.lerpVectors(startPos, endPos, t);
    camera.lookAt(target);

    if (t < 1) requestAnimationFrame(animate);
  };

  animate();
}