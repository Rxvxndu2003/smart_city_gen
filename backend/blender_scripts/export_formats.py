"""
Blender export script for IFC, DXF, and other formats.
"""
import bpy
import sys
import argparse
from pathlib import Path


def export_ifc(output_path):
    """Export to IFC format."""
    # Note: Requires BlenderBIM add-on
    try:
        bpy.ops.export_ifc.bim(filepath=str(output_path))
        print(f"Exported IFC to {output_path}")
        return True
    except Exception as e:
        print(f"IFC export failed: {e}")
        return False


def export_dxf(output_path):
    """Export to DXF format."""
    try:
        bpy.ops.export_scene.dxf(filepath=str(output_path))
        print(f"Exported DXF to {output_path}")
        return True
    except Exception as e:
        print(f"DXF export failed: {e}")
        return False


def export_fbx(output_path):
    """Export to FBX format."""
    try:
        bpy.ops.export_scene.fbx(filepath=str(output_path))
        print(f"Exported FBX to {output_path}")
        return True
    except Exception as e:
        print(f"FBX export failed: {e}")
        return False


def main():
    """Main export function."""
    parser = argparse.ArgumentParser(description='Export Blender scene to various formats')
    parser.add_argument('--blend-file', type=str, required=True, help='Input .blend file')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory')
    parser.add_argument('--formats', type=str, required=True, help='Comma-separated export formats')
    parser.add_argument('--job-id', type=str, required=True, help='Job ID for file naming')
    
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    
    # Load blend file
    bpy.ops.wm.open_mainfile(filepath=args.blend_file)
    print(f"Loaded blend file: {args.blend_file}")
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    formats = args.formats.split(',')
    results = {}
    
    for format_name in formats:
        format_name = format_name.strip().upper()
        output_path = output_dir / f"{args.job_id}.{format_name.lower()}"
        
        if format_name == 'IFC':
            results['ifc'] = export_ifc(output_path)
        elif format_name == 'DXF':
            results['dxf'] = export_dxf(output_path)
        elif format_name == 'FBX':
            results['fbx'] = export_fbx(output_path)
        else:
            print(f"Unsupported format: {format_name}")
    
    print(f"Export complete. Results: {results}")


if __name__ == "__main__":
    main()
