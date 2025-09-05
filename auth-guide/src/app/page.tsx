"use client";

import { signIn, signOut, useSession } from "next-auth/react"


import Link from "next/link"

export default function Home() {
  const { data: session } = useSession()

  return (
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        <h1 className="text-4xl font-bold">Next.js + Keycloak</h1>
        {session ? (
          <div className="flex flex-col gap-4 items-center">
            <p>Welcome, {session.user?.name}!</p>
            <Link href="/dashboard" className="underline">Go to Dashboard</Link>
            <button
              onClick={() => signOut()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Sign Out
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-4 items-center">
            <p>You are not signed in.</p>
            <button
              onClick={() => signIn("keycloak")}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Sign In
            </button>
          </div>
        )}
      </main>
    </div>
  )
}