import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import time

# ==========================================
# 专家知识库：款式与场所的交叉商业逻辑 (已增加中英对照)
# ==========================================
SHOE_STYLES = {
    "牛津鞋 (Oxfords)": "评审重点：作为最经典的鞋款，需平衡正式感与现代感。关注鞋楦线条的流畅度、布洛克雕花的视觉排布，以及在不同场所下的‘体面感’表达。",
    "休闲运动鞋 (Sneakers)": "评审重点：强调轻盈、科技与都市动感。关注大底材质的视觉表达、鞋面网格的透气感展示，以及整体画面的活力氛围。",
    "正装鞋 (Dress Shoes)": "评审重点：纯正商务属性。关注皮面反光的处理策划、缝线的严谨度，以及画面是否传达出绝对的专业与稳重。",
    "乐福鞋 (Loafers)": "评审重点：松弛感与便利性。关注穿脱开口的舒适暗示、材质的柔韧度表达，以及半休闲状态下的优雅调性。",
    "靴类 (Boots)": "评审重点：轮廓美学与材质层次。关注鞋帮高度带来的保护感暗示、粗犷与精致的视觉冲突，以及硬朗的线条表达。",
    "一脚蹬/便鞋 (Slip-ons)": "评审重点：极致便利与日常舒适。关注弹力带/开口的细节、内里柔软度的视觉呈现，以及居家或通勤的亲和力。"
}

OCCASIONS = {
    "日常百搭 (Daily Essentials)": "视觉基调：亲切、高频、实穿。背景应具有生活气息，光影应自然均匀，文案应强调耐穿与百搭。",
    "商务职场 (Business-Ready)": "视觉基调：权威、精干、专业。背景应简洁有力（如现代办公建筑），冷色调为主，文案应强调职场身份与品质感。",
    "休闲度假 (Casual & Leisure)": "视觉基调：松弛、自由、柔和。背景应具户外或咖啡馆气息，光线温润，文案应强调心情的释放与脚感的舒适。",
    "特殊/正式场合 (Special Occasions)": "视觉基调：奢华、尊贵、戏剧性。背景应具高级感（如宴会大厅或暗调影棚），光影对比度高，强调独特性与社交溢价。"
}

# ==========================================
# 辅助函数：生成 JPG 报告
# ==========================================
def create_report_image(text, font_path="font.TTF"):
    img_width = 1200
    margin_x = 80
    margin_y = 80
    lines = []
    for paragraph in text.split('\n'):
        wrapped = textwrap.wrap(paragraph, width=38) 
        if not wrapped: lines.append("")
        else: lines.extend(wrapped)
    line_height = 46
    img_height = max(1000, len(lines) * line_height + 300)
    img = Image.new('RGB', (img_width, img_height), color=(24, 24, 28))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, 28)
        title_font = ImageFont.truetype(font_path, 42)
    except IOError:
        font = ImageFont.load_default()
        title_font = font
    draw.text((margin_x, margin_y), "BM Listing 方案深度评审报告", font=title_font, fill=(255, 204, 0))
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
# 主界面
# ==========================================
st.set_page_config(page_title="BM 视觉专家评审系统", layout="wide")
st.title("👞 BM Listing 方案一键评审")

# 侧边栏配置
st.sidebar.header("⚙️ 评审参数配置")
shoe_val = st.sidebar.selectbox("1. 选择鞋子款式 (Shoes)", list(SHOE_STYLES.keys()))
occ_val = st.sidebar.selectbox("2. 选择适用场所 (Occasions)", list(OCCASIONS.keys()))
is_leather = st.sidebar.toggle("3. 是否包含真皮材质", value=False)

uploaded_file = st.file_uploader("请上传方案拼图稿 (支持预览图/设计方案稿)", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    # 图片物理提速压缩
    img.thumbnail((1024, 1024))
    st.image(img, caption="当前待评审方案", use_container_width=True)

    if st.button("🚀 开始专家级深度评审", type="primary"):
        # 实时进度条系统
        progress_container = st.empty()
        status_container = st.status("正在初始化评审引擎...", expanded=True)
        
        with status_container:
            st.write("🔍 正在载入款式与场所专家知识库...")
            time.sleep(0.5)
            st.write("🧠 正在激活‘视觉总监’与‘消费者’双重人格...")
            time.sleep(0.5)
            st.write("💎 正在生成特定材质审查逻辑...")
            time.sleep(0.5)
            
            try:
                # 动态构建材质逻辑（方案稿导向）
                leather_prompt = ""
                if is_leather:
                    leather_prompt = "\n【真皮方案专项审查】：由于该款为真皮，方案需体现‘真皮体感’。重点评审：光影策划是否预留了表现皮革纹理的空间？背景与道具是否匹配真皮的高级感？是否成功营造出昂贵材质的视觉叙事，而不仅仅是展示一张图。"

                # 核心提示词
                system_prompt = f"""
                你是一名拥有15年经验的【资深商业视觉总监】，同时也是一名【极度挑剔的普通消费者】。
                你现在评审的是 Bruno Marc (BM) 品牌的亚马逊 A+ 设计方案稿。
                
                【评审上下文】
                - 款式：{shoe_val} ({SHOE_STYLES[shoe_val]})
                - 场所：{occ_val} ({OCCASIONS[occ_val]})
                - 材质：{'真皮' if is_leather else '常规材质'}{leather_prompt}

                【双重身份准则】
                1. 视觉专家：关注构图平衡、视觉动线、排版空间、光影逻辑、品牌调性。
                2. 普通消费者：关注‘我是否被吸引？’、‘卖点我读懂了吗？’、‘这双鞋看起来值得买吗？’。

                【输出要求：严格按以下5模块】
                
                ### 1. 综合视觉定调
                （综合总监视角与消费者第一感官，一句话点评方案的商业冲击力与场所契合度。）
                
                ### 2. 焦点路径与构图诊断
                （着重分析 PC 端。视觉动线是否顺畅？主体与细节比例是否合理？是否为后续修图预留了表现材质（尤其是{shoe_val}特征）的光影空间？）
                
                ### 3. 卖点表达与文案空间匹配
                （第一步：审查画面视觉是否传达出了文案所写的卖点，若没有，请指出视觉上的缺失。
                第二步：针对缺失点提供具体的视觉修改建议。
                第三步：看文案是否有更具转化的表达，**必须注意**：新文案的字符长度必须与当前画面的排版空间完美匹配，严禁建议过长文案。）
                
                ### 4. 致命缺陷预警
                （指出当前方案中可能导致‘显廉价’、‘信息混乱’或‘跳失’的设计瑕疵。若手机端有重大排版灾难，请一并指出。）
                
                ### 5. 落地执行清单 (To-Do List)
                （提供 3-5 条清晰的行动指令，作为设计师下一步修改的硬性指标。）
                """

                st.write("🚀 正在将像素信息发送至极速 AI 预览服务器...")
                
                # 调用模型（您可根据您的极速 API 配置自由保留 gemini-2.5-flash 或预览版）
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash') 
                
                response = model.generate_content([system_prompt, img])
                
                st.write("📊 正在渲染高质量评审长图...")
                jpg_data = create_report_image(response.text, font_path="font.TTF")
                
                status_container.update(label="✅ 评审任务已圆满完成！", state="complete", expanded=False)

                # 展示结果
                st.success("专家报告已生成：")
                st.markdown(response.text)
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(label="📥 下载 TXT 报告", data=response.text, file_name=f"BM_Review_Report.txt")
                with col2:
                    st.download_button(label="🖼️ 保存为 JPG 长图海报", data=jpg_data, file_name=f"BM_Review_Poster.jpg", mime="image/jpeg")
                    
            except Exception as e:
                status_container.update(label="❌ 评审中断", state="error")
                st.error(f"调用 AI 失败: {e}")
