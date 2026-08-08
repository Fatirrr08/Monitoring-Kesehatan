from typing import Any

from app.config import settings
from app.models.schemas import today_str
from app.services.firebase_service import firebase_service
from app.utils.logger import logger


class UserContextSummary:
    """Encapsulates relevant user context for AI Coach without dumping raw database history."""

    @classmethod
    async def build(cls, telegram_user_id: int) -> dict[str, Any]:
        user = await firebase_service.get_user(telegram_user_id)
        if not user:
            user = await firebase_service.create_user(telegram_user_id)

        summary = await firebase_service.get_daily_summary(telegram_user_id, today_str())
        weights = await firebase_service.get_weight_history(telegram_user_id, limit=2)
        current_w = weights[0].weight_kg if weights else user.profile.current_weight_kg
        diff_w = round(current_w - user.profile.target_weight_kg, 1)

        return {
            "age": user.profile.age,
            "current_weight_kg": current_w,
            "target_weight_kg": user.profile.target_weight_kg,
            "weight_to_target_kg": diff_w,
            "main_muscle_focus": user.profile.main_muscle_focus,
            "preferred_exercises": user.profile.preferred_exercises,
            "daily_calories": summary.total_calories,
            "target_calories": summary.target_calories,
            "daily_protein_g": summary.total_protein_g,
            "target_protein_min_g": user.goals.protein_target_min_g,
            "target_protein_max_g": user.goals.protein_target_max_g,
            "daily_sugar_g": summary.added_sugar_g,
            "max_sugar_g": user.goals.added_sugar_max_g,
            "daily_active_calories": summary.active_calories_burned,
            "daily_active_mins": summary.active_minutes,
            "sleep_hours": summary.sleep_hours,
            "water_ml": summary.total_water_ml,
            "target_water_ml": user.goals.water_target_ml,
        }


class AICoachService:
    """Retrieval-Augmented Conversational AI Coach with friendly Indonesian casual tone."""

    @classmethod
    async def get_coach_response(
        cls,
        telegram_user_id: int,
        user_message: str,
    ) -> str:
        # 1. Build structured, compact context summary
        ctx = await UserContextSummary.build(telegram_user_id)

        # 2. Heuristic fast-path responses for common questions
        msg = user_message.lower().strip()

        if "cheat" in msg or "flexible" in msg:
            return (
                "Boleh banget! Di FitTrack AI kita menyebutnya *flexible meal*, bukan cheat meal 😄.\n\n"
                "Satu porsi makanan favorit tidak akan merusak progres mingguanmu. "
                "Supaya tetap optimal, prioritaskan cukupi kebutuhan protein harian (90–120g) dan nikmati porsi wajarmu tanpa rasa bersalah. "
                "Konsistensi jangka panjang jauh lebih penting daripada kesempurnaan harian!"
            )

        if "bakso" in msg:
            cal_rem = max(ctx["target_calories"] - ctx["daily_calories"], 0)
            return (
                f"Boleh banget makan bakso! 🍲\n\n"
                f"Bakso sapi adalah sumber protein yang oke (~18–25g). "
                f"Hari ini sisa kalori budgetmu masih sekitar `{cal_rem}` kcal. "
                f"Tips santai: pilih kuah kaldu bening, perbanyak sawi/toge, dan batasi gorengan tambahannya agar kalori tetap efisien."
            )

        if "nasi goreng" in msg:
            return (
                "Nasi goreng tetap aman dinikmati kok! 🍚🍳\n\n"
                "Kuncinya adalah porsi dan lauk pendamping. Tambahkan 1-2 butir telur atau suwiran ayam agar protein harianmu tetap tercapai, "
                "dan nikmati porsi sedang (~350-450 kcal). Kamu tidak perlu memusuhi nasi untuk menurunkan lemak!"
            )

        if "protein" in msg and ("kurang" in msg or "cukup" in msg):
            diff = max(ctx["target_protein_min_g"] - ctx["daily_protein_g"], 0.0)
            if diff <= 0:
                return f"Mantap! Asupan proteinmu hari ini sudah mencapai `{ctx['daily_protein_g']}g`, melampaui target minimal `{ctx['target_protein_min_g']}g`. Ototmu aman untuk pemulihan! 💪"
            return (
                f"Hari ini proteinmu tercatat `{ctx['daily_protein_g']}g` dari target minimal `{ctx['target_protein_min_g']}g` (kurang ~`{round(diff, 1)}g`).\n\n"
                f"Pilihan cepat yang terjangkau: 2 butir telur rebus (+12g protein), 2 potong tempe/tahu (+10g), atau 1 gelas susu (+7g)."
            )

        if "kalori" in msg and ("banyak" in msg or "kebanyakan" in msg or "lebih" in msg):
            return (
                f"Total kalorimu hari ini tercatat `{ctx['daily_calories']}` kcal (target harian `{ctx['target_calories']}` kcal).\n\n"
                "Tenang, tidak perlu panik atau memaksakan puasa ekstrem besok. "
                "Tubuh kita merespons rata-rata mingguan, bukan satu hari saja. Cukup kembali ke rutinitas biasa besok dan tetap aktif bergerak!"
            )

        if "badminton" in msg or "bulutangkis" in msg:
            return (
                "Main badminton sangat bagus untuk pembakaran kalori dan kelincahan kardio! 🏸🔥\n\n"
                "2 match badminton membakar sekitar ~250–400 kcal tergantung intensitas. "
                "Pastikan minum air putih dan cukupi elektrolit setelah main ya!"
            )

        if "jalan" in msg or "lari" in msg or "workout" in msg:
            return (
                "Kerja bagus sudah aktif bergerak hari ini! 🔥\n\n"
                "Aktivitas fisik seperti jalan atau lari sangat efektif membakar kalori tanpa membebani sistem saraf pemulihan otot. "
                "Pastikan hidrasi air terjaga."
            )

        if "besok" in msg and ("latihan" in msg or "jadwal" in msg or "olahraga" in msg):
            focus_str = ", ".join(ctx["main_muscle_focus"])
            return (
                f"Untuk fokus rekomposisi ototmu ({focus_str}):\n\n"
                "🏋️ *Rekomendasi Latihan Besok:*\n"
                "1. Push-up / Incline push-up: 3 set x 8-12 repetisi (Dada & Bahu)\n"
                "2. Chair/Bench Dips: 3 set x 10 repetisi (Lengan / Triceps)\n"
                "3. Plank & Mountain Climbers: 3 set x 30 detik (Core)\n"
                "4. Ditutup dengan jalan santai 15-20 menit atau badminton ringan. Konsisten & santai!"
            )

        # 3. LLM Generation via Google Gemini if API Key is set
        if settings.AI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.AI_API_KEY)
                model = genai.GenerativeModel(settings.AI_MODEL_NAME or "gemini-1.5-flash")

                context_prompt = (
                    "You are 'FitTrack AI Coach', a warm, friendly, empathetic Indonesian fitness & nutrition coach.\n"
                    f"User Context Summary: {ctx}\n\n"
                    "Core Principles:\n"
                    "1. Friendly Indonesian casual conversational tone (bahasa Indonesia santai, suportif, akrab, emoji secukupnya).\n"
                    "2. NEVER shame or guilt the user. Do not encourage starvation or skipping meals.\n"
                    "3. Use 'flexible meal' instead of 'cheat meal'. Explain that one higher meal does not ruin progress.\n"
                    "4. Do not demonize rice or Indonesian foods. Encourage protein and recovery.\n\n"
                    f"User query: {user_message}\n"
                    "Answer:"
                )
                response = await model.generate_content_async(context_prompt)
                return response.text.strip()
            except Exception as e:
                logger.warning(f"AI Coach API fallback ({e})")

        # Conversational fallback
        return (
            f"Halo! Kalorimu hari ini tercatat `{ctx['daily_calories']}` kcal "
            f"dengan protein `{ctx['daily_protein_g']}g` (target: `{ctx['target_protein_min_g']}–{ctx['target_protein_max_g']}g`).\n\n"
            "Tetap jaga konsistensi asupan gizi seimbang dan bergerak aktif. Ada yang mau kamu diskusikan lagi seputar target rekomposisi tubuhmu?"
        )


ai_coach_service = AICoachService()
