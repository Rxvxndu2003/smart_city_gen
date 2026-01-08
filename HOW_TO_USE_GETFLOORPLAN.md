# 📖 How to Use GetFloorPlan AI in Your Smart City System

## 🎯 Overview

This guide shows you **exactly how to navigate and use** the GetFloorPlan AI integration in your Smart City Planning System. Whether you're testing via API, command line, or building a frontend UI, this guide walks you through every step.

---

## 🗺️ System Navigation Map

```
Smart City System
│
├─ 📱 FRONTEND (React App)
│   ├─ Login → http://localhost:5173/login
│   ├─ Dashboard → http://localhost:5173/dashboard
│   ├─ Projects List → http://localhost:5173/projects
│   ├─ Create Project → http://localhost:5173/projects/create
│   ├─ Project Detail → http://localhost:5173/projects/{id}
│   ├─ Floor Plan Generator → http://localhost:5173/floorplan [🆕 ADD GETFLOORPLAN HERE]
│   └─ Interior Customizer (within tours) [✅ Already working]
│
├─ 🔧 BACKEND API (FastAPI)
│   ├─ API Documentation → http://localhost:8000/api/docs
│   ├─ Health Check → http://localhost:8000/health
│   │
│   └─ 🆕 GetFloorPlan Endpoints:
│       ├─ POST /api/v1/getfloorplan/upload-plan
│       ├─ POST /api/v1/getfloorplan/check-plan-status
│       ├─ GET /api/v1/getfloorplan/get-360-tour/{plan_id}
│       ├─ GET /api/v1/getfloorplan/get-rendered-images/{plan_id}
│       └─ GET /api/v1/getfloorplan/get-full-data/{plan_id}
│
└─ 🧪 TESTING
    ├─ Test Script → python test_getfloorplan_integration.py
    ├─ Backend Logs → tail -f backend/logs/app.log
    └─ Swagger UI → http://localhost:8000/api/docs
```

---

## 🚀 Method 1: Quick Testing (Command Line)

**Best for:** Testing the integration immediately without building UI

### Step 1: Start Your Backend

```bash
# Terminal 1: Start Backend
cd /Users/ravindubandara/Desktop/smart_city/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify it's running:**
- Open: http://localhost:8000/health
- Should show: `{"status": "healthy", ...}`

### Step 2: Get Your Authentication Token

**Option A: Login via Frontend**
```bash
# Terminal 2: Start Frontend
cd /Users/ravindubandara/Desktop/smart_city/frontend
npm run dev
```

1. Open http://localhost:5173/login
2. Login with your credentials
3. Open browser DevTools (F12)
4. Go to Application → Local Storage → http://localhost:5173
5. Copy the value of `access_token`

**Option B: Login via API**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email@example.com&password=your_password"
```

Save the `access_token` from response!

### Step 3: Upload a Floor Plan

```bash
# Replace YOUR_TOKEN with your actual access_token
# Replace floor_plan.png with your actual floor plan image

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

**✅ SAVE THE `plan_id` - YOU WILL NEED IT!**

### Step 4: Wait for Processing

⏰ **Processing takes 30-120 minutes**

During this time, GetFloorPlan AI is:
1. Analyzing your floor plan with neural networks
2. Generating 3D models
3. Creating 360° virtual tour
4. Placing furniture intelligently
5. Rendering in multiple formats (SVG, JPG, 3D assets)

### Step 5: Check Status (After 30+ Minutes)

```bash
# Check every 2 minutes
curl -X POST "http://localhost:8000/api/v1/getfloorplan/check-plan-status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_ids": [12345]}'  # Replace 12345 with your plan_id
```

**When Processing (status: 0):**
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

**When Ready (status: 1):**
```json
{
  "success": true,
  "message": "1/1 plans ready",
  "results": [{
    "status": 1,
    "svg": ["https://backend.estate.hart-digital.com/.../floor_plan.svg"],
    "jpg": ["https://backend.estate.hart-digital.com/.../render_1.jpg", "...render_2.jpg"],
    "widget_link": "https://backend.estate.hart-digital.com/widget/12345",
    "neural_json": "https://.../neural_data.json",
    "furniture_json": "https://.../furniture.json",
    "unreal3d": ["https://.../3d_asset.uasset"]
  }]
}
```

### Step 6: Get Your 360° Tour

```bash
curl -X GET "http://localhost:8000/api/v1/getfloorplan/get-360-tour/12345" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "360° tour ready",
  "widget_link": "https://backend.estate.hart-digital.com/widget/12345",
  "plan_id": 12345
}
```

### Step 7: View Your Tour!

**Option A: Browser**
- Copy the `widget_link` URL
- Paste in browser
- Explore your 360° tour!

**Option B: Embed in HTML**
```html
<iframe 
  src="https://backend.estate.hart-digital.com/widget/12345"
  width="100%"
  height="600px"
  frameborder="0"
  allowfullscreen>
</iframe>
```

---

## 🧪 Method 2: Using the Test Script

**Best for:** Automated testing with detailed output

### Run the Test Script

```bash
cd /Users/ravindubandara/Desktop/smart_city

# Make sure backend is running first!
python test_getfloorplan_integration.py /path/to/your/floor_plan.png
```

**What it does:**
1. ✅ Uploads your floor plan
2. ✅ Shows plan ID
3. ✅ Checks current status
4. ✅ Attempts to get tour URL (won't work if still processing)
5. ✅ Attempts to get rendered images
6. ✅ Provides summary with curl command for later status checks

**Example Output:**
```
🚀 GetFloorPlan AI Integration Test Suite
============================================================
Floor Plan: floor_plan.png
============================================================

============================================================
TEST 1: Upload Floor Plan
============================================================
✅ Upload successful!
Plan ID: 12345
Estimated processing time: 30-120 minutes

============================================================
TEST 2: Check Plan Status
============================================================
⏳ Plan 12345 is still processing...
Status: Not ready

============================================================
TEST 3: Get 360° Tour URL
============================================================
⏳ 360° Tour not ready yet

============================================================
TEST 4: Get Rendered Images
============================================================
⏳ No images available yet

============================================================
TEST SUMMARY
============================================================
Plan ID: 12345
Status: Check again in 30-120 minutes

To check status later, run:
  curl -X POST 'http://localhost:8000/api/v1/getfloorplan/check-plan-status' \
    -H 'Authorization: Bearer YOUR_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{"plan_ids": [12345]}'

✅ Integration test complete!
```

---

## 🖥️ Method 3: Using Swagger UI (Interactive)

**Best for:** Visual exploration and testing without writing code

### Step 1: Open Swagger UI

```
http://localhost:8000/api/docs
```

### Step 2: Authorize

1. Click the **"Authorize"** button (🔒 icon, top right)
2. Enter: `Bearer YOUR_ACCESS_TOKEN`
3. Click **"Authorize"**
4. Click **"Close"**

### Step 3: Upload Floor Plan

1. Scroll to **"GetFloorPlan AI"** section
2. Click **POST `/api/v1/getfloorplan/upload-plan`**
3. Click **"Try it out"**
4. Click **"Choose File"** and select your floor plan image
5. Set `use_3d` to `true`
6. Set `language` to `en`
7. Click **"Execute"**
8. **Copy the `plan_id` from the response!**

### Step 4: Check Status

1. Click **POST `/api/v1/getfloorplan/check-plan-status`**
2. Click **"Try it out"**
3. In the request body, enter:
   ```json
   {
     "plan_ids": [12345],
     "language": "en"
   }
   ```
4. Click **"Execute"**
5. Check if `status: 1` (ready)

### Step 5: Get Tour

1. Click **GET `/api/v1/getfloorplan/get-360-tour/{plan_id}`**
2. Click **"Try it out"**
3. Enter your `plan_id` in the field
4. Click **"Execute"**
5. Copy the `widget_link` from response
6. Open in new browser tab!

---

## 📱 Method 4: Frontend Integration (For Developers)

**Best for:** Adding UI to your Smart City app

### Where to Add in Your App

Your app structure:
```
frontend/src/
├── pages/
│   ├── floorplan/
│   │   └── FloorPlanGenerator.tsx  ← ADD GETFLOORPLAN HERE
│   ├── projects/
│   │   └── ProjectDetail.tsx       ← OR HERE (in project view)
│   └── dashboard/
│       └── Dashboard.tsx            ← OR HERE (quick upload)
```

### Option A: Add to FloorPlanGenerator Page

**File:** `frontend/src/pages/floorplan/FloorPlanGenerator.tsx`

**Add GetFloorPlan Upload Section:**

```tsx
import React, { useState } from 'react';
import { Button, Box, Typography, CircularProgress, Alert } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

export default function FloorPlanGenerator() {
  const [planId, setPlanId] = useState<number | null>(null);
  const [tourUrl, setTourUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);

  // Upload floor plan to GetFloorPlan AI
  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
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
      if (data.success) {
        setPlanId(data.plan_id);
        setProcessing(true);
        // Start polling
        pollForCompletion(data.plan_id);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  // Poll for completion
  const pollForCompletion = async (planId: number) => {
    const interval = setInterval(async () => {
      try {
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
          setProcessing(false);
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Status check error:', error);
      }
    }, 120000); // Check every 2 minutes
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        🏗️ Professional 3D Floor Plan Generator
      </Typography>

      {/* Upload Section */}
      <Box my={3}>
        <input
          type="file"
          accept="image/*"
          id="floor-plan-upload"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files && handleUpload(e.target.files[0])}
        />
        <label htmlFor="floor-plan-upload">
          <Button
            variant="contained"
            component="span"
            startIcon={<CloudUploadIcon />}
            disabled={uploading || processing}
          >
            {uploading ? 'Uploading...' : 'Upload Floor Plan'}
          </Button>
        </label>
      </Box>

      {/* Status Messages */}
      {planId && (
        <Alert severity="info" sx={{ my: 2 }}>
          Plan ID: {planId} - Processing will take 30-120 minutes
        </Alert>
      )}

      {processing && (
        <Box display="flex" alignItems="center" gap={2} my={2}>
          <CircularProgress size={24} />
          <Typography>
            Generating 3D model and 360° tour... (Checking status every 2 minutes)
          </Typography>
        </Box>
      )}

      {/* 360° Tour Display */}
      {tourUrl && (
        <Box my={3}>
          <Typography variant="h6" gutterBottom>
            ✅ Your 360° Virtual Tour is Ready!
          </Typography>
          <iframe
            src={tourUrl}
            width="100%"
            height="600px"
            frameBorder="0"
            allowFullScreen
            title="360° Virtual Tour"
          />
        </Box>
      )}
    </Box>
  );
}
```

### Option B: Add to Project Detail Page

**File:** `frontend/src/pages/projects/ProjectDetail.tsx`

Add a new tab or section for "Generate 360° Tour" within your project view.

### Navigation Flow for Users:

1. **Login** → http://localhost:5173/login
2. **Dashboard** → Click "Projects" or "Floor Plans"
3. **Floor Plan Page** → Upload floor plan image
4. **Wait 30-120 min** → System polls automatically
5. **View 360° Tour** → Embedded iframe appears
6. **[Optional] Customize** → Use existing InteriorCustomizer on tour images

---

## 🎨 Method 5: Interior Customization on Tours

**After GetFloorPlan generates your 360° tour**, you can customize the interiors!

### Step 1: Get a Tour Image URL

From the 360° tour or rendered images:
```
https://backend.estate.hart-digital.com/tours/room_1.jpg
```

### Step 2: Detect Furniture

```bash
curl -X POST "http://localhost:8000/api/v1/interior/detect-object" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://backend.estate.hart-digital.com/tours/room_1.jpg",
    "click_x": 512,
    "click_y": 384
  }'
```

### Step 3: Replace Furniture

```bash
curl -X POST "http://localhost:8000/api/v1/interior/replace-furniture" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://backend.estate.hart-digital.com/tours/room_1.jpg",
    "object_info": {"object_type": "sofa"},
    "replacement_prompt": "modern leather sectional sofa, gray, minimalist",
    "preset": "modern"
  }'
```

**The InteriorCustomizer component in your frontend already handles this!**

---

## 📊 Understanding the Workflow

```
┌─────────────────────────────────────────────────────────┐
│ USER JOURNEY: From Floor Plan to Customized 360° Tour  │
└─────────────────────────────────────────────────────────┘

1. 📤 UPLOAD (Instant)
   User uploads floor plan → Backend receives → Sends to GetFloorPlan API
   ↓ Returns plan_id immediately
   
2. ⏳ PROCESSING (30-120 minutes - Happens on GetFloorPlan servers)
   • AI analyzes floor plan
   • Generates 3D model
   • Creates 360° virtual tour
   • Places furniture intelligently
   • Renders multiple formats
   
3. 🔍 POLLING (Every 2 minutes)
   Your system checks: "Is it ready yet?"
   • status: 0 → Still processing
   • status: 1 → Ready!
   
4. ✅ READY (Instant)
   • Get widget_link for 360° tour
   • Get SVG/JPG/3D assets
   • Display in your app
   
5. 🎨 CUSTOMIZE (Optional - Uses your existing AI)
   • Click on furniture in tour
   • SAM detects object
   • GPT-4 identifies it
   • SDXL replaces with custom design
   • Get personalized tour
```

---

## 🗂️ Where Files Are Stored

### Configuration
```
/backend/.env                          ← API credentials
/backend/app/config.py                 ← Settings loaded here
```

### Service Code
```
/backend/app/services/
├── getfloorplan_service.py           ← GetFloorPlan API client
├── segmentation_service.py            ← Interior customization (SAM)
└── interior_inpainting_service.py     ← Furniture replacement (SDXL)
```

### API Endpoints
```
/backend/app/routers/
├── getfloorplan.py                    ← GetFloorPlan endpoints
└── interior_customization.py          ← Interior AI endpoints
```

### Frontend Components
```
/frontend/src/
├── pages/floorplan/FloorPlanGenerator.tsx  ← Add upload UI here
└── components/tours/InteriorCustomizer.tsx ← Furniture editing (exists)
```

### Documentation
```
GETFLOORPLAN_INTEGRATION_GUIDE.md     ← Full API reference
GETFLOORPLAN_QUICK_REFERENCE.md       ← Quick commands
GETFLOORPLAN_ARCHITECTURE.md          ← System diagrams
HOW_TO_USE_GETFLOORPLAN.md           ← This file!
```

### Testing
```
test_getfloorplan_integration.py       ← Test script
```

---

## 🔧 Troubleshooting Navigation

### Problem: Can't access backend API

**Check:**
```bash
# Is backend running?
curl http://localhost:8000/health

# Should return: {"status": "healthy", ...}
```

**Fix:**
```bash
cd /Users/ravindubandara/Desktop/smart_city/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Problem: Can't login / No access token

**Get token via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email&password=your_password"
```

### Problem: Upload fails with 401 Unauthorized

**Issue:** Wrong or expired token

**Fix:**
1. Login again to get fresh token
2. Make sure using `Bearer YOUR_TOKEN` format
3. Check token is in `Authorization` header

### Problem: Status always returns 0

**Explanation:** Processing takes 30-120 minutes!

**What to do:**
- Wait at least 30 minutes before checking
- Check every 2 minutes after that
- Be patient - AI is working!

### Problem: Can't see 360° tour

**Check:**
1. Is `status: 1`? (Must be ready first)
2. Did you get `widget_link` in response?
3. Is link accessible in browser?
4. Does iframe allow cross-origin?

---

## 📞 Quick Help

### Check Backend Status
```bash
curl http://localhost:8000/health
```

### View API Documentation
```
http://localhost:8000/api/docs
```

### Check Logs
```bash
tail -f /Users/ravindubandara/Desktop/smart_city/backend/logs/app.log
```

### Test Full Workflow
```bash
python test_getfloorplan_integration.py floor_plan.png
```

---

## 🎯 Summary: How to Actually Use This

### For Quick Testing (Right Now):
1. **Start backend:** `uvicorn app.main:app --reload`
2. **Get token:** Login via frontend or API
3. **Upload:** Use curl or Swagger UI
4. **Wait:** 30-120 minutes
5. **Check:** Poll with curl or test script
6. **View:** Open widget_link in browser

### For Production Use (Later):
1. **Add UI:** Modify `FloorPlanGenerator.tsx`
2. **Upload button:** Let users upload floor plans
3. **Progress indicator:** Show "Processing... 30-120 min"
4. **Auto-poll:** Check status every 2 minutes
5. **Display tour:** Show iframe when ready
6. **Link customization:** Connect to InteriorCustomizer

### Where to Start:
- **Just testing?** → Use **Method 2** (test script)
- **Want interactive?** → Use **Method 3** (Swagger UI)
- **Building UI?** → Use **Method 4** (Frontend integration)

---

**🎉 You're Ready! Start with Method 2 (test script) to see it in action, then build your UI!**
