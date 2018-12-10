#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# vim: fileencoding=utf-8 autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

# 该程序的目的是在已知冰箱内容尺寸, 离心管尺寸的前提下, 假设一些间隙数据, 最大化
# 估算离心管冻存盒的尺寸, 使得总空间利用率最大化.
#
# 尺寸数据单位均为 mm

import numpy as np

class Tube:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def add_horizontal_margin(self):
        return self.cap_width + self.cap_margin*2

    def add_depth_margin(self):
        return self.add_horizontal_margin()

    def add_top_margin(self):
        return self.height + self.top_margin

    def get_volume(self):
        return  self.height * self.add_horizontal_margin()**2

    def get_horizontal_space(self):
        return self.add_horizontal_margin()

    def get_depth_space(self):
        # 因为管子所占空间是个正方形, 所有水平空间和深度空间一样
        return self.get_horizontal_space()


class TubeBox:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


    def add_top_margin(self):
        return self.height + self.top_margin

    def get_volume(self):
        return self.width * self.depth * self.height

    def get_hole_diameter(self, tube_diameter):
        # 冻存盒的管孔直径
        return tube_diameter + 1


class DrawerBox:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def remove_margin_for_horizontal(self):
        return self.width \
                - self.margin_with_shell*2 \
                - self.margin_with_tubebox_horizontal*2

    def remove_margin_for_depth(self):
        # 深度方向可能会放很多个盒子, 所有多留出一些空间
        return self.depth - self.thickness*2 - self.margin_with_tubebox_depth

    def get_width_for_tubebox(self):
        return self.remove_margin_for_horizontal()

    def get_depth_for_tubebox(self):
        return self.remove_margin_for_depth()

    def get_margin_with_tubebox_horizontal(self):
        return self.margin_with_tubebox_horizontal * 2

    def get_margin_with_shell(self):
        return self.margin_with_shell * 2

    def get_depth_for_drawer(self):
        return self.depth - self.thickness

    def get_drawer_width(self, tubebox_width):
        return tubebox_width + self.get_margin_with_tubebox_horizontal()

    def get_width(self, tubebox_width):
        return tubebox_width  \
               + self.get_margin_with_tubebox_horizontal()  \
               + self.get_margin_with_shell()  \
               + self.thickness*2


class Refrigerator:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def remove_margin_horizontal(self):
        return self.inner_width - self.margin*2

    def remove_margin_vertical(self):
        return (
                (self.inner_height - (self.division-1)*self.plate_thickness) / self.division
               ) - self.margin

    def remove_margin_depth(self):
        return self.inner_depth - self.margin*2

    def get_height_for_drawerbox(self):
        return self.remove_margin_vertical()

    def get_width_for_drawerbox(self):
        # 该width是水平方向上所有可以用来摆放抽屉架的长度, 而非单个抽屉架的长度
        return self.remove_margin_horizontal()

    def get_depth_for_drawerbox(self):
        return self.remove_margin_depth()

    def get_volume(self):
        return self.inner_width * self.inner_depth * self.inner_height



class Computer:

    def compute_percent(self, a, b):
        return "%.2f%%" % (100*float(a)/float(b))

    def is_even(self, x):
        if x % 2 == 0:
            return True
        else:
            return False

    def compute_optimal_tubebox_size(self, tube, large_tube,  tubebox, drawerbox, refrigerator):
        # 该算法适用于 0.5mL离心管的冻存
        # 该计算方案中本来有3个变量: 盒子的宽度, 盒子的深度, 冰箱隔断数.
        # 盒子的高度信息直接通过离心管的高度加上垂直方向的空间冗余可以计算出来
        # 冰箱隔断的数量范围有限, 采用参数手动控制, 于是该方案就变成了
        # 二元一次方程求最优解问题. 所以,基本思路是通过所有已知参数计算
        # 整个冰箱的离心管的最大存储量和最小空间浪费.

        # 通过已知离心管的各尺寸数据, 以及离心管之间的间隙数据, 计算得到包含冻存盒
        # 所有可能宽度数据的一个一维数组
        candidate_tubebox_width_pool = []
        candidate_tube_num_horizontal_pool = []
        for num_tube in range(tube.num_min_horizontal, tube.num_max_horizontal+1):
            candidate_tubebox_width_pool.append(
                    # 存放离心管的水平空间 + 两端盒子的厚度
                    num_tube*tube.get_horizontal_space() + tubebox.thickness*2
                    )
            candidate_tube_num_horizontal_pool.append(num_tube)

        # 计算一个包含冻存盒所有可能深度数据的一个一维数组
        candidate_tubebox_depth_pool = []
        candidate_tube_num_depth_pool = []
        for num_tube in range(tube.num_min_depth, tube.num_max_depth+1):
            candidate_tubebox_depth_pool.append(
                    # 存放离心管的垂直空间 + 两端盒子的厚度
                    num_tube*tube.get_depth_space() + tubebox.thickness*2
                    )
            candidate_tube_num_depth_pool.append(num_tube)



        candidate_tubebox_width_array = np.array(candidate_tubebox_width_pool)
        candidate_tubebox_depth_array = np.array(
                [[i] for i in candidate_tubebox_depth_pool]
                )


        # 计算单个抽屉架所有可能宽度数据的一个一维数组
        candidate_drawerbox_width_array = drawerbox.get_width(candidate_tubebox_width_array)

        # 计算水平方向可以存放多少个抽屉架, 因为水平方向每个抽屉架只存放一个冻存盒,
        # 所以, 也就相当于计算到了水平方向可以存放多少个冻存盒
        candidate_drawerbox_horizontal_num_array = np.floor_divide(
                                                    refrigerator.get_width_for_drawerbox(),
                                                    candidate_drawerbox_width_array)
        candidate_tubebox_num_horizontal_array = candidate_drawerbox_horizontal_num_array

        # 计算深度方向上可以存放多少个冻存盒
        candidate_tubebox_num_depth_array = np.floor_divide(
                refrigerator.get_depth_for_drawerbox(),
                candidate_tubebox_depth_array
                )

        # 计算高度方向上, 冰箱里的一层空间可以存放多少层冻存盒
        tubebox_num_vertical = refrigerator.get_height_for_drawerbox() \
                                // drawerbox.drawer_height

        # 计算一个冰箱里能存放的总冻存盒数量
        tube_num_horizontal_array = np.array(candidate_tube_num_horizontal_pool)
        tube_num_depth_array = np.array(
                [[i] for i in candidate_tube_num_depth_pool]
                )
        tube_num_for_tubebox_array = tube_num_horizontal_array * tube_num_depth_array
        total_tubebox_num_array = candidate_tubebox_num_horizontal_array  \
                                  * candidate_tubebox_num_depth_array  \
                                  * tubebox_num_vertical  \
                                  * refrigerator.division
        total_tube_num_array = total_tubebox_num_array  \
                               * tube_num_for_tubebox_array \
                               - total_tubebox_num_array

        # 找到离心管存储量的最优解
        indices = np.transpose(np.where(total_tube_num_array == total_tube_num_array.max()))
        max_tube_num = total_tube_num_array.max()

        # 离心管所占空间容积
        tube_volume = tube.get_volume()
        refrigerator_volume = refrigerator.get_volume()

        print("冰箱型号为: %s" % refrigerator.model)
        print("冰箱市场价格为：%d 元, 折扣是：%.4f, 折后价格是：%d" % \
                (refrigerator.price, refrigerator.discount, refrigerator.price*refrigerator.discount))
        print("如下会列出针对该冰箱计算出来的所有可能的最优冻存盒尺寸")
        print("如下所有长度数据的单位均为: mm")
        print("冰箱内部空间尺寸: width %s, depth %s, height: %s\n"
                % (refrigerator.inner_width,
                    refrigerator.inner_depth,
                    refrigerator.inner_height))

        for index in indices:

            # 冻存盒的深度方向存放的离心管数量
            tube_num_depth = tube_num_depth_array[index[0]][0]
            # 冻存盒的宽度方向存放的离心管数量
            tube_num_horizontal = tube_num_horizontal_array[index[1]]
            # 单个冻存盒能存储的离心管数量
            # 因为第一个孔位置被用来贴二维码,所以需要减去1.
            tube_num_for_tubebox = tube_num_depth * tube_num_horizontal- 1
            total_num_tubebox = total_tubebox_num_array[index[0], index[1]]

            # 冻存盒的深度
            tubebox.depth = candidate_tubebox_depth_array[index[0]][0]
            tubebox.width = candidate_tubebox_width_array[index[1]]
            tubebox_volumn = tubebox.get_volume()

            # 计算50mL离心管的存放数量和排布方式
            large_tube_num_horizontal = tubebox.width // large_tube.get_horizontal_space()
            large_tube_num_depth = tubebox.depth // large_tube.get_depth_space()
            # 因为第一个孔位置被用来贴二维码,所以需要减去1.
            large_tube_num_for_tubebox = large_tube_num_horizontal * large_tube_num_depth - 1

            # 抽屉架的深度
            drawerbox.depth = refrigerator.get_depth_for_drawerbox()

            # 水平方向上抽屉的个数
            drawer_num_horizontal = candidate_drawerbox_horizontal_num_array[index[1]]
            # 水平方向上冻存盒的个数
            tubebox_num_horizontal = drawer_num_horizontal
            # 深度方向上冻存盒的个数
            tubebox_num_depth = candidate_tubebox_num_depth_array[index[0]][0]
            # 一个冰箱里抽屉总个数
            totoal_drawerbox_num = drawer_num_horizontal * refrigerator.division

            # 冻存盒所占总空间容积
            total_tubebox_volumn = drawer_num_horizontal \
                                   * tubebox_num_depth \
                                   * tubebox_num_vertical \
                                   * tubebox_volumn \
                                   * refrigerator.division
            # 一个冰箱里所有抽屉架的总容积
            total_drawbox_volumn  = refrigerator.get_depth_for_drawerbox()   \
                                    * refrigerator.get_width_for_drawerbox()   \
                                    * refrigerator.get_height_for_drawerbox()  \
                                    * refrigerator.division

            print("0.5mL离心管存储最大量为: %d, 最优解坐标为: %s"
                    % (max_tube_num, index))
            print("每个冻存盒可以存放0.5mL离心管数量: %d" % tube_num_for_tubebox)
            print("冻存盒里的0.5mL离心管排布方式为: 水平方向: %d, 深度方向: %d" % \
                    (tube_num_horizontal, tube_num_depth))
            print("如果用来存放50mL离心管, 做多可存放数量为: %d" % large_tube_num_for_tubebox)
            print("50mL离心管在冻存盒里的排布方式是: 水平方向: %d, 深度方向: %d" % \
                    (large_tube_num_horizontal, large_tube_num_depth))
            print("冻存盒深度为: %d" % tubebox.depth)
            print("冻存盒宽度为: %d" % tubebox.width)
            print("冻存盒高度为: %d" % tubebox.height)
            print("冻存盒的0.5mL管孔直径为：%d" % tubebox.get_hole_diameter(tube.diameter))
            print("冻存盒的50mL管孔直径为：%d" % tubebox.get_hole_diameter(large_tube.diameter))
            print("冻存盒总数量为: %d" % total_num_tubebox)

            print("抽屉架深度为: %d"
                    % refrigerator.get_depth_for_drawerbox())
            print("抽屉架宽度为: %d" % drawerbox.get_width(tubebox.width))
            print("抽屉架高度为: %d"
                    % refrigerator.get_height_for_drawerbox())
            print("单层抽屉的高度为: %d" % drawerbox.drawer_height)
            print("单层抽屉的宽度为: %d" % drawerbox.get_drawer_width(tubebox.width))
            print("单层抽屉的深度为: %d" % drawerbox.get_depth_for_drawer())
            print("一个冰箱总共分 %d 层空间" % refrigerator.division)
            print("每层水平方向抽屉架个数为: %d"
                    % drawer_num_horizontal)
            print("%s 层抽屉架总个数为: %d" %
                    (refrigerator.division, totoal_drawerbox_num))
            print("每个抽屉架可以放 %d 层抽屉" % tubebox_num_vertical)
            print("一个抽屉深度方向可放冻存盒个数为：%d" % tubebox_num_depth)
            print("以离心管为有效容积计算, 冰箱总空间利用率为: %s" %
                    computer.compute_percent(tube_volume*max_tube_num,
                                            refrigerator_volume))
            print("以冻存盒为有效容积计算, 冰箱总空间利用率为: %s"
                    % computer.compute_percent(total_tubebox_volumn,
                                            refrigerator_volume))
            print("以抽屉架为有效容积计算, 冰箱总空间利用率为: %s"
                    % computer.compute_percent(total_drawbox_volumn,
                                            refrigerator_volume))
            print("每根离心管的单位耗电功率为: %.4f w" % (
                                    float(refrigerator.power) /
                                    float(max_tube_num)))
            print("每根离心管占冰箱价格成本: %.4f 元\n" % (float(refrigerator.price*refrigerator.discount)/float(max_tube_num)))
        print("-"*80)



if __name__ == "__main__":

    # --------------------- 计算-80冰箱内的冻存架尺寸 --------------- #
    # 设置离心管所有已知的尺寸参数

    # >>> 请输入你自己的尺寸要求
    tube = Tube(
            cap_width          = 0,   # 管帽宽度
            height             = 0,   # 离心管高度
            cap_margin         = 0,   # 两个离心管之间的距离的一半
            top_margin         = 0,   # 离心管跟盒子上盖之间的距离
            num_min_horizontal = 0,   # 水平方向最少存放离心管数量
            num_max_horizontal = 0,   # 水平方向最多存放离心管数量
            num_min_depth      = 0,   # 深度方向最少存放离心管数量
            num_max_depth      = 0,   # 深度方向最多存放离心管数量
            diameter           = 0,   # 离心管的直径
            )

    # >>> 请输入你自己的尺寸要求
    large_tube = Tube(
            heigth     = 0,   # 带盖总高度
            diameter   = 0,  # 管体直径
            cap_width  = 0, # 盖子的直径
            cap_margin = 0, # 两个离心管之间的距离的一半
            top_margin = 0, # 离心管跟盒子上盖之间的距离
            )

    # 设置离心管冻存盒所有已知的尺寸参数
    # >>> 请输入你自己的尺寸要求
    tubebox = TubeBox(
            height     = tube.add_top_margin(), # 冻存盒的高度通过离心管的高度算出来
            top_margin = 0,                     # 冻存盒跟抽屉上盖之间的距离
            thickness  = 0,                     # 冻存盒的纸璧厚度
            )

    # 设置抽屉架的尺寸数据
    # >>> 请输入你自己的尺寸要求
    drawerbox = DrawerBox(
            drawer_height                  = tubebox.add_top_margin(),
            thickness                      = 0,                         # 抽屉架钢板厚度
            margin_with_shell              = 0,                         # 抽屉架跟抽屉板之间的单侧间隙
            margin_with_tubebox_horizontal = 0,                         # 抽屉板跟冻存盒之间的单侧间隙
            margin_with_tubebox_depth      = 0,                         # 深度方向有好多个盒子, 这里留出盒子
            )                                                           # 之间的空隙,盒子跟抽屉板之间的空隙的总和,
                                                                        # 抽屉拉环占去了大概5mm的空间


    # 设置冰箱的所有已知的尺寸数据
    # >>> 请输入你自己的尺寸要求
    refrigerator_list = []
    refrigerator_list.append(Refrigerator(
        inner_width     = 0,              # 冰箱内部空间的宽度
        inner_depth     = 0,              # 冰箱内部空间的深度
        inner_height    = 0,              # 冰箱内部空间的高度
        division        = 0,              # 冰箱内部空间会分割成几个小空间
        plate_thickness = 0,              # 空间分割钢板的厚度
        margin          = 0,              # 冰箱内壁跟抽屉架之间的空间
        power           = 0,              # 冰箱功率
        model           = "",             # 冰箱型号
        price           = 0,              # 价格
        discount        = 0,              # 折扣
    ))


    # 产生一个计算器
    for refrigerator in  refrigerator_list:
        computer = Computer()
        computer.compute_optimal_tubebox_size(tube, large_tube, tubebox, drawerbox, refrigerator)


