"""验证码工具模块"""
import random
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple


class CaptchaGenerator:
    """验证码生成器"""
    
    def __init__(self):
        self.width = 120
        self.height = 40
        self.font_size = 20
        self.captcha_length = 4
    
    def generate_math_expression(self) -> Tuple[str, int]:
        """生成数学表达式和答案"""
        operators = ['+', '-', '*']
        operator = random.choice(operators)
        
        if operator == '+':
            a = random.randint(1, 50)
            b = random.randint(1, 50)
            answer = a + b
            expression = f"{a} + {b}"
        elif operator == '-':
            a = random.randint(10, 50)
            b = random.randint(1, a)
            answer = a - b
            expression = f"{a} - {b}"
        else:  # '*'
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            answer = a * b
            expression = f"{a} × {b}"
        
        return expression, answer
    
    def generate_captcha_image(self, expression: str) -> str:
        """生成验证码图片并返回base64编码"""
        # 创建图片
        image = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 添加干扰线
        for _ in range(5):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill='lightgray', width=1)
        
        # 添加干扰点
        for _ in range(20):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill='gray')
        
        # 绘制文字
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.font_size)
        except:
            # 如果没有找到字体，使用默认字体
            font = ImageFont.load_default()
        
        # 计算文字位置使其居中
        bbox = draw.textbbox((0, 0), expression, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2
        
        # 绘制文字（添加一些颜色变化）
        colors = ['black', 'darkblue', 'darkred', 'darkgreen']
        draw.text((x, y), expression, fill=random.choice(colors), font=font)
        
        # 转换为base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate(self) -> Tuple[str, str, int]:
        """生成验证码
        返回: (图片base64, 表达式, 答案)
        """
        expression, answer = self.generate_math_expression()
        image_base64 = self.generate_captcha_image(expression)
        return image_base64, expression, answer


# 全局验证码生成器实例
captcha_generator = CaptchaGenerator()


def generate_captcha() -> Tuple[str, str, int]:
    """生成验证码的便捷函数"""
    return captcha_generator.generate()