import axios from "axios";
import { NextRequest, NextResponse } from "next/server";

const DJANGO_BASE_URL =
  process.env["NEXT_PUBLIC_API_BASE_URL"] || "http://localhost:8000";

/**
 * Handles token refresh.
 * Forwards authentication cookies and returns new tokens.
 */
export async function POST(request: NextRequest) {
  try {
    // Get cookies from the incoming request
    const cookieHeader = request.headers.get("cookie");
    
    const response = await axios.post(
      `${DJANGO_BASE_URL}/api/user/token-refresh/`,
      null,
      {
        headers: {
          ...(cookieHeader && { Cookie: cookieHeader }),
        },
        withCredentials: true,
      }
    );
    
    // Create a new response
    const nextResponse = NextResponse.json({
      success: true,
      message: "Token refreshed successfully",
      data: response.data,
    });

    // Clear the authentication cookies
    nextResponse.cookies.set('access_token', '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      expires: new Date(0), // Expire the cookie
    });
    
    nextResponse.cookies.set('refresh_token', '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      expires: new Date(0), // Expire the cookie
    });

    return nextResponse;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const errorData = error.response?.data || {
      message: "Internal server error",
    };
    console.error("Token refresh error:", error);
    return NextResponse.json(errorData, { status: statusCode });
  }
}
