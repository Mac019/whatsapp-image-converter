import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";

interface Conversion {
  id: string;
  phone_number: string;
  timestamp: string;
  status: "success" | "failed" | "pending";
  file_size: number;
}

const fetchConversions = async (): Promise<Conversion[]> => {
  const response = await fetch("http://localhost:8000/api/admin/conversions");
  if (!response.ok) {
    throw new Error("Failed to fetch conversions");
  }
  return response.json();
};

const formatPhoneNumber = (phone: string) => {
  // Mask middle digits for privacy
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

export const ConversionsTable = () => {
  const { data: conversions, isLoading, error } = useQuery({
    queryKey: ["conversions"],
    queryFn: fetchConversions,
    refetchInterval: 10000, // Refresh every 10 seconds
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
            Cannot connect to backend. Make sure Python server is running on localhost:8000
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
          History of image to PDF conversions via WhatsApp
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
                <TableHead>File Size</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {conversions.map((conversion) => (
                <TableRow key={conversion.id}>
                  <TableCell className="font-mono text-sm">
                    {format(new Date(conversion.timestamp), "MMM dd, HH:mm:ss")}
                  </TableCell>
                  <TableCell>{formatPhoneNumber(conversion.phone_number)}</TableCell>
                  <TableCell>{formatFileSize(conversion.file_size)}</TableCell>
                  <TableCell>{getStatusBadge(conversion.status)}</TableCell>
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
