import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 页面整体布局设置
st.set_page_config(page_title="视觉设计专家评审台", layout="wide")
st.title("👁️ Listing 方案一键评审台")

# 2. 左侧边栏：配置参数
st.sidebar.header("⚙️ 核心配置")

# 针对您可能的高级视觉产出，设置了精细化的评审预设
style_option = st.sidebar.selectbox(
    "2. 选择当前设计方案的主题风格", 
    [
        "BM 通用", 
        "BM 真皮"
    ]
)

# 3. 主界面：上传与预览区
uploaded_file = st.file_uploader("请拖拽上传您的 A+ 页面或视觉方案 (支持 JPG/PNG)", type=['jpg', 'jpeg', 'png'])

 if uploaded_file is not None:
    img = Image.open(uploaded_file)
    st.image(img, caption="当前待评审方案", use_container_width=True)

    # 4. 触发评审逻辑
   if st.button("🚀 开始深度评审", type="primary"):
     with st.spinner("AI 视觉专家正在进行像素级分析，请稍候..."):
         try:
             # 核心修改：让代码从 Streamlit 的云端保险箱里读取密钥
             api_key = st.secrets["GEMINI_API_KEY"]
             genai.configure(api_key=api_key)
                    # 调用目前最强大的多模态模型
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    system_prompt = f"""
                    你是一个冷静、客观且具有批判性思维的资深商业视觉设计专家。
                    当前用户提交的设计稿属于方案阶段。
                    画面中出现的鞋子为参考样鞋，后期会替换成我们的产品。
                    请以挑剔的普通消费者和专业美术指导的双重视角，对这张商业摄影/设计图进行严苛评审。
                    以此来判断这套方案是否足够吸引你，以及还有哪些优化空间
                    
                    请严格按照以下结构输出报告：
                    ### 1. 综合视觉评分（0-100分）
                    （给出分数，并一针见血地简述第一印象带来的视觉冲击力）
                    
                    ### 2. 视觉焦点热力分析
                    （消费者第一眼会注意到的要素，例如画面的景深、材质细节、光线折射是否达到了商业级水准）
                    
                    ### 3. 卖点与画面匹配度
                    （画面传达的氛围和信息，是否精准支撑了该类产品的核心卖点）
                    
                    ### 4. 核心优化行动清单 (To-Do List)
                    （指出明显的逻辑漏洞、构图缺陷或认知偏差，提供至少 3 条直接具体的修改建议）
                    """
                    
                    response = model.generate_content([system_prompt, img])
                    
                    # 5. 展示结果与下载功能
                    st.success("✅ 评审完成！")
                    st.markdown("---")
                    st.markdown(response.text)
                    st.markdown("---")
                    
                    st.download_button(
                        label="📥 一键下载评审报告 (TXT)", 
                        data=response.text, 
                        file_name="Listing_AI_Review_Report.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"调用 AI 失败，请检查网络或 API Key。错误信息: {e}")
