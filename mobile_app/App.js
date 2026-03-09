import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { StatusBar } from "expo-status-bar";
import { Ionicons } from "@expo/vector-icons";

import DashboardScreen from "./src/screens/DashboardScreen";
import TradesScreen from "./src/screens/TradesScreen";
import PerformanceScreen from "./src/screens/PerformanceScreen";
import MT5Screen from "./src/screens/MT5Screen";
import ConfigScreen from "./src/screens/ConfigScreen";
import NotificationsScreen from "./src/screens/NotificationsScreen";
import { colors } from "./src/theme/colors";

const Tab = createBottomTabNavigator();

const TABS = [
  { name: "Dashboard", component: DashboardScreen, icon: "home", label: "Home" },
  { name: "Trades", component: TradesScreen, icon: "list", label: "Trades" },
  { name: "Performance", component: PerformanceScreen, icon: "stats-chart", label: "Charts" },
  { name: "MT5", component: MT5Screen, icon: "link", label: "MT5" },
  { name: "Config", component: ConfigScreen, icon: "settings", label: "Config" },
  { name: "Alerts", component: NotificationsScreen, icon: "notifications", label: "Alerts" },
];

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="dark" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarStyle: {
            backgroundColor: "#FFFFFF",
            borderTopColor: "#E8ECF0",
            borderTopWidth: 1,
            height: 88,
            paddingBottom: 24,
            paddingTop: 10,
          },
          tabBarActiveTintColor: colors.accent,
          tabBarInactiveTintColor: "#9CA3AF",
          tabBarLabelStyle: { fontSize: 10, fontWeight: "700", letterSpacing: 0.3 },
          tabBarIcon: ({ color, size, focused }) => {
            const tab = TABS.find(t => t.name === route.name);
            return (
              <Ionicons
                name={focused ? tab.icon : `${tab.icon}-outline`}
                size={focused ? size + 1 : size}
                color={color}
              />
            );
          },
        })}
      >
        {TABS.map(tab => (
          <Tab.Screen
            key={tab.name}
            name={tab.name}
            component={tab.component}
            options={{ tabBarLabel: tab.label }}
          />
        ))}
      </Tab.Navigator>
    </NavigationContainer>
  );
}
