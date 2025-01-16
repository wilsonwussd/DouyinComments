from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # 创建一个正方形图像
    size = (256, 256)
    image = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    
    # 绘制圆形背景
    circle_bbox = (20, 20, 236, 236)
    draw.ellipse(circle_bbox, fill='#FF0050')  # 抖音红色
    
    # 绘制评论图标
    comment_bbox = (58, 58, 198, 198)
    draw.ellipse(comment_bbox, fill='white')
    draw.ellipse((78, 78, 178, 178), fill='#FF0050')
    
    # 保存为ICO格式
    image.save('icon.ico', format='ICO', sizes=[(256, 256)])

if __name__ == '__main__':
    create_icon() 