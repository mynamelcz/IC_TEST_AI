import pytest

from ..conftest import reset_pin_pair
from ..utils.gpio_helper import GpioHelper


ROLES = [
    ("MCU-A_stim", "MCU-B_dut"),
    ("MCU-B_stim", "MCU-A_dut"),
]


def _resolve(role, gpio_a, gpio_b, pin_pair):
    """Return (stim_gpio, stim_port, stim_pin, dut_gpio, dut_port, dut_pin, dut_name)."""
    stim_label, dut_label = role
    if stim_label.startswith("MCU-A"):
        return (gpio_a, pin_pair.mcu_a_port, pin_pair.mcu_a_pin,
                gpio_b, pin_pair.mcu_b_port, pin_pair.mcu_b_pin,
                "MCU-B")
    return (gpio_b, pin_pair.mcu_b_port, pin_pair.mcu_b_pin,
            gpio_a, pin_pair.mcu_a_port, pin_pair.mcu_a_pin,
            "MCU-A")


def _pin_id(pin_pair, role):
    """Generate a readable test ID string."""
    stim_label, dut_label = role
    dut_name = "MCU-B" if stim_label.startswith("MCU-A") else "MCU-A"
    if dut_name == "MCU-B":
        return f"{dut_name}-P{pin_pair.label_b}"
    return f"{dut_name}-P{pin_pair.label_a}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_output_high(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-01: DUT outputs HIGH, stimulator reads and verifies."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_INPUT)
        stim.set_pull(sp, spin, GpioHelper.PULL_NONE)

        dut.set_mode(dp, dpin, GpioHelper.MODE_OUTPUT)
        dut.write_pin(dp, dpin, 1)

        actual = stim.read_pin(sp, spin)
        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-01"))
        request.node.user_properties.append(("test_name", "output_high"))
        request.node.user_properties.append(("expected", "1"))
        request.node.user_properties.append(("actual", str(actual)))
        assert actual == 1, f"G-01 {pin_label}: expected HIGH(1), got {actual}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_output_low(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-02: DUT outputs LOW, stimulator reads and verifies."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_INPUT)
        stim.set_pull(sp, spin, GpioHelper.PULL_NONE)

        dut.set_mode(dp, dpin, GpioHelper.MODE_OUTPUT)
        dut.write_pin(dp, dpin, 0)

        actual = stim.read_pin(sp, spin)
        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-02"))
        request.node.user_properties.append(("test_name", "output_low"))
        request.node.user_properties.append(("expected", "0"))
        request.node.user_properties.append(("actual", str(actual)))
        assert actual == 0, f"G-02 {pin_label}: expected LOW(0), got {actual}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_input_read_high(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-03: Stimulator outputs HIGH, DUT reads and verifies."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_OUTPUT)
        stim.write_pin(sp, spin, 1)

        dut.set_mode(dp, dpin, GpioHelper.MODE_INPUT)
        dut.set_pull(dp, dpin, GpioHelper.PULL_NONE)

        actual = dut.read_pin(dp, dpin)
        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-03"))
        request.node.user_properties.append(("test_name", "input_read_high"))
        request.node.user_properties.append(("expected", "1"))
        request.node.user_properties.append(("actual", str(actual)))
        assert actual == 1, f"G-03 {pin_label}: expected HIGH(1), got {actual}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_input_read_low(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-04: Stimulator outputs LOW, DUT reads and verifies."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_OUTPUT)
        stim.write_pin(sp, spin, 0)

        dut.set_mode(dp, dpin, GpioHelper.MODE_INPUT)
        dut.set_pull(dp, dpin, GpioHelper.PULL_NONE)

        actual = dut.read_pin(dp, dpin)
        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-04"))
        request.node.user_properties.append(("test_name", "input_read_low"))
        request.node.user_properties.append(("expected", "0"))
        request.node.user_properties.append(("actual", str(actual)))
        assert actual == 0, f"G-04 {pin_label}: expected LOW(0), got {actual}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_pull_up(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-05: Stimulator floating, DUT pull-up reads HIGH."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_INPUT)
        stim.set_pull(sp, spin, GpioHelper.PULL_NONE)

        dut.set_mode(dp, dpin, GpioHelper.MODE_INPUT)
        dut.set_pull(dp, dpin, GpioHelper.PULL_UP)

        actual = dut.read_pin(dp, dpin)
        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-05"))
        request.node.user_properties.append(("test_name", "pull_up"))
        request.node.user_properties.append(("expected", "1"))
        request.node.user_properties.append(("actual", str(actual)))
        assert actual == 1, f"G-05 {pin_label}: expected HIGH(1) with pull-up, got {actual}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_pull_down(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-06: Stimulator floating, DUT pull-down reads LOW."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_INPUT)
        stim.set_pull(sp, spin, GpioHelper.PULL_NONE)

        dut.set_mode(dp, dpin, GpioHelper.MODE_INPUT)
        dut.set_pull(dp, dpin, GpioHelper.PULL_DOWN)

        actual = dut.read_pin(dp, dpin)
        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-06"))
        request.node.user_properties.append(("test_name", "pull_down"))
        request.node.user_properties.append(("expected", "0"))
        request.node.user_properties.append(("actual", str(actual)))
        assert actual == 0, f"G-06 {pin_label}: expected LOW(0) with pull-down, got {actual}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_open_drain(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-07: DUT open-drain output, stimulator with pull-up reads."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_INPUT)
        stim.set_pull(sp, spin, GpioHelper.PULL_UP)

        dut.set_mode(dp, dpin, GpioHelper.MODE_OUTPUT)
        dut.set_output_type(dp, dpin, GpioHelper.OTYPE_OPEN_DRAIN)
        dut.write_pin(dp, dpin, 0)

        actual_low = stim.read_pin(sp, spin)

        dut.write_pin(dp, dpin, 1)
        actual_high = stim.read_pin(sp, spin)

        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-07"))
        request.node.user_properties.append(("test_name", "open_drain"))
        request.node.user_properties.append(("expected", "low=0,high=1"))
        request.node.user_properties.append(("actual", f"low={actual_low},high={actual_high}"))
        assert actual_low == 0, f"G-07 {pin_label}: OD low expected 0, got {actual_low}"
        assert actual_high == 1, f"G-07 {pin_label}: OD high expected 1, got {actual_high}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_rising_edge_interrupt(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-08: Stimulator LOW->HIGH, DUT checks rising edge interrupt."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_OUTPUT)
        stim.write_pin(sp, spin, 0)

        dut.set_mode(dp, dpin, GpioHelper.MODE_INPUT)
        dut.configure_exti(dp, dpin, rising=True, falling=False)
        dut.clear_exti_pending(dpin)

        stim.write_pin(sp, spin, 1)

        pending = dut.read_exti_pending(dpin)
        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-08"))
        request.node.user_properties.append(("test_name", "rising_edge_interrupt"))
        request.node.user_properties.append(("expected", "True"))
        request.node.user_properties.append(("actual", str(pending)))
        assert pending, f"G-08 {pin_label}: rising edge interrupt not triggered"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_falling_edge_interrupt(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-09: Stimulator HIGH->LOW, DUT checks falling edge interrupt."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_OUTPUT)
        stim.write_pin(sp, spin, 1)

        dut.set_mode(dp, dpin, GpioHelper.MODE_INPUT)
        dut.configure_exti(dp, dpin, rising=False, falling=True)
        dut.clear_exti_pending(dpin)

        stim.write_pin(sp, spin, 0)

        pending = dut.read_exti_pending(dpin)
        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-09"))
        request.node.user_properties.append(("test_name", "falling_edge_interrupt"))
        request.node.user_properties.append(("expected", "True"))
        request.node.user_properties.append(("actual", str(pending)))
        assert pending, f"G-09 {pin_label}: falling edge interrupt not triggered"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_both_edge_interrupt(role, gpio_a, gpio_b, all_pin_pairs, request):
    """G-10: Stimulator toggles, DUT checks both-edge interrupt count."""
    for pp in all_pin_pairs:
        stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
        reset_pin_pair(gpio_a, gpio_b, pp)

        stim.set_mode(sp, spin, GpioHelper.MODE_OUTPUT)
        stim.write_pin(sp, spin, 0)

        dut.set_mode(dp, dpin, GpioHelper.MODE_INPUT)
        dut.configure_exti(dp, dpin, rising=True, falling=True)
        dut.clear_exti_pending(dpin)

        # Toggle: LOW->HIGH (rising)
        stim.write_pin(sp, spin, 1)
        pending_rise = dut.read_exti_pending(dpin)
        dut.clear_exti_pending(dpin)

        # Toggle: HIGH->LOW (falling)
        stim.write_pin(sp, spin, 0)
        pending_fall = dut.read_exti_pending(dpin)

        pin_label = _pin_id(pp, role)
        request.node.user_properties.append(("chip", dname))
        request.node.user_properties.append(("pin", pin_label))
        request.node.user_properties.append(("test_id", "G-10"))
        request.node.user_properties.append(("test_name", "both_edge_interrupt"))
        request.node.user_properties.append(("expected", "rise=True,fall=True"))
        request.node.user_properties.append(("actual", f"rise={pending_rise},fall={pending_fall}"))
        assert pending_rise, f"G-10 {pin_label}: rising edge not triggered"
        assert pending_fall, f"G-10 {pin_label}: falling edge not triggered"
