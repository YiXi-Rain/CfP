# coding: UTF-8
precision = 10


class SN:  # SN即scientific notation(科学计数法)
    """提供科学计数法表示的数。所有方法均不改变原来的值,且除show外return均不为None。"""

    def __init__(self, value, sig: int = precision, simple: bool = False, sign=None, abs_=None, power=None):
        """
        给数字设定有效位数
        :param value: 数的值
        :param sig: 有效数字位数,默认10;如有需要请手动把默认值改成None,那么会根据输入值计算有效数字
        :param simple: 是否开启简化生成模式
        :param sign: 简化生成时传入sign
        :param abs_: 简化生成时传入abs
        :param power: 简化生成时传入power
        """
        if type(value) is SN:
            self.value = value.value
            self.sig = value.sig
            self.sign = value.sign
            self.abs = value.abs_
            self.power = value.power
        else:
            if not simple:  # 标准生成程序
                try:
                    if sig > precision:
                        sig = precision  # 浮点运算时总会出现如.000000000000001的结果，规定最高有效数字位数配合函数round消除
                    elif sig < 1:
                        sig = None
                except TypeError:  # 没有设定有效数字位数,需要自动生成
                    sig = None
                if (not sig) and (type(value) is int):  # 如果传入整数
                    sig = len(str(value))
                self.value = value  # 值value
                # 符号sign
                if value >= 0:
                    self.sign = 1
                else:
                    self.sign = -1
                # 指数power&绝对值abs
                self.abs = value * self.sign  # 取绝对值方便科学计数法的处理
                self.power = 0
                if value != 0:  # 为零会死循环
                    while self.abs / 10 >= 1:  # 系数大于等于10时的处理
                        self.power += 1
                        self.abs = self.abs / 10
                    while self.abs * 10 < 10:  # 系数小于1时的处理
                        self.power -= 1
                        self.abs = self.abs * 10
                    self.abs = round(self.abs, precision)  # abs可能含有.0000000000001
                    # 保留规定有效数字
                    if sig:
                        self.sig = sig
                    else:  # 根据abs自动生成有效数字位数
                        self.sig = len(str(self.abs)) - 1  # 减去小数点占位
                    self.abs, self.power = self.__abs_round(self.sig)
                    self.value = self.sign * self.abs * 10 ** self.power  # value有效数字比设定多一位
                    self.abs, self.power = self.__abs_round(self.sig - 1)
                else:  # 如果为0
                    self.sig = precision
                self.abs *= 1.0  # 确保abs为浮点数
            else:  # 简化生成模式
                self.value = value
                self.sig = sig
                self.sign = sign
                self.abs = abs_
                self.power = power

    def __abs_round(self, n):
        """
        abs属性的round方法,如果进位将会自动再次round并且修改abs和power值(不改变原值)
        :param n: 保留小数的位数
        :return abs和power
        """
        abs_ = round(self.abs, n)
        power = self.power
        while abs_ / 10 >= 1:  # 上一步round存在进位可能性，需检验有效数字位数
            power += 1
            abs_ = abs_ / 10
        return round(abs_, n), power

    def __neg__(self):
        return SN(-self.value, self.sig, True, -self.sign, self.abs, self.power)

    def __pos__(self):
        return self

    def __str__(self):
        if -3 < self.power < 3:
            return self.str_if_power(0)
        else:
            return self.str_if_power()

    def __abs_if_change_n(self, change, n):
        if n:
            return round(self.abs * 10 ** change, n)
        else:
            return round(self.abs * 10 ** change)

    def __abs__(self):
        return self.abs

    def __add(self, other):
        """
        实际调用的加法function
        :param other: 与之相加的另一个SN类实例
        :return: 和的SN类实例
        """
        value = self.value + other.value
        str1 = self.abs_str_if_power(self.power)
        str2 = other.abs_str_if_power(self.power)
        sig = self.sig  # __add__方法中的if语句保证了结果的有效数字不超过self(加法不进位/减法不降数量级时)
        if len(str1) > len(str2):
            sig -= len(str1) - len(str2)  # 加法不进位/减法不降数量级时的有效数字位数
        if self.sign * other.sign == 1:  # 对abs而言是加法
            if abs(value) >= 10:  # 加法进位
                sig += 1
                if sig == 2:  # 原来只有一位有效数字,低位不可能进位,和的有效数字一定是2位
                    return SN(value, sig)
            if sig == 1:  # 整数加小数且最高位不进位,低位不可能进位,和的有效数字一定是1位
                return SN(value, sig)
            try:
                n1 = int(str1[sig])
            except IndexError:
                n1 = 0
            try:
                n2 = int(str1[sig])
            except IndexError:
                n2 = 0
            if n1 + n2 >= 10:  # 低位发生进位
                return SN(value, sig - 1)
            else:
                return SN(value, sig)
        else:  # 加法的有效数字已经无懈可击了,减法的暂时先用着吧
            sn = SN(value, None)  # 根据差的形式直接生成有效数字位数
            if sn.sig <= sig + 1:  #
                return sn.set_sig(sn.sig - 1)
            else:
                return sn.set_sig(sig)

    def __add__(self, other):
        if type(other) is SN:
            if self.power > other.power:  # 以power更大的为基准
                return self.__add(other)
            elif (self.power == other.power) and (self.sig < other.sig):  # power相同时,以sig更少的为基准
                return self.__add(other)
            else:
                return other.__add(self)
        else:
            return self + SN(other)

    def __sub__(self, other):
        if type(other) is SN:
            return self + -other
        else:
            return self - SN(other)

    def __mul__(self, other):
        if type(other) is SN:
            return SN(self.value * other.value, min(self.sig, other.sig))
        else:
            return self * SN(other)

    def __pow__(self, power, modulo=None):
        return SN(self.value ** power, self.sig)

    def __truediv__(self, other):
        if type(other) is SN:
            return SN(self.value / other.value, min(self.sig, other.sig))
        else:
            return self / SN(other)

    def set_sig(self, sig):
        """
        设置有效数字位数为n,不改变原值
        :param sig: 有效数字位数
        :return: 设置有效数字位数为n后的新SN类实例
        """
        if (sig > precision) or (sig < 1):
            sig = precision  # 浮点运算时总会出现诸如.000000000000001/.999999999998的结果，规定最高有效数字位数配合函数round消除
        abs_, power = self.__abs_round(sig)
        value = self.sign * abs_ * 10 ** power  # value有效数字比设定多一位
        abs_, power = self.__abs_round(sig - 1)
        return SN(value, sig, True, self.sign, abs_, power)

    def abs_if_power(self, power):
        change = self.power - power
        n = self.sig - 1 - change
        if n:
            return round(self.abs * 10 ** change, n)
        else:
            return round(self.abs * 10 ** change)

    def abs_str_if_power(self, power):
        """给定一个power,返回对应的abs字符串(保证有效数字位数)"""
        change = self.power - power
        n = self.sig - 1 - change
        string = str(self.__abs_if_change_n(change, n))
        if n > 0:  # 可能需要补充0
            string += "0" * (n + 2 - len(string))
        return string

    def str_if_power(self, power=None):
        """
        返回给定数量级下的科学计数法表示
        :param power: 数量级,留空则使用标准科学计数法
        """
        if power is None:
            power = self.power
        string = self.abs_str_if_power(power)
        if self.sign == -1:
            string = "-" + string
        if power:
            return string + f"e{power}"
        else:
            return string

    def show(self, power=None):
        """
        给定幂指数(或者说数量级),打印该数量级下的科学计数法表示结果
        :param power: 数量级,留空则使用标准科学计数法
        """
        print(self.str_if_power(power))
