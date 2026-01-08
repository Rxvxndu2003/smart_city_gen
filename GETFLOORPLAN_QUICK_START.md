# 🚀 GetFloorPlan - Quick Start Guide

## How to Use GetFloorPlan in Your Smart City App

### 1️⃣ Navigate to Floor Plan AI
- Log in to your account
- Click **"Floor Plan AI"** from dashboard

### 2️⃣ Select GetFloorPlan
```
┌─────────────────────────────────┐
│ Select AI Provider:              │
│  [ AI Render ]  [✓ 3D Model]    │  ← Click "3D Model (Full)"
└─────────────────────────────────┘
```

### 3️⃣ Upload Floor Plan
- Click upload area
- Select a 2D floor plan (JPG, PNG)
- Preview appears

### 4️⃣ Start Processing
Click **"Upload to GetFloorPlan"** (green button)

### 5️⃣ Wait for Processing
You'll see:
```
🔄 Processing Floor Plan
Processing... Status: In progress
⏱️ This typically takes 30-120 minutes
Plan ID: abc123
```
- Automatic status checks every 2 minutes
- Leave page open or return later

### 6️⃣ View Your 360° Tour
When ready:
```
✅ 360° Virtual Tour Ready
[Interactive Tour Viewer - 600px]
[📷 Open in Full Screen]
```

---

## 📋 Quick Reference

| Action | Provider | Button Text | Time |
|--------|----------|-------------|------|
| Fast AI Render | Replicate | "Transform into 3D" | ~15s |
| Full 3D Tour | GetFloorPlan | "Upload to GetFloorPlan" | 30-120 min |

---

## ✅ What You Get

### Replicate (Fast)
- 2D photorealistic renders
- Room views
- 3D model (if enabled)
- ⏱️ **15-90 seconds**

### GetFloorPlan (Full)
- Professional 3D model
- Interactive 360° virtual tour
- Walkthrough experience
- ⏱️ **30-120 minutes**

---

## 🎯 File Locations

**Frontend Code**: `/frontend/src/pages/floorplan/FloorPlanGenerator.tsx`

**New Features**:
- Lines 82-88: State variables
- Lines 950-1062: Upload and polling logic
- Lines 1488-1561: GetFloorPlan UI
- Lines 1754-1788: Tour display

**Documentation**:
- `GETFLOORPLAN_FRONTEND_COMPLETE.md` - Full implementation details
- `GETFLOORPLAN_INTEGRATION_GUIDE.md` - Backend guide
- `HOW_TO_USE_GETFLOORPLAN.md` - Original navigation guide

---

## 🔧 Developer Notes

### API Endpoints
```typescript
// Upload
POST /api/v1/getfloorplan/upload-plan
Body: FormData { file, file_name }
Returns: { plan_id, status, message }

// Check Status
POST /api/v1/getfloorplan/check-plan-status
Body: { plan_id }
Returns: { status, message, tour_360_url? }
```

### Status Flow
```
upload → processing (2min checks) → completed → display tour
                                  → failed → show error
```

### Authentication
- Requires `access_token` in localStorage
- Redirects to `/login` if missing

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't see GetFloorPlan button | Make sure provider is set to "3D Model (Full)" |
| "Please log in" error | Log out and log back in |
| Processing stuck | Wait 2 minutes for next status check |
| Tour not loading | Check browser console for iframe errors |
| Want to cancel | Refresh page (processing continues server-side) |

---

## 🎉 That's It!

You can now:
✅ Upload floor plans to GetFloorPlan  
✅ Track processing automatically  
✅ View 360° tours in-app  

**Questions?** Check `GETFLOORPLAN_FRONTEND_COMPLETE.md` for detailed docs.
