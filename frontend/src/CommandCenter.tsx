import React, { useState, useCallback } from 'react';
import { UploadCloud, Play, CheckCircle, XCircle } from 'lucide-react';

interface CommandCenterProps {
    onStartJob: (prompt: string) => void;
    onUploadPDF: (file: File) => void;
    isProcessing: boolean;
}

export const CommandCenter: React.FC<CommandCenterProps> = ({ onStartJob, onUploadPDF, isProcessing }) => {
    const [prompt, setPrompt] = useState('');
    const [dragActive, setDragActive] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave" || e.type === "drop") {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            if (file.type === "application/pdf") {
                setUploadStatus('success');
                onUploadPDF(file);

                // Reset status after a few seconds
                setTimeout(() => setUploadStatus('idle'), 3000);
            } else {
                setUploadStatus('error');
                setTimeout(() => setUploadStatus('idle'), 3000);
            }
        }
    }, [onUploadPDF]);

    return (
        <div className="flex flex-col md:flex-row gap-6 p-6 bg-slate-900 text-white rounded-xl shadow-2xl border border-slate-800">
            <div className="flex-1 flex flex-col gap-4">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    Agent Prompt
                </h2>
                <div className="flex gap-3">
                    <input
                        type="text"
                        className="flex-1 bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500 transition-all placeholder:text-slate-500"
                        placeholder="e.g. Find a 12V 300RPM brushed DC motor with a 4mm D-shaft"
                        value={prompt}
                        onChange={e => setPrompt(e.target.value)}
                        disabled={isProcessing}
                        onKeyDown={e => e.key === 'Enter' && !isProcessing && prompt && onStartJob(prompt)}
                    />
                    <button
                        disabled={isProcessing || !prompt}
                        onClick={() => onStartJob(prompt)}
                        className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-colors"
                    >
                        {isProcessing ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Play size={20} />}
                        Run
                    </button>
                </div>
            </div>

            <div className="md:w-1/3 flex flex-col gap-4">
                <h2 className="text-xl font-bold">PDF Ingestion</h2>
                <div
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    className={`flex-1 flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-3 transition-colors ${dragActive ? 'border-blue-500 bg-blue-500/10' : 'border-slate-700 hover:border-slate-600 bg-slate-800/50'} ${isProcessing ? 'opacity-50 cursor-not-allowed pointer-events-none' : 'cursor-pointer'}`}
                >
                    {uploadStatus === 'success' ? (
                        <div className="flex flex-col items-center text-green-400">
                            <CheckCircle size={32} className="mb-2" />
                            <span className="font-medium text-sm">PDF Uploaded</span>
                        </div>
                    ) : uploadStatus === 'error' ? (
                        <div className="flex flex-col items-center text-red-400">
                            <XCircle size={32} className="mb-2" />
                            <span className="font-medium text-sm">Invalid File</span>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center text-slate-400">
                            <UploadCloud size={32} className="mb-2 group-hover:text-slate-300 transition-colors" />
                            <span className="font-medium text-sm">Drag & Drop PDF</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
