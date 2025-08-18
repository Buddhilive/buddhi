import { NextApiRequest } from 'next';
import { authAPI } from '@/lib/auth';
import { NextResponse } from 'next/server';

export async function POST(req: NextApiRequest) {
  if (req.method !== 'POST') {
    return NextResponse.json({ message: 'Method not allowed' }, { status: 405 });
  }

  try {
    const response = await authAPI.register(req.body);
    return NextResponse.json(response.data, { status: 201 });
  } catch (error: any) {
    const statusCode = error.response?.status || 500;
    const errorData = error.response?.data || { message: 'Internal server error' };
    return NextResponse.json(errorData, { status: statusCode });
  }
}