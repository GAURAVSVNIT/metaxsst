import axios from 'axios';

const API_BASE = 'http://127.0.0.1:7860';

export const api = axios.create({
  baseURL: API_BASE,
});

export interface DocumentSummary {
  doc_id: string;
  doc_type: string;
  title: string;
  preview: string;
  is_read: boolean;
}

export interface FraudSignal {
  signal_type: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface Observation {
  task_id: string;
  task_description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  available_documents: DocumentSummary[];
  read_documents: Record<string, any>;
  detected_signals: FraudSignal[];
  steps_taken: number;
  steps_remaining: number;
  cumulative_reward: number;
  last_action_result: string | null;
  last_action_error: string | null;
  done: boolean;
  info: any;
}

export const fetchTasks = async () => {
  const { data } = await api.get('/tasks');
  return data;
};

export const resetEnv = async (taskId: string, sessionId: string = 'frontend-user') => {
  const { data } = await api.post('/reset', { task_id: taskId, session_id: sessionId });
  return data as Observation;
};

export const stepEnv = async (action: any, sessionId: string = 'frontend-user') => {
  const { data } = await api.post('/step', { action, session_id: sessionId });
  return data;
};

export const fetchState = async (sessionId: string = 'frontend-user') => {
  const { data } = await api.get('/state', { params: { session_id: sessionId } });
  return data;
};
