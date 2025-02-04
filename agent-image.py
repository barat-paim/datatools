import torch
from diffusers import StableDiffusionPipeline

model_id = "runwayml/stable-diffusion-v1-5"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda")  # or "mps" on macOS with Apple Silicon

prompt = (
    "An illustration of happy grandparents with their grandchildren, "
    "warm hearts, symbolizing love and a bright financial future, "
    "soft pastel tones, professional, inviting"
)

image = pipe(prompt, num_inference_steps=30, guidance_scale=7.5).images[0]
image.save("grandparents_investment_email.jpg")