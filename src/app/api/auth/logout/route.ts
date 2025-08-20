import { NextResponse } from 'next/server';

/**
 * Handles user logout.
 * Clears authentication cookies.
 */
export async function POST() {
  const response = NextResponse.json({ message: 'Logged out successfully' });
  return response;
}
