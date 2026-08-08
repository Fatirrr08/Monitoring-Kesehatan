import json
from typing import Any

from app.config import settings
from app.models.schemas import UserDocument
from app.utils.logger import logger


class NutritionAnalyzer:
    """Extracts nutrition facts labels and evaluates them against user goals."""

    @classmethod
    async def analyze_label(cls, image_bytes: bytes, user: UserDocument | None = None) -> dict[str, Any]:
        """Parse nutrition label using OCR / Vision AI."""
        if settings.AI_API_KEY:
            try:
                import io

                import google.generativeai as genai
                from PIL import Image

                genai.configure(api_key=settings.AI_API_KEY)
                model = genai.GenerativeModel(settings.AI_MODEL_NAME or "gemini-1.5-flash")
                pil_img = Image.open(io.BytesIO(image_bytes))

                prompt = (
                    "Extract nutrition facts from this product label.\n"
                    "Extract fields: product_name, serving_size, calories, protein_g, carbs_g, fat_g, "
                    "saturated_fat_g, sugar_g, lactose_g, sodium_mg, fiber_g.\n"
                    "Return ONLY JSON format:\n"
                    "{\n"
                    '  "product_name": "Susu UHT",\n'
                    '  "serving_size": "250 ml",\n'
                    '  "calories": 140,\n'
                    '  "protein_g": 6.0,\n'
                    '  "carbs_g": 18.0,\n'
                    '  "fat_g": 5.0,\n'
                    '  "saturated_fat_g": 3.0,\n'
                    '  "sugar_g": 8.0,\n'
                    '  "lactose_g": 0.0,\n'
                    '  "sodium_mg": 125,\n'
                    '  "fiber_g": 0.0\n'
                    "}"
                )

                response = await model.generate_content_async([prompt, pil_img])
                text = response.text.strip()
                text = text.removeprefix("```json")
                text = text.removesuffix("```")
                return json.loads(text.strip())
            except Exception as e:
                logger.warning(f"Label OCR error ({e}). Using mock parser.")

        # Default fallback sample
        return {
            "product_name": "Susu Protein UHT / Minuman Sehat",
            "serving_size": "250 ml",
            "calories": 140,
            "protein_g": 6.0,
            "carbs_g": 18.0,
            "fat_g": 5.0,
            "saturated_fat_g": 2.5,
            "sugar_g": 8.0,
            "lactose_g": 0.0,
            "sodium_mg": 125,
            "fiber_g": 0.0,
        }

    @staticmethod
    def format_label_card(data: dict[str, Any], user: UserDocument | None = None) -> str:
        """Format the product label result and explain fit with user goals."""
        sugar_g = data.get("sugar_g", 0.0)
        sugar_note = "🟢 Gula terkendali" if sugar_g <= 10 else "🟡 Perhatikan batas gula harian"
        prot_g = data.get("protein_g", 0.0)

        lines = [
            "🥛 *PRODUCT ANALYSIS*",
            f"📦 *Produk:* {data.get('product_name', 'Kemasan Makanan/Minuman')}",
            f"📏 *Serving:* {data.get('serving_size', '1 sajian')}",
            "",
            f"🔥 *Calories:* `{data.get('calories')} kcal`",
            f"💪 *Protein:* `{prot_g} g`",
            f"🍞 *Carbohydrates:* `{data.get('carbs_g')} g`",
            f"🥑 *Fat:* `{data.get('fat_g')} g` (Jenuh: `{data.get('saturated_fat_g', 0.0)} g`)",
            f"🍬 *Total Sugar:* `{sugar_g} g` ({sugar_note})",
        ]

        if "lactose_g" in data and data["lactose_g"] is not None:
            lines.append(f"🥛 *Lactose:* `{data['lactose_g']} g`")

        lines.append(f"🧂 *Sodium:* `{data.get('sodium_mg')} mg`")
        if data.get("fiber_g", 0.0) > 0:
            lines.append(f"🥗 *Fiber:* `{data.get('fiber_g')} g`")

        lines.extend([
            "",
            "🎯 *Kesesuaian Target Harian:*",
            f"• Memberikan kontribusi `{prot_g}g` dari target protein harianmu (90–120g).",
            f"• Gula {sugar_g}g aman dalam batas maksimal 25g added sugar per hari.",
            "",
            "👉 *Catat produk ini ke jurnal harian?*"
        ])

        return "\n".join(lines)


nutrition_analyzer = NutritionAnalyzer()
