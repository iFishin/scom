# 生成指定长度的顺序数字
length = 4096
sequential_data = [i % 10 for i in range(length)]

# 将数据转换为字符串
sequential_data_str = ''.join(str(num) for num in sequential_data)

# 将数据写入txt文件
file_path = '../tmps/byte.txt'
with open(file_path, 'w') as file:
    file.write(sequential_data_str)

print(f"数据已成功写入文件：{file_path}")
