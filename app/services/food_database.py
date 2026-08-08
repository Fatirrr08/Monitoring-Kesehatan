
from pydantic import BaseModel


class IndonesianFoodItem(BaseModel):
    key: str
    name: str
    default_portion: str
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    total_sugar_g: float
    added_sugar_g: float
    fiber_g: float
    sodium_mg: float
    category: str
    notes: str | None = None


INDONESIAN_FOOD_DATABASE: dict[str, IndonesianFoodItem] = {
    "nasi_putih": IndonesianFoodItem(
        key="nasi_putih",
        name="Nasi Putih",
        default_portion="1 centong sedang (100g)",
        calories=130,
        protein_g=2.7,
        carbs_g=28.2,
        fat_g=0.3,
        total_sugar_g=0.1,
        added_sugar_g=0.0,
        fiber_g=0.4,
        sodium_mg=1,
        category="staple",
        notes="Sumber karbohidrat utama, jangan dihindari tapi sesuaikan porsi."
    ),
    "nasi_goreng": IndonesianFoodItem(
        key="nasi_goreng",
        name="Nasi Goreng",
        default_portion="1 piring (200g)",
        calories=350,
        protein_g=8.0,
        carbs_g=45.0,
        fat_g=15.0,
        total_sugar_g=2.0,
        added_sugar_g=1.5,
        fiber_g=1.5,
        sodium_mg=520,
        category="staple",
        notes="Estimasi standar dengan kecap manis dan minyak wajar."
    ),
    "nasi_bakar": IndonesianFoodItem(
        key="nasi_bakar",
        name="Nasi Bakar",
        default_portion="1 bungkus (180g)",
        calories=310,
        protein_g=7.5,
        carbs_g=42.0,
        fat_g=12.0,
        total_sugar_g=1.2,
        added_sugar_g=0.5,
        fiber_g=1.2,
        sodium_mg=450,
        category="staple"
    ),
    "bubur_ayam": IndonesianFoodItem(
        key="bubur_ayam",
        name="Bubur Ayam",
        default_portion="1 mangkuk lengkap (250g)",
        calories=280,
        protein_g=12.0,
        carbs_g=38.0,
        fat_g=8.5,
        total_sugar_g=1.5,
        added_sugar_g=0.5,
        fiber_g=1.0,
        sodium_mg=580,
        category="staple"
    ),
    "ayam_crispy": IndonesianFoodItem(
        key="ayam_crispy",
        name="Ayam Goreng Crispy",
        default_portion="1 potong paha/dada (120g)",
        calories=290,
        protein_g=22.0,
        carbs_g=11.0,
        fat_g=17.0,
        total_sugar_g=0.0,
        added_sugar_g=0.0,
        fiber_g=0.5,
        sodium_mg=480,
        category="protein"
    ),
    "ayam_kemangi": IndonesianFoodItem(
        key="ayam_kemangi",
        name="Ayam Suwir Kemangi",
        default_portion="1 porsi (100g)",
        calories=175,
        protein_g=25.0,
        carbs_g=3.0,
        fat_g=7.0,
        total_sugar_g=0.5,
        added_sugar_g=0.2,
        fiber_g=1.0,
        sodium_mg=380,
        category="protein",
        notes="Pilihan protein tinggi dan rendah minyak."
    ),
    "ayam_bawang_putih": IndonesianFoodItem(
        key="ayam_bawang_putih",
        name="Ayam Goreng Bawang Putih",
        default_portion="1 potong (100g)",
        calories=220,
        protein_g=24.0,
        carbs_g=4.0,
        fat_g=12.0,
        total_sugar_g=0.2,
        added_sugar_g=0.0,
        fiber_g=0.5,
        sodium_mg=390,
        category="protein"
    ),
    "dada_ayam": IndonesianFoodItem(
        key="dada_ayam",
        name="Dada Ayam Panggang / Rebus",
        default_portion="1 potong dada (100g)",
        calories=165,
        protein_g=31.0,
        carbs_g=0.0,
        fat_g=3.6,
        total_sugar_g=0.0,
        added_sugar_g=0.0,
        fiber_g=0.0,
        sodium_mg=74,
        category="protein",
        notes="Sangat ideal untuk target rekomposisi otot."
    ),
    "tongkol": IndonesianFoodItem(
        key="tongkol",
        name="Ikan Tongkol Balado / Masak",
        default_portion="1 potong sedang (80g)",
        calories=140,
        protein_g=20.0,
        carbs_g=2.5,
        fat_g=5.5,
        total_sugar_g=0.5,
        added_sugar_g=0.2,
        fiber_g=0.4,
        sodium_mg=310,
        category="protein"
    ),
    "ikan_teri": IndonesianFoodItem(
        key="ikan_teri",
        name="Ikan Teri Goreng / Sambal",
        default_portion="2 sdm (30g)",
        calories=95,
        protein_g=9.5,
        carbs_g=1.0,
        fat_g=6.0,
        total_sugar_g=0.0,
        added_sugar_g=0.0,
        fiber_g=0.0,
        sodium_mg=450,
        category="protein"
    ),
    "telur": IndonesianFoodItem(
        key="telur",
        name="Telur Ayam (Rebus / Ceplok)",
        default_portion="1 butir (55g)",
        calories=78,
        protein_g=6.3,
        carbs_g=0.6,
        fat_g=5.3,
        total_sugar_g=0.2,
        added_sugar_g=0.0,
        fiber_g=0.0,
        sodium_mg=62,
        category="protein",
        notes="Protein hemat dan bernilai biologis tinggi."
    ),
    "telur_puyuh": IndonesianFoodItem(
        key="telur_puyuh",
        name="Telur Puyuh Rebus",
        default_portion="3 butir (30g)",
        calories=48,
        protein_g=3.9,
        carbs_g=0.3,
        fat_g=3.3,
        total_sugar_g=0.1,
        added_sugar_g=0.0,
        fiber_g=0.0,
        sodium_mg=42,
        category="protein"
    ),
    "tahu": IndonesianFoodItem(
        key="tahu",
        name="Tahu Goreng / Kukus",
        default_portion="2 potong sedang (100g)",
        calories=80,
        protein_g=8.0,
        carbs_g=2.0,
        fat_g=4.5,
        total_sugar_g=0.4,
        added_sugar_g=0.0,
        fiber_g=1.2,
        sodium_mg=15,
        category="protein",
        notes="Protein nabati ramah kantong."
    ),
    "tempe": IndonesianFoodItem(
        key="tempe",
        name="Tempe Goreng / Bacem / Orek",
        default_portion="2 potong sedang (60g)",
        calories=115,
        protein_g=11.5,
        carbs_g=5.5,
        fat_g=6.0,
        total_sugar_g=0.5,
        added_sugar_g=0.0,
        fiber_g=2.8,
        sodium_mg=20,
        category="protein",
        notes="Kaya serat dan protein nabati berkualitas tinggi."
    ),
    "opor": IndonesianFoodItem(
        key="opor",
        name="Opor Ayam",
        default_portion="1 potong ayam + kuah (150g)",
        calories=260,
        protein_g=21.0,
        carbs_g=4.0,
        fat_g=17.5,
        total_sugar_g=1.0,
        added_sugar_g=0.5,
        fiber_g=0.5,
        sodium_mg=420,
        category="curry"
    ),
    "ceker": IndonesianFoodItem(
        key="ceker",
        name="Ceker Ayam Masak / Pedas",
        default_portion="3 buah (60g)",
        calories=130,
        protein_g=11.5,
        carbs_g=1.0,
        fat_g=9.0,
        total_sugar_g=0.2,
        added_sugar_g=0.1,
        fiber_g=0.0,
        sodium_mg=260,
        category="protein"
    ),
    "bakso": IndonesianFoodItem(
        key="bakso",
        name="Bakso Sapi Kuah",
        default_portion="1 porsi (5 butir + kuah)",
        calories=320,
        protein_g=18.0,
        carbs_g=24.0,
        fat_g=16.0,
        total_sugar_g=2.0,
        added_sugar_g=0.5,
        fiber_g=1.0,
        sodium_mg=850,
        category="meal",
        notes="Pilih kuah bening untuk menjaga kalori tetap efisien."
    ),
    "mie_ayam": IndonesianFoodItem(
        key="mie_ayam",
        name="Mie Ayam Standar",
        default_portion="1 mangkuk sedang (250g)",
        calories=420,
        protein_g=16.0,
        carbs_g=62.0,
        fat_g=12.5,
        total_sugar_g=4.0,
        added_sugar_g=2.5,
        fiber_g=2.0,
        sodium_mg=780,
        category="meal"
    ),
    "gorengan": IndonesianFoodItem(
        key="gorengan",
        name="Gorengan (Bakwan / Tahu Isi / Pisgor)",
        default_portion="1 buah sedang (50g)",
        calories=140,
        protein_g=2.0,
        carbs_g=14.0,
        fat_g=8.5,
        total_sugar_g=1.5,
        added_sugar_g=0.5,
        fiber_g=0.8,
        sodium_mg=190,
        category="snack",
        notes="Boleh dinikmati sebagai flexible meal, perhatikan porsinya."
    ),
    "sayur_sop": IndonesianFoodItem(
        key="sayur_sop",
        name="Sayur Sop Rumahan",
        default_portion="1 mangkuk sedang (150g)",
        calories=55,
        protein_g=2.5,
        carbs_g=9.0,
        fat_g=1.0,
        total_sugar_g=3.0,
        added_sugar_g=0.0,
        fiber_g=2.5,
        sodium_mg=340,
        category="vegetable",
        notes="Rendah kalori, kaya serat dan mikronutrisi."
    ),
    "timun": IndonesianFoodItem(
        key="timun",
        name="Timun Segar",
        default_portion="1 buah / lalapan (100g)",
        calories=15,
        protein_g=0.7,
        carbs_g=3.6,
        fat_g=0.1,
        total_sugar_g=1.7,
        added_sugar_g=0.0,
        fiber_g=0.5,
        sodium_mg=2,
        category="vegetable"
    ),
    "tomat": IndonesianFoodItem(
        key="tomat",
        name="Tomat Segar",
        default_portion="1 buah sedang (100g)",
        calories=18,
        protein_g=0.9,
        carbs_g=3.9,
        fat_g=0.2,
        total_sugar_g=2.6,
        added_sugar_g=0.0,
        fiber_g=1.2,
        sodium_mg=5,
        category="vegetable"
    ),
    "selada": IndonesianFoodItem(
        key="selada",
        name="Selada Hijau",
        default_portion="1 mangkuk lalap (50g)",
        calories=8,
        protein_g=0.6,
        carbs_g=1.4,
        fat_g=0.1,
        total_sugar_g=0.4,
        added_sugar_g=0.0,
        fiber_g=0.6,
        sodium_mg=4,
        category="vegetable"
    ),
    "jambu_merah": IndonesianFoodItem(
        key="jambu_merah",
        name="Jambu Biji Merah Segar",
        default_portion="1 buah sedang (100g)",
        calories=68,
        protein_g=2.6,
        carbs_g=14.3,
        fat_g=1.0,
        total_sugar_g=8.9,
        added_sugar_g=0.0,  # CRITICAL: Gula alami dari buah utuh BUKAN added sugar
        fiber_g=5.4,
        sodium_mg=2,
        category="fruit",
        notes="Kaya vitamin C & serat tinggi. Gula alami tidak dihitung sebagai added sugar."
    ),
    "susu": IndonesianFoodItem(
        key="susu",
        name="Susu Sapi UHT Plain",
        default_portion="1 gelas (200ml)",
        calories=120,
        protein_g=6.5,
        carbs_g=9.5,
        fat_g=6.5,
        total_sugar_g=9.5,
        added_sugar_g=0.0,  # Laktosa alami
        fiber_g=0.0,
        sodium_mg=95,
        category="drink"
    ),
    "almond_milk": IndonesianFoodItem(
        key="almond_milk",
        name="Almond Milk Unsweetened",
        default_portion="1 gelas (200ml)",
        calories=40,
        protein_g=1.5,
        carbs_g=1.5,
        fat_g=3.0,
        total_sugar_g=0.2,
        added_sugar_g=0.0,
        fiber_g=1.0,
        sodium_mg=120,
        category="drink"
    ),
    "americano": IndonesianFoodItem(
        key="americano",
        name="Kopi Americano / Hitam Polos",
        default_portion="1 cangkir (200ml)",
        calories=4,
        protein_g=0.3,
        carbs_g=0.6,
        fat_g=0.0,
        total_sugar_g=0.0,
        added_sugar_g=0.0,
        fiber_g=0.0,
        sodium_mg=5,
        category="drink",
        notes="Tanpa gula dan kalori minimal, aman sebelum olahraga."
    ),
    "teh": IndonesianFoodItem(
        key="teh",
        name="Teh Manis Hangat",
        default_portion="1 cangkir (200ml)",
        calories=70,
        protein_g=0.0,
        carbs_g=17.5,
        fat_g=0.0,
        total_sugar_g=17.0,
        added_sugar_g=17.0,  # Added sugar dari gula pasir
        fiber_g=0.0,
        sodium_mg=2,
        category="drink",
        notes="Mengandung gula pasir tambahan (added sugar)."
    ),
    "jamu_kunyit_asam": IndonesianFoodItem(
        key="jamu_kunyit_asam",
        name="Jamu Kunyit Asam",
        default_portion="1 gelas (200ml)",
        calories=85,
        protein_g=0.5,
        carbs_g=21.0,
        fat_g=0.2,
        total_sugar_g=18.0,
        added_sugar_g=12.0,  # Gula aren/jawa tambahan
        fiber_g=0.5,
        sodium_mg=12,
        category="drink",
        notes="Segar dan berkhasiat, diolah dengan sedikit gula aren."
    )
}


def search_food(query: str) -> list[IndonesianFoodItem]:
    """Fuzzy-search food items in the Indonesian database."""
    q = query.lower().strip()
    results = []
    for item in INDONESIAN_FOOD_DATABASE.values():
        if q in item.key or q in item.name.lower() or q in item.category:
            results.append(item)
    return results


def get_food_by_key(key: str) -> IndonesianFoodItem | None:
    return INDONESIAN_FOOD_DATABASE.get(key)
