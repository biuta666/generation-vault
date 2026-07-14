"""
Generation Vault Launcher — 静默启动，自动打开浏览器
"""
import os, sys, subprocess, webbrowser, time, socket, threading

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0)); return s.getsockname()[1]

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = find_free_port()
    url = f"http://localhost:{port}"
    
    # 2秒后开浏览器
    threading.Thread(target=lambda: (time.sleep(2), webbrowser.open(url)), daemon=True).start()
    
    # 启动Streamlit（无头模式，不显示任何调试信息）
    sys.argv = ["streamlit", "run", "src/ui/app.py",
                "--server.port", str(port),
                "--server.headless", "true",
                "--server.enableCORS", "false",
                "--browser.gatherUsageStats", "false",
                "--client.toolbarMode", "minimal",
                "--logger.level", "error"]
    
    from streamlit.web import cli as stcli
    sys.exit(stcli.main())
