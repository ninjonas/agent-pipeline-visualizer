// API service for interacting with the Flask backend
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export type ApiResponse<T = any> = {
  data: T | null;
  error: string | null;
  loading: boolean;
};

export async function fetchData<T>(endpoint: string): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`/api${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    const data = await response.json();
    return { data, error: null, loading: false };
  } catch (error) {
    console.error('API fetch error:', error);
    return { data: null, error: error instanceof Error ? error.message : 'Unknown error', loading: false };
  }
}

export async function postData<T, R = any>(endpoint: string, data: T): Promise<ApiResponse<R>> {
  try {
    const response = await fetch(`/api${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    const responseData = await response.json();
    return { data: responseData, error: null, loading: false };
  } catch (error) {
    console.error('API post error:', error);
    return { data: null, error: error instanceof Error ? error.message : 'Unknown error', loading: false };
  }
}

export async function deleteData<R = any>(endpoint: string): Promise<ApiResponse<R>> {
  try {
    const response = await fetch(`/api${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    const responseData = await response.json();
    return { data: responseData, error: null, loading: false };
  } catch (error) {
    console.error('API delete error:', error);
    return { data: null, error: error instanceof Error ? error.message : 'Unknown error', loading: false };
  }
}
