import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const protectedRoutes = ['/dashboard'];

export default function middleware(req: NextRequest) {
  const token = req.cookies.get('access_token');
  
  console.log('=== MIDDLEWARE DEBUG ===');
  console.log('Path:', req.nextUrl.pathname);
  console.log('Token present:', !!token);
  console.log('All cookies:', req.cookies.getAll().map(c => ({ name: c.name, value: c.value.substring(0, 20) + '...' })));
  console.log('========================');

  if (!token && protectedRoutes.includes(req.nextUrl.pathname)) {
    const loginUrl = new URL('/login', req.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*'],
};