path = "/Users/vincent/Downloads/actor_names.txt"

remove_words = ['永久域名', '上一頁']

filtered_lines = []
removed_lines = []

# with open(path, 'r', encoding='utf-8') as file:
#     lines = file.readlines()
#     for line in lines:
#         if any(word in line for word in remove_words):
#             removed_lines.append(line)
#         elif len(line.strip()):
#             filtered_lines.append(line)

# print(removed_lines)
# print(filtered_lines)

last_line = ''

with open(path, 'r', encoding='utf-8') as file:
    lines = file.readlines()
    for line in lines:
        if line != last_line:
            last_line = line
            filtered_lines.append(line)

with open(path, 'w', encoding='utf-8') as file:
    file.writelines(filtered_lines)
