# GetFloorPlan AI Integration Guide

## Overview

Your Smart City Planning System now integrates with **GetFloorPlan AI** - a professional service that generates high-quality 3D renders and 360° virtual tours from 2D floor plans. This replaces the previous Replicate-based approach with enterprise-grade floor plan visualization.

## What's New?

### GetFloorPlan AI Capabilities
- **Professional 3D Rendering**: Converts 2D floor plans to photorealistic 3D visualizations
- **360° Virtual Tours**: Interactive widget for immersive property exploration
- **Multiple Export Formats**: SVG, JPG, Unreal Engine 3D assets
- **AI-Powered Furniture Placement**: Intelligent room furnishing with neural network analysis
- **Multi-language Support**: Generate tours in multiple languages

### Your Existing Features (Still Work!)
- **AI Interior Customization**: Click-to-edit furniture replacement with SAM + SDXL inpainting
- **Object Detection**: GPT-4 Vision identifies furniture and objects in tours
- **Custom Design Presets**: Modern, traditional, minimalist, industrial styles
- **Real-time Editing**: Interactive canvas for furniture customization

## Architecture

```
User Upload Floor Plan
        ↓
GetFloorPlan API Upload (/api/v1/getfloorplan/upload-plan)
        ↓
Processing (30-120 min)
        ↓
Check Status (/api/v1/getfloorplan/check-plan-status)
        ↓
Get 360° Tour URL (/api/v1/getfloorplan/get-360-tour/{plan_id})
        ↓
Interior Customization (/api/v1/interior/detect-object, /replace-furniture)
        ↓
Final Customized Tour
```

## API Endpoints

### 1. Upload Floor Plan

**Endpoint:** `POST /api/v1/getfloorplan/upload-plan`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/getfloorplan/upload-plan" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@floor_plan.png" \
  -F "use_3d=true" \
  -F "language=en"
```

**Response:**
```json
{
  "success": true,
  "message": "Floor plan uploaded successfully. Processing will take 30-120 minutes.",
  "plan_id": 12345,
  "estimated_time": "30-120 minutes"
}
```

**Important:** Save the `plan_id` - you'll need it to check status and retrieve results!

### 2. Check Plan Status

**Endpoint:** `POST /api/v1/getfloorplan/check-plan-status`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/getfloorplan/check-plan-status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_ids": [12345],
    "language": "en"
  }'
```

**Response (Processing):**
```json
{
  "success": true,
  "message": "0/1 plans ready",
  "results": [{
    "status": 0,
    "svg": [],
    "jpg": [],
    "widget_link": null
  }]
}
```

**Response (Ready):**
```json
{
  "success": true,
  "message": "1/1 plans ready",
  "results": [{
    "status": 1,
    "svg": ["https://...floor_plan.svg"],
    "jpg": ["https://...floor_plan_1.jpg", "https://...floor_plan_2.jpg"],
    "widget_link": "https://...360-tour-widget",
    "neural_json": "https://...neural_data.json",
    "furniture_json": "https://...furniture.json",
    "unreal3d": ["https://...3d_asset.uasset"],
    "canvas": "https://...canvas_data"
  }]
}
```

**Status Codes:**
- `status: 0` - Plan is still processing (not ready)
- `status: 1` - Plan is ready with all assets

### 3. Get 360° Tour URL

**Endpoint:** `GET /api/v1/getfloorplan/get-360-tour/{plan_id}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/getfloorplan/get-360-tour/12345?wait=false&language=en" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Parameters:**
- `plan_id` (path): The CRM Plan ID from upload
- `wait` (query, optional): If `true`, waits up to 2 hours for completion. Default: `false`
- `language` (query, optional): Language for tour. Default: `"en"`

**Response (Ready):**
```json
{
  "success": true,
  "message": "360° tour ready",
  "widget_link": "https://backend.estate.hart-digital.com/widget/12345",
  "plan_id": 12345
}
```

**Response (Processing):**
```json
{
  "success": false,
  "message": "Plan is still processing. Please try again later.",
  "widget_link": null,
  "plan_id": 12345
}
```

### 4. Get Rendered Images

**Endpoint:** `GET /api/v1/getfloorplan/get-rendered-images/{plan_id}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/getfloorplan/get-rendered-images/12345" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Rendered images retrieved",
  "plan_id": 12345,
  "images": {
    "svg": ["https://...floor_plan.svg"],
    "jpg": ["https://...render_1.jpg", "https://...render_2.jpg"],
    "unreal3d": ["https://...3d_model.uasset"]
  }
}
```

### 5. Get Full Plan Data

**Endpoint:** `GET /api/v1/getfloorplan/get-full-data/{plan_id}`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/getfloorplan/get-full-data/12345" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:** Complete plan data with all assets (SVG, JPG, 360° tour, furniture data, neural data, etc.)

## Usage Workflow

### Recommended Approach: Poll for Status

```python
import asyncio
from app.services.getfloorplan_service import getfloorplan_service

# 1. Upload floor plan
plan_id = await getfloorplan_service.upload_floorplan(
    file_path="/path/to/floor_plan.png",
    use_3d=True
)
print(f"Plan ID: {plan_id}")

# 2. Wait a reasonable time (recommended: 30-120 minutes)
await asyncio.sleep(3600)  # Wait 1 hour

# 3. Check status
results = await getfloorplan_service.check_plan_status([plan_id])
if results[0]['status'] == 1:
    print("Plan is ready!")
    widget_link = results[0]['widgetLink']
else:
    print("Still processing, check again later")
```

### Alternative: Wait for Completion (Blocking)

```python
# This will poll every 2 minutes until ready (max 2 hours)
tour_url = await getfloorplan_service.get_360_tour_url(
    plan_id=plan_id,
    wait=True  # Blocks until ready
)
print(f"360° Tour: {tour_url}")
```

## Integration with Interior Customization

Once you have the 360° tour from GetFloorPlan, you can use your existing interior customization features:

### 1. Detect Objects in Tour

```bash
curl -X POST "http://localhost:8000/api/v1/interior/detect-object" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://backend.estate.hart-digital.com/tours/image_1.jpg",
    "click_x": 512,
    "click_y": 384
  }'
```

**Response:**
```json
{
  "success": true,
  "object_type": "sofa",
  "description": "Modern sectional sofa",
  "bounding_box": [100, 200, 400, 500],
  "image_url": "https://replicate.delivery/...mask.png"
}
```

### 2. Replace Furniture

```bash
curl -X POST "http://localhost:8000/api/v1/interior/replace-furniture" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://backend.estate.hart-digital.com/tours/image_1.jpg",
    "object_info": {
      "object_type": "sofa",
      "description": "Modern sectional sofa"
    },
    "replacement_prompt": "luxurious leather chesterfield sofa, brown, traditional style",
    "preset": "traditional"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Furniture replaced successfully",
  "output_url": "https://replicate.delivery/...customized.png",
  "original_object": "sofa",
  "replacement_prompt": "luxurious leather chesterfield sofa..."
}
```

## Configuration

### Environment Variables (.env)

```bash
# GetFloorPlan AI API Configuration
GETFLOORPLAN_AUTH_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...
GETFLOORPLAN_CRM_TAG_ID=3106
GETFLOORPLAN_DOMAIN=https://backend.estate.hart-digital.com
```

⚠️ **Important:** Your API token is already configured! It expires on **2027-01-11** (valid for ~2 years).

### Config Access

```python
from app.config import settings

# Access credentials
auth_token = settings.GETFLOORPLAN_AUTH_TOKEN
crm_tag_id = settings.GETFLOORPLAN_CRM_TAG_ID
domain = settings.GETFLOORPLAN_DOMAIN
```

## Best Practices

### 1. Polling Strategy

- **Recommended interval:** 2 minutes (API recommends 2 hours, but 2 min is safe for testing)
- **Maximum wait time:** 2 hours default (configurable)
- **Production:** Use webhooks for automatic notifications (requires setup with GetFloorPlan)

### 2. Error Handling

```python
try:
    plan_id = await getfloorplan_service.upload_floorplan(file_path)
    if plan_id:
        # Success
        print(f"Uploaded: {plan_id}")
    else:
        # Failed
        print("Upload failed")
except Exception as e:
    print(f"Error: {e}")
```

### 3. File Types

Supported formats: PNG, JPG, JPEG, GIF, BMP, TIFF

### 4. Rate Limiting

- No specific rate limits mentioned in API docs
- Use reasonable polling intervals (2 minutes)
- Avoid hammering the status endpoint

## Testing the Integration

### 1. Test Upload

```bash
cd /Users/ravindubandara/Desktop/smart_city/backend

# Upload a test floor plan
curl -X POST "http://localhost:8000/api/v1/getfloorplan/upload-plan" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_floor_plan.png" \
  -F "use_3d=true"
```

### 2. Monitor Status

```bash
# Check every 2 minutes
while true; do
  curl -X POST "http://localhost:8000/api/v1/getfloorplan/check-plan-status" \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"plan_ids": [YOUR_PLAN_ID]}'
  sleep 120
done
```

### 3. Get Results

```bash
# When status = 1, get the tour
curl -X GET "http://localhost:8000/api/v1/getfloorplan/get-360-tour/YOUR_PLAN_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Frontend Integration (Coming Soon)

### React Component Example

```tsx
import React, { useState } from 'react';

function FloorPlanUploader() {
  const [planId, setPlanId] = useState<number | null>(null);
  const [tourUrl, setTourUrl] = useState<string | null>(null);

  const uploadFloorPlan = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('use_3d', 'true');

    const response = await fetch('/api/v1/getfloorplan/upload-plan', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: formData
    });

    const data = await response.json();
    setPlanId(data.plan_id);
    
    // Start polling for status
    pollStatus(data.plan_id);
  };

  const pollStatus = async (planId: number) => {
    const interval = setInterval(async () => {
      const response = await fetch('/api/v1/getfloorplan/check-plan-status', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ plan_ids: [planId] })
      });

      const data = await response.json();
      if (data.results[0].status === 1) {
        setTourUrl(data.results[0].widget_link);
        clearInterval(interval);
      }
    }, 120000); // Poll every 2 minutes
  };

  return (
    <div>
      <input type="file" onChange={(e) => uploadFloorPlan(e.target.files![0])} />
      {planId && <p>Plan ID: {planId}</p>}
      {tourUrl && <iframe src={tourUrl} width="100%" height="600px" />}
    </div>
  );
}
```

## Troubleshooting

### Issue: Upload returns 500 error

**Solution:** Check backend logs for specific error. Ensure:
- File is valid image format
- API credentials are correct in .env
- Network can reach GetFloorPlan API domain

### Issue: Status check returns empty results

**Solution:** 
- Verify plan_id is correct
- Plan may not exist - check upload response
- Try checking with different language parameter

### Issue: 360° tour widget not loading

**Solution:**
- Check widget_link URL is valid
- Ensure iframe allows cross-origin content
- Verify plan status is 1 (ready)

## API Documentation

Full GetFloorPlan API documentation: `https://backend.estate.hart-digital.com/api/documentation`

## Support

- **GetFloorPlan API Issues:** Contact GetFloorPlan support (your account: ravindukavinda08@gmail.com)
- **Integration Issues:** Check backend logs in `/logs/app.log`
- **Interior Customization Issues:** Review existing Interior Customization docs

## Next Steps

1. ✅ GetFloorPlan service created
2. ✅ API endpoints implemented
3. ✅ Configuration added
4. 🔄 Test with real floor plan (upload and poll for results)
5. 📋 Create frontend UI component for upload + tour display
6. 🎨 Integrate with existing InteriorCustomizer component
7. 🚀 Deploy to production

---

**Status:** GetFloorPlan AI integration complete and ready for testing! Your interior customization features remain fully functional and will work seamlessly with GetFloorPlan-generated 360° tours.
