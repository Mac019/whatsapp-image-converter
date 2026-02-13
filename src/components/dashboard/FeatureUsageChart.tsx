import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { api, FeatureUsageData } from "@/lib/api";
import { PieChart as PieChartIcon } from "lucide-react";

const COLORS = [
  "hsl(var(--whatsapp))",
  "#3b82f6",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#f97316",
  "#14b8a6",
  "#6366f1",
  "#84cc16",
];

interface CustomLabelProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percentage: number;
}

const renderCustomLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percentage,
}: CustomLabelProps) => {
  if (percentage < 5) return null;
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      className="text-xs font-medium"
    >
      {`${percentage.toFixed(0)}%`}
    </text>
  );
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: FeatureUsageData;
  }>;
}

const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  return (
    <div className="rounded-lg border bg-background px-3 py-2 text-sm shadow-lg">
      <p className="font-medium">{data.feature}</p>
      <p className="text-muted-foreground">
        {data.count} conversions ({data.percentage.toFixed(1)}%)
      </p>
    </div>
  );
};

export const FeatureUsageChart = () => {
  const {
    data: features,
    isLoading,
    error,
  } = useQuery<FeatureUsageData[]>({
    queryKey: ["featureUsage"],
    queryFn: api.getFeatureUsage,
    refetchInterval: 60000,
  });

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Feature Data Error</CardTitle>
          <CardDescription>
            Failed to load feature usage data.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PieChartIcon className="h-5 w-5 text-whatsapp" />
          Feature Popularity
        </CardTitle>
        <CardDescription>
          Breakdown of feature usage across all conversions
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-[300px] items-center justify-center">
            <p className="text-muted-foreground">Loading feature data...</p>
          </div>
        ) : features && features.length > 0 ? (
          <div className="flex flex-col gap-4">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={features}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ cx, cy, midAngle, innerRadius, outerRadius, index }) =>
                    renderCustomLabel({
                      cx,
                      cy,
                      midAngle,
                      innerRadius,
                      outerRadius,
                      percentage: features[index].percentage,
                    })
                  }
                  outerRadius={110}
                  dataKey="count"
                  nameKey="feature"
                >
                  {features.map((_entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  formatter={(value: string) => (
                    <span className="text-xs text-foreground">{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>

            {/* Feature list with percentages */}
            <div className="space-y-2">
              {features.map((feature, index) => (
                <div
                  key={feature.feature}
                  className="flex items-center justify-between text-sm"
                >
                  <div className="flex items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{
                        backgroundColor: COLORS[index % COLORS.length],
                      }}
                    />
                    <span>{feature.feature}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-muted-foreground">
                      {feature.count} uses
                    </span>
                    <span className="font-medium">
                      {feature.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex h-[300px] items-center justify-center">
            <p className="text-muted-foreground">No feature usage data yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
