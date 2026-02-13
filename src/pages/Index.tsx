import { useState } from "react";
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { ConversionsTable } from "@/components/dashboard/ConversionsTable";
import { SettingsForm } from "@/components/dashboard/SettingsForm";
import { SetupGuide } from "@/components/dashboard/SetupGuide";
import { AnalyticsCharts } from "@/components/dashboard/AnalyticsCharts";
import { FeatureUsageChart } from "@/components/dashboard/FeatureUsageChart";
import { UserAnalytics } from "@/components/dashboard/UserAnalytics";
import { ErrorTracking } from "@/components/dashboard/ErrorTracking";
import { SystemHealth } from "@/components/dashboard/SystemHealth";
import { GeoDistribution } from "@/components/dashboard/GeoDistribution";
import { ExportButton } from "@/components/dashboard/ExportButton";
import {
  MessageSquare, FileImage, Settings, BookOpen,
  BarChart3, Users, AlertTriangle, Activity, History,
} from "lucide-react";

const navItems = [
  { key: "dashboard", label: "Dashboard", icon: FileImage },
  { key: "analytics", label: "Analytics", icon: BarChart3 },
  { key: "users", label: "Users", icon: Users },
  { key: "errors", label: "Errors", icon: AlertTriangle },
  { key: "system", label: "System", icon: Activity },
  { key: "history", label: "History", icon: History },
] as const;

const configItems = [
  { key: "settings", label: "Settings", icon: Settings },
  { key: "setup", label: "Setup", icon: BookOpen },
] as const;

type Section = (typeof navItems)[number]["key"] | (typeof configItems)[number]["key"];

function SectionContent({ section }: { section: Section }) {
  switch (section) {
    case "dashboard":
      return (
        <div className="space-y-6">
          <StatsCard />
          <div className="grid gap-6 lg:grid-cols-2">
            <AnalyticsCharts />
            <FeatureUsageChart />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <UserAnalytics />
            <GeoDistribution />
          </div>
        </div>
      );
    case "analytics":
      return (
        <div className="space-y-6">
          <AnalyticsCharts />
          <FeatureUsageChart />
        </div>
      );
    case "users":
      return (
        <div className="space-y-6">
          <UserAnalytics />
          <GeoDistribution />
        </div>
      );
    case "errors":
      return <ErrorTracking />;
    case "system":
      return <SystemHealth />;
    case "history":
      return <ConversionsTable />;
    case "settings":
      return <SettingsForm />;
    case "setup":
      return <SetupGuide />;
  }
}

const sectionTitles: Record<Section, string> = {
  dashboard: "Dashboard",
  analytics: "Analytics",
  users: "Users",
  errors: "Error Tracking",
  system: "System Health",
  history: "Conversion History",
  settings: "Settings",
  setup: "Setup Guide",
};

const Index = () => {
  const [activeSection, setActiveSection] = useState<Section>("dashboard");

  return (
    <SidebarProvider>
      <Sidebar collapsible="icon">
        <SidebarHeader className="p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-whatsapp text-white">
              <MessageSquare className="h-4 w-4" />
            </div>
            <span className="truncate font-semibold group-data-[collapsible=icon]:hidden">
              DocBot Admin
            </span>
          </div>
        </SidebarHeader>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>Navigation</SidebarGroupLabel>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.key}>
                  <SidebarMenuButton
                    isActive={activeSection === item.key}
                    tooltip={item.label}
                    onClick={() => setActiveSection(item.key)}
                    className={
                      activeSection === item.key
                        ? "bg-whatsapp/10 text-whatsapp-dark hover:bg-whatsapp/20 hover:text-whatsapp-dark"
                        : ""
                    }
                  >
                    <item.icon />
                    <span>{item.label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>

          <SidebarGroup>
            <SidebarGroupLabel>Configuration</SidebarGroupLabel>
            <SidebarMenu>
              {configItems.map((item) => (
                <SidebarMenuItem key={item.key}>
                  <SidebarMenuButton
                    isActive={activeSection === item.key}
                    tooltip={item.label}
                    onClick={() => setActiveSection(item.key)}
                    className={
                      activeSection === item.key
                        ? "bg-whatsapp/10 text-whatsapp-dark hover:bg-whatsapp/20 hover:text-whatsapp-dark"
                        : ""
                    }
                  >
                    <item.icon />
                    <span>{item.label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        </SidebarContent>

        <SidebarFooter>
          <ExportButton compact />
        </SidebarFooter>

        <SidebarRail />
      </Sidebar>

      <main className="flex-1 overflow-auto">
        <header className="sticky top-0 z-10 flex items-center gap-3 border-b bg-background px-4 py-3">
          <SidebarTrigger />
          <h1 className="text-lg font-semibold">{sectionTitles[activeSection]}</h1>
        </header>
        <div className="p-6">
          <SectionContent section={activeSection} />
        </div>
      </main>
    </SidebarProvider>
  );
};

export default Index;
