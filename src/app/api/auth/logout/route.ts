import axios from "axios";
import { NextResponse } from "next/server";

const DJANGO_BASE_URL =
  process.env["NEXT_PUBLIC_API_BASE_URL"] || "http://localhost:8000";

/**
 * Handles user logout.
 * Clears authentication cookies.
 */
export async function POST() {
  try {
    const response = await axios.post(
      `${DJANGO_BASE_URL}/api/user/logout/`,
      null,
      { withCredentials: true }
    );
    // Create a new response to set cookies
    const nextResponse = NextResponse.json({
      success: true,
      message: "Logged out successfully",
      data: response.data,
    });

    return nextResponse;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const errorData = error.response?.data || {
      message: "Internal server error",
    };
    console.error("Logout error:", error);
    return NextResponse.json(errorData, { status: statusCode });
  }
}
