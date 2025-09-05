import NextAuth from "next-auth";
import Keycloak from "next-auth/providers/keycloak";

// NextAuth v5: export handlers (GET/POST) and helpers from a shared `auth.ts`.
export const {
  auth,
  signIn,
  signOut,
  // expose the route handlers so the API route can re-export them
  handlers: { GET, POST },
} = NextAuth({
  providers: [
    Keycloak({
      clientId: process.env.AUTH_KEYCLOAK_ID,
      clientSecret: process.env.AUTH_KEYCLOAK_SECRET,
      issuer: process.env.AUTH_KEYCLOAK_ISSUER,
      authorization: {
        params: {
          prompt: "login",
        },
      },
    }),
  ],
});