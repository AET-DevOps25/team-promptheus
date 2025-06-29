/**
 * Base API client configuration and utilities for the application.
 * Provides a consistent interface for making HTTP requests with proper error handling.
 */

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
}

/**
 * Base API client with consistent error handling and response formatting
 */
class ApiClient {
  private baseURL: string;

  constructor(baseURL = "") {
    this.baseURL = baseURL;
  }

  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

      try {
        const errorData = await response.json();
        if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // If we can't parse JSON, use the default error message
      }

      throw new ApiError(errorMessage, response.status, response.statusText);
    }

    const data = await response.json();
    return {
      data,
      status: response.status,
      statusText: response.statusText,
    };
  }

  async get<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseURL}${url}`, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      method: "GET",
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  async post<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseURL}${url}`, {
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      method: "POST",
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  async patch<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseURL}${url}`, {
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      method: "PATCH",
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  async put<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseURL}${url}`, {
      body: body ? JSON.stringify(body) : undefined,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      method: "PUT",
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  async delete<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseURL}${url}`, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      method: "DELETE",
      ...options,
    });

    return this.handleResponse<T>(response);
  }
}

// Create and export the default API client instance
export const apiClient = new ApiClient("/api");

// Export the class for creating custom instances if needed
export { ApiClient };
