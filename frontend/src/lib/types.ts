export type AskRequest = {
  query: string;
};

export type AskResponse = {
  query: string;
  answer: string;
  confidence: number;
  sources: string[];
  model: string;
  latency_ms: number;
  found: boolean;
  title?: string;
  url?: string;
  finish_reason?: string;
  response_length?: number;
};

export type ApiError = {
  detail?: string;
};

