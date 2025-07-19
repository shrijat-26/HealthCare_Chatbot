// actions.tsx
"use client";

import { CoreMessage } from "ai";

export async function checkUserExists(user_id: string) {
  const response = await fetch("http://127.0.0.1:8000/check-user", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id }),
  });
  
  if (!response.ok) {
    throw new Error("Failed to check user existence");
  }

  const data = await response.json();
  return data;
}

export async function createUserProfile(user_id: string, name: string, age: string) {
  const response = await fetch("http://127.0.0.1:8000/create-profile", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, name, age }),
  });
  
  if (!response.ok) {
    throw new Error("Failed to create user profile");
  }

  const data = await response.json();
  return data;
}

export async function continueConversation(messages: CoreMessage[], user_id?: string) {
  // Perform a POST request to your local server
  console.log(messages);
  const response = await fetch("http://127.0.0.1:8000/text", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ messages, user_id }),
  });
  
  if (!response.ok) {
    throw new Error("Failed to fetch from python backend");
  }

  const data = await response.json();
  console.log(data);
  return data.answer;
}

// New function to handle file uploads
export async function continueConversationFile(file: File, user_id?: string) {
  console.log("Sending Voicenote");
  const formData = new FormData();
  formData.append("file", file);
  if (user_id) {
    formData.append("user_id", user_id);
  }

  const response = await fetch("http://127.0.0.1:8000/voice", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to fetch from python backend");
  }

  const data = await response.json();
  return data.answer;
}
