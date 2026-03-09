import React from 'react';
import { NodeEvent, ComponentData, SpecValue } from './types';
import { Database, Zap, HardDrive, ExternalLink } from 'lucide-react';

interface LiveInspectorProps {
    event: NodeEvent | null;
}

const isSIUnit = (unit: string | undefined) => unit && ['Nm', 'mm', 'V'].includes(unit);

export const LiveInspector: React.FC<LiveInspectorProps> = ({ event }) => {
    if (!event) {
        return (
            <div className="flex flex-col gap-4 p-6 bg-slate-900 rounded-xl shadow-2xl border border-slate-800 h-full items-center justify-center text-slate-500">
                <Database size={48} className="text-slate-700 mb-4" />
                <p>Select a node from the waterfall to inspect its state</p>
            </div>
        );
    }

    const { state, node } = event;

    let candidates: ComponentData[] = [];
    if (node === 'Checker' && state?.final_selection) {
        candidates = [state.final_selection];
    } else if (state?.candidates_evaluated && state.candidates_evaluated.length > 0) {
        candidates = [state.candidates_evaluated[state.candidates_evaluated.length - 1]];
    }

    const traces = state?.agent_traces || [];
    const activeTrace = traces.find(t => t.node_name === node);

    return (
        <div className="flex flex-col h-full overflow-hidden p-6 bg-slate-900 rounded-xl shadow-2xl border border-slate-800">
            <div className="border-b border-slate-800 pb-4 flex-shrink-0">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Database className="text-purple-400" />
                    Live Inspector
                </h2>
                <div className="mt-2 text-sm text-slate-400">Active Node: <span className="text-blue-400 font-mono bg-blue-400/10 px-2 py-0.5 rounded">{node}</span></div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-6 pr-2 pt-4">
                {activeTrace && (
                    <div className="bg-slate-950 rounded-lg p-5 border border-slate-800 shadow-inner">
                        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-widest mb-4 flex items-center gap-2">
                            <Database size={14} className="text-emerald-500" /> Agent Trace Log
                        </h3>
                        <div className="space-y-4">
                            <div>
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Routed From</h4>
                                <div className="text-blue-300 font-mono text-xs bg-slate-900 p-2.5 rounded border border-slate-800 break-words">
                                    {activeTrace.routed_from || 'Unknown'}
                                </div>
                            </div>

                            <div>
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Input Received</h4>
                                <div className="text-slate-300 font-mono text-xs bg-slate-900 p-2.5 rounded border border-slate-800 break-words">
                                    {activeTrace.input_received || 'None'}
                                </div>
                            </div>

                            <div>
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">System Prompt</h4>
                                <div className="text-purple-300 font-mono text-xs bg-purple-900/10 p-2.5 rounded border border-purple-900/30 break-words whitespace-pre-wrap">
                                    {activeTrace.system_prompt || 'N/A - Deterministic Logic Node'}
                                </div>
                            </div>

                            <div>
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Agent Output / Action</h4>
                                <div className="text-emerald-400 font-mono text-xs bg-slate-900 p-2.5 rounded border border-slate-800 break-words whitespace-pre-wrap">
                                    {activeTrace.agent_output || 'None'}
                                </div>
                            </div>

                            <div>
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">Routing To</h4>
                                <div className="text-orange-300 font-mono text-xs bg-slate-900 p-2.5 rounded border border-slate-800 break-words">
                                    {activeTrace.routing_to || 'Unknown'}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {candidates.length > 0 ? candidates.map((candidate, idx) => (
                    <div key={`${candidate.part_number}-${idx}`} className="bg-slate-800 rounded-lg p-5 border border-slate-700 hover:border-slate-600 transition-colors">
                        <div className="flex items-start justify-between mb-6">
                            <div>
                                <h3 className="text-xl font-bold text-white">{candidate.name || 'Unknown Part'}</h3>
                                <div className="text-sm text-slate-400 font-mono mt-1 px-2 py-1 bg-slate-900 rounded inline-block">{candidate.part_number}</div>
                            </div>
                            <span className="px-3 py-1 bg-purple-500/20 text-purple-300 text-xs font-bold rounded-full border border-purple-500/30 flex items-center gap-1.5 whitespace-nowrap">
                                <HardDrive size={12} />
                                {candidate.source_type}
                            </span>
                        </div>

                        <div className="space-y-3">
                            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest border-b border-slate-700 pb-2">Properties (JSON)</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {Object.entries(candidate.specs).map(([key, specObj], i) => {
                                    const spec = specObj as SpecValue;
                                    const val = spec?.value;
                                    const unit = spec?.unit;
                                    const highlightUnit = isSIUnit(unit as string);

                                    if (key === 'supplier_url' && val) {
                                        return (
                                            <div key={i} className="col-span-1 md:col-span-2 flex flex-col justify-center bg-slate-900/80 p-3 rounded-lg border border-slate-800 hover:border-slate-700 transition-colors">
                                                <span className="text-slate-400 font-mono text-xs mb-1 uppercase tracking-wide truncate">Supplier Link</span>
                                                <a href={String(val)} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1.5 truncate hover:underline">
                                                    <ExternalLink size={16} />
                                                    View on Supplier Website
                                                </a>
                                            </div>
                                        );
                                    }

                                    return (
                                        <div key={i} className="flex flex-col justify-center bg-slate-900/80 p-3 rounded-lg border border-slate-800 hover:border-slate-700 transition-colors">
                                            <span className="text-slate-400 font-mono text-xs mb-1 uppercase tracking-wide truncate" title={key.replace(/_/g, ' ')}>{key.replace(/_/g, ' ')}</span>
                                            <div className="flex items-baseline gap-2 overflow-hidden">
                                                <span className="text-emerald-400 font-mono text-base font-semibold truncate" title={String(val)}>{val !== undefined ? String(val) : 'N/A'}</span>
                                                {unit && (
                                                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded flex items-center ml-auto ${highlightUnit ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50' : 'text-slate-500 bg-slate-800'}`}>
                                                        {highlightUnit && <Zap size={10} className="inline mr-1" />}
                                                        {unit}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )
                                })}
                                {Object.keys(candidate.specs).length === 0 && (
                                    <div className="text-slate-500 text-sm italic col-span-full py-2">No flexible specs extracted.</div>
                                )}
                            </div>
                        </div>
                    </div>
                )) : null}

                {!activeTrace && candidates.length === 0 && (
                    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 flex flex-col justify-center h-full">
                        <div className="flex flex-col items-center text-center mb-6">
                            <Database size={48} className="text-slate-600 mb-4" />
                            <h3 className="text-lg font-bold text-white mb-2">Node Metadata</h3>
                            <p className="text-slate-400 text-sm">No component data extracted at this step.</p>
                        </div>

                        <div className="space-y-4 w-full mt-4">
                            <div>
                                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1 border-b border-slate-700 pb-1">Status Message</h4>
                                <div className="text-emerald-400 font-mono bg-slate-900 mt-2 p-3 rounded text-sm w-full break-words border border-slate-800">
                                    {event.message || event.status || 'No status message available.'}
                                </div>
                            </div>

                            {event.query && (
                                <div>
                                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1 border-b border-slate-700 pb-1">Active Query</h4>
                                    <div className="text-slate-300 font-mono bg-slate-900 mt-2 p-3 rounded text-sm w-full break-words border border-slate-800">
                                        {event.query}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
