import argparse
import datetime
import os
import time
from scripts.utils import print_with_color

user_input = '1'  # 1代表自主探索，2代表人类演示

# 描述应用代理的探索阶段
arg_desc = "AppAgent - exploration phase"
# 创建一个命令行解析器
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=arg_desc)
# 添加应用参数
parser.add_argument("--app")
# 添加任务参数
parser.add_argument("--task")
# 添加 是否使用了任务终止模式方法
parser.add_argument("--using_method")
# 添加此时执行excel表格中的第num行任务
parser.add_argument("--num")
# 添加根目录参数，默认为当前目录
parser.add_argument("--root_dir", default="./")
# 解析命令行参数
args = vars(parser.parse_args())

# 获取应用参数
app = args["app"]
# 获取任务参数
task = '"' + args["task"] + '"'
# 获取此时执行excel表格中的第num行
num = args["num"]
# 获取是否使用了任务终止模式方法
using_method = args["using_method"]

print_with_color(f"数据从excel中传过来了，本次调用learn.py的应用是{app}, 任务是{task}", "blue")

# 获取根目录参数
root_dir = args["root_dir"]

# 打印欢迎信息和探索阶段的目标
print_with_color("Welcome to the exploration phase of AppAgent!\nThe exploration phase aims at generating "
                 "documentations for UI elements through either autonomous exploration or human demonstration. "
                 "Both options are task-oriented, which means you need to give a task description. During "
                 "autonomous exploration, the agent will try to complete the task by interacting with possible "
                 "elements on the UI within limited rounds. Documentations will be generated during the process of "
                 "interacting with the correct elements to proceed with the task. Human demonstration relies on "
                 "the user to show the agent how to complete the given task, and the agent will generate "
                 "documentations for the elements interacted during the human demo. To start, please enter the "
                 "main interface of the app on your phone.", "yellow")
# 提示用户选择模式
if user_input == '0':
    print_with_color("Choose from the following modes:\n1. autonomous exploration\n2. human demonstration\n"
                     "Type 1 or 2.", "blue")
elif user_input == '1':
    print_with_color("You have chosen autonomous exploration mode.", "blue")
else:
    print_with_color("You have chosen human demonstration mode.", "blue")
# 获取用户输入的模式
# user_input = ""
# while user_input != "1" and user_input != "2":
#     user_input = input()

# 如果没有提供应用参数，提示用户输入
if not app:
    print_with_color("What is the name of the target app?", "blue")
    app = input()
    app = app.replace(" ", "")

# 如果用户选择了自主探索模式
if user_input == "1":
    # 执行自主探索脚本
    os.system(
        f"python scripts/self_explorer.py --app {app} --task {task} --root_dir {root_dir} --using_method {using_method} --num {num}")
else:
    # 如果用户选择了人类演示模式
    # 获取当前时间戳
    demo_timestamp = int(time.time())
    # 格式化演示名称
    demo_name = datetime.datetime.fromtimestamp(demo_timestamp).strftime(f"demo_{app}_%Y-%m-%d_%H-%M-%S")
    # 执行步骤记录脚本
    os.system(f"python scripts/step_recorder.py --app {app} --demo {demo_name} --root_dir {root_dir} --num {num}")
    # 执行文档生成脚本
    os.system(f"python scripts/document_generation.py --app {app} --demo {demo_name} --root_dir {root_dir}")
