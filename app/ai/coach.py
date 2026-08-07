from typing import Optional, Dict, Any
from app.config import settings
from app.services.firebase_service import firebase_service
from app.models.schemas import UserDocument, DailySummary, today_str
from app.utils.logger import logger


class AICoachService:
    """Retrieval-Augmented Conversational AI Coach with friendly Indonesian casual tone."""

    @classmethod
    async def get_coach_response(
        cls,
        telegram_user_id: int,
        user_message: str,
    ) -> str:
        """Fetch user's current context from Firestore and formulate supportive advice."""
        # 1. Fetch user profile and today's summary
        user = await firebase_service.get_user(telegram_user_id)
        if not user:
            user = await firebase_service.create_user(telegram_user_id)

        summary = await firebase_service.get_daily_summary(telegram_user_id, today_str())
        weight_history = await firebase_service.get_weight_history(telegram_user_id, limit=3)
        current_w = weight_history[0].weight_kg if weight_history else user.profile.current_weight_kg

        # 2. Heuristic fast-path responses for common questions (ensuring speed & offline capability)
        msg = user_message.lower().strip()

        if "cheat" in msg or "flexible" in msg:
            return (
                "Boleh banget! Di FitTrack AI kita menyebutnya *flexible meal*, bukan cheat meal 😄.\n\n"
                "Satu porsi makanan favorit tidak akan merusak progres mingguanmu. "
                "Supaya tetap optimal, prioritaskan cukupi kebutuhan protein harian (90–120g) dan nikmati porsi wajarmu tanpa rasa bersalah. "
                "Konsistensi jangka panjang jauh lebih penting daripada kesempurnaan harian!"
            )

        if "bakso" in msg:
            cal_rem = max(user.goals.daily_calories_target - summary.total_calories, 0)
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
            diff = max(user.goals.protein_target_min_g - summary.total_protein_g, 0.0)
            if diff <= 0:
                return f"Mantap! Asupan proteinmu hari ini sudah mencapai `{summary.total_protein_g}g`, melampaui target minimal `{user.goals.protein_target_min_g}g`. Ototmu aman untuk pemulihan! 💪"
            return (
                f"Hari ini proteinmu tercatat `{summary.total_protein_g}g` dari target minimal `{user.goals.protein_target_min_g}g` (kurang ~`{round(diff, 1)}g`).\n\n"
                f"Pilihan cepat yang terjangkau: 2 butir telur rebus (+12g protein), 2 potong tempe/tahu (+10g), atau 1 gelas susu (+7g)."
            )

        if "kalori" in msg and ("banyak" in msg or "kebanyakan" in msg or "lebih" in msg):
            return (
                f"Total kalorimu hari ini tercatat `{summary.total_calories}` kcal (target harian `{summary.target_calories}` kcal).\n\n"
                "Tenang, tidak perlu panik atau memaksakan puasa ekstrem besok. "
                "Tubuh kita merespons rata-rata mingguan, bukan satu hari saja. Cukup kembali ke rutinitas biasa besok dan tetap aktif jalan santai!"
            )

        if "jalan" in msg or "lari" in msg or "workout" in msg:
            return (
                "Kerja bagus sudah aktif bergerak hari ini! 🔥\n\n"
                "Aktivitas fisik seperti jalan atau lari sangat efektif membakar kalori tanpa menaikkan hormon stres. "
                "Pastikan minum air putih yang cukup dan penuhi kebutuhan protein untuk pemulihan otot."
            )

        if "besok" in msg and ("latihan" in msg or "jadwal" in msg or "olahraga" in msg):
            return (
                f"Untuk fokus rekomposisi ototmu ({', '.join(user.profile.main_muscle_focus)}):\n\n"
                "🏋️ *Rekomendasi Latihan Besok:*\n"
                "1. Push-up / Incline push-up: 3 set x 8-12 repetisi (Dada & Bahu)\n"
                "2. Chair/Bench Dips: 3 set x 10 repetisi (Lengan / Triceps)\n"
                "3. Plank & Mountain Climbers: 3 set x 30 detik (Core)\n"
                "4. Ditutup dengan jalan kaki santai 15-20 menit. Ringan tapi berdampak besar!"
            )

        # 3. LLM Generation if API key is configured
        if settings.AI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.AI_API_KEY)
                model = genai.GenerativeModel(settings.AI_MODEL_NAME or "gemini-1.5-flash")

                context_prompt = (
                    "You are 'FitTrack AI Coach', a warm, friendly, empathetic, and knowledgeable Indonesian fitness & nutrition coach.\n"
                    "User Context:\n"
                    f"- Age: {user.profile.age}, Current Weight: {current_w} kg, Target Weight: {user.profile.target_weight_kg} kg\n"
                    f"- Goals: Body Recomposition (fat loss + muscle gain in {', '.join(user.profile.main_muscle_focus)})\n"
                    f"- Today's Nutrition: {summary.total_calories}/{summary.target_calories} kcal, Protein: {summary.total_protein_g}/{user.goals.protein_target_min_g}-{user.goals.protein_target_max_g}g, Added Sugar: {summary.added_sugar_g}/{user.goals.added_sugar_max_g}g\n"
                    f"- Today's Activity: {summary.active_calories_burned} kcal burned ({summary.active_minutes} min)\n"
                    f"- Today's Sleep: {summary.sleep_hours} hours, Water: {summary.total_water_ml}/{summary.target_water_ml} ml\n\n"
                    "Core Principles:\n"
                    "1. Friendly Indonesian casual conversational tone (bahasa Indonesia santai, suportif, akrab, emoji secukupnya).\n"
                    "2. NEVER shame or guilt the user. Do not encourage starvation or skipping meals.\n"
                    "3. Use 'flexible meal' instead of 'cheat meal'. Explain that one higher meal does not ruin progress.\n"
                    "4. Do not demonize rice or Indonesian foods. Encourage protein and recovery.\n\n"
                    f"User message: {user_message}\n"
                    "Response:"
                )
                response = await model.generate_content_async(context_prompt)
                return response.text.strip()
            except Exception as e:
                logger.warning(f"AI Coach API fallback ({e})")

        # Conversational fallback
        return (
            f"Halo! Terkait pertanyaanmu, saat ini kalorimu tercatat `{summary.total_calories}` kcal "
            f"dengan protein `{summary.total_protein_g}g` dari target minimal `{user.goals.protein_target_min_g}g`.\n\n"
            "Tetap jaga konsistensi asupan gizi seimbang dan bergerak aktif setiap hari. Ada yang mau kamu diskusikan lagi seputar target rekomposisi tubuhmu?"
        )


ai_coach_service = AICoachService()
