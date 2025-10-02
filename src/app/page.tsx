"use client";
import { listen } from '@tauri-apps/api/event';
import { useEffect } from 'react';
import { useSidecarStore } from '@/stores/sidecarStore';
import Splashscreen from '@/components/splashscreen';

export default function Home() {
  const { logs, isSidecarReady, addLog } = useSidecarStore();
  
  useEffect(() => {
    if (isSidecarReady) {
      initSidecarListeners();
    }
  }, [isSidecarReady]);

  const initSidecarListeners = async () => {
    // Listen for stdout lines from the sidecar
    const unlistenStdout = await listen('sidecar-stdout', (event) => {
      console.log('Sidecar stdout:', event.payload);
      if (`${event.payload}`.length > 0 && event.payload !== "\r\n") {
        addLog(`${event.payload}`);
      }
    });

    // Listen for stderr lines from the sidecar
    const unlistenStderr = await listen('sidecar-stderr', (event) => {
      console.error('Sidecar stderr:', event.payload);
      if (`${event.payload}`.length > 0 && event.payload !== "\r\n") {
        addLog(`${event.payload}`);
      }
    });

    // Cleanup listeners when not needed
    return () => {
      unlistenStdout();
      unlistenStderr();
    };
  };

  // Show splashscreen until sidecar is ready, then show main content
  if (!isSidecarReady) {
    return <Splashscreen>Logs will appear here...</Splashscreen>;
  }

  return (
    <div className="flex flex-1 flex-col gap-4 px-4 py-10">
      <code className="bg-muted/50 mx-auto h-full w-full max-w-3xl rounded-xl p-2">{logs}</code>
    </div>
  );
}
