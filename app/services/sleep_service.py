import re
import uuid

from app.models.schemas import SleepLog, today_str, utc_now


class SleepService:
    """Evaluates sleep duration independently from sleep schedule timing."""

    @staticmethod
    def parse_sleep_input(input_str: str) -> tuple[str, str, float]:
        """Parse time strings like '07:00 15:00', '23:30 07:30', or '8h'."""
        text = input_str.strip().lower()

        # Check for two HH:MM or HH.MM times
        time_matches = re.findall(r"(\d{1,2})[:.](\d{2})", text)
        if len(time_matches) >= 2:
            h1, m1 = int(time_matches[0][0]), int(time_matches[0][1])
            h2, m2 = int(time_matches[1][0]), int(time_matches[1][1])

            bedtime_str = f"{h1:02d}:{m1:02d}"
            wake_time_str = f"{h2:02d}:{m2:02d}"

            # Calculate duration in hours
            t1_mins = h1 * 60 + m1
            t2_mins = h2 * 60 + m2

            if t2_mins >= t1_mins:
                duration_mins = t2_mins - t1_mins
            else:
                # Crossed midnight (e.g. 23:00 -> 07:00 = 8h)
                duration_mins = (1440 - t1_mins) + t2_mins

            duration_hours = round(duration_mins / 60.0, 1)
            return bedtime_str, wake_time_str, duration_hours

        # Check for simple number (e.g. "8" or "7.5 jam")
        num_match = re.search(r"([\d\.]+)", text)
        if num_match:
            hours = float(num_match.group(1))
            return "23:00", "07:00", round(hours, 1)

        # Default fallback
        return "23:00", "07:00", 8.0

    @classmethod
    def evaluate_sleep(
        cls,
        telegram_user_id: int,
        input_str: str,
        notes: str | None = None,
    ) -> SleepLog:
        """Create structured SleepLog separating duration assessment from schedule timing."""
        bedtime, wake_time, duration = cls.parse_sleep_input(input_str)

        # 1. Evaluate Duration
        if duration >= 7.0 and duration <= 9.0:
            dur_assessment = "optimal 🟢"
        elif duration >= 6.0:
            dur_assessment = "cukup 🟡"
        else:
            dur_assessment = "kurang 🟠"

        # 2. Evaluate Timing (circadian regularity)
        h_bed = int(bedtime.split(":")[0])
        if 21 <= h_bed or h_bed <= 1:
            timing_assessment = "reguler malam 🟢"
        elif 2 <= h_bed <= 6:
            timing_assessment = "larut malam 🟡"
        else:
            timing_assessment = "shift / siang 🟠"

        sleep_id = f"sleep_{today_str()}_{uuid.uuid4().hex[:6]}"

        return SleepLog(
            sleep_id=sleep_id,
            telegram_user_id=telegram_user_id,
            bedtime=bedtime,
            wake_time=wake_time,
            duration_hours=duration,
            duration_assessment=dur_assessment,
            timing_assessment=timing_assessment,
            notes=notes,
            sleep_date=today_str(),
            created_at=utc_now(),
        )

    @staticmethod
    def render_sleep_message(log: SleepLog) -> str:
        """Render positive, supportive sleep summary without shaming."""
        return (
            "😴 *SLEEP LOG*\n\n"
            f"⏱️ *Duration:*\n"
            f"  `{log.duration_hours}` jam ({log.duration_assessment})\n\n"
            f"🕒 *Schedule:*\n"
            f"  `{log.bedtime}` – `{log.wake_time}` ({log.timing_assessment})\n\n"
            "💡 *Saran Santai:*\n"
            "_Tidur yang cukup adalah kunci pemulihan otot dan pembakaran lemak optimal. "
            "Jangan khawatir jika sesekali tidur larut, yang penting akumulasi istirahat tetap terjaga._"
        )


sleep_service = SleepService()
