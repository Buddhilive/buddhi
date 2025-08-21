import axios from 'axios';
import { NextResponse } from 'next/server';

export async function registerUser(email: string, password: string) {
    try {
      const response = await axios.post(`/api/auth/register/`, {
        email,
        password,
      });
      return NextResponse.json({ message: 'User registered successfully', data: response.data, status: 201 });
    } catch (error: any) {
      return NextResponse.json({ message: 'User registration failed', error: error.message }, { status: 500 });
    }
}

export async function loginUser(email: string, password: string) {
  try {
    const response = await axios.post(`/api/auth/login/`, {
      email,
      password,
    });
    return NextResponse.json({ message: 'User logged in successfully', data: response.data, status: 200 });
  } catch (error: any) {
    return NextResponse.json({ message: 'User login failed', error: error.message }, { status: 500 });
  }
}

export async function logoutUser() {
  try {
    const response = await axios.post(`/api/auth/logout/`);
    return NextResponse.json({ message: 'User logged out successfully', data: response.data, status: 200 });
  } catch (error: any) {
    return NextResponse.json({ message: 'User logout failed', error: error.message }, { status: 500 });
  }
}
