import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import time
import re

# ==========================================
# 专家知识库：款式与场所的中英对照逻辑
# ==========================================
SHOE_STYLES = {
    "牛津鞋 (Oxfords)": "正式感与现代感的平衡，关注鞋楦线条及布洛克细节。",
    "休闲运动鞋 (Sneakers)": "强调轻盈科技与都市动感，关注材质透气感及画面活力。",
    "正装鞋 (Dress Shoes)": "纯正商务属性，关注缝线严谨度及稳重调性。",
    "乐福鞋 (Loafers)": "松弛优雅，关注穿脱便利性及皮质柔韧度。",
    "靴类 (Boots)": "轮廓美学与硬朗层次，关注男性气概的视觉传达。",
    "一脚蹬/便鞋 (Slip-ons)": "极致便利与居家/通勤的亲和力表达。"
}

OCCASIONS = {
    "日常百搭 (Daily Essentials)": "生活气息背景，自然光影，强调耐穿百搭。",
    "商务职场 (Business-Ready)": "简洁有力背景，冷色调，强调专业身份。",
    "休闲度假 (Casual & Leisure)": "户外/咖啡馆氛围，温润光线，强调脚感舒适。",
    "特殊/正式场合 (Special Occasions)": "高级感/暗调背景，高对比度光影，强调社交溢价。"
}

# ==========================================
# 辅助函数：生成纯净排版的 JPG 报告 (移除 Markdown 符号)
# ==========================================
def create_report_image(text, font_path="font.TTF"):
    # 1. 预处理文本：移除 Markdown 符号
    clean_text = text.replace("**", "").replace("__", "")
    
    img_width = 1200
    margin_x = 80
    margin_y = 80
    line_height = 50
    
    # 2. 准备排版行
    processed_lines = []
    raw_paragraphs = clean_text.split('\n')
    
    for p in raw_paragraphs:
        if not p.strip():
            processed_lines.append(("EMPTY", ""))
            continue
        
        # 识别标题行并移除 #
        if p.startswith('#'):
            title_content = p.replace('#', '').strip()
            processed_lines.append(("TITLE", title_content))
        else:
            # 正文自动换行
            wrapped = textwrap.wrap(p, width=42)
            for w_line in wrapped:
                processed_lines.append(("BODY", w_line))

    # 3. 计算高度
    img_height = len(processed_lines) * line_height + 300
    img = Image.new('RGB', (img_width, img_height), color=(24, 24, 28))
    draw = ImageDraw.Draw(img)
    
    try:
        font_body = ImageFont.truetype(font_path, 28)
        font_title = ImageFont.truetype(font_path, 38)
        font_main_title = ImageFont.truetype(font_path, 48)
    except:
        font_body = font_title = font_main_title = ImageFont.load_default()

    # 4. 绘制页眉
    draw.text((margin_x, margin_y), "BM Listing 视觉方案评审报告", font=font_main_title, fill=(255, 204, 0))
    draw.line([(margin_x, margin_y + 80), (img_width - margin_x, margin_y + 80)], fill=(60, 60, 65), width=2)

    # 5. 循环绘制
    y_cursor = margin_y + 140
    for l_type, content in processed_lines:
        if l_type == "TITLE":
            y_cursor += 20
            draw.text((margin_x, y_cursor), content, font=font_title, fill=(255, 204, 0))
            y_cursor += line_height + 10
        elif l_type == "BODY":
            # 识别列表符号并稍微缩进
            x_pos = margin_x
            if content.strip().startswith('-') or content.strip().startswith('·'):
                x_pos += 20
            draw.text((x_pos, y_cursor), content, font=font_body, fill=(210, 210, 215))
            y_cursor += line_height
        elif l_type == "EMPTY":
            y_cursor += 30

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=95)
    return img_byte_arr.getvalue()

# ==========================================
# 主界面
# ==========================================
st.set_page_config(page_title="BM 视觉专家评审系统", layout="wide")
st.title("👞 BM Listing 方案一键评审")

st.sidebar.header("⚙️ 评审参数配置")
shoe_val = st.sidebar.selectbox("选择品类", list(SHOE_STYLES.keys()))
occ_val = st.sidebar.selectbox("选择场所", list(OCCASIONS.keys()))
is_leather = st.sidebar.toggle("是否包含真皮材质", value=False)

uploaded_file = st.file_uploader("上传设计方案 (JPG/PNG)", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    img.thumbnail((1024, 1024))
    st.image(img, caption="当前待评审方案", use_container_width=True)

    if st.button("🚀 开始专家级深度评审", type="primary"):
        # 1. 初始化百分比进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("正在初始化专家大脑... 15%")
        progress_bar.progress(15)
        time.sleep(0.4)
        
        status_text.text("正在分析款式与场所契合度... 40%")
        progress_bar.progress(40)
        
        try:
            leather_prompt = ""
            if is_leather:
                leather_prompt = "\n【真皮专项审查】：方案需体现‘真皮体感’。评审光影策划是否预留了表现纹理的空间，背景是否支撑真皮的高级感。"

            system_prompt = f"""
            你是一名【资深商业视觉总监】和【挑剔买家】。评审 Bruno Marc (BM) 亚马逊 A+ 方案。
            款式：{shoe_val} | 场所：{occ_val} | {'真皮' if is_leather else '常规材质'}{leather_prompt}

            【输出要求：模块3必须中英对照】
            ### 1. 综合视觉定调
            ### 2. 焦点路径与构图诊断
            ### 3. 卖点表达与文案优化 (Bilingual Review)
            - 视觉匹配诊断：(中文说明)
            - 视觉修改方案：(中文说明)
            - 文案优化建议：(必须提供中英对照格式，例如：'Cloud-like Comfort (如云朵般舒适的脚感)')，且英文长度必须适配排版空间。
            ### 4. 致命缺陷预警
            ### 5. 落地执行清单 (To-Do List)
            """

            status_text.text("AI 正在像素级扫描画面细节... 75%")
            progress_bar.progress(75)

            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
            # 使用您反馈的极速预览版模型
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            response = model.generate_content([system_prompt, img])
            
            status_text.text("正在生成纯净版长图报告... 95%")
            progress_bar.progress(95)
            
            jpg_data = create_report_image(response.text, font_path="font.TTF")
            
            progress_bar.progress(100)
            status_text.text("评审已就绪！")
            time.sleep(0.5)
            status_text.empty()
            progress_bar.empty()

            st.success("专家报告已生成：")
            st.markdown(response.text)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(label="📥 下载 TXT 报告", data=response.text, file_name="BM_Report.txt")
            with col2:
                st.download_button(label="🖼️ 保存为 JPG 纯净版长图", data=jpg_data, file_name="BM_Review_Poster.jpg", mime="image/jpeg")
                
        except Exception as e:
            st.error(f"调用 AI 失败: {e}")
