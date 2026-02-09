# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IC_TEST_AI is a Python-based automated testing framework for RISC-V MCU digital peripherals. It uses a dual-MCU architecture where two MCUs test each other's peripherals through pin-to-pin connections, controlled via JTAG from a PC.

**Architecture:**
```
PC (Python + pytest)
    |
    +-- JTAG-A (FT232H) --> MCU-A (Stimulator/DUT)
    |
    +-- JTAG-B (FT232H) --> MCU-B (DUT/Stimulator)
                             |
                    pin-to-pin connection
```

**Two test modes:**
- **Pure JTAG mode**: Direct register access (currently used for GPIO tests)
- **Firmware mode**: Download test firmware, run, read results via JTAG (planned)

## Common Commands

```bash
# Install dependencies
pip install pytest pyyaml

# Run all GPIO tests with mock mode (no hardware required)
pytest ic_test/tests/test_gpio.py --use-mock -v

# Run single test
pytest ic_test/tests/test_gpio.py::test_output_high -v --use-mock

# Run with CSV report
pytest ic_test/tests/test_gpio.py --use-mock --csv-report=gpio_report.csv -v

# Run with HTML report
pytest ic_test/tests/test_gpio.py --use-mock --html=report.html --self-contained-html

# Use real JTAG probes (default: FT232H-A, FT232H-B)
pytest ic_test/tests/test_gpio.py --jtag-a=FT232H-A --jtag-b=FT232H-B -v
```

## Key Architecture Components

### Driver Layer (`ic_test/drivers/`)
- `chip_interface.py`: Abstract base class (`ChipInterface`) defining register/memory operations
- `jtag_impl.py`: Contains `JtagImpl` (skeleton for real JTAG tools) and `MockJtagImpl` (fully functional mock for testing without hardware)

### Utility Layer (`ic_test/utils/`)
- `gpio_helper.py`: High-level GPIO operations (set_mode, set_pull, read/write_pin, configure_exti, bsrr_set/reset, etc.)
- `reg_parser.py`: Parses YAML config files into dataclasses
- `report.py`: CSV report plugin for pytest

### Configuration (`ic_test/config/`)
- `regs/gpio.yaml`: GPIO register definitions
- `pin_map.yaml`: Pin mapping between MCU-A and MCU-B (44 pin pairs)

### Tests (`ic_test/tests/`)
- `test_gpio.py`: 16 GPIO test cases (G-01 ~ G-16), each runs in both roles (A stim/B dut, B stim/A dut)
- `conftest.py`: Pytest fixtures including automatic pin_pair parametrization

## Role Swapping Pattern

Tests use `@pytest.mark.parametrize("role", ROLES)` with `ROLES = [("MCU-A_stim", "MCU-B_dut"), ("MCU-B_stim", "MCU-A_dut")]` to ensure both MCUs are tested as both stimulator and DUT.

Internal function `_resolve(role, gpio_a, gpio_b, pin_pair)` parses role and returns the appropriate GPIO helper instances.

## Adding New Tests

1. **Create peripheral YAML config** in `config/regs/<peripheral>.yaml`
2. **Add parser functions** in `utils/reg_parser.py`
3. **Create helper class** in `utils/<peripheral>_helper.py`
4. **Create test file** in `tests/test_<peripheral>.py`
5. **Use role swapping pattern** with parametrization for comprehensive coverage

## Current Status

- **GPIO tests**: 16 test cases fully implemented (1672 test variants including pin/role combinations)
- **Mock implementation**: Complete and functional
- **Real JTAG driver**: Skeleton (NotImplementedError) - needs pyftdi/OpenOCD integration
- **Planned peripherals**: UART, SPI, I2C, Timer, ADC, DAC, DMA
