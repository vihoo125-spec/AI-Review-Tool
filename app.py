import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io

# ==========================================
# 辅助函数：将纯文本排版并渲染为高质量 JPG 长图
# ==========================================
def create_report_image(text, font_path="font.TTF"):
    lines = []
    for paragraph in text.split('\n'):
        wrapped = textwrap.wrap(paragraph, width=32) 
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)
            
    line_height = 40
    img_height = max(800, len(lines) * line_height + 200)
    
    img = Image.new('RGB', (800, img_height), color=(24, 24, 28))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(font_path, 24)
        title_font = ImageFont.truetype(font_path, 36)
    except IOError:
        st.warning("⚠️ 未检测到 font.ttf 字体文件，图片中文可能无法正常显示。")
        font = ImageFont.load_default()
        title_font = font

    draw.text((40, 40), "Listing 深度评审报告", font=title_font, fill=(255, 204, 0))
    draw.line([(40, 95), (760, 95)], fill=(60, 60, 65), width=2)

    y_text = 120
    for line in lines:
        text_color = (255, 255, 255) if line.startswith("#") else (200, 200, 200)
        draw.text((40, y_text), line, font=font, fill=text_color)
        y_text += line_height

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=95)
    return img_byte_arr.getvalue()


# ==========================================
# 主界面代码
# ==========================================
st.set_page_config(page_title="视觉设计专家评审台", layout="wide")
st.title("👁️ Listing 方案一键评审台")

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
                
                jpg_data = create_report_image(response.text, font_path="font.ttf")
                
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
