import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileImage, Clock, CheckCircle, AlertCircle } from "lucide-react";

interface Stats {
  total_conversions: number;
  today_conversions: number;
  success_rate: number;
  pending: number;
}

const fetchStats = async (): Promise<Stats> => {
  const response = await fetch("http://localhost:8000/api/admin/stats");
  if (!response.ok) {
    throw new Error("Failed to fetch stats");
  }
  return response.json();
};

export const StatsCard = () => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const statsData = [
    {
      title: "Total Conversions",
      value: stats?.total_conversions ?? 0,
      icon: FileImage,
      description: "All time",
      color: "text-whatsapp",
    },
    {
      title: "Today",
      value: stats?.today_conversions ?? 0,
      icon: Clock,
      description: "Last 24 hours",
      color: "text-blue-500",
    },
    {
      title: "Success Rate",
      value: `${stats?.success_rate ?? 0}%`,
      icon: CheckCircle,
      description: "Successful conversions",
      color: "text-green-500",
    },
    {
      title: "Pending",
      value: stats?.pending ?? 0,
      icon: AlertCircle,
      description: "In queue",
      color: "text-yellow-500",
    },
  ];

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Connection Error</CardTitle>
          <CardDescription>
            Cannot connect to backend at localhost:8000. Make sure Python server is running.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {statsData.map((stat) => (
        <Card key={stat.title} className="transition-shadow hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className={`h-5 w-5 ${stat.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? "..." : stat.value}
            </div>
            <p className="text-xs text-muted-foreground">{stat.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};
