# RunPod Real-ESRGAN Upscaling Worker

GPU-accelerated 4K image upscaling worker for RunPod Serverless.

## Features

- **Real-ESRGAN x4plus** model for photorealistic upscaling
- **Real-ESRGAN x4plus Anime** model for anime/illustration upscaling
- **4x upscaling** from 1080p to 4K in 10-30 seconds
- **FP16 optimization** for faster GPU processing
- **Tiled processing** for large images
- **Automatic model caching** to reduce cold start time

## Performance

- **Processing Time**: 10-30 seconds per 1080p image on RTX 4090
- **GPU Memory**: ~8GB VRAM for 4K output
- **Cost**: ~$0.0012 per image ($0.44/hour GPU × 10 sec)

## Input Format

```json
{
  "input": {
    "image_base64": "base64_encoded_image_data",
    "scale": 4,
    "model": "realesrgan-x4plus",
    "format": "jpg",
    "quality": 95
  }
}
```

### Parameters

- `image_base64` (required): Base64-encoded input image
- `scale` (optional): Upscaling factor, 2 or 4 (default: 4)
- `model` (optional): `realesrgan-x4plus` or `realesrgan-x4plus-anime` (default: realesrgan-x4plus)
- `format` (optional): Output format `jpg` or `png` (default: jpg)
- `quality` (optional): JPEG quality 1-100 (default: 95)

## Output Format

```json
{
  "image_base64": "base64_encoded_upscaled_image",
  "original_size": [1920, 1080],
  "upscaled_size": [3840, 2160],
  "processing_time": 12.5,
  "model_used": "realesrgan-x4plus",
  "scale_factor": 4
}
```

## Deployment to RunPod

### 1. Push to GitHub

```bash
cd /root/stockmix/runpod-workers/realesrgan-worker
git init
git add .
git commit -m "Initial Real-ESRGAN worker"
git remote add origin https://github.com/YOUR_USERNAME/runpod-realesrgan-worker.git
git push -u origin main
```

### 2. Create RunPod Endpoint

1. Go to [RunPod Console](https://www.runpod.io/console/serverless)
2. Click **New Endpoint**
3. Configure:
   - **Name**: `realesrgan-upscaler`
   - **Container Source**: GitHub
   - **GitHub URL**: `https://github.com/YOUR_USERNAME/runpod-realesrgan-worker`
   - **GPU Type**: RTX 4090 (24GB VRAM recommended)
   - **Max Workers**: 3
   - **Idle Timeout**: 5 seconds
   - **Container Disk**: 20GB
   - **Spot Instance**: Yes (50-70% cost savings)

### 3. Get Credentials

After deployment:
- Copy **Endpoint ID** from RunPod dashboard
- Create **API Key** in Settings → API Keys

### 4. Update .env

```bash
echo "RUNPOD_UPSCALING_ENDPOINT_ID=your_endpoint_id_here" >> /root/stockmix/.env
```

## Testing Locally (Docker)

```bash
# Build image
docker build -t realesrgan-worker .

# Run locally
docker run --gpus all -p 8000:8000 realesrgan-worker

# Test with curl
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image_base64": "...",
      "scale": 4,
      "model": "realesrgan-x4plus"
    }
  }'
```

## Cost Optimization

- **Use Spot Instances**: 50-70% cheaper than on-demand
- **Enable Scale-to-Zero**: Only pay when processing
- **Batch Processing**: Send multiple images concurrently
- **Model Caching**: Models are cached after first load

## Supported GPUs

- RTX 4090 (recommended) - $0.44/hour
- RTX 3090 - $0.36/hour
- A100 40GB - $1.00/hour
- A100 80GB - $1.40/hour

## License

MIT License - Uses Real-ESRGAN (BSD-3-Clause)

## References

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN)
- [RunPod Docs](https://docs.runpod.io/serverless/overview)
