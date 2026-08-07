import re
import uuid
from typing import Dict, Any, Optional
from app.models.schemas import ActivityLog, utc_now, today_str

# MET (Metabolic Equivalent of Task) values
MET_TABLE = {
    "walking": 3.8,       # Brisk walking ~5 km/h
    "running": 9.8,       # Moderate running ~8.5-9.5 km/h
    "skipping": 10.0,     # Jump rope moderate
    "home_workout": 5.5,  # Bodyweight circuit / resistance bands
    "cycling": 6.8,       # Moderate cycling
    "other": 4.5,
}


class ActivityService:
    """Calculates caloric expenditure, paces, and parses shorthand fitness commands."""

    @staticmethod
    def calculate_calories(
        activity_type: str,
        duration_minutes: float,
        user_weight_kg: float = 75.0,
    ) -> int:
        """Estimate calories burned = MET * weight_kg * (duration_minutes / 60)."""
        met = MET_TABLE.get(activity_type, 4.5)
        hours = duration_minutes / 60.0
        cals = met * user_weight_kg * hours
        return int(round(cals))

    @classmethod
    def parse_activity_command(
        cls,
        command_type: str,
        args_text: str,
        telegram_user_id: int,
        user_weight_kg: float = 75.0,
    ) -> ActivityLog:
        """Parse commands like:
        - /walk 6 km
        - /run 5 km 42m
        - /skipping 800
        - /workout 35m
        """
        args = args_text.strip().lower()
        act_id = f"act_{today_str()}_{uuid.uuid4().hex[:6]}"
        now_utc = utc_now()

        if command_type == "walk":
            # e.g. "6 km" or "6km" or "45m"
            dist_match = re.search(r"([\d\.]+)\s*(?:km|k)", args)
            dur_match = re.search(r"(\d+)\s*(?:m|menit|min)", args)

            distance = float(dist_match.group(1)) if dist_match else 5.0
            # Estimate duration if only distance is given (approx 11 min/km for brisk walk)
            if dur_match:
                duration = float(dur_match.group(1))
            else:
                duration = distance * 11.5

            steps = int(distance * 1350)
            cals = cls.calculate_calories("walking", duration, user_weight_kg)

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="walking",
                distance_km=distance,
                duration_minutes=duration,
                steps=steps,
                pace_min_per_km=round(duration / distance, 2) if distance > 0 else None,
                estimated_calories=cals,
                source="command",
                notes=f"Jalan kaki {distance} km (~{steps:,} langkah)",
                activity_date=today_str(),
                created_at=now_utc,
            )

        elif command_type == "run":
            # e.g. "5 km 42m" or "5km"
            dist_match = re.search(r"([\d\.]+)\s*(?:km|k)", args)
            dur_match = re.search(r"(\d+)\s*(?:m|menit|min)", args)

            distance = float(dist_match.group(1)) if dist_match else 5.0
            if dur_match:
                duration = float(dur_match.group(1))
            else:
                duration = distance * 7.5  # default ~7.5 min/km

            pace = round(duration / distance, 2) if distance > 0 else 7.5
            steps = int(distance * 1100)
            cals = cls.calculate_calories("running", duration, user_weight_kg)

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="running",
                distance_km=distance,
                duration_minutes=duration,
                steps=steps,
                pace_min_per_km=pace,
                estimated_calories=cals,
                source="command",
                notes=f"Lari {distance} km dalam {int(duration)} menit (Pace {pace}'/km)",
                activity_date=today_str(),
                created_at=now_utc,
            )

        elif command_type == "skipping":
            # e.g. "800" or "800 lompatan 15m"
            reps_match = re.search(r"(\d+)", args)
            reps = int(reps_match.group(1)) if reps_match else 500
            dur_match = re.search(r"(\d+)\s*(?:m|menit|min)", args)
            # Roughly 100 jumps per minute
            duration = float(dur_match.group(1)) if dur_match else (reps / 90.0)
            cals = cls.calculate_calories("skipping", duration, user_weight_kg)

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="skipping",
                repetitions=reps,
                duration_minutes=round(duration, 1),
                estimated_calories=cals,
                source="command",
                notes=f"Skipping {reps} lompatan (~{round(duration, 1)} menit)",
                activity_date=today_str(),
                created_at=now_utc,
            )

        elif command_type == "workout":
            # e.g. "35m" or "dada & lengan 30m"
            dur_match = re.search(r"(\d+)\s*(?:m|menit|min)?", args)
            duration = float(dur_match.group(1)) if dur_match else 30.0
            cals = cls.calculate_calories("home_workout", duration, user_weight_kg)

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="home_workout",
                duration_minutes=duration,
                estimated_calories=cals,
                source="command",
                notes=f"Home workout ({args or 'bodyweight/resistance'})",
                activity_date=today_str(),
                created_at=now_utc,
            )

        else:
            # Fallback
            duration = 30.0
            cals = cls.calculate_calories("other", duration, user_weight_kg)
            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="other",
                duration_minutes=duration,
                estimated_calories=cals,
                source="command",
                notes=args or "Aktivitas fisik",
                activity_date=today_str(),
                created_at=now_utc,
            )


activity_service = ActivityService()
