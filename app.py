import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io

# ==========================================
# 辅助函数：将纯文本排版并渲染为高质量 JPG 长图
# ==========================================
def create_report_image(text, font_path="font.ttf"):
    # 1. 扩大图片画布尺寸和边距（从 800 扩大到 1200）
    img_width = 1200
    margin_x = 80
    margin_y = 80
    
    # 2. 优化每行字数限制，绝对防止截断
    lines = []
    for paragraph in text.split('\n'):
        # 限制每行最多 38 个字符，留出充足的右侧呼吸感留白
        wrapped = textwrap.wrap(paragraph, width=38) 
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)
            
    # 3. 动态计算长图的整体高度
    line_height = 46
    img_height = max(1000, len(lines) * line_height + 300)
    
    # 4. 创建深色高级感画布
    img = Image.new('RGB', (img_width, img_height), color=(24, 24, 28))
    draw = ImageDraw.Draw(img)
    
    # 5. 加载字体并调大字号
    try:
        font = ImageFont.truetype(font_path, 28) # 正文加大到28
        title_font = ImageFont.truetype(font_path, 42) # 标题加大到42
    except IOError:
        font = ImageFont.load_default()
        title_font = font

    # 6. 绘制标题与分割线
    draw.text((margin_x, margin_y), "Listing 深度评审报告", font=title_font, fill=(255, 204, 0))
    draw.line([(margin_x, margin_y + 70), (img_width - margin_x, margin_y + 70)], fill=(60, 60, 65), width=2)

    # 7. 逐行绘制正文文字
    y_text = margin_y + 120
    for line in lines:
        text_color = (255, 255, 255) if line.startswith("#") else (200, 200, 200)
        draw.text((margin_x, y_text), line, font=font, fill=text_color)
        y_text += line_height

    # 8. 导出高清图片
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=100)
    return img_byte_arr.getvalue()

# ==========================================
# 主界面代码
# ==========================================
st.set_page_config(page_title="视觉设计专家评审台", layout="wide")
st.title("👞 BM Listing 方案一键评审台")

st.sidebar.header("⚙️ 核心配置")

style_option = st.sidebar.selectbox(
    "选择当前设计方案的主题风格", 
    [
        "高奢鞋履/服饰纪实 (强调面料垂坠感与自然光影)", 
        "8K超清珠宝静物 (强调极致微距与材质光泽)", 
        "南欧城市街拍氛围 (强调复古胶片感与建筑背景层次)",
        "智能化教育空间展示 (强调现代多媒体科技感)",
        "通用亚马逊商业展示"
    ]
)

uploaded_file = st.file_uploader("请拖拽上传您的 A+ 页面或视觉方案 (支持 JPG/PNG)", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, caption="当前待评审方案", use_container_width=True)

    if st.button("🚀 开始深度评审", type="primary"):
        with st.spinner("AI 视觉专家正在进行像素级分析，请稍候..."):
            try:
                # 从云端保险箱读取密钥
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                system_prompt = f"""
                你是一个冷静、客观且具有批判性思维的资深商业视觉设计专家。
                当前用户提交的设计稿属于【{style_option}】风格。
                请以挑剔的普通消费者和专业美术指导的双重视角，对这张商业摄影/设计图进行严苛评审。
                
                请严格按照以下结构输出报告：
                ### 1. 综合视觉评分（0-100分）
                ### 2. 视觉焦点热力分析
                ### 3. 卖点与画面匹配度
                ### 4. 核心优化行动清单 (To-Do List)
                （提供至少 3 条直接具体的修改建议）
                """
                
                response = model.generate_content([system_prompt, img])
                
                st.success("✅ 评审完成！")
                st.markdown("---")
                st.markdown(response.text)
                st.markdown("---")
                
                jpg_data = create_report_image(response.text, font_path="font.TTF")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 一键下载评审报告 (TXT文本)", 
                        data=response.text, 
                        file_name="Listing_AI_Review_Report.txt",
                        mime="text/plain"
                    )
                with col2:
                    st.download_button(
                        label="🖼️ 保存为 JPG 图片 (长图)", 
                        data=jpg_data, 
                        file_name="Listing_AI_Review_Poster.jpg",
                        mime="image/jpeg"
                    )
                    
            except Exception as e:
                st.error(f"调用 AI 失败，请检查错误信息: {e}")
