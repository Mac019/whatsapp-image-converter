import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api, AdminStats } from "@/lib/api";
import {
  FileImage, Clock, CheckCircle, AlertCircle,
  Users, Timer, Star, HardDrive,
} from "lucide-react";

export const StatsCard = () => {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["stats"],
    queryFn: api.getStats,
    refetchInterval: 30000,
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
      title: "Active Users",
      value: stats?.active_users ?? 0,
      icon: Users,
      description: "Unique users",
      color: "text-purple-500",
    },
    {
      title: "Avg Time",
      value: stats?.avg_processing_time_ms
        ? `${(stats.avg_processing_time_ms / 1000).toFixed(1)}s`
        : "—",
      icon: Timer,
      description: "Processing time",
      color: "text-orange-500",
    },
    {
      title: "Top Feature",
      value: stats?.top_feature || "—",
      icon: Star,
      description: "Most used",
      color: "text-yellow-500",
    },
    {
      title: "Bandwidth",
      value: stats?.total_bandwidth_mb
        ? `${stats.total_bandwidth_mb.toFixed(1)} MB`
        : "0 MB",
      icon: HardDrive,
      description: "Total processed",
      color: "text-cyan-500",
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
            Cannot connect to backend. Make sure Python server is running.
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
