from ..drivers.chip_interface import ChipInterface
from .reg_parser import GpioRegMap


class GpioHelper:
    """High-level GPIO register operations."""

    # Pin modes (MODER)
    MODE_INPUT = 0
    MODE_OUTPUT = 1
    MODE_AF = 2
    MODE_ANALOG = 3

    # Output types (OTYPER)
    OTYPE_PUSH_PULL = 0
    OTYPE_OPEN_DRAIN = 1

    # Pull resistors (PUPDR)
    PULL_NONE = 0
    PULL_UP = 1
    PULL_DOWN = 2

    def __init__(self, chip: ChipInterface, reg_map: GpioRegMap):
        self.chip = chip
        self.reg_map = reg_map

    def set_mode(self, port: str, pin: int, mode: int) -> None:
        """Set pin mode (input/output/AF/analog)."""
        addr = self.reg_map.get_reg_addr(port, "MODER")
        self.chip.reg_write_field(addr, pin * 2, 2, mode)

    def set_output_type(self, port: str, pin: int, otype: int) -> None:
        """Set output type (push-pull / open-drain)."""
        addr = self.reg_map.get_reg_addr(port, "OTYPER")
        self.chip.reg_write_field(addr, pin, 1, otype)

    def set_pull(self, port: str, pin: int, pull: int) -> None:
        """Set pull-up/pull-down resistor."""
        addr = self.reg_map.get_reg_addr(port, "PUPDR")
        self.chip.reg_write_field(addr, pin * 2, 2, pull)

    def write_pin(self, port: str, pin: int, value: int) -> None:
        """Write output level (0 or 1)."""
        addr = self.reg_map.get_reg_addr(port, "ODR")
        self.chip.reg_write_field(addr, pin, 1, value & 1)

    def read_pin(self, port: str, pin: int) -> int:
        """Read input level (0 or 1)."""
        addr = self.reg_map.get_reg_addr(port, "IDR")
        return self.chip.reg_read_field(addr, pin, 1)

    def reset_pin(self, port: str, pin: int) -> None:
        """Reset pin to default state (input, no pull, push-pull)."""
        self.set_mode(port, pin, self.MODE_INPUT)
        self.set_output_type(port, pin, self.OTYPE_PUSH_PULL)
        self.set_pull(port, pin, self.PULL_NONE)
        self.write_pin(port, pin, 0)

    def configure_exti(self, port: str, pin: int, rising: bool, falling: bool) -> None:
        """Configure EXTI interrupt for a pin."""
        exti = self.reg_map.exti
        if exti is None:
            raise ValueError("EXTI not defined in register map")

        # Enable interrupt mask
        imr_addr = exti.base_addr + exti.imr_offset
        self.chip.reg_write_field(imr_addr, pin, 1, 1)

        # Configure rising edge
        rtsr_addr = exti.base_addr + exti.rtsr_offset
        self.chip.reg_write_field(rtsr_addr, pin, 1, 1 if rising else 0)

        # Configure falling edge
        ftsr_addr = exti.base_addr + exti.ftsr_offset
        self.chip.reg_write_field(ftsr_addr, pin, 1, 1 if falling else 0)

    def read_exti_pending(self, pin: int) -> bool:
        """Read EXTI pending flag for a pin."""
        exti = self.reg_map.exti
        if exti is None:
            raise ValueError("EXTI not defined in register map")
        pr_addr = exti.base_addr + exti.pr_offset
        return bool(self.chip.reg_read_field(pr_addr, pin, 1))

    def clear_exti_pending(self, pin: int) -> None:
        """Clear EXTI pending flag (write-1-to-clear)."""
        exti = self.reg_map.exti
        if exti is None:
            raise ValueError("EXTI not defined in register map")
        pr_addr = exti.base_addr + exti.pr_offset
        self.chip.reg_write(pr_addr, 1 << pin)
