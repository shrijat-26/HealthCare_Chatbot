// chat.tsx
"use client";

import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import { type CoreMessage } from "ai";
import { BsNvidia } from "react-icons/bs";
import ChatInput from "./chat-input";
import { FaUserAstronaut } from "react-icons/fa6";
import { IoLogoVercel } from "react-icons/io5";
import { continueConversation, continueConversationFile, checkUserExists, createUserProfile } from "../app/actions";
import { toast } from "sonner";
import remarkGfm from "remark-gfm";
import { MemoizedReactMarkdown } from "./markdown";

// A simple component to animate the "Thinking" dots
function ThinkingDots() {
  const [dots, setDots] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length < 3 ? prev + "." : ""));
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return <span>Thinking{dots}</span>;
}

export const dynamic = "force-dynamic";
export const maxDuration = 30;

export default function Chat() {
  const [messages, setMessages] = useState<CoreMessage[]>([]);
  const [input, setInput] = useState("");
  const messageEndRef = useRef<HTMLDivElement>(null);
  const [userId, setUserId] = useState<string>("");
  const [userIdInput, setUserIdInput] = useState<string>("");
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [profileData, setProfileData] = useState({ name: "", age: "" });
  const [isLoading, setIsLoading] = useState(false);

  const THOUGHT_MARKER = "__THINKING__"; // marker for the animated placeholder

  const handleUserIdSubmit = async () => {
    if (!userIdInput.trim()) return;
    
    setIsLoading(true);
    try {
      const userCheck = await checkUserExists(userIdInput.trim());
      
      if (userCheck.exists) {
        // User exists, proceed to chat
        setUserId(userIdInput.trim());
        toast.success(`Welcome back, ${userCheck.profile.name}!`);
      } else {
        // User doesn't exist, show profile form
        setShowProfileForm(true);
      }
    } catch (error) {
      toast.error("Failed to check user. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleProfileSubmit = async () => {
    if (!profileData.name.trim() || !profileData.age.trim()) {
      toast.error("Please fill in both name and age.");
      return;
    }

    setIsLoading(true);
    try {
      await createUserProfile(userIdInput.trim(), profileData.name.trim(), profileData.age.trim());
      setUserId(userIdInput.trim());
      setShowProfileForm(false);
      toast.success(`Profile created for ${profileData.name}!`);
    } catch (error) {
      toast.error("Failed to create profile. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (input.trim().length === 0) return;
    if (!userId) return;
    // Add the user message
    const newMessages: CoreMessage[] = [
      ...messages,
      { content: input, role: "user" },
    ];
    setMessages(newMessages);
    setInput("");
    // Add a placeholder for the assistant's response using the marker
    const placeholderMessage: CoreMessage = { role: "assistant", content: THOUGHT_MARKER };
    setMessages([...newMessages, placeholderMessage]);
    try {
      // Pass userId to backend
      const result = await continueConversation(newMessages, userId);
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        updatedMessages[updatedMessages.length - 1] = { role: "assistant", content: result };
        return updatedMessages;
      });
    } catch (error) {
      toast.error((error as Error).message);
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        updatedMessages[updatedMessages.length - 1] = {
          role: "assistant",
          content: "Error retrieving answer.",
        };
        return updatedMessages;
      });
    }
  };

  // Handle voice message submissions
  const handleFileSubmit = async (file: File) => {
    if (!userId) return;
    const newMessages: CoreMessage[] = [
      ...messages,
      { content: "[Voice message]", role: "user" },
    ];
    setMessages(newMessages);
    const placeholderMessage: CoreMessage = { role: "assistant", content: THOUGHT_MARKER };
    setMessages([...newMessages, placeholderMessage]);
    try {
      const result = await continueConversationFile(file, userId);
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        updatedMessages[updatedMessages.length - 1] = { role: "assistant", content: result };
        return updatedMessages;
      });
    } catch (error) {
      toast.error((error as Error).message);
      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];
        updatedMessages[updatedMessages.length - 1] = {
          role: "assistant",
          content: "Error retrieving answer.",
        };
        return updatedMessages;
      });
    }
  };

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Show profile creation form
  if (showProfileForm) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="bg-white dark:bg-zinc-900 p-8 rounded-lg shadow-md flex flex-col items-center gap-4">
          <h2 className="text-2xl font-semibold">Create Your Profile</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">User ID: {userIdInput}</p>
          <input
            type="text"
            className="border rounded px-4 py-2 text-lg w-full"
            placeholder="Your Name"
            value={profileData.name}
            onChange={e => setProfileData(prev => ({ ...prev, name: e.target.value }))}
            onKeyDown={e => { if (e.key === "Enter" && profileData.name.trim() && profileData.age.trim()) handleProfileSubmit(); }}
          />
          <input
            type="text"
            className="border rounded px-4 py-2 text-lg w-full"
            placeholder="Your Age"
            value={profileData.age}
            onChange={e => setProfileData(prev => ({ ...prev, age: e.target.value }))}
            onKeyDown={e => { if (e.key === "Enter" && profileData.name.trim() && profileData.age.trim()) handleProfileSubmit(); }}
          />
          <button
            className="bg-nvidia text-white px-6 py-2 rounded hover:bg-nvidia/80 transition"
            onClick={handleProfileSubmit}
            disabled={!profileData.name.trim() || !profileData.age.trim() || isLoading}
          >
            {isLoading ? "Creating..." : "Create Profile"}
          </button>
          <button
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            onClick={() => setShowProfileForm(false)}
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  // Show user ID input
  if (!userId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="bg-white dark:bg-zinc-900 p-8 rounded-lg shadow-md flex flex-col items-center gap-4">
          <h2 className="text-2xl font-semibold">Enter your User ID</h2>
          <input
            type="text"
            className="border rounded px-4 py-2 text-lg"
            placeholder="User ID"
            value={userIdInput}
            onChange={e => setUserIdInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && userIdInput.trim()) handleUserIdSubmit(); }}
          />
          <button
            className="bg-nvidia text-white px-6 py-2 rounded hover:bg-nvidia/80 transition"
            onClick={handleUserIdSubmit}
            disabled={!userIdInput.trim() || isLoading}
          >
            {isLoading ? "Checking..." : "Continue"}
          </button>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="stretch mx-auto flex min-h-screen w-full max-w-xl flex-col justify-center px-4 pb-[8rem] pt-[6rem] md:px-0 md:pt-[4rem] xl:pt-[2rem]">
        <h1 className="text-center text-5xl font-medium tracking-tighter">
          <a
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-nvidia hover:cursor-pointer transition-all duration-150 ease-linear"
          >
            Kare.ai
          </a>
        </h1>
        <h2 className="text-center text-nvidia">by QuantumWar</h2>
        <div className="mt-6 flex items-center justify-center gap-4">
          <IoLogoVercel className="size-20" />
        </div>

        <div className="mt-6 px-3 md:px-0">
          <h2 className="text-base font-medium">Points to note:</h2>
          <ul className="ml-6 mt-2 flex list-disc flex-col items-start gap-2.5 text-sm text-primary/80">
            <li>
              Introducing your <span className="text-nvidia font-medium">Emotion‑Aware Healthcare Companion</span>, a next‑generation chat interface that understands not just what you say, but how you feel.
            </li>
            <li>
              As you type or speak, our real‑time emotion meter visualizes your mood, while intelligent symptom extraction and RAG‑powered medical retrieval deliver personalized diagnostic insights.
            </li>
            <li>
              Experience compassionate, tone‑adaptive responses and book appointments with nearby specialists in just a few clicks—right within the conversation.
            </li>
          </ul>
        </div>

        <ChatInput input={input} setInput={setInput} handleSubmit={handleSubmit} />
      </div>
    );
  }

  return (
    <div className="stretch mx-auto w-full max-w-2xl px-4 py-[8rem] pt-24 md:px-0">
      {messages.map((m, i) => (
        <div key={i} className="mb-4 flex items-start p-2">
          <div>
            {m.role === "user" ? (
              <FaUserAstronaut />
            ) : (
              <IoLogoVercel className="size-4" />
            )}
          </div>
          <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1">
            {m.content === THOUGHT_MARKER ? (
              // Render the animated ThinkingDots component if the marker is found
              <ThinkingDots />
            ) : (
              <MemoizedReactMarkdown
                remarkPlugins={[remarkGfm]}
                className="prose prose-sm break-words dark:prose-invert prose-pre:rounded-lg prose-pre:bg-zinc-100 prose-pre:p-4 prose-pre:text-zinc-900 dark:prose-pre:bg-zinc-900 dark:prose-pre:text-zinc-100"
              >
                {m.content as string}
              </MemoizedReactMarkdown>
            )}
          </div>
        </div>
      ))}
      <div ref={messageEndRef} />
      <ChatInput
        input={input}
        setInput={setInput}
        handleSubmit={handleSubmit}
        handleFileSubmit={handleFileSubmit} // pass our new callback
      />
    </div>
  );
}
