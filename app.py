import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io

# ==========================================
# 专家知识库：基于 Bruno Marc 品牌品类精细化梳理
# ==========================================
EXPERT_PROMPTS = {
    "通用系列": "无需叠加特定材质 or 场景要求，请纯粹以最高标准的通用商业视觉法则进行严苛评审。",
    "BM-正装系列 (Dress Shoes)": "在此基础上，重点评审其经典英伦/商务感的呈现，苛求鞋头（Toe-cap）轮廓的锋利度、缝线细节的精致感，以及画面是否传达出‘职场精英’的稳重与高端质感。",
    "BM-乐福/休闲系列 (Loafers)": "在此基础上，重点评审‘Smart Casual’风格的平衡点，强调‘一脚蹬’的穿脱便利性视觉暗示、皮面或麂皮的柔软褶皱感，以及画面是否传达出松弛、优雅的意式度假或通勤氛围。",
    "BM-靴类系列 (Boots)": "在此基础上，重点评审切尔西或查卡靴的线条流线性、鞋跟的稳重感以及材质的硬朗度。画面需传达出一种现代都市与粗犷美学结合的‘男性气概’。",
    "BM-休闲运动系列 (Sneakers)": "在此基础上，重点评审轻量化设计（Lightweight）的视觉表达、鞋面材质的透气性细节，以及画面是否具备现代都市运动感，色彩搭配是否清爽自然。",
    "BM-居家/便鞋系列 (Slippers)": "在此基础上，聚焦极致的‘舒适包裹感’。重点评审内里材质（如仿毛、记忆棉）的质感展示，以及画面是否成功营造出温暖、私密的家庭松弛感氛围。"
}

# ==========================================
# 辅助函数：将纯文本排版并渲染为高质量 JPG 长图
# ==========================================
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
        font = ImageFont.truetype(font_path, 28)
        title_font = ImageFont.truetype(font_path, 42)
    except IOError:
        st.warning(f"⚠️ 未检测到 {font_path} 字体文件，图片中文可能无法正常显示。")
        font = ImageFont.load_default()
        title_font = font

    draw.text((margin_x, margin_y), "Bruno Marc A+ 方案深度评审报告", font=title_font, fill=(255, 204, 0))
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
st.set_page_config(page_title="BM 视觉专家评审台", layout="wide")
st.title("👞 BM Listing 方案一键评审")

st.sidebar.header("⚙️ 核心配置")

style_option = st.sidebar.selectbox(
    "选择品类", 
    list(EXPERT_PROMPTS.keys())
)

is_leather = st.sidebar.toggle("是否真皮", value=False, help="开启后，AI 将苛求皮革纹理、自然光泽，严打假皮塑料感。")

uploaded_file = st.file_uploader("请上传 A+ 页面拼图稿 (支持 JPG/PNG)", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, caption="当前待评审方案", use_container_width=True)

    if st.button("🚀 开始深度评审", type="primary"):
        with st.spinner("AI 视觉专家正在进行像素级分析，请稍候..."):
            try:
                expert_focus = EXPERT_PROMPTS[style_option]
                
                leather_rule = ""
                if is_leather:
                    leather_rule = "\n3. 【真皮材质附加审查】：作为高级皮具鉴定专家，重点苛求皮料纹理的真实感、皮面光泽的自然折射率、以及如何通过高级光影凸显皮革的昂贵与细腻质感，严厉批评任何呈现出‘廉价PU塑料反光’的修图失误。"
                
                system_prompt = f"""
                你是一个冷静、客观且具有批判性思维的资深商业视觉设计专家。你深谙 Bruno Marc (BM) 品牌的全球化审美：高性价比、经典复古、舒适科技与现代男士生活方式。
                
                【特别分析指令：端次优先级】
                请注意：用户上传的可能是一张拼图。你的评审重心必须绝对倾斜于 PC 端。对于手机端，除非存在影响阅读或认知的“重大错误”，否则直接忽视。
                
                【专家人设与 BM 品牌标准】
                当前评审系列为：【{style_option}】。
                作为 BM 的资深设计总监，你的评审必须遵循以下双重阶梯标准：
                
                1. 【BM 通用视觉标准 (底座)】：首先审查画面是否遵循“极简且有力”的排版，留白是否体现呼吸感；重点检查 BM 核心舒适技术（如 Cushioned Insole, Lightweight Sole）是否在视觉上有清晰表达。
                2. 【系列专属强化建议】：{expert_focus}{leather_rule}
                
                【输出要求】
                请严格按照以下 5 个模块输出：
                
                ### 1. 综合视觉定调
                （摒弃数字打分，直接用一句话点评整体视觉冲击力与品牌调性契合度）
                
                ### 2. 焦点路径与排版诊断
                （着重分析 PC 端主图与关联图的视觉引导、构图比例、光影处理是否达到了 BM 品牌要求的专业水准）
                
                ### 3. 卖点契合度与文案优化
                （评价画面传达的信息是否精准支撑了核心功能卖点；直接提供更具‘美式风格’、更具转化率的英语文案改写建议及中文释义）
                
                ### 4. 致命缺陷预警
                （一针见血地指出当前最容易导致‘显廉价’、‘假货感’或‘跳失率高’的致命设计缺陷）
                
                ### 5. 落地执行清单 (To-Do)
                （提炼出 3-5 条直接修改行动指令，作为设计师的执行标准）
                """

                # 核心配置：已切换为最新的 gemini-3.1-pro-preview
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3.1-pro-preview')
                response = model.generate_content([system_prompt, img])
                
                st.success("✅ 评审完成！")
                st.markdown("---")
                st.markdown(response.text)
                st.markdown("---")
                
                jpg_data = create_report_image(response.text, font_path="font.TTF")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 下载 TXT 报告", 
                        data=response.text, 
                        file_name="BM_Review_Report.txt"
                    )
                with col2:
                    st.download_button(
                        label="🖼️ 保存为 JPG 长图", 
                        data=jpg_data, 
                        file_name="BM_Review_Poster.jpg",
                        mime="image/jpeg"
                    )
                    
            except Exception as e:
                st.error(f"调用 AI 失败: {e}")
