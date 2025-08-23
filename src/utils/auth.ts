import { NextResponse } from "next/server";

export async function registerUser(email: string, password: string) {
  try {
    const response = await fetch(`/api/auth/register`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
  } catch (error: any) {
    console.error('User registration failed:', error);
    throw error;
  }
}

export async function loginUser(email: string, password: string) {
  try {
    const response = await fetch(`/api/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
  } catch (error: any) {
    console.error('User login failed:', error);
    throw error;
  }
}

export async function logoutUser() {
  try {
    const response = await fetch(`/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
  } catch (error: any) {
    console.error('User logout failed:', error);
    throw error;
  }
}

export async function getUserInfo() {
  try {
    const response = await fetch(`/api/auth/user`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
  } catch (error: any) {
    console.error('User information retrieval failed:', error);
    throw error;
  }
}

export async function refreshToken() {
  try {
    const response = await fetch(`/api/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
  } catch (error: any) {
    console.error('User token refresh failed:', error);
    throw error;
  }
}
