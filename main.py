import streamlit as st
import m3u8
import requests
import os
import io
from urllib.parse import urljoin, unquote, urlparse
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Extract title from URL
def extract_title_from_url(url):
    path = urlparse(url).path
    filename = os.path.basename(path)
    return unquote(filename.replace(".m3u8", "").replace(" ", "_")) or f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Parse M3U8 Playlist
def parse_m3u8(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": url
        }
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

# Download segment
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

# Download video to memory
def download_m3u8_to_memory(m3u8_url, progress_callback=None):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": m3u8_url
        }
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
                i = futures[future]
                data = future.result()
                if data:
                    downloaded_data[i] = data
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        buffer = io.BytesIO()
        for seg_data in downloaded_data:
            if seg_data:
                buffer.write(seg_data)

        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Download error: {e}")
        return None

# Streamlit App
def main():
    st.set_page_config(page_title="M3U8 Video Downloader", layout="centered")
    st.title("📺 M3U8 Video Downloader")

    url = st.text_input("Paste M3U8 URL here:")

    if url:
        resolutions = parse_m3u8(url)
        if resolutions:
            resolution = st.selectbox("Choose resolution", list(resolutions.keys()))
            selected_url = resolutions[resolution]

            if st.button("Download Video"):
                title = extract_title_from_url(url)
                filename = f"{title}.mp4"  # TS format for in-browser download

                progress_bar = st.progress(0)
                status = st.empty()

                def update_progress(current, total):
                    percent = int((current / total) * 100)
                    progress_bar.progress(min(percent, 100))
                    status.text(f"Downloading... {current}/{total}")

                st.info("Downloading video to memory...")
                video_buffer = download_m3u8_to_memory(selected_url, update_progress)

                if video_buffer:
                    st.success("✅ Download ready.")
                    st.download_button("⬇️ Download Video", data=video_buffer, file_name=filename, mime="video/mp2t")

                    # Show file info
                    file_size = len(video_buffer.getvalue()) / (1024 * 1024)
                    st.subheader("📁 File Info")
                    st.markdown(f"**Filename:** `{filename}`")
                    st.markdown(f"**Size:** `{file_size:.2f} MB`")
                    st.markdown(f"**Date:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

if __name__ == "__main__":
    main()
