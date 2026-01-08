import { useState, useRef } from 'react';
import { MapContainer, TileLayer, FeatureGroup, Marker, Popup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import L from 'leaflet';
import { MapPin, Check } from 'lucide-react';

// Fix for default markers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapSelectorProps {
  onLocationSelect: (data: {
    coordinates: { lat: number; lng: number };
    boundary?: any;
    area?: number;
    address?: string;
  }) => void;
  initialCenter?: [number, number];
  initialZoom?: number;
}

const MapSelector = ({ 
  onLocationSelect, 
  initialCenter = [6.9271, 79.8612], // Colombo, Sri Lanka
  initialZoom = 13 
}: MapSelectorProps) => {
  const [center] = useState<[number, number]>(initialCenter);
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [boundary, setBoundary] = useState<any>(null);
  const [calculatedArea, setCalculatedArea] = useState<number>(0);
  const featureGroupRef = useRef<any>(null);

  const handleCreated = (e: any) => {
    const { layerType, layer } = e;
    
    if (layerType === 'polygon' || layerType === 'rectangle') {
      // Calculate area in square meters
      const area = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
      setCalculatedArea(Math.round(area));
      
      // Store boundary as GeoJSON
      const geoJSON = layer.toGeoJSON();
      setBoundary(geoJSON);
      
      // Get center of polygon
      const bounds = layer.getBounds();
      const centerPoint = bounds.getCenter();
      setSelectedLocation(centerPoint);
      
      // Call parent callback
      onLocationSelect({
        coordinates: centerPoint,
        boundary: geoJSON,
        area: Math.round(area)
      });
    } else if (layerType === 'marker') {
      const latlng = layer.getLatLng();
      setSelectedLocation(latlng);
      
      onLocationSelect({
        coordinates: latlng,
        area: calculatedArea
      });
    }
  };

  const handleDeleted = () => {
    setBoundary(null);
    setCalculatedArea(0);
    setSelectedLocation(null);
  };

  return (
    <div className="space-y-4">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <MapPin className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-medium text-blue-900 mb-1">How to select your site:</h4>
            <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
              <li>Click the polygon tool (⬟) in the top-left to draw your site boundary</li>
              <li>Click points around your site perimeter, double-click to complete</li>
              <li>Or click the marker tool (📍) to place a single point</li>
              <li>The site area will be calculated automatically</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Map Container */}
      <div className="border border-gray-300 rounded-lg overflow-hidden">
        <MapContainer
          center={center}
          zoom={initialZoom}
          style={{ height: '500px', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          <FeatureGroup ref={featureGroupRef}>
            <EditControl
              position="topleft"
              onCreated={handleCreated}
              onDeleted={handleDeleted}
              draw={{
                rectangle: {
                  shapeOptions: {
                    color: '#3b82f6',
                    weight: 2
                  }
                },
                polygon: {
                  shapeOptions: {
                    color: '#3b82f6',
                    weight: 2
                  },
                  allowIntersection: false,
                  drawError: {
                    color: '#ef4444',
                    message: '<strong>Error:</strong> Shape edges cannot cross!'
                  }
                },
                circle: false,
                circlemarker: false,
                marker: true,
                polyline: false
              }}
              edit={{
                remove: true
              }}
            />
          </FeatureGroup>

          {selectedLocation && !boundary && (
            <Marker position={[selectedLocation.lat, selectedLocation.lng]}>
              <Popup>
                Selected Location<br />
                Lat: {selectedLocation.lat.toFixed(6)}<br />
                Lng: {selectedLocation.lng.toFixed(6)}
              </Popup>
            </Marker>
          )}
        </MapContainer>
      </div>

      {/* Location Info Display */}
      {selectedLocation && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Check className="h-5 w-5 text-green-600" />
              <div>
                <p className="font-medium text-green-900">Location Selected</p>
                <p className="text-sm text-green-700">
                  Coordinates: {selectedLocation.lat.toFixed(6)}, {selectedLocation.lng.toFixed(6)}
                </p>
                {calculatedArea > 0 && (
                  <p className="text-sm text-green-700 font-semibold">
                    Site Area: {calculatedArea.toLocaleString()} m²
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search/Address Input (Future Enhancement) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Address (Optional)
        </label>
        <input
          type="text"
          className="input-field"
          placeholder="Enter address or search location (e.g., Colombo 7, Sri Lanka)"
          onChange={(e) => {
            // TODO: Implement geocoding with Google Maps API or Nominatim
            // For now, just pass the text
            if (selectedLocation) {
              onLocationSelect({
                coordinates: selectedLocation,
                boundary,
                area: calculatedArea,
                address: e.target.value
              });
            }
          }}
        />
        <p className="text-xs text-gray-500 mt-1">
          You can manually enter the address. Map search will be added in future updates.
        </p>
      </div>
    </div>
  );
};

export default MapSelector;
