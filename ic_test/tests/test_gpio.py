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
def test_output_high(role, gpio_a, gpio_b, pin_pair, request):
    """G-01: DUT outputs HIGH, stimulator reads and verifies."""
    pp = pin_pair
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
def test_output_low(role, gpio_a, gpio_b, pin_pair, request):
    """G-02: DUT outputs LOW, stimulator reads and verifies."""
    pp = pin_pair
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
def test_input_read_high(role, gpio_a, gpio_b, pin_pair, request):
    """G-03: Stimulator outputs HIGH, DUT reads and verifies."""
    pp = pin_pair
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
def test_input_read_low(role, gpio_a, gpio_b, pin_pair, request):
    """G-04: Stimulator outputs LOW, DUT reads and verifies."""
    pp = pin_pair
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
def test_pull_up(role, gpio_a, gpio_b, pin_pair, request):
    """G-05: Stimulator floating, DUT pull-up reads HIGH."""
    pp = pin_pair
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
def test_pull_down(role, gpio_a, gpio_b, pin_pair, request):
    """G-06: Stimulator floating, DUT pull-down reads LOW."""
    pp = pin_pair
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
def test_open_drain(role, gpio_a, gpio_b, pin_pair, request):
    """G-07: DUT open-drain output, stimulator with pull-up reads."""
    pp = pin_pair
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
def test_rising_edge_interrupt(role, gpio_a, gpio_b, pin_pair, request):
    """G-08: Stimulator LOW->HIGH, DUT checks rising edge interrupt."""
    pp = pin_pair
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
def test_falling_edge_interrupt(role, gpio_a, gpio_b, pin_pair, request):
    """G-09: Stimulator HIGH->LOW, DUT checks falling edge interrupt."""
    pp = pin_pair
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
def test_both_edge_interrupt(role, gpio_a, gpio_b, pin_pair, request):
    """G-10: Stimulator toggles, DUT checks both-edge interrupt count."""
    pp = pin_pair
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


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_bsrr_set(role, gpio_a, gpio_b, pin_pair, request):
    """G-11: DUT sets pin HIGH via BSRR atomic set, stimulator verifies."""
    pp = pin_pair
    stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
    reset_pin_pair(gpio_a, gpio_b, pp)

    stim.set_mode(sp, spin, GpioHelper.MODE_INPUT)
    stim.set_pull(sp, spin, GpioHelper.PULL_NONE)

    dut.set_mode(dp, dpin, GpioHelper.MODE_OUTPUT)
    dut.write_pin(dp, dpin, 0)
    dut.bsrr_set(dp, dpin)

    actual = stim.read_pin(sp, spin)
    pin_label = _pin_id(pp, role)
    request.node.user_properties.append(("chip", dname))
    request.node.user_properties.append(("pin", pin_label))
    request.node.user_properties.append(("test_id", "G-11"))
    request.node.user_properties.append(("test_name", "bsrr_set"))
    request.node.user_properties.append(("expected", "1"))
    request.node.user_properties.append(("actual", str(actual)))
    assert actual == 1, f"G-11 {pin_label}: BSRR set expected HIGH(1), got {actual}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_bsrr_reset(role, gpio_a, gpio_b, pin_pair, request):
    """G-12: DUT resets pin LOW via BSRR atomic reset, stimulator verifies."""
    pp = pin_pair
    stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
    reset_pin_pair(gpio_a, gpio_b, pp)

    stim.set_mode(sp, spin, GpioHelper.MODE_INPUT)
    stim.set_pull(sp, spin, GpioHelper.PULL_NONE)

    dut.set_mode(dp, dpin, GpioHelper.MODE_OUTPUT)
    dut.write_pin(dp, dpin, 1)
    dut.bsrr_reset(dp, dpin)

    actual = stim.read_pin(sp, spin)
    pin_label = _pin_id(pp, role)
    request.node.user_properties.append(("chip", dname))
    request.node.user_properties.append(("pin", pin_label))
    request.node.user_properties.append(("test_id", "G-12"))
    request.node.user_properties.append(("test_name", "bsrr_reset"))
    request.node.user_properties.append(("expected", "0"))
    request.node.user_properties.append(("actual", str(actual)))
    assert actual == 0, f"G-12 {pin_label}: BSRR reset expected LOW(0), got {actual}"


SPEED_VALUES = [
    GpioHelper.SPEED_LOW,
    GpioHelper.SPEED_MEDIUM,
    GpioHelper.SPEED_HIGH,
    GpioHelper.SPEED_VERY_HIGH,
]
SPEED_IDS = ["low", "medium", "high", "very_high"]


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
@pytest.mark.parametrize("speed_val", SPEED_VALUES, ids=SPEED_IDS)
def test_ospeedr_readback(role, speed_val, gpio_a, gpio_b, pin_pair, request):
    """G-13: Write OSPEEDR speed value, read back and verify."""
    pp = pin_pair
    _, _, _, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
    reset_pin_pair(gpio_a, gpio_b, pp)

    dut.set_mode(dp, dpin, GpioHelper.MODE_OUTPUT)
    dut.set_speed(dp, dpin, speed_val)
    actual = dut.read_speed(dp, dpin)

    pin_label = _pin_id(pp, role)
    request.node.user_properties.append(("chip", dname))
    request.node.user_properties.append(("pin", pin_label))
    request.node.user_properties.append(("test_id", "G-13"))
    request.node.user_properties.append(("test_name", "ospeedr_readback"))
    request.node.user_properties.append(("expected", str(speed_val)))
    request.node.user_properties.append(("actual", str(actual)))
    assert actual == speed_val, (
        f"G-13 {pin_label}: OSPEEDR expected {speed_val}, got {actual}"
    )


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_odr_readback(role, gpio_a, gpio_b, pin_pair, request):
    """G-14: Write ODR bit, read back via read_odr and verify."""
    pp = pin_pair
    _, _, _, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
    reset_pin_pair(gpio_a, gpio_b, pp)

    dut.set_mode(dp, dpin, GpioHelper.MODE_OUTPUT)

    dut.write_pin(dp, dpin, 1)
    actual_high = dut.read_odr(dp, dpin)

    dut.write_pin(dp, dpin, 0)
    actual_low = dut.read_odr(dp, dpin)

    pin_label = _pin_id(pp, role)
    request.node.user_properties.append(("chip", dname))
    request.node.user_properties.append(("pin", pin_label))
    request.node.user_properties.append(("test_id", "G-14"))
    request.node.user_properties.append(("test_name", "odr_readback"))
    request.node.user_properties.append(("expected", "high=1,low=0"))
    request.node.user_properties.append(("actual", f"high={actual_high},low={actual_low}"))
    assert actual_high == 1, f"G-14 {pin_label}: ODR readback expected 1, got {actual_high}"
    assert actual_low == 0, f"G-14 {pin_label}: ODR readback expected 0, got {actual_low}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_exti_disabled(role, gpio_a, gpio_b, pin_pair, request):
    """G-15: EXTI disabled (IMR=0), edge should not set pending flag."""
    pp = pin_pair
    stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
    reset_pin_pair(gpio_a, gpio_b, pp)

    stim.set_mode(sp, spin, GpioHelper.MODE_OUTPUT)
    stim.write_pin(sp, spin, 0)

    dut.set_mode(dp, dpin, GpioHelper.MODE_INPUT)
    dut.configure_exti(dp, dpin, rising=True, falling=True)
    dut.clear_exti_pending(dpin)
    dut.disable_exti(dp, dpin)

    # Produce a rising edge
    stim.write_pin(sp, spin, 1)

    pending = dut.read_exti_pending(dpin)
    pin_label = _pin_id(pp, role)
    request.node.user_properties.append(("chip", dname))
    request.node.user_properties.append(("pin", pin_label))
    request.node.user_properties.append(("test_id", "G-15"))
    request.node.user_properties.append(("test_name", "exti_disabled"))
    request.node.user_properties.append(("expected", "False"))
    request.node.user_properties.append(("actual", str(pending)))
    assert not pending, f"G-15 {pin_label}: EXTI should be disabled but pending={pending}"


@pytest.mark.parametrize("role", ROLES, ids=["A_stim-B_dut", "B_stim-A_dut"])
def test_open_drain_pull_down(role, gpio_a, gpio_b, pin_pair, request):
    """G-16: DUT open-drain with stimulator pull-down. OD write 0 reads 0, OD write 1 (release) pull-down reads 0."""
    pp = pin_pair
    stim, sp, spin, dut, dp, dpin, dname = _resolve(role, gpio_a, gpio_b, pp)
    reset_pin_pair(gpio_a, gpio_b, pp)

    stim.set_mode(sp, spin, GpioHelper.MODE_INPUT)
    stim.set_pull(sp, spin, GpioHelper.PULL_DOWN)

    dut.set_mode(dp, dpin, GpioHelper.MODE_OUTPUT)
    dut.set_output_type(dp, dpin, GpioHelper.OTYPE_OPEN_DRAIN)

    dut.write_pin(dp, dpin, 0)
    actual_low = stim.read_pin(sp, spin)

    dut.write_pin(dp, dpin, 1)
    actual_release = stim.read_pin(sp, spin)

    pin_label = _pin_id(pp, role)
    request.node.user_properties.append(("chip", dname))
    request.node.user_properties.append(("pin", pin_label))
    request.node.user_properties.append(("test_id", "G-16"))
    request.node.user_properties.append(("test_name", "open_drain_pull_down"))
    request.node.user_properties.append(("expected", "low=0,release=0"))
    request.node.user_properties.append(("actual", f"low={actual_low},release={actual_release}"))
    assert actual_low == 0, f"G-16 {pin_label}: OD low expected 0, got {actual_low}"
    assert actual_release == 0, f"G-16 {pin_label}: OD release with pull-down expected 0, got {actual_release}"
