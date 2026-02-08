from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class RegisterDef:
    name: str
    offset: int
    bits_per_pin: int
    access: str = "read-write"


@dataclass
class GpioPortDef:
    name: str
    base_addr: int
    pins: List[int]


@dataclass
class ExtiDef:
    base_addr: int
    imr_offset: int
    rtsr_offset: int
    ftsr_offset: int
    pr_offset: int


@dataclass
class SyscfgDef:
    base_addr: int
    exticr_offsets: List[int]


@dataclass
class GpioRegMap:
    ports: dict[str, GpioPortDef] = field(default_factory=dict)
    registers: dict[str, RegisterDef] = field(default_factory=dict)
    exti: ExtiDef | None = None
    syscfg: SyscfgDef | None = None

    def get_reg_addr(self, port: str, reg_name: str) -> int:
        """Return absolute address for a register on a given port."""
        port_def = self.ports[port]
        reg_def = self.registers[reg_name]
        return port_def.base_addr + reg_def.offset


@dataclass
class PinPair:
    mcu_a_port: str
    mcu_a_pin: int
    mcu_b_port: str
    mcu_b_pin: int

    @property
    def label_a(self) -> str:
        return f"{self.mcu_a_port[-1]}{self.mcu_a_pin}"

    @property
    def label_b(self) -> str:
        return f"{self.mcu_b_port[-1]}{self.mcu_b_pin}"


@dataclass
class PinMapConfig:
    pin_pairs: List[PinPair]
    excluded_pins: List[dict]
    jtag_id_a: str
    jtag_id_b: str


def load_gpio_regs(yaml_path: str | Path) -> GpioRegMap:
    """Load GPIO register definitions from a YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    gpio = data["gpio"]
    reg_map = GpioRegMap()

    # Parse ports
    for name, info in gpio["ports"].items():
        reg_map.ports[name] = GpioPortDef(
            name=name,
            base_addr=info["base_addr"],
            pins=info["pins"],
        )

    # Parse registers
    for name, info in gpio["registers"].items():
        reg_map.registers[name] = RegisterDef(
            name=name,
            offset=info["offset"],
            bits_per_pin=info["bits_per_pin"],
            access=info.get("access", "read-write"),
        )

    # Parse EXTI
    if "exti" in gpio:
        exti = gpio["exti"]
        regs = exti["registers"]
        reg_map.exti = ExtiDef(
            base_addr=exti["base_addr"],
            imr_offset=regs["IMR"],
            rtsr_offset=regs["RTSR"],
            ftsr_offset=regs["FTSR"],
            pr_offset=regs["PR"],
        )

    # Parse SYSCFG
    if "syscfg" in gpio:
        sc = gpio["syscfg"]
        reg_map.syscfg = SyscfgDef(
            base_addr=sc["base_addr"],
            exticr_offsets=sc["exticr_offsets"],
        )

    return reg_map


def load_pin_map(yaml_path: str | Path) -> PinMapConfig:
    """Load pin mapping configuration from a YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    pairs = []
    for item in data["pin_pairs"]:
        a = item["mcu_a"]
        b = item["mcu_b"]
        pairs.append(PinPair(
            mcu_a_port=a["port"],
            mcu_a_pin=a["pin"],
            mcu_b_port=b["port"],
            mcu_b_pin=b["pin"],
        ))

    return PinMapConfig(
        pin_pairs=pairs,
        excluded_pins=data.get("excluded_pins", []),
        jtag_id_a=data["jtag"]["mcu_a"],
        jtag_id_b=data["jtag"]["mcu_b"],
    )
