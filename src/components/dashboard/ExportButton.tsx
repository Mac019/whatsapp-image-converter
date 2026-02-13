import { useState } from "react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Download, Loader2, CheckCircle, AlertCircle } from "lucide-react";

type ExportState = "idle" | "loading" | "success" | "error";

export const ExportButton = ({ compact = false }: { compact?: boolean }) => {
  const [state, setState] = useState<ExportState>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const handleExport = async () => {
    setState("loading");
    setErrorMessage("");

    try {
      const blob = await api.exportConversions();

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;

      // Generate filename with current date
      const date = new Date().toISOString().split("T")[0];
      link.download = `conversions-export-${date}.csv`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setState("success");

      // Reset to idle after 3 seconds
      setTimeout(() => setState("idle"), 3000);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Export failed unexpectedly";
      setErrorMessage(message);
      setState("error");

      // Reset to idle after 5 seconds
      setTimeout(() => {
        setState("idle");
        setErrorMessage("");
      }, 5000);
    }
  };

  const getIcon = () => {
    switch (state) {
      case "loading":
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case "success":
        return <CheckCircle className="h-4 w-4" />;
      case "error":
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Download className="h-4 w-4" />;
    }
  };

  const getLabel = () => {
    switch (state) {
      case "loading":
        return "Exporting...";
      case "success":
        return "Downloaded!";
      case "error":
        return "Export Failed";
      default:
        return "Export CSV";
    }
  };

  const getVariant = (): "default" | "destructive" | "outline" => {
    switch (state) {
      case "error":
        return "destructive";
      case "success":
        return "outline";
      default:
        return "default";
    }
  };

  return (
    <div className={compact ? "flex flex-col gap-1" : "flex items-center gap-2"}>
      <Button
        variant={getVariant()}
        onClick={handleExport}
        disabled={state === "loading"}
        size={compact ? "sm" : "default"}
        className={`${
          state === "success"
            ? "border-green-500 text-green-500 hover:bg-green-500/10"
            : ""
        }${compact ? " w-full" : ""}`}
      >
        {getIcon()}
        <span className="ml-2">{getLabel()}</span>
      </Button>
      {state === "error" && errorMessage && (
        <span className="text-xs text-destructive">{errorMessage}</span>
      )}
    </div>
  );
};
