import { NextResponse } from 'next/server';
import { djangoFetch, setAuthCookies, clearAuthCookies } from '@/utils/auth';
import { cookies } from 'next/headers';

/**
 * Handles refreshing authentication tokens.
 * Reads refresh token from cookie, sends to Django, and updates cookies with new tokens.
 */
export async function POST(request: Request) {
  const cookieStore = cookies();
  const refreshToken = (await cookieStore).get('refreshToken')?.value;

  if (!refreshToken) {
    return NextResponse.json(
      { message: 'No refresh token found' },
      { status: 401 }
    );
  }

  // Call Django refresh token endpoint
  const djangoResponse = await djangoFetch('/token/refresh/', {
    method: 'POST',
    body: JSON.stringify({ refresh: refreshToken }),
  });

  const response = NextResponse.json({}); // Default response to modify

  if (!djangoResponse.ok) {
    // If refresh fails (e.g., refresh token expired or invalid)
    // Clear cookies and return error
    clearAuthCookies(response);
    const errorData = await djangoResponse.json();
    return NextResponse.json(errorData, { status: djangoResponse.status });
  }

  const { access, refresh: newRefreshToken } = await djangoResponse.json();

  if (!access || !newRefreshToken) {
    clearAuthCookies(response);
    return NextResponse.json(
      { message: 'Token refresh failed: New tokens not received' },
      { status: 500 }
    );
  }

  // Set new HTTP-only cookies
  setAuthCookies(response, access, newRefreshToken);

  return response;
}
