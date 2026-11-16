# Real-ESRGAN upscaling worker for RunPod Serverless

<p>
  <img src="https://img.shields.io/badge/RunPod-serverless-673AB7?style=flat-square" alt="RunPod serverless">
  <img src="https://img.shields.io/badge/Real--ESRGAN-x4plus-orange?style=flat-square" alt="Real-ESRGAN">
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT">
</p>

Send an image, get back a ×2 or ×4 upscale (1080p → 4K). A small, readable
[Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) worker for RunPod Serverless that scales to zero
when idle, so you only pay for the seconds it runs.

- **Two models**: `realesrgan-x4plus` for photos, `realesrgan-x4plus-anime` for illustration and anime
- **FP16 on GPU**, with **tiled** processing (512 px tiles) so large images fit in VRAM
- Model weights download once per worker and stay cached, and each model is kept loaded after first use
- JPEG or PNG output; one file (`handler.py`) that's easy to fork

## Request

```json
{
  "input": {
    "image_base64": "<base64 image>",
    "scale": 4,
    "model": "realesrgan-x4plus",
    "format": "jpg",
    "quality": 95
  }
}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `image_base64` | ✅ | | Any format Pillow can read |
| `scale` | | `4` | Output scale, `2` or `4` |
| `model` | | `realesrgan-x4plus` | or `realesrgan-x4plus-anime` |
| `format` | | `jpg` | `jpg` or `png` |
| `quality` | | `95` | JPEG quality 1–100 |

## Response

```json
{
  "image_base64": "<base64 upscaled image>",
  "original_size": [1920, 1080],
  "upscaled_size": [7680, 4320],
  "processing_time": 12.5,
  "model_used": "realesrgan-x4plus",
  "scale_factor": 4
}
```

On failure you get `{"error": "<message>"}`.

## Call it

```python
import base64, requests

ENDPOINT_ID, API_KEY = "your-endpoint-id", "your-runpod-api-key"

with open("photo.jpg", "rb") as f:
    payload = {"input": {"image_base64": base64.b64encode(f.read()).decode(), "scale": 4}}

r = requests.post(f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
                  json=payload, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=300)
out = r.json()["output"]
open("photo_4x.jpg", "wb").write(base64.b64decode(out["image_base64"]))
```

## Deploy

1. Fork this repo.
2. In the [RunPod console](https://www.runpod.io/console/serverless), go to **New Endpoint → GitHub repo** and pick your fork (it builds from the `Dockerfile`).
3. Suggested settings: a 24 GB GPU (RTX 4090 / 3090 / A5000), **min workers 0**, idle timeout ~5 s, container disk 20 GB.
4. Copy the **Endpoint ID**, and create an **API key** under *Settings → API Keys*.

## Test locally

Needs a CUDA GPU, or a lot of patience on CPU:

```bash
pip install -r requirements.txt
python test_local.py path/to/image.jpg     # writes <name>_4k.jpg next to it
```

## Performance and cost (rough)

Expect seconds to tens of seconds per 1080p image on a 24 GB card, plus a one-off cold start while weights download.
With scale-to-zero you pay per second of GPU time. Check current RunPod pricing and measure on your own images.

## License

MIT, see [LICENSE](LICENSE). Real-ESRGAN and its weights are BSD-3-Clause, © Xintao Wang et al.
