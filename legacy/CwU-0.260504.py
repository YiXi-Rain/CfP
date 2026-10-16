# coding: UTF-8
from __future__ import annotations
import warnings
import re

"""
Project: Calculating with Units
Interpreter: python 3.12.12
version: 0.260504
说明: 
(v0.241028)删除SN类、Unit类;单位改为使用字典储存;有效数字位数可选择是否显示
(v0.260504)有效数字、科学计数法、自然单位制开关均放入Quantity类内部；优化了与常数的运算
"""


max_significance: int = 15
prefixes = {'Y': 1e24, 'Z': 1e21, 'E': 1e18, 'P': 1e15, 'T': 1e12, 'G': 1e9, 'M': 1e6, 'k': 1e3, 'h': 1e2, 'da': 1e1,
            'd': 1e-1, 'c': 1e-2, 'm': 1e-3, 'μ': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15, 'a': 1e-18, 'z': 1e-21,
            'y': 1e-24}  # SI词头
special = ('Pa', 'T', 'Gy', 'kat', 'm', 'kg', 'mol', 'cd', 'c', 'Gs', 'h')  # special judge
standard_dic = {"u": (1.660538851e-27, "kg"), 'eV': (1.602176634e-19, 'kg*m2/s2'), 'Hz': (1, 's-1'),
                'Pa': (1, 'kg/m/s2'), 'F': (1, 'A2*s4/kg/m2'), 'C': (1, 's*A'), 'omega': (1, 'kg*m2/s3/A2'),
                'T': (1, 'kg/s2/A'), 'H': (1, 'kg*m2/s2/A2'), 'Wb': (1, 'kg*m2/s2/A'), 'h': (3600, 's'),
                'V': (1, 'kg*m2/s3/A'), 'W': (1, 'kg*m2/s3'), 'J': (1, 'kg*m2/s2'), 'N': (1, 'kg*m/s2'),
                'c': (2.99792458e8, 'm/s'),
                'g': (1e-3, 'kg')}  # SI Standard Units("m", "kg", "s", "K", "A", "mol", "cd")
natural_dic = {"K": (8.617333262145179e-11, "MeV/k"), "s": (1.5192674478786259e21, "h_/MeV"),
               "m": (5.067730716156395e12, "h_*c/MeV"), "kg": (5.609588603804452e29, "MeV/c2")}


def get_sicentific_notation(real_number: float | int) -> tuple[int, float, int]:
    """
    获取实数的科学计数法表示
    return: sign, coefficient, power(based in 10)
    """
    if not isinstance(real_number, (float, int)):
        raise TypeError(f"必须传入实数(float or int)！当前类型为: {type(real_number)}")
    
    if not real_number:
        return 0, 0.0, 0
    
    sign = 1 if real_number > 0 else -1
    coefficient = float(abs(real_number))
    power = 0
    while coefficient >= 10:
        coefficient /= 10
        power += 1
    while coefficient < 1:
        coefficient *= 10
        power -= 1
    return sign, round(real_number, max_significance - 1), power


def unit_str_formatted(unit_str: str) -> str:
    """通过正则表达式递归处理实现格式化字符串（缺少最后一步转换成字典排序）"""
    unit_formatted: str = unit_str.strip()
    replace_map = {"−": "-", "（": "(", "）": ")", "·": "*", "**": "", "^": ""}
    for old, new in replace_map.items():
        unit_formatted = unit_formatted.replace(old, new)
    unit_formatted = re.sub(r"\s+", "", unit_formatted)

    bracket_re = re.compile(r"\(([^()]+)\)([-+]?\d*\.?\d+)?")
    
    while "(" in unit_formatted:
        match = bracket_re.search(unit_formatted)
        if not match:
            break

        outer_power = float(match.group(2)) if match.group(2) else 1.0
        start_idx = match.start()
        is_div = start_idx > 0 and unit_formatted[start_idx - 1] == "/"
        effective_power = -outer_power if is_div else outer_power
        
        inner_dict = unit_str_to_dict(match.group(1), effective_power)
        flattened = "".join(f"*{unit_str}{power}" for unit_str, power in inner_dict.items())
        
        prefix_limit = start_idx - 1 if is_div else start_idx
        unit_formatted = unit_formatted[:max(0, prefix_limit)] + flattened + unit_formatted[match.end():]
    
    if "(" in unit_formatted or ")" in unit_formatted:
        raise ValueError(f"请检查单位字符串 {unit_str} 中可能存在未成对括号！")

    return unit_formatted


def unit_str_to_dict(unit_str: str, outer_power: float | int = 1) -> dict[str, float]:
    """将字符串格式的单位转化为字典"""
    unit_dict: dict[str, float] = {}
    token_re = re.compile(r"([*/]?)([a-zA-Zμ_]+)([-+]?\d*\.?\d+)?")

    for match in token_re.finditer(unit_str):
        operator, unit_name, power_str = match.groups()
        power_value = float(power_str) if power_str else 1.0
        power_sign = -1.0 if operator == "/" else 1.0
        unit_dict[unit_name] = unit_dict.get(unit_name, 0.0) + power_sign * power_value * outer_power

    return unit_dict_check(unit_dict)


def unit_dict_check(unit_dict: dict[str, float]) -> dict[str, float]:
    """标准化单位字典(删除指数为0和单位为''部分)"""
    new_dict: dict[str, float] = {}
    unit_dict[""] = 0
    for unit_name in unit_dict:
        power = round(unit_dict[unit_name], max_significance)
        if power:
            new_dict[unit_name] = float(power)
    return new_dict


def unit_dict_combine(unit_dict1: dict[str, float], unit_dict2: dict[str, float], sign: int = 1) -> dict[str, float]:
    """
    合并字典形式的单位
    param dict1: 待合并字典1
    param dict2: 待合并字典2
    param sign: 1(加法)/-1(减法)
    return: 合并后的字典
    """
    unit_dict: dict[str, float] = unit_dict1.copy()
    for unit_name in unit_dict2:
        unit_dict[unit_name] = unit_dict.get(unit_name, 0.0) + unit_dict2[unit_name] * sign
    return unit_dict_check(unit_dict)


class BoolSwitch:
    """严格限制只能赋值为布尔值的描述符"""
    def __init__(self, value: bool):
        self.__value = value

    def __get__(self, instance, owner):
        return self.__value

    def __set__(self, obj, value):
        if not isinstance(value, bool):
            raise TypeError(f"必须为布尔值 (True/False)，不支持 {type(value).__name__}")
        self.__value = value


class Quantity:
    """物理量(标量)类，内部存储采用国际单位制基本单位或自然单位制(不成熟)。如果需要调用特定单位下的值，需使用 get_value 方法"""
    use_significance = BoolSwitch(True)
    use_scientific_notation = BoolSwitch(False)
    use_natural_units = BoolSwitch(False)

    def __init__(self, value: float | int | Quantity, unit: str | dict = "", significance: int = 0):
        """
        储存物理量的值(科学计数法)和单位(SI基本单位)
        :param value: 物理量的值
        :param unit: 物理量的单位, 若为字典则判定为简化生成模式
        :param significance: 有效数字位数
        """
        if isinstance(value, Quantity):
            self.__value: float = value.__value
            self.__unit: dict[str, float] = value.__unit
            self.__significance: int = value.__significance
            return
        

        if not isinstance(value, (float, int)):
            raise TypeError(f"物理量的值需要为整数或者浮点数，当前为: {type(value).__name__}")

        match unit:
            case str():  # 正常输入模式,会将单位从字符串形式转化为字典
                self.__significance: int = max_significance
                if significance:
                    self.significance = significance
                elif significance % 1:
                    significance = len(str(get_sicentific_notation(abs(value))[0])) - 1
                    self.__significance = min(self.__significance, significance)

                unit_dict: dict[str, float] = unit_str_to_dict(unit_str_formatted(unit))
                self.__unit: dict[str, float] = {}
                self.__value: float = float(value)
                for unit_str, power in unit_dict.items():  # 处理词头
                    for prefix in prefixes:
                        if (unit_str.startswith(prefix)) and (unit_str not in special):  # 首字母与词头重复的单位的特判
                            unit_name = unit_str[len(prefix):]
                            self.__value *= prefixes[prefix] ** power
                            self.__unit[unit_name] = self.__unit.get(unit_name, 0.0) + power
                            break
                    else:
                        self.__unit[unit_str] = power
                self.__trans_units(standard_dic)
                if Quantity.use_natural_units:  # 自然单位制
                    self.__trans_units(natural_dic)
            case dict():  # 简化输入
                self.__value: float = value
                self.__unit: dict[str, float] = unit
                self.__significance: int = significance
            case _:
                raise TypeError(f"当前程序无法处理类型为 {type(unit).__name__} 的单位输入！")

    def __trans_units(self, dictionary: dict[str, tuple[float, str]]) -> None:
        new_unit: dict[str, float] = {}
        old_unit = unit_dict_check(self.unit_dict)
        for unit_name in old_unit:
            if unit_name in dictionary:  # 单位在单位换算字典里
                self.__value *= (dictionary[unit_name][0] ** old_unit[unit_name])
                tem_unit_dict = unit_str_to_dict(dictionary[unit_name][1])
                for tem_unit_str in tem_unit_dict:
                    new_unit[tem_unit_str] = new_unit.get(tem_unit_str, 0.0) + tem_unit_dict[tem_unit_str] * old_unit[unit_name]
            else:
                new_unit[unit_name] = new_unit.get(unit_name, 0.0) + old_unit[unit_name]
        self.__unit = unit_dict_check(new_unit)

    def __str__(self) -> str:
        result_str: str = ""
        value: float = self.value
        sign, coefficient, power = get_sicentific_notation(value)

        if not sign:
            result_str = f"{coefficient} {self.unit_str}"
        
        elif Quantity.use_scientific_notation:
            if Quantity.use_significance:
                result_str = f"{sign * coefficient:.{self.significance - 1}f}e{power} {self.unit_str}"
            elif coefficient % 1:
                result_str = f"{round(sign * coefficient, max_significance - 1)}e{power} {self.unit_str}"
            else:
                result_str = f"{int(sign * coefficient)}e{power} {self.unit_str}"
        
        else:
            if Quantity.use_significance:
                precision = self.significance - 1 - power
                if precision >= 0:
                    result_str = f"{value:.{precision}f} {self.unit_str}"
                else:
                    result_str =  f"{int(round(value, precision))} {self.unit_str}"
            else:
                result_str = f"{value} {self.unit_str}"

        return result_str.strip()

    def __copy__(self):
        return Quantity(self.value, self.unit_dict, self.significance)

    def __pos__(self):
        return self.__copy__()

    def __neg__(self):
        return Quantity(-self.value, self.unit_dict, self.significance)

    def __add__(self, other: Quantity | int | float) -> Quantity:
        if isinstance(other, (int, float)):
            # 视为无单位数值相加
            return Quantity(self.value + other, self.unit_dict, self.significance)
        
        if isinstance(other, Quantity):
            if self.unit_dict != other.unit_dict:
                raise ValueError(f"单位不匹配: {self.unit_str} vs {other.unit_str}")
            # 简化版有效数字逻辑
            return Quantity(self.value + other.value, self.unit_dict, min(self.significance, other.significance))
        
        raise TypeError(f"不支持 Quantity 与 {type(other).__name__} 的加法")

    def __sub__(self, other):
        return self + -other

    def __mul__(self, other: Quantity | int | float) -> Quantity:
        if isinstance(other, (int, float)):
            return Quantity(self.value * other, self.unit_dict, self.significance)
        if isinstance(other, Quantity):
            return Quantity(self.value * other.value, unit_dict_combine(self.unit_dict, other.unit_dict), min(self.significance, other.significance))
        raise TypeError(f"不支持的乘法操作数: {type(other).__name__}")

    def __rmul__(self, other: int | float) -> Quantity:
        return self.__mul__(other)

    def __pow__(self, power: int | float | Quantity, modulo=None):
        if power == 0:
            return Quantity(1)

        if isinstance(power, Quantity):
            unit_str = power.unit_str
            if unit_str:
                raise TypeError(f"有单位的物理量不能作为指数！当前物理量单位为: {unit_str}")
            power = power.value

        unit_dict = self.unit_dict
        for unit_name in unit_dict:
            unit_dict[unit_name] = unit_dict[unit_name] * power
        return Quantity(self.value ** power, unit_dict_check(unit_dict), self.significance)

    def __truediv__(self, other: "Quantity | int | float") -> "Quantity":
        if isinstance(other, Quantity):
            # 使用 unit_dict_combine 合并单位，-1 表示指数取反（除法逻辑）
            return Quantity(
                self.value / other.value, 
                unit_dict_combine(self.unit_dict, other.unit_dict, -1), 
                min(self.significance, other.significance)
            )
        if isinstance(other, (int, float)):
            # 这里的 unit 使用 self.unit_dict，因为 scalar 不带单位
            return Quantity(self.value / other, self.unit_dict, self.significance)
        
        raise TypeError(f"不支持 Quantity 与 {type(other).__name__} 的除法运算")

    def __rtruediv__(self, other: int | float) -> "Quantity":
        # 处理 scalar / Quantity 的情况，单位指数需全部取反
        new_unit = {unit_name: -power for unit_name, power in self.unit_dict.items()}
        return Quantity(other / self.value, new_unit, self.significance)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Quantity):
            # 只有当数值和单位字典完全一致时才相等
            return self.value == other.value and self.unit_dict == other.unit_dict
        if isinstance(other, (int, float)):
            # 如果是数值，则仅在当前对象无单位时进行比较，否则通常判定为不相等
            return self.value == other and not self.unit_dict
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: "Quantity | int | float") -> bool:
        if isinstance(other, Quantity):
            if self.unit_dict != other.unit_dict:
                raise TypeError(f"量纲不匹配，无法比较大小: {self.unit_str} vs {other.unit_str}")
            return self.value < other.value
        if isinstance(other, (int, float)):
            if self.unit_dict:
                raise TypeError("不能将有单位的物理量与无单位数值进行比较")
            return self.value < other
        raise TypeError(f"不支持 Quantity 与 {type(other).__name__} 的比较")

    def __gt__(self, other: "Quantity | int | float") -> bool:
        if isinstance(other, Quantity):
            if self.unit_dict != other.unit_dict:
                raise TypeError(f"量纲不匹配，无法比较大小: {self.unit_str} vs {other.unit_str}")
            return self.value > other.value
        if isinstance(other, (int, float)):
            if self.unit_dict:
                raise TypeError("不能将有单位的物理量与无单位数值进行比较")
            return self.value > other
        raise TypeError(f"不支持 Quantity 与 {type(other).__name__} 的比较")

    def __le__(self, other: "Quantity | int | float") -> bool:
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other: "Quantity | int | float") -> bool:
        return self.__gt__(other) or self.__eq__(other)

    @property
    def value(self) -> float:
        """只读属性：返回物理量的数值"""
        return self.__value

    @property
    def unit_dict(self) -> dict[str, float]:
        """只读属性：返回单位字典的副本，防止外部修改原字典"""
        return self.__unit.copy()
    
    @property
    def unit_str(self) -> str:
        """只读属性：返回单位字符串"""
        MULTSIGN: str = "·"
        unit_list: list[tuple[str, float]] = list(self.unit_dict.items())
        unit_list.sort(key=lambda x: x[0])
        unit_str: str = ""
        for unit_name, power in unit_list:
            operator: str = "/" if power < 0 else MULTSIGN
            power = abs(power)
            power_str = str(power) if power % 1 else str(int(power))
            power_str = "" if power_str == "1" else power_str
            unit_str += operator + unit_name + power_str
        return unit_str[1:] if unit_str.startswith(MULTSIGN) else unit_str

    @property
    def significance(self) -> int:
        return self.__significance

    @significance.setter
    def significance(self, value: int | float):
        if isinstance(value, (int, float)):
            value = int(value)
            if value < 1:
                warnings.warn(f"有效数字位数不能小于1，修改无效。")
            elif value > max_significance:
                warnings.warn(f"有效数字位数超过计算程序精度: {max_significance}，已自动调整为{max_significance}。")
                self.__significance = max_significance
            else:
                self.__significance = value
        else:
            warnings.warn(f"有效数字必须为整数类型，修改无效。")

    def copy(self) -> Quantity:
        return self.__copy__()

    def get_value(self, unit_str: str | None = None) -> float:
        """
        获取物理量在特定单位下的数值，无视科学计数法以及有效数字应用设置。
        :param unit_str: 目标单位字符串。若为 None，则返回当前单位制下的数值。
        :return: 换算后的浮点数值。
        """
        if unit_str is None:
            return self.value

        if not isinstance(unit_str, str):
            raise TypeError(f"单位必须为字符串类型，当前为: {type(unit_str).__name__}")

        target = Quantity(1, unit_str)
        result = self / target

        if result.unit_dict:
            raise ValueError(f"量纲不匹配：无法将 [{self.unit_str}] 转换为 [{unit_str}]")

        return result.value
    
    def get_str(self, unit_str: str | None = None) -> str:
        """
        在特定单位下将物理量转化为字符串信息，遵循科学计数法以及有效数字应用设置。
        :param unit_str: 目标单位字符串。若为 None，则返回当前单位制下的数值。
        """
        if unit_str is None:
            return str(self)

        if not isinstance(unit_str, str):
            raise TypeError(f"单位必须为字符串类型，当前为: {type(unit_str).__name__}")

        target = Quantity(1, unit_str)
        result = self / target

        if result.unit_dict:
            raise ValueError(f"量纲不匹配：无法将 [{self.unit_str}] 转换为 [{unit_str}]")

        return f"{str(result)} {unit_str}".strip()

    def show(self, unit_str: str | None = None) -> Quantity:
        """
        在特定单位下print物理量，遵循科学计数法以及有效数字应用设置。
        :param unit_str: 目标单位字符串。若为 None，则返回当前单位制下的数值。
        """
        print(self.get_str(unit_str))
        return self


# 数学常数
pi = Quantity(3.141592653589793)
e_ = Quantity(2.718281828459045)
one = Quantity(1)
# 物理学常量(第26届国际计量大会决议定义精确值)
c = Quantity(2.99792458e8, "m/s", 15)
h = Quantity(6.62607015e-34, "J*s", 15)
e = Quantity(1.602176634e-19, "C", 15)
k = Quantity(1.380649e-23, "J/K", 15)
NA = Quantity(6.02214076e23, "mol-1", 15)
# 测定常数(数据来源:https://zh.webqc.org/constants.php)
G = Quantity(6.6742e-11, "N*m2/kg2", 5)
me = Quantity(9.1093826e-31, "kg", 8)
mp = Quantity(1.67262171e-27, "kg", 9)
mn = Quantity(1.67492728e-27, "kg", 9)
# 计算常数
h_ = h / 2 / pi
mu0 = Quantity(1e-7, "H/m", 15) * 4 * pi
ep0 = one / c ** 2 / mu0
# 组合常数
alpha = e * e / pi / ep0 / (h_ * c) / 4
# 磁子
muB = e * h_ / me / 2
muN = e * h_ / mp / 2

if __name__ == "__main__":
    pass

    
