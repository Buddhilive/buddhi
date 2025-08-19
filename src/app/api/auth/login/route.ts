import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000/api/auth';

export async function POST(request: NextRequest) {
    const body = await request.json();
    const { username, password } = body;

    try {
        const response = await fetch(`${DJANGO_API_URL}/api/auth/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            return NextResponse.json({ error: 'Login failed' }, { status: response.status });
        }

        // Get access and refresh tokens from the Django response headers
        const djangoCookies = response.headers.getSetCookie();

        // Set cookies in the Next.js response to the client
        const nextResponse = new NextResponse(response.body, {
            status: response.status,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        djangoCookies.forEach(cookie => {
            nextResponse.headers.append('Set-Cookie', cookie);
        });

        return nextResponse;
    } catch (error) {
        console.error('Login error:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}