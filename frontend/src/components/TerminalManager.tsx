"use client";

import { useState } from 'react';
import Terminal from './Terminal';

interface Tab {
  id: string;
  title: string;
}

export default function TerminalManager() {
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [activeTab, setActiveTab] = useState<string>('');
  const [command, setCommand] = useState('');

  const addTab = async () => {
    const response = await fetch('http://localhost:8000/commands/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ command }),
    });

    if (response.ok) {
      const { executionId } = await response.json();
      const newTab: Tab = { id: executionId, title: command };
      setTabs([...tabs, newTab]);
      setActiveTab(executionId);
      setCommand('');
    } else {
      console.error('Failed to start command');
    }
  };

  const closeTab = (id: string) => {
    setTabs(tabs.filter(tab => tab.id !== id));
    if (activeTab === id) {
      setActiveTab(tabs.length > 1 ? tabs[0].id : '');
    }
  };

  return (
    <div className="w-full h-screen bg-gray-800 text-white p-4">
      <div className="flex items-center mb-4">
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          className="bg-gray-700 text-white p-2 rounded-l w-full"
          placeholder="Enter command"
        />
        <button
          onClick={addTab}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-r"
        >
          Run
        </button>
      </div>
      <div className="flex border-b border-gray-700">
        {tabs.map(tab => (
          <div
            key={tab.id}
            className={`px-4 py-2 cursor-pointer ${activeTab === tab.id ? 'bg-gray-700' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.title}
            <button
              onClick={() => closeTab(tab.id)}
              className="ml-2 text-red-500"
            >
              x
            </button>
          </div>
        ))}
      </div>
      <div className="mt-4">
        {tabs.map(tab => (
          <div key={tab.id} className={`${activeTab === tab.id ? '' : 'hidden'}`}>
            <Terminal executionId={tab.id} />
          </div>
        ))}
      </div>
    </div>
  );
}
