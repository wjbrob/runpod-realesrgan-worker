"""
Local test script for Real-ESRGAN handler
Tests the upscaling functionality before deploying to RunPod
"""

import base64
import sys
from pathlib import Path
from handler import handler


def test_upscaling(image_path: str):
    """Test upscaling with a local image"""

    # Read and encode test image
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Prepare test event
    event = {
        "input": {
            "image_base64": image_base64,
            "scale": 4,
            "model": "realesrgan-x4plus",
            "format": "jpg",
            "quality": 95
        }
    }

    print(f"Testing upscaling with image: {image_path}")
    print(f"Input size: {len(image_bytes) / 1024:.1f} KB")

    # Run handler
    result = handler(event)

    # Check result
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False

    print(f"✅ Success!")
    print(f"   Original size: {result['original_size']}")
    print(f"   Upscaled size: {result['upscaled_size']}")
    print(f"   Processing time: {result['processing_time']:.2f}s")
    print(f"   Model: {result['model_used']}")
    print(f"   Output size: {len(result['image_base64']) * 3/4 / 1024:.1f} KB")

    # Save output image
    output_data = base64.b64decode(result['image_base64'])
    output_path = Path(image_path).stem + "_4k.jpg"
    with open(output_path, 'wb') as f:
        f.write(output_data)

    print(f"   Saved to: {output_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_local.py <image_path>")
        print("\nExample:")
        print("  python test_local.py /path/to/test_image.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)

    success = test_upscaling(image_path)
    sys.exit(0 if success else 1)
