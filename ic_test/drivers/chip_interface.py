from abc import ABC, abstractmethod


class JtagError(Exception):
    """JTAG communication error."""
    pass


class ChipInterface(ABC):
    """Abstract base class for chip operations via JTAG."""

    def __init__(self, probe_id: str, name: str = ""):
        self.probe_id = probe_id
        self.name = name or probe_id

    @abstractmethod
    def reg_read(self, addr: int) -> int:
        """Read a 32-bit register."""
        ...

    @abstractmethod
    def reg_write(self, addr: int, value: int) -> None:
        """Write a 32-bit register."""
        ...

    def reg_read_field(self, addr: int, bit_offset: int, bit_width: int) -> int:
        """Read a bit field from a register."""
        val = self.reg_read(addr)
        mask = (1 << bit_width) - 1
        return (val >> bit_offset) & mask

    def reg_write_field(self, addr: int, bit_offset: int, bit_width: int, value: int) -> None:
        """Read-modify-write a bit field in a register."""
        reg_val = self.reg_read(addr)
        mask = ((1 << bit_width) - 1) << bit_offset
        reg_val = (reg_val & ~mask) | ((value << bit_offset) & mask)
        self.reg_write(addr, reg_val)

    @abstractmethod
    def mem_read(self, addr: int, size: int) -> bytes:
        """Read a block of memory."""
        ...

    @abstractmethod
    def mem_write(self, addr: int, data: bytes) -> None:
        """Write a block of memory."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset the MCU."""
        ...

    @abstractmethod
    def halt(self) -> None:
        """Halt the MCU."""
        ...

    @abstractmethod
    def run(self) -> None:
        """Resume MCU execution."""
        ...

    @abstractmethod
    def download_firmware(self, path: str) -> None:
        """Download firmware to the MCU."""
        ...
