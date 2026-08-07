from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.models.schemas import DailySummary, WeightLog
from app.services.firebase_service import firebase_service
from app.utils.formatting import make_progress_bar


class ReportService:
    """Computes daily scores and generates weekly fitness & body recomposition reports."""

    @staticmethod
    def render_daily_score_text(summary: DailySummary) -> str:
        """Render the multi-metric daily score view."""
        bd = summary.daily_score_breakdown
        score_val = summary.daily_score

        # Indicator badge
        if score_val >= 8.0:
            badge = "🟢 Excellent"
        elif score_val >= 6.0:
            badge = "🟡 Good Consistency"
        else:
            badge = "⚪ Steady Step"

        return (
            "⭐ *DAILY SCORE*\n\n"
            f"🎯 *Total Score:* `{score_val}` / `10.0` ({badge})\n\n"
            f"🥗 Nutrition:       {bd.get('nutrition', '⚪')}\n"
            f"💪 Protein:         {bd.get('protein', '⚪')}\n"
            f"🍬 Sugar Control:   {bd.get('sugar', '⚪')}\n"
            f"🏃 Activity:        {bd.get('activity', '⚪')}\n"
            f"😴 Sleep:           {bd.get('sleep', '⚪')}\n"
            f"💧 Hydration:       {bd.get('hydration', '⚪')}\n\n"
            "💡 *Tips:* _Skor harian adalah cermin konsistensi, bukan penghakiman. "
            "Fokus pada kebiasaan kecil yang berkelanjutan!_"
        )

    @staticmethod
    async def generate_weekly_report(telegram_user_id: int) -> str:
        """Aggregate 7-day data for weekly analytics."""
        now = datetime.now()
        summaries: List[DailySummary] = []

        for i in range(7):
            dt_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            s = await firebase_service.get_daily_summary(telegram_user_id, dt_str)
            if s and (s.total_calories > 0 or s.active_calories_burned > 0 or s.total_water_ml > 0 or s.sleep_hours > 0):
                summaries.append(s)

        weights = await firebase_service.get_weight_history(telegram_user_id, limit=7)

        # Weight Trend
        if len(weights) >= 2:
            start_w = weights[-1].weight_kg
            latest_w = weights[0].weight_kg
            weight_text = f"`{start_w}` → `{latest_w}` kg ({round(latest_w - start_w, 2):+} kg)"
        elif weights:
            weight_text = f"`{weights[0].weight_kg}` kg"
        else:
            weight_text = "`Belum ada log berat badan`"

        # Averages
        days_with_food = [s for s in summaries if s.total_calories > 0]
        avg_cal = int(sum(s.total_calories for s in days_with_food) / len(days_with_food)) if days_with_food else 0
        avg_prot = round(sum(s.total_protein_g for s in days_with_food) / len(days_with_food), 1) if days_with_food else 0.0
        avg_sugar = round(sum(s.added_sugar_g for s in days_with_food) / len(days_with_food), 1) if days_with_food else 0.0

        active_days = len([s for s in summaries if s.active_minutes > 0 or s.active_calories_burned > 0])
        sleep_days = [s for s in summaries if s.sleep_hours > 0]
        avg_sleep = round(sum(s.sleep_hours for s in sleep_days) / len(sleep_days), 1) if sleep_days else 0.0
        h_part = int(avg_sleep)
        m_part = int(round((avg_sleep - h_part) * 60))

        avg_water = int(sum(s.total_water_ml for s in summaries) / len(summaries)) if summaries else 0

        lines = [
            "📊 *WEEKLY REPORT*",
            "Rekapitulasi 7 hari terakhir:\n",
            f"⚖️ *Weight Trend:* {weight_text}",
            f"🔥 *Avg Calories:* `{avg_cal}` kcal/day",
            f"💪 *Avg Protein:* `{avg_prot}` g/day",
            f"🍬 *Avg Added Sugar:* `{avg_sugar}` g/day (Target <= 25g)",
            f"🏃 *Activity Frequency:* `{active_days}` / 7 hari",
            f"😴 *Avg Sleep:* `{h_part}h {m_part}m` per hari",
            f"💧 *Avg Water:* `{avg_water:,}` ml/day",
            "",
            "🎯 *Overall Evaluation:*",
            "🟢 *Good Progress!* Konsistensi asupan protein dan aktivitas terus membuahkan hasil.",
            "",
            "✨ *Area Pengembangan:*",
            "• Jaga hidrasi air putih minimal 2,000–2,500 ml setiap hari.",
            "• Pertahankan asupan protein di rentang 90–120g untuk mendukung pembentukan otot."
        ]

        return "\n".join(lines)


report_service = ReportService()
