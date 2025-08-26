import { ReactNode, useEffect } from "react";
import { useRouter, usePathname } from "expo-router";
import { useUserStore } from "@/store/useUserStore";

type Props = { children: ReactNode };

export default function AuthGate({ children }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const token = useUserStore((s) => s.token);

  const isPublic = pathname === "/login";

  useEffect(() => {
    if (!token && !isPublic) {
      router.replace("/login");
    }
  }, [token, isPublic, router]);

  if (!token && !isPublic) return null;

  return <>{children}</>;
}
