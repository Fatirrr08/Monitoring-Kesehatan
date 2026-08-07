from aiogram.fsm.state import State, StatesGroup


class ProfileState(StatesGroup):
    editing_weight = State()
    editing_target = State()
    editing_protein = State()
    editing_sugar = State()


class FoodState(StatesGroup):
    waiting_food_text = State()
    waiting_food_photo = State()
    waiting_label_photo = State()
    confirming_food = State()
    editing_portion = State()


class ActivityState(StatesGroup):
    waiting_activity_input = State()


class WeightState(StatesGroup):
    waiting_weight_input = State()


class SleepState(StatesGroup):
    waiting_sleep_input = State()


class WaterState(StatesGroup):
    waiting_water_input = State()


class CoachState(StatesGroup):
    chatting = State()
