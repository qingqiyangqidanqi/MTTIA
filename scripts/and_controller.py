import os
import subprocess
import xml.etree.ElementTree as ET

from config import load_config
from utils import print_with_color

configs = load_config()


class AndroidElement:
    """
        Class representing an Android UI element.
    """
    def __init__(self, uid, bbox, attrib):
        """
        Initialize an AndroidElement instance.

        :param uid: Unique identifier for the element
        :param bbox: Bounding box of the element
        :param attrib: Attributes of the element
        """
        self.uid = uid
        self.bbox = bbox
        self.attrib = attrib


def execute_adb(adb_command):
    """
     Execute an adb command and return the result.

    :param adb_command: The adb command to execute
    :return: The result of the command execution
    """
    # print(adb_command)
    result = subprocess.run(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    print_with_color(f"Command execution failed: {adb_command}", "red")
    print_with_color(result.stderr, "red")
    return "ERROR"


def list_all_devices():
    """
        List all connected Android devices.

        :return: A list of device identifiers
    """
    adb_command = "adb devices"
    device_list = []
    result = execute_adb(adb_command)
    if result != "ERROR":
        devices = result.split("\n")[1:]
        for d in devices:
            device_list.append(d.split()[0])

    return device_list


def get_id_from_element(elem):
    """
    为 Android UI 元素生成一个唯一标识符。

    这个函数使用元素的 'bounds'，'resource-id' 和 'content-desc' 属性来生成 ID。
    'bounds' 属性用于计算元素的宽度和高度。
    如果 'resource-id' 属性存在，那么它将被用作 ID。
    如果 'resource-id' 属性不存在，那么元素的 'class' 属性以及其宽度和高度将被用作 ID。
    如果 'content-desc' 属性存在并且其长度小于 20，那么它将被添加到 ID 中。

    :param elem: 一个 Android UI 元素
    :return: 元素的唯一标识符
    """
    bounds = elem.attrib["bounds"][1:-1].split("][")
    x1, y1 = map(int, bounds[0].split(","))
    x2, y2 = map(int, bounds[1].split(","))
    elem_w, elem_h = x2 - x1, y2 - y1
    if "resource-id" in elem.attrib and elem.attrib["resource-id"]:
        elem_id = elem.attrib["resource-id"].replace(":", ".").replace("/", "_")
    else:
        elem_id = f"{elem.attrib['class']}_{elem_w}_{elem_h}"
    if "content-desc" in elem.attrib and elem.attrib["content-desc"] and len(elem.attrib["content-desc"]) < 20:
        content_desc = elem.attrib['content-desc'].replace("/", "_").replace(" ", "").replace(":", "_")
        elem_id += f"_{content_desc}"
    return elem_id


def traverse_tree(xml_path, elem_list, attrib, add_index=False):
    """
    遍历 XML 树，查找具有特定属性的元素，并将其添加到列表中。

    这个函数遍历 XML 树，查找具有特定属性的元素。如果找到这样的元素，它会生成一个唯一的 ID，
    并将其添加到提供的列表中。如果元素的父元素存在，那么父元素的 ID 会被添加到元素的 ID 前面。
    如果 `add_index` 参数为 True，那么元素的索引也会被添加到 ID 中。

    :param xml_path: XML 文件的路径
    :param elem_list: 用于存储找到的元素的列表
    :param attrib: 要查找的属性
    :param add_index: 是否在 ID 中添加元素的索引
    """
    path = []
    for event, elem in ET.iterparse(xml_path, ['start', 'end']):
        if event == 'start':
            path.append(elem)
            if attrib in elem.attrib and elem.attrib[attrib] == "true":
                parent_prefix = ""
                if len(path) > 1:
                    parent_prefix = get_id_from_element(path[-2])
                bounds = elem.attrib["bounds"][1:-1].split("][")
                x1, y1 = map(int, bounds[0].split(","))
                x2, y2 = map(int, bounds[1].split(","))
                center = (x1 + x2) // 2, (y1 + y2) // 2
                elem_id = get_id_from_element(elem)
                if parent_prefix:
                    elem_id = parent_prefix + "_" + elem_id
                if add_index:
                    elem_id += f"_{elem.attrib['index']}"
                close = False
                for e in elem_list:
                    bbox = e.bbox
                    center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
                    dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
                    if dist <= configs["MIN_DIST"]:
                        close = True
                        break
                if not close:
                    elem_list.append(AndroidElement(elem_id, ((x1, y1), (x2, y2)), attrib))

        if event == 'end':
            path.pop()


class AndroidController:
    """
    AndroidController 类用于控制 Android 设备。

    这个类提供了一系列方法，用于与 Android 设备进行交互，包括获取设备尺寸、获取屏幕截图、获取 XML、发送返回、点击、输入文本、长按和滑动等操作。
    """

    def __init__(self, device):
        """
        初始化 AndroidController 实例。

        :param device: 要控制的 Android 设备
        """
        self.device = device
        self.screenshot_dir = configs["ANDROID_SCREENSHOT_DIR"]
        self.xml_dir = configs["ANDROID_XML_DIR"]
        self.width, self.height = self.get_device_size()
        self.backslash = "\\"

    def get_device_size(self):
        """
        获取 Android 设备的尺寸。

        :return: 设备的宽度和高度
        """
        adb_command = f"adb -s {self.device} shell wm size"
        result = execute_adb(adb_command)
        if result != "ERROR":
            return map(int, result.split(": ")[1].split("x"))
        return 0, 0

    def get_screenshot(self, prefix, save_dir):
        """
        获取 Android 设备的屏幕截图。

        :param prefix: 截图文件的前缀
        :param save_dir: 截图文件的保存目录
        :return: 截图文件的路径
        """
        cap_command = f"adb -s {self.device} shell screencap -p " \
                      f"{os.path.join(self.screenshot_dir, prefix + '.png').replace(self.backslash, '/')}"
        pull_command = f"adb -s {self.device} pull " \
                       f"{os.path.join(self.screenshot_dir, prefix + '.png').replace(self.backslash, '/')} " \
                       f"{os.path.join(save_dir, prefix + '.png')}"
        result = execute_adb(cap_command)
        if result != "ERROR":
            result = execute_adb(pull_command)
            if result != "ERROR":
                return os.path.join(save_dir, prefix + ".png")
            return result
        return result

    def get_xml(self, prefix, save_dir):
        """
        获取 Android 设备的 XML。

        :param prefix: XML 文件的前缀
        :param save_dir: XML 文件的保存目录
        :return: XML 文件的路径
        """
        dump_command = f"adb -s {self.device} shell uiautomator dump " \
                       f"{os.path.join(self.xml_dir, prefix + '.xml').replace(self.backslash, '/')}"
        pull_command = f"adb -s {self.device} pull " \
                       f"{os.path.join(self.xml_dir, prefix + '.xml').replace(self.backslash, '/')} " \
                       f"{os.path.join(save_dir, prefix + '.xml')}"
        result = execute_adb(dump_command)
        if result != "ERROR":
            result = execute_adb(pull_command)
            if result != "ERROR":
                return os.path.join(save_dir, prefix + ".xml")
            return result
        return result

    def back(self):
        """
        发送返回操作到 Android 设备。

        :return: 操作的结果
        """
        adb_command = f"adb -s {self.device} shell input keyevent KEYCODE_BACK"
        ret = execute_adb(adb_command)
        return ret

    def tap(self, x, y):
        """
        在 Android 设备上的指定位置进行点击操作。

        :param x: 点击位置的 x 坐标
        :param y: 点击位置的 y 坐标
        :return: 操作的结果
        """
        adb_command = f"adb -s {self.device} shell input tap {x} {y}"
        ret = execute_adb(adb_command)
        return ret

    def text(self, input_str):
        """
        向 Android 设备输入文本。

        :param input_str: 要输入的文本
        :return: 操作的结果
        """
        input_str = input_str.replace(" ", "%s")
        input_str = input_str.replace("'", "")
        adb_command = f"adb -s {self.device} shell input text {input_str}"
        ret = execute_adb(adb_command)
        return ret

    def long_press(self, x, y, duration=1000):
        """
        在 Android 设备上的指定位置进行长按操作。

        :param x: 长按位置的 x 坐标
        :param y: 长按位置的 y 坐标
        :param duration: 长按的持续时间，单位为毫秒
        :return: 操作的结果
        """
        adb_command = f"adb -s {self.device} shell input swipe {x} {y} {x} {y} {duration}"
        ret = execute_adb(adb_command)
        return ret

    def swipe(self, x, y, direction, dist="medium", quick=False):
        """
        在 Android 设备上进行滑动操作。

        :param x: 滑动起始位置的 x 坐标
        :param y: 滑动起始位置的 y 坐标
        :param direction: 滑动的方向，可以是 "up"、"down"、"left" 或 "right"
        :param dist: 滑动的距离，可以是 "long"、"medium" 或 "short"
        :param quick: 是否进行快速滑动
        :return: 操作的结果
        """
        unit_dist = int(self.width / 10)
        if dist == "long":
            unit_dist *= 3
        elif dist == "medium":
            unit_dist *= 2
        if direction == "up":
            offset = 0, -2 * unit_dist
        elif direction == "down":
            offset = 0, 2 * unit_dist
        elif direction == "left":
            offset = -1 * unit_dist, 0
        elif direction == "right":
            offset = unit_dist, 0
        else:
            return "ERROR"
        duration = 100 if quick else 400
        adb_command = f"adb -s {self.device} shell input swipe {x} {y} {x + offset[0]} {y + offset[1]} {duration}"
        ret = execute_adb(adb_command)
        return ret

    def swipe_precise(self, start, end, duration=400):
        """
        在 Android 设备上进行精确滑动操作。

        :param start: 滑动起始位置的坐标
        :param end: 滑动结束位置的坐标
        :param duration: 滑动的持续时间，单位为毫秒
        :return: 操作的结果
        """
        start_x, start_y = start
        end_x, end_y = end
        adb_command = f"adb -s {self.device} shell input swipe {start_x} {start_x} {end_x} {end_y} {duration}"
        ret = execute_adb(adb_command)
        return ret