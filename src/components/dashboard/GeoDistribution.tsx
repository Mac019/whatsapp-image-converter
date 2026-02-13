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
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { api, UserAnalyticsData } from "@/lib/api";
import { Globe } from "lucide-react";

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: { country: string; code: string; count: number };
  }>;
}

const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  return (
    <div className="rounded-lg border bg-background px-3 py-2 text-sm shadow-lg">
      <p className="font-medium">
        {data.country} ({data.code})
      </p>
      <p className="text-muted-foreground">
        {data.count.toLocaleString()} user{data.count !== 1 ? "s" : ""}
      </p>
    </div>
  );
};

export const GeoDistribution = () => {
  const {
    data: analytics,
    isLoading,
    error,
  } = useQuery<UserAnalyticsData>({
    queryKey: ["userAnalytics"],
    queryFn: api.getUserAnalytics,
    refetchInterval: 60000,
  });

  const distribution = analytics?.country_distribution ?? [];
  const totalUsers = distribution.reduce((sum, c) => sum + c.count, 0);

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">
            Geo Data Unavailable
          </CardTitle>
          <CardDescription>
            Failed to load geographic distribution data.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-whatsapp" />
          Geographic Distribution
        </CardTitle>
        <CardDescription>
          User distribution by country (based on phone number prefixes)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-[300px] items-center justify-center">
            <p className="text-muted-foreground">
              Loading geographic data...
            </p>
          </div>
        ) : distribution.length > 0 ? (
          <div className="space-y-6">
            {/* Bar chart for top countries */}
            {distribution.length > 1 && (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart
                  data={distribution.slice(0, 10)}
                  margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    className="stroke-muted"
                  />
                  <XAxis
                    dataKey="code"
                    className="text-xs"
                    tick={{ fill: "hsl(var(--muted-foreground))" }}
                  />
                  <YAxis
                    className="text-xs"
                    tick={{ fill: "hsl(var(--muted-foreground))" }}
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar
                    dataKey="count"
                    fill="hsl(var(--whatsapp))"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}

            {/* Full table */}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Country</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead className="text-right">Users</TableHead>
                  <TableHead className="text-right">Share</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {distribution.map((country) => {
                  const share =
                    totalUsers > 0
                      ? ((country.count / totalUsers) * 100).toFixed(1)
                      : "0.0";

                  return (
                    <TableRow key={country.code}>
                      <TableCell className="font-medium">
                        {country.country}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          {country.code}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {country.count.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {share}%
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        ) : (
          <div className="flex h-[300px] items-center justify-center">
            <p className="text-muted-foreground">
              No geographic data available yet
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
