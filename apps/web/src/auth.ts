import NextAuth, { type DefaultSession, type NextAuthConfig } from "next-auth";
import Google from "next-auth/providers/google";
import { SignJWT, jwtVerify, type JWTPayload } from "jose";

declare module "next-auth" {
  interface Session {
    user_id: string;
    providers: string[];
    user: DefaultSession["user"];
  }
}

const secretEnv = process.env.AUTH_SECRET;
if (!secretEnv) {
  // NextAuth v5 will throw a clearer error in production, but failing fast
  // here makes local-dev breakage obvious.
  // eslint-disable-next-line no-console
  console.warn("AUTH_SECRET is not set — auth flows will fail.");
}
const secret = new TextEncoder().encode(secretEnv ?? "");

// HS256 (JWS) instead of NextAuth's default JWE so apps/api can verify the
// same token using a shared AUTH_SECRET. Without this override, apps/api
// would have to decrypt A256GCM, which requires JOSE primitives Python
// doesn't expose cleanly.
const SEVEN_DAYS_SECONDS = 60 * 60 * 24 * 7;

const config: NextAuthConfig = {
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      authorization: { params: { prompt: "consent", access_type: "offline" } },
    }),
  ],
  session: { strategy: "jwt", maxAge: SEVEN_DAYS_SECONDS },
  jwt: {
    maxAge: SEVEN_DAYS_SECONDS,
    async encode({ token }) {
      return await new SignJWT(token as JWTPayload)
        .setProtectedHeader({ alg: "HS256", typ: "JWT" })
        .setIssuedAt()
        .setExpirationTime(`${SEVEN_DAYS_SECONDS}s`)
        .sign(secret);
    },
    async decode({ token }) {
      if (!token) return null;
      try {
        const { payload } = await jwtVerify(token, secret, { algorithms: ["HS256"] });
        return payload;
      } catch {
        return null;
      }
    },
  },
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account && profile) {
        const existingProviders = (token.providers as string[] | undefined) ?? [];
        token.providers = Array.from(new Set([...existingProviders, account.provider]));
        token.user_id = (profile.sub as string | undefined) ?? token.sub;
        token.email = profile.email as string | undefined;
      }
      return token;
    },
    async session({ session, token }) {
      session.user_id = (token.user_id as string | undefined) ?? token.sub ?? "";
      session.providers = (token.providers as string[] | undefined) ?? [];
      return session;
    },
  },
  cookies: {
    sessionToken: {
      name:
        process.env.NODE_ENV === "production"
          ? "__Secure-lockin.session-token"
          : "lockin.session-token",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: process.env.NODE_ENV === "production",
      },
    },
  },
};

export const { handlers, signIn, signOut, auth } = NextAuth(config);
