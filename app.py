import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io

# ==========================================
# 专家知识库：为不同鞋履风格配置专属的评审侧重点
# ==========================================
EXPERT_PROMPTS = {
    "通用系列": "关注整体电商视觉规范、排版布局合理性、以及商品展示的清晰度和转化逻辑。",
    "真皮系列": "作为高级皮具鉴定与视觉呈现专家，重点苛求皮料纹理（如荔枝纹、纳帕皮）的真实感、皮面光泽的折射率、以及如何通过光影凸显皮革的昂贵与细腻质感。",
    "牛津鞋": "作为英伦经典男装视觉专家，评审重点在于体现鞋履的正式感、布洛克雕花的细节锐度、以及整体画面的绅士、复古、严谨与克制的高级氛围。",
    "运动鞋": "作为潮流与运动科技视觉专家，重点评审鞋底科技感（如气垫、发泡材质）的表达、透气网面的材质细节、以及画面是否传递出动感、轻盈、透气和爆发力。",
    "正装鞋": "作为高端商务视觉专家，要求画面呈现出绝对的稳重与专业感，关注线条的流畅度、漆皮或抛光面的完美倒影、楦型的修长感，以及搭配场景的商务等级。",
    "乐福鞋": "作为Smart Casual与地中海度假风视觉专家，重点评审画面是否传达出慵懒、松弛、优雅的氛围，以及麂皮或软皮面料的柔软度与垂坠感展示。",
    "一脚蹬鞋": "作为日常通勤与休闲视觉专家，重点评估穿脱便利性的视觉暗示（如松紧带细节）、鞋垫软弹感的表达，以及整体画面的亲和力与生活化场景营造。"
}

# ==========================================
# 辅助函数：将纯文本排版并渲染为高质量 JPG 长图
# ==========================================
# ⚠️ 注意：这里已经将默认字体后缀改为了大写的 .TTF
def create_report_image(text, font_path="font.TTF"):
    img_width = 1200
    margin_x = 80
    margin_y = 80
    
    lines = []
    for paragraph in text.split('\n'):
        wrapped = textwrap.wrap(paragraph, width=38) 
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)
            
    line_height = 46
    img_height = max(1000, len(lines) * line_height + 300)
    
    img = Image.new('RGB', (img_width, img_height), color=(24, 24, 28))
    draw = ImageDraw.Draw(img)
    
    try:
        # 这里会去读取您的 font.TTF
        font = ImageFont.truetype(font_path, 28)
        title_font = ImageFont.truetype(font_path, 42)
    except IOError:
        st.warning(f"⚠️ 未检测到 {font_path} 字体文件，图片中文可能无法正常显示。请确保文件名大小写完全一致。")
        font = ImageFont.load_default()
        title_font = font

    draw.text((margin_x, margin_y), "Listing 深度评审报告", font=title_font, fill=(255, 204, 0))
    draw.line([(margin_x, margin_y + 70), (img_width - margin_x, margin_y + 70)], fill=(60, 60, 65), width=2)

    y_text = margin_y + 120
    for line in lines:
        text_color = (255, 255, 255) if line.startswith("#") else (200, 200, 200)
        draw.text((margin_x, y_text), line, font=font, fill=text_color)
        y_text += line_height

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=100)
    return img_byte_arr.getvalue()


# ==========================================
# 主界面代码
# ==========================================
st.set_page_config(page_title="视觉设计专家评审台", layout="wide")
st.title("BM Listing 方案一键评审")

st.sidebar.header("⚙️ 核心配置")

style_option = st.sidebar.selectbox(
    "选择当前设计方案的主题风格", 
    list(EXPERT_PROMPTS.keys())
)

uploaded_file = st.file_uploader("请拖拽上传您的 A+ 页面或视觉方案 (支持 JPG/PNG)", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, caption="当前待评审方案", use_container_width=True)

    if st.button("🚀 开始深度评审", type="primary"):
        with st.spinner(f"【{style_option}】专属视觉专家正在进行分析，请稍候..."):
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5--pro')
                
                expert_focus = EXPERT_PROMPTS[style_option]
                
                # ⚠️ 提示词大脑深度重写：强制要求拆分双端评价
                system_prompt = f"""
                你是一个冷静、客观且具有批判性思维的资深商业视觉设计专家，如果我的观点存在事实错误、逻辑漏洞或认知偏差，请直接予以纠正，不要为了礼貌而顺从我。在给出建议时，请权衡利弊，提供多个视角的分析，而不仅仅是支持我的初步想法。
                
                【特别分析指令：同图双端独立评审】
                请极其注意：用户上传的是一张拼图稿件，里面**同时包含了 PC端（通常为较宽的排版）和 手机端（通常为较窄的竖排长图）**的设计方案。如果画面中有横向排列的图片组合，那是轮播图，轮播图会配置在亚马逊的轮播模块，你无需强调。
                你必须在脑内强制将其拆解为两个独立的载体！在接下来的评审中，必须明确区分出“对PC端的评价”和“对手机端的评价”，重点评价PC端，手机端只需要看版面视觉是否顺畅即可。
                
                【专家人设与专属标准】
                当前设计方案品类为：【{style_option}】。
                作为该细分领域的绝对专家，同时也是一名普通的消费者，你的核心评审侧重点是：{expert_focus}
                
                【输出要求】
                请严格按照以下5个模块输出结构化报告：
                
                ### 1. 综合视觉评分（1-10分）
                （给出一个总分，并用一句话犀利地点评第一眼的整体视觉冲击力）
                
                ### 2. 视觉焦点热力分析与优化建议
                * **PC端表现：**（分析宽屏下的视觉引导是否合理）
                * **手机端表现：**（分析窄屏下的留白、主体占比是否聚焦）
                
                ### 3. 卖点提炼与文案撰写的视觉表达
                * **PC端表现：**（评价排版节奏、文案信息层级与文案准确性）
                * **手机端表现：**（特别评价手机端字号是否过小影响阅读）
                
                ### 4. 给设计师的避坑指南
                （以资深总监的口吻，指出当前在双端适配或整体调性上，最容易导致“显廉价”或“降低转化”的致命错误）
                
                ### 5. 总结优化清单
                （提炼出最核心的 3-5 条直接修改行动指令，作为设计师的 To-Do List）
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
