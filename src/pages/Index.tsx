import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { ConversionsTable } from "@/components/dashboard/ConversionsTable";
import { SettingsForm } from "@/components/dashboard/SettingsForm";
import { SetupGuide } from "@/components/dashboard/SetupGuide";
import { MessageSquare, FileImage, Settings, BookOpen } from "lucide-react";

const Index = () => {
  const [activeTab, setActiveTab] = useState("dashboard");

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-whatsapp text-white">
              <MessageSquare className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">WhatsApp Image to PDF</h1>
              <p className="text-sm text-muted-foreground">Convert images via WhatsApp</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-4">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <FileImage className="h-4 w-4" />
              <span className="hidden sm:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger value="conversions" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              <span className="hidden sm:inline">History</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
            <TabsTrigger value="setup" className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              <span className="hidden sm:inline">Setup</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <StatsCard />
          </TabsContent>

          <TabsContent value="conversions">
            <ConversionsTable />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsForm />
          </TabsContent>

          <TabsContent value="setup">
            <SetupGuide />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
