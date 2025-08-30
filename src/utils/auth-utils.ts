interface User {
  username: string;
  email: string;
  avatar: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface LoginResponse {
  success: boolean;
  error?: string;
  user?: User;
}

interface UserInfoResponse {
  success: boolean;
  user?: User;
  error?: string;
  statusCode?: number;
}

/**
 * Login user with username and password
 */
export async function loginUser(credentials: LoginCredentials): Promise<LoginResponse> {
  try {
    const body = new URLSearchParams();
    body.append("username", credentials.username);
    body.append("password", credentials.password);
    
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
      credentials: "include",
    });
    
    const data = await response.json();
    
    if (response.ok) {
      return { success: true, user: data };
    } else {
      return { success: false, error: data?.detail || "Login failed" };
    }
  } catch (error) {
    console.error("Login error:", error);
    return { success: false, error: "Network error occurred" };
  }
}

/**
 * Logout current user
 */
export async function logoutUser(): Promise<LoginResponse> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
    
    if (response.ok) {
      return { success: true };
    } else {
      console.error("Logout failed:", response.status);
      return { success: false, error: `Logout failed with status: ${response.status}` };
    }
  } catch (error) {
    console.error("Logout error:", error);
    return { success: false, error: "Network error occurred during logout" };
  }
}

/**
 * Get current user information
 */
export async function getUserInfo(): Promise<UserInfoResponse> {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/me`, {
      method: "GET",
      credentials: "include",
    });
    
    if (response.ok) {
      const userData = await response.json();
      const user: User = {
        username: userData.username,
        email: userData.email || userData.username,
        avatar: userData.avatar || '/next.svg',
      };
      return { success: true, user };
    } else {
      console.error("Failed to fetch user information:", response.status);
      return { 
        success: false, 
        error: "Failed to fetch user information", 
        statusCode: response.status 
      };
    }
  } catch (error) {
    console.error("Error fetching user information:", error);
    return { success: false, error: "Network error occurred while fetching user info" };
  }
}
