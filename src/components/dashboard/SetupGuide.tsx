import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, ExternalLink } from "lucide-react";

export const SetupGuide = () => {
  const steps = [
    {
      id: "step-1",
      title: "Create Meta Developer Account",
      description: "Set up your Meta for Developers account and create an app",
      content: (
        <ol className="list-decimal space-y-2 pl-4 text-sm text-muted-foreground">
          <li>Go to <a href="https://developers.facebook.com" target="_blank" rel="noopener noreferrer" className="text-whatsapp hover:underline">developers.facebook.com</a></li>
          <li>Create a new app and select "Business" type</li>
          <li>Add "WhatsApp" product to your app</li>
          <li>Complete business verification if required</li>
        </ol>
      ),
    },
    {
      id: "step-2",
      title: "Get WhatsApp Business API Credentials",
      description: "Find your Phone Number ID and Access Token",
      content: (
        <ol className="list-decimal space-y-2 pl-4 text-sm text-muted-foreground">
          <li>In your Meta app dashboard, go to WhatsApp → API Setup</li>
          <li>Copy the <strong>Phone Number ID</strong> from the "From" section</li>
          <li>Copy the <strong>WhatsApp Business Account ID</strong></li>
          <li>Generate a <strong>Permanent Access Token</strong> (or use temporary for testing)</li>
          <li>Enter these values in the Settings tab</li>
        </ol>
      ),
    },
    {
      id: "step-3",
      title: "Run the Python Backend",
      description: "Start the FastAPI server locally",
      content: (
        <div className="space-y-3 text-sm text-muted-foreground">
          <p>Install dependencies and run the server:</p>
          <pre className="overflow-x-auto rounded-lg bg-muted p-3 font-mono text-xs">
{`# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --port 8000`}
          </pre>
        </div>
      ),
    },
    {
      id: "step-4",
      title: "Configure Webhook",
      description: "Connect Meta to your webhook endpoint",
      content: (
        <ol className="list-decimal space-y-2 pl-4 text-sm text-muted-foreground">
          <li>Use ngrok or similar to expose localhost: <code className="rounded bg-muted px-1">ngrok http 8000</code></li>
          <li>In Meta app dashboard, go to WhatsApp → Configuration</li>
          <li>Set Webhook URL to: <code className="rounded bg-muted px-1">https://your-ngrok-url/webhook/whatsapp</code></li>
          <li>Enter your <strong>Verify Token</strong> (same as in Settings tab)</li>
          <li>Subscribe to "messages" webhook field</li>
        </ol>
      ),
    },
    {
      id: "step-5",
      title: "Test the Integration",
      description: "Send an image to your WhatsApp Business number",
      content: (
        <ol className="list-decimal space-y-2 pl-4 text-sm text-muted-foreground">
          <li>Add your phone number as a test recipient in Meta dashboard</li>
          <li>Send a test message to your WhatsApp Business number</li>
          <li>Send any image (JPG, PNG)</li>
          <li>You should receive a PDF version back within seconds!</li>
        </ol>
      ),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>Setup Guide</CardTitle>
          <Badge variant="outline" className="border-whatsapp text-whatsapp">
            5 Steps
          </Badge>
        </div>
        <CardDescription>
          Follow these steps to set up your WhatsApp Image to PDF converter
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible className="w-full">
          {steps.map((step, index) => (
            <AccordionItem key={step.id} value={step.id}>
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center gap-3 text-left">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-whatsapp/10 text-xs font-bold text-whatsapp">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium">{step.title}</p>
                    <p className="text-sm text-muted-foreground">{step.description}</p>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="pl-9 pt-2">
                {step.content}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>

        <div className="mt-6 rounded-lg border border-whatsapp/20 bg-whatsapp/5 p-4">
          <div className="flex items-start gap-3">
            <CheckCircle className="mt-0.5 h-5 w-5 text-whatsapp" />
            <div>
              <p className="font-medium text-foreground">Need help?</p>
              <p className="text-sm text-muted-foreground">
                Check the{" "}
                <a
                  href="https://developers.facebook.com/docs/whatsapp/cloud-api"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-whatsapp hover:underline"
                >
                  Meta WhatsApp Cloud API docs
                  <ExternalLink className="h-3 w-3" />
                </a>
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
