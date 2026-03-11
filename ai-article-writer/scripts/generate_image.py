#!/usr/bin/env python3
"""
Gemini Image Generation Script
用于AI Article Writer Skill的配图生成

API文档: https://doc.apicore.ai/api-314031054
使用OpenAI兼容格式调用Gemini图像生成

使用方式:
    python generate_image.py --prompt "描述" --style "科技感" --output "./images/cover.png"

配置要求:
    需要在环境变量或配置文件中设置:
    - GEMINI_API_KEY: API密钥
"""

import argparse
import os
import sys
import json
import base64
import re
from pathlib import Path
from datetime import datetime

# 尝试导入requests，如果没有则提供安装提示
try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("请运行: pip install requests")
    sys.exit(1)

# API默认配置（仅在配置文件中未指定时使用）
DEFAULT_API_ENDPOINT = "https://api.apicore.ai/v1/chat/completions"
DEFAULT_MODEL_NAME = "gemini-3-pro-image-preview-4k"

def load_config():
    """加载API配置"""
    config = {
        "api_key": os.environ.get("GEMINI_API_KEY", ""),
        "endpoint": DEFAULT_API_ENDPOINT,
        "model": DEFAULT_MODEL_NAME,
    }

    # 尝试从配置文件加载
    config_paths = [
        Path(__file__).parent.parent.parent.parent / "gemini_config.json",  # 项目根目录
        Path(__file__).parent.parent / "gemini_config.json",  # skill目录
        Path.home() / ".gemini" / "config.json"  # 用户目录
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    print(f"已加载配置文件: {config_path}")
                    break
            except Exception as e:
                print(f"警告: 读取配置文件失败 {config_path}: {e}")

    return config

def generate_image(prompt: str, style: str, output_path: str, config: dict) -> bool:
    """
    调用Gemini API生成图片 (OpenAI兼容格式)

    Args:
        prompt: 图片描述
        style: 风格关键词
        output_path: 输出路径
        config: API配置

    Returns:
        bool: 是否成功
    """
    if not config["api_key"]:
        print("错误: 未配置 GEMINI_API_KEY")
        print("请设置环境变量或在配置文件中提供API密钥")
        return False

    # 构建完整的prompt
    full_prompt = f"{prompt}, {style}, high quality, detailed"

    # 构建API请求 (OpenAI兼容格式)
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }

    # 从配置获取endpoint和model
    api_endpoint = config.get("endpoint", DEFAULT_API_ENDPOINT)
    model_name = config.get("model", DEFAULT_MODEL_NAME)

    payload = {
        "model": model_name,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": full_prompt
            }
        ]
    }

    try:
        print(f"正在生成图片: {prompt[:50]}...")
        print(f"使用模型: {model_name}")
        print(f"完整Prompt: {full_prompt}")

        response = requests.post(
            api_endpoint,
            headers=headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()

        result = response.json()

        # 解析OpenAI格式的响应，提取图片数据
        image_data = None

        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]

            # 检查message中的content
            if "message" in choice:
                message = choice["message"]
                content = message.get("content", "")

                if isinstance(content, str):
                    # 情况1: Markdown格式的图片链接 ![Image](url)
                    md_pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
                    md_match = re.search(md_pattern, content)
                    if md_match:
                        image_url = md_match.group(1)
                        print(f"从Markdown提取图片URL: {image_url}")
                        img_response = requests.get(image_url, timeout=30)
                        img_response.raise_for_status()
                        image_data = img_response.content

                    # 情况2: 直接是图片URL
                    elif content.startswith("http") and any(ext in content.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        print(f"获取图片URL: {content}")
                        img_response = requests.get(content, timeout=30)
                        img_response.raise_for_status()
                        image_data = img_response.content

                    # 情况3: base64格式
                    elif content.startswith("data:image"):
                        base64_data = content.split(",", 1)[1]
                        image_data = base64.b64decode(base64_data)

                    else:
                        # 尝试从文本中提取任何URL
                        url_pattern = r'(https?://[^\s\)]+(?:jpg|jpeg|png|gif|webp))'
                        url_match = re.search(url_pattern, content, re.IGNORECASE)
                        if url_match:
                            image_url = url_match.group(1)
                            print(f"从文本提取图片URL: {image_url}")
                            img_response = requests.get(image_url, timeout=30)
                            img_response.raise_for_status()
                            image_data = img_response.content
                        else:
                            print(f"响应内容: {content[:200]}...")

                # 情况4: content是数组（包含图片）
                elif isinstance(content, list):
                    for item in content:
                        if item.get("type") == "image_url":
                            image_url = item.get("image_url", {}).get("url", "")
                            if image_url.startswith("http"):
                                print(f"获取图片URL: {image_url}")
                                img_response = requests.get(image_url, timeout=30)
                                img_response.raise_for_status()
                                image_data = img_response.content
                                break
                            elif image_url.startswith("data:image"):
                                base64_data = image_url.split(",", 1)[1]
                                image_data = base64.b64decode(base64_data)
                                break

        if image_data:
            # 确保输出目录存在
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # 保存图片
            with open(output_path, 'wb') as f:
                f.write(image_data)

            print(f"✅ 图片已保存: {output_path}")
            return True

        # 如果上述方法都没找到图片，打印完整响应用于调试
        print("错误: API响应中未找到图片数据")
        print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
        return False

    except requests.exceptions.Timeout:
        print("错误: API请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"错误: API请求失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应内容: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Gemini图片生成脚本 (APICore)")
    parser.add_argument("--prompt", required=True, help="图片描述")
    parser.add_argument("--style", default="科技感, 现代风格, 高质量", help="风格关键词")
    parser.add_argument("--output", required=True, help="输出路径")
    parser.add_argument("--verbose", action="store_true", help="显示详细信息")

    args = parser.parse_args()

    config = load_config()

    if args.verbose:
        print(f"=" * 50)
        print(f"API Endpoint: {config.get('endpoint', DEFAULT_API_ENDPOINT)}")
        print(f"Model: {config.get('model', DEFAULT_MODEL_NAME)}")
        print(f"API Key: {'*' * 8}...{config['api_key'][-4:] if config['api_key'] else '未配置'}")
        print(f"Prompt: {args.prompt}")
        print(f"Style: {args.style}")
        print(f"Output: {args.output}")
        print(f"=" * 50)

    success = generate_image(args.prompt, args.style, args.output, config)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
