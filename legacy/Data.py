from SN import SN


def data_format(data_str: str):
    """
    格式化传入的数据,返回其转化成的列表和其长度
    :param data_str: 从excel paste的数据
    """
    data_str = data_str.replace(' ', '')
    while data_str.startswith("\n") or data_str.startswith("\t"):
        data_str = data_str[1:]
    while data_str.endswith("\n") or data_str.endswith("\t"):
        data_str = data_str[:-1]
    data_str = data_str.replace('\t', ',').replace('\n', ',')
    data_list = data_str.split(",")
    n = len(data_list)
    for i in range(n):
        data_list[i] = eval(data_list[i])
    return data_list, n


class Data:
    """
    attr清单
    data: 样本数据元组
    n: 样本容量
    aver: 样本均值(未对齐有效位数)
    var: 样本方差
    std: 样本标准差
    std_all: (样本视作)总体标准差
    asd: aver_standard_deviation均值的标准偏差(未校正)
    red: relative_deviation均值的相对偏差(未校正)
    a_eff: aver_effective对齐有效位数的样本均值(未校正)
    asd_fix: 均值的标准偏差(n<=10时校正)
    red_fix: 均值的相对偏差(n<=10时校正)
    a_eff_fix: 对齐有效位数的样本均值(n<=10时校正)
    """
    def __init__(self, data_list: str or list, sig=None):
        """
        输入样本数据，保存样本数据、样本容量、样本均值、样本方差、(样本视作)总体标准差、样本标准差、均值的标准偏差(校正或未校正)
        大部分属性被隐藏了，可以使用intro/show_all方法查看
        """
        if type(data_list) is str:
            data_list, self.__n = data_format(data_list)
        else:  # 记录样本容量
            self.__n = len(data_list)
        if not sig:  # 计算均值(样本)的有效数字
            sig_set = set()
            for i in range(self.__n):
                sig_set.add(SN(data_list[i], None).sig)
            sig = max(sig_set)
        self.__aver = SN(sum(data_list) / self.__n, sig)  # 记录样本均值
        self.var = SN(0)
        self.__data = []  # 储存样本数据
        for i in range(self.__n):
            sn = SN(data_list[i], sig)
            self.__data.append(sn)
            self.var += (sn - self.__aver) ** 2  # 计算样本方差(未除以n)
        self.__data = tuple(self.__data)  # 元组不能修改,防止数据被误删改
        self.std = (self.var / (self.__n - 1)) ** 0.5  # 计算样本标准差
        self.var /= self.__n  # 计算样本方差(除以n)
        self.std_all = self.var ** 0.5  # 计算(样本视作)总体标准差
        self.__asd = self.std / self.__n ** 0.5  # 计算平均值的标准偏差(未校正)
        self.__red = (self.__asd / self.__aver).set_sig(2)  # 计算平均值的相对偏差(未校正),relative_deviation
        self.__asd = (self.__red * self.__aver).set_sig(1)  # 平均值的标准偏差只有一位有效数字aver_standard_deviation
        self.__a_eff = self.__aver.set_sig(len(str(int(self.__aver.abs_if_power(self.__asd.power)))))  # 重新规定均值的有效数字
        if self.__n <= 10:
            tuple683 = (1.84, 1.32, 1.20, 1.14, 1.11, 1.09, 1.08, 1.07, 1.06)  # 置信度为0.683时用stu分布近似正态分布的校正因子
            self.__asd_fix = self.__asd * tuple683[self.__n - 2]  # 计算平均值的标准偏差(校正)
            self.__red_fix = (self.__asd_fix / self.__aver).set_sig(2)  # 计算平均值的相对偏差(校正)
            self.__asd_fix = (self.__red_fix * self.__aver).set_sig(1)
            self.__a_eff_fix = self.__aver.set_sig(len(str(int(self.__aver.abs_if_power(self.__asd_fix.power)))))
        else:  # 缺少>10时的校正数据
            self.__asd_fix = self.__asd
            self.__red_fix = self.__red
            self.__a_eff_fix = self.__a_eff

    def __add__(self, other):
        if type(other) is str:
            other = data_format(other)[0]
        elif type(other) is not list:
            other = list(other)
        return Data(self.__data + other)

    def data(self):
        """返回样本数据元组(元组不能修改,防止数据被误删改)"""
        return tuple(self.__data)

    def show(self, fix=False):
        if not fix:
            print("测量值x=(" + self.__a_eff.abs_str_if_power(self.__a_eff.power) + "±"
                  + self.__asd.abs_str_if_power(self.__a_eff.power) + f")e{self.__a_eff.power}")
            print(f"相对偏差Ex={self.__red.abs_if_power(-2)}%")
            return self
        elif self.__n <= 10:
            print("校正测量值x=(" + self.__a_eff_fix.abs_str_if_power(self.__a_eff_fix.power) + "±"
                  + self.__asd_fix.abs_str_if_power(self.__a_eff_fix.power) + f")e{self.__a_eff_fix.power}")
            print(f"校正相对偏差Ex_fix={self.__red_fix.abs_if_power(-2)}%")
            return self
        else:
            print("样本容量大于10,缺少校正参数,但误差小于6%")
            return self.show()


if __name__ == "__main__":
    data = '''
    4227.192609
    4252.941184
    4214.862684
    4339.041556
    4352.289574
    4316.893686
    4283.282567
    4127.788616
    4129.973617
    '''
    a = Data(data).show()
