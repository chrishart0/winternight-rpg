#!/usr/bin/env python3
"""Generate a deterministic SDXL + Canny + pixel-LoRA candidate batch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import torch
from diffusers import (
    AutoencoderKL,
    ControlNetModel,
    DPMSolverMultistepScheduler,
    StableDiffusionXLControlNetPipeline,
)
from PIL import Image, ImageOps


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--negative",
        default="text, watermark, scenery, blurry, malformed geometry",
    )
    parser.add_argument("--seeds", default="6029,15991,27143,43651")
    parser.add_argument("--base", default="stabilityai/stable-diffusion-xl-base-1.0")
    parser.add_argument("--controlnet", default="diffusers/controlnet-canny-sdxl-1.0")
    parser.add_argument("--lora", default="nerijs/pixel-art-xl")
    parser.add_argument("--lora-file", default="pixel-art-xl.safetensors")
    parser.add_argument("--vae", default="madebyollin/sdxl-vae-fp16-fix")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=36)
    parser.add_argument("--guidance", type=float, default=7.0)
    parser.add_argument("--control-scale", type=float, default=0.95)
    parser.add_argument("--lora-scale", type=float, default=0.7)
    parser.add_argument("--local-files-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this generation workflow")
    seeds = [int(value) for value in args.seeds.split(",")]
    if not seeds:
        raise ValueError("at least one seed is required")
    args.output.mkdir(parents=True, exist_ok=True)

    reference = Image.open(args.reference).convert("RGB")
    reference = ImageOps.fit(reference, (args.width, args.height), Image.Resampling.LANCZOS)
    gray = cv2.cvtColor(np.asarray(reference), cv2.COLOR_RGB2GRAY)
    control = Image.fromarray(cv2.Canny(gray, 80, 180)).convert("RGB")
    control_path = args.output / "control.png"
    control.save(control_path)

    dtype = torch.bfloat16
    controlnet = ControlNetModel.from_pretrained(
        args.controlnet, torch_dtype=dtype, local_files_only=args.local_files_only
    )
    vae = AutoencoderKL.from_pretrained(
        args.vae, torch_dtype=dtype, local_files_only=args.local_files_only
    )
    pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
        args.base,
        controlnet=controlnet,
        vae=vae,
        torch_dtype=dtype,
        variant="fp16",
        use_safetensors=True,
        local_files_only=args.local_files_only,
    ).to("cuda")
    pipe.load_lora_weights(
        args.lora,
        weight_name=args.lora_file,
        adapter_name="pixel",
        local_files_only=args.local_files_only,
    )
    pipe.set_adapters("pixel", adapter_weights=args.lora_scale)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config,
        algorithm_type="sde-dpmsolver++",
        use_karras_sigmas=True,
    )
    pipe.vae.enable_tiling()

    outputs = []
    for index, seed in enumerate(seeds, start=1):
        image = pipe(
            prompt=args.prompt,
            negative_prompt=args.negative,
            image=control,
            controlnet_conditioning_scale=args.control_scale,
            guidance_scale=args.guidance,
            num_inference_steps=args.steps,
            generator=torch.Generator(device="cuda").manual_seed(seed),
            width=args.width,
            height=args.height,
        ).images[0]
        path = args.output / f"candidate-{index}-seed-{seed}.png"
        image.save(path)
        outputs.append({"path": path.name, "seed": seed, "sha256": _sha256(path)})

    metadata = {
        "reference": str(args.reference),
        "reference_sha256": _sha256(args.reference),
        "control_sha256": _sha256(control_path),
        "prompt": args.prompt,
        "negative_prompt": args.negative,
        "models": {
            "base": args.base,
            "controlnet": args.controlnet,
            "lora": args.lora,
            "vae": args.vae,
        },
        "settings": {
            "width": args.width,
            "height": args.height,
            "steps": args.steps,
            "guidance": args.guidance,
            "control_scale": args.control_scale,
            "lora_scale": args.lora_scale,
        },
        "outputs": outputs,
    }
    (args.output / "generation.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
