"use client";

import { useEffect, useRef } from 'react';
import { Terminal as XtermTerminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';

interface TerminalProps {
  executionId: string;
}

export default function Terminal({ executionId }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xterm = useRef<XtermTerminal | null>(null);

  useEffect(() => {
    if (terminalRef.current && !xterm.current) {
      xterm.current = new XtermTerminal();
      xterm.current.open(terminalRef.current);
    }

    const ws = new WebSocket(`ws://localhost:8000/commands/${executionId}/stream`);

    ws.onmessage = (event) => {
      if (xterm.current) {
        if(event.data === '\n[EOF]') {
          xterm.current.writeln('\n\n--- Command finished ---');
          ws.close();
        } else {
          xterm.current.write(event.data);
        }
      }
    };

    return () => {
      ws.close();
      if (xterm.current) {
        xterm.current.dispose();
        xterm.current = null;
      }
    };
  }, [executionId]);

  const stopCommand = async () => {
    await fetch(`http://localhost:8000/commands/${executionId}/stop`, {
      method: 'POST',
    });
  };

  return (
    <div>
      <button
        onClick={stopCommand}
        className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded mb-2"
      >
        Stop
      </button>
      <div ref={terminalRef} />
    </div>
  );
}
