import axios from 'axios';
import { NextApiRequest } from 'next';
import { NextResponse } from 'next/server';

const DJANGO_BASE_URL = process.env['NEXT_PUBLIC_API_BASE_URL'] || 'http://localhost:8000';

export async function POST(req: NextApiRequest) {
  if (req.method !== 'POST') {
    return NextResponse.json({ message: 'Method not allowed' }, { status: 405 });
  }

  try {
    const response = await axios.post(`${DJANGO_BASE_URL}/api/register/`, req.body, {
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const errorData = error.response?.data || { message: 'Internal server error' };
    return NextResponse.json(errorData, { status: statusCode });
  }
}