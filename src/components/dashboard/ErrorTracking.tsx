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
import { api, ErrorTrackingData } from "@/lib/api";
import { format, parseISO } from "date-fns";
import {
  AlertTriangle,
  AlertOctagon,
  TrendingDown,
  Clock,
} from "lucide-react";

export const ErrorTracking = () => {
  const {
    data: errorData,
    isLoading,
    error,
  } = useQuery<ErrorTrackingData>({
    queryKey: ["errorTracking"],
    queryFn: api.getErrorTracking,
    refetchInterval: 30000,
  });

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">
            Error Tracking Unavailable
          </CardTitle>
          <CardDescription>
            Failed to load error tracking data.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const errorRate = errorData?.error_rate ?? 0;
  const rateColor =
    errorRate > 10
      ? "text-red-500"
      : errorRate > 5
        ? "text-yellow-500"
        : "text-green-500";
  const rateBg =
    errorRate > 10
      ? "bg-red-500/10"
      : errorRate > 5
        ? "text-yellow-500/10"
        : "bg-green-500/10";

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Error Rate
            </CardTitle>
            <div className={`rounded-lg p-2 ${rateBg}`}>
              <TrendingDown className={`h-4 w-4 ${rateColor}`} />
            </div>
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${rateColor}`}>
              {isLoading ? "..." : `${errorRate.toFixed(1)}%`}
            </div>
            <p className="text-xs text-muted-foreground">
              {errorRate <= 5
                ? "Healthy"
                : errorRate <= 10
                  ? "Needs attention"
                  : "Critical"}
            </p>
          </CardContent>
        </Card>

        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Errors Today
            </CardTitle>
            <div className="rounded-lg bg-orange-500/10 p-2">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {isLoading ? "..." : (errorData?.errors_today ?? 0)}
            </div>
            <p className="text-xs text-muted-foreground">In the last 24 hours</p>
          </CardContent>
        </Card>

        <Card className="transition-shadow hover:shadow-md">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Errors
            </CardTitle>
            <div className="rounded-lg bg-red-500/10 p-2">
              <AlertOctagon className="h-4 w-4 text-red-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {isLoading
                ? "..."
                : (errorData?.total_errors ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
      </div>

      {/* Error types table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Error Types
          </CardTitle>
          <CardDescription>
            Breakdown of error types by frequency
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <p className="text-muted-foreground">Loading error types...</p>
            </div>
          ) : errorData?.error_types && errorData.error_types.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Error Type</TableHead>
                  <TableHead className="text-right">Count</TableHead>
                  <TableHead className="text-right">Last Occurred</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {errorData.error_types.map((errType) => (
                  <TableRow key={errType.type}>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-xs">
                        {errType.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {errType.count.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      {(() => {
                        try {
                          return format(
                            parseISO(errType.last_occurred),
                            "MMM dd, HH:mm"
                          );
                        } catch {
                          return errType.last_occurred;
                        }
                      })()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex h-32 items-center justify-center">
              <p className="text-muted-foreground">No errors recorded</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent errors */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-muted-foreground" />
            Recent Errors
          </CardTitle>
          <CardDescription>Latest error occurrences</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <p className="text-muted-foreground">Loading recent errors...</p>
            </div>
          ) : errorData?.recent_errors &&
            errorData.recent_errors.length > 0 ? (
            <div className="space-y-3">
              {errorData.recent_errors.map((err) => (
                <div
                  key={err.id}
                  className="flex items-start gap-3 rounded-lg border border-destructive/20 bg-destructive/5 p-3"
                >
                  <AlertOctagon className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className="shrink-0 text-xs"
                      >
                        {err.feature}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {(() => {
                          try {
                            return format(
                              parseISO(err.timestamp),
                              "MMM dd, HH:mm:ss"
                            );
                          } catch {
                            return err.timestamp;
                          }
                        })()}
                      </span>
                    </div>
                    <p className="mt-1 truncate text-sm text-destructive">
                      {err.message}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center">
              <p className="text-muted-foreground">No recent errors</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
