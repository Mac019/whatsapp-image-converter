import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Eye, EyeOff, Save, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

const settingsSchema = z.object({
  whatsapp_business_account_id: z.string().min(1, "Required"),
  phone_number_id: z.string().min(1, "Required"),
  access_token: z.string().min(1, "Required"),
  webhook_verify_token: z.string().min(1, "Required"),
  admin_password: z.string().min(6, "Minimum 6 characters"),
});

type SettingsFormData = z.infer<typeof settingsSchema>;

export const SettingsForm = () => {
  const [showToken, setShowToken] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      whatsapp_business_account_id: "",
      phone_number_id: "",
      access_token: "",
      webhook_verify_token: "",
      admin_password: "",
    },
  });

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const settings = await api.getSettings();
        form.reset({
          whatsapp_business_account_id: settings.whatsapp_business_account_id || "",
          phone_number_id: settings.phone_number_id || "",
          access_token: settings.access_token || "",
          webhook_verify_token: settings.webhook_verify_token || "",
          admin_password: "",
        });
      } catch (error) {
        console.error("Failed to load settings:", error);
      }
    };
    loadSettings();
  }, [form]);

  const onSubmit = async (data: SettingsFormData) => {
    setIsLoading(true);
    try {
      await api.saveSettings(data);
      toast.success("Settings saved successfully!");
      form.setValue("admin_password", "");
    } catch (error: any) {
      toast.error(error.message || "Failed to save settings");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Meta WhatsApp API Settings</CardTitle>
        <CardDescription>
          Configure your WhatsApp Business API credentials from Meta Developer Console
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="whatsapp_business_account_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>WhatsApp Business Account ID</FormLabel>
                    <FormControl>
                      <Input placeholder="123456789012345" {...field} />
                    </FormControl>
                    <FormDescription>
                      Found in Meta Business Suite
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="phone_number_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phone Number ID</FormLabel>
                    <FormControl>
                      <Input placeholder="123456789012345" {...field} />
                    </FormControl>
                    <FormDescription>
                      The ID of your WhatsApp Business phone number
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="access_token"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Access Token</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input
                        type={showToken ? "text" : "password"}
                        placeholder="EAAxxxxxxxxxx..."
                        {...field}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full"
                        onClick={() => setShowToken(!showToken)}
                      >
                        {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </FormControl>
                  <FormDescription>
                    Permanent or temporary access token from Meta Developer Console
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="webhook_verify_token"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Webhook Verify Token</FormLabel>
                    <FormControl>
                      <Input placeholder="my_secure_token_123" {...field} />
                    </FormControl>
                    <FormDescription>
                      Custom token for Meta webhook verification
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="admin_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Admin Password</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          placeholder="••••••••"
                          {...field}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="absolute right-0 top-0 h-full"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </FormControl>
                    <FormDescription>
                      Password to protect admin dashboard
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Button type="submit" className="bg-whatsapp hover:bg-whatsapp-dark" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Settings
                </>
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
};
