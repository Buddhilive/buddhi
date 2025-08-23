import axios from "axios";
import { NextRequest, NextResponse } from "next/server";

const DJANGO_BASE_URL =
  process.env["NEXT_PUBLIC_API_BASE_URL"] || "http://localhost:8000";

/**
 * Handles getting user information.
 * Forwards authentication cookies to Django backend.
 */
export async function GET(request: NextRequest) {
  try {
    // Get cookies from the incoming request
    const cookieHeader = request.headers.get("cookie");
    
    const response = await axios.get(
      `${DJANGO_BASE_URL}/api/user/info/`,
      {
        headers: {
          ...(cookieHeader && { Cookie: cookieHeader }),
        },
        withCredentials: true,
      }
    );
    
    // Create a new response to return user data
    const nextResponse = NextResponse.json({
      success: true,
      message: "User information retrieved successfully",
      data: response.data,
    });

    return nextResponse;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const errorData = error.response?.data || {
      message: "Internal server error",
    };
    console.error("User information retrieval error:", error);
    return NextResponse.json(errorData, { status: statusCode });
  }
}
