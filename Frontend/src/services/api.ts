/**
 * Service to communicate with the RAG backend.
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

export interface Source {
  content: string;
  score: number;
  metadata: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  sources: Source[];
}

export interface InventoryItem {
  id: string;
  name: string;
  full_path: string;
  type: string;
  status: 'indexed' | 'pending';
  vectors: number;
  size: string;
}

export interface SystemStatus {
  status: string;
  total_vectors: number;
  device: string;
  inventory: InventoryItem[];
}

export const chatService = {
  /**
   * Sends a message to the RAG chatbot.
   */
  async sendMessage(query: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to get response from bot');
      }

      return await response.json();
    } catch (error) {
      console.error('Chat service error:', error);
      throw error;
    }
  },

  /**
   * Uploads a file (PDF, CSV, or Audio) to the knowledge base.
   */
  async uploadFile(file: File): Promise<{ message: string }> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to upload file');
      }

      return await response.json();
    } catch (error) {
      console.error('Upload service error:', error);
      throw error;
    }
  },

  /**
   * Checks the status of the backend API and retrieves the full inventory.
   */
  async getStatus(): Promise<SystemStatus> {
    try {
      const response = await fetch(`${API_BASE_URL}/status`);
      if (!response.ok) throw new Error('API offline');
      return await response.json();
    } catch (error) {
      console.error('Status check failed:', error);
      throw error;
    }
  },

  /**
   * Surgically deletes a file and its vectors.
   */
  async deleteFile(filePath: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file_path: filePath }),
      });

      if (!response.ok) throw new Error('Failed to delete file');
      return await response.json();
    } catch (error) {
      console.error('Delete service error:', error);
      throw error;
    }
  }
};
