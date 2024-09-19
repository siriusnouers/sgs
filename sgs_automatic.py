import threading
import time
import coord
import pygetwindow as gw
import pyautogui
import cv2
import numpy as np


window_x, window_y = 0, 0
speed_lock = threading.Lock()   # 判断速率锁
gan_lock = threading.Lock()     # 判断拉线锁
# 创建停止事件
is_ti_gan = False   # 是否需要拉线,开始为不拉
last_gan_time = 0
status_para = 0     # 状态态参数 0为正常钓鱼 1为进入致命一击界面 2为钓鱼结束
son_threa_run = True


speed = 0.09  # 在线程判断速度慢时，需要的点击频率
old_speed = 0.18  # 需要慢下来的点击速率
ti_gan_time = 5.92  # 提杆后，过多少秒就是开钓鱼 这个最好是以加大时间调整,最低时间为5，在往下调,会出bug
# 上方值都是由,本人电脑配置，最佳参数值，若有不一致，可小幅度调整

loop_num = 39    # 为你本次某个鱼饵的数量，填写几个就循环钓鱼几次
ld_height = 35  # 1920*1080分辨率为35 4k分辨率为51 大家根据用微信截图测试一下,自己雷电模拟器上方黑条高度需要填写
# 上
i_up = r'E:\code\python3.10\code\sgs_image\01_up.png'
# 左
i_left = r'E:\code\python3.10\code\sgs_image\02_left.png'
# 下
i_un = r'E:\code\python3.10\code\sgs_image\03_un.png'
# 右
i_right = r'E:\code\python3.10\code\sgs_image\04_right.png'
# 风
i_wind = r'E:\code\python3.10\code\sgs_image\05_wind.png'
# 火
i_fire = r'E:\code\python3.10\code\sgs_image\06_fire.png'
# 雷
i_ray = r'E:\code\python3.10\code\sgs_image\07_ray.png'
# 电
i_electricity = r'E:\code\python3.10\code\sgs_image\08_electricity.png'

def check_color_range(color, range_value, target):
    """
    检查给定的颜色值是否在指定的范围内。

    参数:
    color -- 一个包含r, g, b值的元组。
    range_value -- 允许的颜色值与目标值之间的最大差异。
    r_target, g_target, b_target -- 目标颜色的r, g, b值。

    返回:
    如果颜色在指定范围内，返回True；否则返回False。
    """
    r, g, b = color  # 解包元组
    r_target, g_target, b_target = target
    # 检查r, g, b是否都在指定的范围内
    return (abs(r - r_target) <= range_value and
            abs(g - g_target) <= range_value and
            abs(b - b_target) <= range_value)


# 匹配tag，返回后续要点击的坐标,顺序点击
def click_matching_tags(arr):
    temp_arr = []
    for x in arr:
        # 等待被截图坐标
        cut_cor = {
            'start_x': x-55,
            'start_y': coord.all_tag_y-55,
            'width': 110,
            'height': 110
        }
        temp_x, temp_y = get_image_exist(i_up,
                                         cut_cor, 0.9)
        if temp_x != -1 and temp_y != -1:
            temp_arr.append(coord.up)
            continue
        temp_x, temp_y = get_image_exist(i_left,
                                         cut_cor, 0.9)
        if temp_x != -1 and temp_y != -1:
            temp_arr.append(coord.left)
            continue
        temp_x, temp_y = get_image_exist(i_un,
                                         cut_cor, 0.9)
        if temp_x != -1 and temp_y != -1:
            temp_arr.append(coord.un)
            continue
        temp_x, temp_y = get_image_exist(i_right,
                                         cut_cor, 0.9)
        if temp_x != -1 and temp_y != -1:
            temp_arr.append(coord.right)
            continue
        temp_x, temp_y = get_image_exist(i_wind,
                                         cut_cor, 0.9)
        if temp_x != -1 and temp_y != -1:
            temp_arr.append(coord.wind)
            continue
        temp_x, temp_y = get_image_exist(i_fire,
                                         cut_cor, 0.9)
        if temp_x != -1 and temp_y != -1:
            temp_arr.append(coord.fire)
            continue
        temp_x, temp_y = get_image_exist(i_ray,
                                         cut_cor, 0.9)
        if temp_x != -1 and temp_y != -1:
            temp_arr.append(coord.ray)
            continue
        temp_x, temp_y = get_image_exist(i_electricity,
                                         cut_cor, 0.9)
        if temp_x != -1 and temp_y != -1:
            temp_arr.append(coord.electricity)
    for data in temp_arr:
        pyautogui.click(window_x + data['x'], window_y + data['y'] + ld_height)
        time.sleep(0.2)


# 线程判断是否张力到八十几了
def speed_governing():
    global speed
    r, g, b = coord.norm_color
    range_value = 20
    while True:
        r_target, g_target, b_target = pyautogui.pixel(
            window_x + coord.get_man_color['x'], window_y + coord.get_man_color['y'] + ld_height)
        new_speed = 0.09 if (abs(r - r_target) <= range_value and
                             abs(g - g_target) <= range_value and
                             abs(b - b_target) <= range_value) else old_speed
        with speed_lock:
            speed = new_speed
        time.sleep(0.2)


# 线程判断是否可以提杆与状态变更
def is_full_state():
    global is_ti_gan
    global status_para
    color = coord.pole_color
    # 倒计时图标     其中倒计时无,风有则终极一击，都无则退出，倒计时有，凤无则正常
    color1 = coord.countdown_tag_color
    # 风图标
    color2 = coord.test_wind_color
    range_value = 20
    while True:
        target = pyautogui.pixel(
            window_x + coord.get_pole_color['x'], window_y + coord.get_pole_color['y'] + ld_height)
        new_gan = not check_color_range(color, range_value, target)
        if last_gan_time != 0 and new_gan:
            if time.time() - last_gan_time < 5:
                new_gan = False
        # 倒计时
        target1 = pyautogui.pixel(
            window_x + coord.countdown_tag['x'], window_y + coord.countdown_tag['y'] + ld_height)
        # 风
        target2 = pyautogui.pixel(
            window_x + coord.test_wind['x'], window_y + coord.test_wind['y'] + ld_height)
        temp_status = 0
        if (not check_color_range(color1, range_value, target1) and
                check_color_range(color2, range_value, target2)):
            temp_status = 1
        elif (not check_color_range(color1, range_value, target1) and
              not check_color_range(color2, range_value, target2)):
            time.sleep(1)
            # 倒计时
            target1 = pyautogui.pixel(
                window_x + coord.countdown_tag['x'], window_y + coord.countdown_tag['y'] + ld_height)
            # 风
            target2 = pyautogui.pixel(
                window_x + coord.test_wind['x'], window_y + coord.test_wind['y'] + ld_height)
            if (not check_color_range(color1, range_value, target1) and
                    not check_color_range(color2, range_value, target2)):
                temp_status = 2
            else:
                temp_status = 1
        with gan_lock:
            is_ti_gan = new_gan
            status_para = temp_status if son_threa_run else 0
        time.sleep(1)


# 通过图片,判断当前界面是否是我们想要的界面
# yuan_path 原准备对比图,cut_position 准备截取坐标{start_x,start_y,width,height},threshold 置信度
def get_image_exist(yuan_path, cut_position, threshold):
    # 读取图像
    image = cv2.imread(yuan_path)
    # 转为灰度图像
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 增强对比度
    enhanced_image = cv2.equalizeHist(gray_image)
    # 获取窗口位置
    region = (
        cut_position['start_x'] + window_x, cut_position['start_y'] + window_y + ld_height,
        cut_position['width'], cut_position['height'])  # 替换为实际的截图区域
    # 获取需要截图的区域
    get_image = pyautogui.screenshot(region=region)
    # 将 PIL 图像转换为 NumPy 数组
    get_image_np = np.array(get_image)
    # 转为灰度图像
    gray_get_image = cv2.cvtColor(get_image_np, cv2.COLOR_BGR2GRAY)
    # 增强对比度
    enhanced_get_image = cv2.equalizeHist(gray_get_image)
    # 模板匹配
    result = cv2.matchTemplate(enhanced_get_image, enhanced_image, cv2.TM_CCOEFF_NORMED)
    # 设定置信度阈值
    loc = np.where(result >= threshold)
    # 计算模板尺寸
    template_height, template_width = enhanced_image.shape
    # 检查是否找到匹配区域
    if len(loc[0]) > 0:
        # 获取匹配区域的中心位置
        i, all_x, all_y = 0, 0, 0
        for pt in zip(*loc[::-1]):  # 反转行列坐标
            x, y = pt
            # 计算中心位置
            all_x += x + template_width // 2
            all_y += y + template_height // 2
            i = i + 1
        c_x = round(all_x / i)
        c_y = round(all_y / i)
        # 返回结果为相对，雷电模拟器的坐标
        last_x = cut_position['start_x'] + c_x
        last_y = cut_position['start_y'] + c_y
        return last_x, last_y
    else:
        return - 1, - 1


# 钓鱼
def go_fish():
    time.sleep(2)
    # Step 4: 点击开始钓鱼
    # subprocess.run(['adb', '-s', device, 'shell', 'input', 'tap',
    #                 str(coord.start_fish['x']), str(coord.start_fish['y'])], check=True)
    pyautogui.click(window_x+coord.start_fish['x'], window_y+coord.start_fish['y']+ld_height)
    time.sleep(2)
    # 创建一个线程，target指定线程执行的函数
    thread = threading.Thread(target=speed_governing)
    thread1 = threading.Thread(target=is_full_state)
    thread.daemon = True  # 设置为守护线程
    thread1.daemon = True  # 设置为守护线程
    thread.start()
    thread1.start()
    global son_threa_run
    for _ in range(loop_num):
        global last_gan_time
        last_gan_time = 0
        # Step 5: 抛竿
        pyautogui.moveTo(window_x + coord.start_fish['x'], window_y + coord.start_fish['y'] + ld_height)
        time.sleep(1)
        pyautogui.dragTo(window_x + coord.start_fish['x'], window_y + coord.start_fish['y'] + ld_height - 100, duration=0.5)
        time.sleep(ti_gan_time)
        # Step 6:鱼咬耳了
        pyautogui.click(window_x + coord.start_fish['x'], window_y + coord.start_fish['y'] + ld_height)
        time.sleep(1)
        # Step 7:正式钓鱼
        # 模拟按下鼠标左键
        pyautogui.mouseDown(button='left')
        # 等待一段时间，模拟长按效果
        time.sleep(1.7)  # 1.7秒
        # 释放鼠标左键
        pyautogui.mouseUp(button='left')
        son_threa_run = True
        print("看看线程执行了几次")
        while True:
            with gan_lock:
                current_gan = is_ti_gan
                current_status = status_para
                # 进入致命一击状态了
                if current_status == 1:
                    print("进入致命一击了")
                    # 停止两个子线程
                    time.sleep(0.1)
                    # 判断是4,5,6
                    if check_color_range(coord.center_color,
                                         20,
                                         pyautogui.pixel(
                                             window_x + coord.center_tag['x'], window_y + coord.center_tag['y'] + ld_height)):
                        # 为4,6
                        if check_color_range(coord.four_six_color,
                                             20,
                                             pyautogui.pixel(
                                                 window_x + coord.four_six_tag['x'], window_y + coord.four_six_tag['y'] + ld_height)):
                            # 为6
                            click_matching_tags(coord.six_tag_x)
                        else:
                            # 为4
                            click_matching_tags(coord.four_tag_x)
                    else:
                        # 为5
                        click_matching_tags(coord.five_tag_x)
                    break
                elif current_status == 2:
                    print("结束本次钓鱼了")
                    break
                else:
                    if last_gan_time != 0 :
                        if time.time() - last_gan_time < 5:
                            current_gan = False
                    if current_gan:
                        pyautogui.moveTo(window_x + coord.start_fish['x'], window_y + coord.start_fish['y'] + ld_height)
                        pyautogui.dragTo(window_x + coord.start_fish['x'],
                                         window_y + coord.start_fish['y'] + ld_height - 100, duration=0.2)
                        last_gan_time = time.time()
                        print("看连续拉了几次杆")
                        # time.sleep(0.6)
                    else:
                        pyautogui.click(window_x + coord.start_fish['x'], window_y + coord.start_fish['y'] + ld_height)
                        with speed_lock:
                            current_speed = speed
                        time.sleep(current_speed)

        time.sleep(8)
        son_threa_run = False
        # 点击在钓一次
        # subprocess.run(['adb', '-s', device, 'shell', 'input', 'tap',
        #                 str(coord.again_fish['x']), str(coord.again_fish['y'])], check=True)
        pyautogui.click(window_x+coord.again_fish['x'], window_y+coord.again_fish['y']+ld_height)
        time.sleep(2)


def all_flow():
    game_window = gw.getWindowsWithTitle('雷电模拟器')[0]  # 替换为实际的游戏窗口标题
    # 获取窗口位置
    global window_x
    window_x = game_window.left
    global window_y
    window_y = game_window.top
    go_fish()


def main():
    all_flow()


if __name__ == "__main__":
    main()

