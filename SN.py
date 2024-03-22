# coding: UTF-8
precision = 10


class SN:  # SN即scientific notation(科学计数法)
    """提供科学计数法表示的数"""

    def __init__(self, value, sig: int = precision, simple: bool = False, sign=None, abs_=None, power=None):
        """
        给数字设定有效位数
        :param value: 数的值
        :param sig: 有效数字位数
        :param simple: 是否开启简化生成模式
        :param sign: 简化生成时传入sign
        :param abs_: 简化生成时传入abs
        :param power: 简化生成时传入power
        """
        if not simple:  # 标准生成程序
            self.value = value  # 值value
            # 符号sign
            if value >= 0:
                self.sign = 1
            else:
                self.sign = -1
            # 指数power&绝对值abs
            self.abs = abs(value)  # 取绝对值方便科学计数法的处理
            self.power = 0
            if value != 0:  # 为零会死循环
                while self.abs / 10 >= 1:  # 系数大于等于10时的处理
                    self.power += 1
                    self.abs = self.abs / 10
                while self.abs * 10 < 10:  # 系数小于1时的处理
                    self.power -= 1
                    self.abs = self.abs * 10
                # 保留规定有效数字
                self.set_sig(sig)
            else:  # 值为零时的处理
                self.abs = 0.0  # 确保coefficient为浮点数
        else:  # 简化生成模式
            self.value = value
            self.sig = sig
            self.sign = sign
            self.abs = abs_
            self.power = power

    def abs_round(self, n):
        """
        abs属性的round方法,如果进位将会自动再次round并且修改abs和power值
        :param n:
        :return:
        """
        self.abs = round(self.abs, n)
        while self.abs / 10 >= 1:  # 上一步round存在进位可能性，需检验有效数字位数
            self.power += 1
            self.abs = self.abs / 10
        return round(self.abs, n)

    def set_sig(self, sig):
        """
        设置有效数字位数为n
        :param sig: 有效数字位数
        :return: 是否成功设置为指定值
        """
        if (sig > precision) or (sig < 1):
            sig = precision  # 浮点运算时总会出现诸如.000000000000001/.999999999998的结果，规定最高有效数字位数配合函数round消除
            self.value = self.sign * self.abs_round(sig) * 10 ** self.power  # value有效数字比设定多一位
            self.abs = self.abs_round(sig - 1)
            self.sig = sig
            return False
        else:
            self.value = self.sign * self.abs_round(sig) * 10 ** self.power  # value有效数字比设定多一位
            self.abs = self.abs_round(sig - 1)
            self.sig = sig
            return True

    def __neg__(self):
        return SN(-self.value, self.sig, True, -self.sign, self.abs, self.power)

    def __pos__(self):
        return self

    def __str__(self):
        string = str(self.abs)
        string += "0" * (1 + self.sig - len(string))
        if self.sign == -1:
            string = "-" + string
        if self.power == 0:
            return string
        else:
            return string + f"e{self.power}"

    def abs_if_power(self, power):
        """
        给定一个power,返回对应的abs值
        :param power: 给定科学计数法的指数
        :return: 给定指数下对应的abs值
        """
        return self.abs * 10 ** (self.power - power)

    def __add(self, other):
        """
        实际调用的加法function
        :param other: 与之相加的另一个SN类实例
        :return: 和的SN类实例
        """
        str1 = str(self.abs)
        str2 = str(other.abs_if_power(self.power))
        sig = self.sig  # 以加减法结果的有效数字不超过原来power更大的那个
        if len(str1) > len(str2):
            sig -= len(str1) - len(str2)
        return SN(self.value + other.value, sig)

    def __add__(self, other):
        if type(other) is SN:
            if self.power >= other.power:  # 以power更大的为基准
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

    def str(self, power="default"):
        """
        返回给定power下的字符串表示
        :param power: 留空表示不使用科学计数法
        :return: str
        """
        if power == "default":
            return str(self.value)
        else:
            return f"{self.sign * self.abs_if_power(power)}e{power}"

    def show(self, power):
        print(self.str(power))
