
import fastapi
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi.staticfiles import StaticFiles

app = fastapi.FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>CLI 代理服务测试</title>
    <style>
        body { font-family: sans-serif; margin: 2em; background-color: #f4f4f9; color: #333; }
        h1 { color: #0056b3; }
        #ping-button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        #ping-button:hover { background-color: #0056b3; }
        #ping-button:disabled { background-color: #cccccc; cursor: not-allowed; }
        #output-container {
            margin-top: 20px;
            padding: 15px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #fff;
            min-height: 200px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: monospace;
            background-color: #282c34;
            color: #abb2bf;
        }
    </style>
</head>
<body>
    <h1>CLI 代理服务 - Ping 测试</h1>
    <button id="ping-button">开始 Ping 测试 (ping 8.8.8.8 -c 5)</button>
    <div id="output-container">点击按钮开始测试...</div>

    <script src="/static/script.js"></script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTML_CONTENT

if __name__ == "__main__":
    print("测试应用已启动，请在浏览器中打开 http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
