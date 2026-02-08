import time
from collections import defaultdict

from .chip_interface import ChipInterface, JtagError


class JtagImpl(ChipInterface):
    """Real JTAG driver skeleton. Methods raise NotImplementedError
    until a concrete toolchain (e.g. pyftdi / OpenOCD) is integrated."""

    MAX_RETRIES = 3
    RETRY_DELAY = 0.05  # seconds

    def _retry(self, func, *args):
        """Execute *func* with up to MAX_RETRIES attempts."""
        last_err = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args)
            except JtagError as e:
                last_err = e
                time.sleep(self.RETRY_DELAY)
        raise JtagError(
            f"{self.name}: operation failed after {self.MAX_RETRIES} retries: {last_err}"
        )

    def reg_read(self, addr: int) -> int:
        raise NotImplementedError("Real JTAG reg_read not yet implemented")

    def reg_write(self, addr: int, value: int) -> None:
        raise NotImplementedError("Real JTAG reg_write not yet implemented")

    def mem_read(self, addr: int, size: int) -> bytes:
        raise NotImplementedError("Real JTAG mem_read not yet implemented")

    def mem_write(self, addr: int, data: bytes) -> None:
        raise NotImplementedError("Real JTAG mem_write not yet implemented")

    def reset(self) -> None:
        raise NotImplementedError("Real JTAG reset not yet implemented")

    def halt(self) -> None:
        raise NotImplementedError("Real JTAG halt not yet implemented")

    def run(self) -> None:
        raise NotImplementedError("Real JTAG run not yet implemented")

    def download_firmware(self, path: str) -> None:
        raise NotImplementedError("Real JTAG download_firmware not yet implemented")


# ---------------------------------------------------------------------------
# GPIO register layout constants used by MockJtagImpl
# ---------------------------------------------------------------------------
_MODER_OFFSET = 0x00
_OTYPER_OFFSET = 0x04
_PUPDR_OFFSET = 0x0C
_IDR_OFFSET = 0x10
_ODR_OFFSET = 0x14

# EXTI register offsets (relative to EXTI base)
_EXTI_BASE = 0x40013C00
_EXTI_IMR = 0x00
_EXTI_RTSR = 0x08
_EXTI_FTSR = 0x0C
_EXTI_PR = 0x14

# GPIO port bases used to identify which port an address belongs to
_PORT_BASES = [0x40020000, 0x40020400, 0x40020800]
_PORT_SIZE = 0x400


class MockJtagImpl(ChipInterface):
    """Mock JTAG implementation that simulates GPIO register behaviour
    using an in-memory dict.  Two instances can be linked via *set_peer*
    so that one MCU's output is visible as the other's input."""

    def __init__(self, probe_id: str, name: str = ""):
        super().__init__(probe_id, name)
        self._regs: dict[int, int] = defaultdict(int)
        self._mem: dict[int, int] = {}
        self._peer: "MockJtagImpl | None" = None
        # Track previous ODR values per port for EXTI edge detection
        self._prev_odr: dict[int, int] = defaultdict(int)

    def set_peer(self, other: "MockJtagImpl") -> None:
        """Link two mock instances so they can see each other's outputs."""
        self._peer = other
        other._peer = self

    # -- helpers -------------------------------------------------------------

    def _is_gpio_addr(self, addr: int) -> bool:
        for base in _PORT_BASES:
            if base <= addr < base + _PORT_SIZE:
                return True
        return False

    def _port_base_of(self, addr: int) -> int | None:
        for base in _PORT_BASES:
            if base <= addr < base + _PORT_SIZE:
                return base
        return None

    def _get_pin_mode(self, port_base: int, pin: int) -> int:
        """Return 2-bit MODER value for a pin (0=input,1=output,2=AF,3=analog)."""
        moder = self._regs[port_base + _MODER_OFFSET]
        return (moder >> (pin * 2)) & 0x3

    def _get_pull(self, port_base: int, pin: int) -> int:
        """Return 2-bit PUPDR value (0=none,1=up,2=down)."""
        pupdr = self._regs[port_base + _PUPDR_OFFSET]
        return (pupdr >> (pin * 2)) & 0x3

    def _compute_idr(self, port_base: int) -> int:
        """Compute the IDR value for a GPIO port based on peer's ODR
        and local MODER/PUPDR settings."""
        idr = 0
        for pin in range(16):
            mode = self._get_pin_mode(port_base, pin)
            bit = self._compute_pin_input(port_base, pin, mode)
            if bit:
                idr |= (1 << pin)
        return idr

    def _compute_pin_input(self, port_base: int, pin: int, mode: int) -> int:
        """Compute what a single pin reads as input.

        Logic:
        - If this pin is output mode, IDR reflects own ODR.
        - If this pin is input mode and peer's matching pin is output,
          IDR reflects peer's ODR bit.
        - If peer is floating (input, no drive), use local PUPDR
          (pull-up → 1, pull-down → 0, none → 0).
        """
        # Output mode: IDR mirrors own ODR
        if mode == 1:  # output
            odr = self._regs[port_base + _ODR_OFFSET]
            return (odr >> pin) & 1

        # Input mode: check peer
        if self._peer is not None:
            peer_mode = self._peer._get_pin_mode(port_base, pin)
            if peer_mode == 1:  # peer is driving output
                peer_odr = self._peer._regs[port_base + _ODR_OFFSET]
                peer_bit = (peer_odr >> pin) & 1
                # Open-drain: if peer outputs 1 with open-drain, line is floating
                peer_otype = self._peer._regs[port_base + _OTYPER_OFFSET]
                peer_od = (peer_otype >> pin) & 1
                if peer_od == 1 and peer_bit == 1:
                    # Open-drain high = floating, fall through to pull
                    pass
                else:
                    return peer_bit

        # No external drive — use pull resistor
        pull = self._get_pull(port_base, pin)
        if pull == 1:  # pull-up
            return 1
        return 0  # pull-down or none

    def _update_exti_on_odr_change(self, port_base: int, old_odr: int, new_odr: int) -> None:
        """When this MCU's ODR changes, check if the peer has EXTI
        configured on matching pins and set the peer's PR bits."""
        if self._peer is None:
            return
        changed = old_odr ^ new_odr
        if changed == 0:
            return

        peer_imr = self._peer._regs[_EXTI_BASE + _EXTI_IMR]
        peer_rtsr = self._peer._regs[_EXTI_BASE + _EXTI_RTSR]
        peer_ftsr = self._peer._regs[_EXTI_BASE + _EXTI_FTSR]

        for pin in range(16):
            if not (changed & (1 << pin)):
                continue
            if not (peer_imr & (1 << pin)):
                continue
            old_bit = (old_odr >> pin) & 1
            new_bit = (new_odr >> pin) & 1
            rising = (old_bit == 0 and new_bit == 1)
            falling = (old_bit == 1 and new_bit == 0)
            if (rising and (peer_rtsr & (1 << pin))) or \
               (falling and (peer_ftsr & (1 << pin))):
                self._peer._regs[_EXTI_BASE + _EXTI_PR] |= (1 << pin)

    # -- public interface ----------------------------------------------------

    def reg_read(self, addr: int) -> int:
        port_base = self._port_base_of(addr)
        # IDR is computed dynamically
        if port_base is not None and (addr - port_base) == _IDR_OFFSET:
            return self._compute_idr(port_base)
        return self._regs[addr] & 0xFFFFFFFF

    def reg_write(self, addr: int, value: int) -> None:
        value = value & 0xFFFFFFFF
        port_base = self._port_base_of(addr)

        # EXTI PR is write-1-to-clear
        if addr == _EXTI_BASE + _EXTI_PR:
            self._regs[addr] &= ~value
            return

        # ODR write: trigger EXTI edge detection on peer
        if port_base is not None and (addr - port_base) == _ODR_OFFSET:
            old_odr = self._regs[addr]
            self._regs[addr] = value
            self._update_exti_on_odr_change(port_base, old_odr, value)
            return

        self._regs[addr] = value

    def mem_read(self, addr: int, size: int) -> bytes:
        return bytes(self._mem.get(addr + i, 0) for i in range(size))

    def mem_write(self, addr: int, data: bytes) -> None:
        for i, b in enumerate(data):
            self._mem[addr + i] = b

    def reset(self) -> None:
        self._regs.clear()
        self._mem.clear()
        self._prev_odr.clear()

    def halt(self) -> None:
        pass

    def run(self) -> None:
        pass

    def download_firmware(self, path: str) -> None:
        pass
