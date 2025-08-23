import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const protectedRoutes = ['/dashboard'];

export default function middleware(req: NextRequest) {
  const token = req.cookies.get('access_token');

  if (!token && protectedRoutes.includes(req.nextUrl.pathname)) {
    const loginUrl = new URL('/login', req.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*'],
};