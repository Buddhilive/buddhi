"use client";

import { Button } from "@/components/ui/button";
import { invoke } from "@tauri-apps/api/core";
import { useState } from "react";

export default function LibraryPage() {
  const [greeting, setGreeting] = useState("");

  const greet = async () => {
    const greetings = await invoke("greet_user", { name: "Buddhi" }) as string;
    setGreeting(greetings);
  };

  return (
    <div className="flex flex-1 flex-col gap-4 px-4 py-10">
      <div className="bg-muted/50 mx-auto h-24 w-full max-w-3xl rounded-xl">{greeting}</div>
      <Button onClick={greet}>click</Button>
    </div>
  );
}
