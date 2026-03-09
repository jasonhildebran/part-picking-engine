export interface SpecValue {
    value: number | string;
    unit: string;
}

export interface ComponentData {
    part_number: string;
    name: string;
    source_type: string;
    specs: Record<string, SpecValue>;
}

export interface AgentTrace {
    node_name: string;
    routed_from: string;
    input_received: string;
    system_prompt: string;
    agent_output: string;
    routing_to: string;
}

export interface NodeEvent {
    node: string;
    status: 'running' | 'complete' | 'failed';
    message: string;
    query?: string;
    state?: {
        candidates_evaluated?: ComponentData[];
        final_selection?: ComponentData;
        agent_traces?: AgentTrace[];
    };
}
