"""
RunPod Real-ESRGAN Upscaling Handler
Handles image upscaling requests using Real-ESRGAN on GPU
"""

import runpod
import base64
import io
import os
from PIL import Image
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
from realesrgan.archs.srvgg_arch import SRVGGNetCompact
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Loaded models, one per model variant (each loaded once per worker)
_upsamplers = {}


def download_models():
    """Download and cache Real-ESRGAN models"""
    import urllib.request
    from pathlib import Path

    models_dir = Path('/workspace/models')
    models_dir.mkdir(parents=True, exist_ok=True)

    models = {
        'RealESRGAN_x4plus.pth': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
        'RealESRGAN_x4plus_anime_6B.pth': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth',
    }

    for model_name, url in models.items():
        model_path = models_dir / model_name
        if not model_path.exists():
            logger.info(f"Downloading {model_name}...")
            urllib.request.urlretrieve(url, str(model_path))
            logger.info(f"Downloaded {model_name}")

    return str(models_dir)


def initialize_model(model_name='realesrgan-x4plus'):
    """Initialize Real-ESRGAN model on GPU"""
    key = 'anime' if 'anime' in model_name.lower() else 'x4plus'
    if key in _upsamplers:
        return _upsamplers[key]

    logger.info(f"Initializing {model_name} model...")

    # Download models if not cached
    models_dir = download_models()

    # Determine which model to use
    if 'anime' in model_name.lower():
        model_path = f'{models_dir}/RealESRGAN_x4plus_anime_6B.pth'
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
    else:
        model_path = f'{models_dir}/RealESRGAN_x4plus.pth'
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)

    # Determine device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")

    # Initialize upsampler
    upsampler = RealESRGANer(
        scale=4,
        model_path=model_path,
        model=model,
        tile=512,  # Tile size for processing large images
        tile_pad=10,
        pre_pad=0,
        half=True if device == 'cuda' else False,  # FP16 for faster GPU processing
        device=device
    )

    logger.info("Model initialized successfully")
    _upsamplers[key] = upsampler
    return upsampler


def handler(event):
    """
    RunPod handler for upscaling requests

    Expected input format:
    {
        "input": {
            "image_base64": "base64_encoded_image",
            "scale": 2 or 4 (optional, default 4),
            "model": "realesrgan-x4plus" or "realesrgan-x4plus-anime" (optional),
            "format": "jpg" or "png" (optional, default jpg),
            "quality": 95 (optional, for jpg only)
        }
    }

    Returns:
    {
        "image_base64": "base64_encoded_upscaled_image",
        "original_size": [width, height],
        "upscaled_size": [width, height],
        "processing_time": seconds
    }
    """
    import time
    start_time = time.time()

    try:
        # Extract input parameters
        job_input = event.get('input', {})
        image_base64 = job_input.get('image_base64')
        scale = job_input.get('scale', 4)
        model_name = job_input.get('model', 'realesrgan-x4plus')
        output_format = job_input.get('format', 'jpg').lower()
        quality = job_input.get('quality', 95)

        if not image_base64:
            return {"error": "No image_base64 provided"}

        # Decode input image
        logger.info("Decoding input image...")
        image_data = base64.b64decode(image_base64)
        input_image = Image.open(io.BytesIO(image_data)).convert('RGB')
        original_size = input_image.size

        logger.info(f"Original size: {original_size[0]}x{original_size[1]}")

        # Initialize model (cached globally)
        upsampler = initialize_model(model_name)

        # Convert PIL image to numpy array
        import numpy as np
        import cv2
        img_array = np.array(input_image)
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Perform upscaling
        logger.info("Starting upscaling...")
        output_array, _ = upsampler.enhance(img_array, outscale=scale)

        # Convert back to PIL image
        output_array = cv2.cvtColor(output_array, cv2.COLOR_BGR2RGB)
        output_image = Image.fromarray(output_array)
        upscaled_size = output_image.size

        logger.info(f"Upscaled size: {upscaled_size[0]}x{upscaled_size[1]}")

        # Encode output image
        logger.info("Encoding output image...")
        buffer = io.BytesIO()
        if output_format == 'png':
            output_image.save(buffer, format='PNG', compress_level=3)
        else:
            output_image.save(buffer, format='JPEG', quality=quality, optimize=True)

        buffer.seek(0)
        output_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        processing_time = time.time() - start_time
        logger.info(f"Processing completed in {processing_time:.2f}s")

        return {
            "image_base64": output_base64,
            "original_size": list(original_size),
            "upscaled_size": list(upscaled_size),
            "processing_time": processing_time,
            "model_used": model_name,
            "scale_factor": scale
        }

    except Exception as e:
        logger.error(f"Error during upscaling: {str(e)}", exc_info=True)
        return {"error": str(e)}


# RunPod serverless entry point
runpod.serverless.start({"handler": handler})
