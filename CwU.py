# coding: UTF-8
"""CwU：带单位的标量计算。Python 3.10+，无第三方依赖。"""
from __future__ import annotations

from contextlib import contextmanager
import math
import re
import warnings

__version__ = "0.261016"
max_significance = 15

# 先匹配单位，再拆词头。
prefixes = {'Y': 1e24, 'Z': 1e21, 'E': 1e18, 'P': 1e15, 'T': 1e12,
            'G': 1e9, 'M': 1e6, 'k': 1e3, 'h': 1e2, 'da': 1e1,
            'd': 1e-1, 'c': 1e-2, 'm': 1e-3, 'μ': 1e-6, 'u': 1e-6, 'n': 1e-9,
            'p': 1e-12, 'f': 1e-15, 'a': 1e-18, 'z': 1e-21, 'y': 1e-24}
_SI_BASES = frozenset(('m', 'kg', 's', 'K', 'A', 'mol', 'cd'))
standard_dic = {
    'u': (1.660538851e-27, 'kg'), 'eV': (1.602176634e-19, 'kg*m2/s2'),
    'Hz': (1, 's-1'), 'Pa': (1, 'kg/m/s2'), 'F': (1, 'A2*s4/kg/m2'),
    'C': (1, 's*A'), 'omega': (1, 'kg*m2/s3/A2'), 'S': (1, 'A2*s3/kg/m2'),
    'T': (1, 'kg/s2/A'), 'H': (1, 'kg*m2/s2/A2'), 'Wb': (1, 'kg*m2/s2/A'),
    'h': (3600, 's'), 'min': (60, 's'), 'V': (1, 'kg*m2/s3/A'),
    'W': (1, 'kg*m2/s3'), 'J': (1, 'kg*m2/s2'), 'N': (1, 'kg*m/s2'),
    'g': (1e-3, 'kg'), 'rad': (1, ''),
    'sr': (1, ''), 'lm': (1, 'cd'), 'lx': (1, 'cd/m2'), 'Bq': (1, 's-1'),
    'Gy': (1, 'm2/s2'), 'Sv': (1, 'm2/s2'), 'kat': (1, 'mol/s'),
}
_ALIASES = {'ohm': 'omega'}
_HBAR = 6.62607015e-34 / (2 * math.pi)
_MEV = 1.602176634e-13
# 常量单位；h 表示小时。
constant_unit_dic = {
    'c': (2.99792458e8, 'm/s'),
    'h_': (_HBAR, 'kg*m2/s'),
    'k': (1.380649e-23, 'kg*m2/s2/K'),
}
# 自然单位保留 h_、c、k。
natural_dic = {
    'K': (1.380649e-23 / _MEV, 'MeV/k'),
    's': (_MEV / _HBAR, 'h_/MeV'),
    'm': (_MEV / (_HBAR * 2.99792458e8), 'h_*c/MeV'),
    'kg': (2.99792458e8 ** 2 / _MEV, 'MeV/c2'),
}
_NATURAL_TO_SI = {
    'h_': (_HBAR, 'kg*m2/s'), 'k': (1.380649e-23, 'kg*m2/s2/K'),
    'c': (2.99792458e8, 'm/s'), 'MeV': (_MEV, 'kg*m2/s2'),
}


def _real(value: float | int) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise TypeError('数值须为 int 或 float')
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('数值须有限')
    return result


def get_scientific_notation(real_number: float | int) -> tuple[int, float, int]:
    """返回符号、正系数、十进制指数。"""
    value = _real(real_number)
    if value == 0:
        return 0, 0.0, 0
    coefficient, power = format(abs(value), '.14e').split('e')
    return (1 if value > 0 else -1), float(coefficient), int(power)


# 兼容旧拼写。
get_sicentific_notation = get_scientific_notation


def unit_dict_check(unit_dict: dict[str, float]) -> dict[str, float]:
    """返回规范化副本。"""
    result = {}
    for name, exponent in unit_dict.items():
        if not isinstance(name, str):
            raise TypeError('单位名须为字符串')
        exponent = round(_real(exponent), max_significance)
        if name and exponent:
            result[name] = exponent
    return result


def unit_dict_combine(unit_dict1: dict[str, float], unit_dict2: dict[str, float],
                      sign: int = 1) -> dict[str, float]:
    result = unit_dict1.copy()
    for name, exponent in unit_dict2.items():
        result[name] = result.get(name, 0.0) + exponent * sign
    return unit_dict_check(result)


def _normalize_unit(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError('单位须为字符串')
    if any(symbol in text for symbol in ('°', '℃', '℉')):
        raise ValueError('不支持偏移温度单位，请先换算为 K')
    for old, new in {'−': '-', '（': '(', '）': ')', '·': '*',
                     'µ': 'μ', 'Ω': 'omega', 'Ω': 'omega'}.items():
        text = text.replace(old, new)
    # 避免将 m s 误读为 ms。
    if re.search(r'[A-Za-zμ_0-9)]\s+[A-Za-zμ_(]', text):
        raise ValueError('单位间须用 * 或 /')
    return re.sub(r'\s+', '', text)


class _UnitParser:
    """解析单位表达式，不跳过字符。"""
    _name = re.compile(r'[A-Za-zμ_]+')
    _number = re.compile(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)')

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.names = set()

    def error(self, message: str):
        raise ValueError(f'单位 {self.text!r} 第 {self.pos + 1} 位：{message}')

    def parse(self) -> dict[str, float]:
        if not self.text:
            return {}
        result = self.product()
        if self.pos != len(self.text):
            self.error('非法字符或缺少乘除号')
        return unit_dict_check(result)

    def product(self) -> dict[str, float]:
        sign = 1
        if self.pos < len(self.text) and self.text[self.pos] in '*/':
            sign = -1 if self.text[self.pos] == '/' else 1
            self.pos += 1
        result = {name: power * sign for name, power in self.factor().items()}
        while self.pos < len(self.text) and self.text[self.pos] != ')':
            operator = self.text[self.pos]
            if operator not in '*/':
                self.error('单位之间缺少 * 或 /')
            self.pos += 1
            result = unit_dict_combine(result, self.factor(), -1 if operator == '/' else 1)
        return result

    def factor(self) -> dict[str, float]:
        if self.pos >= len(self.text):
            self.error('缺少单位')
        if self.text[self.pos] == '(':
            self.pos += 1
            result = self.product()
            if self.pos >= len(self.text) or self.text[self.pos] != ')':
                self.error('括号未成对')
            self.pos += 1
        elif self.text[self.pos] == '1':
            self.pos += 1
            # 仅接受无量纲单位 1。
            if self.pos < len(self.text) and self.text[self.pos] not in '*/)':
                self.error('单位中仅允许数字 1')
            return {}
        else:
            match = self._name.match(self.text, self.pos)
            if not match:
                self.error('需要单位名称或括号')
            result = {match.group(): 1.0}
            self.names.add(match.group())
            self.pos = match.end()
        explicit = False
        if self.text.startswith('**', self.pos):
            self.pos += 2
            explicit = True
        elif self.text.startswith('^', self.pos):
            self.pos += 1
            explicit = True
        match = self._number.match(self.text, self.pos)
        if match:
            power = _real(float(match.group()))
            result = {name: exponent * power for name, exponent in result.items()}
            self.pos = match.end()
        elif explicit:
            self.error('缺少指数')
        return result


def unit_str_to_dict(unit_str: str, outer_power: float | int = 1) -> dict[str, float]:
    power = _real(outer_power)
    return unit_dict_check({name: exponent * power for name, exponent in
                            _UnitParser(_normalize_unit(unit_str)).parse().items()})


def _unit_text(units: dict[str, float], separator: str = '·') -> str:
    result = ''
    for name, power in sorted(units.items()):
        operator = '/' if power < 0 else separator
        magnitude = abs(power)
        exponent = '' if magnitude == 1 else format(magnitude, '.15g')
        result += operator + name + exponent
    return result.removeprefix(separator)


def unit_str_formatted(unit_str: str) -> str:
    return _unit_text(unit_str_to_dict(unit_str), '*')


def _resolve_unit(name: str, allow_unknown: bool, stack: tuple[str, ...] = ()):
    name = _ALIASES.get(name, name)
    if name in _SI_BASES:
        return 1.0, {name: 1.0}
    if name in stack:
        raise ValueError(f'单位循环定义：{" -> ".join(stack + (name,))}')
    definition = standard_dic.get(name, constant_unit_dic.get(name))
    if definition is not None:
        scale, expression = definition
        inner_scale, inner_units = _resolve_units(unit_str_to_dict(expression), allow_unknown, stack + (name,))
        return scale * inner_scale, inner_units
    for prefix in sorted(prefixes, key=len, reverse=True):
        if name.startswith(prefix):
            base = _ALIASES.get(name[len(prefix):], name[len(prefix):])
            if base in _SI_BASES or base in standard_dic:
                scale, units = _resolve_unit(base, allow_unknown, stack)
                return prefixes[prefix] * scale, units
    if allow_unknown:
        return 1.0, {name: 1.0}
    raise ValueError(f'未知单位 {name!r}；自定义单位请设 allow_unknown_units=True')


def _resolve_units(units: dict[str, float], allow_unknown: bool, stack: tuple[str, ...] = ()):
    scale, result = 1.0, {}
    for name, power in unit_dict_check(units).items():
        factor, expanded = _resolve_unit(name, allow_unknown, stack)
        scale *= factor ** power
        result = unit_dict_combine(result, {key: exponent * power for key, exponent in expanded.items()})
    return scale, result


def _input_units(unit: str | dict, allow_unknown: bool):
    if isinstance(unit, str):
        parser = _UnitParser(_normalize_unit(unit))
        units = parser.parse()
        names = parser.names
    elif isinstance(unit, dict):
        units = {}
        names = set()
        for raw_name, power in unit.items():
            name = _normalize_unit(raw_name)
            if not _UnitParser._name.fullmatch(name):
                raise ValueError(f'非法单位名 {raw_name!r}')
            names.add(name)
            units[name] = units.get(name, 0.0) + _real(power)
    else:
        raise TypeError('单位须为字符串或字典')
    # 先检查名称，避免 x/x 消掉未知单位。
    for name in names:
        _resolve_unit(name, allow_unknown)
    return _resolve_units(units, allow_unknown)


def _substitute(units: dict[str, float], dictionary: dict[str, tuple[float, str]]):
    scale, result = 1.0, {}
    for name, power in units.items():
        factor, expression = dictionary.get(name, (1.0, name))
        scale *= factor ** power
        expanded = unit_str_to_dict(expression)
        result = unit_dict_combine(result, {key: exponent * power for key, exponent in expanded.items()})
    return scale, result


def _order(value: float) -> int:
    return get_scientific_notation(value)[2]


def _significance(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError('有效位数须为整数')
    if value < 1:
        raise ValueError('有效位数须大于 0')
    if value > max_significance:
        warnings.warn(f'有效位数上限为 {max_significance}，已截至上限', stacklevel=3)
    return min(value, max_significance)


_SWITCHES = frozenset(('use_significance', 'use_scientific_notation', 'use_natural_units'))


class _QuantityMeta(type):
    def __setattr__(cls, name, value):
        if name in _SWITCHES and not isinstance(value, bool):
            raise TypeError(f'{name} 须为布尔值')
        super().__setattr__(name, value)


class Quantity(metaclass=_QuantityMeta):
    """带单位标量；有效数字仅控制显示。"""
    use_significance = True
    use_scientific_notation = False
    use_natural_units = False

    def __init__(self, value: float | int | Quantity, unit: str | dict = '',
                 significance: int = 0, *, allow_unknown_units: bool = False):
        if not isinstance(allow_unknown_units, bool):
            raise TypeError('allow_unknown_units 须为布尔值')
        if isinstance(value, Quantity):
            if unit != '' or significance != 0:
                raise ValueError('复制时勿另设单位或有效位数')
            self.__dict__.update(value.__dict__)
            self._unit = value.unit_dict
            return
        if isinstance(significance, bool) or not isinstance(significance, int):
            raise TypeError('有效位数须为整数')
        sig = _significance(significance) if significance else max_significance
        scale, units = _input_units(unit, allow_unknown_units)
        self._value = _real(_real(value) * scale)
        self._unit = units
        self._system = 'si'
        self._allow_unknown = allow_unknown_units
        self._significance = sig
        self._place = _order(self.value) - sig + 1
        self._fixed_place = False
        if Quantity.use_natural_units:
            converted = self.to_natural()
            self.__dict__.update(converted.__dict__)

    def __setattr__(self, name, value):
        if name in _SWITCHES:
            raise AttributeError('全局设置请用 Quantity.configure()')
        super().__setattr__(name, value)

    @classmethod
    def configure(cls, **options: bool) -> None:
        """设置全局开关。"""
        for name, value in options.items():
            if name not in _SWITCHES:
                raise TypeError(f'未知配置项 {name!r}')
            if not isinstance(value, bool):
                raise TypeError(f'{name} 须为布尔值')
        for name, value in options.items():
            setattr(cls, name, value)

    @classmethod
    @contextmanager
    def settings(cls, **options: bool):
        """临时设置，退出后恢复。"""
        previous = {name: getattr(cls, name) for name in _SWITCHES}
        cls.configure(**options)
        try:
            yield
        finally:
            cls.configure(**previous)

    @classmethod
    def _from_parts(cls, value, units, sig, system, allow_unknown=False, place=None):
        result = object.__new__(cls)
        result._value = _real(value)
        result._unit = unit_dict_check(units)
        result._system = system
        result._allow_unknown = allow_unknown
        result._significance = max(1, min(max_significance, sig))
        result._place = _order(result.value) - result.significance + 1 if place is None else place
        result._fixed_place = place is not None
        return result

    def _in_system(self, system: str) -> Quantity:
        if system == self._system:
            return self.copy()
        dictionary = natural_dic if system == 'natural' else _NATURAL_TO_SI
        scale, units = _substitute(self.unit_dict, dictionary)
        result = self._from_parts(self.value * scale, units, self.significance, system, self._allow_unknown)
        if self._fixed_place:
            result._place = self._place + math.floor(math.log10(abs(scale)) + 1e-12)
            result._fixed_place = True
            result._significance = max(1, min(max_significance, _order(result.value) - result._place + 1))
        return result

    def to_si(self) -> Quantity:
        return self._in_system('si')

    def to_natural(self) -> Quantity:
        """转换为自然单位表示。"""
        return self._in_system('natural')

    @property
    def value(self) -> float:
        return self._value

    @property
    def unit_dict(self) -> dict[str, float]:
        return self._unit.copy()

    @property
    def unit_str(self) -> str:
        return _unit_text(self.unit_dict)

    @property
    def significance(self) -> int:
        return self._significance

    @significance.setter
    def significance(self, value: int):
        self._significance = _significance(value)
        self._place = _order(self.value) - self.significance + 1
        self._fixed_place = False

    def copy(self) -> Quantity:
        result = self._from_parts(self.value, self.unit_dict, self.significance,
                                  self._system, self._allow_unknown, self._place)
        result._fixed_place = self._fixed_place
        return result

    def __copy__(self):
        return self.copy()

    def __pos__(self):
        return self.copy()

    def __neg__(self):
        result = self.copy()
        result._value = -result.value
        return result

    def __abs__(self):
        result = self.copy()
        result._value = abs(result.value)
        return result

    def _same_units(self, other: Quantity) -> Quantity:
        other = other._in_system(self._system)
        if self.unit_dict != other.unit_dict:
            raise ValueError(f'量纲不匹配：[{self.unit_str or "1"}] 与 [{other.unit_str or "1"}]')
        return other

    def __add__(self, other):
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            if self.unit_dict:
                if other == 0:  # 支持 sum()。
                    return self.copy()
                raise ValueError('有单位的量不能加减普通数字')
            value = self.value + _real(other)
            sig = _order(value) - self._place + 1
            return self._from_parts(value, self.unit_dict, sig,
                                    self._system, self._allow_unknown, self._place)
        if not isinstance(other, Quantity):
            return NotImplemented
        other = self._same_units(other)
        value = self.value + other.value
        place = max(self._place, other._place)
        sig = _order(value) - place + 1
        return self._from_parts(value, self.unit_dict, sig, self._system,
                                self._allow_unknown or other._allow_unknown, place)

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        if isinstance(other, (Quantity, int, float)) and not isinstance(other, bool):
            return self + -other
        return NotImplemented

    def __rsub__(self, other):
        return -self + other

    def __mul__(self, other):
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self._from_parts(self.value * _real(other), self.unit_dict,
                                    self.significance, self._system, self._allow_unknown)
        if not isinstance(other, Quantity):
            return NotImplemented
        other = other._in_system(self._system)
        return self._from_parts(self.value * other.value,
                                unit_dict_combine(self.unit_dict, other.unit_dict),
                                min(self.significance, other.significance), self._system,
                                self._allow_unknown or other._allow_unknown)

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self._from_parts(self.value / _real(other), self.unit_dict,
                                    self.significance, self._system, self._allow_unknown)
        if not isinstance(other, Quantity):
            return NotImplemented
        other = other._in_system(self._system)
        return self._from_parts(self.value / other.value,
                                unit_dict_combine(self.unit_dict, other.unit_dict, -1),
                                min(self.significance, other.significance), self._system,
                                self._allow_unknown or other._allow_unknown)

    def __rtruediv__(self, other):
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return self._from_parts(_real(other) / self.value,
                                    {name: -power for name, power in self.unit_dict.items()},
                                    self.significance, self._system, self._allow_unknown)
        return NotImplemented

    def __pow__(self, power, modulo=None):
        if modulo is not None:
            raise TypeError('乘方不支持取模')
        if isinstance(power, Quantity):
            if power.unit_dict:
                raise ValueError('指数须无量纲')
            power = power.value
        power = _real(power)
        if power == 0:
            return self._from_parts(1, {}, max_significance, self._system)
        return self._from_parts(self.value ** power,
                                {name: exponent * power for name, exponent in self.unit_dict.items()},
                                self.significance, self._system, self._allow_unknown)

    def __eq__(self, other):
        if isinstance(other, Quantity):
            other = other._in_system(self._system)
            return self.value == other.value and self.unit_dict == other.unit_dict
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            return not self.unit_dict and self.value == other
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Quantity):
            return self.value < self._same_units(other).value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            if self.unit_dict:
                raise ValueError('有单位的量不能与普通数字比大小')
            return self.value < _real(other)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Quantity):
            return self.value > self._same_units(other).value
        if isinstance(other, (int, float)) and not isinstance(other, bool):
            if self.unit_dict:
                raise ValueError('有单位的量不能与普通数字比大小')
            return self.value > _real(other)
        return NotImplemented

    def __le__(self, other):
        less = self.__lt__(other)
        return NotImplemented if less is NotImplemented else less or self == other

    def __ge__(self, other):
        greater = self.__gt__(other)
        return NotImplemented if greater is NotImplemented else greater or self == other

    def _number_str(self) -> str:
        place = self._place
        if not self._fixed_place and self.value:
            # 处理舍入进位，如 9.99 -> 10。
            rounded = round(self.value, -place)
            place = _order(rounded) - self.significance + 1
        value = round(self.value, -place) if Quantity.use_significance else self.value
        if Quantity.use_scientific_notation:
            if Quantity.use_significance:
                digits = max(1, min(max_significance, _order(value) - place + 1))
                coefficient, power = format(value, f'.{digits - 1}e').split('e')
            else:
                coefficient, power = format(value, '.14e').split('e')
                coefficient = coefficient.rstrip('0').rstrip('.')
            return f'{coefficient}e{int(power)}'
        if Quantity.use_significance:
            return format(value, f'.{max(0, -place)}f')
        return str(value)

    def __str__(self) -> str:
        return f'{self._number_str()} {self.unit_str}'.strip()

    def _at_unit(self, unit_str: str) -> Quantity:
        if not isinstance(unit_str, str):
            raise TypeError('目标单位须为字符串')
        scale, units = _input_units(unit_str, self._allow_unknown)
        target = self._from_parts(scale, units, max_significance, 'si', self._allow_unknown)
        target = target._in_system(self._system)
        self._same_units(target)
        # 换算不减少有效位数。
        result = self._from_parts(self.value / target.value, {}, self.significance,
                                  self._system, self._allow_unknown)
        if self._fixed_place:
            result._place = self._place - math.ceil(math.log10(abs(target.value)) - 1e-12)
            result._fixed_place = True
            result._significance = max(1, min(max_significance, _order(result.value) - result._place + 1))
        return result

    def get_value(self, unit_str: str | None = None) -> float:
        """取数值，不受显示设置影响。"""
        return self.value if unit_str is None else self._at_unit(unit_str).value

    def get_str(self, unit_str: str | None = None) -> str:
        """取显示文本。"""
        if unit_str is None:
            return str(self)
        return f'{self._at_unit(unit_str)._number_str()} {unit_str}'.strip()

    def show(self, unit_str: str | None = None) -> Quantity:
        print(self.get_str(unit_str))
        return self


Q = Quantity

# 常量沿用本地版数值。
pi = Quantity(math.pi)
e_ = Quantity(math.e)
one = Quantity(1)
c = Quantity(2.99792458e8, 'm/s', 15)
h = Quantity(6.62607015e-34, 'J*s', 15)
e = Quantity(1.602176634e-19, 'C', 15)
k = Quantity(1.380649e-23, 'J/K', 15)
NA = Quantity(6.02214076e23, 'mol-1', 15)
G = Quantity(6.6742e-11, 'N*m2/kg2', 5)
me = Quantity(9.1093826e-31, 'kg', 8)
mp = Quantity(1.67262171e-27, 'kg', 9)
mn = Quantity(1.67492728e-27, 'kg', 9)
h_ = h / 2 / pi
# 沿用 mu0 ≈ 4π×10^-7 H/m。
mu0 = Quantity(1e-7, 'H/m', 15) * 4 * pi
ep0 = one / c ** 2 / mu0
alpha = e * e / pi / ep0 / (h_ * c) / 4
muB = e * h_ / me / 2
muN = e * h_ / mp / 2
