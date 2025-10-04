"use client";

import { useEffect, useState } from 'react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { invoke } from '@tauri-apps/api/core';
import { listen, Event } from '@tauri-apps/api/event';

export default function Splashscreen() {
  const [loadingMessage, setLoadingMessage] = useState("Initializing application...");
  const [progress, setProgress] = useState(0);
  const appWindow = getCurrentWindow();

  useEffect(() => {
    let unlistenStdout: (() => void) | null = null;
    let unlistenStderr: (() => void) | null = null;
    
    // Function to check if sidecar is ready
    const checkSidecarReady = async () => {
      try {
        setLoadingMessage("Starting Python sidecar...");
        setProgress(20);
        
        // Start the sidecar if not already running
        await invoke('start_sidecar');
        setProgress(40);
        
        // Listen for sidecar stdout to detect when it's ready
        unlistenStdout = await listen('sidecar-stdout', (event: Event<string>) => {
          console.log('Sidecar stdout:', event.payload);
          
          // Check if the payload indicates the sidecar is ready
          // This depends on what your Python sidecar outputs when ready
          if (event.payload.toLowerCase().includes('ready') || 
              event.payload.toLowerCase().includes('listening') ||
              event.payload.toLowerCase().includes('server running') ||
              event.payload.toLowerCase().includes('started')) {
            hideSplashscreen();
          }
        });

        // Listen for sidecar stderr as well
        unlistenStderr = await listen('sidecar-stderr', (event: Event<string>) => {
          console.error('Sidecar stderr:', event.payload);
          
          // Handle error conditions if needed
          if (event.payload.toLowerCase().includes('error')) {
            setLoadingMessage("Error starting sidecar. Please check logs.");
          }
        });

        setProgress(60);
        setLoadingMessage("Waiting for Python sidecar to be ready...");
        
        // Set a timeout to show the main window even if we don't get a ready signal
        setTimeout(() => {
          // Only hide splashscreen if it hasn't been hidden already
          if (progress < 100) {
            hideSplashscreen();
          }
        }, 10000); // Wait up to 10 seconds
        
      } catch (error) {
        console.error('Error during splashscreen:', error);
        setLoadingMessage("Error initializing. Please try again.");
      }
    };

    const hideSplashscreen = async () => {
      try {
        setProgress(100);
        setLoadingMessage("Loading main application...");
        
        // Close the splashscreen window
        await appWindow.close();
        
        // Show the main window
        await invoke('show_main_window');
      } catch (error) {
        console.error('Error hiding splashscreen:', error);
      }
    };

    // Start the initialization process
    checkSidecarReady();

    // Cleanup function
    return () => {
      if (unlistenStdout) unlistenStdout();
      if (unlistenStderr) unlistenStderr();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex flex-col items-center justify-center text-white p-8">
      <div className="flex flex-col items-center">
        {/* Logo/Icon placeholder */}
        <div className="mb-8 flex flex-col items-center">
          <div className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-white/30 rounded-full animate-pulse"></div>
          </div>
          <h1 className="text-3xl font-bold text-center">Buddhi AI</h1>
        </div>
        
        {/* Loading message */}
        <p className="text-lg text-center mb-8">{loadingMessage}</p>
        
        {/* Progress bar */}
        <div className="w-full max-w-xs bg-gray-700/50 rounded-full h-2.5 mb-4">
          <div 
            className="bg-blue-500 h-2.5 rounded-full transition-all duration-300 ease-out" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        
        {/* Progress percentage */}
        <span className="text-sm text-gray-300">{Math.round(progress)}%</span>
      </div>
    </div>
  );
}