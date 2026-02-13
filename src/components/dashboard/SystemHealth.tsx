import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { api, SystemHealthData } from "@/lib/api";
import {
  Cpu,
  MemoryStick,
  HardDrive,
  Clock,
  Activity,
  Users,
} from "lucide-react";

const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  const parts: string[] = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  parts.push(`${minutes}m`);

  return parts.join(" ");
};

const getUsageColor = (percent: number): string => {
  if (percent >= 90) return "text-red-500";
  if (percent >= 70) return "text-yellow-500";
  return "text-green-500";
};

const getUsageBadge = (percent: number) => {
  if (percent >= 90) {
    return (
      <Badge variant="destructive" className="text-xs">
        Critical
      </Badge>
    );
  }
  if (percent >= 70) {
    return (
      <Badge className="bg-yellow-500 text-xs hover:bg-yellow-500/90">
        Warning
      </Badge>
    );
  }
  return (
    <Badge className="bg-green-500 text-xs hover:bg-green-500/90">
      Healthy
    </Badge>
  );
};

interface UsageBarProps {
  label: string;
  icon: React.ElementType;
  percent: number;
  detail: string;
  isLoading: boolean;
}

const UsageBar = ({
  label,
  icon: Icon,
  percent,
  detail,
  isLoading,
}: UsageBarProps) => {
  const color = getUsageColor(percent);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`h-4 w-4 ${color}`} />
          <span className="text-sm font-medium">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          {!isLoading && getUsageBadge(percent)}
          <span className={`text-sm font-bold ${color}`}>
            {isLoading ? "..." : `${percent.toFixed(1)}%`}
          </span>
        </div>
      </div>
      <Progress value={isLoading ? 0 : percent} className="h-2" />
      <p className="text-xs text-muted-foreground">
        {isLoading ? "Loading..." : detail}
      </p>
    </div>
  );
};

export const SystemHealth = () => {
  const {
    data: health,
    isLoading,
    error,
    dataUpdatedAt,
  } = useQuery<SystemHealthData>({
    queryKey: ["systemHealth"],
    queryFn: api.getSystemHealth,
    refetchInterval: 10000,
  });

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">System Unavailable</CardTitle>
          <CardDescription>
            Cannot reach the backend server. The system may be offline.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const lastUpdated = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString()
    : "Never";

  return (
    <div className="space-y-4">
      {/* Resource usage */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1.5">
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-whatsapp" />
                System Resources
              </CardTitle>
              <CardDescription>
                Server resource utilization (auto-refreshes every 10s)
              </CardDescription>
            </div>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <div className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              Last updated: {lastUpdated}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <UsageBar
            label="CPU Usage"
            icon={Cpu}
            percent={health?.cpu_percent ?? 0}
            detail={`${(health?.cpu_percent ?? 0).toFixed(1)}% of available CPU`}
            isLoading={isLoading}
          />

          <UsageBar
            label="Memory Usage"
            icon={MemoryStick}
            percent={health?.memory_percent ?? 0}
            detail={
              health
                ? `${health.memory_used_mb.toFixed(0)} MB / ${health.memory_total_mb.toFixed(0)} MB`
                : "Loading..."
            }
            isLoading={isLoading}
          />

          <UsageBar
            label="Disk Usage"
            icon={HardDrive}
            percent={health?.disk_percent ?? 0}
            detail={
              health
                ? `${health.disk_used_gb.toFixed(1)} GB / ${health.disk_total_gb.toFixed(1)} GB`
                : "Loading..."
            }
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      {/* System info */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Uptime
            </CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading
                ? "..."
                : formatUptime(health?.uptime_seconds ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Since last restart
            </p>
          </CardContent>
        </Card>

        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Python Version
            </CardTitle>
            <Badge variant="outline" className="text-xs">
              Runtime
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? "..." : health?.python_version ?? "Unknown"}
            </div>
            <p className="text-xs text-muted-foreground">
              Backend interpreter
            </p>
          </CardContent>
        </Card>

        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active Sessions
            </CardTitle>
            <Users className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? "..." : (health?.active_sessions ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Currently connected
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
