"use client";

import { Button } from "@/components/ui/button";

export default function LibraryPage() {

  const greet = async () => {
    console.log("Namo Buddhaya!");
  };

  return (
    <div className="flex flex-1 flex-col gap-4 px-4 py-10">
      <div className="bg-muted/50 mx-auto h-24 w-full max-w-3xl rounded-xl"></div>
      <Button onClick={greet}>click</Button>
    </div>
  );
}
