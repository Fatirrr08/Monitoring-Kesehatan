from typing import List, Dict, Any
from app.models.schemas import FoodLog, DailySummary
from app.utils.formatting import make_progress_bar


class NutritionService:
    """Business logic for nutrition calculations, sugar monitoring, and visual formatting."""

    @staticmethod
    def calculate_sugar_summary(total_sugar: float, added_sugar: float, max_added: float = 25.0) -> Dict[str, Any]:
        """Differentiate natural sugar (from fruits/dairy) and added sugar with traffic light indicator."""
        status = "🟢 Good" if added_sugar <= max_added else "🟡 Di atas target"
        return {
            "total_sugar": round(total_sugar, 1),
            "added_sugar": round(added_sugar, 1),
            "max_added": max_added,
            "status": status,
            "is_safe": added_sugar <= max_added,
        }

    @staticmethod
    def render_protein_bar(current_g: float, target_max_g: float = 120.0, length: int = 10) -> str:
        """Render ASCII progress bar for daily protein intake."""
        return make_progress_bar(current_g, target_max_g, length=length)

    @staticmethod
    def render_nutrition_summary_text(summary: DailySummary) -> str:
        """Generate the clean, standard Indonesian nutrition overview message."""
        protein_bar = NutritionService.render_protein_bar(
            summary.total_protein_g,
            summary.target_protein_max_g
        )
        water_bar = make_progress_bar(summary.total_water_ml, summary.target_water_ml, length=10)
        sugar_status = "🟢 Good" if summary.added_sugar_g <= summary.added_sugar_max_g else "🟡 Perhatikan"

        lines = [
            "📊 *DAILY SUMMARY*",
            f"📅 Tanggal: `{summary.summary_date}`",
            "",
            "🔥 *Calories:*",
            f"  `{summary.total_calories}` / `{summary.target_calories}` kcal",
            "",
            "💪 *Protein:*",
            f"  `{summary.total_protein_g}` / `{int(summary.target_protein_min_g)}–{int(summary.target_protein_max_g)}` g",
            f"  {protein_bar}",
            "",
            "🍞 *Carbohydrates:*",
            f"  `{summary.total_carbs_g}` g",
            "",
            "🥑 *Fat:*",
            f"  `{summary.total_fat_g}` g",
            "",
            "🍬 *Sugar (Added):*",
            f"  `{summary.added_sugar_g}` / `{int(summary.added_sugar_max_g)}` g  {sugar_status}",
            f"  _(Total gula termasuk alami: {summary.total_sugar_g} g)_",
            "",
            "🥗 *Fiber:*",
            f"  `{summary.total_fiber_g}` g",
            "",
            "🍽️ *Meals logged:*",
            f"  `{summary.meal_count}` kali makan",
            "",
            "🏃 *Activity:*",
            f"  `{summary.active_calories_burned}` kcal burned (`{int(summary.active_minutes)}` menit)",
            "",
            "😴 *Sleep:*",
            f"  `{summary.sleep_hours}` jam" + (f" ({summary.sleep_bedtime} - {summary.sleep_wake_time})" if summary.sleep_bedtime else ""),
            "",
            "💧 *Water:*",
            f"  `{summary.total_water_ml:,}` / `{summary.target_water_ml:,}` ml",
            f"  {water_bar}",
        ]

        if summary.ai_feedback:
            lines.extend([
                "",
                "💡 *Catatan Ringkas:*",
                f"_{summary.ai_feedback}_"
            ])

        return "\n".join(lines)


nutrition_service = NutritionService()
