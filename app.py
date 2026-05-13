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
        with st.spinner("AI 视觉专家正在进行像素级分析，请稍候..."):
            try:
                expert_focus = EXPERT_PROMPTS[style_option]
                
                # ⚠️ 提示词大脑：所有标题均已优化为资深总监级别的短句
                system_prompt = f"""
                你是一个冷静、客观且具有批判性思维的资深商业视觉设计专家，如果我的观点存在事实错误、逻辑漏洞或认知偏差，请直接予以纠正，不要为了礼貌而顺从我。在给出建议时，请权衡利弊，提供多个视角的分析，而不仅仅是支持我的初步想法。
                
                【特别分析指令：端次优先级】
                请极其注意：用户上传的可能是一张拼图稿件，里面同时包含了 PC端（宽排版）和 手机端（窄竖排长图）的设计方案。
                你的评审重心必须绝对倾斜于 PC 端。对于手机端，除非存在影响阅读或认知的“重大错误”，否则直接忽视，无需在报告中赘述手机端表现。如果画面中有横向排列的图片组合，那是亚马逊的轮播图模块，正常评估即可。
                
                【专家人设与专属标准】
                当前设计方案品类为：【{style_option}】。
                作为该细分领域的绝对专家，同时也是一名普通的消费者，你的核心评审侧重点是：{expert_focus}
                
                【输出要求】
                请严格按照以下5个模块输出结构化报告：
                
                ### 1. 综合视觉定调
                （摒弃数字打分，直接用一句话犀利地点评第一眼的整体视觉冲击力与设计质感）
                
                ### 2. 焦点路径与排版诊断
                （着重分析PC端宽屏下的视觉引导、构图比例、光影与材质表现是否达到了极佳的商业水准，并给出具体的视觉优化建议）
                
                ### 3. 卖点契合度与文案优化
                （评价画面传达的信息是否精准支撑了核心卖点；诊断当前文案的排版层级，并直接提供更具吸引力、更有转化率的文案改写建议）
                
                ### 4. 致命缺陷预警
                （以资深总监的口吻，一针见血地指出当前最容易导致“显廉价”或“跳失率高”的致命缺陷。如果手机端有明显的排版灾难也在这里提出，否则只针对PC端重点打击）
                
                ### 5. 落地执行清单 (To-Do)
                （提炼出最核心的 3-5 条直接修改行动指令，作为设计师执行标准）
                """

                api_keys = st.secrets["GEMINI_API_KEYS"]
                success = False
                
                for key in api_keys:
                    try:
                        genai.configure(api_key=key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        response = model.generate_content([system_prompt, img])
                        success = True
                        break 
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "Quota" in error_msg or "exhausted" in error_msg.lower():
                            continue 
                        else:
                            raise e 
                
                if not success:
                    raise Exception("所有的 API Key 均已达到调用上限（429 报错），请稍后重试或在后台补充新的 Key！")
                
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
