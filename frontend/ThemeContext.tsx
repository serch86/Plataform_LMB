// ThemeContext.tsx
import React, { createContext, useContext, useState } from "react";
import { temasPorGrupo } from "@/styles/theme";

type Grupo = "A" | "B";

interface ThemeContextType {
  grupo: Grupo;
  setGrupo: (grupo: Grupo) => void;
  theme: (typeof temasPorGrupo)[Grupo];
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [grupo, setGrupo] = useState<Grupo>("A"); // Por defecto: A

  const theme = temasPorGrupo[grupo];

  return (
    <ThemeContext.Provider value={{ grupo, setGrupo, theme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme debe usarse dentro de ThemeProvider");
  }
  return context;
};
