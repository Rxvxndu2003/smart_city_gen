# GetFloorPlan AI Integration Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SMART CITY PLANNING SYSTEM                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                         FRONTEND (React)                        │    │
│  │                                                                  │    │
│  │  ┌──────────────────┐         ┌──────────────────────┐         │    │
│  │  │  Floor Plan      │         │  InteriorCustomizer  │         │    │
│  │  │  Upload Component│◄────────┤  Component           │         │    │
│  │  └────────┬─────────┘         │  (Existing)          │         │    │
│  │           │                    └──────────────────────┘         │    │
│  │           │ POST /upload-plan                                   │    │
│  │           │                                                      │    │
│  └───────────┼──────────────────────────────────────────────────────┘    │
│              │                                                            │
│              ▼                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      BACKEND (FastAPI)                            │   │
│  │                                                                    │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │              GetFloorPlan Router                            │  │   │
│  │  │  /api/v1/getfloorplan/*                                     │  │   │
│  │  │                                                              │  │   │
│  │  │  • POST /upload-plan                                        │  │   │
│  │  │  • POST /check-plan-status                                  │  │   │
│  │  │  • GET /get-360-tour/{plan_id}                             │  │   │
│  │  │  • GET /get-rendered-images/{plan_id}                      │  │   │
│  │  │  • GET /get-full-data/{plan_id}                            │  │   │
│  │  └──────────────┬─────────────────────────────────────────────┘  │   │
│  │                 │                                                 │   │
│  │                 ▼                                                 │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │         GetFloorPlan Service                                │  │   │
│  │  │  (getfloorplan_service.py)                                  │  │   │
│  │  │                                                              │  │   │
│  │  │  • upload_floorplan()                                       │  │   │
│  │  │  • check_plan_status()                                      │  │   │
│  │  │  • wait_for_plan_completion()                               │  │   │
│  │  │  • get_360_tour_url()                                       │  │   │
│  │  │  • get_rendered_images()                                    │  │   │
│  │  └──────────────┬─────────────────────────────────────────────┘  │   │
│  │                 │ HTTPS API Calls                                │   │
│  └─────────────────┼────────────────────────────────────────────────┘   │
│                    │                                                     │
└────────────────────┼─────────────────────────────────────────────────────┘
                     │
                     │ Auth: Bearer Token
                     │ CRM Tag: 3106
                     │
                     ▼
     ┌───────────────────────────────────────────────────┐
     │         GetFloorPlan AI API                        │
     │  https://backend.estate.hart-digital.com          │
     │                                                    │
     │  ┌──────────────────────────────────────────┐    │
     │  │  AI Processing Pipeline                   │    │
     │  │                                            │    │
     │  │  1. Floor Plan Recognition (AI)           │    │
     │  │  2. 3D Model Generation                   │    │
     │  │  3. 360° Tour Creation                    │    │
     │  │  4. Furniture Placement (Neural Net)      │    │
     │  │  5. Multi-format Export                   │    │
     │  │                                            │    │
     │  │  Processing Time: 30-120 minutes          │    │
     │  └──────────────────────────────────────────┘    │
     │                                                    │
     │  Returns:                                          │
     │  • SVG floor plans                                │
     │  • JPG renders                                    │
     │  • 360° tour widget URL                          │
     │  • Unreal 3D assets                              │
     │  • Furniture placement data                       │
     └────────────────────────────────────────────────────┘
```

## Data Flow

### Upload Flow
```
User Uploads Floor Plan (PNG/JPG)
         │
         ├─► Frontend sends to Backend
         │
         ├─► Backend receives file
         │
         ├─► Saves to temp location
         │
         ├─► Calls GetFloorPlan API
         │     • Auth token in header
         │     • CRM tag in form data
         │     • File in multipart/form-data
         │
         ├─► GetFloorPlan returns Plan ID
         │
         └─► Backend returns Plan ID to Frontend
               (Processing starts in background)
```

### Status Check Flow
```
Frontend requests status
         │
         ├─► Backend calls GetFloorPlan API
         │     POST /api/external/v1/plans/check
         │     Body: {"planIds": [12345]}
         │
         ├─► GetFloorPlan returns status
         │     • status: 0 (processing)
         │     • status: 1 (ready)
         │
         └─► If ready, returns all assets:
               - SVG URLs
               - JPG URLs
               - Widget link (360° tour)
               - 3D assets
               - Furniture data
```

### Integration with Interior Customization
```
GetFloorPlan 360° Tour Image URL
         │
         ├─► User clicks on furniture
         │
         ├─► Frontend sends to detect-object
         │
         ├─► Backend uses SAM + GPT-4 Vision
         │     • Segment object with SAM
         │     • Identify with GPT-4o
         │
         ├─► Returns object info + mask
         │
         ├─► User selects replacement
         │
         ├─► Frontend sends to replace-furniture
         │
         ├─► Backend uses SDXL Inpainting
         │     • Applies mask
         │     • Generates new furniture
         │
         └─► Returns customized image URL
               (Can save back to project)
```

## Component Interactions

### New Components (GetFloorPlan)
```
getfloorplan_service.py
    ├─► Handles API communication
    ├─► Manages authentication
    ├─► Implements polling logic
    └─► Parses API responses

getfloorplan.py (router)
    ├─► Exposes REST endpoints
    ├─► Validates requests
    ├─► Handles file uploads
    └─► Returns formatted responses

config.py
    ├─► Loads API credentials
    ├─► Manages environment variables
    └─► Provides settings to services
```

### Existing Components (Still Work!)
```
segmentation_service.py
    ├─► SAM for object segmentation
    └─► GPT-4 Vision for identification

interior_inpainting_service.py
    ├─► SDXL for furniture replacement
    └─► Preset management

interior_customization.py (router)
    ├─► /detect-object endpoint
    └─► /replace-furniture endpoint

InteriorCustomizer.tsx
    ├─► Canvas interaction
    ├─► Object selection
    └─► Preset selection
```

## Authentication Flow

```
Frontend
    │
    ├─► User logs in
    │
    ├─► Receives JWT access_token
    │
    ├─► Stores in localStorage['access_token']
    │
    ├─► Includes in all API calls:
    │     Authorization: Bearer <access_token>
    │
    └─► Backend validates token
          │
          ├─► Extracts user info
          │
          ├─► Calls GetFloorPlan API with:
          │     Authorization: Bearer <GETFLOORPLAN_AUTH_TOKEN>
          │     (Different token for GetFloorPlan)
          │
          └─► Returns results to user
```

## Configuration Hierarchy

```
Environment Variables (.env)
    │
    ├─► GETFLOORPLAN_AUTH_TOKEN=eyJ0eXAiOiJKV1Q...
    ├─► GETFLOORPLAN_CRM_TAG_ID=3106
    ├─► GETFLOORPLAN_DOMAIN=https://backend.estate.hart-digital.com
    │
    ▼
Settings (config.py)
    │
    ├─► settings.GETFLOORPLAN_AUTH_TOKEN
    ├─► settings.GETFLOORPLAN_CRM_TAG_ID
    ├─► settings.GETFLOORPLAN_DOMAIN
    │
    ▼
Service (getfloorplan_service.py)
    │
    ├─► self.auth_token = settings.GETFLOORPLAN_AUTH_TOKEN
    ├─► self.crm_tag_id = settings.GETFLOORPLAN_CRM_TAG_ID
    ├─► self.domain = settings.GETFLOORPLAN_DOMAIN
    │
    ▼
API Calls
    │
    └─► Headers: {"Authorization": f"Bearer {self.auth_token}"}
        Form: {"crm_tag_id": str(self.crm_tag_id)}
```

## Error Handling

```
Upload Error
    ├─► Invalid file type → 400 Bad Request
    ├─► File too large → 413 Payload Too Large
    ├─► API auth failed → 401 Unauthorized
    ├─► API timeout → 504 Gateway Timeout
    └─► Unknown error → 500 Internal Server Error

Status Check Error
    ├─► Invalid plan_id → 404 Not Found
    ├─► API error → 500 Internal Server Error
    └─► Network error → 503 Service Unavailable

Tour Retrieval Error
    ├─► Plan not ready → 404 with message "still processing"
    ├─► Invalid plan_id → 404 Not Found
    └─► API error → 500 Internal Server Error
```

## Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     Technology Stack                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend:                                                   │
│  • React 18.2.0                                             │
│  • TypeScript                                               │
│  • Material-UI v7.3.6                                       │
│  • InteriorCustomizer.tsx (existing)                        │
│                                                              │
│  Backend:                                                    │
│  • FastAPI 0.104.1                                          │
│  • Python 3.11+                                             │
│  • httpx (async HTTP client)                                │
│  • SQLAlchemy (database)                                    │
│                                                              │
│  AI Services (Existing):                                     │
│  • OpenAI GPT-4o Vision                                     │
│  • Segment Anything Model (SAM)                             │
│  • Stable Diffusion XL Inpainting                           │
│  • Replicate API                                            │
│                                                              │
│  AI Services (New):                                          │
│  • GetFloorPlan AI                                          │
│    - Neural network floor plan recognition                   │
│    - 3D model generation                                    │
│    - 360° tour creation                                     │
│    - AI furniture placement                                 │
│                                                              │
│  Authentication:                                             │
│  • JWT Bearer tokens                                        │
│  • User tokens (frontend → backend)                         │
│  • API tokens (backend → GetFloorPlan)                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Considerations

```
Development:
    • localhost:8000 (backend)
    • localhost:5173 (frontend)
    • Test with small floor plans
    • Monitor backend logs

Staging:
    • Deploy to test server
    • Configure CORS origins
    • Test with production-like data
    • Validate all endpoints

Production:
    • Use HTTPS only
    • Configure rate limiting
    • Set up monitoring/alerts
    • Cache frequently requested plans
    • Implement webhook for status updates
    • Add database persistence for plan_ids
    • Scale backend horizontally if needed
```

---

This architecture seamlessly combines:
1. **GetFloorPlan AI** - Professional 3D floor plan generation
2. **Your Existing AI** - Interior customization and object editing
3. **Smart City Features** - UDA compliance, project management, blockchain

All working together in a unified system! 🎉
