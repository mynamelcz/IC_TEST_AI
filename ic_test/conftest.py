from pathlib import Path

import pytest

from .drivers.jtag_impl import JtagImpl, MockJtagImpl
from .utils.reg_parser import load_gpio_regs, load_pin_map
from .utils.gpio_helper import GpioHelper
from .utils.report import CsvReportPlugin

_CONFIG_DIR = Path(__file__).parent / "config"


def pytest_configure(config):
    csv_path = config.getoption("--csv-report", default=None)
    if csv_path:
        plugin = CsvReportPlugin(csv_path)
        config.pluginmanager.register(plugin, "csv_report")


def pytest_addoption(parser):
    parser.addoption("--use-mock", action="store_true", default=False,
                     help="Use mock JTAG implementation")
    parser.addoption("--jtag-a", default="FT232H-A",
                     help="JTAG probe ID for MCU-A")
    parser.addoption("--jtag-b", default="FT232H-B",
                     help="JTAG probe ID for MCU-B")
    parser.addoption("--csv-report", default=None,
                     help="Path to CSV report output file")


@pytest.fixture(scope="session")
def gpio_reg_map():
    return load_gpio_regs(_CONFIG_DIR / "regs" / "gpio.yaml")


@pytest.fixture(scope="session")
def pin_map():
    return load_pin_map(_CONFIG_DIR / "pin_map.yaml")


@pytest.fixture(scope="session")
def mcu_a(request):
    use_mock = request.config.getoption("--use-mock")
    probe_id = request.config.getoption("--jtag-a")
    if use_mock:
        return MockJtagImpl(probe_id, name="MCU-A")
    return JtagImpl(probe_id, name="MCU-A")


@pytest.fixture(scope="session")
def mcu_b(request, mcu_a):
    use_mock = request.config.getoption("--use-mock")
    probe_id = request.config.getoption("--jtag-b")
    if use_mock:
        b = MockJtagImpl(probe_id, name="MCU-B")
        mcu_a.set_peer(b)
        return b
    return JtagImpl(probe_id, name="MCU-B")


@pytest.fixture(scope="session")
def gpio_a(mcu_a, gpio_reg_map):
    return GpioHelper(mcu_a, gpio_reg_map)


@pytest.fixture(scope="session")
def gpio_b(mcu_b, gpio_reg_map):
    return GpioHelper(mcu_b, gpio_reg_map)


@pytest.fixture(scope="session")
def all_pin_pairs(pin_map):
    return pin_map.pin_pairs


def _pin_pair_id(pp):
    """Generate short ID like A0, B5, C15 from a PinPair."""
    port_letter = pp.mcu_a_port[-1]  # 'A', 'B', 'C'
    return f"{port_letter}{pp.mcu_a_pin}"


def pytest_generate_tests(metafunc):
    """Auto-parametrize tests that request the 'pin_pair' fixture."""
    if "pin_pair" in metafunc.fixturenames:
        pin_map_cfg = load_pin_map(_CONFIG_DIR / "pin_map.yaml")
        pairs = pin_map_cfg.pin_pairs
        ids = [_pin_pair_id(pp) for pp in pairs]
        metafunc.parametrize("pin_pair", pairs, ids=ids, scope="function")


def reset_pin_pair(gpio_a, gpio_b, pin_pair):
    """Reset both sides of a pin pair to default state."""
    gpio_a.reset_pin(pin_pair.mcu_a_port, pin_pair.mcu_a_pin)
    gpio_b.reset_pin(pin_pair.mcu_b_port, pin_pair.mcu_b_pin)
