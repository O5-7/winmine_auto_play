import pywintypes
import win32api, win32con, win32gui
import pyautogui
import time
import numpy as np
import cv2
import os
import time

'''
-1 已探明
0 未探明
1-8 数字方块
9 已标记
'''


def kernel_deal(kernel: np.ndarray, chest_num: int):
    """
    对周围格子进行判断\n
    :param kernel: 格子核\n
    :param chest_num: 中心数\n
    :return: 处理\n
    """
    empty = 0
    certain = 0
    for line in kernel:
        for block in line:
            if block == 0:
                empty += 1
                continue
            if block == 9:
                certain += 1
    rest_mine = chest_num - certain
    if rest_mine == 0:
        """
        无地雷
        """
        return 0
    elif rest_mine == empty:
        """
        全地雷
        """
        return 1
    return 2


class winmine_auto:
    def __init__(self, mine_count: int):
        self.status = 0
        """
        0： 随机点击
        1： 死亡
        2： 初级确认
        3： 减法确认
        4： 高级确认
        5： 概率随即点击
        6： 二选一随机
        7: 胜利
        """
        self.mine_count = mine_count
        self.window_name = '扫雷'
        self.wh = win32gui.FindWindow(0, self.window_name)
        if self.wh == 0:
            return

        self.pos = (0, 0, 0, 0)
        self.game_size = np.zeros((2,))
        self.chest_size = np.zeros((2,))
        self.orgin_img = np.ndarray
        self.chest_img = np.ndarray
        self.get_screenshot()
        self.chest = np.zeros((self.chest_size[1], self.chest_size[0]), dtype=np.int8)
        self.uselese = np.zeros((self.chest_size[1], self.chest_size[0]), dtype=np.int8)
        self.get_chest()

        self.last_mine_click = np.ndarray
        self.last_no_mine_click = np.ndarray

    def get_screenshot(self):
        """
        获得游戏截图
        获得棋盘大小
        获得棋盘图片
        """
        win32gui.SetForegroundWindow(self.wh)
        self.pos = np.array(win32gui.GetWindowRect(self.wh))
        self.game_size = np.array([self.pos[2] - self.pos[0] - 6, self.pos[3] - self.pos[1] - 4])
        self.chest_size = ((self.game_size - np.array((20, 108))) / 16).astype(np.uint8)
        img_get = pyautogui.screenshot(
            region=[self.pos[0] + 3, self.pos[1] + 2, self.game_size[0], self.game_size[1]])
        self.orgin_img = np.array(img_get)
        self.chest_img = self.orgin_img[100:-8, 12:-8]

    def get_chest(self):
        for x in range(self.chest_size[1]):
            for y in range(self.chest_size[0]):
                # cv2.imshow('checing', self.chest_img[16 * x: 16 * x + 15, 16 * y:16 * y + 15])
                # cv2.waitKey(1)
                if np.all(self.chest_img[16 * x][16 * y] == 255):
                    '''
                    未探明 已标记
                    '''
                    if self.chest_img[16 * x + 5][16 * y + 5][0] == 255:
                        self.chest[x, y] = 9
                        continue
                else:
                    """
                    数字方块 已探明
                    """
                    color = self.chest_img[16 * x + 10][16 * y + 9]
                    if color[0] == 192 and color[1] == 192 and color[2] == 192:
                        self.chest[x, y] = -1
                        continue
                    if color[0] == 0 and color[1] == 0 and color[2] == 255:
                        self.chest[x, y] = 1
                        continue
                    if color[0] == 0 and color[1] == 128 and color[2] == 0:
                        self.chest[x, y] = 2
                        continue
                    if color[0] == 255 and color[1] == 0 and color[2] == 0:
                        self.chest[x, y] = 3
                        continue
                    if color[0] == 0 and color[1] == 0 and color[2] == 128:
                        self.chest[x, y] = 4
                        continue
                    if color[0] == 128 and color[1] == 0 and color[2] == 0:
                        self.chest[x, y] = 5
                        continue
                    if color[0] == 0 and color[1] == 128 and color[2] == 128:
                        self.chest[x, y] = 6
                        continue
                    if color[0] == 0 and color[1] == 0 and color[2] == 0:
                        self.chest[x, y] = 7
                        continue
                    if color[0] == 128 and color[1] == 128 and color[2] == 128:
                        self.chest[x, y] = 8
                        continue

    def find_num_chest(self, num: int):
        out = list()
        where = np.array(np.where(self.chest == num)).T
        for loc in where:
            out.append(list(loc))
        return out

    def click(self, clicks: np.ndarray, left_right: int):
        if left_right == 0:
            for click in clicks:
                pyautogui.click(self.pos[0] + 23 + click[1] * 16, self.pos[1] + 110 + click[0] * 16, button='left')
            pyautogui.moveTo(self.pos[0], self.pos[1])
            return
        elif left_right == 1:
            for click in clicks:
                pyautogui.click(self.pos[0] + 23 + click[1] * 16, self.pos[1] + 110 + click[0] * 16, button='right')
            pyautogui.moveTo(self.pos[0], self.pos[1])
            return

    def primer_find(self):
        out_useless = list()
        out_mine = list()
        out_no_mine = list()
        for chest_num in range(1, 9):
            locs = self.find_num_chest(chest_num)
            for loc in locs:
                x = loc[0]
                y = loc[1]
                if x != 0 and x != self.chest_size[1] and y != 0 and y != self.chest_size[0]:
                    '''8'''
                    kernel = np.array(self.chest[x - 1:x + 2, y - 1:y + 2])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs + loc - np.array((1, 1))
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
                ''''''
                if x == 0 and y == 0:
                    kernel = np.array(self.chest[x:x + 2, y:y + 2])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
                if x == 0 and y == self.chest_size[0]:
                    kernel = np.array(self.chest[x:x + 2, y - 1:y + 1])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs + loc - np.array((0, 1))
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
                if x == self.chest_size[1] and y == 0:
                    kernel = np.array(self.chest[x - 1:x + 1, y:y + 2])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs + loc - np.array((1, 0))
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
                if x == self.chest_size[1] and y == self.chest_size[0]:
                    kernel = np.array(self.chest[y - 1:y + 1, y - 1:y + 1])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs + loc - np.array((1, 1))
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
                ''''''
                if x == 0:
                    '''up'''
                    kernel = np.array(self.chest[x:x + 2, y - 1:y + 2])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs + loc - np.array((0, 1))
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
                if x == self.chest_size[1]:
                    '''down'''
                    kernel = np.array(self.chest[x - 1:x + 1, y - 1:y + 2])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs + loc - np.array((1, 1))
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
                if y == 0:
                    '''left'''
                    kernel = np.array(self.chest[x - 1:x + 2, y:y + 2])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs + loc - np.array((1, 0))
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
                if y == self.chest_size[0]:
                    '''right'''
                    kernel = np.array(self.chest[x - 1:x + 2, y - 1:y + 1])
                    kernel_locs = np.array(np.where(kernel == 0)).T
                    locs = kernel_locs + loc - np.array((1, 1))
                    deal = kernel_deal(kernel, chest_num)
                    if deal == 2:
                        continue
                    if deal == 1:
                        out_useless.append(loc)
                        for i in locs:
                            out_mine.append(list(i))
                        continue
                    elif deal == 0:
                        out_useless.append(loc)
                        for i in locs:
                            out_no_mine.append(list(i))
                        continue
                    continue
        return (np.unique(np.array(out_useless), axis=0),
                np.unique(np.array(out_mine), axis=0),
                np.unique(np.array(out_no_mine), axis=0),)

    def primer_click(self):
        self.get_screenshot()
        self.get_chest()
        useless, mine, no_mine = a.primer_find()
        if mine.size == 0 and no_mine.size == 0:
            return False
        if mine.shape == self.last_mine_click.shape and np.sum(np.abs(mine - self.last_mine_click)) == 0:
            if no_mine.shape == self.last_no_mine_click.shape and np.sum(
                    np.abs(no_mine - self.last_no_mine_click)) == 0:
                self.status = 1
                return True
        '''print(mine)
        print(no_mine)'''
        for useless_one in useless:
            self.uselese[useless_one[0], useless_one[1]] = 1
        self.click(no_mine, 0)
        self.click(mine, 1)
        self.last_mine_click = mine.copy()
        self.last_no_mine_click = no_mine.copy()
        return True

    def subtraction_deal(self, subtraction_able_one: np.ndarray):
        out_mine = list()
        out_no_mine = list()
        x0, y0, x1, y1 = subtraction_able_one[0], subtraction_able_one[1], subtraction_able_one[2], \
                         subtraction_able_one[3]
        A = self.chest[x0, y0]
        B = self.chest[x1, y1]
        dif = A - B
        kernel = self.chest[x0 - 1:x1 + 2, y0 - 1:y1 + 2]
        if kernel.shape == (3, 3):
            if x0 == x1:
                new_kernel = np.zeros((3, 4))
                new_kernel[:3, :3] = kernel
                kernel = new_kernel.copy()
            if y0 == y1:
                new_kernel = np.zeros((4, 3))
                new_kernel[:3, :3] = kernel
                kernel = new_kernel.copy()
        print(kernel)

        mine_A = 0
        empty_A = 0
        mine_B = 0
        empty_B = 0
        direction = -1

        if x0 == x1:
            '''
            横行结构
            '''
            direction = 0
            for x in range(3):
                if kernel[x, 0] == 0:
                    empty_A += 1
                    continue
                if kernel[x, 0] == 9:
                    mine_A += 1
                    continue

            for x in range(3):
                if kernel[x, 3] == 0:
                    empty_B += 1
                    continue
                if kernel[x, 3] == 9:
                    mine_B += 1
                    continue

        if y0 == y1:
            '''
            竖行结构
            '''
            direction = 1
            for y in range(3):
                if kernel[0, y] == 0:
                    empty_A += 1
                    continue
                if kernel[0, y] == 9:
                    mine_A += 1
                    continue

            for y in range(3):
                if kernel[3, y] == 0:
                    empty_B += 1
                    continue
                if kernel[3, y] == 9:
                    mine_B += 1
                    continue

        if dif == 0:
            if empty_A == 0 and mine_A == 0 and empty_B > 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 3] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 + 2])
                if direction == 1:
                    for y in range(3):
                        if kernel[3, y] == 0:
                            out_no_mine.append([x0 + 2, y0 - 1 + y])
            if empty_B == 0 and mine_B == 0 and empty_A > 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 0] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 - 1])
                if direction == 1:
                    for y in range(3):
                        if kernel[0, y] == 0:
                            out_no_mine.append([x0 - 1, y0 - 1 + y])
            if mine_A - mine_B == empty_B and mine_A > 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 0] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 - 1])
                        if kernel[x, 3] == 0:
                            out_mine.append([x0 - 1 + x, y0 + 2])
                if direction == 1:
                    for y in range(3):
                        if kernel[0, y] == 0:
                            out_no_mine.append([x0 - 1, y0 - 1 + y])
                        if kernel[3, y] == 0:
                            out_mine.append([x0 + 2, y0 - 1 + y])
            if mine_B - mine_A == empty_A and mine_B > 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 3] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 + 2])
                        if kernel[x, 0] == 0:
                            out_mine.append([x0 - 1 + x, y0 - 1])
                if direction == 1:
                    for y in range(3):
                        if kernel[3, y] == 0:
                            out_no_mine.append([x0 + 2, y0 - 1 + y])
                        if kernel[0, y] == 0:
                            out_mine.append([x0 - 1, y0 - 1 + y])

        if dif > 0:
            if mine_A + empty_A == dif and empty_A > 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 0] == 0:
                            out_mine.append([x0 - 1 + x, y0 - 1])
                if direction == 1:
                    for y in range(3):
                        if kernel[0, y] == 0:
                            out_mine.append([x0 - 1, y0 - 1 + y])
            if mine_A == dif and empty_A == 0 and empty_B > 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 3] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 + 2])
                if direction == 1:
                    for y in range(3):
                        if kernel[3, y] == 0:
                            out_no_mine.append([x0 + 2, y0 - 1 + y])
            if (mine_A - mine_B) == (dif + empty_B):
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 3] == 0:
                            out_mine.append([x0 - 1 + x, y0 + 2])
                if direction == 1:
                    for y in range(3):
                        if kernel[3, y] == 0:
                            out_mine.append([x0 + 2, y0 - 1 + y])
            if mine_A + empty_A - mine_B == dif:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 0] == 0:
                            out_mine.append([x0 - 1 + x, y0 - 1])
                        if kernel[x, 3] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 + 2])
                if direction == 1:
                    for y in range(3):
                        if kernel[0, y] == 0:
                            out_mine.append([x0 - 1, y0 - 1 + y])
                        if kernel[3, y] == 0:
                            out_no_mine.append([x0 + 2, y0 - 1 + y])
            if mine_A - mine_B == dif and empty_B == 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 0] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 - 1])
                if direction == 1:
                    for y in range(3):
                        if kernel[0, y] == 0:
                            out_no_mine.append([x0 - 1, y0 - 1 + y])

        if dif < 0:
            dif = -dif
            if mine_B + empty_B == dif and empty_B > 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 3] == 0:
                            out_mine.append([x0 - 1 + x, y0 + 2])
                if direction == 1:
                    for y in range(3):
                        if kernel[3, y] == 0:
                            out_mine.append([x0 + 2, y0 - 1 + y])
            if mine_B == dif and empty_B == 0 and empty_A > 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 0] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 - 1])
                if direction == 1:
                    for y in range(3):
                        if kernel[0, y] == 0:
                            out_no_mine.append([x0 - 1, y0 - 1 + y])
            if (mine_B - mine_A) == (dif + empty_A):
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 0] == 0:
                            out_mine.append([x0 - 1 + x, y0 - 1])
                if direction == 1:
                    for y in range(3):
                        if kernel[0, y] == 0:
                            out_mine.append([x0 - 1, y0 - 1 + y])
            if mine_B + empty_B - mine_A == dif:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 0] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 - 1])
                        if kernel[x, 3] == 0:
                            out_mine.append([x0 - 1 + x, y0 + 2])
                if direction == 1:
                    for y in range(3):
                        if kernel[0, y] == 0:
                            out_no_mine.append([x0 - 1, y0 - 1 + y])
                        if kernel[3, y] == 0:
                            out_mine.append([x0 + 2, y0 - 1 + y])
            if mine_B - mine_A == dif and empty_A == 0:
                if direction == 0:
                    for x in range(3):
                        if kernel[x, 3] == 0:
                            out_no_mine.append([x0 - 1 + x, y0 + 2])
                if direction == 1:
                    for y in range(3):
                        if kernel[3, y] == 0:
                            out_no_mine.append([x0 + 2, y0 - 1 + y])

        print(out_mine, out_no_mine)
        return out_mine, out_no_mine

    def subtraction_find(self):
        mine_list = list()
        no_mine_list = list()
        side_with_block = list()
        subtraction_able = list()
        '''
        找到邻边存在empty的方块
        '''
        for x in range(1, self.chest_size[1] - 1):
            for y in range(1, self.chest_size[0] - 1):
                if 1 <= self.chest[x, y] <= 8:
                    kernel = self.chest[x - 1:x + 2, y - 1:y + 2]
                    if 0 in kernel:
                        side_with_block.append(np.array([x, y]))

        side_with_block_array = np.array(side_with_block)
        if side_with_block_array.shape[0] == 0:
            return np.array(((-1, -1),)), np.array(((-1, -1),))
        '''
        通过数字方块找临边方块
        '''
        for x in range(1, self.chest_size[1] - 2):
            for y in range(1, self.chest_size[0] - 2):
                if 1 <= self.chest[x, y] <= 8:
                    if np.min(np.sum(np.abs(side_with_block_array - np.array([x + 1, y])), axis=1)) == 0:
                        subtraction_able.append([np.array([x, y, x + 1, y])])
                    if np.min(np.sum(np.abs(side_with_block_array - np.array([x, y + 1])), axis=1)) == 0:
                        subtraction_able.append([np.array([x, y, x, y + 1])])

        '''
        通过临边方块找数字方块
        '''
        for block in side_with_block:
            x = block[0]
            y = block[1]
            if 1 <= self.chest[x + 1, y] <= 8:
                subtraction_able.append([np.array([x, y, x + 1, y])])
            if 1 <= self.chest[x, y + 1] <= 8:
                subtraction_able.append([np.array([x, y, x, y + 1])])

        subtraction_able_uniqe = np.unique(np.array(subtraction_able), axis=0)
        subtraction_able_uniqe = subtraction_able_uniqe.reshape((-1, 4))

        for subtraction_able_one in subtraction_able_uniqe:
            print(subtraction_able_one)
            mine, no_mine = self.subtraction_deal(subtraction_able_one)
            if len(mine) > 0:
                for mine_block in mine:
                    if mine_block[0] != self.chest_size[1] and mine_block[1] != self.chest_size[0]:
                        mine_list.append(mine_block)
            if len(no_mine) > 0:
                for no_mine_block in no_mine:
                    if no_mine_block[0] != self.chest_size[1] and no_mine_block[1] != self.chest_size[0]:
                        no_mine_list.append(no_mine_block)

        mine_click_array = np.unique(np.array(mine_list), axis=0)
        no_mine_click_array = np.unique(np.array(no_mine_list), axis=0)

        return mine_click_array, no_mine_click_array

    def subtraction_click(self):
        mine_array, no_mine_array = self.subtraction_find()
        if mine_array.size == 0 and no_mine_array.size == 0:
            return False
        if mine_array.shape == (1, 2) and mine_array[0][0] == -1:
            return False
        print(mine_array)
        print(no_mine_array)
        self.click(mine_array, 1)
        self.click(no_mine_array, 0)
        return True

    def hyper_find(self):
        pass

    def hyper_click(self):
        pass

    def start(self):
        self.get_screenshot()
        self.get_chest()
        if np.max(self.chest) == 9:
            self.status = 2
        while True:
            self.get_screenshot()
            self.get_chest()

            if self.status == 0:
                print('status', 0)
                click_pos = np.random.random((1, 2))
                click_pos[0, 0] = click_pos[0, 0] * self.chest_size[1]
                click_pos[0, 1] = click_pos[0, 1] * self.chest_size[0]
                self.click(np.floor(click_pos), 0)
                self.get_screenshot()
                self.get_chest()
                if self.primer_click():
                    self.status = 2

            if self.status == 1:
                print('status', 1)
                pyautogui.click(self.pos[0] + self.game_size[0] / 2, self.pos[1] + 76, button='left')
                self.status = 0
                self.__init__(self.mine_count)

            if self.status == 2:
                print('status', 2)
                if not self.primer_click():
                    self.status = 3

            if self.status == 3:
                print('status', 3)
                result = self.subtraction_click()
                if result:
                    self.status = 2
                else:
                    self.status = 4
                pass

            if self.status == 4:
                print('status', 4)
                return
                pass

            if self.status == 5:
                print('status', 5)
                pass

            if self.status == 6:
                print('status', 6)
                pass

            if self.status == 7:
                print('status', 7)
                pass


if __name__ == '__main__':
    pyautogui.PAUSE = 0
    a = winmine_auto(40)
    a.start()
