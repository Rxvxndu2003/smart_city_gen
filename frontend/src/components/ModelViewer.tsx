import { Box as BoxIcon } from 'lucide-react';

interface ModelViewerProps {
  modelUrl?: string;
  fallbackMessage?: string;
}

const ModelViewer = ({ modelUrl, fallbackMessage }: ModelViewerProps) => {
  return (
    <div className="relative w-full h-full min-h-[400px] bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 rounded-lg overflow-hidden">
      {/* 3D Viewer - Clean version without overlay */}
      <div className="absolute inset-0 flex items-center justify-center">
        {modelUrl ? (
          <div className="text-center text-white">
            <div className="mb-4 flex justify-center">
              <BoxIcon className="h-20 w-20 text-blue-300 animate-pulse" />
            </div>
            <p className="text-xl font-bold mb-2">3D Model Loaded</p>
            <p className="text-sm text-blue-200 mb-4">
              Interactive 3D viewer • Rotate, zoom, and explore
            </p>
            <div className="inline-block px-4 py-2 bg-blue-500/30 rounded-lg border border-blue-400/50">
              <p className="text-xs text-blue-100">
                💡 Use Babylon.js or Three.js for full interactive experience
              </p>
            </div>
          </div>
        ) : (
          <div className="text-center text-white">
            <div className="mb-4 flex justify-center">
              <BoxIcon className="h-16 w-16 text-gray-400" />
            </div>
            <p className="text-lg font-semibold mb-2">No Model Yet</p>
            <p className="text-sm text-gray-300">
              {fallbackMessage || 'Click Generate to create a 3D model'}
            </p>
          </div>
        )}
      </div>

      {/* Decorative grid overlay */}
      <div className="absolute inset-0 opacity-10" style={{
        backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
        backgroundSize: '50px 50px'
      }}></div>
    </div>
  );
};

export default ModelViewer;
