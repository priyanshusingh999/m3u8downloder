import streamlit as st
import m3u8
import requests
import os
from urllib.parse import urljoin, unquote, urlparse
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit.components.v1 import html

# Constants
DOWNLOAD_DIR = "downloads"
Path(DOWNLOAD_DIR).mkdir(exist_ok=True)

def extract_title_from_url(url):
    path = urlparse(url).path
    filename = os.path.basename(path)
    return unquote(filename.replace(".m3u8", "").replace(" ", "_")) or f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def parse_m3u8(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": url}
        m3u8_obj = m3u8.load(uri=url, headers=headers)
        if m3u8_obj.playlists:
            resolutions = {}
            for playlist in m3u8_obj.playlists:
                res = playlist.stream_info.resolution
                resolution = f"{res[0]}x{res[1]}"
                resolutions[resolution] = urljoin(url, playlist.uri)
            return resolutions
        else:
            return {"default": url}
    except Exception as e:
        st.error(f"Failed to parse M3U8: {e}")
        return {}

def download_segment(segment_url, headers, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(segment_url, headers=headers, timeout=10)
            r.raise_for_status()
            return r.content
        except Exception:
            if attempt < retries - 1:
                continue
            else:
                return None

def download_m3u8_multithreaded(m3u8_url, ts_path, progress_callback=None):
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": m3u8_url}
        m3u8_obj = m3u8.load(uri=m3u8_url, headers=headers)
        base_uri = m3u8_url.rsplit('/', 1)[0] + "/"
        segments = m3u8_obj.segments
        total = len(segments)
        downloaded_data = [None] * total

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(download_segment, urljoin(base_uri, seg.uri), headers): i
                for i, seg in enumerate(segments)
            }

            completed = 0
            for future in as_completed(futures):
                if st.session_state.get("cancel_download"):
                    return None
                i = futures[future]
                data = future.result()
                if data:
                    downloaded_data[i] = data
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        with open(ts_path, "wb") as f:
            for seg_data in downloaded_data:
                if seg_data:
                    f.write(seg_data)

        return ts_path
    except Exception as e:
        st.error(f"Download error: {e}")
        return None

def main():
    st.set_page_config(page_title="M3U8 Video Downloader", layout="centered")
    st.title("📺 M3U8 Video Downloader")

    if "cancel_download" not in st.session_state:
        st.session_state.cancel_download = False

    url = st.text_input("Paste M3U8 URL here:")

    if url:
        resolutions = parse_m3u8(url)
        if resolutions:
            resolution = st.selectbox("Choose resolution", list(resolutions.keys()))
            selected_url = resolutions[resolution]

            col1, col2 = st.columns([1, 1])
            download_clicked = col1.button("⬇️ Download Video")
            cancel_clicked = col2.button("❌ Cancel Download")

            if cancel_clicked:
                st.session_state.cancel_download = True
                st.warning("Download cancelled.")

            if download_clicked:
                st.session_state.cancel_download = False
                title = extract_title_from_url(url)
                ts_name = f"{title}.mp4"
                ts_path = os.path.join(DOWNLOAD_DIR, ts_name)

                progress_bar = st.progress(0)
                status = st.empty()

                def update_progress(current, total):
                    percent = int((current / total) * 100)
                    progress_bar.progress(min(percent, 100))
                    status.text(f"Downloading... {current}/{total}")

                st.info("Starting download...")
                ts_result = download_m3u8_multithreaded(selected_url, ts_path, update_progress)

                if ts_result:
                    st.success("✅ Download complete.")
                    with open(ts_result, "rb") as f:
                        video_bytes = f.read()

                    st.download_button(
                        label="⬇️ Manual Download",
                        data=video_bytes,
                        file_name=ts_name,
                        mime="video/mp4"
                    )

                    file_size = os.path.getsize(ts_result) / (1024 * 1024)
                    st.subheader("📁 File Info")
                    st.markdown(f"**Filename:** `{ts_name}`")
                    st.markdown(f"**Size:** `{file_size:.2f} MB`")
                    st.markdown(f"**Date:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
                elif st.session_state.cancel_download:
                    st.info("Download was cancelled by user.")

    # Ads in footer
    footer_ads = """
    <style>
      .ad-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background: #fff;
        border-top: 1px solid #ccc;
        padding: 10px 0;
        text-align: center;
        z-index: 9999;
      }
      .ad-slider {
        display: inline-block;
        width: 300px;
        height: 250px;
        overflow: hidden;
        position: relative;
      }
      .ad-slide {
        position: absolute;
        width: 100%;
        height: 100%;
        transition: opacity 1s ease-in-out;
        opacity: 0;
      }
      .ad-slide.active {
        opacity: 1;
      }
    </style>

    <div class="ad-footer">
      <div class="ad-slider">
        <!-- Ad 1 -->
        <div class="ad-slide active">
          <script async="async" data-cfasync="false" src="//pl26589582.profitableratecpm.com/b4cc063169b5ae7158931d87d09b2e9c/invoke.js"></script>
          <div id="container-b4cc063169b5ae7158931d87d09b2e9c" style="width: 300px; height: 250px;"></div>
        </div>
        
        <!-- Ad 2 -->
        <div class="ad-slide">
          <script type="text/javascript">
            atOptions = {
              'key' : '8c7155ca9199bcc38833ea34a30713b0',
              'format' : 'iframe',
              'height' : 250,
              'width' : 300,
              'params' : {}
            };
          </script>
          <script type="text/javascript" src="//www.highperformanceformat.com/8c7155ca9199bcc38833ea34a30713b0/invoke.js"></script>
        </div>
      </div>
    </div>

    <script>
      let slides = document.querySelectorAll('.ad-slide');
      let currentIndex = 0;
      setInterval(() => {
        slides[currentIndex].classList.remove('active');
        currentIndex = (currentIndex + 1) % slides.length;
        slides[currentIndex].classList.add('active');
      }, 5000);
    </script>
    """

    html(footer_ads, height=300)

if __name__ == "__main__":
    main()



