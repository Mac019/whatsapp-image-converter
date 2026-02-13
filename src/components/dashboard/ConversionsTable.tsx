import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { api, Conversion } from "@/lib/api";
import { format } from "date-fns";
import { ChevronDown, ChevronRight } from "lucide-react";

const formatPhoneNumber = (phone: string) => {
  if (phone.length > 6) {
    return phone.slice(0, 4) + "****" + phone.slice(-4);
  }
  return phone;
};

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
};

const ConversionDetail = ({ conversion }: { conversion: Conversion }) => {
  const [open, setOpen] = useState(false);

  const hasDetails = conversion.feature || conversion.processing_time_ms || conversion.error_message;
  if (!hasDetails) return null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
          {open ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-2 space-y-1 rounded bg-muted p-2 text-xs">
          {conversion.feature && <p><span className="font-medium">Feature:</span> {conversion.feature}</p>}
          {conversion.input_type && <p><span className="font-medium">Input:</span> {conversion.input_type}</p>}
          {conversion.output_type && <p><span className="font-medium">Output:</span> {conversion.output_type}</p>}
          {conversion.processing_time_ms != null && (
            <p><span className="font-medium">Time:</span> {(conversion.processing_time_ms / 1000).toFixed(2)}s</p>
          )}
          {conversion.output_file_size != null && (
            <p><span className="font-medium">Output size:</span> {formatFileSize(conversion.output_file_size)}</p>
          )}
          {conversion.error_message && (
            <p className="text-destructive"><span className="font-medium">Error:</span> {conversion.error_message}</p>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

export const ConversionsTable = () => {
  const { data: conversions, isLoading, error } = useQuery({
    queryKey: ["conversions"],
    queryFn: api.getConversions,
    refetchInterval: 10000,
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return <Badge className="bg-success hover:bg-success/90">Success</Badge>;
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      case "pending":
        return <Badge variant="secondary">Pending</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

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
    <Card>
      <CardHeader>
        <CardTitle>Recent Conversions</CardTitle>
        <CardDescription>
          History of document conversions via WhatsApp
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-32 items-center justify-center">
            <p className="text-muted-foreground">Loading conversions...</p>
          </div>
        ) : conversions && conversions.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Phone Number</TableHead>
                <TableHead>Feature</TableHead>
                <TableHead>File Size</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {conversions.map((conversion) => (
                <TableRow key={conversion.id}>
                  <TableCell className="font-mono text-sm">
                    {format(new Date(conversion.timestamp), "MMM dd, HH:mm:ss")}
                  </TableCell>
                  <TableCell>{formatPhoneNumber(conversion.phone_number)}</TableCell>
                  <TableCell>
                    {conversion.feature ? (
                      <Badge variant="outline" className="text-xs">{conversion.feature}</Badge>
                    ) : "—"}
                  </TableCell>
                  <TableCell>{formatFileSize(conversion.file_size)}</TableCell>
                  <TableCell>{getStatusBadge(conversion.status)}</TableCell>
                  <TableCell>
                    <ConversionDetail conversion={conversion} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="flex h-32 items-center justify-center">
            <p className="text-muted-foreground">No conversions yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
