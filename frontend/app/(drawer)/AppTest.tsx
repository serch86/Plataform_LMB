import React from "react";
import { Text } from "react-native";
import { useUserStore } from "@/store/useUserStore";

export default function AppTest() {
  const token = useUserStore((s) => s.token);

  return <Text>Token: {token}</Text>;
}
