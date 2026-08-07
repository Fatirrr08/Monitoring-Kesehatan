import pytest
from app.bot.bot import create_dispatcher, create_bot


def test_dispatcher_routers_registration():
    dp = create_dispatcher()
    assert dp is not None
    # Verify sub routers are included
    router_names = [r.name for r in dp.sub_routers]
    assert "start_router" in router_names
    assert "dashboard_router" in router_names
    assert "food_router" in router_names
    assert "activity_router" in router_names
    assert "weight_router" in router_names
    assert "sleep_router" in router_names
    assert "water_router" in router_names
    assert "statistics_router" in router_names
    assert "coach_router" in router_names


def test_bot_instance():
    bot = create_bot()
    assert bot is not None
    assert bot.token.startswith("123456789:")
