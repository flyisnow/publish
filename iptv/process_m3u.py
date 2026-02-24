#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import requests
import os

# --- 可配置项 ---
RADIO_KEYWORDS = ["广播", "电台", "Radio", "FM", "AM"]

def process_m3u_content(original_content: str) -> str:
    """
    处理M3U内容字符串：过滤广播、添加频道号等。

    Args:
        original_content: 原始的M3U文件内容。

    Returns:
        处理后的M3U内容字符串。
    """
    new_lines = []
    tv_channel_counter = 1
    skipping_current_entry = False
    group_title_pattern = re.compile(r'group-title="([^"]*)"')

    lines = original_content.splitlines()

    if not lines or not lines[0].strip().startswith('#EXTM3U'):
        print("[!] 错误: 文件不是有效的M3U格式 (缺少 #EXTM3U 文件头)。", file=sys.stderr)
        return None

    # 保留文件头
    new_lines.append(lines[0].strip())

    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue

        if line.startswith('#EXTINF'):
            skipping_current_entry = False
            
            match = group_title_pattern.search(line)
            if match and any(keyword in match.group(1) for keyword in RADIO_KEYWORDS):
                print(f"[*] 过滤广播频道 (组: {match.group(1)})", file=sys.stderr)
                skipping_current_entry = True
                continue

            parts = line.split(' ', 1)
            new_attribute = f'channel-number="{tv_channel_counter}"'
            
            modified_line = f"{parts[0]} {new_attribute} {parts[1]}" if len(parts) > 1 else f"{parts[0]} {new_attribute}"
            new_lines.append(modified_line)
            tv_channel_counter += 1
        
        elif line.startswith('#'):
            print(f"[*] 忽略非标准标签/注释行: {line}", file=sys.stderr)
            continue
            
        else: # 通常是URL行
            if skipping_current_entry:
                continue
            new_lines.append(line)

    print(f"[*] 处理完成！保留并编号了 {tv_channel_counter - 1} 个电视频道。", file=sys.stderr)
    return '\n'.join(new_lines)


def main():
    """
    主执行函数：解析参数，获取URL，处理内容，并写入文件。
    """
    if len(sys.argv) != 3:
        print("用法: python process_m3u.py <input_url> <output_filepath>", file=sys.stderr)
        print("示例: python process_m3u.py http://example.com/playlist.m3u ./kodi.m3u8", file=sys.stderr)
        sys.exit(1)

    input_url = sys.argv[1]
    output_filepath = sys.argv[2]
    
    # 1. 获取远程内容
    try:
        print(f"[*] 正在从URL获取文件: {input_url}", file=sys.stderr)
        response = requests.get(input_url, timeout=20)
        response.raise_for_status()
        response.encoding = 'utf-8'
        original_content = response.text
        if not original_content.strip():
            print("[!] 错误: 获取到的文件内容为空。", file=sys.stderr)
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"[!] 错误: 无法获取URL内容。 {e}", file=sys.stderr)
        print("[*] 操作已中断，不会创建或覆盖输出文件。", file=sys.stderr)
        sys.exit(1)

    # 2. 处理内容
    print("[*] 文件获取成功，开始处理内容...", file=sys.stderr)
    processed_content = process_m3u_content(original_content)

    # 3. 检查处理结果并写入文件
    if processed_content:
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(processed_content)
                f.write('\n') # 确保文件末尾有一个换行符
            print(f"[✓] 成功！已将处理后的播放列表写入到: {output_filepath}", file=sys.stderr)
        except IOError as e:
            print(f"[!] 错误: 无法写入文件 {output_filepath}。 {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("[!] 错误: 内容处理失败，未生成任何内容以供写入。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()