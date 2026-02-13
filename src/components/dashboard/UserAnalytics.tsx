import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { api, UserAnalyticsData } from "@/lib/api";
import { format, parseISO } from "date-fns";
import { Users, UserPlus, UserCheck, Crown } from "lucide-react";

const maskPhone = (phone: string): string => {
  if (phone.length > 6) {
    return phone.slice(0, 4) + "****" + phone.slice(-4);
  }
  return "****" + phone.slice(-2);
};

export const UserAnalytics = () => {
  const {
    data: analytics,
    isLoading,
    error,
  } = useQuery<UserAnalyticsData>({
    queryKey: ["userAnalytics"],
    queryFn: api.getUserAnalytics,
    refetchInterval: 30000,
  });

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">User Data Error</CardTitle>
          <CardDescription>
            Failed to load user analytics. Make sure the backend is running.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const statCards = [
    {
      title: "Total Unique Users",
      value: analytics?.total_unique_users ?? 0,
      icon: Users,
      color: "text-whatsapp",
      bgColor: "bg-whatsapp/10",
    },
    {
      title: "Repeat Users",
      value: analytics?.repeat_users ?? 0,
      icon: UserCheck,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
    },
    {
      title: "New Users Today",
      value: analytics?.new_users_today ?? 0,
      icon: UserPlus,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
    },
  ];

  return (
    <div className="space-y-4">
      {/* Stat cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {statCards.map((stat) => (
          <Card key={stat.title} className="transition-shadow hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className={`rounded-lg p-2 ${stat.bgColor}`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {isLoading ? "..." : stat.value.toLocaleString()}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Top users table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Crown className="h-5 w-5 text-yellow-500" />
            Top 10 Users
          </CardTitle>
          <CardDescription>
            Most active users by conversion count
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <p className="text-muted-foreground">Loading user data...</p>
            </div>
          ) : analytics?.top_users && analytics.top_users.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>Phone Number</TableHead>
                  <TableHead className="text-right">Conversions</TableHead>
                  <TableHead className="text-right">Last Active</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {analytics.top_users.map((user, index) => (
                  <TableRow key={user.phone}>
                    <TableCell>
                      {index < 3 ? (
                        <Badge
                          className={
                            index === 0
                              ? "bg-yellow-500 hover:bg-yellow-500/90"
                              : index === 1
                                ? "bg-gray-400 hover:bg-gray-400/90"
                                : "bg-amber-600 hover:bg-amber-600/90"
                          }
                        >
                          {index + 1}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">
                          {index + 1}
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="font-mono">
                      {maskPhone(user.phone)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {user.count.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {(() => {
                        try {
                          return format(
                            parseISO(user.last_active),
                            "MMM dd, HH:mm"
                          );
                        } catch {
                          return user.last_active;
                        }
                      })()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex h-32 items-center justify-center">
              <p className="text-muted-foreground">No user data available</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
