import { NextResponse } from 'next/server';
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
    }, { withCredentials: true});

    if (response.status !== 200) {
      return NextResponse.json(
        { message: 'Login failed', error: response.data },
        { status: response.status }
      );
    }

    // Create a new response to forward the data
    const nextResponse = NextResponse.json({ 
      success: true, 
      message: 'Logged in successfully',
      data: response.data
    });

    // Forward cookies from Django response to client
    const setCookieHeader = response.headers['set-cookie'];
    if (setCookieHeader) {
      setCookieHeader.forEach((cookie: string) => {
        const [nameValue, ...attributes] = cookie.split(';');
        const [name, value] = nameValue.split('=');
        
        // Set the cookie on the response
        nextResponse.cookies.set(name.trim(), value, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          path: '/',
        });
      });
    }

    return nextResponse;
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const errorData = error.response?.data || { message: 'Internal server error' };
    console.error('Login error:', error);
    return NextResponse.json(errorData, { status: statusCode });
  }
}
