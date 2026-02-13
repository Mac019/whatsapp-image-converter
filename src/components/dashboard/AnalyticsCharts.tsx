import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { api, TimeseriesData } from "@/lib/api";
import { format, parseISO } from "date-fns";
import { TrendingUp } from "lucide-react";

type DayRange = "7" | "14" | "30";

export const AnalyticsCharts = () => {
  const [days, setDays] = useState<DayRange>("30");

  const {
    data: timeseries,
    isLoading,
    error,
  } = useQuery<TimeseriesData[]>({
    queryKey: ["timeseries", days],
    queryFn: () => api.getTimeseries(Number(days)),
    refetchInterval: 60000,
  });

  const formatXAxis = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), "MMM dd");
    } catch {
      return dateStr;
    }
  };

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Chart Error</CardTitle>
          <CardDescription>
            Failed to load analytics data. Make sure the backend is running.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="space-y-1.5">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-whatsapp" />
            Conversions Over Time
          </CardTitle>
          <CardDescription>
            Daily conversion activity for the last {days} days
          </CardDescription>
        </div>
        <Select value={days} onValueChange={(v) => setDays(v as DayRange)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Select range" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="14">Last 14 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-[350px] items-center justify-center">
            <p className="text-muted-foreground">Loading chart data...</p>
          </div>
        ) : timeseries && timeseries.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart
              data={timeseries}
              margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tickFormatter={formatXAxis}
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
              />
              <YAxis
                className="text-xs"
                tick={{ fill: "hsl(var(--muted-foreground))" }}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--background))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                labelFormatter={(label) => {
                  try {
                    return format(parseISO(label), "MMMM dd, yyyy");
                  } catch {
                    return label;
                  }
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="conversions"
                name="Total"
                stroke="hsl(var(--whatsapp))"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="successes"
                name="Successes"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="failures"
                name="Failures"
                stroke="#ef4444"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-[350px] items-center justify-center">
            <p className="text-muted-foreground">
              No conversion data available for this period
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
