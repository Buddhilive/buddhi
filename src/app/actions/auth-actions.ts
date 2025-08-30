"use server";

const FASTAPI_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export async function registerUser(username: string, password: string) {
  try {
    const response = await fetch(`${FASTAPI_BASE_URL}/auth/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error: any) {
    console.error("User registration failed:", error);
    throw error;
  }
}

export async function loginUser(username: string, password: string) {
  console.log("Logging in user with URL:", FASTAPI_BASE_URL);
  console.log("Environment variable:", process.env.NEXT_PUBLIC_API_BASE_URL);
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);
  try {
    const response = await fetch(`${FASTAPI_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
      credentials: "include",
    });
    const data = await response.json();
    console.log("Response status:", response.status);
    console.log("Response headers:", Object.fromEntries(response.headers.entries()));
    console.log("Response data:", data);
    if (!response.ok) {
      // Optionally pass FastAPI error message to frontend
      return { success: false, message: data?.detail || `HTTP error! status: ${response.status}` };
    }
    // Wrap FastAPI response in NextResponse-like format
    return { success: true, ...data };
  } catch (error: any) {
    console.error("User login failed:", error);
    return { success: false, message: error?.message || "Network error occurred" };
  }
}

export async function logoutUser() {
  try {
    const response = await fetch(`${FASTAPI_BASE_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error: any) {
    console.error("User logout failed:", error);
    throw error;
  }
}

export async function getUserInfo() {
  try {
    const response = await fetch(`${FASTAPI_BASE_URL}/auth/me`, {
      method: "GET",
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error: any) {
    console.error("User information retrieval failed:", error);
    throw error;
  }
}

export async function refreshToken() {
  try {
    const response = await fetch(`${FASTAPI_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error: any) {
    console.error("User token refresh failed:", error);
    throw error;
  }
}
