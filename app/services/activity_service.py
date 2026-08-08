import re
import uuid

from app.models.schemas import ActivityLog, today_str, utc_now

# MET (Metabolic Equivalent of Task) table
MET_TABLE = {
    "walking": 3.8,       # Brisk walking ~5 km/h
    "running": 9.8,       # Moderate running ~8.5-9.5 km/h
    "badminton": 7.0,     # Competitive/casual badminton rally
    "skipping": 10.0,     # Jump rope moderate
    "home_workout": 5.5,  # Bodyweight circuit / resistance training
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
        - /badminton 2 matches 2 sets
        - /skipping 800
        - /workout 35m
        """
        args = args_text.strip().lower()
        act_id = f"act_{today_str()}_{uuid.uuid4().hex[:6]}"
        now_utc = utc_now()

        if command_type == "walk":
            dist_match = re.search(r"([\d\.]+)\s*(?:km|k\b)", args)
            dur_match = re.search(r"(\d+)\s*(?:menit|min\b|jam|hour|\bm\b|(?<=\d)m(?!\w))", args)

            distance = float(dist_match.group(1)) if dist_match else 5.0
            if dur_match:
                duration = float(dur_match.group(1))
            else:
                duration = distance * 11.5

            steps = int(distance * 1350)
            cals = cls.calculate_calories("walking", duration, user_weight_kg)
            c_min = int(cals * 0.85)
            c_max = int(cals * 1.15)

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="walking",
                distance_km=distance,
                duration_minutes=duration,
                steps=steps,
                pace_min_per_km=round(duration / distance, 2) if distance > 0 else None,
                estimated_calories=cals,
                calories_min=c_min,
                calories_max=c_max,
                source="command",
                notes=f"Jalan kaki {distance} km (~{steps:,} langkah)",
                activity_date=today_str(),
                created_at=now_utc,
            )

        elif command_type == "run":
            dist_match = re.search(r"([\d\.]+)\s*(?:km|k\b)", args)
            dur_match = re.search(r"(\d+)\s*(?:menit|min\b|jam|hour|\bm\b|(?<=\d)m(?!\w))", args)

            distance = float(dist_match.group(1)) if dist_match else 5.0
            if dur_match:
                duration = float(dur_match.group(1))
            else:
                duration = distance * 7.5

            pace = round(duration / distance, 2) if distance > 0 else 7.5
            steps = int(distance * 1100)
            cals = cls.calculate_calories("running", duration, user_weight_kg)
            c_min = int(cals * 0.9)
            c_max = int(cals * 1.1)

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="running",
                distance_km=distance,
                duration_minutes=duration,
                steps=steps,
                pace_min_per_km=pace,
                estimated_calories=cals,
                calories_min=c_min,
                calories_max=c_max,
                source="command",
                notes=f"Lari {distance} km dalam {int(duration)} menit (Pace {pace}'/km)",
                activity_date=today_str(),
                created_at=now_utc,
            )

        elif command_type == "badminton":
            match_regex = re.search(r"(\d+)\s*(?:match|pertandingan|game)", args)
            set_regex = re.search(r"(\d+)\s*(?:set|babak)", args)
            dur_match = re.search(r"(\d+)\s*(?:menit|min\b|jam|hour|\bm\b|(?<=\d)m(?!\w))", args)

            matches_count = int(match_regex.group(1)) if match_regex else 2
            sets_count = int(set_regex.group(1)) if set_regex else None

            if dur_match:
                raw_dur = float(dur_match.group(1))
                duration = (raw_dur * 60.0) if "jam" in args or "hour" in args else raw_dur
            else:
                duration = float(matches_count * 25.0)

            cals = cls.calculate_calories("badminton", duration, user_weight_kg)
            c_min = int(cals * 0.85)
            c_max = int(cals * 1.15)

            notes_str = f"Badminton {matches_count} match"
            if sets_count:
                notes_str += f", {sets_count} set"
            notes_str += f" (~{int(duration)} menit)"

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="badminton",
                matches=matches_count,
                sets=sets_count,
                duration_minutes=duration,
                estimated_calories=cals,
                calories_min=c_min,
                calories_max=c_max,
                source="command",
                notes=notes_str,
                activity_date=today_str(),
                created_at=now_utc,
            )

        elif command_type == "skipping":
            reps_match = re.search(r"(\d+)", args)
            reps = int(reps_match.group(1)) if reps_match else 500
            dur_match = re.search(r"(\d+)\s*(?:menit|min\b|\bm\b|(?<=\d)m(?!\w))", args)
            duration = float(dur_match.group(1)) if dur_match else (reps / 90.0)
            cals = cls.calculate_calories("skipping", duration, user_weight_kg)

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="skipping",
                repetitions=reps,
                duration_minutes=round(duration, 1),
                estimated_calories=cals,
                calories_min=int(cals * 0.85),
                calories_max=int(cals * 1.15),
                source="command",
                notes=f"Skipping {reps} lompatan (~{round(duration, 1)} menit)",
                activity_date=today_str(),
                created_at=now_utc,
            )

        elif command_type == "workout":
            dur_match = re.search(r"(\d+)\s*(?:menit|min\b|\bm\b|(?<=\d)m(?!\w))?", args)
            duration = float(dur_match.group(1)) if (dur_match and dur_match.group(1)) else 30.0
            cals = cls.calculate_calories("home_workout", duration, user_weight_kg)

            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="home_workout",
                duration_minutes=duration,
                estimated_calories=cals,
                calories_min=int(cals * 0.85),
                calories_max=int(cals * 1.15),
                source="command",
                notes=f"Home workout ({args or 'bodyweight/resistance'})",
                activity_date=today_str(),
                created_at=now_utc,
            )

        else:
            duration = 30.0
            cals = cls.calculate_calories("other", duration, user_weight_kg)
            return ActivityLog(
                activity_id=act_id,
                telegram_user_id=telegram_user_id,
                activity_type="other",
                duration_minutes=duration,
                estimated_calories=cals,
                calories_min=int(cals * 0.8),
                calories_max=int(cals * 1.2),
                source="command",
                notes=args or "Aktivitas fisik",
                activity_date=today_str(),
                created_at=now_utc,
            )


activity_service = ActivityService()
