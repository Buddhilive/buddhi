import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import axios from 'axios';

const DJANGO_BASE_URL = process.env['NEXT_PUBLIC_API_BASE_URL'] || 'http://localhost:8000';

/**
 * Handles user login.
 * Sends credentials to Django, receives tokens, and sets HTTP-only cookies.
 */
export async function POST(request: Request) {
  const { email, password } = await request.json();

  if (!email || !password) {
    return NextResponse.json(
      { message: 'Email and password are required' },
      { status: 400 }
    );
  }

  try {
    const response = await axios.post(`${DJANGO_BASE_URL}/api/user/login/`, {
      email,
      password,
    });

    if (response.status !== 200) {
      return NextResponse.json(
        { message: 'Login failed', error: response.data },
        { status: response.status }
      );
    }

    // Create a new response to set cookies
    const nextResponse = NextResponse.json({ success: true, message: 'Logged in successfully' });

    return nextResponse;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const errorData = error.response?.data || { message: 'Internal server error' };
    console.error('Login error:', error);
    return NextResponse.json(errorData, { status: statusCode });
  }
}
