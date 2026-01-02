import streamlit as st
from openai import OpenAI
import os

st.set_page_config(
    page_title="深度对话",
    page_icon="💬",
    layout="wide"
)

st.title("💬 深度对话模式")

# 检查是否有选中的名人
if "selected_celebrity" not in st.session_state or not st.session_state.selected_celebrity:
    st.warning("请先从主页选择一位名人")
    if st.button("返回主页"):
        st.switch_page("app.py")
    st.stop()

celebrity = st.session_state.selected_celebrity

# 显示名人信息
col1, col2 = st.columns([3, 1])
with col1:
    st.header(f"与 {celebrity['name']} 对话")
with col2:
    if st.button("返回主页"):
        st.switch_page("app.py")

# 初始化对话历史
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": f"你好！我是{celebrity['name']}。你可以问我任何问题！"}
    ]

# 显示对话历史
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input(f"向{celebrity['name']}提问..."):
    # 添加用户消息
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)

    # 生成回复
    with st.chat_message("assistant"):
        with st.spinner(f"{celebrity['name']}正在思考..."):
            try:
                # 初始化 OpenAI 客户端
                api_key = os.getenv("DEEPSEEK_API_KEY")
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )

                # 构建系统提示
                system_prompt = f"""你是{celebrity['name']}，请以第一人称回答。
                背景：{celebrity['story']}
                成就：{', '.join(celebrity['key_achievements'])}
                性格特点：{', '.join(celebrity['interesting_facts'])}
                """

                messages = [{"role": "system", "content": system_prompt}]
                messages.extend(st.session_state.chat_history[-10:])  # 最近10条历史

                # 调用 API
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    stream=True,
                    temperature=0.7
                )

                # 流式显示
                response_text = ""
                placeholder = st.empty()
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        response_text += chunk.choices[0].delta.content
                        placeholder.markdown(response_text + "▌")

                placeholder.markdown(response_text)

                # 添加到历史
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text
                })

            except Exception as e:
                st.error(f"API调用失败: {str(e)}")
                import random

                fallback_responses = [
                    f"作为{celebrity['name']}，我对这个问题的看法是...",
                    f"在我那个时代，我们是这样看待这个问题的...",
                    f"这个问题很有意思！让我分享一下我的经历..."
                ]
                fallback = random.choice(fallback_responses)
                st.markdown(fallback)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": fallback
                })

# 侧边栏控制
with st.sidebar:
    st.header("对话控制")

    if st.button("🔄 重新开始对话"):
        st.session_state.chat_history = [
            {"role": "assistant", "content": f"你好！我是{celebrity['name']}。你可以问我任何问题！"}
        ]
        st.rerun()

    if st.button("💾 导出对话"):
        # 创建对话文本
        dialog_text = f"与 {celebrity['name']} 的对话记录\n"
        dialog_text += "=" * 50 + "\n\n"

        for msg in st.session_state.chat_history:
            role = "用户" if msg["role"] == "user" else celebrity['name']
            dialog_text += f"{role}：{msg['content']}\n\n"

        # 提供下载
        st.download_button(
            label="📥 下载对话记录",
            data=dialog_text,
            file_name=f"{celebrity['name']}_对话记录.txt",
            mime="text/plain"
        )