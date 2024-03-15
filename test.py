# 帮我写一个将json格式读入excel文件的函数，函数名为json_to_excel(json_file, excel_file)。json_file是json文件的路径，excel_file是excel文件的路径。json文件的格式如下：
# [
#     {
#         "题干": "MATLAB的Workspace中显示的变量信息不包含以下哪项？",
#         "选项A": "变量类型",
#         "选项B": "变量大小",
#         "选项C": "变量的内存地址",
#         "选项D": "变量的值",
#         "正确答案": "C"
#     },
#     {
#         "题干": "在MATLAB中，如何清除Workspace中所有的变量？",
#         "选项A": "clear all",
#         "选项B": "delete all",
#         "选项C": "remove all",
#         "选项D": "reset all",
#         "正确答案": "A"
#     },
#     {
#         "题干": "如何将Workspace中的变量保存到MAT文件？",
#         "选项A": "file -> save",
#         "选项B": "save('filename.mat')",
#         "选项C": "export('filename.mat')",
#         "选项D": "write('filename.mat')",
#         "正确答案": "B"
#     },
#     {
#         "题干": "在MATLAB中，Workspace窗口通常用来做什么？",
#         "选项A": "显示当前函数的帮助文档",
#         "选项B": "管理当前的路径和文件",
#         "选项C": "显示和修改当前的变量",
#         "选项D": "编写和执行脚本或函数",
#         "正确答案": "C"
#     },
#     {
#         "题干": "在MATLAB中，如果一个变量在Workspace中出现但我不记得它是如何计算出来的，我应该怎么做？",
#         "选项A": "重新启动MATLAB",
#         "选项B": "使用'doc'命令查找帮助文档",
#         "选项C": "检查命令历史记录来追溯该变量",
#         "选项D": "该变量不可能出现在Workspace中",
#         "正确答案": "C"
#     }
# ]
# excel文件的格式如下：
# 题号 题干	选项A	选项B	选项C	选项D	正确答案
# 1	MATLAB的Workspace中显示的变量信息不包含以下哪项？	变量类型	变量大小	变量的内存地址	变量的值	C
# 2	在MATLAB中，如何清除Workspace中所有的变量？	clear all	delete all	remove all	reset all	A
# 3	如何将Workspace中的变量保存到MAT文件？	file -> save	save('filename.mat')	export('filename.mat')	write('filename.mat')	B
# 4	在MATLAB中，Workspace窗口通常用来做什么？	显示当前函数的帮助文档	管理当前的路径和文件	显示和修改当前的变量	编写和执行脚本或函数	C
# 5	在MATLAB中，如果一个变量在Workspace中出现但我不记得它是如何计算出来的，我应该怎么做？	重新启动MATLAB	使用'doc'命令查找帮助文档	检查命令历史记录来追溯该变量	该变量不可能出现在Workspace中	C
# 请你仔细阅读题目描述，然后完成函数的编写。
import jiesheng

jason = {
  "题目1": {
    "题干": "In MATLAB, which command creates a 3x1 column vector?",
    "选项A": "A = [1, 2, 3];",
    "选项B": "A = (1; 2; 3);",
    "选项C": "A = [1; 2; 3];",
    "选项D": "A = 1:3;",
    "正确答案": "C"
  },
  "题目2": {
    "题干": "How would you index the third element of an array named 'arr' in MATLAB?",
    "选项A": "arr(3);",
    "选项B": "arr{3};",
    "选项C": "arr[3];",
    "选项D": "arr<3>;",
    "正确答案": "A"
  },
  "题目3": {
    "题干": "What is the correct syntax to reverse the elements of a row vector v in MATLAB?",
    "选项A": "v(end:-1:1);",
    "选项B": "reverse(v);",
    "选项C": "v[::-1];",
    "选项D": "flip(v);",
    "正确答案": "A"
  },
  "题目4": {
    "题干": "To create a 4x4 identity matrix in MATLAB, which function would you use?",
    "选项A": "eye(4);",
    "选项B": "identity(4);",
    "选项C": "ones(4);",
    "选项D": "zeros(4);",
    "正确答案": "A"
  },
  "题目5": {
    "题干": "In MATLAB, how do you create a 2x3 matrix of zeros?",
    "选项A": "zeros(2, 3);",
    "选项B": "zeros[2, 3];",
    "选项C": "zero(2, 3);",
    "选项D": "zeros{2, 3};",
    "正确答案": "A"
  },
  "题目6": {
    "题干": "If 'M' is a 3x3 matrix, which command would correctly replace the second row with [1, 2, 3]?",
    "选项A": "M(2, :) = [1 2 3];",
    "选项B": "M(2) = [1, 2, 3];",
    "选项C": "M{2} = [1, 2, 3];",
    "选项D": "M[2, :] = [1, 2, 3];",
    "正确答案": "A"
  },
  "题目7": {
    "题干": "In MATLAB, how can you concatenate two row vectors a and b horizontally?",
    "选项A": "[a; b]",
    "选项B": "[a, b]",
    "选项C": "concat(a, b)",
    "选项D": "join(a, b)",
    "正确答案": "B"
  },
  "题目8": {
    "题干": "Which MATLAB function would you use to concatenate two matrices A and B vertically?",
    "选项A": "vertcat(A, B);",
    "选项B": "cat(2, A, B);",
    "选项C": "[A; B];",
    "选项D": "append(A, B);",
    "正确答案": "C"
  }
}
# 请你仔细阅读题目描述，然后完成函数的编写。
import pandas as pd


def json_to_excel(excel_file):
    df = pd.DataFrame(jason).T
    df.index.name = '题号'
    df.reset_index(inplace=True)
    df.to_excel(excel_file, index=False)
    return df


if __name__ == '__main__':
  num = 4
  # step_num = 2
  # explore_tokens = 3
  # reflect_tokens = 4
  # similarity_index = 0.5
  # jiesheng.write_to_excel(num, step_num, explore_tokens, reflect_tokens, similarity_index,
  #                         "D:\Desktop\projects\AppAgent-main\\task_result.xlsx")
  app, task, using_method = jiesheng.learn_from_excel(num, "D:\Desktop\projects\AppAgent-main\\task_result.xlsx")
  print(app, task, using_method)
  print(f"python learn.py --app {app} --task {task} --using_method {using_method} --num {num}")
