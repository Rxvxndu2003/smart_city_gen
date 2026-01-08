import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Building2,
  ArrowLeft,
  ArrowRight,
  Save,
  MapPin,
  Ruler,
  Layers,
  Square,
  TrendingUp,
  Home,
  Car
} from 'lucide-react';
import { projectsApi } from '../../services/api';
import MapSelector from '../../components/MapSelector';

interface ProjectFormData {
  name: string;
  description: string;
  project_type: string;
  district: string;
  site_area: number;
  building_coverage: number;
  floor_area_ratio: number;
  num_floors: number;
  building_height: number;
  open_space_percentage: number;
  parking_spaces: number;
  owner_name: string;
  location?: {
    latitude: number;
    longitude: number;
    address: string;
    boundary?: Array<[number, number]>;
    calculated_area?: number;
  };
  // Urban Planning Parameters
  residential_percentage: number;
  commercial_percentage: number;
  industrial_percentage: number;
  green_space_percentage: number;
  road_network_type: string;
  main_road_width: number;
  secondary_road_width: number;
  pedestrian_path_width: number;
  target_population: number;
  population_density: number;
  average_household_size: number;
  climate_zone: string;
  sustainability_rating: string;
  renewable_energy_target: number;
  water_management_strategy: string;
}

const CreateProject = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const totalSteps = 5;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState<ProjectFormData>({
    name: '',
    description: '',
    project_type: 'RESIDENTIAL',
    district: 'COLOMBO',
    site_area: 0,
    building_coverage: 0,
    floor_area_ratio: 0,
    num_floors: 0,
    building_height: 0,
    open_space_percentage: 0,
    parking_spaces: 0,
    owner_name: '',
    // Urban Planning defaults
    residential_percentage: 60,
    commercial_percentage: 20,
    industrial_percentage: 10,
    green_space_percentage: 10,
    road_network_type: 'GRID',
    main_road_width: 12,
    secondary_road_width: 8,
    pedestrian_path_width: 2,
    target_population: 0,
    population_density: 0,
    average_household_size: 3.5,
    climate_zone: 'TROPICAL',
    sustainability_rating: 'BRONZE',
    renewable_energy_target: 0,
    water_management_strategy: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['site_area', 'building_coverage', 'floor_area_ratio', 'num_floors',
        'building_height', 'open_space_percentage', 'parking_spaces',
        'residential_percentage', 'commercial_percentage', 'industrial_percentage',
        'green_space_percentage', 'main_road_width', 'secondary_road_width',
        'pedestrian_path_width', 'target_population', 'population_density',
        'average_household_size', 'renewable_energy_target'].includes(name)
        ? parseFloat(value) || 0
        : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Only allow submission on the final step
    if (step !== totalSteps) {
      console.log('Form submission prevented - not on final step');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await projectsApi.create(formData);
      toast.success('Project created successfully!');
      navigate(`/projects/${response.data.id}`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create project';
      setError(errorMsg);
      toast.error(errorMsg);
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (step < totalSteps) setStep(step + 1);
  };

  const prevStep = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleLocationSelect = (data: any) => {
    setFormData(prev => ({
      ...prev,
      location: {
        latitude: data.coordinates?.lat || 0,
        longitude: data.coordinates?.lng || 0,
        address: data.address || '',
        boundary: data.boundary,
        calculated_area: data.area
      },
      // Auto-fill site area if calculated from map
      site_area: data.area || prev.site_area
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            type="button"
            onClick={() => navigate('/projects')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back to Projects
          </button>
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-primary-100 rounded-lg">
              <Building2 className="h-8 w-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Create New Project</h1>
              <p className="text-gray-600 mt-1">Fill in the project details to get started</p>
            </div>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            {[1, 2, 3, 4, 5].map((s) => (
              <div key={s} className="flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${s === step
                    ? 'bg-primary-600 text-white'
                    : s < step
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-500'
                    }`}
                >
                  {s}
                </div>
                {s < 5 && <div className={`w-20 h-1 ${s < step ? 'bg-green-500' : 'bg-gray-200'}`} />}
              </div>
            ))}
          </div>
          <div className="flex justify-center mt-2 text-sm text-gray-600 space-x-2">
            <span className={step === 1 ? 'font-semibold' : ''}>Project Info</span>
            <span>→</span>
            <span className={step === 2 ? 'font-semibold' : ''}>Location</span>
            <span>→</span>
            <span className={step === 3 ? 'font-semibold' : ''}>Site Details</span>
            <span>→</span>
            <span className={step === 4 ? 'font-semibold' : ''}>Building Params</span>
            <span>→</span>
            <span className={step === 5 ? 'font-semibold' : ''}>Urban Planning</span>
          </div>
        </div>

        {/* Form Container (using div instead of form to prevent premature submission) */}
        <div>
          <div className="card">
            {/* Step 1: Project Information */}
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="input-field"
                    placeholder="Enter project name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={4}
                    className="input-field"
                    placeholder="Describe your project"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Home className="inline h-4 w-4 mr-1" />
                      Project Type *
                    </label>
                    <select
                      name="project_type"
                      value={formData.project_type}
                      onChange={handleChange}
                      required
                      className="input-field"
                    >
                      <option value="RESIDENTIAL">Residential</option>
                      <option value="COMMERCIAL">Commercial</option>
                      <option value="MIXED_USE">Mixed Use</option>
                      <option value="INDUSTRIAL">Industrial</option>
                      <option value="INSTITUTIONAL">Institutional</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <MapPin className="inline h-4 w-4 mr-1" />
                      District *
                    </label>
                    <select
                      name="district"
                      value={formData.district}
                      onChange={handleChange}
                      required
                      className="input-field"
                    >
                      <option value="COLOMBO">Colombo</option>
                      <option value="GAMPAHA">Gampaha</option>
                      <option value="KALUTARA">Kalutara</option>
                      <option value="KANDY">Kandy</option>
                      <option value="GALLE">Galle</option>
                      <option value="MATARA">Matara</option>
                      <option value="JAFFNA">Jaffna</option>
                      <option value="BATTICALOA">Batticaloa</option>
                      <option value="ANURADHAPURA">Anuradhapura</option>
                      <option value="KURUNEGALA">Kurunegala</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Owner Name
                  </label>
                  <input
                    type="text"
                    name="owner_name"
                    value={formData.owner_name}
                    onChange={handleChange}
                    className="input-field"
                    placeholder="Enter owner name"
                  />
                </div>
              </div>
            )}

            {/* Step 2: Location Selection */}
            {step === 2 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <MapPin className="h-5 w-5 mr-2 text-primary-600" />
                    Select Project Location
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Click on the map or draw a boundary to define the project site. The site area will be calculated automatically.
                  </p>
                </div>

                <MapSelector
                  onLocationSelect={handleLocationSelect}
                />

                {formData.location && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-green-900 mb-2">Location Selected</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs text-green-800">
                      <div><span className="font-medium">Address:</span> {formData.location.address || 'N/A'}</div>
                      <div><span className="font-medium">Coordinates:</span> {formData.location.latitude.toFixed(6)}, {formData.location.longitude.toFixed(6)}</div>
                      {formData.location.calculated_area && (
                        <div><span className="font-medium">Area:</span> {formData.location.calculated_area.toFixed(2)} m²</div>
                      )}
                      {formData.location.boundary && (
                        <div><span className="font-medium">Boundary:</span> {formData.location.boundary.length} points</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Step 3: Site Details */}
            {step === 3 && (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Square className="inline h-4 w-4 mr-1" />
                    Site Area (m²) *
                  </label>
                  <input
                    type="number"
                    name="site_area"
                    value={formData.site_area || ''}
                    onChange={handleChange}
                    required
                    step="0.01"
                    min="0"
                    className="input-field"
                    placeholder="Enter site area"
                  />
                  <p className="text-xs text-gray-500 mt-1">Total land area in square meters</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Building Coverage (%) *
                    </label>
                    <input
                      type="number"
                      name="building_coverage"
                      value={formData.building_coverage || ''}
                      onChange={handleChange}
                      required
                      step="0.1"
                      min="0"
                      max="100"
                      className="input-field"
                      placeholder="0.0"
                    />
                    <p className="text-xs text-gray-500 mt-1">Percentage of site covered by building</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Open Space (%) *
                    </label>
                    <input
                      type="number"
                      name="open_space_percentage"
                      value={formData.open_space_percentage || ''}
                      onChange={handleChange}
                      required
                      step="0.1"
                      min="0"
                      max="100"
                      className="input-field"
                      placeholder="0.0"
                    />
                    <p className="text-xs text-gray-500 mt-1">Percentage of open/green space</p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Car className="inline h-4 w-4 mr-1" />
                    Parking Spaces *
                  </label>
                  <input
                    type="number"
                    name="parking_spaces"
                    value={formData.parking_spaces || ''}
                    onChange={handleChange}
                    required
                    min="0"
                    className="input-field"
                    placeholder="Enter number of parking spaces"
                  />
                </div>
              </div>
            )}

            {/* Step 4: Building Parameters */}
            {step === 4 && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Layers className="inline h-4 w-4 mr-1" />
                      Number of Floors *
                    </label>
                    <input
                      type="number"
                      name="num_floors"
                      value={formData.num_floors || ''}
                      onChange={handleChange}
                      required
                      min="1"
                      className="input-field"
                      placeholder="Enter number of floors"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Ruler className="inline h-4 w-4 mr-1" />
                      Building Height (m) *
                    </label>
                    <input
                      type="number"
                      name="building_height"
                      value={formData.building_height || ''}
                      onChange={handleChange}
                      required
                      step="0.1"
                      min="0"
                      className="input-field"
                      placeholder="Enter building height"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <TrendingUp className="inline h-4 w-4 mr-1" />
                    Floor Area Ratio (FAR) *
                  </label>
                  <input
                    type="number"
                    name="floor_area_ratio"
                    value={formData.floor_area_ratio || ''}
                    onChange={handleChange}
                    required
                    step="0.01"
                    min="0"
                    className="input-field"
                    placeholder="Enter FAR value"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Total floor area divided by site area (typical: 1.5-3.0)
                  </p>
                </div>

                {/* Summary */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
                  <h4 className="text-sm font-semibold text-blue-900 mb-3">Project Summary</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="text-blue-700">Name:</span> <span className="font-medium">{formData.name}</span></div>
                    <div><span className="text-blue-700">Type:</span> <span className="font-medium">{formData.project_type}</span></div>
                    <div><span className="text-blue-700">District:</span> <span className="font-medium">{formData.district}</span></div>
                    <div><span className="text-blue-700">Site Area:</span> <span className="font-medium">{formData.site_area} m²</span></div>
                    <div><span className="text-blue-700">Floors:</span> <span className="font-medium">{formData.num_floors}</span></div>
                    <div><span className="text-blue-700">Height:</span> <span className="font-medium">{formData.building_height} m</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 5: Urban Planning Parameters */}
            {step === 5 && (
              <div className="space-y-6">
                {/* Zoning Distribution */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Zoning Distribution</h3>
                  <p className="text-sm text-gray-600 mb-4">Define how land will be allocated across different zones (must total ≤100%)</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Residential (%) *
                      </label>
                      <input
                        type="number"
                        name="residential_percentage"
                        value={formData.residential_percentage || ''}
                        onChange={handleChange}
                        required
                        step="0.1"
                        min="0"
                        max="100"
                        className="input-field"
                        placeholder="60"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Commercial (%) *
                      </label>
                      <input
                        type="number"
                        name="commercial_percentage"
                        value={formData.commercial_percentage || ''}
                        onChange={handleChange}
                        required
                        step="0.1"
                        min="0"
                        max="100"
                        className="input-field"
                        placeholder="20"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Industrial (%) *
                      </label>
                      <input
                        type="number"
                        name="industrial_percentage"
                        value={formData.industrial_percentage || ''}
                        onChange={handleChange}
                        required
                        step="0.1"
                        min="0"
                        max="100"
                        className="input-field"
                        placeholder="10"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Green Space (%) *
                      </label>
                      <input
                        type="number"
                        name="green_space_percentage"
                        value={formData.green_space_percentage || ''}
                        onChange={handleChange}
                        required
                        step="0.1"
                        min="0"
                        max="100"
                        className="input-field"
                        placeholder="10"
                      />
                    </div>
                  </div>

                  {/* Zoning Total Validation */}
                  {(() => {
                    const total = formData.residential_percentage + formData.commercial_percentage +
                      formData.industrial_percentage + formData.green_space_percentage;
                    return total > 100 ? (
                      <p className="text-sm text-red-600 mt-2">⚠️ Total zoning exceeds 100% ({total.toFixed(1)}%)</p>
                    ) : (
                      <p className="text-sm text-green-600 mt-2">✓ Total: {total.toFixed(1)}%</p>
                    );
                  })()}
                </div>

                {/* Infrastructure */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Infrastructure</h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Road Network Type *
                      </label>
                      <select
                        name="road_network_type"
                        value={formData.road_network_type}
                        onChange={handleChange}
                        required
                        className="input-field"
                      >
                        <option value="GRID">Grid (Manhattan-style)</option>
                        <option value="RADIAL">Radial (Hub and spoke)</option>
                        <option value="ORGANIC">Organic (Natural curves)</option>
                        <option value="MIXED">Mixed (Combination)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Main Road Width (m) *
                      </label>
                      <input
                        type="number"
                        name="main_road_width"
                        value={formData.main_road_width || ''}
                        onChange={handleChange}
                        required
                        step="0.5"
                        min="6"
                        max="30"
                        className="input-field"
                        placeholder="12"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Secondary Road Width (m) *
                      </label>
                      <input
                        type="number"
                        name="secondary_road_width"
                        value={formData.secondary_road_width || ''}
                        onChange={handleChange}
                        required
                        step="0.5"
                        min="4"
                        max="20"
                        className="input-field"
                        placeholder="8"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Pedestrian Path Width (m) *
                      </label>
                      <input
                        type="number"
                        name="pedestrian_path_width"
                        value={formData.pedestrian_path_width || ''}
                        onChange={handleChange}
                        required
                        step="0.5"
                        min="1"
                        max="5"
                        className="input-field"
                        placeholder="2"
                      />
                    </div>
                  </div>
                </div>

                {/* Demographics */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Demographics</h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Target Population
                      </label>
                      <input
                        type="number"
                        name="target_population"
                        value={formData.target_population || ''}
                        onChange={handleChange}
                        min="0"
                        className="input-field"
                        placeholder="50000"
                      />
                      <p className="text-xs text-gray-500 mt-1">Expected number of residents</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Population Density (people/hectare)
                      </label>
                      <input
                        type="number"
                        name="population_density"
                        value={formData.population_density || ''}
                        onChange={handleChange}
                        step="0.1"
                        min="0"
                        className="input-field"
                        placeholder="150"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Average Household Size *
                      </label>
                      <input
                        type="number"
                        name="average_household_size"
                        value={formData.average_household_size || ''}
                        onChange={handleChange}
                        required
                        step="0.1"
                        min="1"
                        max="10"
                        className="input-field"
                        placeholder="3.5"
                      />
                    </div>
                  </div>
                </div>

                {/* Environmental */}
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Environmental & Sustainability</h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Climate Zone *
                      </label>
                      <select
                        name="climate_zone"
                        value={formData.climate_zone}
                        onChange={handleChange}
                        required
                        className="input-field"
                      >
                        <option value="TROPICAL">Tropical</option>
                        <option value="TEMPERATE">Temperate</option>
                        <option value="ARID">Arid</option>
                        <option value="MEDITERRANEAN">Mediterranean</option>
                        <option value="CONTINENTAL">Continental</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Sustainability Rating *
                      </label>
                      <select
                        name="sustainability_rating"
                        value={formData.sustainability_rating}
                        onChange={handleChange}
                        required
                        className="input-field"
                      >
                        <option value="BRONZE">Bronze (Basic)</option>
                        <option value="SILVER">Silver (Good)</option>
                        <option value="GOLD">Gold (Excellent)</option>
                        <option value="PLATINUM">Platinum (Outstanding)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Renewable Energy Target (%)
                      </label>
                      <input
                        type="number"
                        name="renewable_energy_target"
                        value={formData.renewable_energy_target || ''}
                        onChange={handleChange}
                        step="1"
                        min="0"
                        max="100"
                        className="input-field"
                        placeholder="30"
                      />
                      <p className="text-xs text-gray-500 mt-1">% of energy from renewable sources</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Water Management Strategy
                      </label>
                      <input
                        type="text"
                        name="water_management_strategy"
                        value={formData.water_management_strategy}
                        onChange={handleChange}
                        className="input-field"
                        placeholder="e.g., Rainwater harvesting, greywater recycling"
                      />
                    </div>
                  </div>
                </div>

                {/* Final Summary */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mt-6">
                  <h4 className="text-sm font-semibold text-green-900 mb-3">Complete Project Summary</h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                    <div><span className="text-green-700">Name:</span> <span className="font-medium">{formData.name}</span></div>
                    <div><span className="text-green-700">Type:</span> <span className="font-medium">{formData.project_type}</span></div>
                    <div><span className="text-green-700">District:</span> <span className="font-medium">{formData.district}</span></div>
                    <div><span className="text-green-700">Site Area:</span> <span className="font-medium">{formData.site_area} m²</span></div>
                    <div><span className="text-green-700">Floors:</span> <span className="font-medium">{formData.num_floors}</span></div>
                    <div><span className="text-green-700">Height:</span> <span className="font-medium">{formData.building_height} m</span></div>
                    <div><span className="text-green-700">Residential:</span> <span className="font-medium">{formData.residential_percentage}%</span></div>
                    <div><span className="text-green-700">Commercial:</span> <span className="font-medium">{formData.commercial_percentage}%</span></div>
                    <div><span className="text-green-700">Road Type:</span> <span className="font-medium">{formData.road_network_type}</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mt-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={prevStep}
                disabled={step === 1}
                className="px-6 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Previous
              </button>

              {step < totalSteps ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="btn-primary flex items-center"
                >
                  Next
                  <ArrowRight className="h-4 w-4 ml-2" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    handleSubmit(e as any);
                  }}
                  disabled={loading}
                  className="btn-primary flex items-center disabled:opacity-50"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {loading ? 'Creating...' : 'Create Project'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateProject;
