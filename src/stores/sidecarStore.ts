import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface SidecarState {
  isSidecarReady: boolean;
  logs: string;
  setIsSidecarReady: (ready: boolean) => void;
  addLog: (log: string) => void;
  clearLogs: () => void;
}

export const useSidecarStore = create<SidecarState>()(
  devtools((set) => ({
    isSidecarReady: false,
    logs: '[ui] Listening for sidecar & network logs...',

    setIsSidecarReady: (ready) => set({ isSidecarReady: ready }),
    
    addLog: (log) => 
      set((state) => ({ 
        logs: state.logs + `\n${log}`
      })),
    
    clearLogs: () => set({ 
      logs: '[ui] Listening for sidecar & network logs...' 
    }),
  }))
);