"""SellShot GPU API: IC-Light relight товара (премиум-движок)."""
from __future__ import annotations

import base64
import io
import logging
import os

import torch
from fastapi import FastAPI, Header, HTTPException
from PIL import Image
from pydantic import BaseModel

app = FastAPI()
logger = logging.getLogger("sellshot.gpu")

API_TOKEN = os.environ.get("GPU_API_TOKEN", "")
pipe = None


def load_pipe():
    global pipe
    if pipe is None:
        from diffusers import ICLightPipeline

        pipe = ICLightPipeline.from_pretrained(
            "lllyasviel/ic-light",
            torch_dtype=torch.float16,
        )
        pipe.to("cuda")
        pipe.set_progress_bar_config(disable=True)
    return pipe


class GenRequest(BaseModel):
    image: str      # base64 PNG RGBA (вырезанный товар)
    prompt: str = ""
    seed: int = -1


def check_token(x_api_token: str | None = Header(default=None)):
    if API_TOKEN and x_api_token != API_TOKEN:
        raise HTTPException(status_code=403, detail="bad token")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": pipe is not None}


@app.post("/generate")
def generate(req: GenRequest, x_api_token: str | None = Header(default=None)):
    check_token(x_api_token)
    try:
        p = load_pipe()
        fg = Image.open(io.BytesIO(base64.b64decode(req.image))).convert("RGBA")

        prompt = req.prompt or (
            "studio product photo, soft professional lighting, clean background"
        )
        negative = "blurry, low quality, distorted, watermark, text, bad edges"

        generator = None
        if req.seed >= 0:
            generator = torch.Generator(device="cuda").manual_seed(req.seed)

        out = p(
            prompt=prompt,
            negative_prompt=negative,
            image=fg,
            num_inference_steps=25,
            generator=generator,
        ).images[0]

        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return {"image": base64.b64encode(buf.getvalue()).decode()}
    except HTTPException:
        raise
    except Exception:
        # Детали — только в лог, наружу нейтральное сообщение
        logger.exception("Ошибка генерации на GPU")
        raise HTTPException(status_code=500, detail="internal error")