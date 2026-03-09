import { useState } from 'react';
import { CommandCenter } from './CommandCenter';
import { TraceWaterfall } from './TraceWaterfall';
import { LiveInspector } from './LiveInspector';
import { NodeEvent } from './types';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
    const [events, setEvents] = useState<NodeEvent[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [selectedEventIndex, setSelectedEventIndex] = useState<number | null>(null);

    const startStream = async (endpoint: string, options: RequestInit) => {
        if (isProcessing) return;
        setEvents([]);
        setSelectedEventIndex(null);
        setIsProcessing(true);

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, options);
            if (!response.ok) throw new Error("Failed to start job");
            if (!response.body) throw new Error("No readable stream");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Process lines
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.replace('data: ', '').trim();
                            if (!jsonStr) continue;
                            const packet = JSON.parse(jsonStr) as NodeEvent;

                            setEvents(prev => [...prev, packet]);
                        } catch (err) {
                            console.error("Failed to parse SSE", err);
                        }
                    }
                }
            }
        } catch (err) {
            console.error("Stream reading failed", err);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleStartJob = (prompt: string) => {
        startStream('/start_job', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
    };

    const handleUploadPDF = (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        startStream('/ingest_pdf', {
            method: 'POST',
            body: formData
        });
    };

    const selectedEvent = selectedEventIndex !== null ? events[selectedEventIndex] : (events.length > 0 ? events[events.length - 1] : null);

    return (
        <div className="min-h-screen bg-slate-950 p-6 md:p-8 font-sans pb-24 text-slate-200">
            <div className="max-w-7xl mx-auto space-y-8 h-full flex flex-col">
                <header>
                    <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 inline-block">
                        Hardware Procurement Engine
                    </h1>
                    <p className="text-slate-400 mt-2 text-sm font-medium tracking-wide uppercase">Autonomous Multi-Agent Analysis Dashboard</p>
                </header>

                <CommandCenter
                    onStartJob={handleStartJob}
                    onUploadPDF={handleUploadPDF}
                    isProcessing={isProcessing}
                />

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 min-h-[600px] mt-8 flex-1">
                    <TraceWaterfall
                        events={events}
                        onSelectEvent={(evt) => setSelectedEventIndex(events.indexOf(evt))}
                        selectedEventIndex={selectedEventIndex !== null ? selectedEventIndex : (events.length > 0 ? events.length - 1 : null)}
                    />
                    <LiveInspector event={selectedEvent} />
                </div>
            </div>
        </div>
    );
}

export default App;
