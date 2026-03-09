import React, { useEffect, useRef } from 'react';
import { NodeEvent } from './types';
import { Activity, Check, AlertTriangle, Loader2 } from 'lucide-react';

interface TraceWaterfallProps {
    events: NodeEvent[];
    onSelectEvent: (event: NodeEvent) => void;
    selectedEventIndex: number | null;
}

export const TraceWaterfall: React.FC<TraceWaterfallProps> = ({ events, onSelectEvent, selectedEventIndex }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTo({
                top: containerRef.current.scrollHeight,
                behavior: 'smooth'
            });
        }
    }, [events]);

    return (
        <div className="flex flex-col gap-4 p-6 bg-slate-900 rounded-xl shadow-2xl border border-slate-800 h-full" >
            <h2 className="text-xl font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-4">
                <Activity className="text-blue-400" />
                Execution Trace Waterfall
            </h2>
            <div className="flex-1 overflow-y-auto pr-2 space-y-4" ref={containerRef}>
                {events.map((evt, idx) => {
                    const isSelected = selectedEventIndex === idx;

                    let borderColor = 'border-slate-700';
                    let icon = <Loader2 className="animate-spin text-blue-400" size={20} />;
                    let bgColor = 'bg-slate-800/50';

                    if (evt.status === 'complete' || evt.status === 'failed') {
                        if (evt.node.includes('Failed') || evt.status === 'failed' || evt.message.includes('Failed') || evt.message.includes('Error')) {
                            borderColor = 'border-red-500/50';
                            icon = <AlertTriangle className="text-red-400" size={20} />;
                            bgColor = 'bg-red-500/10';
                        } else {
                            borderColor = 'border-green-500/50';
                            icon = <Check className="text-green-400" size={20} />;
                            bgColor = 'bg-green-500/10';
                        }
                    } else if (evt.status === 'running') {
                        // pulsing blue
                        borderColor = 'border-blue-500/50';
                        bgColor = 'bg-blue-500/10 animate-pulse';
                    }

                    if (isSelected) {
                        borderColor = 'border-white';
                    }

                    return (
                        <div
                            key={`${evt.node}-${idx}`}
                            onClick={() => onSelectEvent(evt)}
                            className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:-translate-y-1 ${borderColor} ${bgColor}`}
                        >
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-slate-800 rounded-full shadow-inner flex-shrink-0">
                                    {icon}
                                </div>
                                <div className="flex-1 overflow-hidden">
                                    <h3 className="font-bold text-slate-100 text-lg truncate">{evt.node}</h3>
                                    <p className="text-slate-400 text-sm mt-1 truncate">{evt.message}</p>
                                </div>
                            </div>
                        </div>
                    );
                })}

                {events.length === 0 && (
                    <div className="h-full flex items-center justify-center text-slate-500 p-8 text-center border-2 border-dashed border-slate-800 rounded-lg">
                        Awaiting Agent Execution...<br />Provide a prompt or upload a PDF to begin.
                    </div>
                )}
            </div>
        </div>
    );
};
