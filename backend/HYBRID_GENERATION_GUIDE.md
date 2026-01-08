# Hybrid City Generation - Setup Guide

## Overview

The hybrid city generation system combines:
1. **Blender** - Precise geometric 3D city generation
2. **Replicate API** - AI-powered photorealistic enhancement

## Prerequisites

### 1. Replicate API Account

1. Sign up at [replicate.com](https://replicate.com)
2. Get your API token from [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens)
3. Add to your `.env` file:
   ```bash
   REPLICATE_API_TOKEN=r8_your_token_here
   ```

### 2. Python Dependencies

Already installed:
- `replicate` - Replicate Python client
- `pillow` - Image processing

## API Endpoints

### Regular City Generation
```
POST /api/v1/city-generator/generate
```

Generates 3D city using Blender only (no AI enhancement).

### Hybrid Generation (NEW)
```
POST /api/v1/city-generator/generate-hybrid
```

Generates 3D city with optional AI enhancement.

**Request Body:**
```json
{
  "name": "Downtown Colombo",
  "place_name": "Colombo Fort, Sri Lanka",
  "enable_ai_enhancement": true,
  "enhancement_strength": 0.7,
  "num_views": 4,
  "min_building_height": 10,
  "max_building_height": 50
}
```

**Response:**
```json
{
  "status": "queued",
  "message": "Hybrid city generation task queued",
  "generation_id": "uuid-here",
  "estimated_cost": 0.0092
}
```

### Check Status
```
GET /api/v1/city-generator/status/{generation_id}
```

Returns progress and results.

## Cost Estimation

| Model | Cost per Image | 4 Views | 8 Views |
|-------|---------------|---------|---------|
| SDXL  | $0.0023       | $0.0092 | $0.0184 |
| ControlNet | $0.0020  | $0.0080 | $0.0160 |

## Workflow

### 1. Blender Generation (60% of time)
- Fetches OpenStreetMap data
- Generates 3D geometry
- Exports to GLB/GLTF

### 2. Multi-View Rendering (20% of time)
- Renders 4-8 camera angles
- Saves base renders as PNG

### 3. AI Enhancement (20% of time)
- Enhances each render with Stable Diffusion XL
- Preserves structure while adding photorealism
- Saves enhanced versions

## Models Used

### Stable Diffusion XL (SDXL)
- **Purpose**: Image-to-image enhancement
- **Model**: `stability-ai/sdxl`
- **Strength**: 0.7 (configurable)
- **Best for**: Photorealistic city views

### ControlNet (Optional)
- **Purpose**: Structure-preserving enhancement
- **Model**: `jagilley/controlnet-canny`
- **Best for**: Maintaining exact geometry

## Configuration

### Enhancement Strength
- `0.0-0.3`: Subtle enhancement, preserves original
- `0.4-0.7`: Balanced (recommended)
- `0.8-1.0`: Heavy transformation, may lose accuracy

### Number of Views
- `1-2`: Quick preview
- `4`: Standard (recommended)
- `6-8`: Comprehensive coverage

## Error Handling

The system includes automatic fallbacks:
1. If Replicate API fails → Uses base Blender render
2. If token missing → Disables AI enhancement
3. If individual view fails → Continues with others

## Testing

### Without AI Enhancement
```bash
curl -X POST http://localhost:8000/api/v1/city-generator/generate-hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test City",
    "place_name": "Colombo, Sri Lanka",
    "enable_ai_enhancement": false
  }'
```

### With AI Enhancement
```bash
curl -X POST http://localhost:8000/api/v1/city-generator/generate-hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Enhanced City",
    "place_name": "Colombo Fort, Sri Lanka",
    "enable_ai_enhancement": true,
    "enhancement_strength": 0.7,
    "num_views": 4
  }'
```

## Monitoring

Check generation status:
```bash
curl http://localhost:8000/api/v1/city-generator/status/{generation_id}
```

Response includes:
- `status`: queued, generating_geometry, rendering_views, enhancing_ai, completed, failed
- `progress`: 0.0 to 1.0
- `message`: Current step description
- `base_renders`: Array of base render paths
- `enhanced_renders`: Array of enhanced render paths

## Troubleshooting

### "Replicate API not configured"
- Check `.env` file has `REPLICATE_API_TOKEN`
- Restart backend server

### "Enhancement failed for view X"
- Check Replicate API quota
- Verify token is valid
- System will fallback to base render

### High costs
- Reduce `num_views` (4 instead of 8)
- Lower `enhancement_strength`
- Disable AI enhancement for testing

## Next Steps

See `implementation_plan.md` for:
- Phase 3: Frontend integration
- Phase 4: Production deployment
