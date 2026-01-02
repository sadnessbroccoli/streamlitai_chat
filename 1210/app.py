import streamlit as st
import json
import pandas as pd
import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# 初始化 DeepSeek 客户端
def init_deepseek_client():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        st.error("⚠️ 未找到 DeepSeek API 密钥，请在 .env 文件中配置 DEEPSEEK_API_KEY")
        return None

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


# 页面配置
st.set_page_config(
    page_title="DeepSeek名人故事智能体",
    page_icon="🌟",
    layout="wide"
)

# 应用标题
st.title("🌟 DeepSeek名人故事智能体")
st.markdown("### AI驱动的名人故事探索与对话")


# 加载数据
@st.cache_data
def load_celebrities():
    try:
        # 1. 绝对路径定位：获取 app.py 所在的文件夹 (1210 文件夹)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. 拼接路径：指向 1210/data/celebrities.json
        file_path = os.path.join(current_dir, 'data', 'celebrities.json')
        
        # 调试用：如果读不到，在网页上打印出它尝试访问的路径
        if not os.path.exists(file_path):
            st.error(f"⚠️ 文件未找到！请检查 GitHub 路径。当前尝试访问: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 确保返回的是列表
        return data.get('celebrities', [])
        
    except Exception as e:
        st.error(f"❌ 加载出错: {str(e)}")
        return []

# 在调用 random.choice 之前，一定要加这个判断防止崩溃
celebrities = load_celebrities()
if not celebrities:
    st.warning("⚠️ 列表为空，正在等待数据加载...")
    st.stop()  # 停止执行后面的逻辑，直到数据加载成功

# 创建标签页
tab1, tab2, tab3 = st.tabs(["📚 名人探索", "💬 AI对话", "🎨 AI创作"])

with tab1:
    # 名人探索界面（保持原来的代码）
    st.subheader("🔍 搜索名人")

    # 搜索框
    search_query = st.text_input("输入关键词搜索", placeholder="如：科学家、物理、创新...")

    # 显示名人卡片
    if celebrities:
        filtered_celebrities = celebrities

        if search_query:
            filtered_celebrities = [
                c for c in filtered_celebrities
                if search_query.lower() in c.get('name', '').lower() or
                   search_query.lower() in c.get('category', '').lower() or
                   any(search_query.lower() in tag.lower() for tag in c.get('tags', []))
            ]

        cols = st.columns(3)
        for idx, celebrity in enumerate(filtered_celebrities[:9]):  # 最多显示9个
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {celebrity['name']}")
                    st.caption(f"🏷️ {celebrity['category']} | 📅 {celebrity['era']}")

                    # 简要介绍
                    with st.expander("📖 查看故事"):
                        st.write(celebrity['story'])

                        st.markdown("**主要成就:**")
                        for achievement in celebrity['key_achievements']:
                            st.markdown(f"✅ {achievement}")

                        st.markdown("**趣闻轶事:**")
                        for fact in celebrity['interesting_facts']:
                            st.markdown(f"✨ {fact}")

                        # 对话按钮
                        if st.button(f"与{celebrity['name']}对话", key=f"chat_{celebrity['id']}"):
                            st.session_state.selected_celebrity = celebrity
                            st.switch_page("pages/chat.py")
    else:
        st.warning("暂无名人数据")

with tab2:
    st.subheader("🤖 AI名人对话")

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "selected_celebrity" not in st.session_state:
        st.session_state.selected_celebrity = None

    # 选择要对话的名人
    col1, col2 = st.columns([2, 1])

    with col1:
        celebrity_names = ["请选择名人"] + [c["name"] for c in celebrities]
        selected_name = st.selectbox(
            "选择要对话的名人",
            celebrity_names
        )

        if selected_name != "请选择名人":
            st.session_state.selected_celebrity = next(
                (c for c in celebrities if c["name"] == selected_name),
                None
            )

    with col2:
        if st.button("🔄 开始新对话", type="primary"):
            st.session_state.messages = []
            st.rerun()

    # 显示选中的名人信息
    if st.session_state.selected_celebrity:
        celebrity = st.session_state.selected_celebrity

        with st.expander(f"👤 {celebrity['name']} 简介", expanded=False):
            st.write(celebrity['story'])
            st.markdown(f"**时代:** {celebrity['era']}")
            st.markdown(f"**国籍:** {celebrity['nationality']}")

        # 显示对话历史
        st.divider()
        st.subheader("💭 对话历史")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 用户输入
        if prompt := st.chat_input(f"向 {celebrity['name']} 提问..."):
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})

            # 显示用户消息
            with st.chat_message("user"):
                st.markdown(prompt)

            # 生成 AI 回复
            with st.chat_message("assistant"):
                with st.spinner(f"{celebrity['name']} 正在思考..."):
                    try:
                        # 获取 DeepSeek 客户端
                        client = init_deepseek_client()

                        if client:
                            # 构建系统提示
                            system_prompt = f"""你正在扮演 {celebrity['name']}，请以第一人称回答。

                            背景信息：
                            - 身份：{celebrity['category']}
                            - 时代：{celebrity['era']}
                            - 国籍：{celebrity['nationality']}
                            - 主要成就：{', '.join(celebrity['key_achievements'])}
                            - 生平：{celebrity['story']}

                            要求：
                            1. 使用第一人称（我）
                            2. 保持角色性格和时代背景
                            3. 回答要生动有趣
                            4. 可以适当发挥但不要脱离事实
                            5. 语言风格要符合人物特点
                            """

                            # 构建消息
                            messages = [
                                {"role": "system", "content": system_prompt}
                            ]

                            # 添加对话历史（限制最近10条）
                            recent_messages = st.session_state.messages[-10:] if len(
                                st.session_state.messages) > 10 else st.session_state.messages
                            for msg in recent_messages:
                                messages.append(msg)

                            # 调用 API
                            response = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=messages,
                                stream=True,
                                temperature=0.7,
                                max_tokens=500
                            )

                            # 流式显示回复
                            response_text = ""
                            placeholder = st.empty()
                            for chunk in response:
                                if chunk.choices[0].delta.content:
                                    response_text += chunk.choices[0].delta.content
                                    placeholder.markdown(response_text + "▌")

                            placeholder.markdown(response_text)

                            # 添加到会话历史
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response_text
                            })
                        else:
                            st.error("无法连接 DeepSeek API，请检查配置")

                    except Exception as e:
                        st.error(f"生成回复失败: {str(e)}")
                        # 提供备用回复
                        backup_responses = [
                            f"作为{celebrity['name']}，我很乐意回答你的问题。关于{prompt}，我的看法是...",
                            f"这个问题很有趣！在我那个时代，情况是这样的...",
                            f"让我想想怎么回答这个问题。根据我的经验...",
                        ]
                        import random

                        backup_response = random.choice(backup_responses)
                        st.markdown(backup_response)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": backup_response
                        })
    else:
        st.info("👈 请在左侧选择一个名人开始对话")

with tab3:
    st.subheader("🎨 AI创作名人故事")

    col1, col2 = st.columns(2)

    with col1:
        # 创作参数
        story_type = st.selectbox(
            "故事类型",
            ["励志故事", "趣闻轶事", "专业成就", "情感故事", "历史时刻"]
        )

        story_length = st.slider("故事长度", 100, 1000, 300, step=50)

        target_audience = st.multiselect(
            "目标受众",
            ["儿童", "青少年", "成年人", "学生", "研究者"],
            default=["成年人"]
        )

    with col2:
        # 名人选择
        selected_for_story = st.selectbox(
            "选择名人",
            ["随机选择"] + [c["name"] for c in celebrities]
        )

        custom_prompt = st.text_area(
            "自定义要求（可选）",
            placeholder="例如：突出他的创新精神，语言生动有趣..."
        )

    if st.button("✨ 生成故事", type="primary"):
        if selected_for_story == "随机选择":
            import random

            celebrity = random.choice(celebrities)
        else:
            celebrity = next((c for c in celebrities if c["name"] == selected_for_story), None)

        if celebrity:
            with st.spinner("AI正在创作中..."):
                try:
                    client = init_deepseek_client()

                    if client:
                        # 构建创作提示
                        creative_prompt = f"""请创作一个关于 {celebrity['name']} 的{story_type}。

                        基本信息：
                        - 身份：{celebrity['category']}
                        - 时代：{celebrity['era']}
                        - 成就：{', '.join(celebrity['key_achievements'])}

                        要求：
                        1. 故事类型：{story_type}
                        2. 目标受众：{', '.join(target_audience)}
                        3. 长度：约{story_length}字
                        4. 语言生动有趣
                        5. 基于事实但可以合理发挥

                        {f"额外要求：{custom_prompt}" if custom_prompt else ""}

                        请开始创作：
                        """

                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": creative_prompt}],
                            temperature=0.8,
                            max_tokens=story_length * 2
                        )

                        story = response.choices[0].message.content

                        # 显示结果
                        st.success("✅ 故事创作完成！")
                        st.markdown("---")
                        st.markdown(f"### 📖 {celebrity['name']}的{story_type}")
                        st.markdown(story)

                        # 提供下载
                        import datetime

                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{celebrity['name']}_{story_type}_{timestamp}.txt"

                        st.download_button(
                            label="📥 下载故事",
                            data=story,
                            file_name=filename,
                            mime="text/plain"
                        )
                    else:
                        st.error("无法连接 DeepSeek API")

                except Exception as e:
                    st.error(f"创作失败: {str(e)}")

# 侧边栏信息
with st.sidebar:
    st.header("⚙️ 配置")

    # API 状态
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        st.success("✅ DeepSeek API 已配置")
        st.caption(f"密钥：{api_key[:10]}...{api_key[-4:]}")
    else:
        st.error("❌ DeepSeek API 未配置")
        st.info("请在 .env 文件中添加：DEEPSEEK_API_KEY=你的密钥")

    st.divider()

    # 数据统计
    st.subheader("📊 统计信息")
    st.metric("名人数量", len(celebrities))

    categories = {}
    for c in celebrities:
        cat = c.get('category', '未知')
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in categories.items():
        st.metric(cat, count)

    st.divider()

    # 快速操作
    st.subheader("🚀 快速操作")

    if st.button("随机对话"):
        import random

        random_celebrity = random.choice(celebrities)
        st.session_state.selected_celebrity = random_celebrity
        st.rerun()

    if st.button("清空对话"):
        if "messages" in st.session_state:
            st.session_state.messages = []
        st.rerun()