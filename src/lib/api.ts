import {
  ChatCompletionRequest,
  ChatCompletionResponse,
  RetrievalMatch,
  RetrievalResponse,
} from "@/types/chat";
import { fetch } from "pyloid-js";

export const chatApi = {
  async getCompletion(
    request: ChatCompletionRequest
  ): Promise<ChatCompletionResponse> {
    try {
      // In a Tauri app, we might use tauri commands or make a fetch to our backend
      // For now, assuming the backend is running locally
      const response = await fetch("/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: request.model || "gemma-3-270m-it", // Default model
          messages: request.messages,
          temperature: request.temperature || 1.0,
          max_tokens: request.max_tokens || 50,
        }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        let errorMessage = `API Error: ${response.status} - ${errorData}`;

        // Provide more user-friendly error messages
        if (response.status === 400) {
          errorMessage = "Bad request: Please check your input";
        } else if (response.status === 404) {
          errorMessage =
            "API endpoint not found. Please check if the backend is running";
        } else if (response.status === 500) {
          errorMessage =
            "Server error: The AI service is temporarily unavailable";
        } else if (response.status === 503) {
          errorMessage =
            "Service unavailable: The AI model is not loaded properly";
        }

        throw new Error(errorMessage);
      }

      const data: ChatCompletionResponse = await response.json();
      return data;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error(
          "Network error: Unable to connect to the AI service. Please make sure the backend server is running...\n" +
            error.message
        );
      }

      if (error instanceof Error) {
        throw error;
      } else {
        throw new Error("Unknown error occurred while fetching completion");
      }
    }
  },
  async queryKnowledgebase(query: string): Promise<RetrievalResponse> {
    const url = "/v1/embeddings/query_pdf/";

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        // Try to extract JSON error detail if available
        const errorText = await response.text();
        let errorDetail: string | undefined;
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail ?? errorText;
        } catch {
          errorDetail = errorText;
        }

        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: RetrievalResponse = await response.json();
      return data;
    } catch (err: any) {
      // Handle both network and parsing errors gracefully
      throw new Error(err.detail ?? "Network or parsing error");
    }
  },
  getTopRelevantMatch(matches: RetrievalMatch[]): RetrievalMatch | undefined {
    const filtered = matches.filter((m) => m.similarity_score > 0.3);
    if (filtered.length === 0) return undefined;

    // Return the match with the maximum similarity_score
    return filtered.reduce((best, current) =>
      current.similarity_score > best.similarity_score ? current : best
    );
  },
};
