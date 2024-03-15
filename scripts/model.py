import re
import requests

from config import load_config
from utils import print_with_color

configs = load_config()


def ask_gpt4v(content):
    """
    这个函数用于与GPT-4模型进行交互。

    参数:
    content (str): 将发送到GPT-4模型的内容。

    返回:
    dict: GPT-4模型的响应。

    """

    # 请求的头部信息
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {configs['OPENAI_API_KEY']}"
    }

    # 请求的负载
    payload = {
        "model": configs["OPENAI_API_MODEL"],
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "temperature": configs["TEMPERATURE"],
        "max_tokens": configs["MAX_TOKENS"]
    }

    # 向OpenAI API发送POST请求
    response = requests.post(configs["OPENAI_API_BASE"], headers=headers, json=payload)

    # 如果响应中没有错误
    if "error" not in response.json():
        # 从响应中获取使用详情
        usage = response.json()["usage"]
        prompt_tokens = usage["prompt_tokens"]
        completion_tokens = usage["completion_tokens"]

        # 打印请求的成本
        print_with_color(f"请求的成本是 "
                         f"${'{0:.2f}'.format(prompt_tokens / 1000 * 0.01 + completion_tokens / 1000 * 0.03)}",
                         "yellow")

    # 返回GPT-4模型的响应
    return response.json()


def parse_explore_rsp(rsp):
    """
    这个函数用于解析GPT-4模型的响应。

    参数:
    rsp (dict): GPT-4模型的响应。

    返回:
    list: 解析后的结果。

    """

    try:
        # 从响应中获取消息内容
        msg = rsp["choices"][0]["message"]["content"]
        # 从消息中提取观察结果
        observation = re.findall(r"Observation: (.*?)$", msg, re.MULTILINE)[0]
        # 从消息中提取思考结果
        think = re.findall(r"Thought: (.*?)$", msg, re.MULTILINE)[0]
        # 从消息中提取行动结果
        act = re.findall(r"Action: (.*?)$", msg, re.MULTILINE)[0]
        # 从消息中提取最后的行动结果
        last_act = re.findall(r"Summary: (.*?)$", msg, re.MULTILINE)[0]
        # 打印观察结果
        print_with_color("Observation:", "yellow")
        print_with_color(observation, "magenta")
        # 打印思考结果
        print_with_color("Thought:", "yellow")
        print_with_color(think, "magenta")
        # 打印行动结果
        print_with_color("Action:", "yellow")
        print_with_color(act, "magenta")
        # 打印最后的行动结果
        print_with_color("Summary:", "yellow")
        print_with_color(last_act, "magenta")
        # 如果行动结果包含"FINISH"，则返回["FINISH"]
        if "FINISH" in act:
            return ["FINISH"]
        # 提取行动名称
        act_name = act.split("(")[0]
        # 根据不同的行动名称，进行不同的处理
        if act_name == "tap":
            area = int(re.findall(r"tap\((.*?)\)", act)[0])
            return [act_name, area, last_act]
        elif act_name == "text":
            input_str = re.findall(r"text\((.*?)\)", act)[0][1:-1]
            return [act_name, input_str, last_act]
        elif act_name == "long_press":
            area = int(re.findall(r"long_press\((.*?)\)", act)[0])
            return [act_name, area, last_act]
        elif act_name == "swipe":
            params = re.findall(r"swipe\((.*?)\)", act)[0]
            area, swipe_dir, dist = params.split(",")
            area = int(area)
            swipe_dir = swipe_dir.strip()[1:-1]
            dist = dist.strip()[1:-1]
            return [act_name, area, swipe_dir, dist, last_act]
        elif act_name == "grid":
            return [act_name]
        else:
            print_with_color(f"ERROR: Undefined act {act_name}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]

def parse_grid_rsp(rsp):
    """
    这个函数用于解析GPT-4模型的网格响应。

    参数:
    rsp (dict): GPT-4模型的响应。

    返回:
    list: 解析后的结果。

    """

    try:
        # 从响应中获取消息内容
        msg = rsp["choices"][0]["message"]["content"]
        # 从消息中提取观察结果
        observation = re.findall(r"Observation: (.*?)$", msg, re.MULTILINE)[0]
        # 从消息中提取思考结果
        think = re.findall(r"Thought: (.*?)$", msg, re.MULTILINE)[0]
        # 从消息中提取行动结果
        act = re.findall(r"Action: (.*?)$", msg, re.MULTILINE)[0]
        # 从消息中提取最后的行动结果
        last_act = re.findall(r"Summary: (.*?)$", msg, re.MULTILINE)[0]
        # 打印观察结果
        print_with_color("Observation:", "yellow")
        print_with_color(observation, "magenta")
        # 打印思考结果
        print_with_color("Thought:", "yellow")
        print_with_color(think, "magenta")
        # 打印行动结果
        print_with_color("Action:", "yellow")
        print_with_color(act, "magenta")
        # 打印最后的行动结果
        print_with_color("Summary:", "yellow")
        print_with_color(last_act, "magenta")
        # 如果行动结果包含"FINISH"，则返回["FINISH"]
        if "FINISH" in act:
            return ["FINISH"]
        # 提取行动名称
        act_name = act.split("(")[0]
        # 根据不同的行动名称，进行不同的处理
        if act_name == "tap":
            params = re.findall(r"tap\((.*?)\)", act)[0].split(",")
            area = int(params[0].strip())
            subarea = params[1].strip()[1:-1]
            return [act_name + "_grid", area, subarea, last_act]
        elif act_name == "long_press":
            params = re.findall(r"long_press\((.*?)\)", act)[0].split(",")
            area = int(params[0].strip())
            subarea = params[1].strip()[1:-1]
            return [act_name + "_grid", area, subarea, last_act]
        elif act_name == "swipe":
            params = re.findall(r"swipe\((.*?)\)", act)[0].split(",")
            start_area = int(params[0].strip())
            start_subarea = params[1].strip()[1:-1]
            end_area = int(params[2].strip())
            end_subarea = params[3].strip()[1:-1]
            return [act_name + "_grid", start_area, start_subarea, end_area, end_subarea, last_act]
        elif act_name == "grid":
            return [act_name]
        else:
            print_with_color(f"ERROR: Undefined act {act_name}!", "red")
            return ["ERROR"]
    except Exception as e:
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]


def parse_reflect_rsp(rsp):
    """
    这个函数用于解析GPT-4模型的反射响应。

    参数:
    rsp (dict): GPT-4模型的响应。

    返回:
    list: 解析后的结果。

    """

    try:
        # 从响应中获取消息内容
        msg = rsp["choices"][0]["message"]["content"]
        # 从消息中提取决策结果
        decision = re.findall(r"Decision: (.*?)$", msg, re.MULTILINE)[0]
        # 从消息中提取思考结果
        think = re.findall(r"Thought: (.*?)$", msg, re.MULTILINE)[0]
        # 打印决策结果
        print_with_color("Decision:", "yellow")
        print_with_color(decision, "magenta")
        # 打印思考结果
        print_with_color("Thought:", "yellow")
        print_with_color(think, "magenta")
        # 如果决策结果是"INEFFECTIVE"，则返回[决策结果, 思考结果]
        if decision == "INEFFECTIVE":
            return [decision, think]
        # 如果决策结果是"BACK"或"CONTINUE"或"SUCCESS"
        elif decision == "BACK" or decision == "CONTINUE" or decision == "SUCCESS":
            # 从消息中提取文档结果
            doc = re.findall(r"Documentation: (.*?)$", msg, re.MULTILINE)[0]
            # 打印文档结果
            print_with_color("Documentation:", "yellow")
            print_with_color(doc, "magenta")
            # 返回[决策结果, 思考结果, 文档结果]
            return [decision, think, doc]
        else:
            # 打印错误信息
            print_with_color(f"ERROR: Undefined decision {decision}!", "red")
            return ["ERROR"]
    except Exception as e:
        # 打印错误信息
        print_with_color(f"ERROR: an exception occurs while parsing the model response: {e}", "red")
        print_with_color(rsp, "red")
        return ["ERROR"]
