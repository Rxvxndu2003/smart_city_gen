# GetFloorPlan AI - Quick Reference Card

## 🚀 Quick Start (3 Steps)

### 1. Upload Floor Plan
```bash
curl -X POST "http://localhost:8000/api/v1/getfloorplan/upload-plan" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@floor_plan.png" \
  -F "use_3d=true"
```
**Save the `plan_id` from response!**

### 2. Check Status (After 30-120 min)
```bash
curl -X POST "http://localhost:8000/api/v1/getfloorplan/check-plan-status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_ids": [YOUR_PLAN_ID]}'
```
**Wait for `status: 1` (ready)**

### 3. Get 360° Tour
```bash
curl "http://localhost:8000/api/v1/getfloorplan/get-360-tour/YOUR_PLAN_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
**Embed `widget_link` in iframe**

---

## 📋 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/getfloorplan/upload-plan` | POST | Upload floor plan |
| `/api/v1/getfloorplan/check-plan-status` | POST | Check processing status |
| `/api/v1/getfloorplan/get-360-tour/{id}` | GET | Get tour widget URL |
| `/api/v1/getfloorplan/get-rendered-images/{id}` | GET | Get SVG/JPG/3D files |
| `/api/v1/getfloorplan/get-full-data/{id}` | GET | Get all plan data |

---

## 🔑 Configuration

**File:** `/backend/.env`

```env
GETFLOORPLAN_AUTH_TOKEN=eyJ0eXAiOiJKV1QiLCJhbGc...
GETFLOORPLAN_CRM_TAG_ID=3106
GETFLOORPLAN_DOMAIN=https://backend.estate.hart-digital.com
```

**Account:** ravindukavinda08@gmail.com  
**Expires:** 2027-01-11

---

## 📁 Files Created

```
backend/app/services/getfloorplan_service.py   ← API service
backend/app/routers/getfloorplan.py           ← REST endpoints
backend/app/config.py                          ← Updated config
backend/app/main.py                            ← Registered router
backend/.env                                   ← Added credentials

GETFLOORPLAN_INTEGRATION_GUIDE.md            ← Full guide
GETFLOORPLAN_IMPLEMENTATION_COMPLETE.md      ← Summary
GETFLOORPLAN_ARCHITECTURE.md                 ← Architecture
test_getfloorplan_integration.py              ← Test script
```

---

## 🧪 Test Commands

**Run Test Script:**
```bash
cd /Users/ravindubandara/Desktop/smart_city
python test_getfloorplan_integration.py floor_plan.png
```

**Start Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**View API Docs:**
```
http://localhost:8000/api/docs
```

---

## 📊 Response Examples

### Upload Success
```json
{
  "success": true,
  "plan_id": 12345,
  "estimated_time": "30-120 minutes"
}
```

### Status (Processing)
```json
{
  "success": true,
  "message": "0/1 plans ready",
  "results": [{"status": 0, "widget_link": null}]
}
```

### Status (Ready)
```json
{
  "success": true,
  "message": "1/1 plans ready",
  "results": [{
    "status": 1,
    "svg": ["https://...floor_plan.svg"],
    "jpg": ["https://...render_1.jpg"],
    "widget_link": "https://...tour-widget",
    "unreal3d": ["https://...3d_asset.uasset"]
  }]
}
```

---

## 🎨 Integration with Interior Customization

**Workflow:**
1. Get 360° tour from GetFloorPlan
2. Extract image URL from tour
3. Use existing `/interior/detect-object` endpoint
4. Use existing `/interior/replace-furniture` endpoint

**Works seamlessly together!**

---

## ⚡ Processing Time

- **Upload:** Instant (returns plan_id immediately)
- **Processing:** 30-120 minutes (GetFloorPlan AI)
- **Status Check:** <1 second (polling)
- **Retrieval:** <1 second (when ready)

**Recommendation:** Check status every 2 minutes after upload

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| Upload fails | Check API credentials in `.env` |
| Status always 0 | Wait 30-120 minutes for processing |
| 404 on tour | Plan not ready yet or invalid ID |
| 500 error | Check backend logs: `tail -f logs/app.log` |

---

## 📖 Documentation Links

- **Full Integration Guide:** `GETFLOORPLAN_INTEGRATION_GUIDE.md`
- **Implementation Summary:** `GETFLOORPLAN_IMPLEMENTATION_COMPLETE.md`
- **Architecture Diagram:** `GETFLOORPLAN_ARCHITECTURE.md`
- **GetFloorPlan API:** https://backend.estate.hart-digital.com/api/documentation

---

## ✅ What Works Now

- ✅ Upload floor plans via API
- ✅ Monitor processing status
- ✅ Retrieve 360° tours
- ✅ Get rendered images (SVG, JPG, 3D)
- ✅ Interior customization on tour images
- ✅ JWT authentication
- ✅ Error handling
- ✅ Background processing

---

## 🎯 Next Steps (Optional)

- [ ] Create frontend upload UI
- [ ] Add progress indicator (30-120 min)
- [ ] Display tours in project viewer
- [ ] Save plan_ids to database
- [ ] Implement webhook for auto-updates
- [ ] Deploy to production

---

## 💡 Key Points

1. **Processing is asynchronous** - Takes 30-120 minutes
2. **Poll for status** - Check every 2 minutes until ready
3. **Works with existing features** - Interior customization still works!
4. **Well documented** - Complete guides available
5. **Production ready** - API credentials valid until 2027

---

## 🆘 Support

- **Backend Logs:** `/backend/logs/app.log`
- **Test Script:** `python test_getfloorplan_integration.py`
- **API Docs:** http://localhost:8000/api/docs
- **GetFloorPlan Support:** Contact via ravindukavinda08@gmail.com

---

**Built with:** FastAPI + GetFloorPlan AI + Your Existing Interior Customization  
**Status:** ✅ Fully Integrated and Ready to Use!
