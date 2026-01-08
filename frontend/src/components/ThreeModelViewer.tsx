import { useEffect, useRef, useState } from 'react';
import { Box, Loader } from 'lucide-react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

interface ThreeModelViewerProps {
  modelUrl: string;
  onError?: () => void;
}

const ThreeModelViewer = ({ modelUrl, onError }: ThreeModelViewerProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const sceneRef = useRef<{
    scene: any;
    camera: any;
    renderer: any;
    controls: any;
    animationId?: number;
  } | null>(null);

  useEffect(() => {
    if (!containerRef.current || !modelUrl) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight || 400;

    // Setup scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    
    // Add fog for depth
    scene.fog = new THREE.Fog(0x1a1a2e, 50, 200);

    // Setup camera
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(40, 30, 40);
    camera.lookAt(0, 0, 0);

    // Setup renderer
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true 
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(50, 50, 25);
    directionalLight.castShadow = true;
    directionalLight.shadow.camera.left = -50;
    directionalLight.shadow.camera.right = 50;
    directionalLight.shadow.camera.top = 50;
    directionalLight.shadow.camera.bottom = -50;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);

    const fillLight = new THREE.DirectionalLight(0x4a90e2, 0.5);
    fillLight.position.set(-30, 20, -30);
    scene.add(fillLight);

    // Add ground plane with grid
    const groundGeometry = new THREE.PlaneGeometry(200, 200);
    const groundMaterial = new THREE.MeshStandardMaterial({ 
      color: 0x2a2a3e,
      roughness: 0.8,
      metalness: 0.2
    });
    const ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = 0;
    ground.receiveShadow = true;
    scene.add(ground);

    // Add grid helper
    const gridHelper = new THREE.GridHelper(100, 50, 0x444466, 0x333344);
    gridHelper.position.y = 0.01;
    scene.add(gridHelper);

    // Setup controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = false;
    controls.minDistance = 10;
    controls.maxDistance = 200;
    controls.maxPolarAngle = Math.PI / 2;

    sceneRef.current = { scene, camera, renderer, controls };

    // Load GLTF/GLB model
    const loader = new GLTFLoader();
    const fullModelUrl = modelUrl.startsWith('http') ? modelUrl : `http://localhost:8000${modelUrl}`;
    
    loader.load(
      fullModelUrl,
      (gltf: any) => {
        const model = gltf.scene;
        
        // Enable shadows and vertex colors
        model.traverse((child: any) => {
          if (child instanceof THREE.Mesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            
            // Enable vertex colors if they exist
            if (child.geometry && child.geometry.attributes.color) {
              if (child.material) {
                // Create a new material with vertex colors enabled
                const oldMaterial = child.material;
                child.material = new THREE.MeshStandardMaterial({
                  vertexColors: true,
                  roughness: oldMaterial.roughness || 0.7,
                  metalness: oldMaterial.metalness || 0.1,
                  side: THREE.DoubleSide
                });
              }
            } else if (child.material) {
              // No vertex colors, ensure material is still visible
              child.material.needsUpdate = true;
            }
          }
        });

        // Center and scale model
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 30 / maxDim;
        
        model.scale.setScalar(scale);
        model.position.sub(center.multiplyScalar(scale));
        model.position.y = 0;

        scene.add(model);
        setLoading(false);

        // Adjust camera to fit model
        const distance = maxDim * 1.5;
        camera.position.set(distance, distance * 0.7, distance);
        camera.lookAt(0, size.y * scale / 2, 0);
        controls.target.set(0, size.y * scale / 2, 0);
        controls.update();
      },
      (progress: any) => {
        const percent = (progress.loaded / progress.total) * 100;
        console.log(`Loading 3D model: ${percent.toFixed(0)}%`);
      },
      (error: any) => {
        console.error('Error loading model:', error);
        setError(true);
        setLoading(false);
        if (onError) onError();
      }
    );

    // Animation loop
    const animate = () => {
      if (!sceneRef.current) return;
      
      sceneRef.current.animationId = requestAnimationFrame(animate);
      sceneRef.current.controls.update();
      sceneRef.current.renderer.render(sceneRef.current.scene, sceneRef.current.camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!containerRef.current || !sceneRef.current) return;
      
      const newWidth = containerRef.current.clientWidth;
      const newHeight = containerRef.current.clientHeight || 400;
      
      sceneRef.current.camera.aspect = newWidth / newHeight;
      sceneRef.current.camera.updateProjectionMatrix();
      sceneRef.current.renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      
      if (sceneRef.current) {
        if (sceneRef.current.animationId) {
          cancelAnimationFrame(sceneRef.current.animationId);
        }
        sceneRef.current.renderer.dispose();
        sceneRef.current.controls.dispose();
        if (container && renderer.domElement) {
          container.removeChild(renderer.domElement);
        }
      }
    };
  }, [modelUrl, onError]);

  if (error) {
    return (
      <div className="relative w-full h-full min-h-[400px] bg-gradient-to-br from-red-900/20 via-gray-900 to-gray-800 rounded-lg flex items-center justify-center">
        <div className="text-center text-white">
          <Box className="h-16 w-16 text-red-400 mx-auto mb-4" />
          <p className="text-lg font-semibold mb-2">Failed to Load Model</p>
          <p className="text-sm text-gray-400">The 3D model could not be loaded</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full min-h-[400px] rounded-lg overflow-hidden bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-10">
          <div className="text-center text-white">
            <Loader className="h-12 w-12 text-blue-400 animate-spin mx-auto mb-4" />
            <p className="text-lg font-semibold mb-1">Loading 3D Model...</p>
            <p className="text-sm text-blue-300">Preparing interactive viewer</p>
          </div>
        </div>
      )}
      
      <div ref={containerRef} className="w-full h-full min-h-[400px]" />
      
      {!loading && (
        <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur-sm rounded-lg p-3">
          <div className="flex items-center justify-between text-white text-sm">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <span className="text-blue-400 mr-2">🖱️</span>
                <span>Rotate: Left Click + Drag</span>
              </div>
              <div className="flex items-center">
                <span className="text-blue-400 mr-2">🔍</span>
                <span>Zoom: Scroll</span>
              </div>
              <div className="flex items-center">
                <span className="text-blue-400 mr-2">✋</span>
                <span>Pan: Right Click + Drag</span>
              </div>
            </div>
            <div className="px-3 py-1 bg-green-500/20 border border-green-500/50 rounded text-green-300 text-xs font-semibold">
              ✓ LIVE 3D
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThreeModelViewer;
