import axios from 'axios';
import { NextResponse } from 'next/server';

const DJANGO_BASE_URL = process.env['NEXT_PUBLIC_API_BASE_URL'] || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    const response = await axios.post(`${DJANGO_BASE_URL}/api/user/register/`, body, {
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });
    
    return NextResponse.json({
      success: true,
      message: 'User registered successfully',
      data: response.data
    }, { status: 201 });
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const errorData = error.response?.data || { message: 'Internal server error' };
    console.error('Registration error:', error);
    return NextResponse.json(errorData, { status: statusCode });
  }
}