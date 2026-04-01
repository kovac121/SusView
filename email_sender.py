#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件发送模块
将生成的HTML通过邮件发送
"""
import os
import sys
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

# 解决Windows控制台编码问题（只在主模块中重定向，避免重复重定向）
if __name__ == '__main__' and sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 163邮箱配置（从环境变量读取）
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.163.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'kovac121@163.com')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')
RECIPIENTS = os.getenv('RECIPIENTS', 'kovac121@163.com').split(',')


def send_html_email(html_content: str, subject: str = None, recipients: list = None) -> bool:
    """发送HTML邮件"""
    if subject is None:
        subject = f"ESG新闻 {datetime.now().strftime('%Y年%m月%d日')}"

    if recipients is None:
        recipients = RECIPIENTS

    if not SENDER_PASSWORD:
        print("⚠️ 邮件功能未配置 SENDER_PASSWORD 环境变量")
        return False

    try:
        print(f"📧 正在发送邮件到 {recipients}...")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"ESG Bot <{SENDER_EMAIL}>"
        msg['To'] = ','.join(recipients)

        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        server.quit()

        print(f"✅ 邮件发送成功!")
        return True

    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


def send_html_file(html_file_path: str, subject: str = None, recipients: list = None) -> bool:
    """发送HTML文件"""
    if subject is None:
        subject = f"ESG新闻 {datetime.now().strftime('%Y年%m月%d日')}"

    if recipients is None:
        recipients = RECIPIENTS

    if not SENDER_PASSWORD:
        print("⚠️ 邮件功能未配置 SENDER_PASSWORD 环境变量")
        return False

    try:
        html_path = Path(html_file_path)
        if not html_path.exists():
            print(f"❌ HTML文件不存在: {html_file_path}")
            return False

        html_content = html_path.read_text(encoding='utf-8')

        # 纯文本版本（包含源码供微信公众号使用）
        plain_content = f"""ESG新闻 {datetime.now().strftime('%Y年%m月%d日')}

========== 微信公众号发布说明 ==========
1. 复制下方 HTML 源码（从 <!DOCTYPE 开始到 </html> 结束）
2. 登录微信公众号后台
3. 新建图文消息 → 点击「源码」按钮（<> 图标）
4. 粘贴内容即可发布
=====================================

"""

        plain_content += html_content

        return send_mixed_email(plain_content, html_content, subject, recipients)

    except Exception as e:
        print(f"❌ 发送HTML文件失败: {e}")
        return False


def send_mixed_email(plain_content: str, html_content: str, subject: str, recipients: list) -> bool:
    """发送混合邮件（纯文本 + HTML）"""
    try:
        print(f"📧 正在发送邮件到 {recipients}...")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"ESG Bot <{SENDER_EMAIL}>"
        msg['To'] = ','.join(recipients)

        plain_part = MIMEText(plain_content, 'plain', 'utf-8')
        msg.attach(plain_part)

        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        server.quit()

        print(f"✅ 邮件发送成功!")
        return True

    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


if __name__ == '__main__':
    print("测试邮件发送...")
    test_html = "<h1>测试邮件</h1><p>这是一封测试邮件</p>"
    result = send_html_email(test_html, "ESG新闻测试")
    print(f"测试{'成功' if result else '失败'}")