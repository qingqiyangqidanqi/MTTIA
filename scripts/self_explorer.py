import argparse
import ast
import datetime
import json
import os
import re
import sys
import time
import jiesheng
import prompts
from config import load_config
from and_controller import list_all_devices, AndroidController, traverse_tree
from model import ask_gpt4v, parse_explore_rsp, parse_reflect_rsp
from utils import print_with_color, draw_bbox_multi, encode_image

# 定义命令行参数的描述
arg_desc = "AppAgent - Autonomous Exploration"
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
parser.add_argument("--app")
parser.add_argument("--task")
parser.add_argument("--using_method")
parser.add_argument("--num")
parser.add_argument("--root_dir", default="./")
args = vars(parser.parse_args())

# 加载配置
configs = load_config()

# 获取命令行参数
app = args["app"]
task = args["task"]
using_method = args["using_method"]
root_dir = args["root_dir"]
num = int(args["num"])  # 此时执行excel表格中的第num行的任务
similarity_index = 0

# 如果没有提供应用参数，提示用户输入
if not app:
    print_with_color("What is the name of the target app?", "blue")
    app = input()
    app = app.replace(" ", "")

# 创建工作目录
work_dir = os.path.join(root_dir, "apps")
if not os.path.exists(work_dir):
    os.mkdir(work_dir)
work_dir = os.path.join(work_dir, app)
if not os.path.exists(work_dir):
    os.mkdir(work_dir)
demo_dir = os.path.join(work_dir, "demos")
if not os.path.exists(demo_dir):
    os.mkdir(demo_dir)
demo_timestamp = int(time.time())
task_name = datetime.datetime.fromtimestamp(demo_timestamp).strftime("self_explore_%Y-%m-%d_%H-%M-%S")
task_dir = os.path.join(demo_dir, task_name)
os.mkdir(task_dir)
docs_dir = os.path.join(work_dir, "auto_docs")
if not os.path.exists(docs_dir):
    os.mkdir(docs_dir)
explore_log_path = os.path.join(task_dir, f"log_explore_{task_name}.txt")
reflect_log_path = os.path.join(task_dir, f"log_reflect_{task_name}.txt")

# 获取设备列表
device_list = list_all_devices()
if not device_list:
    print_with_color("ERROR: No device found!", "red")
    sys.exit()
print_with_color(f"List of devices attached:\n{str(device_list)}", "yellow")
if len(device_list) == 1:
    device = device_list[0]
    print_with_color(f"Device selected: {device}", "yellow")
else:
    print_with_color("Please choose the Android device to start demo by entering its ID:", "blue")
    device = input()
controller = AndroidController(device)
width, height = controller.get_device_size()
if not width and not height:
    print_with_color("ERROR: Invalid device size!", "red")
    sys.exit()
print_with_color(f"Screen resolution of {device}: {width}x{height}", "yellow")

# 提示用户输入任务描述
if not task:
    print_with_color("Please enter the description of the task you want me to complete in a few sentences:", "blue")
    task_desc = input()
else:
    task_desc = task
    print_with_color(f"you enter the description of the task is {task}, the app is {app}", "blue")
# 初始化变量
round_count = 0
doc_count = 0
useless_list = set()
last_act = "None"
task_complete = False

# 开始自主探索
# 这段代码是一个循环，用于在达到最大轮数之前进行自主探索
while round_count < configs["MAX_ROUNDS"]:

    if using_method == 'TRUE':  # jiesheng.py中的代码
        if round_count != 0:
            # 设置一个函数与之前的上一步的图片进行比对，相似度为70%以上则跳出循环，视作任务已经完成了
            img_result = os.path.join(
                task_dir, "assets", "result_pic", f"{app}_{task}.jpg")
            img2_path = os.path.join(task_dir, f"{round_count}_after.png")
            similarity = jiesheng.pic_ssim(img_result, img2_path)
            similarity_index = similarity[0]
            if similarity[1] == True:
                print(f"与最终任务相似度为{similarity[0]}，任务已经完成了")
                task_complete = True
                break
            else:
                print(f"与最终任务相似度为{similarity[0]}，任务还未完成")

    # 每次循环开始时，轮数加一
    round_count += 1
    # 打印当前轮数
    print_with_color(f"Round {round_count}", "yellow")
    # 获取当前屏幕截图
    screenshot_before = controller.get_screenshot(f"{round_count}_before", task_dir)
    # 获取当前屏幕的XML
    xml_path = controller.get_xml(f"{round_count}", task_dir)
    # 如果获取截图或XML失败，则跳出循环
    if screenshot_before == "ERROR" or xml_path == "ERROR":
        break
    # 初始化可点击（按钮，触摸等）和可聚焦（键盘输入文本）元素列表
    clickable_list = []
    focusable_list = []
    # 遍历XML，获取可点击和可聚焦元素
    traverse_tree(xml_path, clickable_list, "clickable", True)
    traverse_tree(xml_path, focusable_list, "focusable", True)
    # 初始化元素列表
    elem_list = []
    # 遍历可点击元素，如果元素不在无用列表中，则添加到元素列表
    for elem in clickable_list:
        if elem.uid in useless_list:
            continue
        elem_list.append(elem)
    # 遍历可聚焦元素，如果元素不在无用列表中，则添加到元素列表
    for elem in focusable_list:
        if elem.uid in useless_list:
            continue
        # 计算元素的中心点
        bbox = elem.bbox
        center = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
        # 初始化关闭标志
        close = False
        # 遍历可点击元素，计算元素中心点之间的距离，如果距离小于最小距离，则设置关闭标志为True
        for e in clickable_list:
            bbox = e.bbox
            center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
            dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
            if dist <= configs["MIN_DIST"]:
                close = True
                break
        # 如果关闭标志为False，则将元素添加到元素列表
        if not close:
            elem_list.append(elem)
    # 在截图上绘制元素的边界框
    draw_bbox_multi(screenshot_before, os.path.join(task_dir, f"{round_count}_before_labeled.png"), elem_list,
                    dark_mode=configs["DARK_MODE"])

    # 生成提示，替换任务描述和最后的动作
    prompt = re.sub(r"<task_description>", task_desc, prompts.self_explore_task_template)
    prompt = re.sub(r"<last_act>", last_act, prompt)
    # 编码截图
    base64_img_before = encode_image(os.path.join(task_dir, f"{round_count}_before_labeled.png"))
    # 生成内容，包括提示和截图
    content = [
        {
            "type": "text",
            "text": prompt
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_img_before}"
            }
        }
    ]
    # 打印正在思考下一步的动作
    print_with_color("Thinking about what to do in the next step...", "yellow")
    # 向GPT-4V发送请求，获取响应
    rsp = ask_gpt4v(content)

    # 如果响应中没有错误
    if "error" not in rsp:
        # 将步骤、提示、图片和响应写入日志文件
        with open(explore_log_path, "a") as logfile:
            log_item = {"step": round_count, "prompt": prompt, "image": f"{round_count}_before_labeled.png",
                        "response": rsp}
            logfile.write(json.dumps(log_item) + "\n")
        # 解析响应，获取动作名称和最后的动作
        res = parse_explore_rsp(rsp)
        act_name = res[0]
        last_act = res[-1]
        res = res[:-1]
        # 如果动作名称是"FINISH"，则设置任务完成标志为True，跳出循环
        if act_name == "FINISH":
            task_complete = True
            break
        # 如果动作名称是"tap"，则执行点击操作
        if act_name == "tap":
            _, area = res
            tl, br = elem_list[area - 1].bbox
            x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
            ret = controller.tap(x, y)
            if ret == "ERROR":
                print_with_color("ERROR: tap execution failed", "red")
                break
        # 如果动作名称是"text"，则执行输入操作
        elif act_name == "text":
            _, input_str = res
            ret = controller.text(input_str)
            if ret == "ERROR":
                print_with_color("ERROR: text execution failed", "red")
                break
        # 如果动作名称是"long_press"，则执行长按操作
        elif act_name == "long_press":
            _, area = res
            tl, br = elem_list[area - 1].bbox
            x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
            ret = controller.long_press(x, y)
            if ret == "ERROR":
                print_with_color("ERROR: long press execution failed", "red")
                break
        # 如果动作名称是"swipe"，则执行滑动操作
        elif act_name == "swipe":
            _, area, swipe_dir, dist = res
            tl, br = elem_list[area - 1].bbox
            x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
            ret = controller.swipe(x, y, swipe_dir, dist)
            if ret == "ERROR":
                print_with_color("ERROR: swipe execution failed", "red")
                break
        # 如果动作名称不是以上任何一个，跳出循环
        else:
            break
        # 等待一段时间
        time.sleep(configs["REQUEST_INTERVAL"])
    # 如果响应中有错误，打印错误信息，跳出循环
    else:
        print_with_color(rsp["error"]["message"], "red")
        break

    # 获取操作后的屏幕截图
    screenshot_after = controller.get_screenshot(f"{round_count}_after", task_dir)
    # 如果获取截图失败，跳出循环
    if screenshot_after == "ERROR":
        break
    # 在截图上绘制元素的边界框
    draw_bbox_multi(screenshot_after, os.path.join(task_dir, f"{round_count}_after_labeled.png"), elem_list,
                    dark_mode=configs["DARK_MODE"])
    # 编码截图
    base64_img_after = encode_image(os.path.join(task_dir, f"{round_count}_after_labeled.png"))

    # 根据动作名称生成提示
    if act_name == "tap":
        prompt = re.sub(r"<action>", "tapping", prompts.self_explore_reflect_template)
    elif act_name == "text":
        continue
    elif act_name == "long_press":
        prompt = re.sub(r"<action>", "long pressing", prompts.self_explore_reflect_template)
    elif act_name == "swipe":
        swipe_dir = res[2]
        if swipe_dir == "up" or swipe_dir == "down":
            act_name = "v_swipe"
        elif swipe_dir == "left" or swipe_dir == "right":
            act_name = "h_swipe"
        prompt = re.sub(r"<action>", "swiping", prompts.self_explore_reflect_template)
    else:
        print_with_color("ERROR: Undefined act!", "red")
        break
    # 替换提示中的UI元素、任务描述和最后的动作
    prompt = re.sub(r"<ui_element>", str(area), prompt)
    prompt = re.sub(r"<task_desc>", task_desc, prompt)
    prompt = re.sub(r"<last_act>", last_act, prompt)

    # 生成内容，包括提示和截图
    content = [
        {
            "type": "text",
            "text": prompt
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_img_before}"
            }
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_img_after}"
            }
        }
    ]
    # 打印正在反思上一步的动作
    print_with_color("Reflecting on my previous action...", "yellow")
    # 向GPT-4V发送请求，获取响应
    rsp = ask_gpt4v(content)
    # 如果响应中没有错误
    if "error" not in rsp:
        # 获取元素的资源ID
        resource_id = elem_list[int(area) - 1].uid
        # 将步骤、提示、图片和响应写入日志文件
        with open(reflect_log_path, "a") as logfile:
            log_item = {"step": round_count, "prompt": prompt, "image_before": f"{round_count}_before_labeled.png",
                        "image_after": f"{round_count}_after.png", "response": rsp}
            logfile.write(json.dumps(log_item) + "\n")
        # 解析响应，获取决策
        res = parse_reflect_rsp(rsp)
        decision = res[0]
        # 如果决策是"ERROR"，跳出循环
        if decision == "ERROR":
            break
        # 如果决策是"INEFFECTIVE"，将资源ID添加到无用列表，设置最后的动作为"None"
        if decision == "INEFFECTIVE":
            useless_list.add(resource_id)
            last_act = "None"
        # 如果决策是"BACK"、"CONTINUE"或"SUCCESS"
        elif decision == "BACK" or decision == "CONTINUE" or decision == "SUCCESS":
            # 如果决策是"BACK"或"CONTINUE"，将资源ID添加到无用列表，设置最后的动作为"None"
            if decision == "BACK" or decision == "CONTINUE":
                useless_list.add(resource_id)
                last_act = "None"
                # 如果决策是"BACK"，执行返回操作
                if decision == "BACK":
                    ret = controller.back()
                    if ret == "ERROR":
                        print_with_color("ERROR: back execution failed", "red")
                        break
            # 获取文档
            doc = res[-1]
            # 生成文档名称
            doc_name = resource_id + ".txt"
            # 生成文档路径
            doc_path = os.path.join(docs_dir, doc_name)
            # 如果文档已存在
            if os.path.exists(doc_path):
                # 读取文档内容
                doc_content = ast.literal_eval(open(doc_path).read())
                # 如果文档内容中已有动作名称，打印文档已存在的消息，继续下一次循环
                if doc_content[act_name]:
                    print_with_color(f"Documentation for the element {resource_id} already exists.", "yellow")
                    continue
            # 否则，初始化文档内容
            else:
                doc_content = {
                    "tap": "",
                    "text": "",
                    "v_swipe": "",
                    "h_swipe": "",
                    "long_press": ""
                }
            # 将文档添加到文档内容
            doc_content[act_name] = doc
            # 将文档内容写入文件
            with open(doc_path, "w") as outfile:
                outfile.write(str(doc_content))
            # 文档计数加一
            doc_count += 1
            # 打印生成文档的消息
            print_with_color(f"Documentation generated and saved to {doc_path}", "yellow")
        # 如果决策不是以上任何一个，打印错误信息，跳出循环
        else:
            print_with_color(f"ERROR: Undefined decision! {decision}", "red")
            break
    else:
        print_with_color(rsp["error"]["message"], "red")
        break
    time.sleep(configs["REQUEST_INTERVAL"])

# 根据任务是否完成打印相应的消息
if task_complete:
    print_with_color(f"Autonomous exploration completed successfully. {doc_count} docs generated.", "yellow")
elif round_count == configs["MAX_ROUNDS"]:
    print_with_color(f"Autonomous exploration finished due to reaching max rounds. {doc_count} docs generated.",
                     "yellow")
else:
    print_with_color(f"Autonomous exploration finished unexpectedly. {doc_count} docs generated.", "red")

# 调用jiesheng.py内的方法将相关数据存入excel表格中
txt_path1 = os.path.join(root_dir, "apps", app, "demos", task_name,
                         f"log_explore_{task_name}.txt")
txt_path2 = os.path.join(root_dir, "apps", app, "demos", task_name,
                         f"log_reflect_{task_name}.txt")
step_num, explore_tokens, reflect_tokens = jiesheng.read_json_from_txt(txt_path1, txt_path2)
print("step_num:", step_num, "explore_tokens:", explore_tokens, "reflect_tokens:", reflect_tokens)  # test
print("similarity_index:", similarity_index)  # test
jiesheng.write_to_excel(num, step_num, explore_tokens, reflect_tokens, similarity_index,
                        "D:\Desktop\projects\AppAgent-main\\task_result.xlsx")
