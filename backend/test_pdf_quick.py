#!/usr/bin/env python3
"""
快速测试PDF解析功能的脚本

使用方法:
    python test_pdf_quick.py <pdf_file_path>

示例:
    python test_pdf_quick.py temp_files/联邦劳动法.pdf
    python test_pdf_quick.py /absolute/path/to/file.pdf
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.parse_doc import extract_text_from_pdf


def test_pdf(pdf_path):
    """测试PDF文件解析"""
    print("=" * 60)
    print("PDF 文档解析测试")
    print("=" * 60)

    # 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"❌ 错误: 文件不存在: {pdf_path}")
        print(f"   当前工作目录: {os.getcwd()}")
        print(f"   绝对路径: {os.path.abspath(pdf_path)}")
        return False

    # 检查是否是PDF文件
    if not pdf_path.lower().endswith('.pdf'):
        print(f"❌ 错误: 不是PDF文件: {pdf_path}")
        return False

    print(f"\n📄 文件路径: {pdf_path}")
    print(f"📍 绝对路径: {os.path.abspath(pdf_path)}")
    print(f"📦 文件大小: {os.path.getsize(pdf_path) / 1024:.2f} KB")

    try:
        # 提取文本
        print("\n🔄 正在解析PDF...")
        text = extract_text_from_pdf(pdf_path)

        # 显示结果
        print("\n✅ 解析成功!")
        print(f"\n📊 统计信息:")
        print(f"   - 总字符数: {len(text)}")
        print(f"   - 总字节数: {len(text.encode('utf-8'))}")
        print(f"   - 行数: {text.count(chr(10)) + 1}")

        # 显示内容预览
        preview_length = min(500, len(text))
        print(f"\n📖 内容预览 (前 {preview_length} 个字符):")
        print("-" * 60)
        print(text[:preview_length])
        if len(text) > preview_length:
            print("...")

        if len(text) > 1000:
            print(f"\n📖 内容预览 (后 500 个字符):")
            print("-" * 60)
            print("...")
            print(text[-500:])

        # 保存到文件
        output_file = "extracted_text_output.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n💾 完整文本已保存到: {output_file}")

        print("\n" + "=" * 60)
        return True

    except ValueError as e:
        print(f"\n❌ 验证错误: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python test_pdf_quick.py <pdf_file_path>")
        print("\n示例:")
        print("  python test_pdf_quick.py temp_files/联邦劳动法.pdf")
        print("  python test_pdf_quick.py tests/fixtures/test_sample.pdf")
        print("\n可用的测试文件:")

        # 列出可用的PDF文件
        test_dirs = ["tests/fixtures", "temp_files", "upload_files"]
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                pdf_files = [f for f in os.listdir(test_dir) if f.endswith('.pdf')]
                if pdf_files:
                    print(f"\n  {test_dir}/")
                    for pdf_file in pdf_files:
                        file_path = os.path.join(test_dir, pdf_file)
                        size = os.path.getsize(file_path) / 1024
                        print(f"    - {pdf_file} ({size:.2f} KB)")

        sys.exit(1)

    pdf_path = sys.argv[1]
    success = test_pdf(pdf_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
