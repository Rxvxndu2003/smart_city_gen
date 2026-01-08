"""
Test script for GetFloorPlan API integration

Run this to test the complete workflow:
1. Upload a floor plan
2. Monitor processing status
3. Retrieve 360° tour and rendered images

Usage:
    python test_getfloorplan_integration.py /path/to/floor_plan.png
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.getfloorplan_service import getfloorplan_service


async def test_upload(file_path: str):
    """Test floor plan upload"""
    print("=" * 60)
    print("TEST 1: Upload Floor Plan")
    print("=" * 60)
    
    plan_id = await getfloorplan_service.upload_floorplan(
        file_path=file_path,
        use_3d=True
    )
    
    if plan_id:
        print(f"✅ Upload successful!")
        print(f"Plan ID: {plan_id}")
        print(f"Estimated processing time: 30-120 minutes")
        return plan_id
    else:
        print("❌ Upload failed!")
        return None


async def test_status_check(plan_id: int):
    """Test status checking"""
    print("\n" + "=" * 60)
    print("TEST 2: Check Plan Status")
    print("=" * 60)
    
    results = await getfloorplan_service.check_plan_status([plan_id])
    
    if results:
        result = results[0]
        status = result.get('status', 0)
        
        if status == 0:
            print(f"⏳ Plan {plan_id} is still processing...")
            print("Status: Not ready")
        elif status == 1:
            print(f"✅ Plan {plan_id} is ready!")
            print("Status: Ready")
            print(f"\nGenerated Assets:")
            print(f"  - SVG files: {len(result.get('svg', []))}")
            print(f"  - JPG files: {len(result.get('jpg', []))}")
            print(f"  - 360° Tour: {result.get('widgetLink', 'N/A')}")
            print(f"  - 3D Assets: {len(result.get('unreal3d', []))}")
        else:
            print(f"⚠️  Unknown status: {status}")
        
        return result
    else:
        print("❌ Status check failed!")
        return None


async def test_get_tour_url(plan_id: int):
    """Test getting 360° tour URL"""
    print("\n" + "=" * 60)
    print("TEST 3: Get 360° Tour URL")
    print("=" * 60)
    
    widget_link = await getfloorplan_service.get_360_tour_url(
        plan_id=plan_id,
        wait=False  # Don't wait, just check current status
    )
    
    if widget_link:
        print(f"✅ 360° Tour is ready!")
        print(f"Widget Link: {widget_link}")
        print(f"\nEmbed in your app:")
        print(f'<iframe src="{widget_link}" width="100%" height="600px"></iframe>')
        return widget_link
    else:
        print("⏳ 360° Tour not ready yet")
        return None


async def test_get_images(plan_id: int):
    """Test getting rendered images"""
    print("\n" + "=" * 60)
    print("TEST 4: Get Rendered Images")
    print("=" * 60)
    
    images = await getfloorplan_service.get_rendered_images(
        plan_id=plan_id,
        wait=False
    )
    
    if images:
        total_images = len(images.get('svg', [])) + len(images.get('jpg', [])) + len(images.get('unreal3d', []))
        
        if total_images > 0:
            print(f"✅ Retrieved {total_images} rendered images")
            print(f"\nSVG Files ({len(images.get('svg', []))}):")
            for i, url in enumerate(images.get('svg', []), 1):
                print(f"  {i}. {url}")
            
            print(f"\nJPG Files ({len(images.get('jpg', []))}):")
            for i, url in enumerate(images.get('jpg', []), 1):
                print(f"  {i}. {url}")
            
            print(f"\n3D Assets ({len(images.get('unreal3d', []))}):")
            for i, url in enumerate(images.get('unreal3d', []), 1):
                print(f"  {i}. {url}")
        else:
            print("⏳ No images available yet")
        
        return images
    else:
        print("❌ Failed to retrieve images")
        return None


async def run_full_test(file_path: str):
    """Run complete test workflow"""
    print("\n🚀 GetFloorPlan AI Integration Test Suite")
    print("=" * 60)
    print(f"Floor Plan: {file_path}")
    print("=" * 60)
    
    # Validate file exists
    if not Path(file_path).exists():
        print(f"❌ Error: File not found: {file_path}")
        return
    
    # Test 1: Upload
    plan_id = await test_upload(file_path)
    if not plan_id:
        return
    
    # Test 2: Check status
    await test_status_check(plan_id)
    
    # Test 3: Get tour URL
    await test_get_tour_url(plan_id)
    
    # Test 4: Get images
    await test_get_images(plan_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Plan ID: {plan_id}")
    print(f"Status: Check again in 30-120 minutes")
    print(f"\nTo check status later, run:")
    print(f"  curl -X POST 'http://localhost:8000/api/v1/getfloorplan/check-plan-status' \\")
    print(f"    -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"    -H 'Content-Type: application/json' \\")
    print(f"    -d '{{\"plan_ids\": [{plan_id}]}}'")
    print("\n✅ Integration test complete!")


async def poll_until_ready(plan_id: int, max_wait_minutes: int = 120):
    """Poll status until plan is ready"""
    print(f"\n⏳ Polling for plan {plan_id} completion...")
    print(f"Max wait time: {max_wait_minutes} minutes")
    print("Press Ctrl+C to stop polling")
    
    poll_interval = 120  # 2 minutes
    elapsed_minutes = 0
    
    try:
        while elapsed_minutes < max_wait_minutes:
            results = await getfloorplan_service.check_plan_status([plan_id])
            
            if results and results[0].get('status') == 1:
                print(f"\n✅ Plan {plan_id} is ready!")
                await test_get_tour_url(plan_id)
                await test_get_images(plan_id)
                return
            
            elapsed_minutes += poll_interval / 60
            print(f"⏳ Still processing... ({elapsed_minutes:.1f}/{max_wait_minutes} minutes elapsed)")
            await asyncio.sleep(poll_interval)
        
        print(f"\n⏰ Timeout after {max_wait_minutes} minutes")
    except KeyboardInterrupt:
        print("\n⚠️  Polling stopped by user")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_getfloorplan_integration.py <floor_plan_image>")
        print("\nExample:")
        print("  python test_getfloorplan_integration.py floor_plan.png")
        print("\nOptional: Add 'poll' to wait for completion")
        print("  python test_getfloorplan_integration.py floor_plan.png poll")
        sys.exit(1)
    
    floor_plan_path = sys.argv[1]
    should_poll = len(sys.argv) > 2 and sys.argv[2] == "poll"
    
    # Run test
    asyncio.run(run_full_test(floor_plan_path))
    
    # Optional: Poll until ready
    if should_poll:
        # Get plan ID from previous run (you'd normally save this)
        print("\n⚠️  Polling mode: You need to provide the plan ID")
        plan_id_input = input("Enter plan ID to poll (or press Enter to skip): ")
        if plan_id_input:
            try:
                plan_id = int(plan_id_input)
                asyncio.run(poll_until_ready(plan_id))
            except ValueError:
                print("Invalid plan ID")
