document.addEventListener('DOMContentLoaded', () => {
    const pingButton = document.getElementById('ping-button');
    const outputContainer = document.getElementById('output-container');

    console.log('DOM fully loaded and parsed. Initializing script.');
    console.log('Ping Button:', pingButton);
    console.log('Output Container:', outputContainer);

    if (!pingButton || !outputContainer) {
        console.error('Required DOM elements not found!');
        return;
    }

    pingButton.addEventListener('click', async () => {
        console.log('Ping button clicked!');
        pingButton.disabled = true;
        outputContainer.textContent = '正在启动命令...';

        try {
            console.log('Sending POST request to /commands/start...');
            // 1. 发送请求启动命令
            const response = await fetch('http://localhost:8000/commands/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: 'ping 8.8.8.8 -c 5' })
            });

            console.log('Received response from /commands/start:', response);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const executionId = data.executionId;
            outputContainer.textContent = `命令已启动，Execution ID: ${executionId}\n正在连接 WebSocket...\n\n`;
            console.log('Command started, executionId:', executionId);

            // 2. 连接 WebSocket
            console.log('Connecting to WebSocket:', `ws://localhost:8000/commands/${executionId}/stream`);
            const ws = new WebSocket(`ws://localhost:8000/commands/${executionId}/stream`);

            ws.onopen = () => {
                console.log('WebSocket 连接已建立');
            };

            ws.onmessage = (event) => {
                // 3. 接收并显示流式输出
                outputContainer.textContent += event.data;
            };

            ws.onclose = () => {
                console.log('WebSocket 连接已关闭');
                pingButton.disabled = false;
            };

            ws.onerror = (error) => {
                console.error('WebSocket 错误:', error);
                outputContainer.textContent += '\n\nWebSocket 连接出错，请检查控制台。';
                pingButton.disabled = false;
            };

        } catch (error) {
            console.error('请求失败:', error);
            outputContainer.textContent = `请求失败: ${error.message}`;
            pingButton.disabled = false;
        }
    });
});