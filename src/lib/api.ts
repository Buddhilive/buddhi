import { ChatMessage } from '@/types/chat';

interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
}

interface ChatCompletionResponse {
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

export interface ApiError {
  message: string;
  status?: number;
}

export const chatApi = {
  async getCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    try {
      // In a Tauri app, we might use tauri commands or make a fetch to our backend
      // For now, assuming the backend is running locally
      const response = await fetch('http://127.0.0.1:8008/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: request.model || 'gemma-3-270m-it', // Default model
          messages: request.messages,
          temperature: request.temperature || 1.0,
          max_tokens: request.max_tokens || 50
        }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        let errorMessage = `API Error: ${response.status} - ${errorData}`;
        
        // Provide more user-friendly error messages
        if (response.status === 400) {
          errorMessage = "Bad request: Please check your input";
        } else if (response.status === 404) {
          errorMessage = "API endpoint not found. Please check if the backend is running";
        } else if (response.status === 500) {
          errorMessage = "Server error: The AI service is temporarily unavailable";
        } else if (response.status === 503) {
          errorMessage = "Service unavailable: The AI model is not loaded properly";
        }
        
        throw new Error(errorMessage);
      }

      const data: ChatCompletionResponse = await response.json();
      return data;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error: Unable to connect to the AI service. Please make sure the backend server is running...\n' + error.message);
      }
      
      if (error instanceof Error) {
        throw error;
      } else {
        throw new Error('Unknown error occurred while fetching completion');
      }
    }
  }
};