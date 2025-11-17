export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string | null;
}

export interface Message {
  id?: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp?: Date;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface RetrievalMatch {
  text: string;
  similarity_score: number;
  source_filename: string;
}

export interface RetrievalResponse {
  query: string;
  retrieval_model: string;
  top_k: number;
  matches: RetrievalMatch[];
}


export interface ApiError {
  message: string;
  status?: number;
}