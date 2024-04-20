import asyncio
import streamlit as st
from datetime import datetime

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .time {
        font-size: 130px !important;
        font-weight: 700 !important;
        color: #ec5953 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

async def watch(test):
    while True:
        test.markdown(
            f"""
            <p class="time">
                {str(datetime.now())}
            </p>
            """, unsafe_allow_html=True)
        await asyncio.sleep(1)

test = st.empty()

if st.button("Click me."):
    st.image("https://cdn11.bigcommerce.com/s-7va6f0fjxr/images/stencil/1280x1280/products/40655/56894/Jdm-Decals-Like-A-Boss-Meme-Jdm-Decal-Sticker-Vinyl-Decal-Sticker__31547.1506197439.jpg?c=2", width=200)

asyncio.run(watch(test))
st.markdown("Done!")